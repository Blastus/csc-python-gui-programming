#! /usr/bin/env python3

"""Module for starting threads that have their errors logged.

The start_thread function is the only procedure for use in this module.
When threads are started, errors will be automatically written to a file."""

################################################################################

__author__ = 'Stephen "Zero" Chappell <Noctis.Skytower@gmail.com>'
__date__ = '21 February 2011'
__version__ = '$Revision: 1 $'

################################################################################

import _thread
import logging
import os
import sys
import traceback

################################################################################

def start_thread(function, *args, **kwargs):
    "Start a new thread and wrap with error catching."
    _thread.start_new_thread(_bootstrap, (function, args, kwargs))

def _bootstrap(function, args, kwargs):
    "Run function with arguments and log any errors."
    try:
        function(*args, **kwargs)
    except Exception:
        basename = os.path.basename(sys.argv[0])
        filename = os.path.splitext(basename)[0] + '.log'
        logging.basicConfig(filename=filename)
        logging.error(traceback.format_exc())
