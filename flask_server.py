from flask import Flask, send_file, request, abort
import os
import sys
import json
import uuid
import shutil
from zipfile import ZipFile

from metadata import load_metadata, write_metadata

def extract_client_to_server_archive(base_dir, zipfile, UID):
    # make the temp directory
    tempdir = os.path.join(base_dir, '.blackjay/c2s'+UID)
    os.mkdir(tempdir)
    # extract the zip file
    with ZipFile(zipfile,'r') as z:
        z.extractall(tempdir)
    push = load_metadata(os.path.join(tempdir,'.blackjay/push'))
    pull = load_metadata(os.path.join(tempdir,'.blackjay/pull'))
    conflicts = load_metadata(os.path.join(tempdir,'.blackjay/conflicts'))
    return push, pull, conflicts

# now (push, pull, conflicts) are just those changes accepted by the server
def prep_server_to_client_archive(base_dir, push, pull, conflicts, UID):
    # make a response directory
    zipname = os.path.join(base_dir, '.blackjay/s2c'+UID+'.zip')
    # now prep the zip archive
    with ZipFile(zipname,'w') as z:
        z.writestr(os.path.join(base_dir,'.blackjay/push'),json.dumps(push,indent=3))
        z.writestr(os.path.join(base_dir,'.blackjay/pull'),json.dumps(pull,indent=3))
        z.writestr(os.path.join(base_dir,'.blackjay/conflicts'),json.dumps(conflicts,indent=3))
        for name,meta in pull.items():
            if meta['del_flag'] is False:
                z.write(os.path.join(base_dir, name))
        for name,meta in conflicts.items():
            if meta['del_flag'] is False:
                z.write(os.path.join(base_dir, name))
    return zipname

def make_server_updates_live(base_dir, push,UID):
    meta_filename = os.path.join(base_dir, '.blackjay/metadata')
    local_meta = load_metadata(meta_filename)
    # for pushes which were accepted, update local metadata
    for name,meta in push.items():
        local_meta[name] = meta
        dest_name = os.path.join(base_dir, name)
        source_name = os.path.join(base_dir, '.blackjay/c2s'+UID, name)
        if meta['del_flag'] is False:
            os.rename(source_name,dest_name)
    # for pulling from the server, no metadata changes
    # the server doesn't handle conflicts
    write_metadata(local_meta,meta_filename)

def cleanup_server_temp_files(base_dir, UID):
    os.remove(os.path.join(base_dir, '.blackjay/c2s'+UID+'.zip'))
    os.remove(os.path.join(base_dir, '.blackjay/s2c'+UID+'.zip'))
    shutil.rmtree(os.path.join(base_dir, '.blackjay/c2s'+UID))


## Flask server ####################################################

app = Flask(__name__)

@app.route('/<string:base_dir>/.blackjay/metadata', methods=['GET'])
def get_metadata(base_dir):
    # ignore basedir for now
    base_dir=''
    # check the blackjay folder exists
    blackjay_path = os.path.join(base_dir,'.blackjay')
    if os.path.isdir(os.path.join(base_dir, '.blackjay')) is False:
        #abort(404, message="Base Directory {} doesn't exist".format(base_dir))
        abort(404)
    # get random uid
    uid = str(uuid.uuid4())
    # make the uid folder, for future communications regarding this operation
    os.mkdir(os.path.join(blackjay_path,uid))
    # archive the local metadata folder for future comparisons
    # MUTEX LOCK
    shutil.copy(os.path.join(blackjay_path,'metadata'),
                os.path.join(blackjay_path,uid,'metadata'))
    # MUTEX UNLOCK
    meta = load_metadata(os.path.join(blackjay_path,uid,'metadata'))
    # send uid, metadata to client
    return json.dumps( (uid,meta) )

@app.route('/<string:base_dir>/.blackjay/<string:uid>', methods=['POST'])
def post_update(base_dir,uid):
    # ignore basedir for now
    base_dir=''
    print('REQUEST FILES:',request.files)
    if '.blackjay/c2s.zip' not in request.files:
        #abort(400, message="No file in post request")
        abort(400)
    if not os.path.isdir(os.path.join(base_dir, '.blackjay')):
        #abort(404, message="Base Directory {} doesn't exist".format(base_dir))
        abort(404)
    req_zipname = os.path.join(base_dir, '.blackjay/c2s{}.zip'.format(uid))
    request.files['.blackjay/c2s.zip'].save(req_zipname)
    push, pull, conflicts = extract_client_to_server_archive(base_dir,req_zipname,uid)
    resp_zipname = prep_server_to_client_archive(base_dir,push,pull,conflicts,uid)
    make_server_updates_live(base_dir,push,uid)
    resp_file = open(resp_zipname, 'r')
    cleanup_server_temp_files(base_dir,uid)
    return send_file(resp_file, mimetype='application/x-compressed')


def main():
    port = 12345 # default value
    host = '0.0.0.0' # externally visible server

    if len(sys.argv) > 1:
        os.chdir(sys.argv[1])
    if len(sys.argv) > 2:
        port = int(sys.argv[2])
    if len(sys.argv) > 3:
        host = sys.argv[3]

    app.run(host=host, port=port, debug=True)

if __name__ == '__main__':
    main()
