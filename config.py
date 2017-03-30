import configparser
import os, sys
import getpass

from ignore import default_ignore_file

def enter_password():
    print("Enter password for file encryption")
    pprompt = lambda: (getpass.getpass(), getpass.getpass('Retype password: '))
    while True:
        p1, p2 = pprompt()
        if p1 != p2:
            print('Passwords do not match. Try again')
        elif len(p1) < 8:
            print('Password must be at least 8 characters for blowfish encryption.')
        else:
            break
    return p1

def enter_hostname():
    host = 'localhost'
    try:
        host = input('Enter the hostname or ip of server (localhost): ') or 'localhost'
    except:
        pass
    return host

def enter_port():
    port = 0
    while not port:
        try:
            portstr = input('Enter the port number for communication with server (12345): ') or '12345'
        except:
            pass

        try:
            port = int(portstr)
        except:
            print('Hey you dullard, port NUMBER is a number no whatever {} is'.format(portstr))
    return str(port)

def enter_transport_security():
    security = 'ssh'
    try:
        security = input('Enter the transport security ( [ssh]/None_PleaseAttackMeManInTheMiddle ): ') or 'ssh'
    except:
        pass
    if security != 'ssh' and security != 'None_PleaseAttackMeManInTheMiddle':
        security = 'ssh'
        print('transport security set to "ssh"')
    return security

def enter_ssh_private_key():
    ssh_pkey = '~/.ssh/id_rsa'
    try:
        ssh_pkey = input('Enter ssh private key to use (~/.ssh/id_rsa): ') or '~/.ssh/id_rsa'
    except:
        pass
    return ssh_pkey


def get_config(configpath = None):
    if not configpath:
        configpath = os.path.abspath('.blackjay/config')

    # assumes we are in the base directory
    config = configparser.ConfigParser()

    print('Looking for blackjay in {}'.format(os.path.abspath('.')))

    if os.path.isdir('.blackjay') is not True:
        print('Looks like a new install... creating a .blackjay folder')
        os.mkdir('.blackjay')
        open(os.path.join('.blackjay','metadata'),'a').close()
        # start with sane defaults in ignore file
        ignf = open(os.path.join('.blackjay','ignore'),'w')
        ignf.write(default_ignore_file)
        ignf.close()

    if os.path.exists(configpath) is not True:
        print('Setting up a new config file at {}'.format(configpath))
        config.add_section('blackjay')
        config['blackjay']['host'] = enter_hostname()
        config['blackjay']['port'] = enter_port()
        config['blackjay']['transport_security'] = enter_transport_security()
        config['blackjay']['password'] = enter_password()
        config['blackjay']['ssh_pkey'] = enter_ssh_private_key()

        with open(configpath, 'w') as configfile:
            config.write(configfile)

    with open(configpath, 'r') as configfile:
        config.read_file(configfile)

    if not 'blackjay' in config.sections():
        print('It looks like your config file is missint the blackjay section')
        config.add_section('blackjay')

    # we now test if all the options have been set in config
    host = config.get('blackjay','host',fallback=None)
    portstr = config.get('blackjay','port',fallback=None)
    transport_security = config.get('blackjay','transport_security',fallback=None)
    password = config.get('blackjay','password',fallback=None)
    ssh_pkey = config.get('blackjay','ssh_pkey',fallback=None)

    if not host:
        print('Host not found in config, enter new host value.')
        config['blackjay']['host'] = enter_hostname()

    if not portstr:
        print('Port not found in config, enter new port value')
        config['blackjay']['port'] = enter_port()

    if not transport_security:
        print('transport_security not found in config, enter new transport_security value')
        config['blackjay']['transport_security'] = enter_transport_security()

    if not password:
        print('Password not found in config, enter new password value')
        config['blackjay']['port'] = enter_password()

    if not ssh_pkey:
        print('ssh private key not found in config, enter new ssh private key file')
        config['blackjay']['ssh_pkey'] = enter_ssh_private_key()

    with open(configpath, 'w') as configfile:
        config.write(configfile)

    ret_val = dict(config.items('blackjay'))
    ret_val['password'] = ret_val['password'].encode('utf8')
    return ret_val


def main():
    if len(sys.argv) == 2:
        os.chdir(sys.argv[1])

    config = get_config()
    print('Host: ', config['host'])
    print('Port: ', config['port'])
    print('Transport Security: ', config['transport_security'])
    print('Password: ', config['password'])
    print('ssh private key: ',config['ssh_pkey'])

    print(config)

if __name__ == '__main__':
    main()
