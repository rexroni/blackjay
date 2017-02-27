import json
import os
import hashlib
import re
from ignore import *

def get_md5sum(f):
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
    return re.sub('((?:\.[^/.]*)?$)','.server_copy\\1',name)

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
    immediate_updates = {}
    for root, dirs, files in os.walk('.'):
        for f in files:
            name = os.path.join(root,f).replace(os.path.sep,'/')
            # ignore files that are already in our database
            meta_entry = meta.get(name,None)
            if meta_entry is not None and meta_entry['del_flag'] is False:
                # always set found_an_update if a server_copy was deleted
                if meta_entry['was_confl'] and os.path.exists(conflict_name(name)) is False:
                    found_an_update = True
                # check if this will become a local_update
                mtime = os.stat(name).st_mtime
                # first condition is, has it been touched since we last checked
                if mtime != meta_entry['mtime']:
                    # then make sure there's actually a change
                    md5sum_now = get_md5sum(name)
                    if md5sum_now == meta_entry['md5sum']:
                        # if it is not a change, just update the local database
                        meta_entry['mtime'] = mtime
                        immediate_updates[name] = meta_entry
                        meta[name] = meta_entry
                    else:
                        # if there is a change, change the md5sum
                        meta_entry['md5sum_now'] = md5sum_now
                        meta_entry['mtime'] = mtime
                        immediate_updates[name] = meta_entry
                        meta[name] = meta_entry
                        # handling updates on conlficted files is handled above
                        if meta_entry['was_confl'] is False:
                            found_an_update = True
                continue
            # and ignore files that match ignore patterns
            if should_ignore(name,ignore_patterns):
                continue
            ### otherwise, we have a new file:
            found_an_update = True
            # hmac and md5sum at last sync (not yet synced)
            hmac = 'none yet'
            md5sum = 'none yet'
            # md5sum_now is as-of-right-now, used for verifying difference between files
            mtime = os.stat(name).st_mtime
            md5sum_now = get_md5sum(name)
            # last touched lets us not re-md5sum files over and over if ...
            # ... they are touched but not synced
            meta[name] = { 'mtime':mtime,
                           'hmac':hmac,
                           'md5sum':md5sum,
                           'md5sum_now':md5sum_now,
                           'del_flag':False,
                           'was_confl':False,
                           'confl_md5sum':'none' }
    # check for deleted files
    for name in meta.keys():
        if os.path.exists(name) is False:
            meta[name]['del_flag'] = True
            found_an_update = True
    return meta, immediate_updates, found_an_update

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
            local['md5sum'] = local['md5sum_now']
            files_to_push[name] = local
            continue
        if local['del_flag'] and os.path.exists(name):
            local['del_flag'] = False
        local_delete = local['del_flag']
        remote_delete = remote['del_flag']
        # compare mod times to see what has been updated
        local_update = False if local_delete is True \
            else (local['md5sum_now'] != local['md5sum'])
        remote_update = False if remote_delete is True \
            else (local['md5sum'] != remote['md5sum'])
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
            local['md5sum'] = local['md5sum_now']
            files_to_push[name] = local
            continue
        if local_update and remote_update:
#A          # found a conflict, but this conflict could be in one of four states:
            print('Conflict on %s'%(name))
            # State 1) new conflict (was_confl == false)
            if local['was_confl'] is False:
                # add to conflicts list, we will pull it from the server
                # print('cstate 1')
                local['was_confl'] = True
                local['confl_md5sum'] = remote['md5sum']
                conflicts[name] = local
            # State 2) old conflict, no update (was_confl == true, conflict file exists)
            elif local['was_confl'] is True and os.path.exists(conflict_name(name)) is True:
                # no need to do anything until user deletes the server_version file
                # print('cstate 2')
                pass
            # State 3) resolve conflict (was_confl == true, conflict file removed)
            elif local['was_confl'] is True and os.path.exists(conflict_name(name)) is False:
                # Did the user deconflict against the most current version?
                if local['confl_md5sum'] == remote['md5sum']:
                    # print('cstate 3')
                    local['was_confl'] = False
                    local['confl_md5sum'] = 'none'
                    local['md5sum'] = local['md5sum_now']
                    files_to_push[name] = local
                else:
                    # print('cstate 4')
                    print('Oh no! you deconflicted against a version that is now old!')
                    print('sorry, you must deconflict again...')
                    # get ready to download another server version
                    local['was_confl'] = True
                    local['confl_md5sum'] = remote['md5sum']
                    conflicts[name] = local
            # State 4) another update to server while you were editing (ignore this for now)
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
            local['md5sum'] = 'deleted'
            files_to_push[name] = local
            continue
        if local_update:
#8          # push to server
            local['md5sum'] = local['md5sum_now']
            files_to_push[name] = local
            continue
#2     # if all false, do nothing
#B,C: also check for new files at remote
    for name,remote in remotemeta.items():
        if localmeta.get(name,None) is None:
            files_to_pull[name] = remote
    return files_to_push, files_to_pull, conflicts

