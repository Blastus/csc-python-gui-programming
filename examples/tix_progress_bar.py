'''Module for displaying progress bars.

This module provides access to a class that implements an
easy to use progress bar that is built from the Tix library.'''

################################################################################

__version__ = '$Revision: 0 $'
__date__ = 'February 11, 2007'
__author__ = 'Stephen "Zero" Chappell <my.bios@gmail.com>'
__credits__ = '''\
S. Schaub, for introducing me to programming.
F. Lundh, for providing on-line reference material.
J. Grayson, for writing a book on GUI programming.'''

################################################################################

import sys as _sys
import tkinter.tix as _Tix

################################################################################

class Progress_Bar:

    'Progress_Bar() -> Progress Bar'

    def __init__(self):
        'Initialize the Progress Bar object.'
        self.__tk = _Tix.Tk()
        self.__tk.resizable(False, False)
        self.__tk.title('Progress Bar')
        self.__meter = _Tix.Meter(self.__tk)
        self.__meter.pack()

    def show(self):
        'Show the Progress Bar on the screen.'
        self.__tk.deiconify()

    def hide(self):
        'Hide the Progress Bar from the screen.'
        self.__tk.withdraw()

    def update(self, value):
        'Update the data shown on the Progress Bar.'
        self.__meter.configure(value=value)
        self.__meter.update()

################################################################################

if __name__ == '__main__':
    _sys.stdout.write('Content-Type: text/plain\n\n')
    _sys.stdout.write(open(_sys.argv[0]).read())
