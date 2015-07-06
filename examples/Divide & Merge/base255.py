'''Module for string conversion.

This module provides two functions that allow
strings to be encoded and decoded in base 255.'''

__version__ = 1.0

################################################################################

def encode(string, divide=1024):
    'Encode a string to base 255.'
    def encode(string):
        if isinstance(string, str):
            string = string.encode('ascii')
        elif not isinstance(string, bytes):
            raise TypeError('string must be of type bytes')
        number = 0
        for character in string:
            number *= 257
            number += character + 1
        string = bytearray()
        while number:
            string.insert(0, number % 254 + 2)
            number //= 254
        return string
    return b'\1'.join([encode(string[index:index+divide]) for index in range(0, len(string), divide)])

def decode(string):
    'Decode a string from base 255.'
    def decode(string):
        if isinstance(string, str):
            string = string.encode('ascii')
        elif not isinstance(string, bytes):
            raise TypeError('string must be of type bytes')
        number = 0
        for character in string:
            number *= 254
            number += character - 2
        string = bytearray()
        while number:
            string.insert(0, number % 257 - 1)
            number //= 257
        return string
    return b''.join([decode(string) for string in string.split(b'\1')])

################################################################################

if __name__ == '__main__':
    import sys
    sys.stdout.write('Content-Type: text/plain\n\n' + open(sys.argv[0]).read())
