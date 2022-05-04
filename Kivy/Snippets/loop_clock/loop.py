from kivy.app import App
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.widget import Widget
from kivy.clock import Clock

Window.size=(300,300)
Builder.load_file('loop.kv')


class MyLayout(Widget):
    loop_thread = None

    def callback_to_loop(self, dt):
        try:
            current = int(self.ids.label_print.text)
        except Exception as e:
            print(e)
            current = 0
        self.ids.label_print.text = str(current+1)
        if current == 11:
            Clock.unschedule(self.loop_thread)

    def loop(self):
        self.loop_thread = Clock.schedule_interval(self.callback_to_loop, 1)


class LoopApp(App):
    def build(self):
        return MyLayout()

if __name__=='__main__':
    LoopApp().run()