import threading
import socket
import socketserver
import time
import sys
import struct
from metadata import *
import json
import sftp

metadata_req_message = b"gimme the mettadata"
prepare_message = b"prepare to receive all my acorns"
prepare_response = b"send your worst"

def recv_all(sock):
    total_len = 0; total_data = []; size = sys.maxsize
    size_data = sock_data = b''; recv_size = 8196
    len_data = b''; len_size = 0
    while total_len < size:
        sock_data = sock.recv(min(size-total_len, 2048))
        if not len_size:
            if len(sock_data)>1:
                len_size = sock_data[0]
                # print("Len of size field: {}".format(len_size))
                sock_data = sock_data[1:]
            else:
                continue

        if not total_data:
            if len(sock_data)>len_size:
                size_data += sock_data
                size = int(size_data[:len_size])
                # print("Received {} bytes".format(size))
                recv_size = size
                total_data.append(size_data[len_size:])
            else:
                size_data += sock_data
        else:
            total_data.append(sock_data)
        total_len=sum([len(i) for i in total_data])
    return b''.join(total_data)

def send_file(filename, sock):
    size = str(os.stat(filename).st_size)
    print("send_file: file size: {}".format(size))
    with open(filename, 'rb') as f:
        send_size(size, sock)
        data = f.read(2048) 
        while data:
            send_size(data, sock)
            data = f.read(2048) 

def progress_bar(completed, size):
    width = 60
    progress = completed/size
    progress_bar_width = width - 13
    num_equals = int(progress*progress_bar_width)
    num_space = int(progress_bar_width - num_equals)
    progress_bar = "="*num_equals + " "*num_space
    print("\r[{}] {:.2f}%".format(progress_bar, (progress*100)), end='')
    if completed == size:
        print("")

def recv_file(filename, sock):
    size = int(recv_all(sock))
    print("recv_file: file size: {}".format(size))
    read_size = 0

    with open(filename, 'wb') as f:
        while(read_size < size):
            data = recv_all(sock)
            f.write(data)
            read_size += len(data)
            progress_bar(read_size, size)

def send_size(data, sock):
    if type(data) is str:
        data = bytes(data, 'utf8')

    len_str = "{}".format(len(data))
    len_str_size = chr(len(len_str))
    send_data = bytes(len_str_size+len_str, 'ascii')+data
    sock.sendall(send_data)

def client_req(ip, port, message):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((ip, port))
        send_size(message, sock)
        response = recv_all(sock)
        sock.close()
        return response

def metadata_req(ip, port):
    global metadata_req_message
    return client_req(ip, port, metadata_req_message)

def push_update(ip, port, filename):
    global prepare_message
    global prepare_response
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((ip, port))
        send_size(prepare_message, sock)
        response = recv_all(sock)
        if response != prepare_response:
            print("yoohoo: NO NO NO NO")
            return False;
        else:
            send_file(filename, sock)

class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):
    def handle(self):
        data = recv_all(self.request)
        cur_thread = threading.current_thread()
        response = 'you fucked up'
        if data == metadata_req_message:
            send_size(json.dumps(load_metadata(".blackjay/metadata")), self.request)
        elif data == prepare_message:
            send_size(prepare_response, self.request)
            recv_file('.blackjay/c2s{}.zip'.format(cur_thread), self.request)
            print("Like a boss")
        else:
            send_size('you fucked up', self.request)
        self.request.close()

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

def main():
    if len(sys.argv) > 1:
        os.chdir(sys.argv[1])
    else:
        os.chdir("s")
    if os.path.isdir('.blackjay') is not True:
        if len(os.listdir()) == 0:
            print('looks like a new installation.  Initializing...')
            os.mkdir('.blackjay')
            os.mkdir('.blackjay/tmp')
            open('.blackjay/metadata','a').close()
        # else:
        #     print('looks like restoring an old installation...')
        #     print('... I don\'t know how to do that yet!!')
        #     exit(1)

    # Port 0 means to select an arbitrary unused port
    HOST, PORT = socket.gethostname(), 0

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

        meta = metadata_req(ip, port)
        print("metadata: {}".format(meta))

        push_update(ip, port, "trash.zip")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Shutting down")

        server.shutdown()

if __name__ == "__main__":
    main()