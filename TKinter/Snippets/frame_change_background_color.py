from tkinter import *
import random

class ColoredFrame(Frame):
    def __init__(self, master=None, **kwargs):
        Frame.__init__(self, master)
        self.master = master
        self.master.configure(**kwargs)

def change_background_color():
    """Test-function to switch background color of ColoredFrame object"""
    colors = ["black", "blue", "red", "yellow", "orange", "gray", "green"]
    color_frame.master.configure(background=random.choice(colors))

# create root object, set window size based on screen size
root=Tk()
root.geometry(f"{root.winfo_screenwidth()}x{root.winfo_screenheight()}")

# create child-frame with background color
color_frame = ColoredFrame(master=root, background="green")
color_frame.pack()

# create test-label
test_label = Label(color_frame, text="Hello", bg="gray", fg="yellow").pack()
test_button = Button(color_frame, text="Click me", bg="blue", fg="red", command=change_background_color).pack()

root.mainloop()