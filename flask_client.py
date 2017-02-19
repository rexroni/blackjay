import os
import socket
import sys
import json
import stat
import shutil
import sshtunnel
from time import sleep
from watchdog.observers import Observer
import watchdog.events
from watchdog.events import FileSystemEventHandler
from pprint import pprint
from zipfile import ZipFile
import requests
from requests_toolbelt import MultipartEncoder

from ignore import *
from metadata import *
from file_encryption import *
from config import get_config

global_host = '127.0.0.1'
global_port = 0
config = None
tunnel = None

# here, (push, pull, conflicts) is generated by comparing local and remote metadata
def prep_client_to_server_archive(push, pull, conflicts, password):
    # now prep the zip archive
    with ZipFile('.blackjay/c2s.zip','w') as z:
        z.writestr('.blackjay/push',json.dumps(push,indent=3))
        z.writestr('.blackjay/pull',json.dumps(pull,indent=3))
        z.writestr('.blackjay/conflicts',json.dumps(conflicts,indent=3))
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
    with ZipFile(os.path.join('.blackjay/s2c.zip'),'r') as z:
        z.extractall(tempdir)
    push = load_metadata(os.path.join(tempdir,'.blackjay/push'))
    pull = load_metadata(os.path.join(tempdir,'.blackjay/pull'))
    conflicts = load_metadata(os.path.join(tempdir,'.blackjay/conflicts'))
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
            decrypt_file(os.path.join('.blackjay/s2c',name),tempname,iv,password)
            # verify hmac before overwriting local file
            if(meta['hmac'] == get_hmac(tempname,password)):
                os.rename(tempname,name)
            else:
                print('----------------------------------------------')
                print('!!!!!!!!!!!!!HMAC DID NOT MATCH!!!!!!!!!!!!!!!')
                print('----------------------------------------------')
    # for conflicts, move file to conflict-styled name
    for name,meta in conflicts.items():
        local_meta[name] = meta
        cname = conflict_name(name)
        tempname = '.blackjay/decrypt.temp'
        iv = gen_iv(name,meta['mtime'])
        decrypt_file(os.path.join('.blackjay/s2c',name),tempname,iv,password)
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
    # os.remove('.blackjay/c2s.zip')
    os.remove('.blackjay/s2c.zip')
    shutil.rmtree('.blackjay/s2c')

def get_remote_metadata(host,port,server_path):
    metadata_req = requests.get('http://'+host+':'+str(port) \
            +'/'+server_path \
            +'/.blackjay/metadata')
    return json.loads(metadata_req.content)

def push_update(host,port,server_path,uid,filepath):
    url = 'http://'+host+':'+str(port)+'/'\
            +server_path+'/' \
            +'.blackjay/'+uid
    uploadfile = open(filepath, 'rb')
    payload = MultipartEncoder({uploadfile.name: (uploadfile.name, uploadfile, 'application/x-compressed')})
    update_req = requests.post(url, data=payload, headers={'Content-Type': payload.content_type})
    return update_req.contents

def synchronize(force_pull=False):
    # debounce timeout
    sleep(.3)
    global global_host, global_port, config
    local_meta, immediate_updates, any_updates = get_updated_local_metadata()
    # if there's immediate updates (like a new latest md5sum or mtime), save to disk
    if len(immediate_updates) > 0:
        temp_meta = load_metadata('.blackjay/metadata')
        for name,meta_entry in immediate_updates.items():
            temp_meta[name] = meta_entry
        write_metadata(temp_meta,'.blackjay/metadata')
    print('any updates?',any_updates)
    if any_updates is False and force_pull is False: return
    # update the tunnel
    if tunnel is not None and tunnel.is_alive is False:
        print('restarting tunnel')
        tunnel.restart()
    uid, remote_meta = get_remote_metadata(global_host,global_port,'.')
    push, pull, conflicts = compare_metadata(local_meta,remote_meta)
    print('pushing',push)
    print('pulling',pull)
    print('conflicts',conflicts)
    push = add_hmacs_to_metadata(push, config['password'])
    prep_client_to_server_archive(push, pull, conflicts, config['password'])
    print('pushing update')
    # update the tunnel
    if tunnel is not None and tunnel.is_alive is False:
        print('restarting tunnel')
        tunnel.restart()
    update_req = push_update(global_host,global_port,'.',uid,'.blackjay/c2s.zip')
    print(update_req)
    print('recieved files:',update_req.files)
    if 's2c.zip' not in update_req.files:
        print(request.files)
        #abort(400, message="No file in post request")
        abort(400)
    request.files['s2c.zip'].save('.blackjay/c2s.zip')
    # push_update will also recieve the response!
    print('extracting s2c')
    npush, npull, nconfl = extract_server_to_client_archive()
    print('pushing',npush)
    print('pulling',npull)
    print('conflicts',nconfl)
    make_client_updates_live(npush,npull,nconfl,config['password'])
    cleanup_client_temp_files()

class SyncHandler(FileSystemEventHandler):
    def __init__(self):
        super(SyncHandler, self).__init__()
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
        if should_ignore(event.src_path, ['/.*\.server_copy[^/]*']) \
          and event.event_type == 'deleted':
            pass
        elif should_ignore(event.src_path,load_ignore_patterns()):
            #print('ignoring file: ',event.src_path)
            return
        print('syncing due to',event.src_path)
        synchronize()
        print('')

def main():
    global config, tunnel, global_host, global_port
    if len(sys.argv) == 2:
        os.chdir(sys.argv[1])
    else:
        print('usage:    python client.py <local location>')
        exit(1)

    # load config file
    config = get_config()
    tunnel = None if config['host'] == 'localhost' \
                  else sshtunnel.SSHTunnelForwarder(config['host'],
                       remote_bind_address=('localhost',int(config['port'])),
                       ssh_pkey='/home/rdbeethe/.ssh/id_rsa')

    if config['host'] != 'localhost':
        print("starting ssh tunnel")
        tunnel.start()
        global_port = tunnel.local_bind_port
        print(tunnel.tunnel_is_up)
    else:
        global_host = '127.0.0.1'
        global_port = int(config['port'])

    # start watching files
    print('Client running... watching for changes')
    observer = Observer()
    observer.schedule(SyncHandler(), '.', recursive=True)
    observer.start()
    try:
        while True:
            sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

    #kill the ssh tunnel if it is active
    if tunnel and tunnel.is_active:
        tunnel.stop()

if __name__ == "__main__":
    main()
