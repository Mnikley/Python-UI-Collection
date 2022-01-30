"""
Tkinter Crypto GUI to get account balances, transaction history and more from various crypto platforms
Currently supports: Bitpanda, Binance Smart Chain

Notes
-----
Requires valid API keys for:
    - Bitpanda
    - Forex Crypto Stock Exchange
    - ExchangeRate-API (https://www.exchangerate-api.com/)
    - Binance Smart Chain Scan (https://www.bscscan.com)
"""


from tkinter import Tk, Toplevel, SOLID, Menu, Label, Button, Checkbutton, BooleanVar, StringVar, LabelFrame
from tkinter import simpledialog, messagebox
from tkinter.ttk import Notebook, Frame
from functools import partial
from configparser import ConfigParser
import os
from crypto_api import get_trades, get_asset_wallets, get_fiat_wallets, get_fiat_transactions, write_to_temporary_file
from crypto_api import resolve_bitpanda_crypto_ids
import webbrowser


class ToolTip(object):
    """Create tooltips for tkinter widgets.

    Notes
    -----
    Call with function::

        create_tooltip(widget, text)

    """

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
                      font=("consolas", "8", "normal"))
        label.pack(ipadx=5, ipady=5, fill="both")

    def hidetip(self):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()


def create_tooltip(widget, text):
    """
    Supplementary function for Tooltip class. Creates tooltip for any widget.

    Parameters
    ----------
    widget : object
        TKinter widget to append tooltip to
    text : string
        Tooltip text

    Examples
    --------
    ::

        my_widget = Button(text="Click me")
        create_tooltip(my_widget, text="That is a great button")
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
        """Init function of UI class"""
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
        """Build root UI including Notebook and tabs, calls functions to build widgets for tabs"""

        # create tab control + tabs
        tab_control = Notebook()
        tab_bitpanda = Frame(tab_control)
        tab_binance = Frame(tab_control)
        tab_control.add(tab_bitpanda, text='Bitpanda')
        tab_control.add(tab_binance, text='Binance')
        tab_control.pack(expand=1, fill="both")
        
        # call functions to build tab-contents
        self.build_bitpanda_tab(tab_root=tab_bitpanda)
        self.build_binance_tab(tab_root=tab_binance)

    def build_bitpanda_tab(self, tab_root=None):
        """Build the widgets of the Bitpanda tab

        Parameters
        ----------
        tab_root : Frame
            Frame created in build_ui(), part of a Notebook
        """
        Label(master=tab_root, text="Bitpanda UI", font=("Arial", 18)).pack()

        # INFO
        self.wdgs["status_frame"] = LabelFrame(master=tab_root, text="API key status")

        self.wdgs["bitpanda_api_key"] = StringVar(value=self.cfg.get("bitpanda", "api_key"))
        self.wdgs["bitpanda_api_key_displayvar"] = StringVar(value="Not set")
        self.wdgs["bitpanda_api_key_label"] = Label(self.wdgs["status_frame"],
                                                    textvariable=self.wdgs["bitpanda_api_key_displayvar"])
        self.wdgs["bitpanda_api_key_label"].grid(row=0, column=1, padx=2, sticky="w")
        Label(self.wdgs["status_frame"], text="Bitpanda").grid(row=0, column=0, padx=2, sticky="w")
        
        self.wdgs["forexcryptostock_api_key"] = StringVar(value=self.cfg.get("forexcryptostock", "api_key"))
        self.wdgs["forexcryptostock_api_key_displayvar"] = StringVar(value="Not set")
        self.wdgs["forexcryptostock_api_key_label"] = Label(self.wdgs["status_frame"],
                                                            textvariable=self.wdgs["forexcryptostock_api_key_displayvar"])
        self.wdgs["forexcryptostock_api_key_label"].grid(row=1, column=1, padx=2, sticky="w")
        Label(self.wdgs["status_frame"], text="Forex Crypto Stock").grid(row=1, column=0, padx=2, sticky="w")
        
        self.wdgs["exchangerate_api_key"] = StringVar(value=self.cfg.get("exchangerate", "api_key"))
        self.wdgs["exchangerate_api_key_displayvar"] = StringVar(value="Not set")
        self.wdgs["exchangerate_api_key_label"] = Label(self.wdgs["status_frame"],
                                                        textvariable=self.wdgs["exchangerate_api_key_displayvar"])
        self.wdgs["exchangerate_api_key_label"].grid(row=2, column=1, padx=2, sticky="w")
        Label(self.wdgs["status_frame"], text="ExchangeRate").grid(row=2, column=0, padx=2, sticky="w")

        self.wdgs["status_frame"].pack(padx=5, pady=5, ipadx=2, ipady=2)

        # Separator(self, orient="horizontal").pack(fill="x", pady=5)

        # GET ASSETS FRAME
        self.wdgs["get_assets_frame"] = LabelFrame(master=tab_root, text="Bitpanda Assets")

        self.wdgs["convert_assets_var"] = BooleanVar(value=False)
        self.wdgs["convert_assets_enable"] = Checkbutton(self.wdgs["get_assets_frame"], text="Convert",
                                                         variable=self.wdgs["convert_assets_var"])

        self.wdgs["convert_assets_enable"].grid(row=0, column=0, sticky="w")
        current_currency = self.cfg.get("general", "main_currency")
        create_tooltip(self.wdgs["convert_assets_enable"], f"If checked, balances will be converted to "
                                                           f"{current_currency} by using the forex crypto stock API and "
                                                           f"ExchangeRate API (requires valid API keys)")

        self.wdgs["convert_assets_debug_var"] = BooleanVar(value=False)
        self.wdgs["convert_assets_debug"] = Checkbutton(self.wdgs["get_assets_frame"], text="Show details",
                                                        variable=self.wdgs["convert_assets_debug_var"])
        self.wdgs["convert_assets_debug"].grid(row=0, column=1, sticky="w")
        create_tooltip(self.wdgs["convert_assets_debug"], "Print details of the conversion steps to console")

        self.wdgs["convert_assets_export_var"] = BooleanVar(value=False)
        self.wdgs["convert_assets_export"] = Checkbutton(self.wdgs["get_assets_frame"], text="Export",
                                                         variable=self.wdgs["convert_assets_export_var"])
        self.wdgs["convert_assets_export"].grid(row=1, column=0, sticky="w")
        create_tooltip(self.wdgs["convert_assets_export"], "Exports data to a .json file")

        self.wdgs["get_assets"] = Button(self.wdgs["get_assets_frame"], text="Get Assets", command=self.get_assets)
        self.wdgs["get_assets"].grid(row=1, column=1, columnspan=2)
        create_tooltip(self.wdgs["get_assets"], "Get Assets from various wallets from your Bitpanda account. "
                                                "Includes Stocks, Metals, Cryptos etc.")

        self.wdgs["current_balance_var"] = StringVar(value="None")
        self.wdgs["current_balance_label"] = Label(self.wdgs["get_assets_frame"],
                                                   text=f"Balance [{self.cfg.get('general','main_currency')}]:")
        self.wdgs["current_balance_label"].grid(row=2, column=0, sticky="w")
        self.wdgs["current_balance"] = Label(self.wdgs["get_assets_frame"],
                                             textvariable=self.wdgs["current_balance_var"])
        self.wdgs["current_balance"].grid(row=2, column=1, columnspan=2)

        self.wdgs["get_assets_frame"].pack(padx=5, pady=5, ipadx=2, ipady=2)

        # GET TRADES
        self.wdgs["get_trades_frame"] = LabelFrame(master=tab_root, text="Bitpanda Trades")
        self.wdgs["get_trades_export_var"] = BooleanVar(value=False)
        self.wdgs["get_trades_export"] = Checkbutton(self.wdgs["get_trades_frame"], text="Export",
                                                     variable=self.wdgs["get_trades_export_var"])
        self.wdgs["get_trades_export"].grid(row=0, column=0, sticky="w")
        create_tooltip(self.wdgs["convert_assets_export"], "Exports data to a .json file")
        self.wdgs["get_trades"] = Button(self.wdgs["get_trades_frame"], text="Get Trades", command=self.get_trades)
        self.wdgs["get_trades"].grid(row=0, column=1)
        self.wdgs["get_trades_amount_label"] = Label(self.wdgs["get_trades_frame"], text=f"Trades:")
        self.wdgs["get_trades_amount_label"].grid(row=1, column=0, padx=2, sticky="w")
        self.wdgs["get_trades_amount_var"] = StringVar(value="None")
        self.wdgs["get_trades_amount"] = Label(self.wdgs["get_trades_frame"], 
                                               textvariable=self.wdgs["get_trades_amount_var"])
        self.wdgs["get_trades_amount"].grid(row=1, column=1)
        self.wdgs["get_trades_invested_label"] = Label(self.wdgs["get_trades_frame"],
                                                       text=f"Invested [{self.cfg.get('general','main_currency')}]:")
        self.wdgs["get_trades_invested_label"].grid(row=2, column=0, padx=2, sticky="w")
        self.wdgs["get_trades_invested_var"] = StringVar(value="None")
        self.wdgs["get_trades_invested"] = Label(self.wdgs["get_trades_frame"],
                                                 textvariable=self.wdgs["get_trades_invested_var"])
        self.wdgs["get_trades_invested"].grid(row=2, column=1)
        self.wdgs["get_trades_frame"].pack(padx=5, pady=5, ipadx=2, ipady=2)

        # GET FIAT INFO
        self.wdgs["get_fiat_frame"] = LabelFrame(master=tab_root, text="Bitpanda Fiat Data")
        self.wdgs["get_fiat_export_var"] = BooleanVar(value=False)
        self.wdgs["get_fiat_export"] = Checkbutton(self.wdgs["get_fiat_frame"], text="Export",
                                                   variable=self.wdgs["get_fiat_export_var"])
        self.wdgs["get_fiat_export"].grid(row=0, column=0, sticky="w")
        
        self.wdgs["get_fiat"] = Button(self.wdgs["get_fiat_frame"], text="Get Fiat Data", command=self.get_fiat)
        self.wdgs["get_fiat"].grid(row=0, column=1)

        self.wdgs["get_fiat_balance_var"] = StringVar(value="None")
        self.wdgs["get_fiat_balance_label"] = Label(self.wdgs["get_fiat_frame"], text="Balance")
        self.wdgs["get_fiat_balance_label"].grid(row=1, column=0, padx=2, sticky="w")
        self.wdgs["get_fiat_balance"] = Label(self.wdgs["get_fiat_frame"],
                                              textvariable=self.wdgs["get_fiat_balance_var"])
        self.wdgs["get_fiat_balance"].grid(row=1, column=1)
        self.wdgs["get_fiat_transactions_var"] = StringVar(value="None")
        self.wdgs["get_fiat_transactions_label"] = Label(self.wdgs["get_fiat_frame"], text="Transactions")
        self.wdgs["get_fiat_transactions_label"].grid(row=2, column=0, padx=2, sticky="w")
        self.wdgs["get_fiat_transactions"] = Label(self.wdgs["get_fiat_frame"],
                                                   textvariable=self.wdgs["get_fiat_transactions_var"])
        self.wdgs["get_fiat_transactions"].grid(row=2, column=1)

        self.wdgs["get_fiat_frame"].pack(padx=5, pady=5, ipadx=2, ipady=2)

    def build_binance_tab(self, tab_root=None):
        """Build the widgets of the Binance tab

        Parameters
        ----------
        tab_root : Frame
            Frame created in build_ui(), part of a Notebook
        """
        Label(master=tab_root, text="Binance UI", font=("Arial", 18)).pack()

    def build_menu(self):
        """Builds the menu bar on top"""
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

        # credentials menu
        credentials_menu = Menu(menubar, tearoff=0)

        # bitpanda options
        credentials_menu_bitpanda = Menu(credentials_menu, tearoff=0)
        credentials_menu_bitpanda.add_command(label="Change base URL",
                                              command=partial(self.write_cfg, "bitpanda", "url"))
        credentials_menu_bitpanda.add_command(label="Change API key",
                                              command=partial(self.write_cfg, "bitpanda", "api_key"))
        credentials_menu_bitpanda.add_command(label="Get API key",
                                              command=partial(webbrowser.open_new, r"https://web.bitpanda.com/apikey"))
        credentials_menu.add_cascade(label="Bitpanda", menu=credentials_menu_bitpanda)

        # forex cryptostock options
        credentials_menu_forexcryptostock = Menu(credentials_menu, tearoff=0)
        credentials_menu_forexcryptostock.add_command(label="Change base URL",
                                                      command=partial(self.write_cfg, "forexcryptostock", "url"))
        credentials_menu_forexcryptostock.add_command(label="Change API key",
                                                      command=partial(self.write_cfg, "forexcryptostock", "api_key"))
        credentials_menu_forexcryptostock.add_command(label="Get API key",
                                                      command=partial(webbrowser.open_new,
                                                                      r"https://fcsapi.com/document/crypto-api"))

        credentials_menu.add_cascade(label="Forex Crypto Stock", menu=credentials_menu_forexcryptostock)

        # ExchangeRate API options
        credentials_menu_exchangerate = Menu(credentials_menu, tearoff=0)
        credentials_menu_exchangerate.add_command(label="Change base URL",
                                                  command=partial(self.write_cfg, "exchangerate", "url"))
        credentials_menu_exchangerate.add_command(label="Change API key",
                                                  command=partial(self.write_cfg, "exchangerate", "api_key"))
        credentials_menu_exchangerate.add_command(label="Get API key",
                                                  command=partial(webbrowser.open_new,
                                                                  r"https://app.exchangerate-api.com/sign-up"))
        credentials_menu.add_cascade(label="ExchangeRate", menu=credentials_menu_exchangerate)
        menubar.add_cascade(label="Credentials", menu=credentials_menu)

        self.config(menu=menubar)

    def open_config(self):
        """Opens the config.ini file"""
        try:
            os.startfile("config.ini")
        except Exception as e:
            print(e)

    def write_cfg(self, section=None, option=None, value=None):
        """Overwrites  the config.ini file

        Parameters
        ----------
        section : string
            Section in config
        option : string
            Option in config
        value : any or None
            Value to write to config, will be converted to string; Creates prompt if no value is given

        Examples
        --------
        ::

            # Write a hard-coded value
            self.write_cfg(section="general", option="main_currency", value="EUR")

            # prompt for a value
            self.write_cfg(section="bitpanda", option="api_key")
        """
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
                    self.refresh_tooltips()

    def refresh_tooltips(self):
        """Refresh tooltips to update stringvars after a config-change. Additionally changes label texts and colors"""

        # iterate over available widgets
        for wdg_id, wdg in self.wdgs.items():

            # go further if widget is StringVar
            if isinstance(wdg, StringVar):

                # skip widgets ending with _displayvar to make following block of code work
                if wdg_id.endswith("_displayvar"):
                    continue

                # skip widgets who do not resemble api key status
                if wdg_id.endswith("api_key"):

                    # if value is not "None", set label to "Set", highlight green and put related value as tooltip
                    if wdg.get() != "None":
                        self.wdgs[f"{wdg_id}_displayvar"].set(f"Set")
                        self.wdgs[f"{wdg_id}_label"].config(fg="green")
                        create_tooltip(self.wdgs[f"{wdg_id}_label"], f"Set to: {wdg.get()}")

                    # if it is "None", set to "Not set", colorcode and create tooltip explaining how to set API key
                    else:
                        self.wdgs[f"{wdg_id}_displayvar"].set(f"Not set")
                        self.wdgs[f"{wdg_id}_label"].config(fg="red")
                        create_tooltip(self.wdgs[f"{wdg_id}_label"], f"Set via Credentials > "
                                                                     f"{wdg_id.split('_')[0].title()} > "
                                                                     f"Change API key\n"
                                                                     f"Get a new API key via Credentials > "
                                                                     f"{wdg_id.split('_')[0].title()} > Get API key")

        self.update_idletasks()

    def get_assets(self):
        """Get assets from bitpanda wallets. Requires valid Bitpanda API key

        Notes
        -----
        Requires additional forex crypto & exchangerate API keys if enable_conversion is True (Convert checkbox in GUI)
        """
        enable_conversion = self.wdgs["convert_assets_var"].get()
        debug_text = not self.wdgs["convert_assets_debug_var"].get()
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

        # try to fetch wallet data
        try:
            wallet_data = get_asset_wallets(enable_conversion=enable_conversion, bitpanda_api_key=bitpanda_api_key,
                                            forex_api_key=forex_api_key, exchangerate_api_key=exchangerate_api_key,
                                            conversion_currency=conversion_currency, conversion_silent=debug_text,
                                            conversion_alt_currencies=conversion_alt_currencies)
        except ValueError as e:
            self.wdgs["current_balance_var"].set("API key error!")
            create_tooltip(self.wdgs["current_balance"], e)
            self.wdgs["current_balance"].config(fg="red")
            return

        if not wallet_data:
            return

        # write to temporary file
        if export_as_json:
            write_to_temporary_file(wallet_data)

        # set StringVar to sum of converted values
        if "summary_cryptocoin" in wallet_data:
            converted_crypto_sum = wallet_data["summary_cryptocoin"][f"Sum {conversion_currency}"]
            self.wdgs["current_balance_var"].set(str(round(converted_crypto_sum, 2)))
        else:
            self.wdgs["current_balance_var"].set("Not converted")

        # create tooltip from return_string
        if "exchange_rates" in wallet_data:
            wallet_data["return_string"] += f"\n!!!! Not converted coins: " \
                                            f"{wallet_data['exchange_rates']['Not converted coins']} !!!!"
        create_tooltip(self.wdgs["current_balance"], wallet_data["return_string"])

    def get_trades(self):
        """Get crypto trade history from bitpanda wallet. Requires valid Bitpanda API key"""
        # TODO: tooltip auf self.wdgs["get_trades_result"] zahl auf self.wdgs["get_trades_var"]
        bitpanda_api_key = self.cfg.get("bitpanda", "api_key")
        export_as_json = self.wdgs["get_trades_export_var"].get()

        # fetch trade data
        trade_data = get_trades(bitpanda_api_key=bitpanda_api_key)

        if not trade_data:
            return

        # set values to StringVars
        self.wdgs["get_trades_amount_var"].set(len(trade_data["balance_data"]))
        self.wdgs["get_trades_invested_var"].set(trade_data["total_invested"])

        # resolve crypto IDs to names
        crypto_resolver = resolve_bitpanda_crypto_ids(bitpanda_api_key=bitpanda_api_key)

        # create tooltip
        tmp_tooltip = f"{'type'.center(8)} | {'coin'.center(8)} | {'amount_fiat'.center(15)} | " \
                      f"{'amount_crypto'.center(20)} | {'time'.center(35)}"
        tmp_tooltip += "\n" + "-"*len(tmp_tooltip)
        for row in trade_data["balance_data"]:
            try:
                tmp_tooltip += "\n" + f'{row["attributes"]["type"].center(8)} | ' \
                                      f'{crypto_resolver[int(row["attributes"]["cryptocoin_id"])].center(8)} | ' \
                                      f'{row["attributes"]["amount_fiat"].center(15)} | ' \
                                      f'{str(round(float(row["attributes"]["amount_cryptocoin"]), 2)).center(20)} | ' \
                                      f'{row["attributes"]["time"]["date_iso8601"].center(35)}'
            except Exception as e:
                print(e)
                print(row["attributes"]["cryptocoin_id"])
                print(crypto_resolver.keys())
        create_tooltip(self.wdgs["get_trades_amount"], tmp_tooltip)

        # write to temporary file
        if export_as_json:
            write_to_temporary_file(trade_data["balance_data"])

    def get_fiat(self):
        """Get fiat wallets and transactions from bitpanda API"""
        bitpanda_api_key = self.cfg.get("bitpanda", "api_key")
        export_as_json = self.wdgs["get_fiat_export_var"].get()

        # fetch fiat wallets and transactions
        fiat_wallet_data = get_fiat_wallets(bitpanda_api_key=bitpanda_api_key)
        fiat_transaction_data = get_fiat_transactions(bitpanda_api_key=bitpanda_api_key)

        if export_as_json:
            export_dict = {"fiat_wallet_data": fiat_wallet_data["fiat_data"],
                           "fiat_transaction_data": fiat_transaction_data["transaction_data"]}
            write_to_temporary_file(export_dict)

        wallet_info = []
        for wallet in fiat_wallet_data["fiat_data"]:
            if float(wallet["attributes"]["balance"]) != 0:
                wallet_info.append(f"{wallet['attributes']['balance']} {wallet['attributes']['fiat_symbol']}")

        if wallet_info:
            wallet_info = ", ".join(wallet_info)
        else:
            wallet_info = "0"

        self.wdgs["get_fiat_balance_var"].set(wallet_info)
        self.wdgs["get_fiat_transactions_var"].set(len(fiat_transaction_data['transaction_data']))

        create_tooltip(self.wdgs["get_fiat_balance"], fiat_wallet_data["return_string"])
        create_tooltip(self.wdgs["get_fiat_transactions"], fiat_transaction_data["return_string"])


if __name__ == '__main__':
    """Boilerplate code - creates default config.ini on first start"""

    # check if config.ini exists, if not, write default hardcoded config.ini
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

        # write to file
        with open("config.ini", "w") as cfg:
            cfg.write(default_ini)

    # call UI class
    app = UI()

    # set window title
    app.title(f"leysolutions.com | Crypto UI")
    # app.overrideredirect(1)  # remove top badge
    # app.attributes("-toolwindow", True)
    # app.geometry("300x300")
    # style = ThemedStyle(app)
    # style.set_theme("plastik")
    app.mainloop()
