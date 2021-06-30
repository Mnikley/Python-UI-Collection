"""Demo App to demonstrate tooltip functionality for Labels, Buttons, Slider and Switches"""

from kivy.properties import BooleanProperty, ObjectProperty
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.uix.switch import Switch
from kivy.app import App
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from kivy.uix.popup import Popup


class Tooltip(Label):
    pass


class HoverBehavior(object):
    """Hover behavior.
    :Events:
        `on_enter`
            Fired when mouse enter the bbox of the widget.
        `on_leave`
            Fired when the mouse exit the widget
    """

    hovered = BooleanProperty(False)
    border_point = ObjectProperty(None)

    def __init__(self, **kwargs):
        self.register_event_type('on_enter')
        self.register_event_type('on_leave')
        Window.bind(mouse_pos=self.on_mouse_pos)  # for recognizing tooltips
        super(HoverBehavior, self).__init__(**kwargs)

    def on_mouse_pos(self, *args):
        if not self.get_root_window():
            return
        pos = args[1]
        inside = self.collide_point(*self.to_widget(*pos))  # compensate for relative layout
        if self.hovered == inside:
            return
        self.border_point = pos
        self.hovered = inside
        if inside:
            self.dispatch('on_enter')
        else:
            self.dispatch('on_leave')

    def on_enter(self):
        pass

    def on_leave(self):
        pass


class TTLabel(HoverBehavior, Label):
    """Resizable Label with Tooltip, inherits Label and HoverBehaviour class"""

    def __init__(self, **kwargs):
        super().__init__()
        self.tooltip = None  # Attribute set in kv file
        self.markup = True
        self.tooltip_wdg = Tooltip()

    def on_enter(self):
        """Event fires when entering widget"""
        if self.tooltip:  # only binds event if tooltip variable is set
            Window.bind(mouse_pos=lambda w, p: setattr(self.tooltip_wdg, 'pos', p))  # binds position to cursor
            self.tooltip_wdg.text = self.tooltip  # sets text to tooltip variable
            Window.add_widget(self.tooltip_wdg)

    def on_leave(self):
        """Event fires when leaving widget"""
        if self.tooltip:
            Window.remove_widget(self.tooltip_wdg)


class TTButton(HoverBehavior, Button):
    """Resizable Button with Tooltip"""
    def __init__(self, **kwargs):
        super().__init__()
        self.tooltip = None  # Attribute set in kv file
        self.markup = True
        self.tooltip_wdg = Tooltip()

    def on_enter(self):
        """Event fires when entering widget"""
        if self.tooltip:  # only binds event if tooltip variable is set
            Window.bind(mouse_pos=lambda w, p: setattr(self.tooltip_wdg, 'pos', p))  # binds position to cursor
            self.tooltip_wdg.text = self.tooltip  # sets text to tooltip variable
            Window.add_widget(self.tooltip_wdg)

    def on_leave(self):
        """Event fires when leaving widget"""
        if self.tooltip:
            Window.remove_widget(self.tooltip_wdg)


class TTSwitch(HoverBehavior, Switch):
    """Switch with Tooltip"""
    def __init__(self, **kwargs):
        super().__init__()
        self.tooltip = None
        self.tooltip_wdg = Tooltip()
        self.bind(active=self.refresh_tooltip)  # refresh tooltip on value change

    def on_enter(self):
        if self.tooltip:  # only binds event if tooltip variable is set
            Window.bind(mouse_pos=lambda w, p: setattr(self.tooltip_wdg, 'pos', p))  # binds position to cursor
            self.tooltip_wdg.text = self.tooltip  # sets text to tooltip variable
            Window.add_widget(self.tooltip_wdg)

    def on_leave(self):
        if self.tooltip:
            Window.remove_widget(self.tooltip_wdg)

    def refresh_tooltip(self, *args):
        if self.tooltip:
            Clock.schedule_once(self.refresh_tooltip_callback)

    def refresh_tooltip_callback(self, dt):
        self.tooltip_wdg.text = self.tooltip


class TTSlider(HoverBehavior, Slider):
    """Slider with Tooltip"""
    def __init__(self, **kwargs):
        super().__init__()
        self.tooltip = None
        self.tooltip_wdg = Tooltip()
        Window.bind(on_touch_up=self.on_touch_up)  # refresh tooltip on mouse up

    def on_enter(self):
        if self.tooltip:  # only binds event if tooltip variable is set
            Window.bind(mouse_pos=lambda w, p: setattr(self.tooltip_wdg, 'pos', p))  # binds position to cursor
            self.tooltip_wdg.text = self.tooltip  # sets text to tooltip variable
            Window.add_widget(self.tooltip_wdg)

    def on_leave(self):
        if self.tooltip:
            Window.remove_widget(self.tooltip_wdg)

    def on_touch_up(self, *args):
        if self.tooltip:
            self.tooltip_wdg.text = self.tooltip
        # add callback here if wanted


class Root(BoxLayout):
    """ Root class for callbacks, UI building etc."""

    def __init__(self):
        super().__init__()

    def test_function(self):
        print("Seems like i am working")


class UI(App):
    """App class, access attributes from .kv files via app.attribute_name"""

    def __init__(self, **kwargs):
        super().__init__()
        self.root: BoxLayout = None
        self.splash_popup: Popup = None

    def build(self):
        self.root = Root()
        return Root()

    def on_pause(self):
        return True


if __name__ == "__main__":
    Builder.load_file("layout.kv")
    UI().run()
