#! /usr/bin/env python3

"""Module for animating and displaying error messages.

The indicate_error function is the only available function in this module.
Calling it with the appropriate arguments should display an error for you."""

################################################################################

__author__ = 'Stephen "Zero" Chappell <Noctis.Skytower@gmail.com>'
__date__ = '21 February 2011'
__version__ = '$Revision: 1 $'

################################################################################

import _tkinter
import math

################################################################################

def indicate_error(root, alternative, callback, force=False):
    "Prepare to shake the application's root window."
    if force:
        _tkinter.setbusywaitinterval(20)
    elif _tkinter.getbusywaitinterval() != 20:
        # Show error message if not running at 50 FPS.
        alternative.show()
        return callback()
    root.after_idle(_shake, root, callback)

def _shake(root, callback, frame=0):
    "Animate each step of shaking the root window."
    frame += 1
    # Get the window's location and update the X position.
    x, y = map(int, root.geometry().split('+')[1:])
    x += round(math.sin(math.pi * frame / 2.5) * \
               math.sin(math.pi * frame / 50) * 5)
    root.geometry('+{}+{}'.format(x, y))
    if frame < 50:
        # Schedule next step in the animation.
        root.after(20, _shake, root, callback, frame)
    else:
        # Enable operations after one second.
        callback()
