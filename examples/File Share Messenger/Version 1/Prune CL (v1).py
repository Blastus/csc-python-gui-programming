#! /usr/bin/env python3
import time
import os
import time

LIMIT = 60 * 60 # One Hour

def main():
    now = time.time()
    for name in os.listdir('CHAT LOGS\\V1'):
        path = os.path.join('CHAT LOGS\\V1', name)
        if os.path.isfile(path):
            with open(path) as file:
                user, clock, message = file.read().split('\n')[:3]
            if now - float(clock) > LIMIT:
                os.remove(path)
                print('REMOVED:', name)
    print('====\nDONE')
    time.sleep(5)

if __name__ == '__main__':
    #Temporarily disabled.
    #main()
