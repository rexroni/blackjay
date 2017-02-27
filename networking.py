import socket
import os, sys

metadata_req_message = b"gimme the metadata"
prepare_message = b"prepare to receive all my acorns"
prepare_response = b"send your worst"

def recv_all(sock):
    payload_data = b''; size = 0
    len_data = b''; len_size = 0
    # get the length field size
    while len(len_data) < 1:
        len_data = sock.recv(1)

    len_size = ord(len_data)
    len_data = b''

    # get the length field
    while len(len_data) < len_size:
        len_data += sock.recv(len_size-len(len_data))

    size = int(len_data)

    # get the data
    while len(payload_data) < size:
        payload_data += sock.recv(min(size-len(payload_data), 2048))

    return payload_data

def send_file(filename, sock):
    size = str(os.stat(filename).st_size)
    print("send_file: file size: {}".format(size))
    sys.stdout.flush()
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
    sys.stdout.write("\r[{}] {:.2f}%".format(progress_bar, (progress*100)))
    if completed == size:
        print("")

def recv_file(filename, sock):
    size = int(recv_all(sock))
    print("recv_file: {}, size: {}".format(filename,size))
    sys.stdout.flush()
    read_size = 0

    with open(filename, 'wb') as f:
        while(read_size < size):
            data = recv_all(sock)
            f.write(data)
            read_size += len(data)
            progress_bar(read_size, size)

def send_size(data, sock):
    len_str = "{}".format(len(data))
    len_str_size = chr(len(len_str))
    send_data = bytes(len_str_size+len_str,'ascii')+data
    total_sent = 0
    total_len = len(send_data)
    while total_sent < total_len:
        data_sent = sock.send(send_data[total_sent:])
        total_sent += data_sent
    #sock.sendall(send_data)

def client_req(ip, port, message):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
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
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
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
