# IMPORTS
import os
import sys
import tkinter
import tkinter.filedialog
import tkinter.messagebox

# CONFIGURATION
FONT = 'Courier 8'
WIDTH = 34
PADX = 4
PADY = 4
BUFFER = 1 << 20
DEFAULT_DIRS = 'C:\\Users', 'C:\\'

################################################################################

def main():
    global master, source_directory, destination_directory, source_entry, \
           destination_entry, name_of_backup_entry
    # Create the master widget.
    master = tkinter.Tk()
    master.resizable(False, False)
    master.title('Backup 2.5')
    # Create the folder dialogs.
    options = dict(mustexist=True,
                   parent=master,
                   title='Please choose a source directory and select OK.')
    if os.name == 'nt':
        for directory in DEFAULT_DIRS:
            if os.path.isdir(directory):
                options['initialdir'] = directory
                break
    source_directory = tkinter.filedialog.Directory(master, **options)
    options['title'] = options['title'].replace('source', 'destination')
    destination_directory = tkinter.filedialog.Directory(master, **options)
    # Create the label frames.
    source_label_frame = tkinter.LabelFrame(master,
                                            font=FONT,
                                            text='Source')
    destination_label_frame = tkinter.LabelFrame(master,
                                                 font=FONT,
                                                 text='Destination')
    name_of_backup_label_frame = tkinter.LabelFrame(master,
                                                    font=FONT,
                                                    text='Name of Backup')
    # Create the entry widgets.
    source_entry = tkinter.Entry(source_label_frame,
                                 font=FONT,
                                 width=WIDTH)
    destination_entry = tkinter.Entry(destination_label_frame,
                                      font=FONT,
                                      width=WIDTH)
    name_of_backup_entry = tkinter.Entry(name_of_backup_label_frame,
                                         font=FONT,
                                         width=WIDTH)
    # Create the button widgets.
    source_button = tkinter.Button(source_label_frame,
                                   font=FONT,
                                   text='Browse ...',
                                   command=browse_source)
    destination_button = tkinter.Button(destination_label_frame,
                                        font=FONT,
                                        text='Browse ...',
                                        command=browse_destination)
    name_of_backup_button = tkinter.Button(name_of_backup_label_frame,
                                           font=FONT,
                                           text=' Continue ',
                                           command=backup)
    # Create the entry bindings.
    source_entry.bind('<Return>', browse_source)
    destination_entry.bind('<Return>', browse_destination)
    name_of_backup_entry.bind('<Return>', backup)
    master.bind_class('Entry', '<Control-Key-a>', select_all)
    # Create the button bindings.
    source_button.bind('<Return>', browse_source)
    destination_button.bind('<Return>', browse_destination)
    name_of_backup_button.bind('<Return>', backup)
    # Arrange label frames on master widget.
    source_label_frame.grid(row=0, padx=PADX, pady=PADY)
    destination_label_frame.grid(row=1, padx=PADX, pady=PADY)
    name_of_backup_label_frame.grid(row=2, padx=PADX, pady=PADY)
    # Arrange widgets on label frames.
    source_entry.grid(row=0, column=0, padx=PADX, pady=PADY)
    source_button.grid(row=0, column=1, padx=PADX, pady=PADY)
    destination_entry.grid(row=0, column=0, padx=PADX, pady=PADY)
    destination_button.grid(row=0, column=1, padx=PADX, pady=PADY)
    name_of_backup_entry.grid(row=0, column=0, padx=PADX, pady=PADY)
    name_of_backup_button.grid(row=0, column=1, padx=PADX, pady=PADY)
    # Run tkinter's main loop.
    master.mainloop()

def browse_source(event=None):
    # Browse for a source.
    path = source_directory.show()
    if path:
        # Change the source text.
        source_entry.delete(0, tkinter.END)
        source_entry.insert(0, os.path.realpath(path))
    # Set the focus on the source entry widget.
    source_entry.focus_set()

def browse_destination(event=None):
    # Browse for a destination.
    path = destination_directory.show()
    if path:
        # Change the destination text.
        destination_entry.delete(0, tkinter.END)
        destination_entry.insert(0, os.path.realpath(path))
    # Set the focus on the destination entry widget.
    destination_entry.focus_set()

def backup(event=None):
    # Get the source and destination.
    source = source_entry.get()
    destination = destination_entry.get()
    try:
        # Check for problems.
        assert os.path.exists(source), 'The source does not exist.'
        assert os.path.isdir(source), 'The source is not a directory.'
        assert os.path.exists(destination), 'The destination does not exist.'
        assert os.path.isdir(destination), 'The destination is not a directory.'
        # Execute the backup process.
        master.withdraw()
        try:
            copy(source, os.path.join(destination, name_of_backup_entry.get()))
        except:
            tkinter.messagebox.showerror('Error',
                                         'The backup could not be created.')
        master.deiconify()
    except AssertionError as warning:
        # Display warning message box.
        tkinter.messagebox.showwarning('Warning', str(warning))
    # Set the focus on the name of backup entry widget.
    name_of_backup_entry.focus_set()

def copy(source, destination, ignore=None, errors=None):
    # Check recursion level.
    if ignore is None or errors is None:
        root = True
        ignore = destination
        errors = list()
    else:
        root = False
    # Copy everything from the source to the destination.
    directory = os.listdir(source)
    os.mkdir(destination)
    for name in directory:
        source_name = os.path.join(source, name)
        destination_name = os.path.join(destination, name)
        try:
            if source_name == ignore:
                continue
            elif os.path.isdir(source_name):
                copy(source_name, destination_name, ignore, errors)
            elif os.path.isfile(source_name):
                source_file = open(source_name, 'rb')
                destination_file = open(destination_name, 'wb')
                buff = source_file.read(BUFFER)
                while buff:
                    destination_file.write(buff)
                    buff = source_file.read(BUFFER)
                source_file.close()
                destination_file.close()
        except:
            errors.append('{}\n{}'.format(source_name, destination_name))
    # Write error log if needed.
    if root and errors:
        open(os.path.join(os.path.dirname(sys.argv[0]), 'error.log'), 'w'
             ).write('\n\n'.join(errors))

def select_all(event):
    # Select everything in an entry widget.
    event.widget.selection_range(0, tkinter.END)
    return 'break'

################################################################################

# Check for direct execution.
if __name__ == '__main__':
    main()
