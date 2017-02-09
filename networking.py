import socket
import os

metadata_req_message = b"gimme the metadata"
prepare_message = b"prepare to receive all my acorns"
prepare_response = b"send your worst"

def recv_all(sock):
    total_len = 0; payload_data = b''; size = 0
    size_data = sock_data = b''
    len_data = b''; len_size = 0
    # get the length field size
    while not len_size:
        sock_data = sock.recv(1)
        if len(sock_data)>0:
            len_size = sock_data[0]

    # get the length field
    while len(len_data) < len_size:
        len_data += sock.recv(len_size-len(len_data))
        if len(len_data) == len_size:
            size = int(len_data[:len_size])

    # get the data
    while len(payload_data) < size:
        payload_data += sock.recv(min(size-total_len, 65536))

    return payload_data

def send_file(filename, sock):
    size = str(os.stat(filename).st_size)
    print("send_file: file size: {}".format(size), flush=True)
    with open(filename, 'rb') as f:
        send_size(size, sock)
        data = f.read(65536)
        while data:
            send_size(data, sock)
            data = f.read(65536)

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
    print("recv_file: {}, size: {}".format(filename,size), flush=True)
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
        print("Trying to connect on : {}".format((ip,port)))
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
            recv_file('.blackjay/s2c.zip', sock)

        sock.close()
