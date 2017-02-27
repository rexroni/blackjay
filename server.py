import threading
import time
import sys
import json
import shutil
from zipfile import ZipFile

from metadata import *
from networking import *

def extract_client_to_server_archive(zipfile,UID):
    # make the temp directory
    tempdir = '.blackjay/c2s'+UID
    os.mkdir(tempdir)
    # extract the zip file
    with ZipFile(zipfile,'r') as z:
        z.extractall(tempdir)
    push = load_metadata(tempdir+'/.blackjay/push')
    pull = load_metadata(tempdir+'/.blackjay/pull')
    conflicts = load_metadata(tempdir+'/.blackjay/conflicts')
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

def make_server_updates_live(push,UID):
    local_meta = load_metadata('.blackjay/metadata')
    # for pushes which were accepted, update local metadata
    for name,meta in push.items():
        local_meta[name] = meta
        if meta['del_flag'] is False:
            os.rename('.blackjay/c2s'+UID+'/'+name,name)
    # for pulling from the server, no metadata changes
    # the server doesn't handle conflicts
    write_metadata(local_meta,'.blackjay/metadata')

def cleanup_server_temp_files(UID):
    os.remove('.blackjay/c2s'+UID+'.zip')
    os.remove('.blackjay/s2c'+UID+'.zip')
    shutil.rmtree('.blackjay/c2s'+UID+'')

class handle_connection(threading.Thread):
    def __init__ ( self, sock, mutex):
       self.sock = sock
       self.mutex = mutex
       threading.Thread.__init__ ( self )

    def run(self):
        self.mutex.acquire()
        try:
            data = recv_all(self.sock)
            if data == metadata_req_message:
                send_size(json.dumps(load_metadata(".blackjay/metadata")), self.sock)
                UID = str(time.time())
                zipfile = '.blackjay/c2s{}.zip'.format(UID)
                recv_file(zipfile, self.sock)
                print("Like a boss")
                push, pull, conflicts = extract_client_to_server_archive(zipfile,UID)
                # right now, accept every acorn!
                resp_zipname = prep_server_to_client_archive(push, pull, conflicts, UID)
                send_file(resp_zipname, self.sock)
                make_server_updates_live(push,UID)
                cleanup_server_temp_files(UID)
            else:
                send_size('you fucked up', self.sock)
            self.sock.close()
        except:
            pass
        self.mutex.release()

def main():
    serverport = 12345 # default value

    if len(sys.argv) > 1:
        os.chdir(sys.argv[1])
    if len(sys.argv) > 2:
        serverport = int(sys.argv[2])

    if os.path.isdir('.blackjay') is not True:
        if len(os.listdir()) == 0:
            print('looks like a new installation.  Initializing...')
            os.mkdir('.blackjay')
            os.mkdir('.blackjay/tmp')
            open('.blackjay/metadata','a').close()

    # Port 0 means to select an arbitrary unused port
    HOST, PORT = '', serverport
    listener = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    listener.bind((HOST,PORT))
    listener.listen(5)
    mutex = threading.Lock()
    try:
        while True:
            conn,addr = listener.accept()
            handle_connection(conn,mutex).start()
    except KeyboardInterrupt:
        print("Shutting down")




if __name__ == "__main__":
    main()
