#! /usr/bin/env python3

"""Module executing same method on tuple items.

The Apply class can store items and run the same method on all objects.
Results are returned as a tuple, and exeception are raised when needed."""

################################################################################

__author__ = 'Stephen "Zero" Chappell <Noctis.Skytower@gmail.com>'
__date__ = '21 February 2011'
__version__ = '$Revision: 1 $'

################################################################################

class Apply(tuple):

    "Create a container that can run a method from its contents."

    def __getattr__(self, name):
        "Get a virtual method to map and apply to the contents."
        return self.__Method(self, name)

    ########################################################################

    class __Method:

        "Provide a virtual method that can be called on the array."

        def __init__(self, array, name):
            "Initialize the method with array and method name."
            self.__array = array
            self.__name = name

        def __call__(self, *args, **kwargs):
            "Execute method on contents with provided arguments."
            name, error, buffer = self.__name, False, []
            for item in self.__array:
                attr = getattr(item, name)
                try:
                    data = attr(*args, **kwargs)
                except Exception as problem:
                    error = problem
                else:
                    if not error:
                        buffer.append(data)
            if error:
                raise error
            return tuple(buffer)
