#! /usr/bin/env python3
# $Id$
# a simple darkroom clone

##
# <b>Vroom!</b> is an feature-minimal text editor, similar to Write
# Room and Dark Room.
##

from tkinter import *

import os, sys

TITLE = "Vroom!"

##
# A simple room-style editor, inspired by Dark Room by Jeffrey Fuller.

class RoomEditor(Text):

    def __init__(self, master, **options):
        Text.__init__(self, master, **options)

        self.config(
            borderwidth=0,
            font="{Lucida Sans Typewriter} 14",
            foreground="green",
            background="black",
            insertbackground="white", # cursor
            selectforeground="green", # selection
            selectbackground="#008000",
            wrap=WORD, # use word wrapping (default is character)
            undo=True,
            width=64,
            )

        self.filename = None
        self.encoding = None

    # filename property

    def _getfilename(self):
        return self._filename

    def _setfilename(self, filename):
        self._filename = filename
        title = os.path.basename(filename or "(new document)") + " - " + TITLE
        self.winfo_toplevel().title(title)

    ##
    # Filename for the current document.  Changing this modifies the
    # title bar.  To load a document from a file, use the
    # {@link RoomEditor.load} method.

    filename = property(_getfilename, _setfilename)

    ##
    # Modification flag.  If true, the document has been modified since
    # loaded, or since the flag was last reset.  To reset the flag, assign
    # <b>False</b> to it.

    modified = property(Text.edit_modified, Text.edit_modified)

    ##
    # Clears the document.

    def clear(self):
        self.delete(1.0, END)
        self.modified = False
        self.filename = None
        self.encoding = None

    ##
    # Loads a document from file.
    #
    # @param filename The filename to load.  This is assigned to the
    #    {@link RoomEditor.filename} attribute if the document is
    #    successfully loaded.
    # @ion IOError If the file is not found, or cannot be read.

    def load(self, filename):
        text = open(filename, 'rb').read()
        try:
            encoding = "utf-8"
            text = text.decode(encoding)
        except UnicodeError:
            encoding = "iso-8859-1" # pass-thru
            text = text.decode(encoding)
        self.delete(1.0, END)
        self.insert(END, text)
        self.mark_set(INSERT, 1.0)
        self.modified = False
        self.filename = filename
        self.encoding = encoding

    ##
    # Saves the document to file.
    #
    # @param filename The filename to use for the new file.  If omitted,
    #    the current value of {@link RoomEditor.filename} is used.  Updates
    #    the {@link RoomEditor.filename} attribute if the document is
    #    successfully loaded.
    # @exception IOError If the given file cannot be written.

    def save(self, filename=None):
        if filename is None:
            filename = self.filename
        f = open(filename, "wb")
        s = self.get(1.0, END)
        try:
            # normalize trailing whitespace
            f.write(s.rstrip().encode(self.encoding or "utf-8"))
            f.write(b"\n")
        finally:
            f.close()
        self.modified = False
        self.filename = filename

#
# user interface helpers.  note that most of the functions below rely
# on a global 'editor' variable, which contains the current RoomEditor
# instance.

from tkinter.messagebox import showwarning

FILETYPES = [
    ("Text files", "*.txt"), ("All files", "*")
    ]

##
# Exception used by user interface helpers such as {@link askyesnocancel},
# {@link open_as}, etc., to indicate that an operation has been cancelled.

class Cancel(Exception):
    pass

##
# Displays a yes/no/cancel message box.
#
# @keyparam title Title bar.
# @keyparam message Message text.
# @return A true value for yes, a false value for no.
# @exception Cancel If the message box was cancelled.

def askyesnocancel(title=None, message=None, **options):
    # display a yes/no/cancel message box
    import tkinter.messagebox as tkMessageBox
    s = tkMessageBox.Message(
        title=title, message=message,
        icon=tkMessageBox.QUESTION,
        type=tkMessageBox.YESNOCANCEL,
        **options).show()
    # depending on version, Tk may return either booleans or literal
    # strings.  handle all cases here.
    if isinstance(s, bool):
        return s
    if s == "cancel":
        raise Cancel()
    return s == "yes"

##
# Asks the user for a filename, and loads it into the editor.
#
# @exception Cancel If the operation was cancelled.

def open_as():
    from tkinter.filedialog import askopenfilename
    f = askopenfilename(parent=root, filetypes=FILETYPES)
    if not f:
        raise Cancel()
    try:
        editor.load(f)
    except IOError:
        showwarning("Open", "Cannot open the file.")
        raise Cancel()

##
# Asks the user for a file name, and saves the current editor contents
# to that file.
#
# @exception Cancel If the operation was cancelled.

def save_as():
    from tkinter.filedialog import asksaveasfilename
    f = asksaveasfilename(parent=root, defaultextension=".txt")
    if not f:
        raise Cancel()
    try:
        editor.save(f)
    except IOError:
        showwarning("Save As", "Cannot save the file.")
        raise Cancel()

##
# Saves the current editor contents to the current filename.  If the name
# is not set, falls back on {@link save_as}.
#
# @exception Cancel If the operation was cancelled.

def save():
    if editor.filename:
        try:
            editor.save(editor.filename)
        except IOError:
            showwarning("Save", "Cannot save the file.")
            raise Cancel()
    else:
        save_as()

##
# Offers to save the current editor contents to file, if it has been
# modified.
#
# @exception Cancel If the operation was cancelled.

def save_if_modified():
    if not editor.modified:
        return
    if askyesnocancel(TITLE, "Document modified. Save changes?"):
        save()

#
# bindings

def file_new(event=None):
    try:
        save_if_modified()
        editor.clear()
    except Cancel:
        pass
    return "break" # don't propagate events

def file_open(event=None):
    try:
        save_if_modified()
        open_as()
    except Cancel:
        pass
    return "break"

def file_save(event=None):
    try:
        save()
    except Cancel:
        pass
    return "break"

def file_save_as(event=None):
    try:
        save_as()
    except Cancel:
        pass
    return "break"

def file_quit(event=None):
    try:
        save_if_modified()
    except Cancel:
        return
    root.quit()

# set things up

def main():
    root = Tk()
    root.config(background="black")

    editor = RoomEditor(root) # editor is a global variable
    editor.pack(fill=Y, expand=1, pady=10)

    editor.focus_set()

    # preload given filename, if any
    try:
        editor.load(sys.argv[1])
    except (IndexError, IOError):
        pass

    # maximize
    try:
        root.wm_state("zoomed")
    except TclError:
        pass

    editor.bind("<Control-n>", file_new)
    editor.bind("<Control-o>", file_open)
    editor.bind("<Control-s>", file_save)
    editor.bind("<Control-Shift-S>", file_save_as)
    editor.bind("<Control-q>", file_quit)
    editor.bind("<Control-Shift-Q>", file_quit)

    root.protocol("WM_DELETE_WINDOW", file_quit) # window close button

    globals().update(locals())
    mainloop()

if __name__ == "__main__":
    main()
