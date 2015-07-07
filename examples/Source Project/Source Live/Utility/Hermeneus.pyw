# <source name="χερμενεύς 1.1.pyw" size="19427" hash="498090e0955c8b5185f449e72604489e4de35a0c909b86471a6c64e63e09230eba2fa3bedc3b8539b96417c9d9a52988462b378c1f3bd5c4c5d17e01d8905074" />
"""Module for running a specialized File Share Messenger program.

The code in this file is designed to provide all of the needed abilities
for running a FSM for those that may need such a workaround. All classes
and functions may be used for whatever purposes deemed useful for them."""

# These are all the GUI libraries.
import tkinter.ttk
import tkinter.messagebox
import tkinter.font
import tkinter.filedialog
# Here are some general libraries.
import datetime
import getpass
import os
import string
import random
import colorsys
import urllib.parse
import webbrowser
import pickle
import traceback
import sys
import contextlib
import io
import hashlib
import threading
import _thread
import queue
import time
import operator
import pydoc
# Module contents can be imported.
from uuid import uuid4
                
################################################################################

# This code provides error logging facilities.

def main():
    "Begins execution of this File Share Messenger program."
    # Figure out where files should be stored.
    hermeneus_storage = AboutHermeneus.WHO_AM_I + ' Storage'
    public_path = os.path.join('Auxiliary', hermeneus_storage, 'Version 1')
    private_path = os.path.join('..', '..', hermeneus_storage, 'Version 1')
    # Execute the main class (static) function of Hermeneus.
    with capture_stderr() as stderr:
        # Create the root GUI object.
        tkinter.NoDefaultRoot()
        root = Tk()
        # Proceed start up the rest of the systems.
        sentinel = Blinx(root, '..')
        sentinel.start()
        Hermeneus.main(root, public_path, private_path)
        sentinel.join()
    # Cleanup stderr and save and errors to file.
    record(stderr, os.path.join(private_path, 'Pickles'), 'errorlog.pickle')

@contextlib.contextmanager
def capture_stderr():
    "Provides a context manager that captures standard error."
    orig_stderr = sys.stderr
    sys.stderr = io.StringIO()
    try:
        yield sys.stderr
    finally:
        sys.stderr = orig_stderr

def record(stream, path, filename):
    "Saves any errors encountered during program execution."
    # Find out if there were any errors during execution.
    errors = stream.getvalue()
    if errors:
        # Save them to a pickled file with a timestamp.
        with open(os.path.join(path, filename), 'ab', 0) as file:
            problem = getpass.getuser(), datetime.datetime.utcnow(), errors
            pickle.dump(problem, file)
        # Print out errors to console if this is a console app.
        if os.path.splitext(sys.argv[0])[1].lower().endswith('.py'):
            sys.stderr.write(errors)

################################################################################

# This area provides a class for schedules jobs to run on a single thread.

class AffinityLoop:

    """AffinityLoop() -> AffinityLoop

    Restricts code execution to thread that instance was created on."""

    __slots__ = '__action', '__thread'

    def __init__(self):
        "Initializes AffinityLoop with job queue and thread identity."
        self.__action = queue.Queue()
        self.__thread = _thread.get_ident()

    def run(self, func, *args, **keywords):
        "Runs function on creating thread and returns result."
        if _thread.get_ident() == self.__thread:
            self.__run_jobs()
            return func(*args, **keywords)
        else:
            job = self.__Job(func, args, keywords)
            self.__action.put_nowait(job)
            return job.result

    def __run_jobs(self):
        "Runs all pending jobs currently in the job queue."
        while not self.__action.empty():
            job = self.__action.get_nowait()
            job.execute()

    ########################################################################

    class __Job:

        """__Job(func, args, keywords) -> __Job

        Stores information to run a job at a later time."""

        __slots__ = ('__func', '__args', '__keywords',
                     '__error', '__mutex', '__value')

        def __init__(self, func, args, keywords):
            "Initializes the job's info and readies for execution."
            self.__func = func
            self.__args = args
            self.__keywords = keywords
            self.__error = False
            self.__mutex = _thread.allocate_lock()
            self.__mutex.acquire()

        def execute(self):
            "Runs the job, storse any error, and returns to sender."
            try:
                self.__value = self.__func(*self.__args, **self.__keywords)
            except Exception as error:
                self.__error = True
                self.__value = error
            self.__mutex.release()

        @property
        def result(self):
            "Returns execution result or raises an error."
            self.__mutex.acquire()
            if self.__error:
                raise self.__value
            return self.__value

################################################################################

# This is the base class for a thread-safe GUI implementation in tkinter.

class _ThreadSafe:

    """_ThreadSafe(master=None, *args, **keywords) -> _ThreadSafe

    Creates a thread-safe GUI class for safe cross-threaded calls."""

    ROOT = tkinter.Tk

    def __init__(self, master=None, *args, **keywords):
        "Initializes a thread-safe wrapper around a GUI base class."
        if master is None:
            if self.BASE is not self.ROOT:
                raise ValueError('Widget must have a master!')
            self.__job = AffinityLoop()
            self.__schedule(self.__initialize, *args, **keywords)
        else:
            self.master = master
            self.__job = master.__job
            # Patch initialization for the PhotoImage class.
            if self.BASE is not tkinter.PhotoImage:
                self.__schedule(self.__initialize, master, *args, **keywords)
            else:
                keywords['master'] = master
                self.__schedule(self.__initialize, *args, **keywords)

    def __initialize(self, *args, **keywords):
        "Delegates instance creation to later time if necessary."
        self.__obj = self.BASE(*args, **keywords)

    ########################################################################

    # Provide a framework for delaying method execution when needed.

    def __schedule(self, *args, **keywords):
        "Schedules execution of a method till later if necessary."
        return self.__job.run(self.__run, *args, **keywords)

    @classmethod
    def __run(cls, func, *args, **keywords):
        "Executes the function after converting the arguments."
        args = tuple(cls.unwrap(i) for i in args)
        keywords = dict((k, cls.unwrap(v)) for k, v in keywords.items())
        return func(*args, **keywords)

    @staticmethod
    def unwrap(obj):
        "Unpacks inner objects wrapped by _ThreadSafe instances."
        return obj.__obj if isinstance(obj, _ThreadSafe) else obj

    ########################################################################

    # Allow access to and manipulation of wrapped instance's settings.

    def __getitem__(self, key):
        "Gets a configuration option from the underlying object."
        return self.__schedule(operator.getitem, self, key)

    def __setitem__(self, key, value):
        "Sets a configuration option on the underlying object."
        return self.__schedule(operator.setitem, self, key, value)

    ########################################################################

    # Create attribute proxies for methods and allow their execution.
    
    def __getattr__(self, name):
        "Creates a requested attribute and returns cached result."
        attr = self.__Attr(self.__callback, (name,))
        setattr(self, name, attr)
        return attr

    def __callback(self, path, *args, **keywords):
        "Schedules execution of named method from attribute proxy."
        return self.__schedule(self.__method, path, *args, **keywords)

    def __method(self, path, *args, **keywords):
        "Extracts a method and runs it with the provided arguments."
        method = self.__obj
        for name in path:
            method = getattr(method, name)
        return method(*args, **keywords)

    ########################################################################

    # Allow for write super().destroy() and widget.mainloop() in code.

    def destroy(self):
        "Schedules for the destruction of this widget."
        return self.__schedule(self.__obj.destroy)

    def mainloop(self):
        "Processes all GUI events according to tkinter's settings."
        target = time.clock()
        while True:
            try:
                self.update()
            except tkinter.TclError:
                break
            target += tkinter._tkinter.getbusywaitinterval() / 1000
            time.sleep(max(target - time.clock(), 0))
    
    ########################################################################

    class __Attr:

        """__Attr(callback, path) -> __Attr

        Saves an attribute's name and wait for execution."""

        __slots__ = '__callback', '__path'

        def __init__(self, callback, path):
            "Initializes proxy with callback and method path."
            self.__callback = callback
            self.__path = path

        def __call__(self, *args, **keywords):
            "Runs a known method with the given arguments."
            return self.__callback(self.__path, *args, **keywords)

        def __getattr__(self, name):
            "Generates a proxy object for a sub-attribute."
            if name in {'__func__', '__name__'}:
                # Hack for the "tkinter.__init__.Misc._register" method.
                raise AttributeError('This is not a real method!')
            return self.__class__(self.__callback, self.__path + (name,))

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
class Text(_ThreadSafe): BASE = tkinter.Text
class Toplevel(_ThreadSafe): BASE = tkinter.Toplevel
class Labelframe(_ThreadSafe): BASE = tkinter.ttk.Labelframe
class Label(_ThreadSafe): BASE = tkinter.ttk.Label
class Scale(_ThreadSafe): BASE = tkinter.ttk.Scale
class Canvas(_ThreadSafe): BASE = tkinter.Canvas
class Font(_ThreadSafe): BASE = tkinter.font.Font
class OldFrame(_ThreadSafe): BASE = tkinter.Frame
class OldButton(_ThreadSafe): BASE = tkinter.Button
class Checkbutton(_ThreadSafe): BASE = tkinter.ttk.Checkbutton
class StringVar(_ThreadSafe): BASE = tkinter.StringVar
class Spinbox(_ThreadSafe): BASE = tkinter.Spinbox
class PhotoImage(_ThreadSafe): BASE = tkinter.PhotoImage

################################################################################

# The Color class provides a helpful interface when working with the spectrum.

class Color:

    "Color(red, green, blue) -> Color"

    HTML = dict(reversed(color.split(' ')) for color in '''\
#F0F8FF AliceBlue
#FAEBD7 AntiqueWhite
#00FFFF Aqua
#7FFFD4 Aquamarine
#F0FFFF Azure
#F5F5DC Beige
#FFE4C4 Bisque
#000000 Black
#FFEBCD BlanchedAlmond
#0000FF Blue
#8A2BE2 BlueViolet
#A52A2A Brown
#DEB887 BurlyWood
#5F9EA0 CadetBlue
#7FFF00 Chartreuse
#D2691E Chocolate
#FF7F50 Coral
#6495ED CornflowerBlue
#FFF8DC Cornsilk
#DC143C Crimson
#00FFFF Cyan
#00008B DarkBlue
#008B8B DarkCyan
#B8860B DarkGoldenRod
#A9A9A9 DarkGray
#A9A9A9 DarkGrey
#006400 DarkGreen
#BDB76B DarkKhaki
#8B008B DarkMagenta
#556B2F DarkOliveGreen
#FF8C00 Darkorange
#9932CC DarkOrchid
#8B0000 DarkRed
#E9967A DarkSalmon
#8FBC8F DarkSeaGreen
#483D8B DarkSlateBlue
#2F4F4F DarkSlateGray
#2F4F4F DarkSlateGrey
#00CED1 DarkTurquoise
#9400D3 DarkViolet
#FF1493 DeepPink
#00BFFF DeepSkyBlue
#696969 DimGray
#696969 DimGrey
#1E90FF DodgerBlue
#B22222 FireBrick
#FFFAF0 FloralWhite
#228B22 ForestGreen
#FF00FF Fuchsia
#DCDCDC Gainsboro
#F8F8FF GhostWhite
#FFD700 Gold
#DAA520 GoldenRod
#808080 Gray
#808080 Grey
#008000 Green
#ADFF2F GreenYellow
#F0FFF0 HoneyDew
#FF69B4 HotPink
#CD5C5C IndianRed
#4B0082 Indigo
#FFFFF0 Ivory
#F0E68C Khaki
#E6E6FA Lavender
#FFF0F5 LavenderBlush
#7CFC00 LawnGreen
#FFFACD LemonChiffon
#ADD8E6 LightBlue
#F08080 LightCoral
#E0FFFF LightCyan
#FAFAD2 LightGoldenRodYellow
#D3D3D3 LightGray
#D3D3D3 LightGrey
#90EE90 LightGreen
#FFB6C1 LightPink
#FFA07A LightSalmon
#20B2AA LightSeaGreen
#87CEFA LightSkyBlue
#778899 LightSlateGray
#778899 LightSlateGrey
#B0C4DE LightSteelBlue
#FFFFE0 LightYellow
#00FF00 Lime
#32CD32 LimeGreen
#FAF0E6 Linen
#FF00FF Magenta
#800000 Maroon
#66CDAA MediumAquaMarine
#0000CD MediumBlue
#BA55D3 MediumOrchid
#9370D8 MediumPurple
#3CB371 MediumSeaGreen
#7B68EE MediumSlateBlue
#00FA9A MediumSpringGreen
#48D1CC MediumTurquoise
#C71585 MediumVioletRed
#191970 MidnightBlue
#F5FFFA MintCream
#FFE4E1 MistyRose
#FFE4B5 Moccasin
#FFDEAD NavajoWhite
#000080 Navy
#FDF5E6 OldLace
#808000 Olive
#6B8E23 OliveDrab
#FFA500 Orange
#FF4500 OrangeRed
#DA70D6 Orchid
#EEE8AA PaleGoldenRod
#98FB98 PaleGreen
#AFEEEE PaleTurquoise
#D87093 PaleVioletRed
#FFEFD5 PapayaWhip
#FFDAB9 PeachPuff
#CD853F Peru
#FFC0CB Pink
#DDA0DD Plum
#B0E0E6 PowderBlue
#800080 Purple
#FF0000 Red
#BC8F8F RosyBrown
#4169E1 RoyalBlue
#8B4513 SaddleBrown
#FA8072 Salmon
#F4A460 SandyBrown
#2E8B57 SeaGreen
#FFF5EE SeaShell
#A0522D Sienna
#C0C0C0 Silver
#87CEEB SkyBlue
#6A5ACD SlateBlue
#708090 SlateGray
#708090 SlateGrey
#FFFAFA Snow
#00FF7F SpringGreen
#4682B4 SteelBlue
#D2B48C Tan
#008080 Teal
#D8BFD8 Thistle
#FF6347 Tomato
#40E0D0 Turquoise
#EE82EE Violet
#F5DEB3 Wheat
#FFFFFF White
#F5F5F5 WhiteSmoke
#FFFF00 Yellow
#9ACD32 YellowGreen'''.split('\n'))

    @property
    def best_name(self):
        "Returns the closest color names for the current color."
        diffs = []
        for name in self.HTML.keys():
            diffs.append((name, self.diff(getattr(self, name))))
        error = min(diffs, key=lambda pair: pair[1])[1]
        return tuple(pair[0] for pair in diffs if pair[1] == error)

    ########################################################################

    @classmethod
    def hsv(cls, hue, saturation, value):
        "Builds a color instance based on hue, saturation, and value."
        assert 0 <= hue <= 1 and 0 <= saturation <= 1 and 0 <= value <= 1
        r, g, b = colorsys.hsv_to_rgb(hue, saturation, value)
        return cls(round(r * 0xFF), round(g * 0xFF), round(b * 0xFF))

    @classmethod
    def parse(cls, string):
        "Returns a color based on a valid color string."
        assert len(string) == 7 and string[0] == '#'
        return cls(int(string[1:3], 16),
                   int(string[3:5], 16),
                   int(string[5:7], 16))

    ########################################################################

    __slots__ = '__rgb'

    def __init__(self, red, green, blue):
        "Initializes a color instance with red, green, and blue."
        self.__rgb = bytes((red, green, blue))

    def __str__(self):
        "Generates a string equivalent to the current color."
        return '#{:02X}{:02X}{:02X}'.format(*self.__rgb)

    def __repr__(self):
        "Returns a representation of the present color."
        return '{}({}, {}, {})'.format(self.__class__.__name__, *self.__rgb)

    def __hash__(self):
        "Generates a hash from the color (for dictionaries)."
        return hash(self.__rgb)

    def __eq__(self, other):
        "Checks if colors are equal (for dictionaries)."
        return self.__rgb == other.__rgb

    ########################################################################

    @property
    def red(self):
        "Returns red component of color."
        return self.__rgb[0]

    @property
    def green(self):
        "Returns green component of color."
        return self.__rgb[1]

    @property
    def blue(self):
        "Returns blue component of color."
        return self.__rgb[2]

    r, g, b = red, green, blue

    def set_red(self, value):
        "Returns a new color with red set accordingly."
        return self.__class__(value, self.g, self.b)

    def set_green(self, value):
        "Returns a new color with green set accordingly."
        return self.__class__(self.r, value, self.b)

    def set_blue(self, value):
        "Returns a new color with blue set accordingly."
        return self.__class__(self.r, self.g, value)

    def add_red(self, value):
        "Creates a color with red rotated by the value."
        return self.__class__(self.r + value & 0xFF, self.g, self.b)

    def add_green(self, value):
        "Creates a color with green rotated by the value."
        return self.__class__(self.r, self.g + value & 0xFF, self.b)

    def add_blue(self, value):
        "Creates a color with blue rotated by the value."
        return self.__class__(self.r, self.g, self.b + value & 0xFF)

    ########################################################################

    @property
    def hue(self):
        "Returns hue component of color."
        return colorsys.rgb_to_hsv(self.__rgb[0] / 0xFF,
                                   self.__rgb[1] / 0xFF,
                                   self.__rgb[2] / 0xFF)[0]

    @property
    def saturation(self):
        "Returns saturation component of color."
        return colorsys.rgb_to_hsv(self.__rgb[0] / 0xFF,
                                   self.__rgb[1] / 0xFF,
                                   self.__rgb[2] / 0xFF)[1]

    @property
    def value(self):
        "Returns value component of color."
        return colorsys.rgb_to_hsv(self.__rgb[0] / 0xFF,
                                   self.__rgb[1] / 0xFF,
                                   self.__rgb[2] / 0xFF)[2]

    h, s, v = hue, saturation, value

    def set_hue(self, value):
        "Returns a new color with hue set accordingly."
        return self.hsv(value, self.s, self.v)

    def set_saturation(self, value):
        "Returns a new color with saturation set accordingly."
        return self.hsv(self.h, value, self.v)

    def set_value(self, value):
        "Returns a new color with value set accordingly."
        return self.hsv(self.h, self.s, value)

    def add_hue(self, value):
        "Creates a color with hue rotated by the value."
        return self.hsv(self.__mod(self.h + value), self.s, self.v)

    def add_saturation(self, value):
        "Creates a color with saturation rotated by the value."
        return self.hsv(self.h, self.__mod(self.s + value), self.v)

    def add_value(self, value):
        "Creates a color with value rotated by the value."
        return self.hsv(self.h, self.s, self.__mod(self.v + value))

    ########################################################################

    def invert(self):
        "Returns the color with the RGB values inverted."
        return self.__class__(0xFF - self.r, 0xFF - self.g, 0xFF - self.b)

    def rotate(self, value):
        "Returns new color with RGB values rotated by value."
        return self.__class__(self.r + value & 0xFF,
                              self.g + value & 0xFF,
                              self.b + value & 0xFF)

    def diff(self, other):
        "Calculates a numerical difference between colors."
        r = (self.r - other.r) ** 2
        g = (self.g - other.g) ** 2
        b = (self.b - other.b) ** 2
        return r + g + b

    def mix(self, bias, other):
        "Mixes two colors together by the given bias."
        assert 0 <= bias <= 1
        alpha = 1 - bias
        return self.__class__(round(self.r * alpha + other.r * bias),
                              round(self.g * alpha + other.g * bias),
                              round(self.b * alpha + other.b * bias))

    @staticmethod
    def get(bias, *colors):
        "Mixes two or more colors together based on the bias."
        assert 0 <= bias <= 1
        ranges = len(colors) - 1
        assert ranges > 0
        length = 1 / ranges
        index = int(bias / length)
        if index == ranges:
            return colors[-1]
        first, second = colors[index:index+2]
        return first.mix(bias % length / length, second)

    ########################################################################

    @staticmethod
    def __mod(value):
        "Provides a proper modulus for floating-point numbers."
        div, mod = divmod(value, 1.0)
        if div > 0.0 and not mod:
            return 1.0
        return mod

# Create named colors on the Color class.
for key, value in Color.HTML.items():
    setattr(Color, key, Color.parse(value))

################################################################################

# This color dialog allows the user many choices using a nice interface.

class ColorOptions(Toplevel):

    "ColorOptions(master, color) -> ColorOptions"

    LABEL = dict(width=9, anchor=tkinter.CENTER)
    SCALE = dict(orient=tkinter.HORIZONTAL, length=256, from_=0.0, to=1.0)
    VALUE = dict(text='0.0', width=5, relief=tkinter.GROOVE)
    BYTE = dict(text='00', width=3, relief=tkinter.GROOVE,
                anchor=tkinter.CENTER)
    PADDING = dict(padx=2, pady=2)

    ########################################################################

    OPEN = False

    @classmethod
    def open_window(cls, root, color):
        "Only opens window if not already open and return selection."
        if not cls.OPEN:
            cls.OPEN = True
            window = cls(root, color)
            window.mainloop()
            return window.color
        return ''

    ########################################################################

    def __init__(self, master, color):
        "Initializes a color picker for RGB and HSV systems."
        super().__init__(master)
        self.transient(master)
        self.geometry('+{}+{}'.format(master.winfo_rootx(),
                                      master.winfo_rooty()))
        # Build all the widgets that will in the window.
        self.create_interface()
        # Populate the widgets with the correct settings.
        self.load_widget_settings(color)
        # Override the closing of this window to keep track of its state.
        self.protocol('WM_DELETE_WINDOW', self.ask_destroy)
        # Prepare the window for general display.
        self.title('Colors')
        self.resizable(False, False)
        # Create a message box to warn about closing.
        options = dict(title='Warning?', icon=tkinter.messagebox.QUESTION,
                       type=tkinter.messagebox.YESNO, message='''\
Are you sure you want to close?
You will loose all your changes.''')
        self.__cancel_warning = Message(self, **options)

    def load_widget_settings(self, color):
        "Sets the colors from the color argument."
        color = Color.parse(color)
        self.update_hsv(color.h, color.s, color.v)
        self.hsv_updated(color)

    @property
    def color(self):
        "Return the color of the canvas."
        return self.__color

    def ask_destroy(self):
        "Only closes if user wants to loose settings."
        if self.__cancel_warning.show() == tkinter.messagebox.YES:
            self.destroy()
        else:
            self.focus_set()

    def destroy(self):
        "Destroys this window and unset the OPEN flag."
        super().destroy()
        self.quit()
        self.__class__.OPEN = False

    def create_interface(self):
        "Generates the widgets and places them on the screen."
        # Create all the widgets.
        self.rgb_scales = self.create_rgb_scales()
        self.hsv_scales = self.create_hsv_scales()
        self.color_area = self.create_color_area()
        self.input_buttons = self.create_buttons()
        # Place them on the grid.
        self.rgb_scales.grid(row=0, column=0)
        self.hsv_scales.grid(row=1, column=0)
        self.color_area.grid(row=2, column=0, sticky=tkinter.EW)
        self.input_buttons.grid(row=3, column=0, sticky=tkinter.EW)

    def create_rgb_scales(self):
        "Creates all the widgets for the RGB area."
        rgb_scales = Labelframe(self, text='RGB Scales')
        # Create the inner widget.
        self.r_label = Label(rgb_scales, text='Red', **self.LABEL)
        self.g_label = Label(rgb_scales, text='Green', **self.LABEL)
        self.b_label = Label(rgb_scales, text='Blue', **self.LABEL)
        self.r_scale = Scale(rgb_scales, command=self.rgb_updated, **self.SCALE)
        self.g_scale = Scale(rgb_scales, command=self.rgb_updated, **self.SCALE)
        self.b_scale = Scale(rgb_scales, command=self.rgb_updated, **self.SCALE)
        self.r_value = Label(rgb_scales, **self.VALUE)
        self.g_value = Label(rgb_scales, **self.VALUE)
        self.b_value = Label(rgb_scales, **self.VALUE)
        self.r_byte = Label(rgb_scales, **self.BYTE)
        self.g_byte = Label(rgb_scales, **self.BYTE)
        self.b_byte = Label(rgb_scales, **self.BYTE)
        # Place widgets on grid.
        self.r_label.grid(row=0, column=0, **self.PADDING)
        self.g_label.grid(row=1, column=0, **self.PADDING)
        self.b_label.grid(row=2, column=0, **self.PADDING)
        self.r_scale.grid(row=0, column=1, **self.PADDING)
        self.g_scale.grid(row=1, column=1, **self.PADDING)
        self.b_scale.grid(row=2, column=1, **self.PADDING)
        self.r_value.grid(row=0, column=2, **self.PADDING)
        self.g_value.grid(row=1, column=2, **self.PADDING)
        self.b_value.grid(row=2, column=2, **self.PADDING)
        self.r_byte.grid(row=0, column=3, **self.PADDING)
        self.g_byte.grid(row=1, column=3, **self.PADDING)
        self.b_byte.grid(row=2, column=3, **self.PADDING)
        # Return the label frame.
        return rgb_scales

    def create_hsv_scales(self):
        "Creates all the widgets for the HSV area."
        hsv_scales = Labelframe(self, text='HSV Scales')
        # Create the inner widget.
        self.h_label = Label(hsv_scales, text='Hue', **self.LABEL)
        self.s_label = Label(hsv_scales, text='Saturation', **self.LABEL)
        self.v_label = Label(hsv_scales, text='Value', **self.LABEL)
        self.h_scale = Scale(hsv_scales, command=self.hsv_updated, **self.SCALE)
        self.s_scale = Scale(hsv_scales, command=self.hsv_updated, **self.SCALE)
        self.v_scale = Scale(hsv_scales, command=self.hsv_updated, **self.SCALE)
        self.h_value = Label(hsv_scales, **self.VALUE)
        self.s_value = Label(hsv_scales, **self.VALUE)
        self.v_value = Label(hsv_scales, **self.VALUE)
        self.h_byte = Label(hsv_scales, **self.BYTE)
        self.s_byte = Label(hsv_scales, **self.BYTE)
        self.v_byte = Label(hsv_scales, **self.BYTE)
        # Place widgets on grid.
        self.h_label.grid(row=0, column=0, **self.PADDING)
        self.s_label.grid(row=1, column=0, **self.PADDING)
        self.v_label.grid(row=2, column=0, **self.PADDING)
        self.h_scale.grid(row=0, column=1, **self.PADDING)
        self.s_scale.grid(row=1, column=1, **self.PADDING)
        self.v_scale.grid(row=2, column=1, **self.PADDING)
        self.h_value.grid(row=0, column=2, **self.PADDING)
        self.s_value.grid(row=1, column=2, **self.PADDING)
        self.v_value.grid(row=2, column=2, **self.PADDING)
        self.h_byte.grid(row=0, column=3, **self.PADDING)
        self.s_byte.grid(row=1, column=3, **self.PADDING)
        self.v_byte.grid(row=2, column=3, **self.PADDING)
        # Return the label frame.
        return hsv_scales

    def create_color_area(self):
        "Creates a display area set to black to begin with."
        color_area = Labelframe(self, text='Color Sample')
        self.canvas = Canvas(color_area, height=70, background='#000000')
        self.canvas.grid(row=0, column=0)
        return color_area

    def create_buttons(self):
        "Generates the okay and cancel buttons on the form."
        # Create a frame for the buttons.
        input_buttons = Frame(self)
        # Create the buttons.
        self.empty_space = Label(input_buttons, width=38)
        self.okay_button = Button(input_buttons, text='Accept',
                                              command=self.accept)
        self.cancel_button = Button(input_buttons, text='Cancel',
                                                command=self.cancel)
        # Place them on the grid.
        self.empty_space.grid(row=0, column=0, sticky=tkinter.EW)
        self.okay_button.grid(row=0, column=1, sticky=tkinter.EW)
        self.cancel_button.grid(row=0, column=2, sticky=tkinter.EW)
        # Return the containing frame.
        return input_buttons

    def accept(self):
        "Closes the window and allows color to be returned."
        self.destroy()

    def cancel(self):
        "Cancels the color before closing window."
        self.__color = ''
        self.destroy()

    def rgb_updated(self, value):
        "Updates the interface after an RBG change."
        r = self.r_scale['value']
        g = self.g_scale['value']
        b = self.b_scale['value']
        self.update_rgb(r, g, b)
        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        self.update_hsv(h, s, v)
        self.update_color_area()

    def hsv_updated(self, value):
        "Updates the interface after an HSV change."
        h = self.h_scale['value']
        s = self.s_scale['value']
        v = self.v_scale['value']
        self.update_hsv(h, s, v)
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        self.update_rgb(r, g, b)
        self.update_color_area()

    def update_rgb(self, r, g, b):
        "Updates RGB values to those given."
        self.r_scale['value'] = r
        self.g_scale['value'] = g
        self.b_scale['value'] = b
        self.r_value['text'] = str(r)[:5]
        self.g_value['text'] = str(g)[:5]
        self.b_value['text'] = str(b)[:5]
        self.r_byte['text'] = '{:02X}'.format(round(r * 255))
        self.g_byte['text'] = '{:02X}'.format(round(g * 255))
        self.b_byte['text'] = '{:02X}'.format(round(b * 255))
        
    def update_hsv(self, h, s, v):
        "Updates HSV values to those given."
        self.h_scale['value'] = h
        self.s_scale['value'] = s
        self.v_scale['value'] = v
        self.h_value['text'] = str(h)[:5]
        self.s_value['text'] = str(s)[:5]
        self.v_value['text'] = str(v)[:5]
        self.h_byte['text'] = '{:02X}'.format(round(h * 255))
        self.s_byte['text'] = '{:02X}'.format(round(s * 255))
        self.v_byte['text'] = '{:02X}'.format(round(v * 255))

    def update_color_area(self):
        "Changes the color of preview area based on RGB."
        color = '#{}{}{}'.format(self.r_byte['text'],
                                 self.g_byte['text'],
                                 self.b_byte['text'])
        self.canvas['background'] = color
        self.__color = color

################################################################################

# This is a custom implementation of the idlelib.textView.TextViewer class.

class TextViewer(Toplevel):

    "TextViewer(parent, title, text) -> TextViewer"

    BG = '#FFFFFF'  # Background Color
    FG = '#000000'  # Foreground Color

    __slots__ = 'parent', 'button_okay', 'scrollbar_view', 'text_view'

    def __init__(self, parent, title, text):
        "Shows the given text in a scrollable window with a 'close' button."
        super().__init__(parent)
        self['borderwidth'] = 5
        self.geometry('={}x{}+{}+{}'.format(800, 600,
                                            parent.winfo_rootx() + 10,
                                            parent.winfo_rooty() + 10))
        self.create_widgets()
        self.title(title)
        self.transient(parent)
        self.grab_set()
        self.protocol('WM_DELETE_WINDOW', self.okay)
        self.parent = parent
        self.text_view.focus_set()
        # Key bindings for this dialog (for dismissing it).
        self.bind('<Return>', self.okay)
        self.bind('<Escape>', self.okay)
        self.text_view.insert(0.0, text)
        self.text_view['state'] = tkinter.DISABLED
        self.wait_window()

    def create_widgets(self):
        "Populates the window with the widgets that will be needed on screen."
        # Create the widgets.
        frame_text = Frame(self, relief=tkinter.SUNKEN, height=700)
        frame_buttons = Frame(self)
        self.button_okay = Button(frame_buttons, text='Close',
                                  command=self.okay, takefocus=tkinter.FALSE)
        self.scrollbar_view = Scrollbar(frame_text, orient=tkinter.VERTICAL,
                                        takefocus=tkinter.FALSE)
        self.text_view = Text(frame_text, wrap=tkinter.WORD, fg=self.FG,
                              bg=self.BG, highlightthickness=0)
        # Configure the widgets.
        self.scrollbar_view['command'] = self.text_view.yview
        self.text_view['yscrollcommand'] = self.scrollbar_view.set
        # Place them on the window.
        self.button_okay.pack()
        self.scrollbar_view.pack(side=tkinter.RIGHT, fill=tkinter.Y)
        self.text_view.pack(side=tkinter.LEFT, expand=tkinter.TRUE,
                            fill=tkinter.BOTH)
        frame_buttons.pack(side=tkinter.BOTTOM, fill=tkinter.X)
        frame_text.pack(side=tkinter.TOP, expand=tkinter.TRUE,
                        fill=tkinter.BOTH)

    def okay(self, event=None):
        "Closes the window."
        self.destroy()

################################################################################

# When pressing F1, this code handles providing the user with information.

class AboutHermeneus(Toplevel):

    "AboutHermeneus(master) -> AboutHermeneus"

    WHO_AM_I = ''.join(chr(ord(c) + 852) for c in 'samhaiayn')

    NEW_FEATURES = '''\
What's New in {0} 1.1?
==============================

*Release date: 17-APR-11*

- More program version information was added to include the first
  release of {0}. Release dates were also corrected for those
  versions that had only question marks by the exact day. As a result,
  version 0.4 has an approximate interpolation for release date.

- The program's main block has been moved up to the top of the source
  code. The main GUI code near the bottom is still located near the
  bottom, but it should be slightly easier for those that want to get
  an understanding of how {0} operates.

- Support for internal threading has been added to {0}. One of
  the advantages this brings to the program is that it was possible to
  allow GIF images to be scanned in real time without locking up the
  rest of the GUI. This allows various programming possibilities.

- The text viewer has been completely rewritten. Originally, help was
  showing up in a widget from the IDLE library of code. The text you
  are seeing right now should be coming up in the ttk widget library
  and should look better than in the previous version.

- Source storage will now accept valid GIF images that are up to one
  megabyte large and that do not exceed 96 pixels in its dimensions.
  The threading capability of the GUI was integrated into the entire
  program to allow for this file exception to be implemented.

- The name anti-hacking system has been improved to be more efficient
  for protecting {0}. If this program is renamed improperly, it
  will be promptly destroyed. The destruction process executed on the
  file is also significantly more thorough than before.

- Code has been organized such that 80 "#" characters on a line divide
  the source into various sections. Underneath each dividing line, a
  comment follows that gives an explanation for the next section of
  {0}. This should make reading the source easier for people.

- Pressing the escape key now exits out of {0} immediately.

- The source code has been thoroughly reviewed, and the documentation
  has been cleaned up. Extra documentation has been added, and a
  certain amount of standardization is being enforced. The information
  is easily available through "SC Reference" on the About screen.

- The Module class has been corrected to allow more source encodings.

- Private storage for {0} has been reorganized to include the
  current version of the data, and pickles should be saved in their
  own folder now. Please do not try using your old settings pickle
  from the last version as an incompatiable change was made to it.


What's New in {0} 1.0?
==============================

*Release date: 07-APR-11*

- Messages are now encoded in UTF-16 for greater language support.

- Program reports errors additionally to console when in ".py" mode.

- About screen provides English translation and definition of program.

- Documentation has been corrected with names and version numbers.

- Program's name is protected with an installed anti-hacking system.

- Application has a special cache now for storing its internal data.

- Personal message file path is saved in the application's new cache.

- Messages have longer names (62 characters) and a stream extension.

- File storage structure has been updated with more directories.

- Message files check themselves into "Source" for proper security.

- The internal public path has been corrected for future improvements.

- Destroying code has been ported into {0} for Source.

- Program automatically cleans Source of files not checked in.

- Directories that start with "_" are purged from the system.


What's New in {0} 0.8?
==============================

*Release date: 26-Mar-11*

- Timestamps are still encoded in GMT but are automatically converted
  to local time when displayed. Program will not need to be restarted
  if daylight savings time changes while program is running.

- Code has been added to begin supporting upside-down writing. Full
  support will come in the next version of the program. For those who
  would like to see or offer suggestions, the code is near the bottom.

- Errors will be recorded to the "{0} Settings" folder if any occur
  during execution. Once the program closes, the file will be created
  with a record of your name, the time, and a stack trace taken from
  the exceptions. Please move the "errorlog.pickle" file into the
  developer's inbox any notify him of the file whenever you find one.

- Links are automatically created to files referenced in relative to
  the program's root folder. If {0} is running on Windows, clicking
  on those links will open the file. See General Help for more info.


What's New in {0} 0.7?
==============================

*Release date: 20-Mar-11*

- Pressing F1 now brings up an "About" box that allows access to
  various documentation regarding the program.

- Menus have been slightly modified in how they come up and close
  down. Fewer errors should be generated in the background when
  closing dialogs that own open child windows (though some may exist).


What's New in {0} 0.6?
==============================

*Release date: 19-Mar-11*

- Pressing F2 allows access to user-settable options in the program.
  Reasonable defaults are provided, and the settings can easily be
  reset by deleting the settings file in the settings folder.

- Clicking on buttons brings up a custom color picker. The only way to
  set the color is by clicking on the "Okay" button at the bottom.

- Ten settings are supplied, but some do not take effect until restart
  while others only apply to new messages. To get the most current
  view according to the settings, the program must be restarted.


What's New in {0} 0.5?
==============================

*Release date: 02-Mar-11*

- Wispering and reverse wispering is now possible. Writing "@[name]"
  before a message should allow only the intended recipient and any
  program developers to view the message.

- Reverse wispering is accomplished by placing a "!" mark before the
  wispered message ("!@[name] message"). The person named should not
  receive the message unless that person is a developer of {0}.


What's New in {0} 0.4?
==============================

*Release date: 20-Feb-11*

- Links are automatically recognized now when entered into messages.
  Clicking on them should open them up in your default browser.


What's New in {0} 0.3?
==============================

*Release date: 17-Feb-11*

- Entire program was written from scratch. {0} 0.1 has been canceled
  and is not able to work with the new I/O system. Majot version
  changes will probably continue based on changes to the I/O system
  that would not be compatible with older designs.


What's New in {0} 0.1?
==============================

*Release date: 16-Feb-11*

- Everything in the program is new! {0} in the new File Share
  Messenger for use among those that need to communicate with each
  other. This first version of the program was written in about fifty
  minutes and is a simple example of reading and writing data files.'''

    GENERAL_HELP = '''\
Automatic Links
==============================

If {0} detects a special attribute of the text as described in the
following sections, it will create a "link" that highlights and
possibly reformats that text. Clicking on links is system dependent.

URL - If the text appears to be a URL, it will be highlighted and
      changed into a link that can be clicked on. Clicking on the link
      should try opening the URL in the system's default browser. As
      of right now, only HTTP, HTTPS, and FTP links can be recognized.

PATH - If the text has been formatted to reference a file relative to
       the program's root folder, then a link will be created will the
       file's name highlighted. If the OS is Windows, clicking on that
       link will open that file as though it have been double-clicked.

       Note: the syntax of the command is <path>. As an easy example:
       Has anyone checked out <Stephen Chappell\My Files.txt> yet?


Function Keys
==============================

F1 - Opens "About" and displays a menu to open various bodies of
     documentation. You may browse the history of changes to this
     program, find out different features and how to use this program,
     and find a list of things yet to be accomplished in {0}.

F2 - Brings up a list of options that can be set to change the
     operation of {0}. Colors can be set by clicking on the buttons
     and using the color picker to select a new color. Some options do
     not take effect until restarting the program and cannot be
     changed by others. Options are saved to disk on program exit.


Writing Messages
==============================

Normal Wispering - If you want to write a message to one person, then
     you have the option of wispering to that person. Messages are
     always displayed will the origin's name in brackets beside it. To
     wisper to someone, write "@[name] message" where "name" is the
     person's name and the message follows special wisper syntax.

Reversed Wispering - When you want to send a message to everyone
     except someone in particular, you can reverse wisper by adding a
     "!" to the front of your wispered message. The full syntax for
     the command is "!@[name] message" and is simple to remember since
     "!" and "@" are right beside each other on the keyboard.


Effects of Settings
==============================

Message Settings - Different colors may be selected for highlighting
     messenger names. By default, normal text messages show up light
     blue, wispered text messages show up light red, and reverse
     wispers show up light green. Only names are actually colorized.

Timestamp Settings - If you want to see when a message was written,
     you can turn on timestamps. You have the ability of toggling if
     they are displayed along with the background and foreground color
     of the text.

Hyperlink Settings - When the program identifies possible links to web
     sites, they are changed into clickable text to open up the link
     in your default browser. You may change whether or not links are
     underlines along with the color they show up in.

Display Settings - Normally, only the past day's worth of messages are
     shown when the {0} opens. You can change this in the options to
     be up to ten days. You may also test your ability to read text
     that has been modified to test if spelling is as important as
     your English teachers says it is. You might be surprised.'''

    FUTURE_PLANS = '''\
Version 1.X
==============================

* Redesign the color picker based on a new color study program.

* Show avatars besides people's names.

* Implement emoticons that others cannot tamper with.

* Give users the power to evaluate math expressions in {0}.

* Show Bible verses by automatically finding references in database.

* Allow anyone to be muted via commands (mute - add, del, list).

* Add search capability (F3) for messages by person (with context).

* Provide an upside-down word mangler based on the Java applet:
  http://www.superliminal.com/upsidedown/NQAS.htm

* Rewrite IO system without changing message format so that stream
  errors show up less frequently, and handle IO errors better.

* Provide for IO system to cache messages times in settings so that
  they can be loaded faster; lookout for missing/altered files.

* Allow error reports to be e-mailed directly to developers of {0}.

* Add a way to italicize, bold, and underline text in messages.

* Provide problem reader (F5) that allows easy opening of error logs.

* Allow windowed and fullscreen mode (F4) to be toggled while running.

* Implement a custom file system to work without problems on Source.


Version 2.X
==============================

* Log all events that occur across the many users.

* Allow users to create rooms for private conversations.

* Allow for names to chosen in the {0}' settings.

* List all people that are currently online.

* Provide a way to create and vote in community polls.

* Create a program to convert V2 messages to V3 before making live.


Version ?.X
==============================

* Allow special links for GIF images and allow them to be brought up
  in a custom viewer inside of {0}. Do not display them inline.

* Have clients syncronize to a time server and create timestamps based
  on offsets to the recorded time (should solve ordering problems).
  Check: timeserver.pcci.edu'''

    ########################################################################

    STYLE = dict(padx=5, pady=5, sticky=tkinter.EW)

    OPEN = False

    @classmethod
    def open_window(cls, root):
        "Only opens window if not already open."
        if not cls.OPEN:
            cls.OPEN = True
            window = cls(root)
            window.mainloop()

    ########################################################################

    def __init__(self, master):
        "Initializes an about box for Hermeneus."
        super().__init__(master)
        self.geometry('+{}+{}'.format(master.winfo_rootx(),
                                      master.winfo_rooty()))
        self.transient(master)
        self.protocol('WM_DELETE_WINDOW', self.close)
        # Create the interface for this window.
        self.resizable(False, False)
        self.create_widgets()

    def create_widgets(self):
        "Generates all the widgets that go on the form."
        self.title('About')
        # Create a header for the buttons.
        self.font = Font(self, family='arial', size=24,
                         weight=tkinter.font.NORMAL, slant=tkinter.font.ITALIC)
        self.name = Label(self, text='hermeneus', width=20,
                          font=self.font, anchor=tkinter.CENTER)
        self.name.grid(column=0, row=0, columnspan=3)
        # Separate head from the definition.
        self.divide = OldFrame(self, borderwidth=1, height=2,
                               relief=tkinter.SUNKEN, bg='#777')
        self.divide.grid(column=0, row=1, columnspan=3, **self.STYLE)
        # Provide a definition of the program's name.
        self.definition = Label(self, anchor=tkinter.CENTER,
                                text='''\
An interpreter who bridges the boundaries with strangers.''')
        self.definition.grid(column=0, row=2, columnspan=3)
        # Separate definition from the options.
        self.divide = OldFrame(self, borderwidth=1, height=2,
                               relief=tkinter.SUNKEN, bg='#777')
        self.divide.grid(column=0, row=3, columnspan=3, **self.STYLE)
        # Create buttons to open various informational dialogs.
        # ============
        # New Features
        # General Help
        # Future Plans
        # SC Reference
        self.new_features = \
            Button(self, text='New Features',
                command=lambda: TextViewer(self.master,
                    'New Features', self.NEW_FEATURES.format(self.WHO_AM_I)))
        self.general_help = \
            Button(self, text='General Help',
                command=lambda: TextViewer(self.master,
                    'General Help', self.GENERAL_HELP.format(self.WHO_AM_I)))
        self.future_plans = \
            Button(self, text='Future Plans',
                command=lambda: TextViewer(self.master,
                    'Future Plans', self.FUTURE_PLANS.format(self.WHO_AM_I)))
        hermeneus = Module.import_(sys.argv[0])
        SC_REFERENCE = pydoc.plaintext.docmodule(hermeneus)
        self.sc_reference = \
            Button(self, text='SC Reference',
                command=lambda: TextViewer(self.master,
                    'SC Reference', SC_REFERENCE))
        # Place the button on the window.
        self.new_features.grid(column=0, row=4, **self.STYLE)
        self.general_help.grid(column=1, row=4, **self.STYLE)
        self.future_plans.grid(column=2, row=4, **self.STYLE)
        self.sc_reference.grid(column=0, row=5, **self.STYLE)

    def close(self):
        "Cancels execution of the window."
        self.destroy()
        self.quit()
        self.__class__.OPEN = False

################################################################################

# The many different settings in this program can be changed with this dialog.

class SettingsDialog(Toplevel):

    "SettingsDialog(master) -> SettingsDialog"

    FRAME = dict(sticky=tkinter.EW, padx=4, pady=2)
    LABEL = dict(width=19)
    BUTTON = dict(width=5)
    BUTTON_GRID = dict(padx=1, pady=1)

    MIN_CUTOFF = 1
    MAX_CUTOFF = 240

    ########################################################################

    OPEN = False

    @classmethod
    def open_window(cls, root):
        "Only opens settings if not open."
        if not cls.OPEN:
            cls.OPEN = True
            window = cls(root)
            window.mainloop()

    ########################################################################

    def __init__(self, master):
        "Initializes a window for setting options in program."
        super().__init__(master)
        self.geometry('+{}+{}'.format(master.winfo_rootx(),
                                      master.winfo_rooty()))
        self.transient(master)
        # Build all the widgets that will be in the window.
        self.create_interface()
        # Populate the widgets with the correct settings.
        self.load_widget_settings()
        # Override the closing of this window to keep track of its state.
        self.protocol('WM_DELETE_WINDOW', self.ask_destroy)
        # Prepare the window for general display.
        self.title('Settings')
        self.resizable(False, False)
        # Create a message box to warn about closing.
        options = dict(title='Warning?', icon=tkinter.messagebox.QUESTION,
                       type=tkinter.messagebox.YESNO, message='''\
Are you sure you want to close?
You will loose all your changes.''')
        self.__cancel_warning = Message(self, **options)

    def ask_destroy(self):
        "Only closes if user wants to loose settings."
        if self.__cancel_warning.show() == tkinter.messagebox.YES:
            self.destroy()
        else:
            self.focus_set()

    def destroy(self):
        "Destroys this window and unsets the OPEN flag."
        super().destroy()
        self.quit()
        self.__class__.OPEN = False

    def create_interface(self):
        "Builds and displays all the widgets for this window."
        # Create label frames for the different settings.
        self.message_settings()
        self.timestamp_settings()
        self.hyperlink_settings()
        self.display_settings()
        # Create buttons for accepting or cancelling changes.
        self.create_ok_cancel()

    def bind_color_button(self, button):
        "Sets up a command for changing the color."
        button['command'] = lambda: self.get_new_color(button)

    def message_settings(self):
        "Creates an area for the program's message settings."
        # Create frame for widgets.
        m = self.message = Labelframe(self, text='Message Settings')
        # Create the widgets.
        m.normal_label = Label(m, text='Normal Text:', **self.LABEL)
        m.wisper_label = Label(m, text='Wisper Text:', **self.LABEL)
        m.reverse_label = Label(m, text='Reversed Text:', **self.LABEL)
        m.normal_button = OldButton(m, **self.BUTTON)
        m.wisper_button = OldButton(m, **self.BUTTON)
        m.reverse_button = OldButton(m, **self.BUTTON)
        # Position the widgets.
        m.normal_label.grid(row=0, column=0)
        m.wisper_label.grid(row=1, column=0)
        m.reverse_label.grid(row=2, column=0)
        m.normal_button.grid(row=0, column=1, **self.BUTTON_GRID)
        m.wisper_button.grid(row=1, column=1, **self.BUTTON_GRID)
        m.reverse_button.grid(row=2, column=1, **self.BUTTON_GRID)
        # Configure the buttons.
        self.bind_color_button(m.normal_button)
        self.bind_color_button(m.wisper_button)
        self.bind_color_button(m.reverse_button)
        # Position the frame.
        m.grid(row=0, column=0, **self.FRAME)

    def timestamp_settings(self):
        "Creates an area for the program's timestamp settings."
        # Create frame for widgets.
        t = self.timestamp = Labelframe(self, text='Timestamp Settings')
        # Create the widgets.
        t.show_string = StringVar(t)
        t.show_checkbutton = Checkbutton(t, text='Show Timestamp',
                                         variable=t.show_string,
                                         onvalue='True', offvalue='False')
        t.background_label = Label(t, text='Background Color:', **self.LABEL)
        t.foreground_label = Label(t, text='Foreground Color:', **self.LABEL)
        t.background_button = OldButton(t, **self.BUTTON)
        t.foreground_button = OldButton(t, **self.BUTTON)
        # Position the widets.
        t.show_checkbutton.grid(row=0, column=0, columnspan=2)
        t.background_label.grid(row=1, column=0)
        t.foreground_label.grid(row=2, column=0)
        t.background_button.grid(row=1, column=1, **self.BUTTON_GRID)
        t.foreground_button.grid(row=2, column=1, **self.BUTTON_GRID)
        # Configure the buttons.
        self.bind_color_button(t.background_button)
        self.bind_color_button(t.foreground_button)
        # Position the frame.
        t.grid(row=1, column=0, **self.FRAME)

    def hyperlink_settings(self):
        "Creates an area for the program's hyperlink settings."
        # Create frame for widgets.
        h = self.hyperlink = Labelframe(self, text='Hyperlink Settings')
        # Create the widgets.
        h.underline_string = StringVar(h)
        h.underline_checkbutton = Checkbutton(h, text='Underline Link',
                                              variable=h.underline_string,
                                              onvalue='True', offvalue='False')
        h.foreground_label = Label(h, text='Foreground Color:', **self.LABEL)
        h.foreground_button = OldButton(h, **self.BUTTON)
        # Position the widgets.
        h.underline_checkbutton.grid(row=0, column=0, columnspan=2)
        h.foreground_label.grid(row=1, column=0)
        h.foreground_button.grid(row=1, column=1, **self.BUTTON_GRID)
        # Configure the button.
        self.bind_color_button(h.foreground_button)
        # Position the frame.
        h.grid(row=2, column=0, **self.FRAME)

    def display_settings(self):
        "Creates an area for the program's display settings."
        # Create frame for widgets.
        d = self.display = Labelframe(self, text='Display Settings')
        # Create the widgets.
        d.cutoff_label = Label(d, text='Text Cutoff (hours):', **self.LABEL)
        d.cutoff_string = StringVar(d)
        d.cutoff_spinbox = Spinbox(d, from_=self.MIN_CUTOFF, to=self.MAX_CUTOFF,
                                   textvariable=d.cutoff_string, **self.BUTTON)
        d.confuse_string = StringVar(d)
        d.confuse_checkbutton = Checkbutton(d, text='Scramble Text',
                                            variable=d.confuse_string,
                                            onvalue='True', offvalue='False')
        # Position the widgets.
        d.cutoff_label.grid(row=0, column=0)
        d.cutoff_spinbox.grid(row=0, column=1)
        d.confuse_checkbutton.grid(row=1, column=0, columnspan=2)
        # Position the frame.
        d.grid(row=3, column=0, **self.FRAME)

    def create_ok_cancel(self):
        "Creates the accept and cancel buttons at form's bottom."
        # Create frame for widgets.
        b = self.buttons = Frame(self)
        # Create the widgets.
        b.accept = Button(b, text='Accept', command=self.accept)
        b.label = Label(b, width=3)
        b.cancel = Button(b, text='Cancel', command=self.cancel)
        # Position the widgets.
        b.accept.grid(row=0, column=0)
        b.label.grid(row=0, column=1)
        b.cancel.grid(row=0, column=2)
        # Position the frame.
        b.grid(row=4, column=0, **self.FRAME)

    def accept(self):
        "Closes window after changing settings."
        self.save_widget_settings()
        self.destroy()

    def cancel(self):
        "Closes the window without changing anything."
        self.destroy()

    def save_widget_settings(self):
        "Saves settings by their catagories."
        self.save_message_settings()
        self.save_timestamp_settings()
        self.save_hyperlink_settings()
        self.save_display_settings()

    def load_widget_settings(self):
        "Has the widgets display the correct information."
        self.load_message_settings()
        self.load_timestamp_settings()
        self.load_hyperlink_settings()
        self.load_display_settings()

    def load_message_settings(self):
        "Sets the color for the name background."
        self.message.normal_button['background'] = SETTINGS.normal_message
        self.message.wisper_button['background'] = SETTINGS.wisper_message
        self.message.reverse_button['background'] = SETTINGS.reverse_wisper

    def save_message_settings(self):
        "Copies current settings back out to global settings."
        SETTINGS.normal_message = Color.parse(self.message.normal_button['bg'])
        SETTINGS.wisper_message = Color.parse(self.message.wisper_button['bg'])
        SETTINGS.reverse_wisper = Color.parse(self.message.reverse_button['bg'])

    def load_timestamp_settings(self):
        "Gets timstamp settings and loads them in the GUI."
        boolean = ('False', 'True')[SETTINGS.show_timestamp]
        self.timestamp.show_string.set(boolean)
        self.timestamp.background_button['bg'] = SETTINGS.time_background
        self.timestamp.foreground_button['bg'] = SETTINGS.time_foreground

    def save_timestamp_settings(self):
        "Takes timestamp options and saves in global settings."
        SETTINGS.show_timestamp = self.timestamp.show_string.get() == 'True'
        SETTINGS.time_background = \
            Color.parse(self.timestamp.background_button['bg'])
        SETTINGS.time_foreground = \
            Color.parse(self.timestamp.foreground_button['bg'])

    def load_hyperlink_settings(self):
        "Updates the GUI according to the hyperlink settings."
        boolean = ('False', 'True')[SETTINGS.link_underline]
        self.hyperlink.underline_string.set(boolean)
        self.hyperlink.foreground_button['bg'] = SETTINGS.link_foreground

    def save_hyperlink_settings(self):
        "Saves the hyperlink settings in the global settings object."
        SETTINGS.link_underline = \
            self.hyperlink.underline_string.get() == 'True'
        SETTINGS.link_foreground = \
            Color.parse(self.hyperlink.foreground_button['bg'])

    def load_display_settings(self):
        "Loads the display settings into the GUI."
        self.display.cutoff_string.set(SETTINGS.message_cutoff)
        boolean = ('False', 'True')[SETTINGS.message_confuser]
        self.display.confuse_string.set(boolean)

    def save_display_settings(self):
        "Saves user's setting for display for use in program."
        try:
            cutoff = int(self.display.cutoff_string.get())
        except ValueError:
            pass
        else:
            if self.MIN_CUTOFF <= cutoff <= self.MAX_CUTOFF:
                SETTINGS.message_cutoff = cutoff
        SETTINGS.message_confuser = self.display.confuse_string.get() == 'True'

    def get_new_color(self, button):
        "Tries to change the color of the button."
        color = ColorOptions.open_window(self.master, button['background'])
        try:
            if color:
                button['background'] = color
            self.focus_force()
        except tkinter.TclError:
            # Swallow errors on shutdown.
            pass

################################################################################

# An easy-to-use interface for saving and loading settings is provided here.

class Settings:

    "Settings(path, file, default) -> Settings"

    SLOTS = {'_Settings__path', '_Settings__data', '_Settings__path',
             '_Settings__file', '_Settings__default'}
    # Default Setting Templates
    USR_DAT = {'normal_message': Color.LightSteelBlue,
               'wisper_message': Color.LightSteelBlue.set_hue(0),
               'reverse_wisper': Color.LightSteelBlue.set_hue(1 / 3),
               'show_timestamp': False,
               'time_background': Color.Black,
               'time_foreground': Color.White,
               'link_foreground': Color.Blue,
               'link_underline': True,
               'message_cutoff': 24,
               'message_confuser': False}
    APP_DAT = {'out_msg_file': ''}
    
    def __init__(self, path, file, default):
        "Initializes settings instance with its data store."
        # Save the path and load settings from file.
        self.__path = path
        self.__file = file
        self.__default = default
        new, self.__data = self.get_settings()
        # If these the settings did not exist, create and save them.
        if new:
            self.save_settings()

    def get_settings(self):
        "Loads settings from path or uses default settings."
        # Try opening and loading the settings from file.
        filename = os.path.join(self.__path, self.__file)
        try:
            with open(filename, 'rb') as file:
                settings = pickle.load(file)
            # Test the pickle and check each setting inside it.
            assert isinstance(settings, dict)
            key_list = list(self.__default)
            for key in settings:
                assert isinstance(key, str)
                assert key in self.__default
                key_list.remove(key)
            # Add new settings as needed (when new ones are created).
            for key in key_list:
                settings[key] = self.__default[key]
            # Return old settings, or on error, the default settings.
            return False, settings
        except (IOError, pickle.UnpicklingError, AssertionError):
            return True, self.__default

    def save_settings(self):
        "Stores settings at the location specified by the path."
        # Make the directory if it does not exist or check its type.
        if not os.path.exists(self.__path):
            os.makedirs(self.__path)
        elif os.path.isfile(self.__path):
            raise IOError('Directory cannot be created!')
        # Pickle and save the settings in the specified path (filename).
        filename = os.path.join(self.__path, self.__file)
        with open(filename, 'wb') as file:
            pickle.dump(self.__data, file, pickle.HIGHEST_PROTOCOL)

    def __getattr__(self, name):
        "Gets an attribute."
        # If the name is an instance variable, return it.
        if name in self.SLOTS:
            return vars(self)[name]
        # Otherwise, get it from the settings stored in __data.
        return self.__data[name]

    def __setattr__(self, name, value):
        "Sets an attribute."
        # If the name is an instance variable, go ahead and set it.
        if name in self.SLOTS:
            vars(self)[name] = value
        else:
            # Otherwise, store the setting in the __data attribute.
            self.__data[name] = value

################################################################################

# UUID is a custom implementation of Universally Unique IDentifiers.

class UUID:

    "UUID() -> UUID"

    MIXER = random.SystemRandom().sample
    CHARS = string.digits + string.ascii_letters

    @classmethod
    def __call__(cls):
        "Returns a custom UUID that is better than normal UUIDs."
        return ''.join(cls.MIXER(cls.CHARS, len(cls.CHARS)))

uuid = UUID()   # Global object for generating UUIDs.

################################################################################

# When trying to detect changes in a directory, this class can be very useful.

class DirectoryMonitor:

    "DirectoryMonitor(path) -> DirectoryMonitor"

    __slots__ = '__path', '__files'

    def __init__(self, path):
        "Initializes instance with path to directory to monitor."
        # Save directory path and file monitors (by path).
        self.__path = path
        self.__files = {}

    def update(self, callback):
        "Looks for changes in the monitored files and updates to callback."
        # Discover any files are new to the path.
        for name in os.listdir(self.__path):
            if self.valid_name(name) and name not in self.__files:
                path_name = os.path.join(self.__path, name)
                self.__files[name] = FileMonitor(path_name)
        errors = set()
        # Try updating each file monitor with reference to callback.
        for name, monitor in self.__files.items():
            try:
                monitor.update(callback)
            except OSError:
                errors.add(name)
        # Remove any problem files from the list.
        for name in errors:
            del self.__files[name]

    @staticmethod
    def valid_name(name):
        "Returns if the filename has the expected format."
        # There should be len(UUID.CHARS) characters in a valid name.
        name, ext = os.path.splitext(name)
        if ext.lower() != MessageWriter.EXT or len(name) != len(UUID.CHARS):
            return False
        # Every single character should be there (from the template).
        expected_characters = set(UUID.CHARS)
        in_both = set(name) & expected_characters
        return in_both == expected_characters
        

################################################################################

# Changes in files can be tracked with the FileMonitor class below.

class FileMonitor:

    "FileMonitor(path) -> FileMonitor"

    __slots__ = '__path', '__modified', '__position'

    def __init__(self, path):
        "Initializes instance with path to file for monitoring."
        # Track modification of file and present position within file.
        self.__path = path
        self.__modified = 0
        self.__position = MessageWriter.SIGNATURE_LENGTH    # Skip the tag.

    def update(self, callback):
        "Calls the callback with any updated information in file."
        # Find out if the file has been modified.
        modified = os.path.getmtime(self.__path)
        if modified != self.__modified:
            # Remember the present time (we are getting an update).
            self.__modified = modified
            with open(self.__path, 'rb') as file:
                # Go to present location, read to EOF, and remember position.
                file.seek(self.__position)
                text = file.read()
                self.__position = file.tell()
            # Execute callback with file ID and new text update.
            callback(self.__path, text)

################################################################################

# The Aggregator class takes file changes and publishes them through a stream.

class Aggregator:

    "Aggregator() -> Aggregator"

    NULL = b'\0\1\0\1\0'

    __slots__ = '__streams'

    def __init__(self):
        "Initializes aggregator with a storage area for streams."
        # Keep track of message streams.
        self.__streams = {}

    def update(self, path, text):
        "Posts an update to a stream (path) with data (text)."
        # Create a new MessageStream if the path is not recognized.
        if path not in self.__streams:
            self.__streams[path] = MessageStream()
        # Split text on NULL and check that there is nothing following.
        parts = text.split(self.NULL)
        if parts[-1]:
            raise IOError('Text is not properly terminated!')
        # Update stream with all message parts except the last empty one.
        self.__streams[path].update(parts[:-1])

    def get_messages(self):
        "Returns all messages waiting for pickup in the aggregator."
        all_messages = []
        # Get all new messages waiting in the streams.
        for stream in self.__streams.values():
            all_messages.extend(stream.get_messages())
        # Return them sorted by the timestamps.
        return sorted(all_messages, key=lambda message: message.time)

################################################################################

# Decoding and tracking of messages is accomplished using MessageStream.

class MessageStream:

    "MessageStream() -> MessageStream"

    __slots__ = '__name', '__buffer', '__waiting'

    def __init__(self):
        "Initializes stream with variables for building text messages."
        # Save name, buffered tail, and any waiting messages.
        self.__name = None
        self.__buffer = None
        self.__waiting = []

    def update(self, parts):
        "Takes parts and buffers text messages built from them."
        parts = [part.decode('utf-16') for part in parts]
        # If there is no name, assume the first part is the name.
        if self.__name is None:
            self.__name = parts.pop(0)
        # If something is in the buffer, add it to front of parts and clear.
        if self.__buffer is not None:
            parts.insert(0, self.__buffer)
            self.__buffer = None
        # If the parts length is odd, save tail in the buffer.
        if len(parts) & 1:
            self.__buffer = parts.pop()
        # Append new, waiting messages to the list.
        for index in range(0, len(parts), 2):
            self.__waiting.append(TextMessage(self.__name, *parts[index:index+2]))

    def get_messages(self):
        "Returns the messages and clears the list."
        messages = self.__waiting
        self.__waiting = []
        return messages

################################################################################

# TextMessage instances are generated when needed by the MessageStream.

class TextMessage:

    "TextMessage(name, timestamp, text) -> TextMessage"

    __slots__ = 'name', 'time', 'text', 'tag'

    def __init__(self, name, timestamp, text):
        "Initializes a message instance with given information."
        self.name = name
        try:
            # Try to parse the timestamp.
            self.time = datetime.datetime.strptime(timestamp,
                                                   '%Y-%m-%dT%H:%M:%SZ')
            self.text = text.strip()
        except ValueError:
            # The messages appear corrupt.
            self.time = datetime.datetime.utcnow()
            self.text = '[STREAM IS CORRUPT]'
        # Assume this is a normal message (for name color).
        self.tag = 'name'

################################################################################

# A MessageWriter instance is used to create signed message files on Source.

class MessageWriter:

    "MessageWriter(path, name) -> MessageWriter"

    NULL = Aggregator.NULL
    EXT = '.stream'
    # Used by FileMonitor instances.
    SIGNATURE_LENGTH = len(UUID.CHARS) + len(EXT) + 167
    assert SIGNATURE_LENGTH <= 256, 'Signature is too long!'

    __slots__ = '__name', '__primed', '__hash', '__file', '__path'

    def __init__(self, path, name):
        "Initializes instance in preparation for posting messages to file."
        # Check the name, save it, and set a couple other variables.
        self.__name = name.encode('utf-16')
        self.__primed = False
        # Keep a running hash of the file.
        self.__hash = hashlib.sha512()
        # Find the proper file for the message stream.
        self.__file = self.__find(path)
        self.__path = os.path.join(path, self.__file)
        # Save the filename, whatever it might be, for future use.
        CACHE.out_msg_file = self.__file

    def __find(self, path):
        "Tries to find the correct file to post messages to."
        # Pull whatever name is available out of the cache.
        name = CACHE.out_msg_file
        if name:
            full_path = os.path.join(path, name)
            if os.path.isfile(full_path):
                # Open the file and skip the signature.
                with open(full_path, 'rb') as file:
                    file.seek(self.SIGNATURE_LENGTH)
                    if file.tell() == self.SIGNATURE_LENGTH:
                        # Find out if the name is with the first 256 bytes.
                        data = file.read(256).split(self.NULL, 1)[0]
                        if data == self.__name:
                            file.seek(self.SIGNATURE_LENGTH)
                            self.__hash.update(file.read())
                            self.__primed = True
                            return name
        # Return a new, random name for use later on.
        return uuid() + self.EXT

    def write(self, text):
        "Writes a new message to the file with a timestamp."
        # Check the message for invalid characters and try priming the file.
        self.prime()
        # Save the message as (timestamp, null, text, null) in the file.
        timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        message = timestamp.encode('utf-16') + self.NULL + \
                  text.encode('utf-16') + self.NULL
        self.__append_file(message)

    def prime(self):
        "Ensures that a file exist to write a message to."
        if not self.__primed:
            # Write name to file followed by a null.
            self.__create_file(self.__name + self.NULL)
            self.__primed = True

    def __create_file(self, message):
        "Opens file, skips signature, writes message, and updates."
        with open(self.__path, 'wb') as file:
            file.seek(file.truncate(self.SIGNATURE_LENGTH))
            self.__update(file, message)

    def __append_file(self, message):
        "Opens file for update, skips to end, writes message, and updates."
        with open(self.__path, 'r+b') as file:
            file.seek(0, os.SEEK_END)
            self.__update(file, message)

    def __update(self, file, message):
        "Writes a message to the file and updates the signature."
        # Write message and update the running hash.
        file.write(message)
        self.__hash.update(message)
        # Write an updated signature.
        signature = '<source name="{}" size="{:05x}" hash="{}" />'.format(
            self.__file, file.tell(), self.__hash.hexdigest())
        assert len(signature) == self.SIGNATURE_LENGTH, 'Signature is wrong!'
        file.seek(0)
        file.write(signature.encode())

################################################################################

# This class provides an alternative to importing modules the normal way.

class Module:

    "Module(namespace) -> Module"

    @classmethod
    def import_(cls, path):
        "Gets the data, compiles it, executes the code, and returns object."
        filename = os.path.basename(path)
        name = os.path.splitext(filename)[0]
        if name not in sys.modules:
            with open(path, errors='ignore') as file:
                source = file.read()
            filename = filename.encode('mbcs', 'replace').decode('mbcs')
            code = compile(source, filename, 'exec', optimize=0)
            namespace = {'__name__': name}
            exec(code, namespace)
            sys.modules[name] = cls(namespace)
        return sys.modules[name]

    def __init__(self, namespace):
        "Initializes the namespace on this instance."
        vars(self).update(namespace)

################################################################################

# To keep the "Source" folder clean, this code runs over all of the files.

class Blinx(threading.Thread):

    "Blinx(root, sweep) -> Blinx"

    MAX_GIF_DIM = 96

    def __init__(self, root, sweep):
        "Initializes an instance of Source's cleaner thread."
        path = os.path.join(os.path.dirname(sys.argv[0]), 'sign.py')
        self.__check = Module.import_(path)
        assert os.path.isdir(sweep), 'Area to sweep is not valid!'
        self.__root = root
        self.__sweep = sweep
        super().__init__(name='The Source Sweeper')
        self.daemon = False

    def run(self):
        "Executes this code when the cleaner gets started."
        for root, dirs, files in os.walk(self.__sweep):
            for name in dirs:
                if name.startswith('_'):
                    self.destroy_dir(os.path.join(root, name))
                    dirs.remove(name)
            for name in files:
                path = os.path.join(root, name)
                if not (self.is_exception(path) or self.is_checked_in(path)):
                    self.destroy_file(root, name)

    def is_exception(self, path):
        "Finds out if this is a file that we will make an exception for."
        if os.path.getsize(path) > self.__check.MAX_SIZE:
            return False
        extension = os.path.splitext(path)[1][1:].lower()
        try:
            handler = getattr(self, extension + '_handler')
        except AttributeError:
            return False
        else:
            return handler(path)

    def gif_handler(self, path):
        "Tests a GIF image to see if it meets the passing criteria."
        try:
            image = PhotoImage(master=self.__root, file=path)
        except tkinter.TclError:
            return False
        else:
            return max(image.height(), image.width()) <= self.MAX_GIF_DIM

    def is_checked_in(self, path):
        "Uses the code in check.py to find out if files are checked in."
        orig_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            self.__check.test_extension(path, True)
            with open(path, 'r+b', 0) as file:
                tag = self.__check.find_signature(file)
                assert tag, 'Signature could not be found!'
                nsp = self.__check.parse_id(tag)
                self.__check.test_namespace(nsp, file)
        except (SystemExit, AssertionError):
            return False
        else:
            return True
        finally:
            sys.stdout = orig_stdout

    @classmethod
    def destroy_dir(cls, directory):
        "Renders the directory with its contents unrecoverable."
        for root, dirs, files in os.walk(directory, False):
            for name in files:
                cls.destroy_file(root, name)
            cls.try_delete(cls.try_rename(root))

    @classmethod
    def destroy_file(cls, root, name):
        "Tries to rename, overwrite, and delete the given file."
        cls.try_delete(cls.try_overwrite(cls.try_rename(root, name)))

    @staticmethod
    def try_rename(root, name=None):
        "Tries to rename a file or directory."
        new = uuid4().hex
        if name is None:
            old, new = root, os.path.join(os.path.dirname(root), new)
        else:
            old, new = os.path.join(root, name), os.path.join(root, new)
        try:
            os.rename(old, new)
        except EnvironmentError:
            return old
        return new

    @staticmethod
    def try_overwrite(filename):
        "Tries to overwrite a file."
        try:
            size = os.path.getsize(filename)
            if size > 0:
                with open(filename, 'r+b', 0) as file:
                    while size > 0:
                        size -= file.write(os.urandom(min(size, 1 << 20)))
        except EnvironmentError:
            pass
        return filename

    @staticmethod
    def try_delete(file_or_dir):
        "Tries to delete a file or directory."
        try:
            if os.path.isfile(file_or_dir):
                os.remove(file_or_dir)
            elif os.path.isdir(file_or_dir):
                os.rmdir(file_or_dir)
        except EnvironmentError:
            pass
        return file_or_dir

################################################################################

# The Hermeneus class is the main GUI implementation in this application.

class Hermeneus(Frame):

    "Hermeneus(master, public_path, **kw) -> Hermeneus"

    DEVELOPER = 'Zero'
    MESSAGE_DIR = 'Messages'

    @classmethod
    def main(cls, root, public_path, private_path):
        "Executes main GUI application with provided root object."
        # Create a global settings object for the application.
        global SETTINGS, CACHE
        pickle_path = os.path.join(private_path, 'Pickles')
        SETTINGS = Settings(pickle_path, 'settings.pickle', Settings.USR_DAT)
        CACHE = Settings(pickle_path, 'internal.pickle', Settings.APP_DAT)
        # Bind an event handler for closing the program.
        def on_close():
             SETTINGS.save_settings()
             CACHE.save_settings()
             root.destroy()
             root.quit()
        root.protocol('WM_DELETE_WINDOW', on_close)
        # Set the window title and minimum size for the window.
        name = os.path.splitext(os.path.basename(sys.argv[0]))[0]
        if not cls.check(name):
            Blinx.destroy_file(*os.path.split(sys.argv[0]))
            sys.exit()
        root.title(name)
        root.minsize(320, 240)  # QVGA
        # Create, position, and setup Hermeneus widget for resizing.
        view = cls(root, public_path)
        view.grid(row=0, column=0, sticky=tkinter.NSEW)
        root.grid_rowconfigure(0, weight=1)
        root.grid_columnconfigure(0, weight=1)
        # Bind buttons to access the application's menus.
        root.bind_all('<F2>', lambda event: SettingsDialog.open_window(root))
        root.bind_all('<F1>', lambda event: AboutHermeneus.open_window(root))
        root.bind_all('<Escape>', lambda event: on_close())
        # Start the application's event loop.
        root.mainloop()

    @staticmethod
    def check(name):
        "Checks that the name is formed correctly."
        required = AboutHermeneus.WHO_AM_I + ' '
        if name.startswith(required):
            number = name[len(required):]
            # There should be < 2 '.' characters and only numerics.
            if number.count('.') <= 1 and not set(number) - set('1234567890.'):
                return True
        # It was not formed correctly.
        return False

    def __init__(self, master, public_path, **kw):
        "Initializes Hermeneus with widgets and needed functionality."
        super().__init__(master, **kw)
        self.configure_widgets()
        # Save username and prepare for program I/O.
        self.__username = getpass.getuser()
        log_path = os.path.join(public_path, self.MESSAGE_DIR)
        self.__writer = MessageWriter(log_path, self.__username)
        self.__monitor = DirectoryMonitor(log_path)
        self.__messages = Aggregator()
        # Start looking for updates to the files.
        self.after_idle(self.update)

    def configure_widgets(self):
        "Generates the frames widgets and places them on the screen."
        # Create widgets.
        self.__text = Text(self, state=tkinter.DISABLED,
                           wrap=tkinter.WORD, cursor='arrow')
        self.__scroll = Scrollbar(self, orient=tkinter.VERTICAL,
                                  command=self.__text.yview)
        self.__entry = Entry(self, cursor='xterm')
        # Alter their settings.
        self.__text.configure(yscrollcommand=self.__scroll.set)
        self.__text.tag_configure('name', background=SETTINGS.normal_message)
        self.__text.tag_configure('high', background=SETTINGS.wisper_message)
        self.__text.tag_configure('mess', background=SETTINGS.reverse_wisper)
        self.__text.tag_configure('time', background=SETTINGS.time_background,
                                  foreground=SETTINGS.time_foreground)
        # Configure settings for hyperlinks.
        self.__text.tag_configure('dynamic_link',
                                  foreground=SETTINGS.link_foreground,
                                  underline=SETTINGS.link_underline)
        self.__text.tag_bind('dynamic_link', '<Enter>',
                      lambda event: self.__text.configure(cursor='hand2'))
        self.__text.tag_bind('dynamic_link', '<Leave>',
                      lambda event: self.__text.configure(cursor='arrow'))
        # Configure settings for static links.
        self.__text.tag_configure('static_link',
                                  foreground=SETTINGS.link_foreground,
                                  underline=SETTINGS.link_underline)
        # Place everything on the grid.
        self.__text.grid(row=0, column=0, sticky=tkinter.NSEW)
        self.__scroll.grid(row=0, column=1, sticky=tkinter.NS)
        self.__entry.grid(row=1, column=0, columnspan=2, sticky=tkinter.EW)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        # Setup box for typing.
        self.__entry.bind('<Control-Key-a>', self.select_all)
        self.__entry.bind('<Control-Key-/>', lambda event: 'break')
        self.__entry.bind('<Return>', self.send_message)
        self.__entry.focus_set()
        # Save first status and link counts.
        self.__first_line = True
        self.__url_id = 0
        self.__path_id = 0

    def select_all(self, event):
        "Selects everything in the widget."
        event.widget.selection_range(0, tkinter.END)
        return 'break'

    def send_message(self, event):
        "Cuts everything from the entry and writes to file."
        text = self.__entry.get()
        self.__entry.delete(0, tkinter.END)
        self.__writer.write(text)

    def update(self):
        "Updates the directory monitor and displays new messages."
        self.after(1000, self.update)
        self.__monitor.update(self.__messages.update)
        # For each message, show those less than a day old.
        utcnow = datetime.datetime.utcnow()
        for message in self.__messages.get_messages():
            hours = (utcnow - message.time).total_seconds() / 3600
            if hours < SETTINGS.message_cutoff and self.allowed(message):
                self.display(message)

    def allowed(self, message):
        "Tests if the message should be displayed to the screen."
        # If there is no text, it is not allowed.
        if not message.text:
            return False
        # Extract some information about the text.
        dest, text, reverse = self.get_wisper(message.text)
        # If there is no destination, it is allowed.
        if dest is None:
            return True
        # Change the message's color.
        message.tag = 'mess' if reverse else 'high'
        # The message should be showed to the DEVELOPER and the source.
        if self.__username in {self.DEVELOPER, message.name}:
            # ... unless the source really wants to ignore himself.
            if reverse and self.__username != self.DEVELOPER:
                return False
            # Reformat the text and allow message.
            form = '![{}] {}' if reverse else '-> [{}] {}'
            message.text = form.format(dest, text)
            return True
        # If this is not a reversed whisper ...
        if not reverse:
            # It is only allowed for the destination.
            if dest == self.__username:
                message.text = text
                return True
            return False
        # Otherwise, it is not allowed to anyone else.
        if dest != self.__username:
            message.text = '![{}] {}'.format(dest, text)
            return True
        return False

    def get_wisper(self, message):
        "Tries to get information regarding message's wisper status."
        # Note to self: start wispers as "@[" and reversals as "!["
        # next time you implement this system for version 3 of Hermeneus.
        reverse, cleaned = False, message
        # If the messages starts with a '!', it should be cleaned.
        if message[0] == '!':
            reverse, cleaned = True, message[1:]
        # If the message starts with the proper prefix ...
        if cleaned[:2] == '@[':
            try:
                # Find the "end of name" marker.
                index = cleaned.index(']')
            except ValueError:
                pass    # Not wispered.
            else:
                # Return name, cleaned text, and reversal flag.
                dest = cleaned[2:index]
                text = cleaned[index+1:].strip()
                return dest, text, reverse
        # It was not wispered.
        return None, message, False

    def display(self, message):
        "Posts the message to the screen."
        # Enable changes and take first line into account.
        self.__text['state'] = tkinter.NORMAL
        if self.__first_line:
            self.__first_line = False
        else:
            self.__text.insert(tkinter.END, '\n')
        # Show the timestamp if requested.
        if SETTINGS.show_timestamp:
            diff = datetime.datetime.now() - datetime.datetime.utcnow()
            time = message.time + diff
            # Display string that has been corrected for local time zone.
            self.__text.insert(tkinter.END, time.strftime('%I:%M %p'), 'time')
            self.__text.insert(tkinter.END, ' ')
        # Show the name with the proper color (message.tag).
        self.__text.insert(tkinter.END, '[' + message.name + ']', message.tag)
        # Add text with formatting, scroll to botton, and disable changes.
        self.add_text_with_URLs(' ' + message.text)
        self.__text.see(tkinter.END)
        self.__text['state'] = tkinter.DISABLED

    def add_text_with_URLs(self, message):
        "Posts messages that may have URLs in them."
        url_list = self.find_urls(message)
        # Split on each URL, prefix, and create URL.
        for url in url_list:
            head, message = message.split(url, 1)
            self.add_text_with_PATHs(head)
            self.create_url(url)
        # Display whatever may be left.
        self.add_text_with_PATHs(message)

    def add_text_with_PATHs(self, message):
        "Posts messages that may have formatted paths in them."
        path_list = self.find_paths(message)
        # Split on each path markup and create path links.
        for markup, path, name in path_list:
            head, message = message.split(markup, 1)
            self.add_plain_text(head)
            self.create_path(path, name)
        # Finish displaying any trailing text.
        self.add_plain_text(message)

    def create_url(self, url):
        "Creates and shows a URL to the internal text widget."
        # Create a new, incremented URL tag for text.
        self.__url_id += 1
        tag = 'url' + str(self.__url_id)
        # Insert the text and bind a command to open a webbrowser.
        self.__text.insert(tkinter.END, url, ('dynamic_link', tag))
        self.__text.tag_bind(tag, '<1>', lambda event: webbrowser.open(url))

    def create_path(self, path, name):
        "Creates and shows a path to the internal text widget."
        # If the user is running Windows ...
        if hasattr(os, 'startfile'):
            # Create a new tag for the path.
            self.__path_id += 1
            tag = 'path' + str(self.__path_id)
            # Add the text and create an opening command.
            self.__text.insert(tkinter.END, name, ('dynamic_link', tag))
            self.__text.tag_bind(tag, '<1>', lambda event: os.startfile(path))
        else:
            # Insert a link that does not do anything.
            self.__text.insert(tkinter.END, name, 'static_link')

    def add_plain_text(self, message):
        "Confuses text if needed before adding text to display."
        if SETTINGS.message_confuser:
            message = confuse(message)
        self.__text.insert(tkinter.END, message)

    def find_paths(self, message):
        "Looks for and returns paths that may be in message."
        # Track found paths and current search positions.
        paths = []
        index_a = index_b = 0
        # While we are still searching the message's end ...
        while index_a > -1 and index_b > -1:
            index_a = message.find('<', index_b)
            # If the less than symbol has been found ...
            if index_a > -1:
                index_b = message.find('>', index_a)
                # If the greater than symbol has been found ...
                if index_b > -1:
                    path_markup = message[index_a:index_b+1]
                    # Add path to list if it exists.
                    self.test_and_add_path(path_markup, paths)
        return paths

    def test_and_add_path(self, markup, paths):
        "Tests in path is valid and adds to list if so."
        # Extract the path and create an "absolute" path.
        pulled = markup[1:-1].strip()
        program = os.path.dirname(sys.argv[0])
        absolute = os.path.join(program, pulled)
        # Turn the path into a normal path and test for existence.
        normal = os.path.normpath(absolute)
        if os.path.exists(normal):
            # Record the markup, normal path, and filename.
            base = os.path.basename(normal)
            file = os.path.splitext(base)[0]
            paths.append((markup, normal, file))

    def find_urls(self, message):
        "Looks for and returns URLs that may be in message."
        urls = []
        # Split text on whitespace.
        for text in message.split():
            result = urllib.parse.urlparse(text)
            # It is a URL if the protocol is correct and there is a location.
            if result.scheme in {'http', 'https', 'ftp'} and result.netloc:
                urls.append(text)
        # Return the list of found URLs.
        return urls

################################################################################

# To confuse the middle letters of a word, the following functions are used.

def confuse(text):
    "Confuses the text so that it is somewhat readable."
    # Collect all the words in a buffer after processing.
    buffer = []
    for data in words(text):
        if isinstance(data, str):
            buffer.append(data)             # Normal Text
        elif len(data) < 4:
            buffer.append(''.join(data))    # Short Text
        else:
            buffer.append(scramble(data))   # Confused Text
    # Return the processed string.
    return ''.join(buffer)

def words(string):
    "Parses words out of a string and yields data types back."
    # Prepare to process a string.
    data = str(string)
    if data:
        # Collect words and non-words and determine starting state.
        buffer = ''
        mode = 'A' <= data[0] <= 'Z' or 'a' <= data[0] <= 'z'
        for character in data:
            # Add characters to buffer until a mode change.
            if mode == ('A' <= character <= 'Z' or 'a' <= character <= 'z'):
                buffer += character
            else:
                # Yield a data type indicating what has been found.
                yield tuple(buffer) if mode else buffer
                buffer = character
                mode = not mode
        # Yield any remaining data in the buffer.
        yield tuple(buffer) if mode else buffer
    else:
        yield data

def scramble(data):
    "Mixes up a word so that it should still be readable."
    # Get the first letter and scramble the middle letters.
    array = [data[0]]
    array.extend(UUID.MIXER(data[1:-1], len(data) - 2))
    # Append the last letter and return the final string.
    array.append(data[-1])
    return ''.join(array)

################################################################################

# This code handles conversions for writing upside-down and right-side up again.

MAP_A = ' !"#%&\'()*+,-.0123456789<>?@ABCDEFGJKLMOPQRSTUVWYZ[]^\
_`abcdefghijklmnopqrtuvwxy{|}~\xa0¢£¤¦ª¯±³´¸º¾¿ÁÅÐÒ×ñòýÿƒ˜–„‡‹›€'

MAP_B = '\xa0i„‡¾£,)(¤t\'–³OlZEhS9LB6›‹¿PV8j€3ƒÐfý7W0@Òò5±ñAMÅ2\
][v¯´eq¢paJª4!Cÿ1wuºdb¸+n^m×Á}¦{˜ c&*|g_T.`ro%?yYGQxURKkF~-"#><D'

# This is the table for the translation.

TABLE = {32: 160,
         33: 105,
         34: 8222,
         35: 8225,
         37: 190,
         38: 163,
         39: 44,
         40: 41,
         41: 40,
         42: 164,
         43: 116,
         44: 39,
         45: 8211,
         46: 179,
         48: 79,
         49: 108,
         50: 90,
         51: 69,
         52: 104,
         53: 83,
         54: 57,
         55: 76,
         56: 66,
         57: 54,
         60: 8250,
         62: 8249,
         63: 191,
         64: 80,
         65: 86,
         66: 56,
         67: 106,
         68: 8364,
         69: 51,
         70: 402,
         71: 208,
         74: 102,
         75: 253,
         76: 55,
         77: 87,
         79: 48,
         80: 64,
         81: 210,
         82: 242,
         83: 53,
         84: 177,
         85: 241,
         86: 65,
         87: 77,
         89: 197,
         90: 50,
         91: 93,
         93: 91,
         94: 118,
         95: 175,
         96: 180,
         97: 101,
         98: 113,
         99: 162,
         100: 112,
         101: 97,
         102: 74,
         103: 170,
         104: 52,
         105: 33,
         106: 67,
         107: 255,
         108: 49,
         109: 119,
         110: 117,
         111: 186,
         112: 100,
         113: 98,
         114: 184,
         116: 43,
         117: 110,
         118: 94,
         119: 109,
         120: 215,
         121: 193,
         123: 125,
         124: 166,
         125: 123,
         126: 732,
         160: 32,
         162: 99,
         163: 38,
         164: 42,
         166: 124,
         170: 103,
         175: 95,
         177: 84,
         179: 46,
         180: 96,
         184: 114,
         186: 111,
         190: 37,
         191: 63,
         193: 121,
         197: 89,
         208: 71,
         210: 81,
         215: 120,
         241: 85,
         242: 82,
         253: 75,
         255: 107,
         402: 70,
         732: 126,
         8211: 45,
         8222: 34,
         8225: 35,
         8249: 62,
         8250: 60,
         8364: 68}

################################################################################

# Execute the main function if this code is used directly.

if __name__ == '__main__':
    main()
