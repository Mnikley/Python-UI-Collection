"""
Tkinter GUI to display data from Bitpanda account
- Requires valid API keys for Bitpanda, Forex Crypto Stock and ExchangeRate-API
"""


from tkinter import Tk, Toplevel, SOLID, Menu, Label, Button, Frame, Checkbutton, BooleanVar, StringVar
from tkinter import simpledialog, messagebox
from tkinter.ttk import Separator
from tkinter.constants import HORIZONTAL
from functools import partial
from configparser import ConfigParser
import datetime
import os
import json
from crypto_api import get_trades, get_asset_wallets, get_fiat_wallets, get_fiat_transactions


class ToolTip(object):
    """Tooltip class. Call with create_tooltip(widget, text)."""

    def __init__(self, widget):
        self.widget = widget
        self.tipwindow = None
        self.id = None
        self.x = self.y = 0

    def showtip(self, text):
        """Display text in tooltip window"""
        self.text = text
        if self.tipwindow or not self.text:
            return
        x, y, cx, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 57
        y = y + cy + self.widget.winfo_rooty() + 27
        self.tipwindow = tw = Toplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_geometry("+%d+%d" % (x, y))
        label = Label(tw, text=self.text, anchor="w",
                      background="#ffffe0", relief=SOLID, borderwidth=1,
                      font=("tahoma", "8", "normal"))
        label.pack(ipadx=5, ipady=5)

    def hidetip(self):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()


class DateTimeEncoder(json.JSONEncoder):
    def default(self, z):
        if isinstance(z, datetime.datetime):
            return str(z)
        else:
            return super().default(z)


def create_tooltip(widget, text):
    """
    Create tooltip for any widget.
    Example: create_tooltip(some_widget, text="Test Message")
    """
    tool_tip = ToolTip(widget)

    def enter(event):
        try:
            tool_tip.showtip(text)
        except Exception as e:
            print(e)

    def leave(event):
        tool_tip.hidetip()

    widget.bind('<Enter>', enter)
    widget.bind('<Leave>', leave)


class UI(Tk):
    """Main UI Class"""

    def __init__(self):
        Tk.__init__(self)

        # read config
        self.cfg = ConfigParser()
        self.cfg.read("config.ini")

        # widget objects
        self.wdgs = {}

        # build ui
        self.build_ui()
        self.build_menu()

        # refresh tooltips based on config values
        self.refresh_tooltips()

    def build_ui(self):

        # INFO
        Label(text="STATUS").pack()

        Separator(self, orient="horizontal").pack(fill="x", pady=5)

        self.wdgs["bitpanda_api_key"] = StringVar(value=self.cfg.get("bitpanda", "api_key"))
        self.wdgs["bitpanda_api_key_displayvar"] = StringVar(value="Not set")
        self.wdgs["bitpanda_api_key_label"] = Label(textvariable=self.wdgs["bitpanda_api_key_displayvar"])
        self.wdgs["bitpanda_api_key_label"].pack()
        
        self.wdgs["forexcryptostock_api_key"] = StringVar(value=self.cfg.get("forexcryptostock", "api_key"))
        self.wdgs["forexcryptostock_api_key_displayvar"] = StringVar(value="Not set")
        self.wdgs["forexcryptostock_api_key_label"] = Label(textvariable=self.wdgs["forexcryptostock_api_key_displayvar"])
        self.wdgs["forexcryptostock_api_key_label"].pack()
        
        self.wdgs["exchangerate_api_key"] = StringVar(value=self.cfg.get("exchangerate", "api_key"))
        self.wdgs["exchangerate_api_key_displayvar"] = StringVar(value="Not set")
        self.wdgs["exchangerate_api_key_label"] = Label(textvariable=self.wdgs["exchangerate_api_key_displayvar"])
        self.wdgs["exchangerate_api_key_label"].pack()

        Separator(self, orient="horizontal").pack(fill="x", pady=5)

        # GET ASSETS FRAME
        self.wdgs["get_assets_frame"] = Frame(self)

        self.wdgs["convert_assets_var"] = BooleanVar(value=False)
        self.wdgs["convert_assets_enable"] = Checkbutton(self.wdgs["get_assets_frame"], text="Convert",
                                                         variable=self.wdgs["convert_assets_var"])

        self.wdgs["convert_assets_enable"].pack(side="left")
        current_currency = self.cfg.get("general", "main_currency")
        create_tooltip(self.wdgs["convert_assets_enable"], f"If checked, balances will be converted to "
                                                           f"{current_currency} by using the forex crypto stock API and "
                                                           f"ExchangeRate API (requires valid API keys)")

        self.wdgs["convert_assets_debug_var"] = BooleanVar(value=False)
        self.wdgs["convert_assets_debug"] = Checkbutton(self.wdgs["get_assets_frame"], text="Show details",
                                                        variable=self.wdgs["convert_assets_debug_var"])
        self.wdgs["convert_assets_debug"].pack(side="left")
        create_tooltip(self.wdgs["convert_assets_debug"], "Prints details of conversion to console if enabled")

        self.wdgs["convert_assets_export_var"] = BooleanVar(value=False)
        self.wdgs["convert_assets_export"] = Checkbutton(self.wdgs["get_assets_frame"], text="Export",
                                                         variable=self.wdgs["convert_assets_export_var"])
        self.wdgs["convert_assets_export"].pack(side="left")
        create_tooltip(self.wdgs["convert_assets_export"], "Exports data to a .json file if enabled")

        self.wdgs["get_assets"] = Button(self.wdgs["get_assets_frame"], text="Get Assets", command=self.get_assets)
        self.wdgs["get_assets"].pack(side="left")
        create_tooltip(self.wdgs["get_assets"], "Get Assets from various wallets from your Bitpanda account. "
                                                "Includes Stocks, Metals, Cryptos etc.")
        self.wdgs["get_assets_frame"].pack()

    def build_menu(self):
        """Build the menu bar on top"""
        menubar = Menu(self)

        settings_menu = Menu(menubar, tearoff=0)
        settings_menu.add_command(label="Set main currency",
                                  command=partial(self.write_cfg, "general", "main_currency"))
        settings_menu.add_command(label="Set alternative currencies",
                                  command=partial(self.write_cfg, "general", "alt_currencies"))
        settings_menu.add_separator()
        settings_menu.add_command(label="Open Config", command=self.open_config)
        settings_menu.add_separator()
        settings_menu.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="Configuration", menu=settings_menu)

        credentials_menu = Menu(menubar, tearoff=0)
        credentials_menu_bitpanda = Menu(credentials_menu, tearoff=0)
        credentials_menu_bitpanda.add_command(label="Change base URL",
                                              command=partial(self.write_cfg, "bitpanda", "url"))
        credentials_menu_bitpanda.add_command(label="Change API key",
                                              command=partial(self.write_cfg, "bitpanda", "api_key"))
        credentials_menu.add_cascade(label="Bitpanda", menu=credentials_menu_bitpanda)
        credentials_menu_forexcryptostock = Menu(credentials_menu, tearoff=0)
        credentials_menu_forexcryptostock.add_command(label="Change base URL",
                                                      command=partial(self.write_cfg, "forexcryptostock", "url"))
        credentials_menu_forexcryptostock.add_command(label="Change API key",
                                                      command=partial(self.write_cfg, "forexcryptostock", "api_key"))
        credentials_menu.add_cascade(label="Forex Crypto Stock", menu=credentials_menu_forexcryptostock)
        credentials_menu_exchangerate = Menu(credentials_menu, tearoff=0)
        credentials_menu_exchangerate.add_command(label="Change base URL",
                                                  command=partial(self.write_cfg, "exchangerate", "url"))
        credentials_menu_exchangerate.add_command(label="Change API key",
                                                  command=partial(self.write_cfg, "exchangerate", "api_key"))
        credentials_menu.add_cascade(label="ExchangeRate", menu=credentials_menu_exchangerate)
        menubar.add_cascade(label="Credentials", menu=credentials_menu)

        self.config(menu=menubar)

    def open_config(self):
        """Try to open file."""
        try:
            os.startfile("config.ini")
        except Exception as e:
            print(e)

    def write_cfg(self, section=None, option=None, value=None):
        """Overwrite odoo_config.ini."""
        if section is None or option is None:
            print("Give me a section and option")
            return

        # prompt for value if none given
        if value is None:
            initial_value = self.cfg.get(section=section, option=option)
            value = simpledialog.askstring(f"Value for {section} {option}",
                                           f"Please enter a new value for {section} {option}",
                                           initialvalue=initial_value)

            # return if no value is given (cancel)
            if not value:
                return

        if not isinstance(value, str):
            value = str(value)

        # write config
        self.cfg.set(section=section, option=option, value=value)
        with open("config.ini", "w") as __cfg:
            self.cfg.write(__cfg)
        print(f"Updated config.ini: {section} | {option} | {value}")

        # refresh StringVars
        for wdg_id, wdg in self.wdgs.items():
            if isinstance(wdg, StringVar):
                if wdg_id.startswith(section) and wdg_id.endswith(option):
                    wdg.set(value)
                    if value != "None":
                        self.wdgs[f"{wdg_id}_displayvar"].set(f"{wdg_id} set")
                    else:
                        self.wdgs[f"{wdg_id}_displayvar"].set(f"{wdg_id} not set")
                    create_tooltip(self.wdgs[f"{wdg_id}_label"], value)

    def refresh_tooltips(self):
        print("Refreshing tooltips ..")
        for wdg_id, wdg in self.wdgs.items():
            if isinstance(wdg, StringVar):
                try:
                    if wdg.get() != "None":
                        self.wdgs[f"{wdg_id}_displayvar"].set(f"{wdg_id} set")
                        create_tooltip(self.wdgs[f"{wdg_id}_label"], wdg.get())
                    else:
                        self.wdgs[f"{wdg_id}_displayvar"].set(f"{wdg_id} not set")
                        create_tooltip(self.wdgs[f"{wdg_id}_label"], "Set via Configuration panel")
                except Exception as e:
                    pass

        self.update_idletasks()

    def get_assets(self):
        """Get assets from bitpanda wallets. Requires valid Bitpanda API key
        - Requires additional forex crypto & exchangerate API keys if enable_conversion is True
        """
        enable_conversion = self.wdgs["convert_assets_var"].get()
        debug_text = self.wdgs["convert_assets_debug_var"].get()
        export_as_json = self.wdgs["convert_assets_export_var"].get()
        bitpanda_api_key = self.cfg.get("bitpanda", "api_key")
        forex_api_key = self.cfg.get("forexcryptostock", "api_key")
        exchangerate_api_key = self.cfg.get("exchangerate", "api_key")
        conversion_currency = self.cfg.get("general", "main_currency")
        conversion_alt_currencies = self.cfg.get("general", "alt_currencies").split(",")

        if enable_conversion:
            tmp = messagebox.askquestion("Enable conversion", "Are you sure you want to enable conversion? This will "
                                                              "cost you 2 credits from your forex API!")
            if tmp == "no":
                enable_conversion = False

        wallet_data = get_asset_wallets(enable_conversion=enable_conversion, bitpanda_api_key=bitpanda_api_key,
                                        forex_api_key=forex_api_key, exchangerate_api_key=exchangerate_api_key,
                                        conversion_currency=conversion_currency, conversion_silent=debug_text,
                                        conversion_alt_currencies=conversion_alt_currencies)

        if export_as_json:
            file_name = f'wallet_dump_{datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.json'
            with open(file_name, "w") as f:
                f.write(json.dumps(wallet_data, indent=4, cls=DateTimeEncoder))


if __name__ == '__main__':
    # create default config.ini on first start
    if not os.path.isfile("config.ini"):
        print("No config.ini detected. Loading default configuration ..")
        default_ini = f"""[general]
main_currency = EUR
alt_currencies = BTC,USD

[bitpanda]
url = https://api.bitpanda.com/v1/
api_key = None
docs = https://developers.bitpanda.com/platform/

[forexcryptostock]
url = https://fcsapi.com/api-v3/
api_key = None
docs = https://fcsapi.com/document/crypto-api

[exchangerate]
url = https://v6.exchangerate-api.com/v6/
api_key = None
docs = https://app.exchangerate-api.com/sign-up
"""

        with open("config.ini", "w") as cfg:
            cfg.write(default_ini)

    app = UI()
    app.title(f"Bitpanda UI")
    # app.overrideredirect(1)  # remove top badge
    # app.attributes("-toolwindow", True)
    app.geometry("300x300")
    # style = ThemedStyle(app)
    # style.set_theme("plastik")
    app.mainloop()
