# IMPORTS
import base255
import os
import byte_mod
import tkinter
import tkinter.filedialog
import tkinter.messagebox
import hashlib

# CONFIGURATION
FILE_SIZE = 1 << 20

################################################################################

def main():
    global master, source_dialog, destination_dialog, source_entry, \
           destination_entry
    # Create the master frame.
    master = tkinter.Tk()
    master.resizable(False, False)
    master.title('DAM 2.0')
    # Create the dialog boxes.
    source_dialog = tkinter.filedialog.Open(
        master, parent=master,
        title='Please choose a source file and select OK.')
    destination_dialog = tkinter.filedialog.Directory(
        master, mustexist=True, parent=master,
        title='Please choose a destination directory and select OK.')
    # Create the label frames.
    source_frame = tkinter.LabelFrame(master, text='Source')
    destination_frame = tkinter.LabelFrame(master, text='Destination')
    # Create the text widgets.
    source_entry = tkinter.Entry(source_frame)
    destination_entry = tkinter.Entry(destination_frame)
    # Create the push buttons.
    source_button = tkinter.Button(source_frame, text='Browse ...',
                                   command=browse_source)
    destination_button = tkinter.Button(destination_frame, text='Browse ...',
                                        command=browse_destination)
    split_button = tkinter.Button(master, text='Divide', command=split)
    join_button = tkinter.Button(master, text='Merge', command=join)
    # Create the entry bindings.
    source_entry.bind('<Return>', browse_source)
    destination_entry.bind('<Return>', browse_destination)
    master.bind_class('Entry', '<Control-Key-a>', select_all)
    # Create the button bindings.
    source_button.bind('<Return>', browse_source)
    destination_button.bind('<Return>', browse_destination)
    split_button.bind('<Return>', split)
    join_button.bind('<Return>', join)
    # Arrange frames on window.
    source_frame.grid(row=0, padx=5, pady=5, columnspan=2)
    destination_frame.grid(row=1, padx=5, pady=5, columnspan=2)
    # Arrange widgets on frames.
    source_entry.grid(row=0, column=0, padx=5, pady=5)
    source_button.grid(row=0, column=1, padx=5, pady=5)
    destination_entry.grid(row=0, column=0, padx=5, pady=5)
    destination_button.grid(row=0, column=1, padx=5, pady=5)
    # Arrage buttons on window.
    split_button.grid(row=2, column=0, padx=5, pady=5, sticky='news')
    join_button.grid(row=2, column=1, padx=5, pady=5, sticky='news')
    # Run tkinter's main loop.
    master.mainloop()

def browse_source(event=None):
    # Browse for source.
    path = source_dialog.show()
    if path:
        # Change the text.
        source_entry.delete(0, tkinter.END)
        source_entry.insert(0, os.path.realpath(path))
    # Change the focus.
    source_entry.focus_set()

def browse_destination(event=None):
    # Browse for destination.
    path = destination_dialog.show()
    if path:
        # Change the text.
        destination_entry.delete(0, tkinter.END)
        destination_entry.insert(0, os.path.realpath(path))
    # Change the focus.
    destination_entry.focus_set()

def split(event=None):
    # Split the file.
    frame(split_file, 'The file could not be split.')

def join(event=None):
    # Join the file.
    frame(join_file, 'The file could not be joined.')

def select_all(event):
    # Select all in the widget.
    event.widget.selection_range(0, tkinter.END)
    return 'break'

def frame(function, message):
    try:
        # Check and get source and destination.
        source, destination = cag_sad()
        master.withdraw()
        try:
            # Call needed function.
            function(source, destination)
        except:
            tkinter.messagebox.showerror('Error', message)
            raise
        master.deiconify()
    except AssertionError as warning:
        # Display a warning.
        tkinter.messagebox.showwarning('Warning', str(warning))
        raise

def split_file(source, destination):
    # Create an index and get the source data.
    index, source = ([byte_mod.table(), os.path.basename(source)],
                     open(source, 'rb').read())
    # Add the source's digest to the index.
    index.append(hashlib.sha1(source).digest())
    # Translate (encrypt) the source.
    source = byte_mod.translate(source, index[0], False)
    # Partition the source and number the parts.
    for number, part in enumerate(byte_mod.partition(source, FILE_SIZE)):
        # Add the part's digest to the index.
        index.append(hashlib.sha1(part).digest())
        # Write the part to its destination.
        open(os.path.join(destination, '{}.{}.part'.format(number, index[1])),
             'wb').write(part)
    # Encode and write the index to its destination.
    open(os.path.join(destination, '{}.part'.format(index[1])), 'wb').write(
        b'\0'.join(map(base255.encode, index)))

def join_file(source, destination):
    # Load and decode the index and prepare a cache.
    index, cache = list(map(base255.decode, open(source, 'rb').read().split(
        b'\0'))), b''
    index[1] = index[1].decode()
    # Ensure that the filenames match.
    assert os.path.basename(source) == '{}.part'.format(index[1])
    # Collect and process the parts of the file.
    for number, sha1 in enumerate(index[3:]):
        # Get the part's data.
        data = open(os.path.join(os.path.dirname(source), '{}.{}.part'.format(
            number, index[1])), 'rb').read()
        # Ensure that the part's digest matches what was recorded.
        assert hashlib.sha1(data).digest() == sha1
        # Cache the data.
        cache += data
    # Translate (decrypt) the cache.
    cache = byte_mod.translate(cache, index[0], True)
    # Ensure that the cache's digest matches what was recorded.
    assert hashlib.sha1(cache).digest() == index[2]
    # Write the cache to its destination.
    open(os.path.join(destination, index[1]), 'wb').write(cache)

def cag_sad():
    # Get the source and destination
    # and check that they are valid.
    source, destination = source_entry.get(), destination_entry.get()
    assert os.path.exists(source), 'The source does not exist.'
    assert os.path.isfile(source), 'The source is not a file.'
    assert os.path.exists(destination), 'The destination does not exist.'
    assert os.path.isdir(destination), 'The destination is not a directory.'
    return source, destination

################################################################################

# Check for direct execution.
if __name__ == '__main__':
    main()
