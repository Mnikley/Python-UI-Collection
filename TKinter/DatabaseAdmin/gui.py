"""
Connect to RPi databases (PostgreSQL, MongoDB) and manage them

Created: 17.04.2021
Updated: 13.05.2022
Author: Matthias Ley
"""

from tkinter import ttk, simpledialog, messagebox, StringVar, Listbox, Scrollbar, Toplevel, BooleanVar
from tkinter.ttk import Entry, Label, Button, Frame, Checkbutton
from tkinter.constants import HORIZONTAL
import tkinter
from functools import partial
import time
import os
import tempfile
from concurrent.futures import ThreadPoolExecutor
from configparser import ConfigParser

import psycopg2
from pymongo import MongoClient

gui_version = "1.3"

""" ###################################################################################################################
############################### Dictionaries for main classes (PostgreSQLTab, MongoDBTab) ############################# 
################################################################################################################### """
psql = {"btns": {},
        "lbls": {},
        "ents": {},
        "frms": {},
        "vars": {},
        "oths": {},
        "connection": None}

mongo = {"btns": {},
         "lbls": {},
         "ents": {},
         "frms": {},
         "vars": {},
         "oths": {},
         "progress": 0,
         "conn": None,
         "db": None}

""" ###################################################################################################################
############################################ Threadpool executor ###################################################### 
################################################################################################################### """
executor = ThreadPoolExecutor(max_workers=4)


""" ###################################################################################################################
########################################## Supplementary classes ###################################################### 
################################################################################################################### """


class DialogUpdatePSQLTable(simpledialog.Dialog):
    """Supplementary class used by PostgreSQL.update_table() to enter multiple fields in popup"""

    def __init__(self, parent, title, table, content, headers):
        """init"""
        # custom arguments
        self.table = table
        self.content = content
        self.headers = headers
        self.prim_key = headers[0]

        # class vars
        self.ents = {}

        # forward default arguments to init
        simpledialog.Dialog.__init__(self, parent, title)

    def listbox_event(self, event):
        """Listbox click event"""
        selection = None
        if event.widget.curselection():
            selection = event.widget.get(event.widget.curselection()[0])

        # delete all entries, insert data from selection
        if selection:
            for col_entry, col_data in zip(self.ents, selection):
                self.ents[col_entry].configure(state="normal")
                self.ents[col_entry].delete(0, "end")
                if col_data:
                    self.ents[col_entry].insert(0, col_data)
                    if col_entry == self.prim_key:
                        self.ents[col_entry].configure(state="disabled")

    def body(self, master):
        """Body of popup"""
        # header for listbox
        Label(master, text=" | ".join(self.headers)).grid(row=0, column=0, columnspan=2, padx=2, pady=2)

        # scrollable listbox inside a frame
        frame = Frame(master)
        frame.grid(row=1, column=0, columnspan=2, padx=2, pady=2)

        # scrollbars
        v_scrollbar = Scrollbar(frame, orient="horizontal")
        v_scrollbar.pack(side="bottom", fill="x")
        h_scrollbar = Scrollbar(frame, orient="vertical")
        h_scrollbar.pack(side="right", fill="y")

        # # create listbox, insert values from self.content
        listbox_width = max([len("".join(str(f))) for f in self.content]) if self.content else 10
        listbox_height = max(min(len(self.content), 10), 5) if self.content else 4
        self.listbox = Listbox(frame, width=listbox_width, height=listbox_height)
        self.listbox.insert(0, *self.content)
        self.listbox.pack(side="top", fill="x", expand=True)

        # config scrollbar and listbox
        v_scrollbar.config(command=self.listbox.xview)
        h_scrollbar.config(command=self.listbox.yview)
        self.listbox.config(xscrollcommand=v_scrollbar.set,
                            yscrollcommand=h_scrollbar.set)

        # bind click-event to listbox
        self.listbox.bind("<<ListboxSelect>>", self.listbox_event)

        # separator
        ttk.Separator(master, orient=HORIZONTAL).grid(row=2, column=0, columnspan=99, sticky="ew", pady=10)

        # iterate over column names to create entries + labels for actual modification
        # calculate maximum possible length of a field, set as default width for entries
        max_allowed_entry_width = max(len(str(elem)) for row in self.content for elem in row) + 10 \
            if self.content else 10  # 10 is a buffer
        # create widgets in loop, store in self.ents with column header name as key
        for idx, column in enumerate(self.headers):
            Label(master, text=f"{column}:").grid(row=3+idx, column=0, padx=2)
            self.ents[column] = Entry(master, width=max_allowed_entry_width)
            self.ents[column].grid(row=3+idx, column=1, padx=2)

    def ok(self, event=None):
        """Overrides ok method to only accept integers for self.table_id"""

        # if a column id exists in headers, verify the entry
        if "id" in [x.lower() for x in self.headers]:
            error = None
            try:
                int(self.ents["id"].get())
                # check if entered ID exists in self.content column for id
                if int(self.ents["id"].get()) not in [f[self.headers.index("id")] for f in self.content]:
                    error = "ID doesnt exist!"
            except Exception as e:
                print(e)
                error = "Only int allowed!"

            # halt on error, write error text to entry, focus and select text
            if error:
                self.ents["id"].delete(0, "end")
                self.ents["id"].insert(0, error)
                self.ents["id"].focus()
                self.ents["id"].select_range(0, "end")
                return

        # # if a column entry is empty, focus and return
        # for column in self.headers:
        #     if self.ents[column].get() == "":
        #         self.ents[column].focus()
        #         return

        # not sure what this does honestly, comes from original class
        if not self.validate():
            self.initial_focus.focus_set()  # put focus back
            return

        self.withdraw()
        self.update_idletasks()

        try:
            self.apply()
        finally:
            self.cancel()

    def apply(self):
        """Hand over results"""
        # iterate over text in entries, current listbox selection and headers(column names) to find modified data
        modified_data = {}

        # check if something is selected in listbox
        try:
            selection = self.listbox.get(self.listbox.curselection())
        # if not, try to find per ID entered
        except Exception as e:
            selection = [f for f in self.listbox.get(0, "end") if str(f[0]) == self.ents[self.prim_key].get()][0]

        for entry, orig_value, header in zip(self.ents, selection, self.headers):
            # if entry value does not match original value, append to dict by header(column name)
            if self.ents[entry].get() != orig_value:
                # if column is id and values match as ints, continue
                if header == "id":
                    if int(self.ents[entry].get()) == orig_value:
                        continue
                modified_data[header] = self.ents[entry].get()

        self.result = {
            "prim_key": (self.prim_key, self.ents[self.prim_key].get()),
            "orig_values": selection,
            "mod_values": modified_data
        }


class DialogDeleteFromPSQLTable(simpledialog.Dialog):
    """Supplementary class used by PostgreSQL.delete_from_table() to delete certain IDs from table"""

    def __init__(self, parent, title, table, content, headers):
        """table and content are custom arguments handed over from GUI class"""
        # custom arguments
        self.table = table
        # content_mod = []
        # for line in content:
        #     content_mod.append("   ".join([f"{col}" for col in line if type(col) in [int, str] and col != ""]))
        self.content = content
        self.headers = headers

        # forward default arguments to init
        simpledialog.Dialog.__init__(self, parent, title)

    def body(self, master):
        """Body of popup"""
        # header for listbox
        Label(master, text=" | ".join(self.headers)).grid(row=0, column=0, columnspan=2, padx=2, pady=2)

        # scrollable listbox inside a frame
        frame = Frame(master)
        frame.grid(row=1, column=0, columnspan=2, padx=2, pady=2)

        # scrollbars
        v_scrollbar = Scrollbar(frame, orient="horizontal")
        v_scrollbar.pack(side="bottom", fill="x")
        h_scrollbar = Scrollbar(frame, orient="vertical")
        h_scrollbar.pack(side="right", fill="y")

        # # create listbox, insert values from self.content
        listbox_width = max([len("".join(str(f))) for f in self.content]) if self.content else 10
        listbox_height = max(min(len(self.content), 10), 5) if self.content else 4
        self.listbox = Listbox(frame, selectmode="multiple", width=listbox_width, height=listbox_height)
        self.listbox.insert(0, *self.content)
        self.listbox.pack(side="top", fill="x", expand=True)

        # config scrollbar and listbox
        v_scrollbar.config(command=self.listbox.xview)
        h_scrollbar.config(command=self.listbox.yview)
        self.listbox.config(xscrollcommand=v_scrollbar.set,
                            yscrollcommand=h_scrollbar.set)

        # separator
        ttk.Separator(master, orient=HORIZONTAL).grid(row=2, column=0, columnspan=99, sticky="ew", pady=10)

        # Entry to hand over values
        Label(master, text="Delete by Value:").grid(row=3, column=0, padx=2)
        self.values = Entry(master)
        self.values.grid(row=3, column=1, padx=2)

    def apply(self):
        """Hand over results"""
        selected_ids = []
        for idx in self.listbox.curselection():
            selected_ids.append(self.listbox.get(idx))

        self.result = {
            "selected_ids": selected_ids,
            "passed_values": self.values.get()
        }


class CreatePSQLTable(simpledialog.Dialog):
    """Supplementary class used by PostgreSQL.create_table() to read available data types and create a new table"""

    def __init__(self, parent, title, data_types):
        """data_types is a curstom argument handed over from GUI class"""
        # custom arguments
        self.data_types = data_types

        # predefinitions
        self.sql = StringVar()
        self.lbls = {}
        self.lbls_dtypes = {}
        self.ents = {}
        self.btns = {}
        self.table_name = None

        # forward default arguments to init
        simpledialog.Dialog.__init__(self, parent, title)

    def entry_event(self, current_idx, event):
        value = event.widget.get()
        print(f"ID: {current_idx} VAL: {value}")

    def listbox_event(self, event):
        selection = event.widget.curselection()
        if selection:
            data = event.widget.get(selection[0])

        # get stringvar, append new value to it (first column)
        current_val = self.sql.get()
        self.sql.set(f"{current_val} {data}")  # obsolete?

        current_idx = len(self.lbls)

        # label - col #
        self.lbls[current_idx] = Label(self.frame, text=current_idx)
        self.lbls[current_idx].grid(row=current_idx, column=0, padx=2)
        # entry for name
        self.ents[current_idx] = Entry(self.frame)
        self.ents[current_idx].grid(row=current_idx, column=1, padx=2)
        self.ents[current_idx].bind("<Return>", partial(self.entry_event, current_idx))
        # TODO: callback of some sort

        # label - data type
        self.lbls_dtypes[current_idx] = Label(self.frame, text=data)
        self.lbls_dtypes[current_idx].grid(row=current_idx, column=2, padx=2)

        # button - remove
        self.btns[current_idx] = Button(self.frame, text="Remove", command=partial(self.remove_entry, current_idx))
        self.btns[current_idx].grid(row=current_idx, column=3, padx=2)

    def remove_entry(self, current_idx):
        """Remove entry from listbox"""
        # remove entry from dicts
        self.lbls[current_idx].destroy()
        self.lbls_dtypes[current_idx].destroy()
        self.ents[current_idx].destroy()
        self.btns[current_idx].destroy()

    def body(self, master):
        """Body of popup"""
        # Table name on top
        Label(master, text="Table Name:", font=("arial", 9, "bold")).grid(row=0, column=0, padx=2)
        self.table_name = Entry(master, width=40)
        self.table_name.grid(row=0, column=1, padx=2)

        # separator
        ttk.Separator(master, orient=HORIZONTAL).grid(row=1, column=0, columnspan=99, sticky="ew", pady=10)

        # headers for listbox
        Label(master, text="Select a datatype to add as a column:", font=("arial", 9, "bold")).\
            grid(row=3, column=0, columnspan=2, padx=2, pady=2)
        Label(master, text="type | description").grid(row=4, column=0, columnspan=2, padx=2, pady=2)

        # scrollable listbox inside a frame
        frame = Frame(master)
        frame.grid(row=5, column=0, columnspan=2, padx=2, pady=2)
        self.listbox = Listbox(frame, selectmode="single", width=max([len("".join(str(f))) for f in self.data_types]))
        self.listbox.pack(side="left", fill="y")
        scrollbar = Scrollbar(frame, orient="vertical")
        scrollbar.config(command=self.listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.listbox.config(yscrollcommand=scrollbar.set)

        # bind click event
        self.listbox.bind("<<ListboxSelect>>", self.listbox_event)

        # insert values from self.content to Listbox
        self.listbox.insert(0, *self.data_types)

        # separator
        ttk.Separator(master, orient=HORIZONTAL).grid(row=6, column=0, columnspan=99, sticky="ew", pady=10)

        # frame for widgets created by listbox by selecting data types
        # header for frame
        Label(master, text="Col # | name | data type").grid(row=7, column=0, columnspan=2, padx=2, pady=2, sticky="W")
        self.frame = Frame(master)
        self.frame.grid(row=8, column=0, columnspan=2, padx=2, pady=2)

        ttk.Separator(master, orient=HORIZONTAL).grid(row=9, column=0, columnspan=99, sticky="ew", pady=10)

        # Entry to hand over values
        self.sql_label = Label(master, textvariable=self.sql)
        self.sql_label.grid(row=10, column=0, padx=2)

    def buttonbox(self):
        """override default function to get rid of <Return> binding"""

        box = Frame(self)

        w = Button(box, text="OK", width=10, command=self.ok, default="active")
        w.pack(side="left", padx=5, pady=5)
        w = Button(box, text="Cancel", width=10, command=self.cancel)
        w.pack(side="left", padx=5, pady=5)

        # self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)

        box.pack()

    def cancel(self, event=None):
        print("Table creation canceled")
        self.destroy()

    def ok(self, event=None):
        """Hand over results"""

        table_name = self.table_name.get()
        if table_name == "":
            messagebox.showerror("Error", "Please enter a table name.")
            return

        ret_sql = f"CREATE TABLE {table_name} ("
        ret_sql += ", ".join([f"{self.ents[_c].get()} {self.lbls_dtypes[_d].cget('text')}"
                              for _c, _d in zip(self.ents, self.lbls_dtypes)])
        ret_sql += ")"

        self.result = ret_sql
        self.destroy()


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
        x += self.widget.winfo_rootx() + 35
        y += cy + self.widget.winfo_rooty() + 20
        self.tip_window = tw = Toplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_geometry("+%d+%d" % (x, y))
        label = Label(tw, text=self.text, justify="left", relief="solid", borderwidth=1)
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tip_window
        self.tip_window = None
        if tw:
            tw.destroy()


""" ###################################################################################################################
######################################### Supplementary functions ##################################################### 
################################################################################################################### """


def read_config(filename="config.ini", section=None):
    """Parse DB config from .ini file"""
    parser = ConfigParser()
    if not os.path.isfile(filename):
        print(f"Couldnt find {os.path.abspath(filename)}. Creating default config ..")
        with open(filename, "w") as f:
            f.write("""[postgresql]
server=0.0.0.0
port=5432
user=postgresadmin
pass=123
sslmode=require

[mongodb]
server=0.0.0.0
port=27017
user=mongoadmin
pass=123
""")

    ret = parser.read(filename)
    print("Parsed:", ret)

    content = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            content[param[0]] = param[1]
    else:
        raise Exception(f'Section {section} not found in {filename}')

    return content


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


""" ###################################################################################################################
################################################ PSQL main class ###################################################### 
################################################################################################################### """


class PostgreSQLTab(ttk.Frame):
    """Tab for PSQL Control"""

    def __init__(self, parent, *args, **kwargs):
        global psql
        ttk.Frame.__init__(self, parent, *args, **kwargs)
        self.root = parent
        self.show_output = BooleanVar(value=False)
        self.build_psql_tab()
        self.disable_ui()

    """ ########################################### BUILD UI ########################################### """

    def build_psql_tab(self):
        """Build PSQl Tab"""

        # INIT (10+) ############################################################################################ #
        psql["lbls"]["init_title"] = Label(self, text="Initialize", font=("arial", 10, "bold"))
        psql["lbls"]["init_title"].grid(row=10, column=0, padx=5, sticky="W")
        psql["frms"]["init"] = Frame(self)
        psql["btns"]["init"] = Button(psql["frms"]["init"], text="Connect", command=self.init_connection)
        # psql["btns"]["close"] = Button(psql["frms"]["init"], text="Close", command=self.close_connection)
        psql["btns"]["get_version"] = Button(psql["frms"]["init"], text="Info", width=4,  command=self.get_info)
        psql["btns"]["rollback"] = Button(psql["frms"]["init"], text="Rollback", width=8,  command=self.rollback_db)
        psql["btns"]["open_cfg"] = Button(psql["frms"]["init"], text="CFG", width=4,
                                          command=partial(os.startfile, "database.ini"))
        # psql["btns"]["get_tables"] = Button(psql["frms"]["init"], text="Tables in DB", command=self.get_all_tables)
        # psql["btns"]["get_dbs"] = Button(psql["frms"]["init"], text="List DBs", command=self.get_all_dbs)

        psql["frms"]["init"].grid(row=11, column=0, padx=5, sticky="w", columnspan=3)
        psql["btns"]["init"].pack(side="left", padx=2)
        psql["btns"]["get_version"].pack(side="left", padx=2)
        psql["btns"]["rollback"].pack(side="left", padx=2)
        psql["btns"]["open_cfg"].pack(side="left", padx=2)

        ttk.Separator(self, orient=HORIZONTAL).grid(row=19, column=0, columnspan=99, sticky="ew", pady=10)

        # TABLE OPERATIONS (20+) ################################################################################## #
        psql["lbls"]["get_info_title"] = Label(self, text="Operations", font=("arial", 10, "bold"))
        psql["lbls"]["get_info_title"].grid(row=20, column=0, padx=5, sticky="W")

        # combobox to select database and button to create new database
        psql["frms"]["select_db"] = Frame(self)
        psql["frms"]["select_db"].grid(row=21, column=0, padx=5, pady=5, sticky="W", columnspan=3)
        psql["lbls"]["select_db_title"] = Label(psql["frms"]["select_db"], text="Select DB:")
        psql["lbls"]["select_db_title"].grid(row=0, column=0, padx=2, pady=2, sticky="W")
        psql["oths"]["select_db"] = ttk.Combobox(psql["frms"]["select_db"])
        psql["oths"]["select_db"].bind("<<ComboboxSelected>>", self.change_db)
        psql["oths"]["select_db"]["state"] = "readonly"
        psql["oths"]["select_db"].grid(row=0, column=1, padx=2, pady=2, sticky="W")
        psql["btns"]["select_db"] = Button(psql["frms"]["select_db"], text="Create DB", command=self.create_db)
        psql["btns"]["select_db"].grid(row=0, column=2, padx=2, pady=2, sticky="W")
        psql["btns"]["drop_db"] = Button(psql["frms"]["select_db"], text="Drop DB", command=self.drop_db)
        psql["btns"]["drop_db"].grid(row=0, column=3, padx=2, pady=2, sticky="W")

        # combobox to select table and button to create a new table
        psql["lbls"]["select_table_title"] = Label(psql["frms"]["select_db"], text="Select Table:")
        psql["lbls"]["select_table_title"].grid(row=1, column=0, padx=2, pady=2, sticky="W")
        psql["oths"]["select_table"] = ttk.Combobox(psql["frms"]["select_db"])
        psql["oths"]["select_table"].bind("<<ComboboxSelected>>", self.change_table)
        psql["oths"]["select_table"]["state"] = "readonly"
        psql["oths"]["select_table"].grid(row=1, column=1, padx=2, pady=2, sticky="W")
        psql["btns"]["select_table"] = Button(psql["frms"]["select_db"], text="Create Table", command=self.create_table)
        psql["btns"]["select_table"].grid(row=1, column=2, padx=2, pady=2, sticky="W")
        psql["btns"]["drop_table"] = Button(psql["frms"]["select_db"], text="Drop Table", command=self.drop_table)
        psql["btns"]["drop_table"].grid(row=1, column=3, padx=2, pady=2, sticky="W")

        # buttons for actions
        psql["frms"]["table_ops"] = Frame(self)
        psql["frms"]["table_ops"].grid(row=23, column=0, padx=5, pady=5, sticky="W", columnspan=3)
        psql["oths"]["table_content"] = Checkbutton(psql["frms"]["table_ops"], variable=self.show_output,
                                                    onvalue=True, offvalue=False)
        create_tooltip(psql["oths"]["table_content"], "Show output in temporary file")
        psql["oths"]["table_content"].pack(side="left", padx=2)
        psql["btns"]["table_content"] = Button(psql["frms"]["table_ops"], text="Get Content",
                                               command=self.get_table_content)
        psql["btns"]["table_content"].pack(side="left", padx=2)
        psql["btns"]["table_insert"] = Button(psql["frms"]["table_ops"], text="Insert",
                                              command=self.insert_table_content)
        psql["btns"]["table_insert"].pack(side="left", padx=2)
        psql["btns"]["table_update"] = Button(psql["frms"]["table_ops"], text="Update",
                                              command=self.update_table)
        psql["btns"]["table_update"].pack(side="left", padx=2)
        psql["btns"]["table_delete"] = Button(psql["frms"]["table_ops"], text="Delete",
                                              command=self.delete_from_table)
        psql["btns"]["table_delete"].pack(side="left", padx=2)

    def disable_ui(self):
        """Disables all 1st level frame-children except Connect button"""
        for child in self.winfo_children():
            if child.widgetName == "ttk::frame":
                for c in child.winfo_children():
                    if c.widgetName in ["ttk::button", "ttk::combobox", "ttk::checkbutton"] \
                            and c.cget("text") != "Connect":
                        c.configure(state="disabled")

    def enable_ui(self):
        """Enables all 1st level frame-children"""
        for child in self.winfo_children():
            if child.widgetName == "ttk::frame":
                for c in child.winfo_children():
                    if c.widgetName in ["ttk::button", "ttk::combobox", "ttk::checkbutton"]:
                        c.configure(state="normal")

    """ ########################################### PSQL Functions ########################################### """

    def query_all(self, qry=None, debug=False):
        """Open cursor, execute query and return all fetch results"""
        if debug:
            print(f"EXECUTING: {qry}")
        with psql["connection"].cursor() as cursor:  # create cursor
            cursor.execute(qry)  # execute query
            ret = cursor.fetchall()  # fetch all results

        return ret

    def execute(self, sql=None, return_cursor=False):
        """Open cursor, execute sql command, rollback if failed; do nothing with return; Close cursor afterwards!"""
        cursor = psql["connection"].cursor()

        try:
            cursor.execute(sql)
            psql["connection"].commit()
        except Exception as e:
            print(e)
            psql["connection"].rollback()

        if return_cursor:
            return cursor
        else:
            cursor.close()

    def init_connection(self):
        """Read config parameters from database.ini and try to establish a connection"""
        if psql["btns"]["init"]["text"] == "Disconnect":
            psql["connection"].close()
            psql["btns"]["init"].config(text="Connect")
            self.disable_ui()
            return

        cfg = read_config(section="postgresql")

        try:
            # Establish connection
            psql["connection"] = psycopg2.connect(user=cfg["user"], password=cfg["pass"],
                                                  host=cfg["server"], port=cfg["port"], sslmode=cfg["sslmode"])

            # Fetch db names
            dbs = self.query_all("select datname from pg_database;")
            psql["oths"]["select_db"].config(values=[f[0] for f in dbs])
            psql["oths"]["select_db"].current(0)

            print(f"Available DBs: {[f[0] for f in dbs]}")
            psql["btns"]["init"].config(text="Disconnect")
            self.enable_ui()

        except Exception as e:
            print(e)
            psql["connection"] = None

    def close_connection(self, silent=False):
        if not psql["connection"]:
            print("Nothing open.")
            return

        if not silent:
            print("CLOSING CONNECTION")
        psql["connection"].close()
        psql["btns"]["init"].config(text="Connect")
        self.disable_ui()

    def change_db(self, event, target_db=None):
        """Change current database (open new connection)"""
        self.close_connection(silent=True)
        cfg = read_config(section="postgresql")
        db_name = psql["oths"]["select_db"].get()
        if target_db:
            db_name = target_db
        # print(f"CONNECTING TO DB {db_name}")
        psql["connection"] = psycopg2.connect(dbname=db_name, user=cfg["user"], password=cfg["pass"],
                                              host=cfg["server"], port=cfg["port"], sslmode=cfg["sslmode"])
        psql["btns"]["init"].config(text="Disconnect")
        self.enable_ui()
        # print("FETCHING TABLES")
        self.get_all_tables(populate_combobox=True)

    def create_db(self):
        """Create a new database"""
        new_db_name = simpledialog.askstring(title="New DB", prompt="Enter new database name:")
        if not new_db_name or new_db_name == "":
            return

        confirm = messagebox.askokcancel(title="Confirm new DB", message=f"Please confirm creation of database: "
                                                                         f"{new_db_name}")
        if not confirm:
            return

        # set autocommit stuff
        auto_commit = psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT
        psql["connection"].set_isolation_level(auto_commit)

        # create database
        sql = f"CREATE DATABASE {new_db_name}"
        self.execute(sql)

        # reopen connection
        self.close_connection(silent=True)
        self.init_connection()

    def drop_db(self):
        """Drop a database"""
        db_name = psql["oths"]["select_db"].get()
        confirm = messagebox.askokcancel(title="Confirm drop DB", message=f"Please confirm drop of database: {db_name}")
        if not confirm:
            return

        # switch to default db
        self.change_db(None, "postgres")

        # revoke future connections, terminate all connections to the database except my own
        self.execute(f"REVOKE CONNECT ON DATABASE {db_name} FROM PUBLIC;")
        self.execute(f"SELECT pid, pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '{db_name}';")

        # set autocommit stuff
        auto_commit = psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT
        psql["connection"].set_isolation_level(auto_commit)

        # drop desired database
        sql = f"""DROP DATABASE IF EXISTS {db_name}"""
        self.execute(sql)

        # reopen connection
        self.close_connection(silent=True)
        self.init_connection()

    def change_table(self, event):
        """Change table in current database"""
        table = psql["oths"]["select_table"].get()
        print(f"Doing stuff within {table}")

    def create_table(self):
        """Create a new table"""
        # get available datatypes, launch popup, hand over datatypes
        sql = CreatePSQLTable(self, title="Create PSQL Table", data_types=self.get_available_types())

        # prompt to create table with sql.results
        confirm = messagebox.askokcancel(title="Confirm create table", message=f"Please confirm creation of table: "
                                                                               f"{sql.result}")
        if not confirm:
            return

        # create table
        self.execute(sql.result)

        # refresh table list
        self.get_all_tables(populate_combobox=True)

    def drop_table(self):
        """Drop a table"""
        table = psql["oths"]["select_table"].get()
        confirm = messagebox.askokcancel(title="Confirm drop table", message=f"Please confirm drop of table: {table}")
        if not confirm:
            return

        sql = f"DROP TABLE IF EXISTS {table}"
        self.execute(sql)

        # refresh tables
        self.get_all_tables(populate_combobox=True)


    def get_available_types(self):
        """Get available types from pg_catalog.pg_types (not sure how this works and i dont see all types i expect)"""
        # query to get all available PostgreSQL datatypes
        sql = "SELECT typname FROM pg_catalog.pg_type"
        dtypes = self.query_all(sql)
        return [f[0] for f in dtypes if not f[0].startswith("_")]

    def rollback_db(self, silent=False):
        """Rollback DB on invalid query"""
        psql["connection"].rollback()
        if not silent:
            print("Last query rolled back")

    def get_info(self):
        """Get DB version info and current DB user"""
        version = self.query_all("SELECT version()")
        current_user = self.query_all("SELECT current_user")
        print(f"Version: {version[0][0]}\nCurrent User: {current_user[0][0]}")

    def get_all_tables(self, populate_combobox=False):
        """Get all tables in DB"""
        tables = self.query_all("select relname from pg_class where relkind='r' and relname !~ '^(pg_|sql_)';")

        if populate_combobox:
            psql["oths"]["select_table"].config(values=[f[0] for f in tables])
            if tables:
                psql["oths"]["select_table"].current(0)
            else:
                psql["oths"]["select_table"].set("")

        else:
            print([f[0] for f in tables])

    def get_table_content(self):
        """List whole content of table"""
        # query column names
        table = psql["oths"]["select_table"].get()
        sql = f"""SELECT COLUMN_NAME from information_schema.columns WHERE table_name = '{table}'"""
        columns = self.query_all(sql)
        columns = [col[0] for col in columns]

        # query content
        sql = f"""SELECT * FROM {table}"""
        content = self.query_all(sql)

        # max length of columns
        col_lengths = {k: 0 for k in columns}  # dict from list with strings with default value 0
        for row in content:
            for col_content, col_key_in_dict in zip(row, col_lengths.keys()):
                # if length of string in one of the columns in each row is longer than the value in the dict, overwrite
                if len(str(col_content)) >= col_lengths[col_key_in_dict]:
                    col_lengths[col_key_in_dict] = len(str(col_content))

        max_sep_length = sum(col_lengths.values()) + (len(columns)-1)*3
        file_content = ""

        # first line
        tmp_first_line = f" start of {table} ".center(max_sep_length if max_sep_length >= 40 else 40, "*")
        print(tmp_first_line)
        file_content += tmp_first_line + "\n"

        # print header
        tmp_header = " | ".join([columns[i].center(list(col_lengths.values())[i]) for i in range(len(columns))])
        print(tmp_header)
        file_content += tmp_header + "\n"
        # print separator
        tmp_sep = "-" * max_sep_length
        print(tmp_sep)
        file_content += tmp_sep + "\n"

        # print content
        for row in content:
            tmp_content = " | ".join([str(row[i]).center(list(col_lengths.values())[i]) for i in range(len(columns))])
            print(tmp_content)
            file_content += tmp_content + "\n"

        # end line
        tmp_end_line = f" end of {table} ".center(max_sep_length if max_sep_length >= 40 else 40, "*")
        print(tmp_end_line)
        file_content += tmp_end_line + "\n"

        # write to temporary file
        if self.show_output.get():
            executor.submit(partial(self.write_temporary_file, file_content, ".txt"))

    def write_temporary_file(self, data=None, suffix=".txt"):
        """Write to temporary file"""
        temp_file = tempfile.NamedTemporaryFile(suffix=suffix)
        temp_file.write(data.encode())
        temp_file.flush()
        os.startfile(temp_file.name)
        time.sleep(1)
        print("Launched temporary file:", temp_file.name)
        temp_file.close()

    def update_table(self):
        """Update table depending on input"""
        table = psql["oths"]["select_table"].get()

        # fetch headers from selected table
        sql = f"""SELECT COLUMN_NAME from information_schema.columns WHERE table_name = '{table}'"""
        headers = [col[0] for col in self.query_all(sql)]

        # fetch content from selected table
        sql = f"""SELECT * FROM {table}"""
        content = self.query_all(sql)

        # create popup
        prompt = DialogUpdatePSQLTable(self, title=f"Update {table}", table=table, content=content, headers=headers)
        if not prompt.result:
            return

        # get values from popup, reformat to SQL strings
        # prim_key = "=".join(prompt.result["prim_key"])
        prim_key = prompt.result["prim_key"]
        mods = list(prompt.result["mod_values"].items())
        orig_data = dict(zip(headers, prompt.result["orig_values"]))
        # mods = ", ".join(["=".join(f) for f in list(prompt.result["mod_values"].items())])
        # mods = f"({mods})"

        # create text for confirmation popup containing column name, original value and updated value
        mods_confirm_txt = "\n".join([f"{k}: {orig_data[k]} > {v}" for k, v in prompt.result["mod_values"].items()])

        # confirm update of record
        if not messagebox.askokcancel(title=f"Confirm update of {table}", message=f"{'='.join(prim_key)}\n"
                                                                                  f"{mods_confirm_txt}"):
            return

        # update query
        sql = f"""UPDATE "{table}" SET {', '.join([f'"{f[0]}"=(%s)' for f in mods])} WHERE {prim_key[0]}=(%s)"""
        cursor = psql["connection"].cursor()
        # hand over modified column values and prim. key value as (*args)
        cursor.execute(sql, (*[f[1] for f in mods], prim_key[1]))
        print(f"Number of rows updated: {cursor.rowcount}")
        psql["connection"].commit()
        cursor.close()

    def insert_table_content(self):
        """Insert table content"""
        table = psql["oths"]["select_table"].get()

        # fetch headers from selected table
        sql = f"""SELECT COLUMN_NAME from information_schema.columns WHERE table_name = '{table}'"""
        headers = [col[0] for col in self.query_all(sql)]

        # fetch types from selected table
        sql = f"""SELECT DATA_TYPE from information_schema.columns WHERE table_name = '{table}'"""
        types = [col[0] for col in self.query_all(sql)]

        # join headers and types to string in format "header [type]"
        headers_types = [f"{h} [{t}]" for h, t in zip(headers, types)]

        # create simple prompt for entering values
        prompt_tmp = "\n\t".join(headers_types)
        prompt = simpledialog.askstring(title=f"Insert {table}",
                                        prompt=f"Enter values to insert into {table} separated with comma without space"
                                               " (e.g. [1,some string,30])\n\nAvailable columns:\n\t" + prompt_tmp)
        if not prompt:
            return

        # split prompt into values
        values = prompt.split(",")

        # check if number of values matches number of headers
        if len(values) != len(headers):
            messagebox.showerror(title=f"Insert {table}", message=f"Number of values does not match number of headers")
            return

        # create query
        sql = f"""INSERT INTO {table} VALUES ({', '.join(['%s' for _ in range(len(headers))])})"""
        cursor = None
        try:
            cursor = psql["connection"].cursor()
            cursor.execute(sql, values)
            psql["connection"].commit()
            print("Command OK: " + sql % tuple(values))
        except Exception as e:
            messagebox.showerror(title=f"Insert {table}", message=f"{e}")
            self.rollback_db()
        finally:
            cursor.close()

    def delete_from_table(self):
        """Delete entire ids from table based on input"""
        table = psql["oths"]["select_table"].get()
        if not table:
            return

        # fetch headers from selected table
        sql = f"""SELECT COLUMN_NAME from information_schema.columns WHERE table_name = '{table}'"""
        headers = [col[0] for col in self.query_all(sql)]

        # fetch content from selected table
        sql = f"""SELECT * FROM {table}"""
        content = self.query_all(sql)

        # prompt Popup containing Listbox and entry to specify which data to delete
        prompt = DialogDeleteFromPSQLTable(self, title=f"Delete from {table}", table=table,
                                           content=content, headers=headers)

        # return on cancel action
        if not prompt.result:
            return

        selected_ids = prompt.result["selected_ids"]
        passed_values = prompt.result["passed_values"]

        if not selected_ids and not passed_values:
            return

        if selected_ids and passed_values:
            messagebox.showerror(title=f"Delete from {table}", message="Delete either by ID(s) or a value!")
            return

        # if IDs are selected in combobox
        if selected_ids:
            # prepare data & strip to ids
            if len(selected_ids) == 1:
                matches = f"({selected_ids[0][0]})"
            else:
                matches = tuple([f[0] for f in selected_ids])

            # confirm delete
            if not messagebox.askokcancel(title=f"Delete {table}", message=f"Confirm deleting ID(s): {matches}"):
                return

        if passed_values:
            # if something like name=Matzl was entered
            if "=" in passed_values:
                col, val = passed_values.split("=")
                print(f"Argument detected - trying to find value {val} in column {col} ..")
                if col in headers:
                    # sql = f"""SELECT id from {table} where {col} = '{val}'"""
                    sql = f"""SELECT {col} from {table} where {col} = '{val}'"""
                    matches = self.query_all(sql)
                    if not matches:
                        print(f"No matches found by checking column '{col}' for value '{val}'")
                        return

            # if only Matzl was entered
            else:
                for column in headers:
                    # try to fetch matching ids
                    try:
                        # sql = f"""SELECT id from {table} where {column} = '{passed_values}'"""
                        sql = f"""SELECT {column} from {table} where {column} = '{passed_values}'"""
                        matches = self.query_all(sql)
                    except Exception as e:
                        self.rollback_db(silent=True)

                if not matches:
                    print(f"No matches found by checking all columns for value '{passed_values}'")
                    return

            # cleanup return
            matches = tuple([f[0] for f in matches])
            if len(matches) == 1:
                matches = f"({matches[0]})"

            # confirm delete
            sql = f"""SELECT * FROM {table} where ID in {matches}"""
            delete_content = self.query_all(sql)
            delete_header = " | ".join(headers)
            delete_body = "".join([str(" | ".join(str(i) for i in t) + "\n") for t in delete_content])

            if not messagebox.askokcancel(title=f"Delete {table}", message=f"{delete_header}\n{'-'*len(delete_header)}"
                                                                           f"\n{delete_body}\n{'-'*len(delete_header)}"
                                                                           f"\nConfirm deleting ID(s): {matches}"):
                return

        # delete command
        sql = f"""DELETE from {table} where ID in {matches}"""
        cursor = self.execute(sql, return_cursor=True)
        print(f"Number of rows deleted: {cursor.rowcount}")
        cursor.close()

    def get_all_dbs(self):
        dbs = self.query_all("select datname from pg_database;")
        print([f[0] for f in dbs])


""" ###################################################################################################################
############################################## MongoDB main class ##################################################### 
################################################################################################################### """


class MongoDBTab(ttk.Frame):
    """Tab for MongoDB Control"""

    def __init__(self, parent, *args, **kwargs):
        global mongo
        ttk.Frame.__init__(self, parent, *args, **kwargs)
        self.root = parent
        self.build_mongo_tab()

    def update_progress(self, value):
        """Updates progress level of progressbar. Value can be from 0 to 100. """
        mongo["progress"] = value
        root.update()

    def build_mongo_tab(self):
        """Build MongoDB Tab"""
        mongo["lbls"]["title"] = Label(self, text="MongoDB Managing stuff")
        mongo["lbls"]["title"].grid(column=0, row=0, padx=5, sticky="W")
        ttk.Separator(self, orient=HORIZONTAL).grid(row=9, column=0, columnspan=99, sticky="ew", pady=10)

        # INIT (10+) ############################################################################################ #
        mongo["lbls"]["init_title"] = Label(self, text="Initialize")
        mongo["lbls"]["init_title"].grid(row=10, column=0, padx=5, sticky="W")
        mongo["btns"]["init"] = Button(self, text="Initialize", command=self.init_mongodb)
        mongo["btns"]["init"].grid(row=11, column=0, padx=5, sticky="W")

    """ ########################################### MongoDB Functions ########################################### """

    def init_mongodb(self):
        print("Initializing MongoDB Connection ..")
        cfg = read_config(section="mongodb")
        client = MongoClient(f"{cfg['user']}:{cfg['pass']}@{cfg['server']}:{cfg['port']}")
        print(f"Created client connection: {client}")
        # mongodb + srv: // readonly: readonly @ [demodata.rgl39.mongodb.net / demo?retryWrites = true & w = majority](
        #     http: // demodata.rgl39.mongodb.net / demo?retryWrites=true & w=majority)


""" ###################################################################################################################
############################################### Boilerplate init ###################################################### 
################################################################################################################### """


if __name__ == '__main__':
    root = tkinter.Tk()
    root.title(f"RPi DB Manager V{gui_version}")

    # tab management
    tab_root = ttk.Notebook(root)
    tab_psql = PostgreSQLTab(tab_root, style="Black.TLabel", relief="sunken", borderwidth=5)
    tab_mongo = MongoDBTab(tab_root, style="Black.TLabel", relief="sunken", borderwidth=5)
    tab_root.add(tab_psql, text="PostgreSQL")
    tab_root.add(tab_mongo, text="MongoDB")
    tab_root.pack(expand=1, fill="both")

    # start GUI
    root.mainloop()

