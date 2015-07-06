# These are a bunch of modules for this code.
import math
import os
import uuid
import pickle
import pickletools
import hashlib
import bz2
import zlib
import _thread

################################################################################

class Driver:

    "Driver(maximum, quantum) -> Driver"

    def __init__(self, maximum, quantum):
        "Initializes the maximum and quantum values of the driver."
        assert isinstance(maximum, int) and 0 < maximum, \
               'Maximum should be an integer greater than zero!'
        assert isinstance(quantum, int) and 0 < quantum <= 1 << 20, \
               'Quantum should be an integer in the megabyte range!'
        self.__maximum = maximum
        self.__quantum = quantum

    def read(self, index):
        "Checks that the block index is is range."
        assert isinstance(index, int) and 0 <= index < self.__maximum, \
               'Index should be an integer in the maximum range!'

    def write(self, index, data):
        "Checks that the block index is in range and data value is valid."
        assert isinstance(index, int) and 0 <= index < self.__maximum, \
               'Index should be an integer in the maximum range!'
        assert isinstance(data, bytes) and len(data) == self.__quantum, \
               'Data should be bytes of quantum length.'

    def delete(self, index):
        "Checks that the block index is is range."
        assert isinstance(index, int) and 0 <= index < self.__maximum, \
               'Index should be an integer in the maximum range!'

    @property
    def maximum(self):
        "Returns a read-only maximum value of the driver."
        return self.__maximum

    @property
    def quantum(self):
        "Returns a read-only quantum value of the driver."
        return self.__quantum

    @property
    def total_space(self):
        "Returns the total capacity caculated from maximum and quantum."
        return self.__maximum * self.__quantum

    @property
    def used_space(self):
        "Placeholder to be implemented by an inheriting class."
        raise NotImplementedError()

    @property
    def free_space(self):
        "Placeholder to be implemented by an inheriting class."
        raise NotImplementedError()

################################################################################

class RAMDriver(Driver):

    "RAMDriver(minimum) -> RAMDriver"

    DEFAULT_QUANTUM = 1 << 10   # 1 Kilobyte

    def __init__(self, minimum):
        "Initializes driver with empty block and block storage."
        maximum = math.ceil(minimum / self.DEFAULT_QUANTUM)
        super().__init__(maximum, self.DEFAULT_QUANTUM)
        self.__default = bytes(self.DEFAULT_QUANTUM)
        self.__storage = dict()

    def read(self, index):
        "Gets the contents of the block located at the index."
        super().read(index)
        return self.__storage.get(index, self.__default)

    def write(self, index, data):
        "Sets the contents of the block located at the index."
        super().write(index, data)
        self.__storage[index] = data

    def delete(self, index):
        "Annihilates the block contents located at the index."
        super().delete(index)
        self.__storage.pop(index, None)

    def save(self, proxy):
        "Uses proxy to export state data to another location."
        proxy._DiskProxy__save(self.__storage)

    @property
    def used_space(self):
        "Caculates amount of space in use and returns value."
        return len(self.__storage) * self.quantum

    @property
    def free_space(self):
        "Caculates amount of unoccupied space and returns value."
        return (self.maximum - len(self.__storage)) * self.quantum

################################################################################

class DiskProxy:

    "DiskProxy(path, target) -> DiskProxy"

    def __init__(self, path, target):
        "Initializes proxy with the repository's settings."
        assert isinstance(target, int) and target > 0, 'Bad target file size!'
        self.__path = path
        self.__target = target

    def __save(self, blocks):
        "Used by RAMDriver to export internal blocks to disk."
        assert not os.path.exists(self.__path), 'Target path already exists!'
        os.makedirs(self.__path)
        if blocks:
            file = self.__new_file()
            for key, value in blocks.items():
                if sum(value):
                    if file.tell() >= self.__target:
                        file = self.__new_file()
                    block = key, SmartBlock(value)
                    file.write(pickletools.optimize(pickle.dumps(block)))

    def __new_file(self):
        "Creates a new block archive to be automatically signed."
        name = uuid.uuid4().hex + '.bin'
        path = os.path.join(self.__path, name)
        return SignedWriter(path)

    def load(self, driver):
        "Opens repository files and extracts the data from them."
        assert os.path.isdir(self.__path), 'Target path is not directory!'
        for name in os.listdir(self.__path):
            if os.path.splitext(name)[1].lower() == '.bin':
                path = os.path.join(self.__path, name)
                if os.path.isfile(path):
                    with open(path, 'rb') as file:
                        self.__get_data(file, driver)

    def __get_data(self, file, driver):
        "Reads all records in a file and writes them to the driver."
        seek = file.read(1)
        if seek:
            file.seek(seek[0])
        try:
            while True:
                key, block = pickle.load(file)
                driver.write(key, block.value)
        except EOFError:
            pass

################################################################################

class SignedWriter:

    "SignedWriter(path) -> SignedWriter"

    OVERHEAD = 168      # Minimum Size
    MAX_SIZE = 1 << 20  # 1 Megabyte

    def __init__(self, path):
        "Initializes and opens a file to be automatically signed."
        name = os.path.basename(path)
        size = len(name.encode()) + self.OVERHEAD
        assert size <= 256, 'Filename is too long!'
        self.__file = open(path, 'wb')
        self.__file.write(bytes([size]) + \
                          '<source name="{}" size="'.format(name).encode())
        self.__seek = self.__file.tell()
        self.__file.seek(self.__file.truncate(size))
        self.__hash = hashlib.sha512()

    def write(self, data):
        "Records data to file while maintaining internal hash."
        assert self.__file.tell() + len(data) <= self.MAX_SIZE, 'Too much data!'
        self.__file.write(data)
        self.__hash.update(data)

    def tell(self):
        "Returns the current writing position in the file."
        return self.__file.tell()

    def __del__(self):
        "Finishes writing the signature and closes the file."
        size = self.__file.tell()
        self.__file.seek(self.__seek)
        self.__file.write('{:05x}" hash="{}" />'.format(size,
                          self.__hash.hexdigest()).encode())
        self.__file.flush()
        self.__file.close()

################################################################################

def enum(names):
    "Create a simple enumeration for use within Python."
    names = names.replace(',', ' ').split()
    space = dict(map(reversed, enumerate(names)), __slots__=())
    return type('enum', (object,), space)()

################################################################################

class SmartBlock:

    "SmartBlock(binary) -> SmartBlock"

    TYPES = enum('RAW, BZ2, ZLIB')

    def __init__(self, binary):
        "Initializes instance with efficiently stored data."
        values = (binary, bz2.compress(binary, 9), zlib.compress(binary, 9))
        sizes = tuple(map(len, values))
        self.__value = values[sizes.index(min(sizes))]
        self.__type = index

    @property
    def value(self):
        "Returns binary data in its originally given format."
        if self.__type == self.TYPES.BZ2:
            return bz2.decompress(self.__value)
        if self.__type == self.TYPES.ZLIB:
            return zlib.decompress(self.__value)
        return self.__value

################################################################################

class DiskAbstractionLayer1:

    "DiskAbstractionLayer1(driver) -> DiskAbstractionLayer1"

    def __init__(self, driver):
        "Initializes DAL1 with driver and BIT (Block Information Table)."
        self.__driver = driver
        bit_size = self.__partition()
        self.__load_BIT(bit_size)

    def __partition(self):
        "Calculates the number of blocks to reserve for the BIT."
        blocks = self.__driver.maximum
        size = self.__driver.quantum
        bit = 0
        take = math.ceil(blocks / size)
        while take:
            blocks -= take
            bit += take
            give = (bit * size - blocks) // size
            if not give or give == take:
                break
            blocks += give
            bit -= give
            take = (blocks - bit * size) // size
        self.__maximum = blocks
        return bit

    def __load_BIT(self, bit_size):
        "Pulls BIT from driver and caches it in RAM as bytearray."
        blocks = []
        for index in range(bit_size):
            blocks.append(self.__driver.read(self.__maximum + index))
        self.__BIT = bytearray().join(blocks)
        self.__BIT_lock = _thread.allocate_lock()

    def alloc(self, info):
        "Acquires a free block and returns its index."
        assert info, 'May not alloc with a status of zero!'
        with self.__BIT_lock:
            index = self.__BIT.find(b'\0')
            if index == -1:
                raise MemoryError()
            self.__BIT[index] = info
        return index

    def read(self, index):
        "Gets the data from an allocated block and returns it."
        assert index < self.__maximum, 'Index is too large!'
        with self.__BIT_lock:
            assert self.__BIT[index], 'Block has not been allocated!'
            return self.__driver.read(index)

    def write(self, index, data):
        "Sets the data of a block if it has already been allocated."
        assert index < self.__maximum, 'Index is too large!'
        with self.__BIT_lock:
            assert self.__BIT[index], 'Block has not been allocated!'
            self.__driver.write(index, data)

    def free(self, index):
        "Deallocates a used block and deletes the data stored in it."
        assert index < self.__maximum, 'Index is too large!'
        with self.__BIT_lock:
            assert self.__BIT[index], 'Block has not been allocated!'
            self.__driver.delete(index)
            self.__BIT[index] = 0

    def flush(self):
        "Takes the information in the BIT and writes it to the driver."
        quantum = self.__driver.quantum
        with self.__BIT_lock:
            for index, offset in enumerate(range(0, len(self.__BIT), quantum)):
                block = bytes(self.__BIT[offset:offset+quantum])
                self.__driver.write(index + self.__maximum, block)

    def __getitem__(self, key):
        "Reads the value of the BIT for a block and returns it."
        assert 0 <= key < self.__maximum, 'Index is out of range!'
        return self.__BIT[key]

    def __setitem__(self, key, value):
        "Writes the value for a block to the BIT if it is not free."
        assert 0 <= key < self.__maximum, 'Index is out of range!'
        assert value, 'Zero cannot be assigned to a allocated block!'
        with self.__BIT_lock:
            assert self.__BIT[key], 'Block has not been allocated!'
            self.__BIT[key] = value

    @property
    def maximum(self):
        "Returns number of available blocks after BIT allocation."
        return self.__maximum

    @property
    def BIT_lock(self):
        "Returns BIT lock so client can protect data operations."
        return self.__BIT_lock

################################################################################

class DiskAbstractionLayer2:

    "DiskAbstractionLayer2(DAL1, quantum) -> DiskAbstractionLayer2"

    STATUS = enum('closed, file, dir, data')    # 00, 01, 10, 11
    RECORD = enum('root, tail, head, whole')    # 00, 01, 10, 11

    ########################################################################

    class __DirRecord:

        def __init__(self, owner, dirs, files, meta):
            self.__owner = owner
            self.__dirs = dirs
            self.__files = files
            self.__meta = meta

        def encode(self, maximum, pointer):
            buffer = self.__encode_owner(maximum, pointer)
            # START HERE

        def __encode_owner(self):
            size = len(self.__owner)
            assert size < 1 << 8, 'There are too many owners!'
            buffer = bytearray([size])
            for block in self.__owner:
                buffer.extend(self.__format_pointer(block, maximum, pointer))
            return buffer

        @staticmethod
        def __format_pointer(block, maximum, pointer):
            assert 0 <= block <= maximum, 'Block is outside valid range!'
            buffer = bytearray(pointer)
            index = -1
            while block:
                block, byte =  divmod(block, 1 << 8)
                buffer[index] = byte
                index -= 1
            return buffer

    ########################################################################

    class __FileRecord: pass

    ########################################################################

    def __init__(self, DAL1, quantum):
        self.__DAL1 = DAL1
        self.__pointer = math.ceil(math.log(DAL1.maximum) / math.log(1 << 8))
        self.__quantum = quantum - self.__pointer * 2
        assert self.__quantum > 0, 'DAL1 is incompatible with DAL2 needs.'
        if DAL1[0]:
            # Test the root node.
        else:
            # Create the root node.

################################################################################

class DiskAbstractionLayer2:

    STATUS = enum('closed, dir, file, data')
    RECORD = enum('whole, head, root, tail')

    def __init__(self, DAL1, quantum):
        self.__DAL1 = DAL1
        self.__maximum = DAL1.maximum
        self.__quantum = quantum
        self.__setup_size()
        self.__setup_root()

    def __setup_size(self):
        size = math.ceil(math.log(self.__maximum) / math.log(1 << 8))
        self.__useable = self.__quantum - size * 2
        assert self.__useable > 0
        self.__ptr_size = size

    def __setup_root(self):
        root = self.__DAL1[0]
        if not root:
            data = self.__format_dir_record([self.__maximum], [], [], {})
            pointer = self.__create_new_node(self.STATUS.dir, data)[0]
            assert not pointer
        else:
            assert root >> 6 == self.STATUS.dir
            assert root >> 4 & 0b11 in {self.RECORD.whole, self.RECORD.head}
            record = self.__load_dir_record(0)
            # START HERE

    def __load_dir_record(self, pointer):
        pass  # AND HERE

    def __create_new_node(self, status, data):
        assert status in {self.STATUS.dir, self.STATUS.file}
        blocks = math.ceil(len(data) / self.__useable)
        blocks = self.__alloc_node_blocks(blocks, status)
        self.__write_node_blocks(blocks, data)
        return blocks

    def __alloc_node_blocks(self, total, status):
        blocks = []
        try:
            for neg, pos in enumerate(range(total), -total):
                if total == 1:
                    record = self.RECORD.whole
                elif pos == 0:
                    record = self.RECORD.head
                elif new == -1:
                    record = self.RECORD.tail
                else:
                    record = self.RECORD.root
                blocks.append(self.__DAL1.alloc(status << 6 | record << 4))
        except MemoryError:
            for block in blocks:
                self.__DAL1.free(block)
            raise
        return blocks

    def __write_node_blocks(self, blocks, data):
        length = len(data) % self.__useable
        if length:
            data.extend(bytes(self.__useable - length))
        length = len(blocks)
        for index, offset in enumerate(range(0, len(data), self.__useable)):
            buffer = self.__format_block_pointer(blocks[index - 1])
            buffer.extend(data[offset:offset+self.__useable])
            block, index = blocks[index], (index + 1) % length
            buffer.extend(self.__format_block_pointer(blocks[index]))
            self.__DAL1.write(block, bytes(buffer))

    def __format_dir_record(self, owners, dirs, files, meta):
        buffer = self.__format_dir_owners(owners))
        buffer.extend(self.__format_pointer_names(dirs))
        buffer.extend(self.__format_pointer_names(files))
        buffer.extend(self.__format_meta_info(meta))
        return buffer

    def __format_dir_owners(self, pointers):
        size = len(pointers)
        assert size < 1 << 8
        buffer = bytearray([size])
        for pointer in pointers:
            buffer.extend(self.__format_block_pointer(pointer))
        return buffer

    def __format_block_pointer(self, pointer):
        assert 0 <= pointer <= self.__maximum
        value = bytearray(self.__ptr_size)
        index = -1
        while pointer:
            pointer, digit = divmod(pointer, 1 << 8)
            value[index] = digit
            index -= 1
        return value

    def __format_pointer_names(self, records):
        size = len(records)
        buffer = bytearray([size >> 8, size & 0xFF])
        for pointer, name in records:
            buffer.extend(self.__format_block_pointer(pointer))
            buffer.extend(self.__format_length_name(name))
        return buffer

    def __format_length_name(self, name):
        size = len(name)
        assert 0 < size < 1 << 8
        return bytes([size]) + name

    def __format_meta_info(self, mapping):
        size = len(mapping)
        assert len(mapping) < 1 << 8
        buffer = bytearray([size])
        for key, value in mapping.items():
            buffer.extend(self.__format_length_name(key))
            size = len(value)
            buffer.extend(bytes([size >> 8, size & 0xFF]))
            buffer.extend(value)
        return buffer
