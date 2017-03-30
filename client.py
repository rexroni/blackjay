import os
import socket
import sys
import json
import stat
import shutil
import sshtunnel
import threading
import bcrypt
import traceback
from time import sleep
from watchdog.observers import Observer
import watchdog.events
from watchdog.events import FileSystemEventHandler
from pprint import pprint
from zipfile import ZipFile

from ignore import *
from metadata import *
from file_encryption import *
from networking import *
from config import get_config

global_ip = '127.0.0.1'
global_port = 0
config = None
tunnel = None
global_mutex = threading.Lock()

# here, (push, pull, conflicts) is generated by comparing local and remote metadata
def prep_client_to_server_archive(push, pull, conflicts, password):
    # now prep the zip archive
    with ZipFile('.blackjay/c2s.zip','w') as z:
        z.writestr('.blackjay/push',json.dumps(push,indent='    '))
        z.writestr('.blackjay/pull',json.dumps(pull,indent='    '))
        z.writestr('.blackjay/conflicts',json.dumps(conflicts,indent='    '))
        for name,meta in push.items():
            if meta['del_flag'] is False:
                iv = gen_iv(name,meta['mtime'])
                tempname = '.blackjay/encrypt.temp'
                encrypt_file(name,tempname,iv,password)
                z.write(tempname,arcname=name)
                os.remove(tempname)

def extract_server_to_client_archive():
    # make the resp directory
    tempdir = '.blackjay/s2c'
    if os.path.exists(tempdir): shutil.rmtree(tempdir)
    os.mkdir(tempdir)
    # extract the zip file
    with ZipFile('.blackjay/s2c.zip','r') as z:
        z.extractall(tempdir)
    push = load_metadata(tempdir+'/.blackjay/push')
    pull = load_metadata(tempdir+'/.blackjay/pull')
    conflicts = load_metadata(tempdir+'/.blackjay/conflicts')
    return push, pull, conflicts

def make_client_updates_live(push,pull,conflicts,password):
    local_meta = load_metadata('.blackjay/metadata')
    # for pushes which were accepted, update local metadata
    for name,meta in push.items():
        local_meta[name] = meta
    # for pulls which were accepted, move file and update local metadata
    for name,meta in pull.items():
        local_meta[name] = meta
        if meta['del_flag'] is False:
            tempname = '.blackjay/decrypt.temp'
            iv = gen_iv(name,meta['mtime'])
            decrypt_file('.blackjay/s2c/'+name,tempname,iv,password)
            # verify hmac before overwriting local file
            if(meta['hmac'] == get_hmac(tempname,password)):
                # make folders if necessary
                p,f = os.path.split(name)
                os.makedirs(p, exist_ok=True)
                # move the temporary file
                os.rename(tempname,name)
            else:
                print('----------------------------------------------')
                print('!!!!!!!!!!!!!HMAC DID NOT MATCH!!!!!!!!!!!!!!!')
                print('----------------------------------------------')
        else:
            # delete files marked for deletions
            p,f = os.path.split(name)
            # delete the files
            os.remove(name)
            # prune empty folders if necessary
            try:
                os.removedirs(p)
            except OSError:
                pass
    # for conflicts, move file to conflict-styled name
    for name,meta in conflicts.items():
        local_meta[name] = meta
        cname = conflict_name(name)
        tempname = '.blackjay/decrypt.temp'
        iv = gen_iv(name,meta['mtime'])
        decrypt_file('.blackjay/s2c/'+name,tempname,iv,password)
        # verify hmac before copying to local file
        if(meta['hmac'] == get_hmac(tempname,password)):
            os.rename(tempname,cname)
            # make file read-only
            mode = os.stat(cname).st_mode
            os.chmod(cname, mode & ~(stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH))
        else:
            print('----------------------------------------------')
            print('!!!!!!!!!!!!!HMAC DID NOT MATCH!!!!!!!!!!!!!!!')
            print('----------------------------------------------')
    write_metadata(local_meta,'.blackjay/metadata')

def cleanup_client_temp_files():
    os.remove('.blackjay/c2s.zip')
    os.remove('.blackjay/s2c.zip')
    shutil.rmtree('.blackjay/s2c')

def get_remote_metadata(ip,port):
    return json.loads(metadata_req(ip,port))

def synchronize(force_pull=False):
    global global_ip, global_port, config, global_mutex
    global metadata_req_message, prepare_message, prepare_response
    # if another event's synchronize is occuring... just exit
    if global_mutex.acquire(blocking=False) == False:
        print('quitting due to locked mutex')
        return
    try:
        # debounce timeout
        sleep(.3)
        local_meta, immediate_updates, any_updates = get_updated_local_metadata()
        # if there's immediate updates (like a new latest md5sum or mtime), save to disk
        if len(immediate_updates) > 0:
            temp_meta = load_metadata('.blackjay/metadata')
            for name,meta_entry in immediate_updates.items():
                temp_meta[name] = meta_entry
            write_metadata(temp_meta,'.blackjay/metadata')
        print('any updates?',any_updates)
        if any_updates is False and force_pull is False:
            global_mutex.release()
            return
        # update the tunnel
        if tunnel is not None and tunnel.is_alive is False:
            print('restarting tunnel, but I never ever see this run')
            tunnel.stop()
            tunnel.restart()
        # open a persistent socket (simpler this way, for now)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            print("Trying to connect on : {}".format((global_ip,global_port)))
            sock.connect((global_ip,global_port))
            # send salt request message
            send_size(salt_req_message,sock)
            # recieve salt
            salt = recv_all(sock)
            # send hashed password with salt
            hashed_password = bcrypt.hashpw(config['password'],salt)
            send_size(hashed_password, sock)
            # now receive metadata
            meta_or_wrong_password = recv_all(sock)
            if meta_or_wrong_password == wrong_password_message:
                raise ValueError('Password does not match remote store')
            remote_meta = json.loads(meta_or_wrong_password.decode('utf8'))
            #remote_meta = get_remote_metadata(global_ip,global_port)
            # examine remote metadata
            push, pull, conflicts = compare_metadata(local_meta,remote_meta)
            print('pushing',push)
            print('pulling',pull)
            print('conflicts',conflicts)
            push = add_hmacs_to_metadata(push, config['password'])
            prep_client_to_server_archive(push, pull, conflicts, config['password'])
            print('pushing update')
            #push_update(global_ip,global_port,'.blackjay/c2s.zip')
            send_file('.blackjay/c2s.zip', sock)
            recv_file('.blackjay/s2c.zip', sock)
            sock.shutdown(socket.SHUT_RDWR)
            sock.close()
            # now examine response
            print('extracting s2c')
            npush, npull, nconfl = extract_server_to_client_archive()
            print('pushing',npush)
            print('pulling',npull)
            print('conflicts',nconfl)
            make_client_updates_live(npush,npull,nconfl,config['password'])
            cleanup_client_temp_files()
    except:
        traceback.print_exc()
        # try restarting the ssh tunnel
        if tunnel is not None:
            print('restarting tunnel, in case that helps')
            try:
                tunnel.stop()
                tunnel.restart()
                global_port = tunnel.local_bind_port
            except:
                pass


    global_mutex.release()


class SyncHandler(FileSystemEventHandler):
    def __init__(self):
        super()
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
        # pprint( (event.src_path, event.event_type) ) # print now only for degug

        if type(event) == watchdog.events.DirModifiedEvent:
            #print('ignoring dir modified event')
            return
        # now skip anything that matches ignore patterns, except deleting a server_version file
        event_filename = event.src_path.replace(os.path.sep,'/')
        if should_ignore(event_filename, ['/.*\.server_copy[^/]*']) \
          and event.event_type == 'deleted':
            pass
        elif should_ignore(event_filename,load_ignore_patterns()):
            #print('ignoring file: ',event.src_path)
            return
        print('syncing due to',event_filename)
        synchronize()
        print('')

def main():
    global config, tunnel, global_ip, global_port
    if len(sys.argv) == 2:
        os.chdir(sys.argv[1])
    else:
        print('usage:    python client.py <local location>')
        exit(1)

    # load config file
    config = get_config()
    should_continue = True
    while should_continue:
        try:
            tunnel = None if config['host'] == 'localhost' \
                             or config['transport_security'] == 'None_PleaseAttackMeManInTheMiddle' \
                          else sshtunnel.SSHTunnelForwarder(config['host'],
                               remote_bind_address=('localhost',int(config['port'])),
                                       ssh_pkey=os.path.expanduser(config['ssh_pkey']))
            should_continue = False
        except:
            traceback.print_exc()
            print('tunnel creation failed, waiting 15 seconds to try again')
            sleep(15)

    if tunnel is not None:
        print("starting ssh tunnel")
        should_continue = True
        while should_continue:
            try:
                tunnel.start()
                should_continue = False
            except:
                traceback.print_exc()
                print('network failed, trying again in 15 seconds')
                sleep(15)
        global_ip = '127.0.0.1'
        global_port = tunnel.local_bind_port
    else:
        global_ip = config['host']
        global_port = int(config['port'])

    # start watching files
    print('Client running... watching for changes')
    observer = Observer()
    observer.schedule(SyncHandler(), '.', recursive=True)
    observer.start()
    seconds_passed = 0
    try:
        while True:
            sleep(1)
            seconds_passed += 1
            if seconds_passed == 15:
                seconds_passed = 0
                synchronize(force_pull=True)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

    #kill the ssh tunnel if it is active
    if tunnel and tunnel.is_active:
        tunnel.stop()

if __name__ == "__main__":
    main()
