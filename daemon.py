import os
import sys
import time
import logging
from watchdog.observers import Observer
import watchdog.events
from watchdog.events import LoggingEventHandler,FileSystemEventHandler
from time import time, sleep
from pprint import pprint

import client
from ignore import *

class SyncHandler(FileSystemEventHandler):
    def __init__(self, remotepath):
        super()
        self.remotepath = remotepath
        self.on_modified = self.process
        self.on_deleted = self.process
        self.on_modified = self.process
        self.on_created = self.process

    def process(self, event):
        """
        event.event_type 
            'modified' | 'created' | 'moved' | 'deleted'
        event.is_directory
            True | False
        event.src_path
            path/to/observed/file
        """
        # the file will be processed there
        pprint( (event.src_path, event.event_type) ) # print now only for degug

        if type(event) == watchdog.events.DirModifiedEvent: 
            print('ignoring dir modified event')
            return
        if should_ignore(event.src_path,load_ignore_patterns()): 
            print('ignoring file: ',event.src_path)
            return
        print('syncing due to',event.src_path)
        client.synchronize(self.remotepath)
        print('sync finished')


if __name__ == "__main__":
    # first form
    remotepath = ''
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
    if os.path.isdir('.encrynize') is not True:
        if len(os.listdir()) == 0:
            print('looks like a new installation.  Initializing...')
            os.mkdir('.encrynize')
            open('.encrynize/metadata','a').close()
            # start with sane defaults in ignore file
            ignf = open('.encrynize/ignore','w')
            ignf.write(default_ignore_file)
            ignf.close()
        else:
            print('looks like restoring an old installation...')
            print('... I don\'t know how to do that yet!!')
            exit(1)
    
    # start watching files
    observer = Observer()
    observer.schedule(SyncHandler(remotepath), '.', recursive=True)
    observer.start()
    try:
        while True:
            sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


