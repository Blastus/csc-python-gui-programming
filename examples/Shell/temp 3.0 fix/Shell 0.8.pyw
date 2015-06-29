# XXX Exiting routines are currently broken.

import os
import sys
import tkinter.filedialog as tkFileDialog
import tkinter.simpledialog as tkSimpleDialog
import tkinter.messagebox as tkMessageBox
import tkinter.colorchooser as tkColorChooser
import tkinter as Tkinter
from tkinter import *
from winreg import *

file = open

################################################################################

class Shortcut(tkSimpleDialog.Dialog):

    'Allow use to assign shortcut to icon.'

    def __init__(self, parent, widget):
        self.widget = widget
        tkSimpleDialog.Dialog.__init__(self, parent, 'Edit Shortcut')

    def body(self, master):
        self.filename = LabelFrame(master, text='Filename')
        self.entry = Entry(self.filename)
        if hasattr(self.widget, 'shortcut'):
            self.entry.insert(0, self.widget.shortcut)
        self.entry.grid(row=0, column=0, padx=5, pady=5)
        self.button = Button(self.filename, text='Browse...', command=self.command)
        self.button.grid(row=0, column=1, padx=5, pady=5)
        self.filename.pack()
        return self.entry

    def command(self):
        filename = tkFileDialog.Open().show()
        if filename:
            filename = filename.replace('/', '\\')
            self.widget.shortcut = filename
            self.entry.delete(0, END)
            self.entry.insert(0, filename)

    def apply(self):
        self.widget.shortcut = self.entry.get()

    def validate(self):
        if os.path.exists(self.entry.get()):
            return True
        else:
            tkMessageBox.showerror('Error', 'File does not exist.')
            return False

################################################################################

class Create_PhotoImage(tkSimpleDialog.Dialog):

    'Help with creation of new shortcut.'

    def __init__(self, parent, reference, event):
        self.reference = reference
        self.event = event
        tkSimpleDialog.Dialog.__init__(self, parent, 'New Shortcut')

    def body(self, master):
        self.filename = LabelFrame(master, text='Filename')
        self.entry = Entry(self.filename)
        self.entry.grid(row=0, column=0, padx=5, pady=5)
        self.button = Button(self.filename, text='Browse...', command=self.command)
        self.button.grid(row=0, column=1, padx=5, pady=5)
        self.filename.pack()
        return self.entry

    def command(self):
        filename = tkFileDialog.askopenfilename(filetypes=[('GIF files', '*.gif')])
        if filename.lower().endswith('.gif'):
            self.entry.delete(0, END)
            self.entry.insert(0, filename.replace('/', '\\'))

    def validate(self):
        if os.path.exists(self.entry.get()) and self.entry.get().lower().endswith('.gif'):
            return True
        else:
            tkMessageBox.showerror('Error', 'File cannot be used..')
            return False

    def apply(self):
        global w, h
        filename = self.entry.get()
        put(PhotoImage(file=filename), float(self.event.x) / w, float(self.event.y) / h)

################################################################################

def PhotoImage(name=None, cnf={}, master=None, **kw):
    'Return a modified PhotoImage instance.'
    image = Tkinter.PhotoImage(name, cnf, master, **kw)
    image.file = kw['file']
    return image

################################################################################

# PROGRAM START AND EXIT

def main():
    'Setup and execute the program.'
    global root, w, h, reference, media, shortcut_menu
    sys.stderr = file('stderr.log', 'w')
    root = Tk()
    root.protocol('WM_DELETE_WINDOW', do_exit)
    w, h = root.winfo_screenwidth(), root.winfo_screenheight()
    root.overrideredirect(True)
    root.geometry("%dx%d+0+0" % (w, h))
    root.focus_set()
    reference = dict()
    os.chdir(os.path.dirname(sys.argv[0]))
    shortcut_menu = Menu(root, tearoff=0)
    shortcut_menu.add_command(label='New', command=new_PhotoImage)
    shortcut_menu.add_command(label='Edit', command=edit_PhotoImage)
    shortcut_menu.add_command(label='Delete', command=delete_PhotoImage)
    media = Canvas(root, width=w, height=h, highlightthickness=0)
    media.bind('<Button-1>', select)
    media.bind('<B1-Motion>', move)
    media.bind('<Double-Button-1>', activate)
    media.bind('<Button-3>', properties)
    media.pack()
    try:
        load_settings()
    except:
        media.config(background='#00007f')
        for x in range(2):
            for y in range(2):
                put(PhotoImage(file='.\\images\\default.gif'), x, y)
    root.mainloop()

def load_settings():
    'Load configuration settings from the registry.'
    settings = Key(HKEY.CURRENT_USER, 'Software\\Atlantis Zero\\Demo Shell\\settings')
    media.config(background=settings.values['background'].value)
    for key in settings.keys:
        attrs = settings.keys[key]
        image = PhotoImage(file=attrs.values['file'].value)
        reference[media.create_image(float(attrs.values['x'].value), float(attrs.values['y'].value), image=image)] = image
        if 'shortcut' in attrs.values:
            image.shortcut = attrs.values['shortcut'].value

def do_exit():
    'Save settings when program exits.'
    settings = get_key(HKEY.CURRENT_USER, 'Software\\Atlantis Zero\\Demo Shell\\settings', KEY.ALL_ACCESS)
    del settings.keys
    settings.values['background'] = REG_SZ(media['background'])
    for index, item in enumerate(media.find_all()):
        image = get_key(settings, 'IMAGE_%s' % (index + 1), KEY.ALL_ACCESS)
        image.values['file'] = REG_SZ(reference[item].file)
        image.values['x'] = REG_SZ(str(media.coords(item)[0]))
        image.values['y'] = REG_SZ(str(media.coords(item)[1]))
        if hasattr(reference[item], 'shortcut'):
            image.values['shortcut'] = REG_SZ(reference[item].shortcut)
    root.quit()

################################################################################

# ALLOW INTERACTION WITH SHORTCUTS

def select(event):
    'Select a shortcut if possible.'
    global selected, curx, cury
    selected = event.widget.find_withtag(CURRENT)
    if not selected:
        selected = None
    else:
        selected = selected[0]
        curx, cury = event.x, event.y
        event.widget.tag_raise(selected)

def move(event):
    'Move the selected shortcut.'
    global curx, cury
    sel = media.find_withtag(CURRENT)
    if sel:
        sel = sel[0]
    if sel and sel == selected:
        x = media.canvasx(event.x)
        y = media.canvasx(event.y)
        media.move(selected, event.x - curx, event.y - cury)
        curx = event.x
        cury = event.y

def activate(event):
    'Launch shortcut\'s target.'
    global selected
    canvas = event.widget
    sel = canvas.find_withtag(CURRENT)
    if sel:
        sel = sel[0]
    if sel and sel == selected:
        selected = None
        widget = reference[sel]
        if hasattr(widget, 'shortcut') and os.path.exists(widget.shortcut):
            os.chdir(os.path.dirname(widget.shortcut))
            os.startfile(widget.shortcut)
        else:
            filename = tkFileDialog.Open().show()
            if filename:
                widget.shortcut = filename.replace('/', '\\')

################################################################################

# HANDLE RIGHT-CLICKS ON CANVAS

def properties(event):
    global selected_PhotoImage, selected, the_event
    sel = media.find_withtag(CURRENT)
    if sel:
        selected_PhotoImage = reference[sel[0]]
        selected = sel[0]
        the_event = event
        shortcut_menu.post(event.x_root, event.y_root)
    else:
        color = tkColorChooser.askcolor(media['background'])
        if color[1]:
            media.config(background=color[1])

def new_PhotoImage():
    'Create a new shortcut.'
    Create_PhotoImage(root, reference, the_event)

def edit_PhotoImage():
    'Change target of shortcut.'
    Shortcut(root, selected_PhotoImage)

def delete_PhotoImage():
    'Try to delete a shortcut.'
    global selected
    if len(reference) == 1:
        tkMessageBox.showerror('Error', 'Cannot delete last shortcut.')
    else:
        media.delete(selected)
        del reference[selected]

################################################################################

# UTILITY FUNCTIONS

def get_key(key, subkey, mode=None):
    'Get a key, creating it if needed.'
    key = Key(key)
    for subkey in subkey.split('\\'):
        if subkey not in key.keys:
            key.keys = subkey
        key = key.keys[subkey]
    return Key(key, mode=mode)

def put(image, x, y):
    'Put image on the canvas and store reference.'
    a_w, a_h = image.width() / 2, image.height() / 2
    z_w, z_h = int(media['width']) - a_w, int(media['height']) - a_h
    position = (z_w - a_w) * x + a_w, (z_h - a_h) * y + a_h
    reference[media.create_image(position, image=image)] = image

################################################################################

if __name__ == '__main__':
    main()
