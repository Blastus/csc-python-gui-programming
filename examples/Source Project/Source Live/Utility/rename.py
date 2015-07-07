# <source name="rename.py" size="00292" hash="8190a69716fb3d31247e0f8a72ec0ce8c7bc2c0586b6bb334539e963135adf7e0a69113cda4cab07e021689d799871b9f093aa20e320a4419d241619e53e1496" />
import os
import sys

NAMES = {'χερμενεύς 1.1.py': 'Hermeneus.py',
         'Hermeneus.py': 'χερμενεύς 1.1.py',
         'χερμενεύς 1.1.pyw': 'Hermeneus.pyw',
         'Hermeneus.pyw': 'χερμενεύς 1.1.pyw'}

def main():
    paths = os.listdir(os.path.dirname(sys.argv[0]))
    for key, value in NAMES.items():
        if key in paths:
            os.rename(key, value)
            break

if __name__ == '__main__':
    main()
