#! /usr/bin/env python3

"""Module containing main GUI class of application.

The overly large TrimDir class is the main interface to this program.
To use Directory Pruner in other programs, create and use TrimDir objects."""

################################################################################

__author__ = 'Stephen "Zero" Chappell <Noctis.Skytower@gmail.com>'
__date__ = '21 February 2011'
__version__ = '$Revision: 1 $'

################################################################################

import os
import tkinter
from . import animator
from . import discover
from . import remove
from . import runmethod
from . import threadlog
from . import widgets

################################################################################

class TrimDir(widgets.Frame):

    "Widget for examining size of directory with optional deletion."

    WARN = True # Should warnings be made for permanent operations?
    MENU = True # Should the (destructive) context menu be enabled?
    SIZE = True # Should directory sizes be patched for less words?

    # Give names to columns.
    CLMS = 'total_size', 'file_size', 'path'
    TREE = '#0'

    ########################################################################

    # Initialize the TrimDir object.

    __slots__ = ('__tk', '__label', '__path', '__run', '__cancel',
                 '__progress', '__tree', '__scroll_1', '__scroll_2',
                 '__grip', '__menu', '__dialog', '__error', '__warn')

    def __init__(self, master=None, **kw):
        "Initialize the TrimDir instance and configure for operation."
        super().__init__(master, **kw)
        # Initialize and configure this frame widget.
        self.capture_root()
        self.create_widgets()
        self.create_supports()
        self.create_bindings()
        self.configure_grid()
        self.configure_tree()
        self.configure_menu()
        # Set focus to path entry.
        self.__path.focus_set()

    def capture_root(self):
        "Capture the root (Tk instance) of this application."
        widget = self.master
        while not isinstance(widget, widgets.Tk):
            widget = widget.master
        self.__tk = widget

    def create_widgets(self):
        "Create all the widgets that will be placed in this frame."
        self.__label = widgets.Button(self, text='Path:', command=self.choose)
        self.__path = widgets.Entry(self, cursor='xterm')
        self.__run = widgets.Button(self, text='Search', command=self.search)
        self.__cancel = widgets.Button(self, text='Cancel',
                                       command=self.stop_search)
        self.__progress = widgets.Progressbar(self, orient=tkinter.HORIZONTAL)
        self.__tree = widgets.Treeview(self, columns=self.CLMS,
                                       selectmode=tkinter.BROWSE)
        self.__scroll_1 = widgets.Scrollbar(self, orient=tkinter.VERTICAL,
                                            command=self.__tree.yview)
        self.__scroll_2 = widgets.Scrollbar(self, orient=tkinter.HORIZONTAL,
                                            command=self.__tree.xview)
        self.__grip = widgets.Sizegrip(self)

    def create_supports(self):
        "Create all GUI elements not placed directly in this frame."
        self.__menu = widgets.Menu(self)
        self.create_directory_browser()
        self.create_error_message()
        self.create_warning_message()

    def create_directory_browser(self):
        "Find root of file system and create directory browser."
        head, tail = os.getcwd(), True
        while tail:
            head, tail = os.path.split(head)
        self.__dialog = widgets.Directory(self, initialdir=head)

    def create_error_message(self):
        "Create error message when trying to search bad path."
        options = {'title': 'Path Error',
                   'icon': tkinter.messagebox.ERROR,
                   'type': tkinter.messagebox.OK,
                   'message': 'Directory does not exist.'}
        self.__error = widgets.Message(self, **options)

    def create_warning_message(self):
        "Create warning message for permanent operations."
        options = {'title': 'Important Warning',
                   'icon': tkinter.messagebox.QUESTION,
                   'type': tkinter.messagebox.YESNO,
                   'message': '''\
You cannot undo these operations.
Are you sure you want to do this?'''}
        self.__warn = widgets.Message(self, **options)

    def create_bindings(self):
        "Bind the widgets to any events they will need to handle."
        self.__label.bind('<Return>', self.choose)
        self.__path.bind('<Control-Key-a>', self.select_all)
        self.__path.bind('<Control-Key-/>', lambda event: 'break')
        self.__path.bind('<Return>', self.search)
        self.__run.bind('<Return>', self.search)
        self.__cancel.bind('<Return>', self.stop_search)
        self.bind_right_click(self.__tree, self.open_menu)

    @staticmethod
    def select_all(event):
        "Select all of the contents in this Entry widget."
        event.widget.selection_range(0, tkinter.END)
        return 'break'

    def bind_right_click(self, widget, action):
        "Bind action to widget while considering Apple computers."
        if self.__tk.tk.call('tk', 'windowingsystem') == 'aqua':
            widget.bind('<2>', action)
            widget.bind('<Control-1>', action)
        else:
            widget.bind('<3>', action)

    def configure_grid(self):
        "Place all widgets on the grid in their respective locations."
        self.__label.grid(row=0, column=0)
        self.__path.grid(row=0, column=1, sticky=tkinter.EW)
        self.__run.grid(row=0, column=2, columnspan=2)
        self.__run.grid_remove()
        self.__cancel.grid(row=0, column=2, columnspan=2)
        self.__cancel.grid_remove()
        self.__run.grid()
        self.__progress.grid(row=1, column=0, columnspan=4, sticky=tkinter.EW)
        self.__tree.grid(row=2, column=0, columnspan=3, sticky=tkinter.NSEW)
        self.__scroll_1.grid(row=2, column=3, sticky=tkinter.NS)
        self.__scroll_2.grid(row=3, column=0, columnspan=3, sticky=tkinter.EW)
        self.__grip.grid(row=3, column=3, sticky=tkinter.SE)
        # Configure the grid to automatically resize internal widgets.
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(1, weight=1)

    def configure_tree(self):
        "Configure the Treeview widget."
        # Setup the headings.
        self.__tree.heading(self.TREE, text=' Name', anchor=tkinter.W,
                            command=self.sort_name)
        self.__tree.heading(self.CLMS[0], text=' Total Size', anchor=tkinter.W,
                            command=self.sort_total_size)
        self.__tree.heading(self.CLMS[1], text=' File Size', anchor=tkinter.W,
                            command=self.sort_file_size)
        self.__tree.heading(self.CLMS[2], text=' Path', anchor=tkinter.W,
                            command=self.sort_path)
        # Setup the columns.
        self.__tree.column(self.TREE, minwidth=100, width=200)
        self.__tree.column(self.CLMS[0], minwidth=100, width=200)
        self.__tree.column(self.CLMS[1], minwidth=100, width=200)
        self.__tree.column(self.CLMS[2], minwidth=100, width=200)
        # Connect the Scrollbars.
        self.__tree.configure(yscrollcommand=self.__scroll_1.set)
        self.__tree.configure(xscrollcommand=self.__scroll_2.set)
        # PATCH: Provide data store.
        if TrimDir.SIZE:
            self.__tree.nodes = dict()

    def configure_menu(self):
        "Configure the (context) Menu widget."
        # Shortcut for narrowing the search.
        self.__menu.add_command(label='Search Directory',
                                command=self.search_dir)
        self.__menu.add_separator()
        # Operations committed on directory.
        self.__menu.add_command(label='Remove Directory', command=self.rm_dir)
        self.__menu.add_command(label='Remove Files', command=self.rm_files)
        self.__menu.add_separator()
        # Operations that recurse on sub-directories.
        self.__menu.add_command(label='Remove Sub-directories',
                                command=self.rm_subdirs)
        self.__menu.add_command(label='Remove Sub-files',
                                command=self.rm_subfiles)
        self.__menu.add_separator()
        # Operations that remove empty directories and files.
        self.__menu.add_command(label='Remove Empty Directories',
                                command=self.rm_empty_dirs)
        self.__menu.add_command(label='Remove Empty Files',
                                command=self.rm_empty_files)
        # Only add "Open Directory" command on Windows.
        if hasattr(os, 'startfile'):
            self.__menu.add_separator()
            self.__menu.add_command(label='Open Directory',
                                    command=self.open_dir)

    ########################################################################

    # This property is used to control access to operations.

    def __get_operations_enabled(self):
        "Return if run button is in normal state."
        return self.__run['state'].string == tkinter.NORMAL

    def __set_operations_enabled(self, value):
        "Enable or disable run button's state according to value."
        self.__run['state'] = tkinter.NORMAL if value else tkinter.DISABLED

    operations_enabled = property(__get_operations_enabled,
                                  __set_operations_enabled,
                                  doc="Flag controlling certain operations")

    ########################################################################

    # Handle path browsing and searching actions.

    def choose(self, event=None):
        "Show directory browser and set path as needed."
        path = self.__dialog.show()
        if path:
            # Entry is cleared before absolute path is added.
            self.__path.delete(0, tkinter.END)
            self.__path.insert(0, os.path.abspath(path))

    def search(self, event=None):
        "Start search thread while GUI automatically updates."
        threadlog.start_thread(self.search_thread)

    def search_thread(self):
        "Search the path and display the size of the directory."
        if self.operations_enabled:
            self.operations_enabled = False
            # Get absolute path and check existence.
            path = os.path.abspath(self.__path.get())
            if os.path.isdir(path):
                # Enable operations after finishing search.
                self.__search(path)
                self.operations_enabled = True
            else:
                animator.indicate_error(self.__tk, self.__error,
                                        self.enable_operations)

    def __search(self, path):
        "Execute the search procedure and display in Treeview."
        self.__run.grid_remove()
        self.__cancel.grid()
        children = self.start_search()
        try:
            tree = discover.SizeTree(path, self.validate_search)
        except StopIteration:
            self.handle_stop_search(children)
        else:
            self.finish_search(children, tree)
        self.__cancel.grid_remove()
        self.__run.grid()

    ########################################################################

    # Execute various phases of a search.

    def start_search(self):
        "Edit the GUI in preparation for executing a search."
        self.__stop_search = False
        children = runmethod.Apply(treeview.Node(self.__tree).children)
        children.detach()
        self.__progress.configure(mode='indeterminate', maximum=100)
        self.__progress.start()
        return children

    def validate_search(self):
        "Check that the current search action is valid."
        if self.__stop_search:
            self.__stop_search = False
            raise StopIteration('Search has been canceled!')

    def stop_search(self, event=None):
        "Cancel a search by setting its stop flag."
        self.__stop_search = True

    def handle_stop_search(self, children):
        "Reset the Treeview and Progressbar on premature termination."
        children.reattach()
        self.__progress.stop()
        self.__progress['mode'] = 'determinate'

    def finish_search(self, children, tree):
        "Delete old children, update Progressbar, and update Treeview."
        children.delete()
        self.__progress.stop()
        self.__progress.configure(mode='determinate',
                                  maximum=tree.total_nodes+1)
        node = treeview.Node(self.__tree).append(tree.name)
        try:
            self.build_tree(node, tree)
        except StopIteration:
            pass

    ########################################################################

    # Handle Treeview column sorting events initiated by user.

    def sort_name(self):
        "Sort children of selected node by name."
        treeview.Node.current(self.__tree).sort_name()

    def sort_total_size(self):
        "Sort children of selected node by total size."
        treeview.Node.current(self.__tree).sort_total_size()

    def sort_file_size(self):
        "Sort children of selected node by file size."
        treeview.Node.current(self.__tree).sort_file_size()

    def sort_path(self):
        "Sort children of selected node by path."
        treeview.Node.current(self.__tree).sort_path()

    ########################################################################

    # Handle right-click events on the Treeview widget.

    def open_menu(self, event):
        "Select Treeview row and show context menu if allowed."
        item = event.widget.identify_row(event.y)
        if item:
            event.widget.selection_set(item)
            if self.menu_allowed:
                self.__menu.post(event.x_root, event.y_root)

    @property
    def menu_allowed(self):
        "Check if menu is enabled along with operations."
        return self.MENU and self.operations_enabled

    def search_dir(self):
        "Search the path of the currently selected row."
        path = treeview.Node.current(self.__tree).path
        self.__path.delete(0, tkinter.END)
        self.__path.insert(0, path)
        self.search()

    def rm_dir(self):
        "Remove the currently selected directory."
        if self.commit_permanent_operation:
            threadlog.start_thread(self.do_remove_directory)

    def rm_files(self):
        "Remove the files in the currently selected directory."
        if self.commit_permanent_operation:
            threadlog.start_thread(self.do_remove_files)

    def rm_subdirs(self):
        "Remove the sub-directories of the currently selected directory."
        if self.commit_permanent_operation:
            threadlog.start_thread(self.do_remove_subdirectories)

    def rm_subfiles(self):
        "Remove the sub-files of the currently selected directory."
        if self.commit_permanent_operation:
            threadlog.start_thread(self.do_remove_subfiles)

    def rm_empty_dirs(self):
        "Recursively remove empty directories from selected directory."
        if self.commit_permanent_operation:
            threadlog.start_thread(self.do_remove_empty_dirs)

    def rm_empty_files(self):
        "Recursively remove empty files from selected directory."
        if self.commit_permanent_operation:
            threadlog.start_thread(self.do_remove_empty_files)

    @property
    def commit_permanent_operation(self):
        "Check if warning should be issued before committing operation."
        return not self.WARN or self.__warn.show() == tkinter.messagebox.YES

    def open_dir(self):
        "Open up the current directory (only available on Windows)."
        os.startfile(treeview.Node.current(self.__tree).path)

    ########################################################################

    # Execute actions requested by context menu.

    def do_remove_directory(self):
        "Remove a directory and all of its sub-directories."
        self.begin_rm()
        # Get the current Treeview node and delete it.
        node = treeview.Node.current(self.__tree)
        directory_size, path = node.total_size, node.path
        position, parent = node.position, node.delete(True)
        # Delete the entire directory at path.
        remove.directory_files(path, True, True)
        if os.path.isdir(path):
            # Add the directory back to the Treeview.
            tree = discover.SizeTree(path)
            self.begin_rm_update(tree.total_nodes + 1)
            # Rebuild the Treeview under the parent.
            node = parent.insert(position, tree.name)
            self.build_tree(node, tree)
            # New directory size.
            total_size = tree.total_size
        else:
            self.begin_rm_update()
            # New directory size.
            total_size = 0
        # If the size has changed, update parent nodes.
        if directory_size != total_size:
            diff = total_size - directory_size
            self.update_parents(parent, diff)
        self.end_rm()

    def do_remove_files(self):
        "Remove all of the files in the selected directory."
        # Delete files in the directory and get its new size.
        node = treeview.Node.current(self.__tree)
        total_size = remove.files(node.path)
        # Update current and parent nodes if the size changed.
        if node.file_size != total_size:
            diff = total_size - node.file_size
            node.file_size = total_size
            node.total_size += diff
            self.update_parents(node.parent, diff)

    def do_remove_subdirectories(self):
        "Remove all subdirectories in the directory."
        self.begin_rm()
        # Remove all the children nodes in Viewtree.
        node = treeview.Node.current(self.__tree)
        for child in node.children:
            child.delete()
        # Delete all of the subdirectories and their files.
        remove.directory_files(node.path, True)
        # Find out what subdirectories could not be deteled.
        tree = discover.SizeTree(node.path)
        self.begin_rm_update(tree.total_nodes)
        if tree.total_nodes:
            # Rebuild the Viewtree as needed.
            self.build_tree(node, tree, False)
            # Fix node and prepare to update parents.
            diff = node.total_size - tree.total_size
            node.total_size = tree.total_size
        else:
            # Fix node and prepare to update parents.
            diff = node.file_size - node.total_size
            node.total_size = node.file_size
        # Update parents with new size.
        self.update_parents(node.parent, diff)
        self.end_rm()

    def do_remove_subfiles(self):
        "Remove all subfiles while keeping subdirectories in place."
        self.begin_rm()
        node = treeview.Node.current(self.__tree)
        remove.directory_files(node.path)
        self.synchronize_tree(node)

    def do_remove_empty_dirs(self):
        "Remove all empty directories from selected directory."
        self.begin_rm()
        node = treeview.Node.current(self.__tree)
        remove.empty_directories(node.path)
        self.synchronize_tree(node)

    def do_remove_empty_files(self):
        "Remove all empty files from selected directory."
        self.begin_rm()
        # Remove empty files from the current path.
        node = treeview.Node.current(self.__tree)
        remove.empty_files(node.path)
        # Return the Progressbar back to normal.
        self.begin_rm_update()
        self.end_rm()

    ########################################################################

    # Help update Progressbar in removal process.

    def begin_rm(self):
        "Start a long-running removal operation."
        self.operations_enabled = False
        self.__progress.configure(mode='indeterminate', maximum=100)
        self.__progress.start()

    def begin_rm_update(self, nodes=0):
        "Move to determinate mode of updating the Viewtree."
        self.__progress.stop()
        self.__progress.configure(mode='determinate', maximum=nodes)

    def end_rm(self):
        "Finish removal process by enabling operations."
        self.operations_enabled = True

    enable_operations = end_rm  # Create alias for command.

    ########################################################################

    # Update the Viewtree nodes after creating a SizeTree object.

    def synchronize_tree(self, node):
        "Find the current directory state and update the tree."
        # Build a new SizeTree to find the result.
        tree = discover.SizeTree(node.path)
        self.begin_rm_update(tree.total_nodes)
        # Record the difference and patch the Viewtree.
        diff = tree.total_size - node.total_size
        self.patch_tree(node, tree)
        # Fix all parent nodes with the correct size.
        self.update_parents(node.parent, diff)
        self.end_rm()

    def build_tree(self, node, tree, update_node=True):
        "Build the Treeview while updating the Progressbar."
        self.validate_search()
        if update_node:
            self.sync_nodes(node, tree)
        self.add_children(node, tree)

    def sync_nodes(self, node, tree):
        "Update attributes on node and refresh GUI."
        # Copy the information on the node.
        node.total_size = tree.total_size
        node.file_size = tree.file_size
        node.path = tree.path
        # Update the Progressbar and GUI.
        self.__progress.step()

    def patch_tree(self, node, tree):
        "Patch differences between node and tree."
        node.total_size = tree.total_size
        node.file_size = tree.file_size
        self.patch_children(node, tree)
        self.add_children(node, tree)

    def add_children(self, node, tree):
        "Build and traverse all child nodes."
        for child in tree.children:
            subnode = node.append(child.name)
            self.build_tree(subnode, child)

    def patch_children(self, node, tree):
        "Patch Viewtree based on children of SizeTree."
        for subnode in node.children:
            child = tree.pop_child(subnode.name)
            if child is None:
                # Directory is gone.
                subnode.delete()
            else:
                # Dig down further in tree.
                self.__progress.step()
                self.patch_tree(subnode, child)

    @staticmethod
    def update_parents(node, diff):
        "Add in difference to node and parents."
        while not node.root:
            node.total_size += diff
            node = node.parent

################################################################################

# TrimDir must already exist.
from . import treeview
