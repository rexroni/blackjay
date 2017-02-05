import base64
import getpass
import os
import socket
import sys
import traceback

import paramiko
from paramiko.py3compat import input

def setup_sftp(hostname, user, keyfile):
    # Paramiko client configuration
    Port = 22
    key = paramiko.RSAKey.from_private_key_file(keyfile)

    # get host key, if we know one
    hostkeytype = None
    hostkey = None
    try:
        host_keys = paramiko.util.load_host_keys(os.path.expanduser('~/.ssh/known_hosts'))
    except IOError:
        try:
            # try ~/ssh/ too, because windows can't have a folder named ~/.ssh/
            host_keys = paramiko.util.load_host_keys(os.path.expanduser('~/ssh/known_hosts'))
        except IOError:
            print('*** Unable to open host keys file')
            host_keys = {}

    if hostname in host_keys:
        hostkeytype = host_keys[hostname].keys()[0]
        hostkey = host_keys[hostname][hostkeytype]
        print('Using host key of type %s' % hostkeytype)
    else:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # now, connect and use paramiko Transport to negotiate SSH2 across the connection
    try:
        t = paramiko.Transport((hostname, Port))
        t.connect(hostkey, username=user, pkey=key)
        sftp = paramiko.SFTPClient.from_transport(t)

        return sftp,t

    except:
        e = sys.exc_info()[0]
        print('*** Caught exception: %s: %s' % (e.__class__, e))
        traceback.print_exc()
        try:
            t.close()
        except:
            pass
        return None

def trasfer_callback_print(trasfered, total):
    status = "\r{} of {} bytes trasfered".format(trasfered, total)
    print(status, end='')

def push_file(source, dest, hostname, user, keyfile):
    conn = setup_sftp(hostname, user, keyfile)
    if conn:
        print("-----------------------------------")
        sftp,t = conn
        sftp.put(source, dest, trasfer_callback_print)
        t.close()
        print("\ndone!")
        return True
    else:
        return False


def main():
    # setup logging
    paramiko.util.log_to_file('demo_sftp.log')

    push_file('demo_sftp.log', '/Users/tylerjw/workspace/Python/blackjay/paramikoExamples/demo_sftp.log', 'localhost', 'tylerjw', '/Users/tylerjw/.ssh/id_rsa')

if __name__ == '__main__':
    main()