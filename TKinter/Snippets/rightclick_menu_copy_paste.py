from tkinter import *
import pyperclip

class Menu_Entry(Entry):
    def __init__(self,perant,*args,**kwargs):
        Entry.__init__(self,perant,*args,**kwargs)

        self.popup_menu=Menu(self,tearoff=0)
        self.popup_menu.add_command(label="nnnnnnnnnnnnnnnnnn")
        self.popup_menu.add_command(label="nnnnnnnnnnnnnnnnnn")
        self.popup_menu.add_separator()
        
        self.popup_menu.add_command(label="Copy",command=self.copy_to_clipboard, accelerator='Ctrl+C')

        self.bind('<Button-3>',self.popup)
        self.bind('<Menu>',self.popup)
        self.bind("<Control-a>",self.select_all)
        self.bind("<Control-A>",self.select_all)

        self.bind("<Control-c>",self.copy_to_clipboard)
        self.bind("<Control-C>",self.copy_to_clipboard)


    def popup(self, event):
        if self.select_present():
            self.popup_menu.entryconfig("Copy", state=NORMAL)
        else:
            self.popup_menu.entryconfig("Copy", state=DISABLED)

        self.popup_menu.tk_popup(event.x_root, event.y_root, 0)


    def select_all(self, event=None):
            self.select_range(0, END)
            self.icursor(END)
            return 'break'


    def copy_to_clipboard(self, event=None):
        if self.select_present():
            self.clipboard_clear()
            self.update()

            pyperclip.copy(self.selection_get())
            self.update()

            print('string: ', self.selection_get())


root = Tk()
root.title('test')
root.geometry('400x400')

root.ent_user = Menu_Entry(root)
root.ent_user.insert(-1, 'Select me ')
root.ent_user.pack()

root.mainloop()
