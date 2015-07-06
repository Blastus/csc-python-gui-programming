#! /usr/bin/env python3

"""Module for scheduling execution on single thread.

This is the core of the GUI's ability to run in a multi-threaded environment.
Calling run on a class instance ensures execution on the creating thread."""

################################################################################

__author__ = 'Stephen "Zero" Chappell <Noctis.Skytower@gmail.com>'
__date__ = '21 February 2011'
__version__ = '$Revision: 1 $'

################################################################################

import _thread
import functools
import queue
import warnings

################################################################################

class Affinity:

    "Predecessor to AffinityLoop that might not return results."

    __slots__ = '__action', '__thread'

    def __init__(self):
        "Initialize Affinity with job queue and thread identity."
        self.__action = queue.Queue()
        self.__thread = _thread.get_ident()

    def run(self, func, *args, **keywords):
        "Try to run function with arguments on the creating thread."
        self.__action.put_nowait(functools.partial(func, *args, **keywords))
        if _thread.get_ident() == self.__thread:
            problem = False
            while not self.__action.empty():
                delegate = self.__action.get_nowait()
                try:
                    data = delegate()
                except Exception as error:
                    problem = error
            if problem:
                raise problem
            return data
        warnings.warn('Affinity did not return!')

################################################################################

class AffinityLoop:

    "Restricts code execution to thread that instance was created on."

    __slots__ = '__action', '__thread'

    def __init__(self):
        "Initialize AffinityLoop with job queue and thread identity."
        self.__action = queue.Queue()
        self.__thread = _thread.get_ident()

    def run(self, func, *args, **keywords):
        "Run function on creating thread and return result."
        if _thread.get_ident() == self.__thread:
            self.__run_jobs()
            return func(*args, **keywords)
        else:
            job = self.__Job(func, args, keywords)
            self.__action.put_nowait(job)
            return job.result

    def __run_jobs(self):
        "Run all pending jobs currently in the job queue."
        while not self.__action.empty():
            job = self.__action.get_nowait()
            job.execute()

    ########################################################################

    class __Job:

        "Store information to run a job at a later time."

        __slots__ = ('__func', '__args', '__keywords',
                     '__error', '__mutex', '__value')

        def __init__(self, func, args, keywords):
            "Initialize the job's info and ready for execution."
            self.__func = func
            self.__args = args
            self.__keywords = keywords
            self.__error = False
            self.__mutex = _thread.allocate_lock()
            self.__mutex.acquire()

        def execute(self):
            "Run the job, store any error, and return to sender."
            try:
                self.__value = self.__func(*self.__args, **self.__keywords)
            except Exception as error:
                self.__error = True
                self.__value = error
            self.__mutex.release()

        @property
        def result(self):
            "Return execution result or raise an error."
            self.__mutex.acquire()
            if self.__error:
                raise self.__value
            return self.__value
