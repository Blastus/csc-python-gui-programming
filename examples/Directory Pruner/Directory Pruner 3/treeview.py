#! /usr/bin/env python3

"""Module for manipulating nodes in a treeview.

The Node class provides a high-level interface to work with treeview nodes.
When creating a Node instance, a Treeview instance must should be wrapped."""

################################################################################

__author__ = 'Stephen "Zero" Chappell <Noctis.Skytower@gmail.com>'
__date__ = '21 February 2011'
__version__ = '$Revision: 1 $'

################################################################################

import sys
import tkinter
from .bytesize import convert, parse, abbr
from .view import TrimDir

################################################################################

class Node:

    "Interface to allow easier interaction with Treeview instance."

    @classmethod
    def current(cls, tree):
        "Take a tree view and return its currently selected node."
        node = tree.selection()
        return cls(tree, node[0] if node else node)

    ########################################################################

    # Standard Treeview Operations

    __slots__ = '__tree', '__node'

    def __init__(self, tree, node=''):
        "Initialize the Node object (root if node not given)."
        self.__tree = tree
        self.__node = node

    def __str__(self):
        "Return a string representation of this node."
        return '''\
NODE: {!r}
  Name: {}
  Total Size: {}
  File Size: {}
  Path {}\
'''.format(self.__node, self.name, self.total_size, self.file_size, self.path)

    def insert(self, position, text):
        "Insert a new node with text at position in current node."
        node = self.__tree.insert(self.__node, position, text=text)
        # PATCH: Store extra data about node.
        if TrimDir.SIZE:
            self.__tree.nodes[node] = dict()
        return Node(self.__tree, node)

    def append(self, text):
        "Add a new node with text to the end of this node."
        return self.insert(tkinter.END, text)

    def move(self, parent, index):
        "Insert this node under parent at index."
        self.__tree.move(self.__node, parent, index)

    def reattach(self, parent='', index=tkinter.END):
        "Attach node to parent at index (defaults to end of root)."
        self.move(parent, index)

    def detach(self):
        "Unlink this node from its parent but do not delete."
        self.__tree.detach(self.__node)

    def delete(self, get_parent=False, from_tree=True): # Internal Last Flag
        "Delete this node (optionally, return parent)."
        if self.__tree.exists(self.__node):
            parent = self.parent if get_parent else None
            # PATCH: Remove extra data about node.
            if TrimDir.SIZE:
                for child in self.children:
                    child.delete(from_tree=False)
                del self.__tree.nodes[self.__node]
            if from_tree:
                self.__tree.delete(self.__node)
            #=====================================
            return parent
        if get_parent:
            raise ValueError('Cannot return parent!')

    ########################################################################

    # Standard Treeview Properties

    @property
    def root(self):
        "Return if this is the root node."
        return self.__node == ''

    @property
    def parent(self):
        "Return the parent of this node."
        return Node(self.__tree, self.__tree.parent(self.__node))

    @property
    def level(self):
        "Return number of levels this node is under root."
        count, node = 0, self
        while not node.root:
            node = node.parent
            count += 1
        return count

    @property
    def position(self):
        "Return the position of this node in its parent."
        return self.__tree.index(self.__node)

    @property
    def expanded(self):
        "Return whether or not the node is current open."
        value = self.__tree.item(self.__node, 'open')
        return bool(value) and value.string == 'true'

    @property
    def children(self):
        "Yield back each child of this node."
        for child in self.__tree.get_children(self.__node):
            yield Node(self.__tree, child)

    ########################################################################

    # Custom Treeview Properties
    # (specific for application)

    @property
    def name(self):
        "Return the name of this node (tree column)."
        return self.__tree.item(self.__node, 'text')

    # PATCH: Custom Size
    if TrimDir.SIZE:
        # Shortened Byte Size
        def __get_total_size(self):
            return self.__tree.nodes[self.__node][TrimDir.CLMS[0]]

        def __set_total_size(self, value):
            self.__tree.nodes[self.__node][TrimDir.CLMS[0]] = value
            self.__tree.set(self.__node, TrimDir.CLMS[0], abbr(value))

        def __get_file_size(self):
            return self.__tree.nodes[self.__node][TrimDir.CLMS[1]]

        def __set_file_size(self, value):
            self.__tree.nodes[self.__node][TrimDir.CLMS[1]] = value
            self.__tree.set(self.__node, TrimDir.CLMS[1], abbr(value))
    else:
        # Complete Byte Size
        def __get_total_size(self):
            return parse(self.__tree.set(self.__node, TrimDir.CLMS[0]))

        def __set_total_size(self, value):
            self.__tree.set(self.__node, TrimDir.CLMS[0], convert(value))

        def __get_file_size(self):
            return parse(self.__tree.set(self.__node, TrimDir.CLMS[1]))

        def __set_file_size(self, value):
            self.__tree.set(self.__node, TrimDir.CLMS[1], convert(value))
    #=========================================================================

    def __get_path(self):
        return self.__tree.set(self.__node, TrimDir.CLMS[2])

    def __set_path(self, value):
        self.__tree.set(self.__node, TrimDir.CLMS[2], value)

    total_size = property(__get_total_size, __set_total_size,
                          doc="Total size of this node (first column)")

    file_size = property(__get_file_size, __set_file_size,
                         doc="File size of this node (second column)")

    path = property(__get_path, __set_path,
                    doc="Path of this node (third column)")

    ########################################################################

    # Custom Treeview Sort Order
    # (specific for application)

    def sort_name(self):
        "If the node is open, sort its children by name."
        self.__sort(lambda child: child.name)

    def sort_total_size(self):
        "If the node is open, sort its children by total size."
        self.__sort(lambda child: child.total_size)

    def sort_file_size(self):
        "If the node is open, sort its children by file size."
        self.__sort(lambda child: child.file_size)

    def sort_path(self):
        "If the node is open, sort its children by path."
        self.__sort(lambda child: child.path)

    def __sort(self, key):
        "Sort an expanded node's children by the given key."
        if self.expanded:
            nodes = list(self.children)
            order = sorted(nodes, key=key)
            if order == nodes:
                order = reversed(order)
            for child in order:
                self.__tree.move(child.__node, self.__node, tkinter.END)
