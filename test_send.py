import socket
import sys

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('localhost',12345))
with open(sys.argv[1],'rb') as f:
    data = f.read(1024)
    while data:
        print('.',end='',flush=True)
        sock.sendall(data)
        data = f.read(1024)
sock.close()

