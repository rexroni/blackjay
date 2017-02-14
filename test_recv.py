import socket
import threading

class handle_connection(threading.Thread):
    def __init__ ( self, conn):
       self.conn = conn
       threading.Thread.__init__ ( self )

    def run(self):
        print('connected by',conn)
        data = bytearray(1024)
        with open('recvd','wb') as f:
            amount = conn.recv_into(data)
            while amount > 0:
                print('.',end='',flush=True)
                f.write(data[:amount])
                amount = conn.recv_into(data)

sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
sock.bind(('',12345))
sock.listen(5)
while True:
    conn,addr = sock.accept()
    handle_connection(conn).start()
