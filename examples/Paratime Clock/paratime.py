#! /usr/bin/env python3
"""\
Module for paratessares time conversions.

This module provides several functions that
covert earth seconds into paratessares time."""

################################################################################

__version__ = "$Revision: 7 $"
__date__ = "10 November 2009"
__author__ = "Stephen Chappell <Noctis.Skytower@gmail.com>"
__credits__ = """\
S. Schaub, for teaching me about interpreted languages.
D. Wooster, for teaching me about simulations and C#.
B. Gates, for allowing timers to be included with C#."""

################################################################################

import time as _time
import _thread
import sys as _sys

################################################################################

EPOCH_DELTA = 946684800
MION_IN_DAY = 1000000
MILU_IN_DAY = 1000

SECOND_IN_DAY = 86400
DAY_IN_WEEK = 7
WEEK_IN_MONTH = 4
MONTH_IN_SEASON = 3
SEASON_IN_YEAR = 4

SECOND_IN_WEEK = SECOND_IN_DAY * DAY_IN_WEEK
SECOND_IN_MONTH = SECOND_IN_WEEK * WEEK_IN_MONTH
SECOND_IN_SEASON = SECOND_IN_MONTH * MONTH_IN_SEASON
SECOND_IN_YEAR = SECOND_IN_SEASON * SEASON_IN_YEAR

################################################################################

def seconds():
    "Return seconds since the epoch."
    return _time.time() - EPOCH_DELTA

def mion(seconds):
    "Convert from seconds to mion."
    x = seconds % SECOND_IN_DAY * MION_IN_DAY / SECOND_IN_DAY % MILU_IN_DAY
    return int(x)

def milu(seconds):
    "Convert from seconds to milu."
    x = seconds % SECOND_IN_DAY * MILU_IN_DAY / SECOND_IN_DAY
    return int(x)

def day(seconds):
    "Convert from seconds to days."
    x = seconds / SECOND_IN_DAY % DAY_IN_WEEK
    return int(x)

def week(seconds):
    "Convert from seconds to weeks."
    x = seconds / SECOND_IN_WEEK % WEEK_IN_MONTH
    return int(x)

def month(seconds):
    "Convert from seconds to months."
    x = seconds / SECOND_IN_MONTH % MONTH_IN_SEASON
    return int(x)

def season(seconds):
    "Convert from seconds to seasons."
    x = seconds / SECOND_IN_SEASON % SEASON_IN_YEAR
    return int(x)

def year(seconds):
    "Convert from seconds to years."
    x = seconds / SECOND_IN_YEAR
    return int(x)
    
################################################################################

UNITS = year, season, month, week, day, milu, mion

def text(seconds, spec='{0}.{1}.{2}.{3}.{4}.{5:03}.{6:03}', unit=UNITS):
    "Convert from seconds to text."
    return spec.format(*[func(seconds) for func in unit])

################################################################################

class Mion_Timer:

    "Mion_Timer(function, *args, **kwargs) -> Mion_Timer"

    def __init__(self, function, *args, **kwargs):
        "Initialize the Mion_Timer object."
        self.__function = function
        self.__args = args
        self.__kwargs = kwargs
        self.__thread = False
        self.__lock = _thread.allocate_lock()

    def start(self):
        "Start the Mion_Timer object."
        with self.__lock:
            self.__active = True
            if not self.__thread:
                self.__thread = True
                _thread.start_new_thread(self.__run, ())

    def stop(self):
        "Stop the Mion_Timer object."
        with self.__lock:
            self.__active = False

    def __run(self):
        "Private class method."
        start = _time.clock()
        timer = 0
        while True:
            timer += 1
            sleep = start + timer * 0.0864 - _time.clock()
            assert sleep >= 0, 'Function Was Too Slow'
            _time.sleep(sleep)
            with self.__lock:
                if not self.__active:
                    self.__thread = False
                    break
            self.__function(*self.__args, **self.__kwargs)

################################################################################

class Quantum_Timer:

    "Quantum_Timer(function, *args, **kwargs) -> Quantum_Timer"

    def __init__(self, function, *args, **kwargs):
        "Initialize the Quantum_Timer object."
        self.__function = function
        self.__args = args
        self.__kwargs = kwargs
        self.__thread = False
        self.__lock = _thread.allocate_lock()

    def start(self):
        "Start the Quantum_Timer object."
        with self.__lock:
            self.__active = True
            if not self.__thread:
                self.__thread = True
                _thread.start_new_thread(self.__run, ())

    def stop(self):
        "Stop the Quantum_Timer object."
        with self.__lock:
            self.__active = False

    def __run(self):
        "Private class method."
        while True:
            time = _time.clock()
            plus = time + 0.0864
            over = plus % 0.0864
            diff = plus - time - over
            _time.sleep(diff)
            with self.__lock:
                if not self.__active:
                    self.__thread = False
                    break
            self.__function(*self.__args, **self.__kwargs)

################################################################################

if __name__ == '__main__':
    _sys.stdout.write('Content-Type: text/plain\n\n')
    _sys.stdout.write(open(_sys.argv[0]).read())
