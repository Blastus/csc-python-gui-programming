#! /usr/bin/env python3

"""Module for mapping out directory sizes.

Creating a SizeTree instance will automatically discover the directory size.
The directory's structure will be accessible through the tree-like structure."""

################################################################################

__author__ = 'Stephen "Zero" Chappell <Noctis.Skytower@gmail.com>'
__date__ = '21 February 2011'
__version__ = '$Revision: 1 $'

################################################################################

import os

################################################################################

class SizeTree:

    "Create a tree structure outlining a directory's size."

    __slots__ = 'name path children file_size total_size total_nodes'.split()

    def __init__(self, path, callback=None):
        "Initialize the SizeTree object and search the path while updating."
        # Validate the search's current progress.
        if callback is not None:
            callback()
        head, tail = os.path.split(path)
        # Create attributes for this instance.
        self.name = tail or head
        self.path = path
        self.children = []
        self.file_size = 0
        self.total_size = 0
        self.total_nodes = 0
        # Try searching this directory.
        try:
            dir_list = os.listdir(path)
        except OSError:
            pass
        else:
            # Examine each object in this directory.
            for name in dir_list:
                path_name = os.path.join(path, name)
                if os.path.isdir(path_name):
                    # Create child nodes for subdirectories.
                    size_tree = SizeTree(path_name, callback)
                    self.children.append(size_tree)
                    self.total_size += size_tree.total_size
                    self.total_nodes += size_tree.total_nodes + 1
                elif os.path.isfile(path_name):
                    # Try getting the size of files.
                    try:
                        self.file_size += os.path.getsize(path_name)
                    except OSError:
                        pass
            # Add in the total file size to the total size.
            self.total_size += self.file_size

    def pop_child(self, name):
        "Return a named child or None if not found."
        for index, child in enumerate(self.children):
            if child.name == name:
                return self.children.pop(index)

    ########################################################################

    def __str__(self):
        "Return a representation of the tree formed by this object."
        lines = [self.path]
        self.__walk(lines, self.children, '')
        return '\n'.join(lines)

    @classmethod
    def __walk(cls, lines, children, prefix):
        "Generate lines based on children and keep track of prefix."
        dir_prefix, walk_prefix = prefix + '+---', prefix + '|   '
        for pos, neg, child in cls.__enumerate(children):
            if neg == -1:
                dir_prefix, walk_prefix = prefix + '\\---', prefix + '    '
            lines.append(dir_prefix + child.name)
            cls.__walk(lines, child.children, walk_prefix)

    @staticmethod
    def __enumerate(sequence):
        "Generate positive and negative indices for sequence."
        length = len(sequence)
        for count, value in enumerate(sequence):
            yield count, count - length, value
