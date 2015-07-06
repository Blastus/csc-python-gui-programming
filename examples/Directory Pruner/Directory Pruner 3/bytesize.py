#! /usr/bin/env python3

"""Module for converting byte to strings and vice versa.

Various function are provided for changing byte sizes into English words.
If the conversion is exact, the string may also be converted into a number."""

################################################################################

__author__ = 'Stephen "Zero" Chappell <Noctis.Skytower@gmail.com>'
__date__ = '21 February 2011'
__version__ = '$Revision: 1 $'

################################################################################

import math

################################################################################

# Provide a way of converting byte sizes into strings.

def convert(number):
    "Convert bytes into human-readable representation."
    if not number:
        return '0 Bytes'
    if not 0 < number < 1 << 110:
        raise ValueError('Number out of range!')
    ordered = reversed(tuple(format_bytes(partition_number(number, 1 << 10))))
    cleaned = ', '.join(item for item in ordered if item[0] != '0')
    return cleaned

def partition_number(number, base):
    "Continually divide number by base until zero."
    div, mod = divmod(number, base)
    yield mod
    while div:
        div, mod = divmod(div, base)
        yield mod

def format_bytes(parts):
    "Format partitioned bytes into human-readable strings."
    for power, number in enumerate(parts):
        yield '{} {}'.format(number, format_suffix(power, number))

def format_suffix(power, number):
    "Compute the suffix for a certain power of bytes."
    return (PREFIX[power] + 'byte').capitalize() + ('s' if number != 1 else '')

PREFIX = ' kilo mega giga tera peta exa zetta yotta bronto geop'.split(' ')

################################################################################

# Define additional operations for the TreeviewNode class.

def parse(string):
    "Convert human-readable string back into bytes."
    total = 0
    for part in string.split(', '):
        number, unit = part.split(' ')
        s = number != '1' and 's' or ''
        for power, prefix in enumerate(PREFIX):
            if unit == (prefix + 'byte' + s).capitalize():
                break
        else:
            raise ValueError('{!r} not found!'.format(unit))
        total += int(number) * 1 << 10 * power
    return total

def abbr(number):
    "Convert bytes into abbreviated representation."
    # Check value of number before processing.
    if not number:
        return '0 Bytes'
    if not 0 < number < (1 << 100) * 1000:
        raise ValueError('Number out of range!')
    # Calculate range of number and correct value.
    level = int(math.log(number) / math.log(1 << 10))
    value = number / (1 << 10 * level)
    # Move to the next level if number is high enough.
    if value < 1000:
        precision = 4
    else:
        precision = 3
        level += 1
        value /= 1 << 10
    # Format the number before returning to caller.
    if level:
        result = '{:.{}}'.format(value, precision)
        return '{} {}'.format(result, format_suffix(level, result == '1.0'))
    return '{} {}'.format(int(value), format_suffix(level, value))
