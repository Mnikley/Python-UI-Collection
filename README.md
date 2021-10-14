[![build status](
  http://img.shields.io/travis/Mnikley/Python-UI-Collection/master.svg?style=flat)](
 https://travis-ci.org/Mnikley/Python-UI-Collection)
 [![Total alerts](https://img.shields.io/lgtm/alerts/g/Mnikley/Python-UI-Collection.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/Mnikley/Python-UI-Collection/alerts/)
 [![Language grade: JavaScript](https://img.shields.io/lgtm/grade/javascript/g/Mnikley/Python-UI-Collection.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/Mnikley/Python-UI-Collection/context:javascript)
 [![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/Mnikley/Python-UI-Collection.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/Mnikley/Python-UI-Collection/context:python)

# Python UI Collection
This repository is a collection of Python User Interfaces including templates to develop UIs yourself, snippets and more-or-less finished UIs for various purposes. Based on the frameworks Tkinter and Kivy.

# Tkinter Template
Tkinter Template for Desktop Applications; Includes customized classes for scrollable frames, various themes (based on ttkthemes), loading animations, tooltips, config parser, MongoDB API, JSON editor and more

### Setup
1. Clone repository: `git clone https://github.com/Mnikley/Python-UI-Collection`
2. Navigate to folder: `cd Tkinter/Template`
3. Install requirements: `python -m pip install -r requirements.txt`
4. Run GUI: `python GUI.py`

![image](https://user-images.githubusercontent.com/75040444/132994677-9fb3b5f0-9f16-4bbc-a24a-9a9fab63c93f.png)

# Tkinter Bitpanda UI
Lightweight Bitpanda UI to fetch assets (crypto, ETF, index, metal), trades, fiat wallets and transactions via Bitpanda API
- Requires a valid [Bitpanda API Key](https://web.bitpanda.com/apikey)
- For conversion to fiat currencies (e.g. EUR), valid [Forex Crypto Stock API key](https://fcsapi.com/document/crypto-api) as well as a [ExchangeRate API Key](https://app.exchangerate-api.com/sign-up) is required
- Export to .json possible (temporary files which are deleted immediately and are only available in cache)
- Hovering over balances, amount of transactions etc. gives extensive information as Tooltip

### Setup
1. Clone repository: `git clone https://github.com/Mnikley/Python-UI-Collection`
2. Navigate to folder: `cd Tkinter/Bitpanda`
3. Install requirements: `python -m pip install -r requirements.txt`
4. Run GUI: `python crypto_gui.py`
5. Enter valid API keys after first launch via the menu (will be stored in config.ini)

![image](https://user-images.githubusercontent.com/75040444/134688788-5354dc49-a4a3-4575-a3cc-5aa36708f497.png)
![image](https://user-images.githubusercontent.com/75040444/134555724-a53edbb8-db9a-42ad-9bb3-4b122dc74d2b.png)

# Kivy Template
This template should help to get started on how to create responsive desktop applications with the [kivy framework](https://kivy.org/#home) including its [wide variety of widgets](https://kivy.org/doc/stable/api-kivy.uix.html). This template includes additional classes to enable tooltips and other usefull stuff.

### Setup
1. Clone repository: `git clone https://github.com/Mnikley/Python-UI-Collection`
2. Navigate to folder: `cd Kivy/Template`
3. Install requirements: `python -m pip install -r requirements.txt`
4. Run GUI: `python GUI.py`

![image](https://user-images.githubusercontent.com/75040444/137364780-a6db3d78-a21f-4f28-a796-ead600a5743a.png)
![image](https://user-images.githubusercontent.com/75040444/137365136-e2081127-b3cd-47a0-a49f-acbd1657343a.png)
![image](https://user-images.githubusercontent.com/75040444/137365197-dca534d4-f494-4ce2-a69e-3301c2b570d9.png)



