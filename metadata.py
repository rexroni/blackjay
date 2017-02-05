import json
import os
import hashlib
import re
from ignore import *

def hash_file(f):
    BLOCKSIZE = 65536
    hasher = hashlib.md5()
    ff = open(f, 'rb')
    buf = ff.read(BLOCKSIZE)
    while len(buf) > 0:
        hasher.update(buf)
        buf = ff.read(BLOCKSIZE)
    ff.close()
    return hasher.hexdigest()

def conflict_name(name):
    # mangles '.server_copy' after the name but before the extension
    return re.sub('((?:\.[^.]*)?$)','.server_copy\\1',name)

def write_metadata(meta,filename):
    f = open(filename,'w')
    json.dump(meta,f,indent='    ')
    f.close()

def load_metadata(filename):
    try:
        f = open(filename,'r')
        meta = json.load(f)
        f.close()
    except:
        meta = {}
    return meta

def get_updated_local_metadata():
    found_an_update = False
    ignore_patterns = load_ignore_patterns()
    meta = load_metadata('.blackjay/metadata')
    for root, dirs, files in os.walk('.'):
        for f in files:
            name = os.path.join(root,f)
            # ignore files that are already in our database
            meta_entry = meta.get(name,None)
            if meta_entry is not None:
                # check if this will become a local_update
                if os.stat(name).st_mtime != meta_entry['mtime']:
                    found_an_update = True
                continue
            # and ignore files that match ignore patterns
            if should_ignore(name,ignore_patterns):
                continue
            ### otherwise, we have a new file:
            found_an_update = True
            # "Hash At Last Sync"
            hals = 'never hashed'
            # mtime at last sync (not yet synced)
            mtime = 0
            meta[name] = { 'mtime':mtime,
                           'hals':hals,
                           'del_flag':False,
                           'was_confl':False,
                           'confl_mtime':0 }
    # check for deleted files
    for name in meta.keys():
        if os.path.exists(name) is False:
            meta[name]['del_flag'] = True
            found_an_update = True
    return meta, found_an_update

# all possible combinations of updates/deletions
# note that (update AND delete) on one file isn't possible
#   |    local    |   remote    |
#   |update|delete|update|delete| description
#   |------|------|------|------|---------------------------
# 1 |true  |false |   (none)    | new file, push to server
# 2 |false |false |false |false | do nothing
# 3 |false |false |false |true  | pull a deletion
# 4 |false |false |true  |false | pull from server
# 5 |false |true  |false |false | push a deletion
# 6 |false |true  |false |true  | do nothing
# 7 |false |true  |true  |false | pull from server
# 8 |true  |false |false |false | push to server
# 9 |true  |false |false |true  | push to server
# A |true  |false |true  |false | conflict!
# B |   (none)    |true  |false | new file, pull from server
# C |   (none)    |false |true  | file was pushed and deleted by another client,
#                                    pull metadata from server

def compare_metadata(localmeta,remotemeta):
    ignore_patterns = load_ignore_patterns()
    files_to_push = {}
    files_to_pull = {}
    conflicts = {}
    for name,local in localmeta.items():
        if should_ignore(name,ignore_patterns):
            continue
        # "local" and "remote" are metadata for this filename
        remote = remotemeta.get(name,None)
        if remote is None:
 #1         # this is a new file, push it
            local['mtime'] = os.stat(name).st_mtime
            local['hals'] = hash_file(name)
            files_to_push[name] = local
            continue
        local_delete = local['del_flag'] and not os.path.exists(name)
        remote_delete = remote['del_flag']
        # compare mod times to see what has been updated
        local_update = False if local_delete is True \
            else (os.stat(name).st_mtime != local['mtime'])
        remote_update = False if remote_delete is True \
            else (local['mtime'] != remote['mtime'])
### check conditions with two true's (6,7,9,A)
        if local_delete and remote_delete:
#6          # if both are deleted, then do nothing
            continue
        if local_delete and remote_update:
#7          # if there's a remote update, pull it from the server
            files_to_pull[name] = remote
            continue
        if local_update and remote_delete:
#9          # if there's a local update, push it back to the server
            local['mtime'] = os.stat(name).st_mtime
            local['hals'] = hash_file(name)
            files_to_push[name] = local
            continue
        if local_update and remote_update:
#A          # found a conflict, but this conflict could be in one of four states
            # new conflict (was_confl == false)
            # resume conflict (was_confl == true, conflict file exists)
            # resolve conflict (was_confl == true, conflict file removed)
            # another update to server while you were editing (ignore this for now)

            print('Conflict on %s'%(name))
            local['was_confl'] = True
            local['confl_mtime'] = remote['mtime']
            conflicts[name] = local
            continue
### check conditions with one true (3,4,5,8)
        if remote_delete:
#3          # pull a deletion
            files_to_pull[name] = remote
            continue
        if remote_update:
#4          # pull from server
            files_to_pull[name] = remote
            continue
        if local_delete:
#5          # push a deletion
            files_to_push[name] = local
            continue
        if local_update:
#8          # push to server
            local['mtime'] = os.stat(name).st_mtime
            local['hals'] = hash_file(name)
            files_to_push[name] = local
            continue
#2     # if all false, do nothing
#B,C: also check for new files at remote
    for name,remote in remotemeta.items():
        if localmeta.get(name,None) is None:
            files_to_pull[name] = remote
    return files_to_push, files_to_pull, conflicts

