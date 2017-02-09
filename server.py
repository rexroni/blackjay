import threading
import socketserver
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

def cleanup_server_temp_files(UID):
    os.remove('.blackjay/c2s'+UID+'.zip')
    os.remove('.blackjay/s2c'+UID+'.zip')
    shutil.rmtree('.blackjay/c2s'+UID+'')

class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):
    def handle(self):
        data = recv_all(self.request)
        cur_thread = threading.current_thread()
        response = 'you fucked up'
        if data == metadata_req_message:
            send_size(json.dumps(load_metadata(".blackjay/metadata")), self.request)
        elif data == prepare_message:
            send_size(prepare_response, self.request)
            UID = str(cur_thread.getName)
            zipfile = '.blackjay/c2s{}.zip'.format(UID)
            recv_file(zipfile, self.request)
            print("Like a boss")
            push, pull, conflicts = extract_client_to_server_archive(zipfile,UID)
            # right now, accept every acorn!
            resp_zipname = prep_server_to_client_archive(push, pull, conflicts, UID)
            send_file(resp_zipname, self.request)
            make_server_updates_live(push,UID)
            cleanup_server_temp_files(UID)
        else:
            send_size('you fucked up', self.request)
        self.request.close()

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

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

    server = ThreadedTCPServer((HOST, PORT), ThreadedTCPRequestHandler)
    with server:
        ip, port = server.server_address
        print("Server running at hostname: {}, ip: {}, port: {}".format(HOST,ip, port))

        # Start a thread with the server -- that thread will then start one
        # more thread for each request
        server_thread = threading.Thread(target=server.serve_forever)
        # Exit the server thread when the main thread terminates
        server_thread.daemon = True
        server_thread.start()
        print("Server loop running in thread:", server_thread.name)

        # meta = metadata_req(ip, port)
        # print("metadata: {}".format(meta))

        #push_update(ip, port, "trash.zip")
        #push_update(ip, port, "trash.zip")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Shutting down")

        server.shutdown()

if __name__ == "__main__":
    main()
