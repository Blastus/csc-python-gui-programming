#! /usr/bin/env python3

"""Module providing GUI capability to prune any directory.

The code presented in this module is for the purposes of: (1) ascertaining
the space taken up by a directory, its files, its sub-directories, and its
sub-files; (2) allowing for the removal of the sub-files, sub-directories,
files, and directory found in the first purpose; (3) giving the user a GUI
to accomplish said purposes in a convenient way that is easily accessible."""

################################################################################

__author__ = 'Stephen "Zero" Chappell <Noctis.Skytower@gmail.com>'
__date__ = '21 February 2011'
__version__ = '$Revision: 418 $'

################################################################################

import base64
import os
import time
import tkinter
import zlib
from . import view
from . import widgets

################################################################################

ICON = b'eJxjYGAEQgEBBiApwZDBzMAgxsDAoAHEQCEGBQaIOAwkQDE2UOSkiUM\
Gp/rlyd740Ugzf8/uXROxAaA4VvVAqcfYAFCcoHqge4hR/+btWwgCqoez8aj//fs\
XWiAARfCrhyCg+XA2HvV/YACoHs4mRj0ywKWe1PD//p+B4QMOmqGeMAYAAY/2nw=='

################################################################################

def main():
    "Create an application containing a single TrimDir widget."
    tkinter.NoDefaultRoot()
    root = create_application_root()
    attach_window_icon(root, ICON)
    view = setup_class_instance(root)
    main_loop(root)

def create_application_root():
    "Create and configure the main application window."
    root = widgets.Tk()
    root.minsize(430, 215)
    root.title('Directory Pruner')
    root.option_add('*tearOff', tkinter.FALSE)
    return root

def attach_window_icon(root, icon):
    "Generate and use the icon in the window's corner."
    with open('tree.ico', 'wb') as file:
        file.write(zlib.decompress(base64.b64decode(ICON)))
    root.iconbitmap('tree.ico')
    os.remove('tree.ico')

def setup_class_instance(root):
    "Build TrimDir instance that expects resizing."
    instance = view.TrimDir(root)
    instance.grid(row=0, column=0, sticky=tkinter.NSEW)
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)
    return instance

def main_loop(root):
    "Process all GUI events according to tkinter's settings."
    target = time.clock()
    while True:
        try:
            root.update()
        except tkinter.TclError:
            break
        target += tkinter._tkinter.getbusywaitinterval() / 1000
        time.sleep(max(target - time.clock(), 0))
