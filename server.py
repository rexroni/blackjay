import os
import sys
import socket

# this is the example repeater server
def repeater_server():
    sys.stderr.write( 'starting\n')

    # Create a TCP/IP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Bind the socket to the port
    server_address = ('localhost', 10000)
    sys.stderr.write( 'starting up on %s port %s\n' % server_address)
    sock.bind(server_address)

    # Listen for incoming connections
    sock.listen(1)

    while True:
        # Wait for a connection
        sys.stderr.write( 'waiting for a connection\n')
        connection, client_address = sock.accept()


        try:
            sys.stderr.write('connection from '+ str(client_address)+'\n')

            # Receive the data in small chunks and retransmit it
            while True:
                data = connection.recv(16)
                sys.stderr.write( 'received "%s"\n' % data)
                if data:
                    sys.stderr.write( 'sending data back to the client\n')
                    connection.sendall(data)
                else:
                    sys.stderr.write( 'no more data from '+ str(client_address)+'\n')
                    break

        finally:
            # Clean up the connection
            connection.close()



if __name__ == "__main__":
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

