import os
import sys
import random
import pickle as cPickle
import tkinter.filedialog as tkFileDialog
import tkinter.simpledialog as tkSimpleDialog
import tkinter.messagebox as tkMessageBox
import tkinter.colorchooser as tkColorChooser
import tkinter as Tkinter
from tkinter import *

class PhotoImage(Tkinter.PhotoImage):

    def __init__(self, name=None, cnf={}, master=None, **kw):
        Tkinter.PhotoImage.__init__(self, name, cnf, master, **kw)
        self.file = kw['file']

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

def do_exit(event):
    all = media.find_all()
    options = [media.config()['background'][-1]]
    for item in all:
        options.append([reference[item].file, media.coords(item)])
        if hasattr(reference[item], 'shortcut'):
            options[-1].append(reference[item].shortcut)
    cPickle.dump(options, open('shell.ini', 'wb'), -1)
    event.widget.quit()

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

def files():
    return [os.path.join(os.getcwd(), 'images', name) for name in os.listdir(os.path.join(os.getcwd(), 'images'))]

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
    Shortcut(root, selected_PhotoImage, 'Shortcut')

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

def do_config():
    options = cPickle.load(file('shell.ini', 'rb'))
    media.config(background=options[0])
    for item in options[1:]:
        name = item[0]
        coords = item[1]
        image = PhotoImage(file=name)
        reference[media.create_image(coords, image=image)] = image
        if len(item) == 3:
            image.shortcut = item[2]

def do_setup():
    if len(sys.argv) > 1 and sys.argv[1] == 'random':
        do_random = True
    else:
        do_random = False
    if do_random:
        media.config(background='#ffffff')
    else:
        media.config(background='#00007f')
    names = files()
    random.shuffle(names)
    for name in names:
        if name.lower().endswith('default.gif'):
            calibrate = name
        elif name.lower().endswith('.gif') and do_random:
            image = PhotoImage(file=name)
            put(media, image, random.random(), random.random())
    for x in range(2):
        for y in range(2):
            media.tag_lower(put(media, PhotoImage(file=calibrate), x, y))
            
if os.path.exists('shell.ini'):
    try:
        do_config()
    except:
        do_setup()
else:
    do_setup()

root.mainloop()
