import os
import socket
import sys
import shutil
from metadata import *

def get_remote_metadata(remoteroot):
    remotename = os.path.join(remoteroot,'.blackjay/metadata')
    return load_metadata(remotename)

# I actually think that pushing and pulling whole zip archives
# would be an awful lot easier than doing one-file at a time
def push_file(remoteroot,name):
    localname = name
    remotename = os.path.join(remoteroot,name)
    shutil.copy2(localname,remotename)

def pull_file(remoteroot,name):
    localname = name
    remotename = os.path.join(remoteroot,name)
    shutil.copy2(remotename,localname)

# really this should be run as a batch of changes, not a single change
def push_metadata_update(remoteroot,name,meta):
    # first update the remote metadata
    remotename = os.path.join(remoteroot,'.blackjay/metadata')
    remote_meta = load_metadata(remotename)
    remote_meta[name] = meta
    write_metadata(remote_meta,remotename)
    # then update the local metadata, following the sync
    local_meta = load_metadata('.blackjay/metadata')
    local_meta[name] = meta
    write_metadata(local_meta,'.blackjay/metadata')

def delete_local(name):
    if os.path.exists(name):
        os.remove(name)

def delete_remote(remoteroot,name):
    remotename = os.path.join(remoteroot,'.blackjay/metadata')

def synchronize(remoteroot,force_pull=False):
    local_meta, any_updates = get_updated_local_metadata()
    print('any updates?',any_updates)
    if any_updates is False and force_pull is False: return
    remote_meta = get_remote_metadata(remoteroot)
    push, pull, conflicts = compare_metadata(local_meta,remote_meta)
    print('pushing',push)
    print('pulling',pull)
    print('conflicts',conflicts)
    write_metadata(push,'../expush')
    write_metadata(pull,'../expull')
    write_metadata(conflicts,'../exconflicts')
    for name,meta in push.items():
        if meta['del_flag'] is True:
            delete_remote(remoteroot,name)
        else:
            push_file(remoteroot,name)
        push_metadata_update(remoteroot,name,meta)
    for name,meta in pull.items():
        if meta['del_flag'] is True:
            delete_local(name)
        else:
            pull_file(remoteroot,name)
        local_meta[name] = meta
    write_metadata(local_meta,'.blackjay/metadata')





## this was from the example, and will connect to server.py
def repeater_client():

    # Create a TCP/IP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Connect the socket to the port where the server is listening
    server_address = ('localhost', 10000)
    sys.stderr.write( 'connecting to %s port %s\n' % server_address)
    sock.connect(server_address)

    try:

        # Send data
        message = b'This is the message.  It will be repeated.'
        sys.stderr.write( 'sending "%s"\n' % message)
        sock.sendall(message)

        # Look for the response
        amount_received = 0
        amount_expected = len(message)

        while amount_received < amount_expected:
            data = sock.recv(16)
            amount_received += len(data)
            sys.stderr.write( 'received "%s"\n' % data)

    finally:
        sys.stderr.write('closing socket\n')
        sock.close()

