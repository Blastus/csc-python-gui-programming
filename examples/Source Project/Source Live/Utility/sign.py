# <source name="sign.py" size="041b0" hash="c2bb4dc336816aceea1bcdcb630f86e90336389a3447e5e37381ac3ef1cb9ecd1a333408bed8794b2fdea86cd707e6ef23546818f98df1c9ec2209e673a2ad9d" />
import argparse
import os
import sys
import hashlib
import io

################################################################################

# These are various file extensions that the program expects to see.

WHITELIST = 'awk bas bat c cpp cs css h htm html java \
js lsp lua php pl py pyw sh sql svg ws wsa xml'.split()
GRAYLIST = 'bin stream'.split()
BLACKLIST = 'avi bmp divx flac flv gz img iso jpeg jpg m2v \
m4a mid mp3 mp4 ogg png swf tar tga tiff vob wav wma wmv zip'.split()

# These are specific to tag parsing and tag generation.

TAG_PREFIX = b'<source '
TAG_SUFFIX = b'/>'
EXPECTED = [b'name', b'size', b'hash']
NEWLINES = [b'\r\n', b'\r', b'\n']

BUFFER_SIZE = 1 << 12   # Applies to hashes.
MAX_SIZE = 1 << 20      # Applies to files.

################################################################################

# This is the main entry point for the program and action dispatcher.

def main():
    "Parse arguments and dispatch actions based on the choices."
    parser = argparse.ArgumentParser(description='Manage all source.')
    parser.add_argument('-v', '--version', action='version',
                        version='%(prog)s (version 1.0.0)')
    parser.add_argument('action', choices=('in', 'out', 'test'),
                        help='Procedure to be performed by program.')
    parser.add_argument('file', type=argparse.FileType('r+b', 0),
                        help='File to process using the procedure.')
    args = parser.parse_args()
    globals()['check_' + args.action](args.file)

################################################################################

# Checking in and out files dispatches to handlers with self-contained testing.

def check_in(file):
    "Check out the file before checking it back in while showing errors."
    try:
        ext = test_extension(file)
        tag = find_signature(file)
        if tag:
            globals()['check_out_' + ext](file)
        data, newline = find_newline(file)
        globals()['check_in_' + ext](file, data, newline)
        assert is_checked_in(file), 'Check in operation failed!'
        print('File has been signed into the system.')
    finally:
        file.close()

def check_out(file):
    "Check file out only if a tag could be found while showing errors."
    try:
        ext = test_extension(file)
        tag = find_signature(file)
        if not tag:
            print('File is not checked into the system.')
            sys.exit(14)
        globals()['check_out_' + ext](file)
        assert not is_checked_in(file), 'Check out operation failed!'
        print('File has been signed out of the system.')
    finally:
        file.close()

def check_test(file):
    "Find out if the file has a proper tag within the first 256 bytes."
    try:
        ext = test_extension(file, True)
        tag = find_signature(file)
        if not tag:
            print('Tag could not be found.')
            sys.exit(4)
        nsp = parse_id(tag)
        test_namespace(nsp, file)
        print('File has been signed into the system.')
    finally:
        file.close()

################################################################################

# Provide a sanity check so people do not test after checking a file.

def is_checked_in(file):
    "Test the file to see if it is checked into the system."
    file.seek(0)
    tag = find_signature(file)
    if tag:
        orig_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            nsp = parse_id(tag)
            test_namespace(nsp, file)
        except SystemExit:
            pass
        else:
            return True
        finally:
            sys.stdout = orig_stdout
    return False

################################################################################

# Find out if the file extension is okay and find a probably signature.

def test_extension(file_or_path, allow_graylist=False):
    "Test the file's extension to find out what category it is in."
    name = file_or_path if isinstance(file_or_path, str) else file_or_path.name
    ext = os.path.splitext(name)[1][1:].lower()
    if not (ext in WHITELIST or allow_graylist and ext in GRAYLIST):
        print('"{}" files '.format(ext), end='')
        if ext in GRAYLIST:
            print('are not yet supported.')
        elif ext in BLACKLIST:
            print('will never be supported.')
        else:
            print('are not yet recognized.')
        sys.exit(3)
    return ext

def find_signature(file, prefix=TAG_PREFIX, suffix=TAG_SUFFIX):
    "Try to find the probable signature for the given file."
    block = file.read(256)
    start = block.find(prefix)
    if start != -1:
        end = block.find(suffix, start)
        if end != -1:
            end += len(suffix)
            file.seek(end)
            return block[start:end]
    return b''

################################################################################

# Allow the signature/tag to be parsed and verify the attribute namespace.

def parse_id(tag):
    "Generate a namespace based on attributes within the source signature."
    attributes = tag[len(TAG_PREFIX):-len(TAG_SUFFIX)]
    expected = EXPECTED[:]
    namespace = {}
    while expected:
        for name in expected:
            key = name + b'="'
            if attributes.startswith(key):
                break
        else:
            print('Tag is not properly formed.')
            sys.exit(5)
        expected.remove(name)
        attributes = attributes[len(key):]
        index = attributes.find(b'"')
        if index == -1:
            print('Tag is not properly formed.')
            sys.exit(6)
        namespace[name] = attributes[:index]
        attributes = attributes[index:]
        if not attributes.startswith(b'" '):
            print('Tag is not properly formed.')
            sys.exit(7)
        attributes = attributes[2:]
    if attributes:
        print('Tag is not properly formed.')
        sys.exit(8)
    return namespace

def test_namespace(nsp, file):
    "Test the file for correctness based on it's signature namespace."
    if nsp[b'name'] != os.path.basename(file.name).encode():
        print('Tag filename is not correct.')
        sys.exit(9)
    if nsp[b'hash'] != get_sha512_hash(file):
        print('Tag hashcode is not correct.')
        sys.exit(10)
    if get_size(nsp) != file.tell():
        print('Tag filesize is not correct.')
        sys.exit(13)

################################################################################

# Provide help for testing a file's signature attribute namespace.

def get_sha512_hash(file):
    "Caculate the SHA-512 hash of the file following its signature."
    hasher = hashlib.sha512()
    buffer = file.read(BUFFER_SIZE)
    while buffer:
        hasher.update(buffer)
        buffer = file.read(BUFFER_SIZE)
    return hasher.hexdigest().encode()

def get_size(nsp):
    "Verify and parse the size contained with the attribute namespace."
    size = nsp[b'size']
    if len(size) != 5:
        print('Tag filesize is not properly formatted.')
        sys.exit(11)
    try:
        size = int(size, 16)
    except ValueError:
        print('Tag filesize is not a base 16 number.')
        sys.exit(12)
    else:
        return size

################################################################################

# Any helper function for checking in files should be added here.

def find_newline(file):
    "Check the file size and try figuring out the correct newline character."
    file.seek(0, os.SEEK_END)
    if file.tell() > MAX_SIZE:
        print('File is too large to be checked into the system.')
        sys.exit(15)
    file.seek(0)
    data = file.read()
    file.seek(0)
    for newline in NEWLINES:
        if newline in data:
            return data, newline
    return data, NEWLINES[0]

def check_file_in(file, data, tag_prefix, tag_suffix):
    "Caculate the size, signature with hash, the final file state."
    name = os.path.basename(file.name).encode()
    size = calculate_filesize(name, data, tag_prefix, tag_suffix)
    tag = create_tag(name, size, data, tag_suffix)
    file.write(tag_prefix + tag + tag_suffix + data)

def calculate_filesize(name, data, tag_prefix, tag_suffix):
    "Figure out what the file size will be and check against maximum."
    size = 167 + sum(map(len, (name, data, tag_prefix, tag_suffix)))
    if size > MAX_SIZE:
        print('File is too large to be checked into the system.')
        sys.exit(16)
    return size

def create_tag(name, size, data, tag_suffix):
    "Just create the <source name= ... /> byte string for file."
    hash_code = create_sha512_hash(tag_suffix + data)
    file_size = '{:05x}'.format(size).encode()
    return b'<source name="' + name + \
           b'" size="' + file_size + \
           b'" hash="' + hash_code + b'" />'

def create_sha512_hash(data):
    "Caculate the SHA-512 has for the data and the tag suffix (data prefix)."
    hasher = hashlib.sha512()
    for index in range(0, len(data), BUFFER_SIZE):
        buffer = data[index:index+BUFFER_SIZE]
        hasher.update(buffer)
    return hasher.hexdigest().encode()

################################################################################

# Add file handlers for checking in different file formats here.

def check_in_py(file, data, newline):
    "Specify a prefix and suffix for the signature and encode the file."
    tag_prefix = b'# '
    tag_suffix = newline
    check_file_in(file, data, tag_prefix, tag_suffix)

check_in_pyw = check_in_py
check_in_awk = check_in_py
check_in_wsa = check_in_py
check_in_sh = check_in_py

def check_in_c(file, data, newline):
    "Create a comment's beginning and ending to encode the file with."
    tag_prefix = b'/*' + newline + b' * '
    tag_suffix = newline + b' */' + newline
    check_file_in(file, data, tag_prefix, tag_suffix)

check_in_css = check_in_c
check_in_h = check_in_c

def check_in_html(file, data, newline):
    "Create a HTML comment's start and finish and encode file with them."
    tag_prefix = b'<!-- '
    tag_suffix = b' -->' + newline
    check_file_in(file, data, tag_prefix, tag_suffix)

check_in_htm = check_in_html
check_in_xml = check_in_html
check_in_svg = check_in_html

def check_in_cpp(file, data, newline):
    "Create a double-slash comment and end the signature with a newline."
    tag_prefix = b'// '
    tag_suffix = newline
    check_file_in(file, data, tag_prefix, tag_suffix)

check_in_js = check_in_cpp
check_in_java = check_in_cpp

def check_in_bas(file, data, newline):
    "Create a Basic style comment and finish the tag with a newline."
    tag_prefix = b"' "
    tag_suffix = newline
    check_file_in(file, data, tag_prefix, tag_suffix)

def check_in_php(file, data, newline):
    "Create a PHP code block and comment, and end the PHP code block."
    tag_prefix = b'<?php' + newline + b'// '
    tag_suffix = newline + b'?>' + newline
    check_file_in(file, data, tag_prefix, tag_suffix)

def check_in_bat(file, data, newline):
    "Label the signature, end with a newline, and write the tag to file."
    tag_prefix = b':: '
    tag_suffix = newline
    check_file_in(file, data, tag_prefix, tag_suffix)

def check_in_ws(file, data, newline):
    "Let the tag push a zero, pop the zero, and write the signature."
    tag_prefix = b''
    tag_suffix = newline + b' ' + newline + newline
    check_file_in(file, data, tag_prefix, tag_suffix)

def check_in_lua(file, data, newline):
    "Lua comments start with -- and end with the line, so comment the tag."
    tag_prefix = b'-- '
    tag_suffix = newline
    check_file_in(file, data, tag_prefix, tag_suffix)

check_in_sql = check_in_lua

def check_in_lsp(file, data, newline):
    "Comment out the signature with a semicolon and write the file."
    tag_prefix = b'; '
    tag_suffix = newline
    check_file_in(file, data, tag_prefix, tag_suffix)

def check_in_pl(file, data, newline):
    "Guess as to the file type and generate the tag prefix accordingly."
    tag_prefix = guess_perl_or_prolog(data.split(newline))
    tag_suffix = newline
    check_file_in(file, data, tag_prefix, tag_suffix)

def check_in_cs(file, data, newline):
    "Comment out the XML with an C# comment specifically designed for C#."
    tag_prefix = b'/// '
    tag_suffix = newline
    check_file_in(file, data, tag_prefix, tag_suffix)

################################################################################

# Language specific check in helpers should be placed in this section.

def guess_perl_or_prolog(lines):
    perl_score = prolog_score = 1
    for line in lines:
        tokens = line.split()
        if tokens:
            token = tokens[0]
            if token.startswith('#'):
                perl_score += 1
            elif token.startswith('%'):
                prolog_score += 1
    if perl_score / prolog_score >= 2:
        return b'# '
    elif prolog_score / perl_score >= 2:
        return b'% '
    else:
        print('Could not determine if source was Perl or Prolog.')
        sys.exit(18)

################################################################################

# Helper functions for checking out files go in this area.

def consume_newline(file):
    r"Try to read \r\n, \r, and \n newlines from file with correction."
    byte = file.read(1)
    if byte:
        if byte in (b'\r', b'\n'):
            if byte == b'\r':
                byte = file.read(1)
                if byte != b'\n':
                    file.seek(-1, os.SEEK_CUR)
        else:
            file_check_out_error(17)

def file_check_out_error(status):
    "Print out an error message before exiting program with status."
    print('File does not appear to be marked properly.')
    sys.exit(status)

def check_file_out(file):
    "Read all remaining data and write to file starting at beginning."
    data = file.read()
    file.seek(0)
    file.write(data)
    file.truncate()

def consume_chars(file, characters, status):
    "Get some expected characters from a file and check for validity."
    assert isinstance(characters, bytes), 'Characters should be bytes!'
    if file.read(len(characters)) != characters:
        file_check_out_error(status)

def consume_pattern(file, pattern, status):
    "Take in a required pattern, extract it from the file, and verify."
    pattern = pattern.replace(b'\r\n', b'\n').replace(b'\r', b'\n')
    head, *tail = pattern.split(b'\n')
    consume_chars(file, head, status)
    for pattern in tail:
        consume_newline(file)
        consume_chars(file, pattern, status)

################################################################################

# All check_out_[ext] functions should be placed in this area.

def check_out_py(file):
    "Check out a Python file by removing the tag and tag suffix."
    consume_newline(file)
    check_file_out(file)

check_out_pyw = check_out_py
check_out_cpp = check_out_py
check_out_js = check_out_py
check_out_awk = check_out_py
check_out_bas = check_out_py
check_out_java = check_out_py
check_out_wsa = check_out_py
check_out_bat = check_out_py
check_out_sh = check_out_py
check_out_lua = check_out_py
check_out_sql = check_out_py
check_out_lsp = check_out_py
check_out_pl = check_out_py
check_out_cs = check_out_py

def check_out_c(file):
    "Remove the remaining part of the comment before checking out."
    consume_pattern(file, b'\n */\n', 19)
    check_file_out(file)

check_out_css = check_out_c
check_out_h = check_out_c

def check_out_html(file):
    "Remove the remaining HTML comment and newline before checking out."
    consume_pattern(file, b' -->\n', 20)
    check_file_out(file)

check_out_htm = check_out_html
check_out_xml = check_out_html
check_out_svg = check_out_html

def check_out_php(file):
    "Remove newline, PHP ending code, and newline before checking file out."
    consume_pattern(file, b'\n?>\n', 21)
    check_file_out(file)

def check_out_ws(file):
    "Remove the zero's end and pop instruction before finshing check out."
    consume_pattern(file, b'\n \n\n', 22)
    check_file_out(file)

################################################################################

if __name__ == '__main__':
    main()
