"""
TKinter Template GUI with MongoDB API
- Allows to read/write to json files

Updated: 12.09.2021
Author: Matthias Ley
"""

from tkinter import simpledialog, filedialog, Toplevel, Menu, Canvas, messagebox, font, TclError
from tkinter import StringVar, BooleanVar, Listbox
from tkinter.ttk import Label, Button, Frame, Entry, Separator, Progressbar, Checkbutton
from tkinter.ttk import Style, Notebook, Scrollbar
from ttkthemes import ThemedTk
from functools import partial
from configparser import ConfigParser
import datetime
import os
import sys
import getpass
import random
import time
from concurrent.futures import ThreadPoolExecutor
import platform
if platform.system() == "Windows":
    import win32gui  # hide console
    import win32con  # hide console
    import win32console  # hide console
import json
from requests import get  # external ip-check
from pymongo import MongoClient
import pymongo.errors as pymongo_errors


# global dicts for widgets (buttons, labels, entries, frames, variables, other)
btn, lbl, ent, frm, var, oth = {}, {}, {}, {}, {}, {}

# global dict for runtime environmental variables
env = {
    "test_var": None,
    "json_path": None,
    "json_content": None,
    "db": None
}

# other vars
ui_version = "1.0"


class Logger(object):
    """Logger class
    - can be enabled via config.ini when setting logger=True or via GUI
    - logs to console and to .txt file in folder logs with timestamps
    """

    def __init__(self, stream):
        self.terminal = stream
        self.log = open(f"logs{os.sep}{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log", 'a')

    def write(self, message):
        self.terminal.write(message)
        self.log.write(datetime.datetime.today().strftime('[%H:%M:%S] ') + message)

    def flush(self):
        pass


class AutoScrollbar(Scrollbar):
    """AutoScrollbar class
    - displays/hides a scrollbar_y when outer window reaches a certain size
    - applied to canvas > handed over to Frame self.rootframe which is the parent for Notebook self.tab_root
    """

    def set(self, low, high):
        if float(low) <= 0.0 and float(high) >= 1.0:
            self.tk.call("grid", "remove", self)
        else:
            self.grid()
        Scrollbar.set(self, low, high)

    def pack(self, **kw):
        raise TclError("pack cannot be used with this widget")

    def place(self, **kw):
        raise TclError("place cannot be used  with this widget")


class ToolTip(object):
    """Tooltip class
    - Call with create_tooltip(widget, text)"""

    def __init__(self, widget):
        self.widget = widget
        self.tip_window = None
        self.id = None
        self.x = self.y = 0
        self.text = None

    def showtip(self, text):
        """Display text in tooltip window"""
        self.text = text
        if self.tip_window or not self.text:
            return
        x, y, cx, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 57
        y = y + cy + self.widget.winfo_rooty() + 27
        self.tip_window = tw = Toplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_geometry("+%d+%d" % (x, y))

        bg_color = Style(app).lookup('Horizontal.TScale', 'background')  # app.current_theme
        fg_color = Style(app).lookup('TLabel', 'foreground')

        label = Label(tw, text=self.text, justify="left", background=bg_color, foreground=fg_color,
                      relief="solid", borderwidth=0.5, font=(f"{app.font_family}", f"{app.font_size}", "normal"))

        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tip_window
        self.tip_window = None
        if tw:
            tw.destroy()


class RCListbox(Listbox):
    """Listbox allowing right-click commands"""

    def __init__(self, parent, *args, **kwargs):
        Listbox.__init__(self, parent, *args, **kwargs)

        # add scrollbar to the right
        scrollbar = Scrollbar(parent)
        scrollbar.pack(side="right", fill="y")
        self.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.yview)

        self.popup_menu = Menu(self, tearoff=0)
        self.popup_menu.add_command(label="Delete", command=self.delete_selected)
        self.popup_menu.add_command(label="Select All", command=self.select_all)

        self.bind("<Button-3>", self.popup)
        self.bind("<<ListboxSelect>>", self.callback)

    def popup(self, event):
        try:
            self.popup_menu.tk_popup(event.x_root, event.y_root, 0)
        finally:
            self.popup_menu.grab_release()

    def delete_selected(self):
        for i in self.curselection()[::-1]:
            self.delete(i)
            print(f"Deleted listbox entry {i}")

    def select_all(self):
        self.selection_set(0, 'end')
        print(f"You have selected {len(self.curselection())} items")

    def callback(self, event):
        selection = event.widget.curselection()
        if selection:
            index = selection[0]
            data = event.widget.get(index)
            print(f"You selected index {index} with the value {data}")


def create_tooltip(widget, text):
    """
    Create tooltip for any widget.
    Example: create_tooltip(some_widget, text="Test Message")
    """
    tool_tip = ToolTip(widget)

    def enter(event):
        try:
            # add 1 space to beginning of each line and at the end, show tooltip
            tool_tip.showtip(" {}".format(" \n ".join(text.split("\n"))) if text.find("\n") != -1 else f" {text} ")
        except Exception as e:
            print(e)

    def leave(event):
        tool_tip.hidetip()

    widget.bind('<Enter>', enter)
    widget.bind('<Leave>', leave)


def restart_ui(obj):
    """Restart the application. Runtime environment is lost!"""
    python = sys.executable
    os.execl(python, python, *sys.argv)


class UI(ThemedTk):
    """
    Main UI Class
    - called from __name__ == '__main__'
    - access style via Style(app).lookup('TLabel', 'foreground') etc.
    - access other stuff via app.current_theme etc.
    - access children via self.children (dict) (self.children["!canvas"].children etc)
    - call dir(app) in debug
    """

    # ############################################################################################################### #
    # ########################################## UI INIT ############################################################ #
    # ############################################################################################################### #

    def __init__(self):
        global btn, lbl, ent, frm, var, oth, env

        # threadpool executor
        self.executor = ThreadPoolExecutor(max_workers=4)

        # read config
        self.cfg = ConfigParser()
        self.cfg.read("config.ini")

        ThemedTk.__init__(self, theme=self.cfg["style"]["theme"])

        # perform firstrun-check
        self.firstrun_check()

        # define class-wide variables
        self.current_tab = None  # current tab name (e.g. "Json")
        self.cal_widgets = None  # list with empty dict for each entry in file.json for widgets (Calibration tab)
        self.tab_widgets = []  # contains canvas, scrollbars and frames of tabs

        # set font
        self.default_font = font.nametofont("TkDefaultFont")
        self.font_family, self.font_size = self.cfg["style"]["font"].split()
        self.default_font.configure(family=self.font_family, size=int(self.font_size), weight=font.NORMAL)
        # self.option_add("*Font", "TkDefaultFont")

        # create a couple of default fonts
        self.font_default = f"{self.font_family} {int(self.font_size)} normal"
        self.font_bold = f"{self.font_family} {int(self.font_size)} bold"
        self.font_bold_underlined = f"{self.font_family} {int(self.font_size)} bold underlined"
        self.font_header = f"{self.font_family} {int(self.font_size) + 4} bold"
        self.font_subheader = f"{self.font_family} {int(self.font_size) + 2} bold"

        # create style for LabelFrames depending on current UI theme (call with style="Red.TLabelframe.Label")
        self.style_conf = Style()
        self.style_conf.configure('Red.TLabelframe.Label', font=self.font_header)
        self.style_conf.configure('Red.TLabelframe.Label', foreground=Style(self).lookup('TLabel', 'foreground'))
        self.style_conf.configure('Red.TLabelframe.Label', background=Style(self).lookup("Horizontal.TScale",
                                                                                         "background"))

        # define colors
        self.orange = "#ff5501"  # used as warning color

        # set up logger
        if self.cfg["general"]["logging"] == "True":
            self.enable_logger()

        # set title, icon
        self.title(f"Tkinter Template GUI")
        if platform.system() == "Windows":
            self.iconbitmap("static" + os.sep + "icon_dev.ico")

        # set window geometry
        pct = float(self.cfg["style"]["window_size"])
        self.window_size_x, self.window_size_y = int(self.winfo_screenwidth() * pct), int(
            self.winfo_screenheight() * pct)

        if pct == 1:
            self.wm_attributes("-fullscreen", "true")
        else:
            self.geometry(f"{self.window_size_x}x{self.window_size_y}")

        # build menu bar
        self.build_menu()

        # build bottom status bar & progress indicator
        self.status_bar = Frame(self)
        self.status_bar.pack(side="bottom", fill="x")
        lbl["status"] = Label(self.status_bar, text="Status: ")
        lbl["status"].pack(side="left", anchor="w", padx=5)
        oth["progress"] = Progressbar(self.status_bar, length=100, mode="determinate", orient="horizontal")
        oth["progress"].pack(side="right", anchor="e", padx=2, pady=2)

        # # build tabs root
        self.tab_root = Notebook(self)
        self.tab_root.rowconfigure(0, weight=1)
        self.tab_root.columnconfigure(0, weight=1)
        self.tab_root.bind("<<NotebookTabChanged>>", self.callback_tab_changed)

        # build notebook & tabs
        self.tab_database = Frame(self.tab_root, style="Black.TLabel", relief="sunken", borderwidth=2)  # Database
        self.tab_json = Frame(self.tab_root, style="Black.TLabel", relief="sunken", borderwidth=2)  # Json
        self.tab_debug = Frame(self.tab_root, style="Black.TLabel", relief="sunken", borderwidth=2)  # Debug
        self.tab_root.add(self.tab_database, text="Database")
        self.tab_root.add(self.tab_json, text="Json")
        self.tab_root.add(self.tab_debug, text="Debug")
        self.tab_root.pack(expand=1, fill="both")

        # build uis for different tabs
        self.build_database_ui()
        self.build_json_ui()
        self.build_debug_ui()

        # get console
        if platform.system() == "Windows":
            self.console = win32console.GetConsoleWindow()
            if self.cfg["general"]["console"] == "False":
                self.hide_console(overwrite=False)

    # *************************************************************************************************************** *
    # *************************************************************************************************************** *
    # ****************************************** UI BUILDING STARTS HERE ******************************************** *
    # *************************************************************************************************************** *
    # *************************************************************************************************************** *

    # ############################################################################################################### #
    # ########################################## TOP MENU ########################################################### #
    # ############################################################################################################### #
    def build_scrollable_frame(self, root_frame):
        """Builds a scrollable frame. Utilizes AutoScrollbar class.

        Parameters
        ---------
        root_frame : tk.Frame

        Returns
        -------
        canvas : tk.Canvas
        frame : tk.Frame

        Example
        -------
        To create a scrollable frame, execute the following code::

            root = self.tab_debug
            canvas, frame = self.build_scrollable_frame(root)

            some_label = Label(frame, text="Hey")
            some_label.pack()

            self.build_scrollable_frame_post(canvas, frame)
        """

        # # inner function
        def _on_mousewheel(event):
            tab_index = self.tab_root.index(self.tab_root.select())  # index of currently selected tab
            self.tab_widgets[tab_index]["canvas"].yview_scroll(int(-1 * (event.delta / 120)), "units")

        # define rootframe
        root = root_frame

        # append dict to tab_widgets to store widgets
        self.tab_widgets.append({})

        # create autoscrollbars
        self.tab_widgets[-1]["vert_scrollbar"] = AutoScrollbar(root)
        self.tab_widgets[-1]["vert_scrollbar"].grid(row=0, column=1, sticky="ns")
        self.tab_widgets[-1]["hor_scrollbar"] = AutoScrollbar(root, orient="horizontal")
        self.tab_widgets[-1]["hor_scrollbar"].grid(row=1, column=0, sticky="ew")

        # create scrolled canvas (highlightthickness removes white border, bg sets color to current theme background)
        self.tab_widgets[-1]["canvas"] = Canvas(root,
                                                yscrollcommand=self.tab_widgets[-1]["vert_scrollbar"].set,
                                                xscrollcommand=self.tab_widgets[-1]["hor_scrollbar"].set,
                                                bg=self._get_bg_color(),
                                                highlightthickness=0)
        self.tab_widgets[-1]["canvas"].grid(row=0, column=0, sticky="nsew")
        self.tab_widgets[-1]["vert_scrollbar"].config(command=self.tab_widgets[-1]["canvas"].yview)
        self.tab_widgets[-1]["hor_scrollbar"].config(command=self.tab_widgets[-1]["canvas"].xview)

        # make canvas expandable
        root.rowconfigure(0, weight=1)
        root.columnconfigure(0, weight=1)

        # create canvas content
        self.tab_widgets[-1]["frame"] = Frame(self.tab_widgets[-1]["canvas"])
        self.tab_widgets[-1]["frame"].rowconfigure(1, weight=1)
        self.tab_widgets[-1]["frame"].columnconfigure(1, weight=1)

        # bind mousewheel
        self.tab_widgets[-1]["frame"].bind_all("<MouseWheel>", _on_mousewheel)

        # return frame to pack with widgets; after UI building, call build_scrollable_frame_post()
        return self.tab_widgets[-1]["frame"]

    def build_scrollable_frame_post(self):
        """Supplementary function for build_scrollable_frame
        - After creating frame content, call this function to create canvas window, call update_idletasks and to
          configure canvas
        """
        self.tab_widgets[-1]["canvas"].create_window(0, 0, anchor="nw", window=self.tab_widgets[-1]["frame"])
        self.tab_widgets[-1]["frame"].update_idletasks()
        self.tab_widgets[-1]["canvas"].config(scrollregion=self.tab_widgets[-1]["canvas"].bbox("all"))

    def build_menu(self):
        """Build menu bar"""
        # create menu
        menubar = Menu(self)

        # ######### System menu
        systemmenu = Menu(menubar, tearoff=0)
        systemmenu.add_command(label="Connect to MongoDB", command=self.establish_db_connection)
        systemmenu.add_separator()
        systemmenu.add_command(label="Restart UI", command=partial(restart_ui, self))
        systemmenu.add_command(label="Exit UI", command=self.quit)

        menubar.add_cascade(label="System", menu=systemmenu)

        # ######### Config menu
        configmenu = Menu(menubar, tearoff=0)

        # submenu UI
        configmenu_ui = Menu(configmenu, tearoff=0)
        styles = sorted(self.themes)
        accepted_styles = ["adapta", "alt", "arc", "black", "blue", "breeze", "clam", "classic", "clearlooks",
                           "plastik", "ubuntu", "xpnative"]
        for style in styles:
            if style in accepted_styles:
                configmenu_ui.add_command(label=style, command=partial(self.change_style, style))

        # submenu MongoDB data
        configmenu_logins = Menu(configmenu, tearoff=0)
        configmenu_logins.add_command(label="Set MongoDB Username",
                                      command=partial(self.set_config_prompt, "mongodb", "user"))
        configmenu_logins.add_command(label="Set MongoDB Password",
                                      command=partial(self.set_config_prompt, "mongodb", "pass"))
        configmenu_logins.add_command(label="Set MongoDB Cluster",
                                      command=partial(self.set_config_prompt, "mongodb", "cluster"))

        # submenu logging
        configmenu_logging = Menu(configmenu, tearoff=0)
        configmenu_logging.add_command(label="Enable Logging", command=self.enable_logger)
        configmenu_logging.add_command(label="Disable Logging", command=self.disable_logger)
        configmenu_logging.add_command(label="Open Logfolder", command=partial(self.open_file, "logs"))

        # submenu console
        configmenu_console = Menu(configmenu, tearoff=0)
        configmenu_console.add_command(label="Enable Console", command=self.show_console)
        configmenu_console.add_command(label="Disable Console", command=self.hide_console)

        # submenu Window size
        configmenu_window = Menu(configmenu, tearoff=0)
        configmenu_window.add_command(label="25% Screensize", command=partial(self.set_screen_size, 0.25))
        configmenu_window.add_command(label="50% Screensize", command=partial(self.set_screen_size, 0.5))
        configmenu_window.add_command(label="75% Screensize", command=partial(self.set_screen_size, 0.75))
        configmenu_window.add_command(label="Fullscreen", command=partial(self.set_screen_size, 1))

        # submenu  Parameters
        configmenu_params = Menu(configmenu, tearoff=0)
        configmenu_params.add_command(label="Set json folder", command=self.set_json_folder)
        configmenu_params.add_command(label="Set json file", command=self.set_json_file)
        configmenu_params.add_command(label="Open file.json", command=self.open_parameter_path)

        # single actions in config menu
        configmenu.add_cascade(label="UI Theme", menu=configmenu_ui)
        configmenu.add_cascade(label="Window Size", menu=configmenu_window)
        configmenu.add_separator()
        configmenu.add_cascade(label="Logging", menu=configmenu_logging)
        configmenu.add_cascade(label="Console", menu=configmenu_console)
        configmenu.add_separator()
        configmenu.add_cascade(label="Credentials", menu=configmenu_logins)
        configmenu.add_cascade(label="JSON Settings", menu=configmenu_params)
        configmenu.add_command(label="Set Local User", command=self.set_local_username)
        configmenu.add_separator()
        configmenu.add_command(label="Show Configuration", command=partial(self.open_file, "config.ini"))

        menubar.add_cascade(label="Configuration", menu=configmenu)

        # ######### Help menu
        helpmenu = Menu(menubar, tearoff=0)

        # submenu additional_files
        helpmenu_additional_files = Menu(helpmenu, tearoff=0)
        for key, val in self.cfg["additional_files"].items():
            helpmenu_additional_files.add_command(label=key.title(), command=partial(self.open_file, val))

        # add single actions to help menu
        helpmenu.add_cascade(label="Additional files", menu=helpmenu_additional_files)
        helpmenu.add_separator()
        helpmenu.add_command(label="About...", command=self.ui_about_popup)

        menubar.add_cascade(label="Help", menu=helpmenu)

        # set menubar for root app
        self.config(menu=menubar)

    # ############################################################################################################### #
    # ########################################## STATUS TAB ######################################################### #
    # ############################################################################################################### #

    def build_database_ui(self):
        """Build status tab content. Gridlayout. Col0 = labels, Col1 = status, Col2 = buttons."""
        # create scrollable frame
        frame = self.build_scrollable_frame(self.tab_database)

        # create content
        lbl["status_header"] = Label(frame, text=f"Status Information", font=self.font_header)
        lbl["status_header"].grid(row=0, column=0, columnspan=3, padx=5, sticky="w")

        Separator(frame, orient="horizontal").grid(row=10, column=0, columnspan=99, pady=5, sticky="ew")

        # DB connection 12+
        lbl["db_connection_header"] = Label(frame, text="MongoDB connection", font=self.font_bold)
        lbl["db_connection_header"].grid(row=12, column=0, padx=5, sticky="w")
        var["db_connection"] = StringVar(value=f"No connection established")
        lbl["db_connection"] = Label(frame, textvariable=var["db_connection"])
        lbl["db_connection"].grid(row=12, column=1, padx=5, sticky="w")
        btn["db_connection"] = Button(frame, text="Connect", command=self.establish_db_connection)
        btn["db_connection"].grid(row=12, column=2, padx=5, sticky="w")

        # create canvas window, call update_idletasks, configure canvas
        self.build_scrollable_frame_post()

    # ############################################################################################################### #
    # ########################################## Json TAB #################################################### #
    # ############################################################################################################### #

    def build_json_ui(self):
        """Build Json tab content"""
        # create scrollable frame
        frame = self.build_scrollable_frame(self.tab_json)

        # create content
        lbl["json_header"] = Label(frame, text=f"Json Panel", font=self.font_header)
        lbl["json_header"].grid(row=0, column=0, columnspan=2, padx=5, sticky="w")
        Separator(frame, orient="horizontal").grid(row=1, column=0, columnspan=99, pady=5, sticky="ew")
        lbl["json_help_text"] = Label(frame, text="Write fields of the file.json file by entering values "
                                                  "and pressing enter. Might be linked to functions in the future"
                                                  " aswell (sending laser current changes automatically)")
        lbl["json_help_text"].grid(row=2, column=0, columnspan=2, padx=5, sticky="w")

        Separator(frame, orient="horizontal").grid(row=10, column=0, columnspan=99, pady=5, sticky="ew")

        # help / control stuff 11+
        lbl["json_configuration_header"] = Label(frame, text="Configuration", font=self.font_bold)
        lbl["json_configuration_header"].grid(row=11, column=0, padx=5, sticky="w")
        frm["json_configuration"] = Frame(frame)
        btn["json_set_json"] = Button(frm["json_configuration"], text="Load json file",
                                      command=self.set_json_file)

        var["json_overwrite_json"] = BooleanVar(value=self.cfg["json"]["json_overwrite"])
        oth["json_overwrite_json"] = Checkbutton(frm["json_configuration"],
                                                 variable=var["json_overwrite_json"],
                                                 text="Overwrite json",
                                                 command=partial(self.callback_cal_options, "overwrite_json"))
        var["json_send_on_enter"] = BooleanVar(value=self.cfg["json"]["json_callback"])
        oth["json_send_on_enter"] = Checkbutton(frm["json_configuration"],
                                                variable=var["json_send_on_enter"],
                                                text="Apply Callback",
                                                command=partial(self.callback_cal_options, "send_on_enter"))
        frm["json_configuration"].grid(row=11, column=1, padx=5, pady=2, sticky="w")
        btn["json_set_json"].pack(side="left")
        oth["json_overwrite_json"].pack(side="left", padx=2)
        oth["json_send_on_enter"].pack(side="left", padx=2)

        lbl["json_file_header"] = Label(frame, text="Current json file", font=self.font_bold)
        lbl["json_file_header"].grid(row=12, column=0, padx=5, pady=2, sticky="w")
        var["file.json"] = StringVar(value=f"{env['json_path']}")
        lbl["json_file"] = Label(frame, textvariable=var["file.json"])
        lbl["json_file"].grid(row=12, column=1, padx=5, pady=2, sticky="w")
        create_tooltip(lbl["json_file"], "Set via Configuration >  Parameters > Set file.json")

        lbl["json_folder_header"] = Label(frame, text="Json data folder", font=self.font_bold)
        lbl["json_folder_header"].grid(row=13, column=0, padx=5, pady=2, sticky="w")
        var["json_folder"] = StringVar(value=f"{self.cfg['json']['json_folder']}")
        lbl["json_folder"] = Label(frame, textvariable=var["json_folder"])
        lbl["json_folder"].grid(row=13, column=1, padx=5, pady=2, sticky="w")

        Separator(frame, orient="horizontal").grid(row=20, column=0, columnspan=99, pady=5, sticky="ew")

        # JSON parameters 21+
        frm["json_params"] = Frame(frame)
        frm["json_params"].grid(row=21, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        # built in build_json_ui_parameter_fields()
        # triggered from tab-handler or when loading a new file.json file while being in the tab

        # create canvas window, call update_idletasks, configure canvas
        self.build_scrollable_frame_post()

    def build_json_parameter_fields(self):
        """Builds parameter fields based on file.json file
        - Triggered from tab-handler or when loading a new file.json file while being in the tab Json
        """

        # return if no file.json file is selected
        if not env["json_path"]:
            return

        # clear all previous widgets in frame
        for widget in frm["json_params"].winfo_children():
            widget.destroy()

        # create list with empty dict for each entry in json file to store widgets
        self.cal_widgets = [{} for _ in range(len(env["json_content"].items()))]

        # iterate over current parameters read from json file
        for idx, (key, val) in enumerate(env["json_content"].items()):

            # create headers
            label = Label(frm["json_params"], text=key, font=self.font_bold)
            label.grid(row=idx, column=0, sticky="w")

            # color code certain headers
            label.config(foreground="red") if "Red" in key else 0
            label.config(foreground="green") if "Green" in key else 0
            label.config(foreground="blue") if "Blue" in key else 0

            # create top frame for widgets (some values are single items, some are lists etc)
            self.cal_widgets[idx]["top_frame"] = Frame(frm["json_params"])

            # check if value for current key is list
            if isinstance(val, list):

                # create sub_frame for current key
                self.cal_widgets[idx]["sub_frame"] = Frame(self.cal_widgets[idx]["top_frame"])

                # create list for current key
                self.cal_widgets[idx]["list"] = []

                # iterate over list elements
                for list_idx, list_val in enumerate(val):

                    # check if list contains anything but lists (= list with single values) (bools etc not covered)
                    if not isinstance(list_val, list):
                        self.cal_widgets[idx]["list"].append(Entry(self.cal_widgets[idx]["sub_frame"], width=20))
                        self.cal_widgets[idx]["list"][-1].grid(row=0, column=list_idx, padx=2)
                        self.cal_widgets[idx]["list"][-1].insert(0, list_val)
                        self.cal_widgets[idx]["list"][-1].bind("<Return>", partial(self.callback_cal, "list",
                                                                                   idx, key, val, list_idx))

                    # check if list contains nested lists
                    if isinstance(list_val, list):
                        self.cal_widgets[idx]["list"].append([])
                        for sub_list_idx, sub_list in enumerate(list_val):
                            self.cal_widgets[idx]["list"][-1].append(Entry(self.cal_widgets[idx]["sub_frame"],
                                                                           width=20))
                            self.cal_widgets[idx]["list"][-1][-1].grid(row=list_idx, column=sub_list_idx,
                                                                       padx=2, pady=2)
                            self.cal_widgets[idx]["list"][-1][-1].insert(0, sub_list)
                            self.cal_widgets[idx]["list"][-1][-1].bind("<Return>", partial(self.callback_cal,
                                                                                           "nested_list",
                                                                                           idx, key, val,
                                                                                           list_idx, sub_list_idx))

                # attach subframe to grid
                self.cal_widgets[idx]["sub_frame"].grid(row=idx, column=1, sticky="w", pady=2)

            # check if value for current key is a bool (has to be checked first, conflicts with int > elif necessary)
            if isinstance(val, bool):
                self.cal_widgets[idx]["boolvar"] = BooleanVar(value=val)
                self.cal_widgets[idx]["checkbutton"] = Checkbutton(self.cal_widgets[idx]["top_frame"],
                                                                   variable=self.cal_widgets[idx]["boolvar"],
                                                                   command=partial(self.callback_cal, "boolvar",
                                                                                   idx, key, val))

                self.cal_widgets[idx]["checkbutton"].grid(row=idx, column=1, padx=2, pady=2, sticky="w")

            # check if value for current key is a int or float (TODO: not isinstance(val, bool) ? just else ?)
            elif isinstance(val, int) or isinstance(val, float):
                self.cal_widgets[idx]["single_number"] = Entry(self.cal_widgets[idx]["top_frame"], width=20)
                self.cal_widgets[idx]["single_number"].grid(row=idx, column=1, padx=2, pady=2, sticky="w")
                self.cal_widgets[idx]["single_number"].insert(0, val)
                self.cal_widgets[idx]["single_number"].bind("<Return>", partial(self.callback_cal, "single_number",
                                                                                idx, key, val))

            # check if value for current key is a string
            if isinstance(val, str):
                self.cal_widgets[idx]["single_text"] = Entry(self.cal_widgets[idx]["top_frame"], width=20)
                self.cal_widgets[idx]["single_text"].grid(row=idx, column=1, padx=2, pady=2, sticky="w")
                self.cal_widgets[idx]["single_text"].insert(0, val)
                self.cal_widgets[idx]["single_text"].bind("<Return>", partial(self.callback_cal, "single_text",
                                                                              idx, key, val))

            # add separator below (TODO: limited by frame-size)
            Separator(self.cal_widgets[idx]["top_frame"], orient="horizontal").grid(row=999, column=0, columnspan=99,
                                                                                    pady=2, sticky="ew")

            # add top_frame to grid
            self.cal_widgets[idx]["top_frame"].grid(row=idx, column=1, pady=2, sticky="w")

        # refresh frame (scrollbar)
        frm["json_params"].update_idletasks()
        canvas = self.tab_json.children["!canvas"]
        canvas.config(scrollregion=canvas.bbox("all"))

    # ############################################################################################################### #
    # ########################################## DEBUG TAB ########################################################## #
    # ############################################################################################################### #

    def build_debug_ui(self):
        """Build user management tab content """
        # create scrollable frame
        frame = self.build_scrollable_frame(self.tab_debug)

        # create content
        Label(frame, text=f"Debug section", font=self.font_header).pack(anchor="w", padx=5)
        Separator(frame, orient="horizontal").pack(fill="x", pady=5)

        btn["test_statusbar"] = Button(frame, text="Test Statusbar", command=self.test_status_bar)
        btn["test_statusbar"].pack(anchor="w", padx=5, pady=2)

        btn["debug_btn"] = Button(frame, text="DEBUG", command=self.dummy_function)
        btn["debug_btn"].pack(anchor="w", padx=5, pady=2)

        btn["start_inf_loading"] = Button(frame, text="start infinite loading", command=self.start_infinite_loading)
        btn["start_inf_loading"].pack(anchor="w", padx=5, pady=2)

        btn["stop_inf_loading"] = Button(frame, text="stop infinite loading", command=self.stop_infinite_loading)
        btn["stop_inf_loading"].pack(anchor="w", padx=5, pady=2)

        create_tooltip(btn["test_statusbar"], "Test the progressbar and status messages with a timer")

        Separator(frame, orient="horizontal").pack(fill="x", pady=5)

        sub_frame = Frame(frame)
        for i in range(8):
            Button(sub_frame, text=f"Test {i + 1}").pack(side="left", padx=2)
        sub_frame.pack(anchor="w", padx=3)

        Separator(frame, orient="horizontal").pack(fill="x", pady=5)

        for i in range(20):
            Label(frame, text=f"Alot of labels {i}").pack(anchor="w")

        sub_frame = Frame(frame)
        for j in range(10):
            Label(sub_frame, text=f"More horizontal labels {j}").pack(side="left", anchor="w")
        sub_frame.pack(anchor="w")

        Separator(frame, orient="horizontal").pack(fill="x", pady=5)

        list_box = RCListbox(frame, selectmode="single")
        for i in range(15):
            list_box.insert("end", i)
        list_box.pack(padx=5, pady=5, fill="both", expand=True)

        # create canvas window, update tasks, configure canvas
        self.build_scrollable_frame_post()

    # *************************************************************************************************************** *
    # *************************************************************************************************************** *
    # ****************************************** FUNCTIONS START HERE *********************************************** *
    # *************************************************************************************************************** *
    # *************************************************************************************************************** *

    # ############################################################################################################### #
    # ########################################## UI / SYSTEM FUNCTIONS ############################################## #
    # ############################################################################################################### #

    def firstrun_check(self):
        """Check for config.ini and prompt for critical parameters"""
        if self.cfg["mongodb"]["user"] == "None":
            messagebox.showinfo(title="First run detected",
                                message=f"Welcome to the Tkinter Template GUI!\n\n"
                                        f"I will generate a new configuration file and ask you for some essential "
                                        f"information prior to run the GUI. You can change these settings later either "
                                        f"by editing the config.ini file or through the GUI (Configuration Menu).")

            self.set_config_prompt(section="mongodb", option="user", silent=True)
            self.set_config_prompt(section="mongodb", option="pass", silent=True)
            self.set_config_prompt(section="mongodb", option="cluster", silent=True)

    def callback_tab_changed(self, event):
        """Callback is triggered when changing Notebook tab"""
        tab_name = event.widget.tab("current")["text"]
        self.current_tab = tab_name

        if tab_name == "Json":
            self.build_json_parameter_fields()  # call build Json parameters
        # print(event)
        print(f"Changing to tab {tab_name}")

    def callback_cal_options(self, mode):
        if mode == "overwrite_json":
            change_val = var["json_overwrite_json"].get()
            self.write_cfg(section="json", option="json_overwrite", value=change_val)
        if mode == "send_on_enter":
            change_val = var["json_send_on_enter"].get()
            self.write_cfg(section="json", option="json_callback", value=change_val)

    def callback_cal(self, mode, idx, key, orig_value, list_idx=None, sub_list_idx=None, event=None):
        """Callback from Json - write to json & execute stuff."""
        if mode == "list":
            new_value = self.cal_widgets[idx][mode][list_idx].get()
            orig_value = orig_value[list_idx]
            return_text = f"Changing {key}[{list_idx}] from {orig_value} to {new_value}"

        elif mode == "nested_list":
            new_value = self.cal_widgets[idx]["list"][list_idx][sub_list_idx].get()
            orig_value = orig_value[list_idx][sub_list_idx]
            return_text = f"Changing {key}[{list_idx}][{sub_list_idx}] from {orig_value} to {new_value}"

        else:
            new_value = self.cal_widgets[idx][mode].get()
            return_text = f"Changing {key} from {orig_value} to {new_value}"

        # format from string to original value
        if isinstance(orig_value, bool):
            new_value = bool(new_value)
        elif isinstance(orig_value, int):
            new_value = int(new_value)
        elif isinstance(orig_value, float):
            new_value = float(new_value)
        elif isinstance(orig_value, str):
            new_value = str(new_value)

        # overwrite parameters in env
        if mode == "list":
            env["json_content"][key][list_idx] = new_value
        elif mode == "nested_list":
            env["json_content"][key][list_idx][sub_list_idx] = new_value
        else:
            env["json_content"][key] = new_value

        # overwrite json file
        if self.cfg["json"]["json_overwrite"] == "True":
            self.__write_json()
            return_text += " | .json updated"

        # TODO: program callback here to send commands
        if self.cfg["json"]["json_callback"] == "True":
            return_text += " | callback triggered"
            print(f"""### JSON callback triggered! Available arguments: ###
{'arg-name':<20} | {'current_value'}
{'------' * 6:}
{'mode':<20} | {mode}
{'idx':<20} | {idx}
{'key':<20} | {key}
{'orig_value':<20} | {orig_value}
{'list_idx':<20} | {list_idx}
{'sub_list_idx':<20} | {sub_list_idx}
""")
        self.change_status(return_text)

    def write_cfg(self, section=None, option=None, value=None, silent=False):
        """Overwrite config.ini

        Parameters
        ----------
        section : string
            section in config.ini
        option : string
            option (2nd level) in config.ini
        value : any
            value to write to specific [section][option]
        silent : bool
            If True, suppresses status update
        """
        if not isinstance(value, str):
            value = str(value)

        # write config
        self.cfg.set(section=section, option=option, value=value)
        with open("config.ini", "w") as __cfg:
            self.cfg.write(__cfg)

        # change status
        if silent == False:
            self.change_status(f"Updated config.ini: {section} | {option} | {value}")

    def set_local_username(self):
        """Update username"""
        username = simpledialog.askstring(title=f"Enter new user identification",
                                          prompt=f"Set username from '{self.cfg['general']['local_user']}' to: ")
        if username:
            self.write_cfg(section="general", option="local_user", value=username)

    def set_config_prompt(self, section=None, option=None, silent=False):
        """Set any parameter in config.ini via user input prompt
        - less descriptive than dedicated functions (e.g. set_login)

        Example
        -------
        ::

            self.set_any_parameter(section='mongodb', option='cluster')
        """

        if section not in self.cfg.sections():
            print(f"Section {section} does not exist in config.ini!")
            return

        if option not in self.cfg.options(section):
            print(f"Option {option} does not exist in section {section} in config.ini!")
            return

        # fetch current data
        old_val = self.cfg[section][option]

        # prompt new data
        val = simpledialog.askstring(title=f"Change config: {section} | {option}",
                                     prompt=f"Please enter new value for {section} | {option}:",
                                     initialvalue=old_val)

        # overwrite config if data is given
        if val:
            self.write_cfg(section=section, option=option, value=val, silent=silent)

    def set_json_file(self):
        """Set path to  file.json file"""
        # prompt for path to file.json
        path = filedialog.askopenfilename(filetypes=((" file.json file", "*.json"), ("All files", "*.")),
                                          title="Select file.json file",
                                          initialdir=self.cfg["json"]["json_folder"])

        if path:
            # update runtime env
            env["json_path"] = path

            # load json data into runtime env
            self.__load_json()

            # update status
            self.change_status(status=f"Set parameters path (runtime env): {path}")

            # change StringVar for display
            var["file.json"].set(value=env['json_path'])

            # if currently in tab Json, build parameter fields
            if self.current_tab == "Json":
                self.build_json_parameter_fields()

    def open_parameter_path(self):
        """Necessary because if path changes, old path is still bound to button"""
        self.open_file(env["json_path"])

    def set_json_folder(self, silent=False):
        """Set folder for json files

         Parameters
         ----------
         silent : bool
            If True, suppresses status update in UI, force enforces prompt"""
        if self.cfg["json"]["json_folder"] == "None":
            init_dir = os.path.realpath("\\")
        else:
            init_dir = self.cfg["json"]["json_folder"]

        path = filedialog.askdirectory(title="Select folder containing json files", initialdir=init_dir)

        if path:
            self.write_cfg(section="json", option="json_folder", value=path, silent=silent)
            if not silent:
                var["json_folder"].set(path)

    def __load_json(self):
        """Load a file.json file into env["json_path"]
        - after setting the parameter path with set_parameter_path
        - or during open_connection when an EEPROM id is available
          (open_connection has to write path into env["json_path"]
        """
        with open(env["json_path"], "r") as f:
            env["json_content"] = json.load(f)

    def __write_json(self):
        """Overwrite current file.json"""
        with open(env["json_path"], 'w', encoding='utf-8') as f:
            json.dump(env["json_content"], f, ensure_ascii=False, indent=4, separators=None)

    def open_file(self, filename):
        """Try to open a local file

        Parameters
        ----------
        filename : string
            Path to the file to open via os.startfile()"""
        try:
            os.startfile(filename)
            self.change_status(f"Opened {filename}")
        except Exception as e:
            print(e)
            self.change_status(f"Failed to open {filename}", warning=True)

    def disable_logger(self):
        """Disable logging"""
        if self.cfg["general"]["logging"] == "True":
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
            self.write_cfg(section="general", option="logging", value="False")
            print("Disabled logging")
            self.change_status("Disabled logging")
        else:
            pass

    def enable_logger(self):
        """Enable logging"""
        if not os.path.isdir("logs"):
            os.mkdir("logs")

        # tmp = f"logs{os.sep}out{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
        sys.stdout = Logger(sys.stdout)
        sys.stderr = Logger(sys.stderr)

        if self.cfg["general"]["logging"] == "True":
            pass
        else:
            self.write_cfg(section="general", option="logging", value="True")
            print("Enabled logging")
            self.change_status("Enabled logging")

    def ui_about_popup(self):
        """Informative popup (about)"""
        messagebox.showinfo(title="About  Admin GUI", message=f""" Admin GUI {ui_version}
--------------------------------------------
Author:   Matthias Ley
Created:  12.09.2021
Email:    matthias@leysolutions.com
--------------------------------------------
Optimized for Python 3.7, Windows 10 64-bit
\u00A9 leysolutions 2021
""")

    def change_status(self, status=None, warning=None, error=None):
        """Change status text in bottom bar

        Parameters
        ----------
        status : string
            Status text to display in the status bar
        warning : bool
            If True, highlights the status text in orange
        error : bool
            If True, highlights the status text in red and puts the text to bold"""
        lbl["status"].config(text=f"Status: {status}")
        if warning:
            lbl["status"].config(foreground=self.orange, font=f"{self.font_family} 9 normal")  # orange
        elif error:
            lbl["status"].config(foreground="red", font=f"{self.font_family} 9 bold")
        else:
            lbl["status"].config(foreground="", font=f"{self.font_family} 9 normal")

        print(status)

    def update_progress(self, value):
        """Updates progress level of progressbar

        Parameters
        ----------
        value : int
            Value to update progress bar to, ranging from 0 to 100"""
        if value not in range(0, 101):
            return

        oth["progress"]["value"] = value
        self.update()

    def change_style(self, style):
        """Change current GUI style

        Parameters
        ----------
        style : string
            A list of styles can be retrieved via self.get_themes()"""
        self.set_theme(style)

        # overwrite cfg, restart UI
        self.write_cfg(section="style", option="theme", value=style)
        restart_ui(self)

    def hide_console(self, overwrite=True):
        """Hide the python console

        Parameters
        ----------
        overwrite : bool
            Set to True to overwrite config.ini for a permanent change"""
        if platform.system() == "Windows":
            win32gui.ShowWindow(self.console, win32con.SW_HIDE)
            if overwrite:
                self.write_cfg(section="general", option="console", value="False")

    def show_console(self):
        """Show the python console"""
        if platform.system() == "Windows":
            win32gui.ShowWindow(self.console, win32con.SW_SHOW)
            self.write_cfg(section="general", option="console", value="True")

    def set_screen_size(self, pct=0.5):
        """Set window size based on percentage of screen size

        Parameters
        ----------
        pct : float
            Set size of GUI window to percentage of screen size"""
        self.window_size_x, self.window_size_y = int(self.winfo_screenwidth() * pct), int(
            self.winfo_screenheight() * pct)

        if pct == 1:
            self.wm_attributes("-fullscreen", "true")
        else:
            if self.wm_attributes("-fullscreen") == 1:
                self.wm_attributes("-fullscreen", "false")
            self.geometry(f"{self.window_size_x}x{self.window_size_y}")

        self.write_cfg(section="style", option="window_size", value=pct)

    def start_infinite_loading(self):
        """Supplementary function for loading"""
        oth["progress"].config(mode="indeterminate")
        oth["progress"].start(10)

    def stop_infinite_loading(self):
        """Supplementary function for loading"""
        oth["progress"].stop()
        oth["progress"].config(mode="determinate")

    def loading(self, callback_function):
        """Infinite loading animation thread; No returns possible

        Parameters
        ----------
        callback_function : function
            Loading will be active until this handed-over function is finished

        Example
        -------
        ::

            self.loading(callback)
        """

        def __load(thread):
            # start animation
            self.start_infinite_loading()

            # loop while thread is working
            while thread.running():
                time.sleep(0.5)

            # stop loading animation when thread is done
            self.stop_infinite_loading()

        main_thread = self.executor.submit(callback_function)
        self.executor.submit(__load, main_thread)

    # ############################################################################################################### #
    # ########################################## TEST/DEBUG FUNCTIONS ############################################### #
    # ############################################################################################################### #

    def dummy_function(self):
        """Dummy test function"""
        print("DBG dummy_function")
        # print("FRAMESIZE",
        #       self.children["!canvas"].children["!frame"].winfo_width(),
        #       self.children["!canvas"].children["!frame"].winfo_height()
        #       )
        # fonts = list(font.families())
        # fonts.sort()
        # print(fonts)
        # print(self.default_font)
        bg_color = Style(self).lookup("Horizontal.TScale", "background")
        fg_color = Style(self).lookup('TLabel', 'foreground')
        # bg_color = self._get_bg_color()
        print(bg_color)
        print(fg_color)
        oth["progress"].config(mode="indeterminate")
        oth["progress"].start(10)

    def test_status_bar(self):
        """Debug function to test status bar"""
        print("DBG test_status_bar")
        tmp = 0
        while tmp <= 100:
            # warnings
            number = random.randrange(3)
            if number == 0:
                self.change_status("Normal")
            if number == 1:
                self.change_status("Warning", warning=True)
            if number == 2:
                self.change_status("Error", error=True)

            # progressbar
            self.update_progress(value=tmp)
            tmp += 5
            time.sleep(0.1)

    # ############################################################################################################### #
    # ########################################## LIBRARY-UI CALLBACK FUNCTIONS ###################################### #
    # ############################################################################################################### #

    def establish_db_connection(self):
        """Establish a database connection and store db object in env["db"].
        - Launches thread to establish DB connection so GUI is not frozen (callback)
        - Thread result indicates when infinite loading starts / stops (loading)
        """
        self.change_status(f"Establishing connection to MongoDB ..", warning=True)

        def callback():
            """Main thread"""
            # label
            var["db_connection"].set(f"Establishing DB connection ..")
            lbl["db_connection"].config(foreground=self.orange)

            create_tooltip(lbl["db_connection"], "Connecting ..")

            try:
                # set up db connection
                client = MongoClient(f"mongodb+srv://{self.cfg['mongodb']['user']}:{self.cfg['mongodb']['pass']}"
                                     f"@{self.cfg['mongodb']['cluster']}.mongodb.net/?retryWrites=true&w=majority")
                # validate connection
                db_info = client.server_info()
            except pymongo_errors.ConfigurationError:
                cluster = self.cfg["mongodb"]["cluster"]
                self.change_status(f"DB connection failed - wrong cluster? ({cluster})", error=True)
                print(f"DB connection failed - wrong cluster? ({cluster})")
                var["db_connection"].set(f"DB connection failed - wrong cluster? ({cluster})")
                lbl["db_connection"].config(foreground="red")
                create_tooltip(lbl["db_connection"], "Set via Configuration > Credentials > Set MongoDB Cluster")
            except pymongo_errors.OperationFailure:
                self.change_status(f"DB connection failed - wrong credentials", error=True)
                print("DB connection failed - wrong credentials")
                var["db_connection"].set(f"DB connection failed - wrong credentials")
                lbl["db_connection"].config(foreground="red")
                create_tooltip(lbl["db_connection"], "Set via Configuration > Credentials > Set MongoDB Login")
            except pymongo_errors.ServerSelectionTimeoutError:
                ip = get("https://api.ipify.org").text
                self.change_status(f"DB connection failed - IP whitelisted? ({ip})", error=True)
                print(f"DB connection failed - IP whitelisted? ({ip})")
                var["db_connection"].set(f"DB connection failed - IP whitelisted? ({ip})")
                lbl["db_connection"].config(foreground="red")
                create_tooltip(lbl["db_connection"], "Contact DB Administrator")

            # set runtime env
            env["db"] = client

            # build tooltip description
            tmp = ""
            for k, v in db_info.items():
                if isinstance(v, dict):
                    tmp += f"{k}\n"
                    for k_sub, v_sub in v.items():
                        if not isinstance(v_sub, str):
                            tmp += f"\t{k_sub}\t{v_sub}"
                            continue
                        while len(str(v_sub)) >= 100:
                            tmp += f"\t{k_sub}\t{v_sub[:100]}\n"
                            v_sub = v_sub[100:]
                            if len(str(v_sub)) <= 100:
                                break
                        else:
                            tmp += f"\t{k_sub}\t{v_sub}\n"
                else:
                    tmp += f"{k}\t{v}\n"

            # set status
            var["db_connection"].set(f"Established | DB V.{db_info['version']}")
            lbl["db_connection"].config(foreground="green")
            self.change_status(f"DB connection established (V {db_info['version']})")
            create_tooltip(lbl["db_connection"], str(tmp))

            return "OK"

        # start thread & initiate loading
        self.loading(callback)


if __name__ == '__main__':
    """ Boilerplate code. Creates default config.ini, queries CI/CDs from environmental variables, launches UI """
    # create default config.ini on first start
    if not os.path.isfile("config.ini"):
        print("No config.ini detected. Loading default configuration ..")
        default_ini = f"""[general]
local_user = {getpass.getuser()}
logging = False
console = True

[style]
theme = default
font = Barlow 10
window_size = 0.75

[json]
json_folder = None
json_overwrite = True
json_callback = False

[mongodb]
user = None
pass = None
cluster = cluster0.12345
db_tools = None

[webserver]
user = None
pass = None

[additional_files]
some_link = https://www.google.at/
"""

        with open("config.ini", "w") as cfg:
            cfg.write(default_ini)

    # detect TRAVIS CI
    if "TEAMCITY_JRE" in os.environ or "TRAVIS" in os.environ:
        print("UI instance canceled - mainloop avoided")
        # app = UI()
        # app.update()
        # app.update_idletasks()
        # app.after(100, app.destroy())
    else:
        app = UI()
        app.mainloop()

