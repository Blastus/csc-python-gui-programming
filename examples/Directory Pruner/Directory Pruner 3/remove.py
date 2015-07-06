#! /usr/bin/env python3

"""Module for removing files and directories.

These functions help in removing directories and files by various methods.
The core of the context menu is implemented by the provided capabilities."""

################################################################################

__author__ = 'Stephen "Zero" Chappell <Noctis.Skytower@gmail.com>'
__date__ = '21 February 2011'
__version__ = '$Revision: 1 $'

################################################################################

import os

################################################################################

def directory_files(path, remove_directory=False, remove_path=False):
    "Remove directory at path, respecting the flags."
    for root, dirs, files in os.walk(path, False):
        # Ignore path if remove_path is false.
        if remove_path or root != path:
            for name in files:
                filename = os.path.join(root, name)
                try:
                    os.remove(filename)
                except OSError:
                    pass
            # Ignore directory if remove_directory is false.
            if remove_directory:
                try:
                    os.rmdir(root)
                except OSError:
                    pass

def files(path):
    "Remove files in path and get remaining space."
    total_size = 0
    # Find all files in directory of path.
    for name in os.listdir(path):
        pathname = os.path.join(path, name)
        if os.path.isfile(pathname):
            # Try to remove any file that may have been found.
            try:
                os.remove(pathname)
            except OSError:
                # If there was an error, try to get the filesize.
                try:
                    total_size += os.path.getsize(pathname)
                except OSError:
                    pass
    # Return best guess of space still occupied.
    return total_size

def empty_directories(path, remove_root=False, recursive=True):
    "Remove all empty directories while respecting the flags."
    if recursive:
        for name in os.listdir(path):
            try:
                empty_directories(os.path.join(path, name), True)
            except OSError:
                pass
    if remove_root:
        os.rmdir(path)

def empty_files(path, recursive=True):
    "Remove all files that are empty of any contents."
    for root, dirs, files in os.walk(path):
        if not recursive:
            del dirs[:]
        for name in files:
            filename = os.path.join(root, name)
            try:
                if not os.path.getsize(filename):
                    os.remove(filename)
            except OSError:
                pass
