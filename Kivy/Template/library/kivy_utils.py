from kivy.properties import BooleanProperty, ObjectProperty
from kivy.core.window import Window
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.uix.switch import Switch
from kivy.clock import Clock


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
        self.header = None  # Attribute set in kv file
        self.markup = True
        self.tooltip_wdg = Tooltip()
        Window.bind(on_resize=self.on_window_resize)  # binds font_size rescaling function to on_resize event
        Clock.schedule_once(self.on_window_resize, 1.5)  # called once at init cuz widget hasnt final size yet

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

    def on_window_resize(self, *args):
        """Event fires when window is rescaled"""
        fire_refresh = True

        # # Fires when horizontal size is too small
        if self.size[0] < self._label.size[0]:
            fire_refresh = False
            self.texture_size[0] = self.size[0] - 4  # reduce texture size to widget size (- 4 for small border)
            if self.size[1] < self._label.size[1]:  # additionally, if vertical size is too small, reduce aswell
                self.texture_size[1] = self.size[1] - 4
                return

        # Fires when vertical size is too small
        if self.size[1] < self._label.size[1]:
            fire_refresh = False
            self.texture_size[1] = self.size[1] - 4
            if self.size[0] < self._label.size[0]:
                self.texture_size[0] = self.size[0] - 4
                return

        # Fires when widget size > texture size  # TODO: is there another way not to fire all the time?
        if fire_refresh:
            self.texture_update()


class TTButton(HoverBehavior, Button):
    """Resizable Button with Tooltip"""
    def __init__(self, **kwargs):
        super().__init__()
        self.tooltip = None  # Attribute set in kv file
        self.markup = True
        self.tooltip_wdg = Tooltip()
        Window.bind(on_resize=self.on_window_resize)  # binds font_size rescaling function to on_resize event
        Clock.schedule_once(self.on_window_resize, 1.5)  # called once at init cuz widget hasnt final size yet
        # alternative method
        # TTButton (self) has some weird initial width at this point (100) > use Window width
        # self.font_size = Window.width/scale_factor_hor if Window.width/scale_factor_hor <= norm_size else norm_size

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

    def on_window_resize(self, *args):
        """Event fires when window is rescaled"""
        fire_refresh = True

        # # Fires when horizontal size is too small
        if self.size[0] < self._label.size[0]:
            fire_refresh = False
            self.texture_size[0] = self.size[0] - 4  # reduce texture size to widget size (-4 for small border)
            if self.size[1] < self._label.size[1]:  # additionally, if vertical size is too small, reduce aswell
                self.texture_size[1] = self.size[1] - 4
                return

        # Fires when vertical size is too small
        if self.size[1] < self._label.size[1]:
            fire_refresh = False
            self.texture_size[1] = self.size[1] - 4
            if self.size[0] < self._label.size[0]:
                self.texture_size[0] = self.size[0] - 4
                return

        # Fires when widget size > texture size  # TODO: is there another way not to fire all the time?
        if fire_refresh:
            # Clock.schedule_once(self.texture_update, 0.5)
            self.texture_update()

        # alternative method & debug text
        # self.font_size = self.width / scale_factor_hor if self.width / scale_factor_hor <= norm_size else norm_size
        # print(f"size: {self.size}\ttexture_size: {self.texture_size}\tparent.size: {self.parent.size}")


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
