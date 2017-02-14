import networking
import socket
import sys

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('localhost',12345))
networking.send_file(sys.argv[1],sock)
# known to work
#with open(sys.argv[1],'rb') as f:
#    data = bytearray(1024)
#    amount = f.readinto(data)
#    while amount > 0:
#        print('.',end='',flush=True)
#        sock.sendall(data[:amount])
#        amount = f.readinto(data)
#    sock.shutdown(socket.SHUT_RDWR)
sock.close()

