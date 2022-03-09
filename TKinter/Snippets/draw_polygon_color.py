import tkinter as tk
from functools import partial


class Point():

    def __init__(self, canvas, x, y):
        self.x = x
        self.y = y
        canvas.create_oval(x - 2, y - 2, x + 2, y + 2, fill='white')


class Poly():

    def __init__(self, canvas, board, p_list=[]):
        self.p_list = p_list
        self.canvas = canvas
        self.board = board

    def draw_poly(self):
        points = []
        for p in self.p_list:
            points.extend([p.x, p.y])
        points.extend(points[:2])
        self.canvas.create_polygon(points, fill=self.board.current_color, outline=self.board.current_color)

    def add_point(self, p):
        self.p_list.append(p)
        if len(self.p_list) > 1:
            p1 = self.p_list[-1]
            p2 = self.p_list[-2]
            self.canvas.create_line(p1.x, p1.y, p2.x, p2.y, fill="white", width=2)


class Palette():

    def __init__(self, frame, board, colors):
        self.colors = colors
        self.board = board
        self.allColors = []
        for idx, color in enumerate(self.colors):
            f = tk.Frame(frame, bg='lightgrey', bd=3)
            f.pack(expand=1, fill='both', side='left')
            if self.board.current_color == color: f.config(bg='red')
            self.allColors.append(f)
            l = tk.Label(f, bg=color)
            l.pack(expand=1, fill='both', padx=2, pady=2)
            l.bind("<1>", self.set_color)

            l.bind("<Button-3>", partial(self.do_popup, idx))

    def do_popup(self, idx, event):
        clsheet = tk.colorchooser.askcolor()
        self.current_color = clsheet[1].upper()
        print(f"You chose: {self.current_color}")
        self.board.current_color = self.current_color  # required?
        self.selected_color(event.widget.master)
        for frm_idx, frm in enumerate(self.allColors):
            if frm_idx == idx:
                frm.children["!label"].config(bg=self.current_color)

    def set_color(self, e):
        self.board.current_color = e.widget['bg']
        self.selected_color(e.widget.master)

    def selected_color(self, colorFrame):
        for f in self.allColors: f.config(bg='lightgrey')
        colorFrame.config(bg="red")


class Board():

    def __init__(self, root):
        self.colors = ['#B4FE98', '#77E4D4', '#F4EEA9', '#F0BB62', '#FF5F7E', "#9A0680"]
        self.root = root
        self.current_color = self.colors[0]
        self.f1 = tk.Frame(self.root)
        self.f1.pack(expand=1, fill='both', padx=5)
        self.f2 = tk.Frame(self.root)
        self.f2.pack(expand=1, fill='both')
        self.canvas = tk.Canvas(self.f2, bg="#000D6B", height=550)
        self.canvas.pack(expand=1, fill='both', padx=5, pady=5)
        self.pallette = Palette(self.f1, self, self.colors)
        self.canvas.bind("<1>", self.draw_point)
        self.canvas.bind("<Double-Button-1>", self.draw_poly)

        self.poly = None

    def draw_point(self, evnt):
        if self.poly:
            self.poly.add_point(Point(self.canvas, evnt.x, evnt.y))
        else:
            self.poly = Poly(self.canvas, self, [Point(self.canvas, evnt.x, evnt.y)])

    def draw_poly(self, evnt):
        if self.poly and len(self.poly.p_list) > 2:
            self.poly.add_point(Point(self.canvas, evnt.x, evnt.y))
            self.poly.draw_poly()
            self.poly = None
        else:
            self.draw_point(evnt)


# main program
root = tk.Tk()
root.title('my program')
root.geometry("600x700")
root.resizable(0, 0)
Board(root)
tk.mainloop()