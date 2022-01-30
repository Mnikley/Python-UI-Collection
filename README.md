[![build status](
  http://img.shields.io/travis/Mnikley/Python-UI-Collection/master.svg?style=flat)](
 https://travis-ci.org/Mnikley/Python-UI-Collection)
 [![Total alerts](https://img.shields.io/lgtm/alerts/g/Mnikley/Python-UI-Collection.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/Mnikley/Python-UI-Collection/alerts/)
 [![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/Mnikley/Python-UI-Collection.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/Mnikley/Python-UI-Collection/context:python)

# Python UI Collection
This repository is a collection of Python User Interfaces including templates to develop UIs yourself, snippets and more-or-less finished UIs for various purposes. Based on the frameworks Tkinter and Kivy.

### Table of Contents  
- [TKinter Template](#tkinter-template)
- [TKinter Bitpanda](#tkinter-bitpanda)
- [TKinter DatabaseAdmin](#tkinter-databaseadmin)
- [TKinter Snippets](#tkinter-snippets)
- [Kivy Template](#kivy-template)
- [Kivy Tooltips](#kivy-tooltips)
- [Kivy Snippets](#kivy-snippets)

# Tkinter Template
Tkinter Template for Desktop Applications; Includes customized classes for scrollable frames, various themes (based on ttkthemes), loading animations, tooltips, config parser, MongoDB API, JSON editor and more

### Setup
1. Clone repository: `git clone https://github.com/Mnikley/Python-UI-Collection`
2. Navigate to folder: `cd Tkinter/Template`
3. Install requirements: `python -m pip install -r requirements.txt`
4. Run GUI: `python GUI.py`

![image](https://user-images.githubusercontent.com/75040444/132994677-9fb3b5f0-9f16-4bbc-a24a-9a9fab63c93f.png)

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

![image](https://user-images.githubusercontent.com/75040444/134688788-5354dc49-a4a3-4575-a3cc-5aa36708f497.png)
![image](https://user-images.githubusercontent.com/75040444/134555724-a53edbb8-db9a-42ad-9bb3-4b122dc74d2b.png)

# Tkinter DatabaseAdmin
Tool i developed to help me manage my PostgreSQL database on a RaspberryPi, mainly for selecting and updating and deleting rows in an already created table. Functions to create a new table and MongoDB functionalities are WIP.

### Setup
1. Clone repository: `git clone https://github.com/Mnikley/Python-UI-Collection`
2. Navigate to folder: `cd Tkinter/DatabaseAdmin`
3. Install requirements: `python -m pip install -r requirements.txt`
4. Run GUI: `python gui.py`

![image](https://user-images.githubusercontent.com/75040444/151666983-49201450-4f77-42cc-b357-8d523e330220.png)
![image](https://user-images.githubusercontent.com/75040444/151666999-fe2b824e-5c96-42a3-a874-b73a26fff357.png)
![image](https://user-images.githubusercontent.com/75040444/151667023-c72f4a43-9ea6-4590-aee1-5560296eec4b.png)
![image](https://user-images.githubusercontent.com/75040444/151667072-599a39ca-7b86-46b9-ae50-b66836d1ae17.png)

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

![image](https://user-images.githubusercontent.com/75040444/137364780-a6db3d78-a21f-4f28-a796-ead600a5743a.png)
![image](https://user-images.githubusercontent.com/75040444/137365136-e2081127-b3cd-47a0-a49f-acbd1657343a.png)
![image](https://user-images.githubusercontent.com/75040444/137365197-dca534d4-f494-4ce2-a69e-3301c2b570d9.png)

# Kivy Tooltips
Classes to add hover-behaviour and tooltips for Button, Switch and Slider to kivy applications
Usage example .kv file:
```
<Tooltip>:
    size_hint: None, None
    size: self.texture_size[0]+5, self.texture_size[1]+5
    canvas.before:
        Color:
            rgb: 0.2, 0.2, 0.2
        Rectangle:
            size: self.size
            pos: self.pos

<Root>:
    orientation: 'vertical'
	TTLabel:
		text: "Im a label"
		tooltip: "And im your tooltip"
	TTLabel:
		text: "Im just an ordinary label"
	TTButton:
		text: "Im a button"
		on_release: root.test_function()
		tooltip: "Click it for some action"
	TTSlider:
		tooltip: "Current value: " + str(round(self.value, 2))
	TTSwitch:
		tooltip: ["Switch is off", "Switch is on"][self.active]
```

# Kivy Snippets
Collection of small kivy apps and snippets available at `Kivy/Snippets/`
- `file_editor/main.py` - Load/edit/save text-based files with filechooser
- `loop_clock/loop.py` - Simple example of a scheduled thread via Clock
- `graph_objects.py` - Official example of kivy graph objects
- `animated_graph.py` - Example of threaded animated graph, requires `kivy.garden.graph`
- `MD_graph.py` - Example of graph embedded in KivyMD app, requires `kivymd` and `kivy.garden.graph`
