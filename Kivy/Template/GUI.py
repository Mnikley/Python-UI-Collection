"""Kivy demo app with screen-manager, splash screen, tooltips, resizable widgets """

# %% standard python library imports
import os
import sys
import psutil
import platform
if platform.system() == "Windows":
    import win32console  # hide console
    import win32gui  # hide console
    import win32con  # hide console

# %% kivy imports
from kivy.config import Config
Config.read(os.path.join(os.path.dirname(os.path.abspath(__file__)), "GUI.ini"))
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.clock import Clock
from kivy.uix.image import Image
from kivy.uix.popup import Popup

# %% library imports
from library.kivy_utils import TTLabel, TTButton

""" ################################################################################################################### 
################################################# Configuration #######################################################
################################################################################################################### """

# read kivy files
for kv in ["root.kv", "style.kv"]:
    Builder.load_file("layouts" + os.sep + kv)


""" ################################################################################################################### 
################################################### Main Class ########################################################
################################################################################################################### """


class Root(BoxLayout):
    """ Main Root class for callbacks, UI building etc."""
    last_screen = None

    def __init__(self):
        super().__init__()

    def test_function(self):
        print("K TEST")

    def update_status(self, text="", warning=False, critical=False):
        markup = ""
        if warning:
            markup = "[color=d87600]"  # orange
        if critical:
            markup = "[color=ff2600][b]"  # red
        self.ids.status.text = f"{markup}{text}"  # label for status text inside bottom menu
        Clock.schedule_once(self.ids.status.on_window_resize)  # refresh size of status label

        # TODO: write status to log
        # code here

    def sm_switcher(self, go_to_screen):
        """Switch Screen depending on their order to left/right accordingly.

        Parameters
        ----------
        go_to_screen : string
            Screen ID defined in kivy file
        """
        for idx, scr in enumerate(self.ids.sm.screen_names):
            if go_to_screen == scr:
                goto_index_ = idx
            if self.ids.sm.current == scr:
                current_index_ = idx

        if current_index_ > goto_index_:
            self.ids.sm.transition.direction = 'right'
        if current_index_ < goto_index_:
            self.ids.sm.transition.direction = 'left'

        self.last_screen = go_to_screen
        self.ids.sm.current = go_to_screen
        Clock.schedule_once(self.sm_refresh_widgets)
        # self.ids.sm.canvas.ask_update()  # if screenmanager has canvas which changes from screen to screen

    def sm_refresh_widgets(self, *args):
        """Refresh widget size after switching screens. Checks for three levels of nested layouts."""
        # Accesses first layout in Screen (usually BoxLayout, no typecheck)
        root = self.ids[f"'{self.ids.sm.current}'"].children[0]
        # iterate over all children in first Layout in Screen
        for child in root.children:
            # if child is BoxLayout or GridLayout go deeper one level ..
            if isinstance(child, (BoxLayout, GridLayout)):
                for sub_child in child.children:
                    # if sub_child is BoxLayout or GridLayout go deeper yet another level ..
                    if isinstance(sub_child, (BoxLayout, GridLayout)):
                        for sub_sub_child in sub_child.children:
                            # if third-level child is TTButton or TTLabel, trigger resize; no 4th level
                            if isinstance(sub_sub_child, (TTButton, TTLabel)):
                                sub_sub_child.on_window_resize()
                    # if second-level child is TTButton or TTLabel, trigger resize
                    elif isinstance(sub_child, (TTButton, TTLabel)):
                        sub_child.on_window_resize()
            # if top-level child is TTButton or TTLabel, trigger resize
            elif isinstance(child, (TTButton, TTLabel)):
                child.on_window_resize()


class LeysolutionsApp(App):
    """App class, access attributes from .kv files via app.attribute_name"""

    def __init__(self, **kwargs):
        super().__init__()
        self.splash_popup: Popup = None

    def build_config(self, config):
        """Builds default config if none exists (leysolutionsapp.ini).
        - Root config: Config.get()
        - LeysolutionsApp config: self.config['section']['key']
        """
        config.setdefaults("general", {
            "console_enabled": "0"
        })
        config.setdefaults('layout', {
            'font_size_button': '15',
            'font_size_text': '15',
            'font_size_h1': '30',
            'font_size_h2': '25',
            'font_family': 'Barlow',
            'show_splash': '1',
            "dark_mode": "1",
        })
        config.setdefaults("images", {
            "logo_bright": "static" + os.sep + "logo_bright.png",
            "logo_dark": "static" + os.sep + "logo_dark.png",
            "logo_splash": "static" + os.sep + "logo_splash.jpg",
            "bg_dark": "static" + os.sep + "bg_dark.jpg",
            "bg_bright": "static" + os.sep + "bg_bright.jpg",
            "horizontal_line": "static" + os.sep + "horizontal_line_blue.png",
            "bar_dark": "static" + os.sep + "bar_dark.png",
            "bar_bright": "static" + os.sep + "bar_bright.png",
        })

    def build_settings(self, settings):
        """Builds settings menu accessible with F1"""
        settings.add_json_panel('LeysolutionsApp configuration panel', self.config, "static" + os.sep + "settings_menu.json")

    def on_config_change(self, config, section, key, value):
        """Callback if configuration was changed"""
        if config is self.config:
            if key == "font_family":
                if value == "Barlow":
                    tmp = "['Barlow', 'static/Barlow-Medium.ttf', 'static/Barlow-MediumItalic.ttf', " \
                          "'static/Barlow-Bold.ttf', 'static/Barlow-BoldItalic.ttf']"
                if value == "Roboto":
                    tmp = "['Roboto', 'data/fonts/Roboto-Regular.ttf', 'data/fonts/Roboto-Italic.ttf', " \
                          "'data/fonts/Roboto-Bold.ttf', 'data/fonts/Roboto-BoldItalic.ttf']"
                Config.set("kivy", "default_font", tmp)
                Config.write()  # writes to GUI.ini

            if platform.system() == "Windows":
                if key == "console_enabled":
                    if bool(int(value)):
                        print("enabling console")
                        win32gui.ShowWindow(win32console.GetConsoleWindow(), win32con.SW_SHOW)
                    else:
                        print("disabling console")
                        win32gui.ShowWindow(win32console.GetConsoleWindow(), win32con.SW_HIDE)

            print(f"Config updated: {section} | {key} | {value}")
            self.root.update_status(text=f"Config updated: {section} | {key} | {value}")

            # Restart UI on certain keys
            if key.startswith(("font_", "dark_mode")):
                print("Restarting UI in 2 seconds ..")
                Clock.schedule_once(self.restart, 2)

    def build(self):
        config = self.config
        self.root = Root()
        # show/hide splashscreen
        if bool(int(config["layout"]["show_splash"])):
            Clock.schedule_once(self.splash_screen, .01)
        # show/hide console
        if platform.system() == "Windows":
            if bool(int(config["general"]["console_enabled"])) == False:
                win32gui.ShowWindow(win32console.GetConsoleWindow(), win32con.SW_HIDE)
        return self.root

    def on_pause(self):
        return True

    def splash_screen(self, *args):
        """Splash screen at beginning of launch"""
        self.splash_popup = Popup(title="Welcome to my demo app!", title_size=20, title_align="center",
                                  size_hint=(None, None), size=self.root.size, auto_dismiss=True)
        content = BoxLayout(orientation="vertical")
        image = Image(source=self.config["images"]["logo_splash"])
        content.add_widget(image)

        self.splash_popup.content = content

        self.splash_popup.open()

        def kill(*args):
            self.splash_popup.dismiss()

        Clock.schedule_once(kill, 3)

    def restart(self, *args):
        """Restart GUI."""
        print('Restarting GUI .....')
        try:
            p = psutil.Process(os.getpid())
            for handler in p.get_open_files() + p.connections():
                os.close(handler.fd)
        except Exception as e:
            print(e)
            # logging.error(e)

        python = sys.executable
        if platform.system() == "Windows":
            os.execl(python, python, "\"{}\"".format(sys.argv[0]))
        elif platform.system() == "Linux":
            os.execl(python, python, f"{sys.argv[0]}")


if __name__ == "__main__":
    LeysolutionsApp().run()
