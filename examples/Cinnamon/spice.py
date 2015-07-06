#! /usr/bin/env python3
'''Module that implements SPICE.

This module provides access to a standardized implementation
of SPICE (Stephen's Power-Inspired, Computerized Encryption).'''

################################################################################

__version__ = '$Revision: 0 $'
__date__ = 'February 11, 2007'
__author__ = 'Stephen "Zero" Chappell <my.bios@gmail.com>'
__credits__ = '''\
T. Parker, for testing code that led to this module.
A. Baddeley, for contributing to the random module.
R. Hettinger, for adding support for two core generators.'''

################################################################################

import random as _random
import sys as _sys

################################################################################

def major():
    'Create a new Major Key.'
    return  bytes(_random.sample(range(256), 256))

def minor():
    'Create a new Minor Key.'
    sample = _random.sample(tuple(range(4)) * 64, 256)
    return bytes((sample[index * 4] << 6) + (sample[index * 4 + 1] << 4) + (sample[index * 4 + 2] << 2) + sample[index * 4 + 3] for index in range(64))

def encode(source, destination, major_key, minor_key):
    'Encode from source to destination via Major and Minor Keys.'
    _check_major(major_key)
    _check_minor(minor_key)
    map_1 = tuple(major_key)
    map_2 = _setup_minor(minor_key)
    character = source.read(1)
    while character:
        byte = map_1[character[0]]
        for shift in range(6, -2, -2):
            destination.write(bytes([map_2[(byte >> shift) & 3][_random.randrange(64)]]))
        character = source.read(1)
    destination.flush()
    destination.close()
    source.close()

def decode(source, destination, major_key, minor_key):
    'Decode from source to destination via Major and Minor Keys.'
    _check_major(major_key)
    _check_minor(minor_key)
    map_1 = [(byte >> shift) & 3 for byte in minor_key for shift in range(6, -2, -2)]
    map_2 = _setup_major(major_key)
    double_word = source.read(4)
    while double_word:
        destination.write(map_2[(map_1[double_word[0]] << 6) + (map_1[double_word[1]] << 4) + (map_1[double_word[2]] << 2) + map_1[double_word[3]]])
        double_word = source.read(4)
    destination.flush()
    destination.close()
    source.close()

################################################################################

def _check_major(major_key):
    'Private module function.'
    assert isinstance(major_key, bytes) and len(major_key) == 256
    for character in bytes(range(256)):
        assert character in major_key

def _check_minor(minor_key):
    'Private module function.'
    assert isinstance(minor_key, bytes) and len(minor_key) == 64
    indexs = [(byte >> shift) & 3 for byte in minor_key for shift in range(6, -2, -2)]
    for index in range(4):
        assert indexs.count(index) == 64

def _setup_minor(minor_key):
    'Private module function.'
    map_2 = [bytearray(), bytearray(), bytearray(), bytearray()]
    for byte, index in enumerate((byte >> shift) & 3 for byte in minor_key for shift in range(6, -2, -2)):
        map_2[index].append(byte)
    return map_2

def _setup_major(major_key):
    'Private module function.'
    map_2 = [None] * 256
    for byte, index in enumerate(major_key):
        map_2[index] = bytes([byte])
    return map_2

################################################################################

if __name__ == '__main__':
    _sys.stdout.write('Content-Type: text/plain\n\n')
    _sys.stdout.write(open(_sys.argv[0]).read())
