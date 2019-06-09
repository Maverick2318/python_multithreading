#!/usr/bin/env python

import threading
import time

def sleep_thread(num):
    print 'Starting thread %s' % num
    time.sleep(1)
    print 'Exiting thread %x' % num
    return

def main():
    for i in range(5):
        t = threading.Thread(target=sleep_thread, args=(i,))
        t.start()

if __name__ == '__main__':
    main()
