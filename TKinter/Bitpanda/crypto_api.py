"""
Module to get Bitpanda wallet & transaction information and fetches current coin values from fcsapi.com
- Requires Bitpanda API Key: https://web.bitpanda.com/apikey
- Requires Forex Crypto Stock API Key; Documentation: https://fcsapi.com/document/crypto-api
- Requires ExchangeRate-API key obtained from https://app.exchangerate-api.com/sign-up
- BitPanda API Documentation: https://developers.bitpanda.com/platform/#/wallets-get
"""
import os
import tempfile
import time
import json
import requests
import datetime


def __get_data(root_url="https://api.bitpanda.com/v1/", sub_url="", headers=None, bitpanda_api_key=None):
    """Supplementary function to get response data as json
    - Reads data from multiple pages"""

    # default header
    if not headers:
        headers = {"X-API-KEY": bitpanda_api_key}

    # execute requests GET
    try:
        resp = requests.get(root_url + sub_url, headers=headers)
    except Exception as e:
        print(e)
        return False

    # return array
    return_data = []

    # check status code
    if resp.status_code == 200:
        response = resp.json()

        if "data" not in response:
            return response

        elif "meta" not in response and "links" not in response:
            return response["data"]

        else:
            # append current response data to return_data
            [return_data.append(f) for f in response["data"]]

            # iterate as long as there are 'next' links in response data, append response data to return_data
            while True:
                # stop loop when there is no 'next' in response['links']
                if "next" not in response["links"]:
                    break

                # fetch new page data
                print(f"Fetching page {response['meta']['page']} ..")
                resp = requests.get(root_url + sub_url + response["links"]["next"], headers=headers)
                response = resp.json()

                # append response data to return_data
                [return_data.append(f) for f in response["data"]]

            print(f"Fetched {len(return_data)} entries")
            return return_data

    elif resp.status_code == 401:
        print("Bitpanda: Wrong API Key / Access token!")
        return
    elif resp.status_code == 500:
        print("Bitpanda: Internal server error!")
        return
    elif resp.status_code == 422:
        print("Bitpanda: API key expired!")
        return
    else:
        print(f"Bitpanda: Unknown status code received: {resp.status_code}")
        return


def resolve_bitpanda_crypto_ids(bitpanda_api_key=None):
    """Resolve Bitpanda cryptocoin_id to descriptive name"""
    if not bitpanda_api_key:
        return

    wallet_data = __get_data(sub_url="asset-wallets", bitpanda_api_key=bitpanda_api_key)

    if not wallet_data:
        return

    return_dict = {}

    # iterate over wallets in wallet_data to append cryptocoin_id as key and cryptocoin_symbol as value to dict
    for coin in wallet_data["attributes"]["cryptocoin"]["attributes"]["wallets"]:

        # skip empty coins
        if float(coin["attributes"]["balance"]) == 0:
            continue

        # append to dict
        return_dict[int(coin["attributes"]["cryptocoin_id"])] = coin["attributes"]["cryptocoin_symbol"]

    return return_dict


def __get_exchange_rates(fcsapi_key=None, fcsapi_root_url="https://fcsapi.com/api-v3/",
                         exchangerateapi_key=None, exchangerateapi_root_url="https://v6.exchangerate-api.com/v6/",
                         bitpanda_api_key=None, currency="EUR", alt_currencies=["BTC", "USD"], silent=False):
    """Get most recent exchange rates for coins in portfolio, converts to EUR
    - based on Forex stock exchange API and ExchangeRate-API
    - requires API keys

    Parameters
    ----------
    fcsapi_key : basestring
        FCSApi key obtained from https://fcsapi.com/document/crypto-api
    exchangerateapi_key : basestring
        ExchangeRate-API key obtained from https://app.exchangerate-api.com/sign-up
    currency : basestring
        Main currency to convert crypto values to
    alt_currencies : list
        List of strings with alternative currencies to convert crypto values to
    """

    alt_currencies = alt_currencies

    # fetch symbols (1 request)
    url = f"{fcsapi_root_url}crypto/list?type=crypto&access_key={fcsapi_key}"
    try:
        forex_symbols = requests.get(url).json()
    except Exception as e:
        print(e)
        print("*"*120)
        print(f"Fetching URL failed: {url}")
        return
    if not silent:
        print(f" Fetched {len(forex_symbols['response'])} symbols from fcsapi.com ".center(120, "*"))

    # verify all bitpanda symbols exist in forex API
    bitpanda_coins = resolve_bitpanda_crypto_ids(bitpanda_api_key=bitpanda_api_key)
    bitpanda_coins = list(bitpanda_coins.values())
    if not silent:
        print(f" Trying to verify {len(bitpanda_coins)} bitpanda symbols ".center(120, "*"))

    # list for coins which can be fetched directly, coins who need to be converted and coins who can not be found
    coins_available, coins_to_be_converted, coins_corrected = [], [], []

    # final output: exchange rates dictionary
    exchange_rates = {}

    # iterate over forex symbols 1st time
    for forex_symbol in forex_symbols["response"]:

        # iterate over required bitpanda symbols
        for bitpanda_idx, bitpanda_coin in enumerate(bitpanda_coins):

            # check if COIN/CURRENCY is available as is
            if f"{bitpanda_coin}/{currency}" in forex_symbol["symbol"]:
                if not silent:
                    print(f"Found: {bitpanda_coin}/{currency}")
                coins_available.append(f"{bitpanda_coin}/{currency}")
                bitpanda_coins.pop(bitpanda_idx)

            # apply corrections TODO: make this in form of a list or dict
            elif f"BESTb/{currency}" in forex_symbol["symbol"] and bitpanda_coin == "BEST":
                if not silent:
                    print(f"Corrected coin: BEST > BESTb/{currency}")
                coins_corrected.append(f"BESTb/{currency}")
                bitpanda_coins.pop(bitpanda_idx)

            # apply corrections
            elif "BTTN/BTC" in forex_symbol["symbol"] and bitpanda_coin == "BTT":
                if not silent:
                    print(f"Corrected coin: BTT > BTTN/BTC")
                coins_corrected.append("BTTN/BTC")
                bitpanda_coins.pop(bitpanda_idx)

            # apply corrections
            elif "OCEANp/BTC" in forex_symbol["symbol"] and bitpanda_coin == "OCEAN":
                if not silent:
                    print(f"Corrected coin: OCEAN > OCEANp/BTC")
                coins_corrected.append("OCEANp/BTC")
                bitpanda_coins.pop(bitpanda_idx)

    # iterate over forex symbols 2nd time
    for forex_symbol in forex_symbols["response"]:

        # doing this to keep lists unique - iterate over required bitpanda symbols again
        for bitpanda_idx, bitpanda_coin in enumerate(bitpanda_coins):

            # check if COIN is available for CURRENCY in conversion_currencies
            split_symbol, split_target = forex_symbol["symbol"].split("/")
            if split_symbol == bitpanda_coin and split_target in alt_currencies:
                if not silent:
                    print(f"Found alternative: {split_symbol} > {split_target}")
                coins_to_be_converted.append(f"{split_symbol}/{split_target}")
                bitpanda_coins.pop(bitpanda_idx)

    # verify that alt-currency conversions exist in forex_symbols
    conversions = []
    if not silent:
        print(" Checking conversions on Forex API & ExchangeRate API ".center(120, "*"))
    for forex_symbol in forex_symbols["response"]:
        for idx, alt_currency in enumerate(alt_currencies):
            if forex_symbol["symbol"] == f"{alt_currency}/{currency}":
                if not silent:
                    print(f"Conversion found in Forex API: {alt_currency}/{currency}")
                conversions.append(forex_symbol["symbol"])
                _removed_alt_currency = alt_currencies.pop(idx)
                print("Removed", _removed_alt_currency)

    # if alt-currencies remain, check ExchangeRate-API for conversion rates
    if alt_currencies:
        for idx, alt_currency in enumerate(alt_currencies):
            url = f'{exchangerateapi_root_url}{exchangerateapi_key}/latest/{alt_currency}'
            try:
                ex_request = requests.get(url)
            except Exception as e:
                print(e)
                print("*"*120)
                print(f"Fetching URL failed:\n{url}")
                return
            if ex_request.status_code != 200:
                print(f"Error: {ex_request.status_code} - no rate for {alt_currency} found!")
            else:
                ex_data = ex_request.json()
                if currency in ex_data["conversion_rates"].keys():
                    exchange_rates[f"{alt_currency}/{currency}"] = ex_data["conversion_rates"][currency]
                    if not silent:
                        print(f"Conversion found in ExchangeRate API: {alt_currency}/{currency} "
                              f"({ex_data['conversion_rates'][alt_currency]} : "
                              f"{ex_data['conversion_rates'][currency]})")
                    _removed_alt_currency = alt_currencies.pop(idx)
                    print("Removed", _removed_alt_currency)

    # fetch conversion rates from forex API fcsapi.com
    if not silent:
        print(f" Fetching {len(coins_available) + len(coins_to_be_converted) + len(coins_corrected) + len(conversions)}"
              f" conversion rates from fcsapi.com ".center(120, "*"))
    coin_symbols = f"{','.join(coins_available)},{','.join(coins_to_be_converted)}," \
                   f"{','.join(coins_corrected)},{','.join(conversions)}"
    url = f"{fcsapi_root_url}crypto/latest?symbol={coin_symbols}&access_key={fcsapi_key}"
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Error: {response.status_code} - Fetching conversion rates from fcsapi.com failed. Check URL:\n{url}")

    # attach conversion rates to output dict
    forex_conversion_rates = response.json()["response"]

    # {
    #   "s": "BTC/USD",  // Symbol
    #   "o": "8767.415375", // Open
    #   "h": "8740.166220", // High
    #   "l": "8924.587238", // Low
    #   "c": "8892.841263", // Price/Close
    #   "a": "8891.852840", // Ask
    #   "b": "8894.818768", // Bid
    #   "ch": "125.425888", // Change in 1 day candle
    #   "cp: "1.43%", // Change in percentage
    #   "t": "1583238543", // When update last time Time Unix Format (UTC)
    #   "tm": "2020-03-03 12:29:03" // When update last time (UTC)
    # },

    # iterate over return, attach symbols which convert directly into currency to exchange_rates dict
    for conversion in forex_conversion_rates:
        if conversion["s"].split("/")[-1] == currency:
            exchange_rates[conversion["s"]] = conversion["c"]
    # iterate over return, convert symbols which cannot be converted directly with the help of already-converted symbols
    temp_dict = {}
    for conversion in forex_conversion_rates:
        __symbol = conversion["s"]
        __price = conversion["c"]
        if __symbol.split("/")[-1] != currency:
            for __proper_symbol_key, __proper_symbol_val in exchange_rates.items():
                if __symbol.split("/")[-1] == __proper_symbol_key.split("/")[0]:
                    conversion_factor = float(__price)*float(__proper_symbol_val)
                    tmp = f"{__symbol} {__price} to {__proper_symbol_key} {__proper_symbol_val}"
                    new_key = __symbol.split("/")[0] + "/" + __proper_symbol_key.split("/")[-1]
                    if not silent:
                        print(f"Converting {tmp:<60} | {new_key} {conversion_factor}")
                    temp_dict[new_key] = conversion_factor

    # join dicts
    exchange_rates = {**exchange_rates, **temp_dict}
    if not silent:
        print("*"*120)
        print(f"No conversions found for: {bitpanda_coins}")
        print(f" {len(exchange_rates)} exchange rates generated. This has cost you 2 fcsapi.com credits ")
        print("*"*120)

    if silent:
        print(f" {len(exchange_rates)} exchange rates generated. This has cost you 2 fcsapi.com credits ".center(120,
                                                                                                                 "*"))

    # add not converted coins to output dict
    exchange_rates["Not converted coins"] = bitpanda_coins

    # undo corrections
    for _coin in ["BESTb", "BTTN", "OCEANp"]:
        if _coin in exchange_rates.keys():
            # strip last char from key by removing old key/value pair and adding new one
            exchange_rates[f"{_coin[:-1]}/{currency}"] = exchange_rates.pop(f"{_coin}/{currency}")

    return exchange_rates


def get_trades(bitpanda_api_key=None):
    """Get trading information, calculate total invested amount"""
    if not bitpanda_api_key:
        return

    balance_data = __get_data(sub_url="trades", bitpanda_api_key=bitpanda_api_key)
    total_invested = 0
    if not balance_data:
        return

    for trade in balance_data:
        total_invested += float(trade["attributes"]["amount_fiat"])

    print(f"Total invested: {total_invested}")

    return {"balance_data": balance_data, "total_invested": total_invested}


def get_asset_wallets(enable_conversion=False, bitpanda_api_key=None, forex_api_key=None, exchangerate_api_key=None,
                      conversion_currency="EUR", conversion_alt_currencies=["BTC", "USD"], conversion_silent=True):
    """Get asset wallet information (crypto, metal, index, stocks, etf)"""
    if not bitpanda_api_key:
        raise ValueError("Please provide bitpanda_api_key!")

    if enable_conversion:
        if not forex_api_key or forex_api_key == "None":
            raise ValueError("Please provide forex_api_key!")
        if not exchangerate_api_key or forex_api_key == "None":
            raise ValueError("Please provide exchangerate_api_key!")

    # fetch wallet_data from bitpanda API
    wallet_data = __get_data(sub_url="asset-wallets", bitpanda_api_key=bitpanda_api_key)
    if not wallet_data:
        return

    # pre-define output dictionary
    wallets = {"return_string": ""}

    # fetch conversion data if enable_conversion is True
    if enable_conversion:
        conversion_rates = __get_exchange_rates(fcsapi_key=forex_api_key, exchangerateapi_key=exchangerate_api_key,
                                                bitpanda_api_key=bitpanda_api_key, currency=conversion_currency,
                                                alt_currencies=conversion_alt_currencies, silent=conversion_silent)

    # header
    tmp_filler = f"Current Value [{conversion_currency}]"
    tmp = ["", f" | {tmp_filler:<20}"][enable_conversion]
    sep_length = [66, 89][enable_conversion]
    header_text = f"{'Symbol':<20} | {'Balance':<20} | {'Name':<20}{tmp}"
    print(header_text)
    wallets["return_string"] += f"{header_text}\n{'-'*sep_length}\n"

    # iterate over assets, collect wallet information and create formatted dict 'wallets'
    for asset in wallet_data["attributes"].keys():

        if "attributes" in wallet_data["attributes"][asset].keys():
            wallets[asset] = wallet_data["attributes"][asset]["attributes"]["wallets"]
        else:
            for sub_asset in wallet_data["attributes"][asset].keys():
                wallets[sub_asset] = wallet_data["attributes"][asset][sub_asset]["attributes"]["wallets"]

    tmp_wallet = {}
    for asset, asset_data in wallets.items():
        if asset == "return_string":
            continue

        converted_sum = 0
        # pre-evaluate if balances in asset are all zero
        sum_wallets = sum([float(f["attributes"]["balance"]) for f in asset_data])
        if sum_wallets == 0:
            print(f" No {asset} wallets detected ".center(sep_length, "*"))
            continue

        # print header for wallets
        print(f" {len(asset_data)} {asset} wallets ".center(sep_length, "*"))

        # iterate over wallets in asset (formatted dict)
        for wallet in asset_data:
            tmp = wallet["attributes"]

            # skip empty wallets
            if float(tmp["balance"]) == 0:
                continue

            # calculate converted values
            converted_val = ""
            if enable_conversion:
                for key, val in conversion_rates.items():
                    if tmp["cryptocoin_symbol"] == key.split("/")[0]:
                        converted_val = float(val) * float(tmp["balance"])
                        converted_sum += converted_val

            tmp_convert = ["", f" | {converted_val}"][enable_conversion]

            # print information and append to return_string
            tmp_str = f"{tmp['cryptocoin_symbol']:<20} | {tmp['balance']:<20} | {tmp['name']:<20}{tmp_convert}"
            print(tmp_str)
            wallets["return_string"] += f"{tmp_str}\n"

        # print converted sum at end
        if enable_conversion and converted_sum != 0:
            tmp_wallet[f"summary_{asset}"] = {f"Sum {conversion_currency}": converted_sum,
                                              "Timestamp": datetime.datetime.now()}
            print("-"*sep_length)
            sum_text = f"{'':<66} | {converted_sum:<20}"
            print(sum_text)
            wallets["return_string"] += f"{'-'*sep_length}\n{sum_text}\n{'-'*sep_length}\n"

    # join dicts, append conversion_rates
    if enable_conversion:
        wallets = {**wallets, **tmp_wallet, "exchange_rates": conversion_rates}
    else:
        wallets = {**wallets, **tmp_wallet}

    return wallets


def get_fiat_wallets(bitpanda_api_key=None, skip_empty_wallets=False):
    """Get fiat wallet information"""
    if not bitpanda_api_key:
        return

    # fetch fiat wallet data
    fiat_data = __get_data(sub_url="fiatwallets", bitpanda_api_key=bitpanda_api_key)

    # predefine return string
    return_string = ""

    # print header
    tmp_header = f" {len(fiat_data)} fiat wallets ".center(66, "*")
    print(tmp_header)
    return_string += f"{tmp_header}\n"

    # iterate over fiat wallet data
    if not fiat_data:
        return

    for fiat_wallet in fiat_data:
        tmp = fiat_wallet["attributes"]

        if skip_empty_wallets:
            if float(tmp["balance"]) == 0:
                continue

        # print information
        tmp_text = f"{tmp['fiat_symbol'].center(20)} | {tmp['balance'].center(20)} | {tmp['name'].center(20)}"
        print(tmp_text)
        return_string += f"{tmp_text}\n"

    return {"fiat_data": fiat_data, "return_string": return_string}


def get_fiat_transactions(bitpanda_api_key=None):
    """Get all transactions"""
    if not bitpanda_api_key:
        return

    # get transaction data
    transaction_data = __get_data(sub_url="fiatwallets/transactions", bitpanda_api_key=bitpanda_api_key)

    # get lookup-table
    lookup = resolve_bitpanda_crypto_ids(bitpanda_api_key=bitpanda_api_key)

    # predefine return string
    return_string = ""

    # header
    header_tmp = f"{'Time'.center(30)} | {'Type'.center(10)} | {'Fiat ID'.center(10)} | {'Fiat Amount'.center(15)} | " \
                 f"{'Crypto ID'.center(16)} | {'Crypto Amount'.center(20)} | {'Price'.center(20)}"
    print(header_tmp)
    return_string += f"{header_tmp}\n"
    header_sep_tmp = f" {len(transaction_data)} fiat transactions ".center(139, "*")
    print(header_sep_tmp)
    return_string += f"{header_sep_tmp}\n"

    # iterate over transactions
    if not transaction_data:
        return

    for transaction in transaction_data:
        tmp = transaction["attributes"]

        # print information
        tmp_time = " ".join(tmp["time"]["date_iso8601"].replace("T", " ").split())
        if tmp["type"] in ["buy", "sell"]:
            trade = tmp["trade"]["attributes"]
            if int(trade["cryptocoin_id"]) in lookup.keys():
                trade["cryptocoin_id"] = f"{trade['cryptocoin_id'].center(5)} | " \
                                         f"{lookup[int(trade['cryptocoin_id'])].center(6)}"
            tmp_str = f"{tmp_time.center(30)} | {tmp['type'].center(10)} | {trade['fiat_id'].center(10)} | " \
                      f"{trade['amount_fiat'].center(15)} | {trade['cryptocoin_id'].center(16)} | " \
                      f"{trade['amount_cryptocoin'].center(20)} | {trade['price'].center(20)}"
            print(tmp_str)
            return_string += f"{tmp_str}\n"
        elif tmp["type"] == "deposit":
            tmp_str = f"{tmp_time.center(30)} | {tmp['type'].center(10)} | " \
                      f"{tmp['fiat_id'].center(10)} | {tmp['amount'].center(15)} {'-'*64}"
            print(tmp_str)
            return_string += f"{tmp_str}\n"
        elif tmp["type"] == "transfer":
            _tmp_from_to = f" {tmp['in_or_out']} - {tmp['from']} > {tmp['recipient']} "
            tmp_str = f"{tmp_time.center(30)} | {tmp['type'].center(10)} | {tmp['fiat_id'].center(10)} | " \
                      f"{tmp['amount'].center(15)} | {_tmp_from_to.center(62, '*')}"
            print(tmp_str)
            return_string += f"{tmp_str}\n"
        else:
            tmp_str = f"Unknown transaction type: {tmp['type']}"
            print(tmp_str)
            return_string += f"{tmp_str}\n"

    return {"transaction_data": transaction_data, "return_string": return_string}


def get_currency_information():
    """Get currency information from Bitpanda Pro API"""
    currency_data = __get_data(root_url="https://api.exchange.bitpanda.com/public/v1/currencies",
                               headers={"Accept": "application/json"})
    print(currency_data)


class DateTimeEncoder(json.JSONEncoder):
    def default(self, z):
        if isinstance(z, datetime.datetime):
            return str(z)
        else:
            return super().default(z)


def write_to_temporary_file(data=None, suffix=".json"):
    """Write data to a temporary file"""
    temp_file = tempfile.NamedTemporaryFile(suffix=suffix)
    if suffix == ".json":
        temp_file.write(json.dumps(data, indent=4, cls=DateTimeEncoder).encode())
    else:
        temp_file.write(data)
    temp_file.flush()
    os.startfile(temp_file.name)
    time.sleep(1)
    print("Launched temporary file:", temp_file.name)
    temp_file.close()


if __name__ == "__main__":
    print(help(__name__))
