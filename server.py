import threading
import socket
import socketserver
import time
import sys
import struct
from metadata import *
import json

metadata_req_message = b"gimme the mettadata"

def recv_all(sock):
    total_len = 0; total_data = []; size = sys.maxsize
    size_data = sock_data = b''; recv_size = 8196
    len_data = b''; len_size = 0
    while total_len < size:
        sock_data = sock.recv(recv_size)
        if not len_size:
            if len(sock_data)>1:
                len_size = sock_data[0]
                print("Len of size field: {}".format(len_size))
                sock_data = sock_data[1:]
            else:
                continue

        if not total_data:
            if len(sock_data)>len_size:
                size_data += sock_data
                size = int(size_data[:len_size])
                print("Received {} bytes".format(size))
                recv_size = size
                total_data.append(size_data[len_size:])
            else:
                size_data += sock_data
        else:
            total_data.append(sock_data)
        total_len=sum([len(i) for i in total_data])
    return b''.join(total_data)


def send_size(data, sock):
    if type(data) is str:
        data = bytes(data, 'utf8')
    print("Sending {} bytes.".format(len(data)))
    print("Message: {}".format(data))

    len_str = "{}".format(len(data))
    len_str_size = chr(len(len_str))
    send_data = bytes(len_str_size+len_str, 'ascii')+data
    print(send_data)
    sock.sendall(send_data)

def client_req(ip, port, message):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((ip, port))
        send_size(message, sock)
        response = recv_all(sock).decode("utf8")
        sock.close()
        return response

def metadata_req(ip, port):
    global metadata_req_message
    return client_req(ip, port, metadata_req_message)

class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):

    def handle(self):
        data = recv_all(self.request)
        cur_thread = threading.current_thread()
        response = 'you fucked up'
        if data == metadata_req_message:
            response = json.dumps(load_metadata(".blackjay/metadata"))
        send_size(response, self.request)
        self.request.close()

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

def main():
    if len(sys.argv) > 1:
        os.chdir(sys.argv[1])
    if os.path.isdir('.blackjay') is not True:
        if len(os.listdir()) == 0:
            print('looks like a new installation.  Initializing...')
            os.mkdir('.blackjay')
            open('.blackjay/metadata','a').close()
        else:
            print('looks like restoring an old installation...')
            print('... I don\'t know how to do that yet!!')
            exit(1)

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

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Shutting down")

        server.shutdown()

if __name__ == "__main__":
    main()