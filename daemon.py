import os
import sys
import time
import logging
from watchdog.observers import Observer
import watchdog.events
from watchdog.events import LoggingEventHandler,FileSystemEventHandler
from time import time, sleep

import client
from ignore import *

remotepath = None

def catch_update(self,event):
    global remotepath
    if type(event) == watchdog.events.DirModifiedEvent: return
    if should_ignore(event.src_path,load_ignore_patterns()): return
    print('syncing due to',event.src_path)
    client.synchronize(remotepath)

def watch_files():
    logger = LoggingEventHandler()

    handler = FileSystemEventHandler
    #handler.on_created = catch_update
    handler.on_modified = catch_update
    handler.on_deleted = catch_update
    handler.on_moved = catch_update

    observer = Observer()
    observer.schedule(handler, '.', recursive=True)
    observer.start()
    try:
        while True:
            sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    # first form
    if len(sys.argv) == 2:
        remotepath = os.path.abspath(sys.argv[1])
    # second form
    elif len(sys.argv) == 3:
        remotepath = os.path.abspath(sys.argv[2])
        os.chdir(sys.argv[1])
    else:
        print('usage:    python daemon.py <server location>')
        print('          python daemon.py <local location> <server location>')
        exit(1)

    # check for startup situations
    if os.path.isdir('.blackjay') is not True:
        if len(os.listdir()) == 0:
            print('looks like a new installation.  Initializing...')
            os.mkdir('.blackjay')
            open('.blackjay/metadata','a').close()
            # start with sane defaults in ignore file
            ignf = open('.blackjay/ignore','w')
            ignf.write(default_ignore_file)
            ignf.close()
        else:
            print('looks like restoring an old installation...')
            print('... I don\'t know how to do that yet!!')
            exit(1)
    # start watching files
    watch_files()


