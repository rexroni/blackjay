import socket
import threading

class handle_connection(threading.Thread):
    def __init__ ( self, conn):
       self.conn = conn
       threading.Thread.__init__ ( self )

    def run(self):
        print('connected by',conn)
        with open('recvd','wb') as f:
            data = conn.recv(1024)
            while data:
                print('.',end='',flush=True)
                f.write(data)
                data = conn.recv(1024)

sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
sock.bind(('',12345))
sock.listen(5)
while True:
    conn,addr = sock.accept()
    handle_connection(conn).start()
