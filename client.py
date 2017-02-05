import os
import socket
import sys
import shutil
import server
import json
from metadata import *
from archiver import *

g_ip = '127.0.1.1'
g_po = 12345

def get_remote_metadata(ip,port):
    return json.loads(server.metadata_req(ip,port))

def synchronize(remoteroot,force_pull=False):
    global g_ip, g_po
    local_meta, any_updates = get_updated_local_metadata()
    print('any updates?',any_updates)
    if any_updates is False and force_pull is False: return
    remote_meta = get_remote_metadata(g_ip,g_po)
    push, pull, conflicts = compare_metadata(local_meta,remote_meta)
    print('pushing',push)
    print('pulling',pull)
    print('conflicts',conflicts)
    prep_client_to_server_archive(push, pull, conflicts)
    server.push_update(g_ip,g_po,'.blackjay/c2s.zip')
    # push_update will also recieve the response!
    npush, npull, nconfl = extract_server_to_client_archive()
    print('pushing',npush)
    print('pulling',npull)
    print('conflicts',nconfl)
    print('############:', push == npush and pull == npull and conflicts == nconfl)
    make_client_updates_live(npush,npull,nconfl)
    cleanup_client_temp_files()

