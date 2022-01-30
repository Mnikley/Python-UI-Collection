import tkinter as tk
from tkinter import filedialog
import os

"""
Load any file with text-data (.csv, .xml, .txt, ..) and display in UI with line numbers
Modified from: https://stackoverflow.com/questions/16369470/tkinter-adding-line-number-to-text-widget
"""

class TextLineNumbers(tk.Canvas):
    def __init__(self, *args, **kwargs):
        tk.Canvas.__init__(self, *args, **kwargs)
        self.textwidget = None

    def attach(self, text_widget):
        self.textwidget = text_widget

    def redraw(self, *args):
        '''redraw line numbers'''
        self.delete("all")

        i = self.textwidget.index("@0,0")
        while True:
            dline = self.textwidget.dlineinfo(i)
            if dline is None:
                break
            y = dline[1]
            linenum = str(i).split(".")[0]
            self.create_text(2, y, anchor="nw", text=linenum)
            i = self.textwidget.index("%s+1line" % i)


class CustomText(tk.Text):
    def __init__(self, *args, **kwargs):
        tk.Text.__init__(self, *args, **kwargs)

        # create a proxy for the underlying widget
        self._orig = self._w + "_orig"
        self.tk.call("rename", self._w, self._orig)
        self.tk.createcommand(self._w, self._proxy)

    def _proxy(self, *args):
        # let the actual widget perform the requested action
        cmd = (self._orig,) + args
        result = self.tk.call(cmd)

        # generate an event if something was added or deleted,
        # or the cursor position changed
        if (args[0] in ("insert", "replace", "delete") or
                args[0:3] == ("mark", "set", "insert") or
                args[0:2] == ("xview", "moveto") or
                args[0:2] == ("xview", "scroll") or
                args[0:2] == ("yview", "moveto") or
                args[0:2] == ("yview", "scroll")):
            self.event_generate("<<Change>>", when="tail")

        # return what the actual widget returned
        return result


class Example(tk.Frame):
    def __init__(self, *args, **kwargs):
        tk.Frame.__init__(self, *args, **kwargs)
        self.text = CustomText(self)
        self.vsb = tk.Scrollbar(self, orient="vertical", command=self.text.yview)
        self.text.configure(yscrollcommand=self.vsb.set)
        self.text.tag_configure("bigfont", font=("Helvetica", "24", "bold"))
        self.linenumbers = TextLineNumbers(self, width=30)
        self.linenumbers.attach(self.text)

        self.vsb.pack(side="right", fill="y")
        self.linenumbers.pack(side="left", fill="y")
        self.text.pack(side="right", fill="both", expand=True)

        # new button to call load_xml and show status
        self.load_button = tk.Button(root, text="Load file", command=self.load_xml)
        self.load_button.pack(side="top")

        self.text.bind("<<Change>>", self._on_change)
        self.text.bind("<Configure>", self._on_change)

        self.text.insert("end", "one\ntwo\nthree\n")
        self.text.insert("end", "four\n", ("bigfont",))
        self.text.insert("end", "five\n")

    def _on_change(self, event):
        self.linenumbers.redraw()

    def load_xml(self):
        """Load any file, delete current text and insert new data"""
        input_file = filedialog.askopenfilename(title="Load a textfile",
                                                filetypes=(("XML", "*.xml"),
                                                           ("Text", "*.txt"),
                                                           ("All files", "*.*")),
                                                initialdir=os.getcwd())

        if input_file:
            self.text.delete("1.0", "end")
            self.load_button.config(text=f"Currently loaded: {input_file.split(os.sep)[-1]}")
            with open(input_file, 'r') as f:
                self.text.insert("end", f.read())


if __name__ == "__main__":
    root = tk.Tk()
    Example(root).pack(side="top", fill="both", expand=True)
    root.mainloop()
