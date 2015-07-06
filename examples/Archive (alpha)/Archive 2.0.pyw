#! /usr/bin/env python3
# XXX
# Compression is currently disabled
# until it is properly written over
# Unicode is not being decoded well

import bz2
import os
import tempfile
import tkinter as Tkinter
import tkinter.filedialog as tkFileDialog
import tkinter.messagebox as tkMessageBox

################################################################################

def main():
    global root
    root = Tkinter.Tk()
    root.resizable(False, False)
    root.title('Archive 2.0')
    Tkinter.Label(root, text='NOTICE:\nThis program is not backward-compatible and\nconnot be used with the "Archive 1.0" program.', padx=5, pady=5).grid()
    # Tkinter.Button(root, text='Compress Directory to File', command=wrapped_compressor).grid(sticky=Tkinter.NSEW)
    Tkinter.Button(root, text='Decompress File to Directory', command=wrapped_decompressor).grid(sticky=Tkinter.NSEW)
    root.mainloop()

def wrapped_compressor():
    wrapper(GUI_compressor)

def wrapped_decompressor():
    wrapper(GUI_decompressor)

def wrapper(function):
    root.withdraw()
    try:
        function()
    except Exception as error:
        if error:
            tkMessageBox.showerror('Exception', '%s: %s' % (error.__class__.__name__, error))
        else:
            tkMessageBox.showerror('Exception', error.__class__.__name__)
    root.deiconify()

def GUI_compressor():
    source = tkFileDialog.askdirectory(parent=root, title='Please select the source directory.', mustexist=True)
    if source:
        destination = tkFileDialog.asksaveasfilename(parent=root, title='Save Archive', filetypes=['Archive .caa'])
        if destination:
            if not destination.lower().endswith('.caa'):
                destination += '.caa'
            destination = open(destination, 'wb')
            try:
                compress(source, destination)
            finally:
                destination.close()

def GUI_decompressor():
    source = tkFileDialog.askopenfile(mode='rb', parent=root, title='Open Archive', filetypes=['Archive .caa'])
    if source:
        try:
            destination = tkFileDialog.askdirectory(parent=root, title='Please select the destination directory.', mustexist=True)
            if destination:
                decompress(source, destination)
        finally:
            source.close()

def compress(source, destination):
    temp = tempfile.TemporaryFile()
    # dfs.Acquire(temp).acquire(source)
    temp.seek(0)
    compressor = bz2.BZ2Compressor()
    buff = temp.read(2 ** 20)
    while buff:
        destination.write(compressor.compress(buff))
        buff = temp.read(2 ** 20)
    temp.close()
    destination.write(compressor.flush())

def decompress(source, destination):
    decompressor = bz2.BZ2Decompressor()
    temp = tempfile.TemporaryFile()
    buff = source.read(2 ** 20)
    while buff:
        temp.write(decompressor.decompress(buff))
        buff = source.read(2 ** 20)
    temp.write(decompressor.unused_data)
    temp.seek(0)
    Release(temp).release(destination)
    temp.close()

################################################################################

def _int(string):
    integer = 0
    for c in string:
        integer <<= 8
        integer += c
    return integer

class Release:

    'Release(source) -> Release'

    BUFF_SIZE = 2 ** 20

    def __init__(self, source):
        'Initialize the Release object.'
        self.__source = source
        self.__EOF = False

    def release(self, destination):
        'Save source to destination.'
        if self.__EOF:
            raise EOFError('End Of File Found')
        self.__parents = [os.path.abspath(destination)]
        header = self.__source.read(1)
        header = ord(header) if header else -1
        if header == -1:
            self.__EOF = True
            raise Warning('Irregular File Termination Detected')
        while header != -1 and (header > 127 or header & 3):
            if header < 128:
                if header & 3 != 3:
                    raise IOError('Corrupt Directory Header Found')
                self.__dir(header)
            else:
                self.__file(header)
            header = self.__source.read(1)
            header = ord(header) if header else -1
        if header == -1:
            self.__EOF = True

    def EOF(self):
        'Return the End Of File status.'
        return self.__EOF

    def __dir(self, header):
        'Private class method.'
        path = os.path.join(self.__parents[_int(self.__read((header >> 4 & 7) + 1))], self.__read(_int(self.__read((header >> 3 & 1) + 1))).decode())
        if os.path.exists(path):
            if os.path.isfile(path):
                raise IOError('Path Already Exists')
        else:
            os.mkdir(path)
        if header >> 2 & 1:
            self.__parents.append(path)

    def __file(self, header):
        'Private class method.'
        destination = open(os.path.join(self.__parents[_int(self.__read((header >> 4 & 7) + 1))], self.__read(_int(self.__read((header >> 3 & 1) + 1))).decode()), 'wb')
        data_size = _int(self.__read((header & 7) + 1))
        try:
            while data_size:
                buff = self.__source.read(min(self.BUFF_SIZE, data_size))
                if buff:
                    destination.write(buff)
                    data_size -= len(buff)
                else:
                    raise IOError('End Of File Found')
        finally:
            destination.close()

    def __read(self, size):
        'Private class method.'
        if size:
            buff = b''
            while size:
                temp = self.__source.read(size)
                if temp:
                    buff += temp
                    size -= len(temp)
                else:
                    raise IOError('End Of File Found')
            return buff
        raise IOError('Zero Length String Found')

################################################################################

if __name__ == '__main__':
    main()
