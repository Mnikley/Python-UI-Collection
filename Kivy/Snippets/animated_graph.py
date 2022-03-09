from kivy.app import App
import numpy as np
from math import sqrt, exp
from kivy.garden.graph import Graph, SmoothLinePlot
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.animation import Animation


class myApp(App):
    lbl=Label(text="0", size_hint_y=0.3)

    S0=50
    mu=0.05
    sig=0.3
    dt=1/365



    graph=Graph(
                    xmin=0, 
                    xmax=50, 
                    ymin=0, 
                    ymax=100, 
                    x_ticks_major=50,
                    y_ticks_major=10,
                    tick_color=[0.06,0.06,0.06,1],
                    draw_border=False,
                    x_grid=True,
                    y_grid=True
    )



    plot2 = SmoothLinePlot(color=[1, 0, 0, 1])
    plot2.opacity = 0
    first_point=(0,50) 
    plot2.points=[first_point]
    graph.add_plot(plot2)
    event=None
    St=S0

    def on_start(self):
        self.event=Clock.schedule_interval(self.update_plot, 1/60)

    def build(self):
        bl=BoxLayout(orientation="vertical")
        bl.add_widget(self.lbl)
        bl.add_widget(self.graph)
        return bl

    def update_plot(self, *ARGS):
        drift=(self.mu-self.sig*self.sig*0.5)*self.dt
        epsilon=np.random.normal()
        var=epsilon*self.sig*sqrt(self.dt)
        self.St=self.St*exp(drift+var)
        last_x2=self.plot2.points[len(self.plot2.points)-1][0]
        new_point2=(last_x2+1, self.St)
        self.plot2.points.append(new_point2)
        self.lbl.text=str(last_x2)
        if last_x2+1==self.graph.xmax:
            Clock.unschedule(self.event)
            self.lbl.text=str("Clocking stopped")
            anim=Animation(opacity=1, duration=5)  #<-- problem here
            anim.start(self.plot2)
        

myApp().run()