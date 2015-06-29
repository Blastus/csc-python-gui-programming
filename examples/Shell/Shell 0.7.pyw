import os
import sys
import tkFileDialog
import tkSimpleDialog
import tkMessageBox
import tkColorChooser
import Tkinter

from Tkinter import *
from winreg_legacy_1 import *

def PhotoImage(name=None, cnf={}, master=None, **kw):
    image = Tkinter.PhotoImage(name, cnf, master, **kw)
    image.file = kw['file']
    return image

# Define some helper classes.

class Shortcut(tkSimpleDialog.Dialog):

    def __init__(self, parent, widget, title=None):
        self.widget = widget
        tkSimpleDialog.Dialog.__init__(self, parent, title)

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

class Create_PhotoImage(tkSimpleDialog.Dialog):

    def __init__(self, parent, reference, event, title):
        self.reference = reference
        self.event = event
        tkSimpleDialog.Dialog.__init__(self, parent, title)

    def body(self, master):
        self.filename = LabelFrame(master, text='Filename')
        self.entry = Entry(self.filename)
        self.entry.grid(row=0, column=0, padx=5, pady=5)
        self.button = Button(self.filename, text='Browse...', command=self.commander)
        self.button.grid(row=0, column=1, padx=5, pady=5)
        self.filename.pack()
        return self.entry

    def commander(self):
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
        canvas = self.event.widget
        put(canvas, PhotoImage(file=filename), float(self.event.x) / w, float(self.event.y) / h)

# Define action on exit.        

def do_exit(event):
    settings = get_key(HKEY.CURRENT_USER, 'Software\\Atlantis Zero\\Demo Shell\\settings', KEY.ALL_ACCESS)
    del settings.keys
    settings.values['background'] = REG_SZ(media.config()['background'][-1])
    for index, item in enumerate(media.find_all()):
        image = get_key(settings, 'IMAGE_%s' % (index + 1), sam=KEY.ALL_ACCESS)
        image.values['file'] = REG_SZ(reference[item].file)
        image.values['x'] = REG_SZ(str(media.coords(item)[0]))
        image.values['y'] = REG_SZ(str(media.coords(item)[1]))
        if hasattr(reference[item], 'shortcut'):
            image.values['shortcut'] = REG_SZ(reference[item].shortcut)
    event.widget.quit()

def get_key(key, sub_key, sam=None):
    key = Key(key=key)
    for sub_key in sub_key.split('\\'):
        if sub_key not in key.keys:
            key.keys = sub_key
        key = key.keys[sub_key]
    return Key(key=key, sam=sam)

# Start setting up the GUI.

root = Tk()
w, h = root.winfo_screenwidth(), root.winfo_screenheight()
root.overrideredirect(True)
root.geometry("%dx%d+0+0" % (w, h))
root.focus_set()
root.bind("<Escape>", do_exit)

reference = dict()
os.chdir(os.path.dirname(sys.argv[0]))

def put(media, image, x, y):
    media_w, media_h = int(media.config()['width'][-1]), int(media.config()['height'][-1])
    start_w, start_h = image.width() / 2, image.height() / 2
    stop_w, stop_h = media_w - start_w, media_h - start_h
    position = (stop_w - start_w) * x + start_w, (stop_h - start_h) * y + start_h
    handle = media.create_image(position, image=image)
    reference[handle] = image
    return handle

curx = cury = selected = None

def select(event):
    global selected, curx, cury
    selected = event.widget.find_withtag(CURRENT)
    if not selected:
        selected = None
    else:
        selected = selected[0]
        curx, cury = event.x, event.y
        event.widget.tag_raise(selected)

def move(event):
    global curx, cury
    canvas = event.widget
    sel = canvas.find_withtag(CURRENT)
    if sel:
        sel = sel[0]
    if sel and sel == selected:
        canvas = event.widget
        x = canvas.canvasx(event.x)
        y = canvas.canvasx(event.y)
        canvas.move(selected, event.x - curx, event.y - cury)
        curx = event.x
        cury = event.y

def activate(event):
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

def new_PhotoImage():
    Create_PhotoImage(root, reference, the_event, 'New Shortcut')

def edit_PhotoImage():
    Shortcut(root, selected_PhotoImage, 'Edit Shortcut')

def delete_PhotoImage():
    global the_canvas, selected
    if len(reference) == 1:
        tkMessageBox.showerror('Error', 'Cannot delete last shortcut.')
    else:
        the_canvas.delete(selected)
        del reference[selected]

shortcut_menu = Menu(root, tearoff=0)
shortcut_menu.add_command(label='New', command=new_PhotoImage)
shortcut_menu.add_command(label='Edit', command=edit_PhotoImage)
shortcut_menu.add_command(label='Delete', command=delete_PhotoImage)

def properties(event):
    global selected_PhotoImage, selected, the_canvas, the_event
    canvas = event.widget
    sel = canvas.find_withtag(CURRENT)
    if sel:
        selected_PhotoImage = reference[sel[0]]
        selected = sel[0]
        the_canvas = canvas
        the_event = event
        shortcut_menu.post(event.x_root, event.y_root)
    else:
        color = tkColorChooser.askcolor(canvas.config()['background'][-1])
        if color[1]:
            canvas.config(background=color[1])

media = Canvas(root, width=w, height=h)
media.bind('<Button-1>', select)
media.bind('<B1-Motion>', move)
media.bind('<Double-Button-1>', activate)
media.bind('<Button-3>', properties)
media.pack()

# CONFIGURATION

def load_settings():
    settings = Key(key=HKEY.CURRENT_USER, sub_key='Software\\Atlantis Zero\\Demo Shell\\settings')
    media.config(background=settings.values['background'].value)
    for key in settings.keys:
        attrs = settings.keys[key]
        image = PhotoImage(file=attrs.values['file'].value)
        reference[media.create_image(float(attrs.values['x'].value), float(attrs.values['y'].value), image=image)] = image
        if 'shortcut' in attrs.values:
            image.shortcut = attrs.values['shortcut'].value

try:
    load_settings()
except:
    media.config(background='#00007f')
    for x in range(2):
        for y in range(2):
            media.tag_lower(put(media, PhotoImage(file='.\\images\\default.gif'), x, y))

root.mainloop()
