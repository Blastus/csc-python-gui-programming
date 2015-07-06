#! /usr/bin/env python3
import sys, _tkinter, os
if sys.platform == 'win32':
    from tkinter import _fix
tk = _tkinter.create()
path = os.path.join(os.path.dirname(sys.executable),
                    'tcl\\tix8.4.3\\demos\\widget')
tk.evalfile(path)
tk.mainloop()
