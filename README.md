[![build status](
  http://img.shields.io/travis/Mnikley/Python-UI-Collection/master.svg?style=flat)](
 https://travis-ci.org/Mnikley/Python-UI-Collection)
 [![Total alerts](https://img.shields.io/lgtm/alerts/g/Mnikley/Python-UI-Collection.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/Mnikley/Python-UI-Collection/alerts/)
 [![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/Mnikley/Python-UI-Collection.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/Mnikley/Python-UI-Collection/context:python)

# Python UI Collection
This repository is a collection of Python User Interfaces including templates to develop UIs yourself, snippets and more-or-less finished UIs for various purposes. **Feel free to contribute by creating a pull request!**

### Table of Contents  
- [TKinter Template](#tkinter-template)
- [TKinter Bitpanda](#tkinter-bitpanda)
- [TKinter DatabaseAdmin](#tkinter-databaseadmin)
- [TKinter Snippets](#tkinter-snippets)
- [Kivy Template](#kivy-template)
- [Kivy Snippets](#kivy-snippets)

# Tkinter Template
Tkinter Template for Desktop Applications; Includes customized classes for scrollable frames, various themes (based on ttkthemes), loading animations, tooltips, config parser, MongoDB API, JSON editor and more

### Setup
1. Clone repository: `git clone https://github.com/Mnikley/Python-UI-Collection`
2. Navigate to folder: `cd Tkinter/Template`
3. Install requirements: `python -m pip install -r requirements.txt`
4. Run GUI: `python GUI.py`
<div align="center">
  <img src="https://user-images.githubusercontent.com/75040444/132994677-9fb3b5f0-9f16-4bbc-a24a-9a9fab63c93f.png" alt="tkinter template" width="512" height="256">
</div>

# Tkinter Bitpanda
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

<div align="center">
  <table>
    <tr>
      <th align="center">
        <img src="https://user-images.githubusercontent.com/75040444/151707378-426e8f74-4be0-402b-a301-a150a4f8c0bc.png" alt="bitpanda app" width="128" height="256">
      </th>
      <th align="center">
        <img src="https://user-images.githubusercontent.com/75040444/151707374-9d53c7a3-0409-4baf-9211-0be3de3f494d.png" width="256" height="128">
        <br>
        <img src="https://user-images.githubusercontent.com/75040444/151707380-2a31bb7b-48ed-4474-86c8-671b174f5335.png" alt="bitpanda app console" width="256" height="128">
      </th>
    </tr>
  </table>
</div>

# Tkinter DatabaseAdmin
Tool i developed to help me manage my PostgreSQL database on a RaspberryPi, mainly for selecting and updating and deleting rows in an already created table. Functions to create a new table and MongoDB functionalities are WIP.

### Setup
1. Clone repository: `git clone https://github.com/Mnikley/Python-UI-Collection`
2. Navigate to folder: `cd Tkinter/DatabaseAdmin`
3. Install requirements: `python -m pip install -r requirements.txt`
4. Run GUI: `python gui.py`

<div align="center">
  <img src="https://user-images.githubusercontent.com/75040444/151666983-49201450-4f77-42cc-b357-8d523e330220.png" alt="database admin app" width="312" height="256">
  <img src="https://user-images.githubusercontent.com/75040444/151666999-fe2b824e-5c96-42a3-a874-b73a26fff357.png" alt="database admin update" width="456" height="256">
  <img src="https://user-images.githubusercontent.com/75040444/151667023-c72f4a43-9ea6-4590-aee1-5560296eec4b.png" alt="database admin delete" width="512" height="256">
  <img src="https://user-images.githubusercontent.com/75040444/151667072-599a39ca-7b86-46b9-ae50-b66836d1ae17.png" alt="database admin create" width="256" height="256">
</div>

# Tkinter Snippets
Collection of small tkinter apps and snippets available at `Tkinter/Snippets/`
- `DungeonsAndDragons/dnd.py` - WIP of tkinter drag-and-drop application, e.g. for building an interactive dungeons and dragons map. [Picture source](https://angelamaps.com/2021/09/28/island/)
- `draw_polygon_color.py` - Drawing app; Left-click = draw polygon; Doubleclick = fill polygon; Rightclick = select different fill-color
- `frame_change_background_color.py` - Change frame background color after button click
- `table_app.py` - Spreadsheet app based on [pandastable](https://github.com/dmnfarrell/pandastable)
- `table_app_lite.py` - Lightweight spreadsheet app based on [tksheet](https://github.com/ragardner/tksheet)
- `redirect_console_to_textbox.py` - Redirect stdout & stderr to ScrolledText
- `resize_window_locked_aspects.py` - Keep window proportion after resizing window
- `rightclick_menu_copy_paste.py` - Test of a rightclick menu
- `text_editor.py` - Text-editor with line-numbers (save function not implemented)

---

# Kivy Template
This template should help to get started on how to create responsive desktop applications with the [kivy framework](https://kivy.org/#home) including its [wide variety of widgets](https://kivy.org/doc/stable/api-kivy.uix.html). This template includes additional classes to enable tooltips and other usefull stuff.

### Setup
1. Clone repository: `git clone https://github.com/Mnikley/Python-UI-Collection`
2. Navigate to folder: `cd Kivy/Template`
3. Install requirements: `python -m pip install -r requirements.txt`
4. Run GUI: `python GUI.py`

<div align="center">
  <img src="https://user-images.githubusercontent.com/75040444/137364780-a6db3d78-a21f-4f28-a796-ead600a5743a.png" alt="kivy template launch screen" width="512" height="256">
  <img src="https://user-images.githubusercontent.com/75040444/137365136-e2081127-b3cd-47a0-a49f-acbd1657343a.png" alt="kivy template" width="512" height="256">
  <img src="https://user-images.githubusercontent.com/75040444/137365197-dca534d4-f494-4ce2-a69e-3301c2b570d9.png" alt="kivy template tooltips" width="512" height="256">
</div>

# Kivy Snippets
Collection of small kivy apps and snippets available at `Kivy/Snippets/`
- `tooltips/tooltip_test.py` - Standalone tooltip classes and examples to add hover-behaviour to Button, Switch and Slider. Used in template
- `file_editor/main.py` - Load/edit/save text-based files with filechooser
- `loop_clock/loop.py` - Simple example of a scheduled thread via Clock
- `graph_objects.py` - Official example of kivy graph objects
- `animated_graph.py` - Example of threaded animated graph, requires `kivy.garden.graph`
- `MD_graph.py` - Example of graph embedded in KivyMD app, requires `kivymd` and `kivy.garden.graph`
