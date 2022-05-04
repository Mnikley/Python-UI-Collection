from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ObjectProperty
from kivymd.app import MDApp
import matplotlib.pyplot as plt

from kivy.garden.graph import Graph, SmoothLinePlot

KV = '''
<ContentNavigationDrawer>:

    orientation: "vertical"
    padding: "8dp"
    spacing: "8dp"          
                       

Screen:
    MDToolbar:
        id: toolbar
        pos_hint: {"top": 1}
        elevation: 10
        title: "MDNavigationDrawer"
        left_action_items: [["menu", lambda x: nav_drawer.set_state("open")]]
    MDNavigationLayout:
        x: toolbar.height
        
    ScreenManager:
        id: screen_manager
        
        Screen:
            name: "scr Home"
            
            BoxLayout:
                orientation: 'vertical'
                pos_hint: {'center_x': 0.5, 'center_y': 0.68}
                size_hint_x: 0.50
            
                MDLabel:
                    text: "Events"
                    halign: "center"
                    
            MDRaisedButton:
                id: start
                pos_hint: {'center_x': 0.5, 'center_y': 0.5}
                text: 'Go to screen Chart'   
                on_press:
                    app.root.ids.screen_manager.current = "scr Chart"  
                    
                    
        Screen:
            name: "scr Chart"
            
            BoxLayout:
                orientation: 'vertical'
                pos_hint: {'center_x': 0.5, 'center_y': 0.68}
                size_hint_x: 0.50
            
                MDLabel:
                    text: "Chart"
                    halign: "center"
                    
            MDRaisedButton:
                id: start
                pos_hint: {'center_x': 0.5, 'center_y': 0.5}
                text: 'Back to Home'   
                on_press:
                    app.root.ids.screen_manager.current = "scr Home"   
                    
            MDRaisedButton:
                id: showChartID
                pos_hint: {'center_x': 0.9, 'center_y': 0.6}
                text: 'Show Chart'   
                on_press: app.showChart()                    
                     
                    
            BoxLayout:
                id: plotChartLayoutID     
                orientation: "vertical"
                spacing: "10dp"                
                size_hint: 1, 0.4
                                  
                
    MDNavigationDrawer:
        id: nav_drawer
        
        ContentNavigationDrawer:            
            screen_manager: screen_manager
            nav_drawer: nav_drawer        
 
 
'''

plt.plot([1, 23, 2, 4])
plt.ylabel('some numbers')

class ContentNavigationDrawer(BoxLayout):
    screen_manager = ObjectProperty()
    nav_drawer = ObjectProperty()

class TestNavigationDrawer(MDApp):

    def showChart(self):

        samplePoints = [(1, -1.853308), (2, -0.294635), (3, 0.741659), (4, 1.533998), (5, -0.979925), (6, 0.929095), (7, 0.21097), (8, -0.255225), (9, -0.087132), (10, 0.276493), (11, 0.214625), (12, -0.544198), (13, 0.637738), (14, -1.217626), (15, -1.219405), (16, 0.577283), (17, -1.294635), (18, -0.452743), (19, 0.36668200000000006), (20, 0.886161), (21, 0.75048), (22, 0.654791), (23, -3.001915), (24, 0.240651), (25, 0.547257), (26, 1.927036), (27, -1.796374), (28, -0.416351), (29, 1.226682), (30, 0.67815)]

        graph = Graph(xlabel='X', ylabel='Y', x_ticks_minor=1, x_ticks_major=1, y_ticks_major=1,
                      y_grid_label=True, x_grid_label=True, padding=5,
                      x_grid=True, y_grid=True, xmin=-0, xmax=30, ymin=-3, ymax=3)

        graph.background_color = 0, 0, 0, 1    # black color
        plot = SmoothLinePlot(color=[1, 0, 0, 1])

        plot.points = samplePoints
        graph.add_plot(plot)

        self.root.ids.plotChartLayoutID.add_widget(graph)


    def build(self):
        return Builder.load_string(KV)

if __name__=="__main__":
    TestNavigationDrawer().run()