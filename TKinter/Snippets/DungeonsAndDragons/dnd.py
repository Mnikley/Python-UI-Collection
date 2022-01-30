from tkinter import Tk, Frame, Label, Button, Canvas, font
from tkinter import ttk
from PIL import Image, ImageTk

root = Tk()

""" ############################### Configuration parameters ############################ """
image_file_path = "Island_AngelaMaps-1024x768.jpg"
resize_img = False  # set to True if you want to resize the image and therefore change the window size
resize_to = (600, 600)  # resolution to rescale image to


""" ############################### Drag and drop functionality ############################ """


def make_draggable(widget):
    widget.bind("<Button-1>", on_drag_start)
    widget.bind("<B1-Motion>", on_drag_motion)


def on_drag_start(event):
    event.widget._drag_start_x = event.x
    event.widget._drag_start_y = event.y


def on_drag_motion(event):
    x = event.widget.winfo_x() - event.widget._drag_start_x + event.x
    y = event.widget.winfo_y() - event.widget._drag_start_y + event.y
    event.widget.place(x=x, y=y)


""" ############################### Layout ############################ """

# picture frame with picture as background
picture_frame = Frame(root)
picture_frame.pack(side="left", anchor="w", fill="both", expand=True)

# load the image
if resize_img == False:
    img = ImageTk.PhotoImage(Image.open(image_file_path).resize(resize_to, Image.ANTIALIAS))
if resize_img == True:
    img = ImageTk.PhotoImage(Image.open(image_file_path))

# create canvas, set canvas background to the image
canvas = Canvas(picture_frame, width=img.width(), height=img.height())
canvas.pack(side="left")
canvas.background = img  # Keep a reference in case this code is put in a function.
bg = canvas.create_image(0, 0, anchor="nw", image=img)

# subframe inside picture frame for controls
ctrl_subframe = Frame(picture_frame)
ctrl_subframe.pack(side="right", anchor="n")

# separator between picture and controls, inside picture frame
ttk.Separator(picture_frame, orient="vertical").pack(side="right", fill="y")

# header 'Controls' in subframe
ctrl_header = Label(ctrl_subframe, text="Controls", font=("Arial", 10, "bold"))
f = font.Font(ctrl_header, ctrl_header.cget("font"))
f.configure(underline=True)
ctrl_header.configure(font=f)
ctrl_header.pack(side="top", pady=2)

# update window to get proper sizes from widgets
root.update()

# a draggable button, placed below ctrl_header (based on X of ctrl_subframe and height of ctrl_header, plus padding)
drag_button = Button(picture_frame, text="Drag me", bg="green", width=6, height=2)
drag_button.place(x=ctrl_subframe.winfo_x()+2, y=ctrl_header.winfo_height()+10)
make_draggable(drag_button)


""" ############################### Mainloop ############################ """

root.mainloop()
