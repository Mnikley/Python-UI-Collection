import sys
from tkinter import Tk, Button, Frame
from tkinter.scrolledtext import ScrolledText


class PrintLogger(object):  # create file like object

    def __init__(self, textbox):  # pass reference to text widget
        self.textbox = textbox  # keep ref

    def write(self, text):
        self.textbox.configure(state="normal")  # make field editable
        self.textbox.insert("end", text)  # write text to textbox
        self.textbox.see("end")  # scroll to end
        self.textbox.configure(state="disabled")  # make field readonly

    def flush(self):  # needed for file like object
        pass


class MainGUI(Tk):

    def __init__(self):
        Tk.__init__(self)
        self.root = Frame(self)
        self.root.pack()
        self.redirect_button = Button(self.root, text="Redirect console to widget", command=self.redirect_logging)
        self.redirect_button.pack()
        self.redirect_button = Button(self.root, text="Redirect console reset", command=self.reset_logging)
        self.redirect_button.pack()
        self.test_button = Button(self.root, text="Test Print", command=self.test_print)
        self.test_button.pack()
        self.log_widget = ScrolledText(self.root, height=4, width=120, font=("consolas", "8", "normal"))
        self.log_widget.pack()

    def reset_logging(self):
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

    def test_print(self):
        print("Am i working?")

    def redirect_logging(self):
        logger = PrintLogger(self.log_widget)
        sys.stdout = logger
        sys.stderr = logger


if __name__ == "__main__":
    app = MainGUI()
    app.mainloop()
