import os
import stat
import shutil
import json
from zipfile import ZipFile
from metadata import *
from file_encryption import *

# here, (push, pull, conflicts) is generated by comparing local and remote metadata
def prep_client_to_server_archive(push, pull, conflicts, password):
    # now prep the zip archive
    with ZipFile('.blackjay/c2s.zip','w') as z:
        for name,meta in push.items():
            if meta['del_flag'] is False:
                push[name]['hmac'] = get_hmac(name, password)
                ### without encryption:
                tempname = name
                ### with encryption:
                # tempname = '.blackjay/temp_encrypted'
                # encrypt_file(name,tempname,password)
                z.write(tempname,arcname=name)
        # now that push is updated with hmacs, we write metadata into archive as well
        z.writestr('.blackjay/push',json.dumps(push,indent='    '))
        z.writestr('.blackjay/pull',json.dumps(pull,indent='    '))
        z.writestr('.blackjay/conflicts',json.dumps(conflicts,indent='    '))

def extract_client_to_server_archive(zipfile,UID):
    # make the temp directory
    tempdir = '.blackjay/c2s'+UID
    os.mkdir(tempdir)
    # extract the zip file
    with ZipFile(zipfile,'r') as z:
        z.extractall(tempdir)
    push = load_metadata(os.path.join(tempdir,'.blackjay/push'))
    pull = load_metadata(os.path.join(tempdir,'.blackjay/pull'))
    conflicts = load_metadata(os.path.join(tempdir,'.blackjay/conflicts'))
    return push, pull, conflicts

# now (push, pull, conflicts) are just those changes accepted by the server
def prep_server_to_client_archive(push, pull, conflicts, UID):
    # make a response directory
    zipname = '.blackjay/s2c'+UID+'.zip'
    # now prep the zip archive
    with ZipFile(zipname,'w') as z:
        z.writestr('.blackjay/push',json.dumps(push,indent='    '))
        z.writestr('.blackjay/pull',json.dumps(pull,indent='    '))
        z.writestr('.blackjay/conflicts',json.dumps(conflicts,indent='    '))
        for name,meta in pull.items():
            if meta['del_flag'] is False:
                z.write(name)
        for name,meta in conflicts.items():
            if meta['del_flag'] is False:
                z.write(name)
    return zipname

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

def make_server_updates_live(push,UID):
    local_meta = load_metadata('.blackjay/metadata')
    # for pushes which were accepted, update local metadata
    for name,meta in push.items():
        local_meta[name] = meta
        if meta['del_flag'] is False:
            os.rename(os.path.join('.blackjay/c2s'+UID,name),name)
    # for pulling from the server, no metadata changes
    # the server doesn't handle conflicts
    write_metadata(local_meta,'.blackjay/metadata')

def make_client_updates_live(push,pull,conflicts):
    local_meta = load_metadata('.blackjay/metadata')
    # for pushes which were accepted, update local metadata
    for name,meta in push.items():
        local_meta[name] = meta
    # for pulls which were accepted, move file and update local metadata
    for name,meta in pull.items():
        local_meta[name] = meta
        if meta['del_flag'] is False:
            os.rename(os.path.join('.blackjay/s2c',name),name)
    # for conflicts, move file to conflict-styled name
    for name,meta in conflicts.items():
        local_meta[name] = meta
        cname = conflict_name(name)
        os.rename(os.path.join('.blackjay/s2c',name),cname)
        # make file read-only
        mode = os.stat(cname).st_mode
        os.chmod(cname, mode & ~(stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH))
    write_metadata(local_meta,'.blackjay/metadata')

def cleanup_client_temp_files():
    os.remove('.blackjay/c2s.zip')
    os.remove('.blackjay/s2c.zip')
    shutil.rmtree('.blackjay/s2c')

def cleanup_server_temp_files(UID):
    os.remove('.blackjay/c2s'+UID+'.zip')
    os.remove('.blackjay/s2c'+UID+'.zip')
    shutil.rmtree('.blackjay/c2s'+UID+'')
