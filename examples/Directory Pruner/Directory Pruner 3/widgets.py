#! /usr/bin/env python3

"""Module for thread-safe GUI widget library.

The _ThreadSafe base class is provides a foundation for the other widgets.
Support for more widgets can be easily added by adding more definitions."""

################################################################################

__author__ = 'Stephen "Zero" Chappell <Noctis.Skytower@gmail.com>'
__date__ = '21 February 2011'
__version__ = '$Revision: 1 $'

################################################################################

import operator
import tkinter.filedialog
import tkinter.messagebox
import tkinter.ttk
from . import scheduler

################################################################################

class _ThreadSafe:

    "Create a thread-safe GUI class for safe cross-threaded calls."

    ROOT = tkinter.Tk

    def __init__(self, master=None, *args, **keywords):
        "Initialize a thread-safe wrapper around a GUI base class."
        if master is None:
            if self.BASE is not self.ROOT:
                raise ValueError('Widget must have a master!')
            # Use Affinity() if it does not break.
            self.__job = scheduler.AffinityLoop()
            self.__schedule(self.__initialize, *args, **keywords)
        else:
            self.master = master
            self.__job = master.__job
            self.__schedule(self.__initialize, master, *args, **keywords)

    def __initialize(self, *args, **keywords):
        "Delegate instance creation to later time if necessary."
        self.__obj = self.BASE(*args, **keywords)

    ########################################################################

    # Provide a framework for delaying method execution when needed.

    def __schedule(self, *args, **keywords):
        "Schedule execution of a method till later if necessary."
        return self.__job.run(self.__run, *args, **keywords)

    @classmethod
    def __run(cls, func, *args, **keywords):
        "Execute the function after converting the arguments."
        args = tuple(cls.unwrap(i) for i in args)
        keywords = dict((k, cls.unwrap(v)) for k, v in keywords.items())
        return func(*args, **keywords)

    @staticmethod
    def unwrap(obj):
        "Unpack inner objects wrapped by _ThreadSafe instances."
        return obj.__obj if isinstance(obj, _ThreadSafe) else obj

    ########################################################################

    # Allow access to and manipulation of wrapped instance's settings.

    def __getitem__(self, key):
        "Get a configuration option from the underlying object."
        return self.__schedule(operator.getitem, self, key)

    def __setitem__(self, key, value):
        "Set a configuration option on the underlying object."
        return self.__schedule(operator.setitem, self, key, value)

    ########################################################################

    # Create attribute proxies for methods and allow their execution.
    
    def __getattr__(self, name):
        "Create a requested attribute and return cached result."
        attr = self.__Attr(self.__callback, (name,))
        setattr(self, name, attr)
        return attr

    def __callback(self, path, *args, **keywords):
        "Schedule execution of named method from attribute proxy."
        return self.__schedule(self.__method, path, *args, **keywords)

    def __method(self, path, *args, **keywords):
        "Extract a method and run it with the provided arguments."
        method = self.__obj
        for name in path:
            method = getattr(method, name)
        return method(*args, **keywords)

    ########################################################################

    class __Attr:

        "Save an attribute's name and wait for execution."

        __slots__ = '__callback', '__path'

        def __init__(self, callback, path):
            "Initialize proxy with callback and method path."
            self.__callback = callback
            self.__path = path

        def __call__(self, *args, **keywords):
            "Run a known method with the given arguments."
            return self.__callback(self.__path, *args, **keywords)

        def __getattr__(self, name):
            "Generate a proxy object for a sub-attribute."
            if name in {'__func__', '__name__'}:
                # Hack for the "tkinter.__init__.Misc._register" method.
                raise AttributeError('This is not a real method!')
            return type(self)(self.__callback, self.__path + (name,))

################################################################################

# Provide thread-safe classes to be used from tkinter.

class Tk(_ThreadSafe): BASE = tkinter.Tk
class Frame(_ThreadSafe): BASE = tkinter.ttk.Frame
class Button(_ThreadSafe): BASE = tkinter.ttk.Button
class Entry(_ThreadSafe): BASE = tkinter.ttk.Entry
class Progressbar(_ThreadSafe): BASE = tkinter.ttk.Progressbar
class Treeview(_ThreadSafe): BASE = tkinter.ttk.Treeview
class Scrollbar(_ThreadSafe): BASE = tkinter.ttk.Scrollbar
class Sizegrip(_ThreadSafe): BASE = tkinter.ttk.Sizegrip
class Menu(_ThreadSafe): BASE = tkinter.Menu
class Directory(_ThreadSafe): BASE = tkinter.filedialog.Directory
class Message(_ThreadSafe): BASE = tkinter.messagebox.Message
