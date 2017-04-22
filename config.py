import configparser
import os, sys
import getpass

from ignore import default_ignore_file

def enter_password():
    print("\nEnter password for file encryption")
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
        host = input('\nEnter the hostname or ip of server: ') or 'localhost'
    except:
        pass
    if host == 'localhost':
        print('hostname set to localhost.  Transport security will be disabled.')
    return host

def enter_port():
    port = 0
    while not port:
        try:
            portstr = input('\nEnter the blackjay port (12345): ') or '12345'
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
        security = input('\nEnter the transport security ( [ssh]/None_PleaseAttackMeManInTheMiddle ): ') or 'ssh'
    except:
        pass
    if security != 'ssh' and security != 'None_PleaseAttackMeManInTheMiddle':
        security = 'ssh'
        print('transport security set to "ssh"')
    return security

def enter_ssh_private_key():
    ssh_pkey = 'none'
    while True:
        try:
            ssh_pkey = input('\nEnter ssh private key to use, defaults to "none", meaning use system defaults (only seems to work on Macs): ') or 'none'
        except:
            pass
        if ssh_pkey is 'none':
            return ssh_pkey
        if os.path.isfile(os.path.expanduser(ssh_pkey)) is False:
            print(ssh_pkey,'is not a correct path to a file')
        else:
            return ssh_pkey

def enter_ssh_user():
    ssh_user = 'none'
    try:
        ssh_user = input('\nEnter ssh username to use, defaults to "none", meaning use the current user\'s username: ') or 'none'
    except:
        pass
    return ssh_user

def enter_ssh_port():
    ssh_portstr = 'none'
    while True:
        try:
            ssh_portstr = input('\nEnter ssh port to use, defaults to "none", meaning use the ssh config file values (should work in Linux and Mac): ') or 'none'
        except:
            pass
        if ssh_portstr is 'none':
            return ssh_portstr
        else:
            try:
                ssh_port = int(ssh_portstr)
                return ssh_portstr
            except:
                print('ssh port must be "none" or a number. ',ssh_portstr,'is not valid.')

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
    else:
        with open(configpath, 'r') as configfile:
            config.read_file(configfile)
        if not 'blackjay' in config.sections():
            config.add_section('blackjay')

    # we now test if all the options have been set in config
    host = config.get('blackjay','host',fallback=None)
    port = config.get('blackjay','port',fallback=None)
    transport_security = config.get('blackjay','transport_security',fallback=None)
    password = config.get('blackjay','password',fallback=None)
    ssh_pkey = config.get('blackjay','ssh_pkey',fallback=None)
    ssh_user = config.get('blackjay','ssh_user',fallback=None)
    ssh_port = config.get('blackjay','ssh_port',fallback=None)

    if not host:
        print('Host not found in config, enter new host value.')
        host = enter_hostname()
        config['blackjay']['host'] = host
        if host == 'localhost':
            print('disabling transport security.')
            print('This should not be a problem since blackjay is being hosted locally')
            transport_security = 'None_BlackjayIsHostedLocally'
            config['blackjay']['transport_security'] = transport_security

    if host != 'localhost' and not transport_security:
        print('transport_security not found in config, enter new transport_security value')
        transport_security = enter_transport_security()
        config['blackjay']['transport_security'] = transport_security

    if transport_security == 'ssh':
        if not ssh_user:
            print('ssh username not found in config, enter new ssh username')
            config['blackjay']['ssh_user'] = enter_ssh_user()
        if not ssh_pkey:
            print('ssh private key not found in config, enter new ssh private key file')
            config['blackjay']['ssh_pkey'] = enter_ssh_private_key()
        if not ssh_port:
            print('ssh port not found in config, enter new ssh port')
            config['blackjay']['ssh_port'] = enter_ssh_port()

    if not port:
        print('Blackjay port not found in config, enter new port value')
        config['blackjay']['port'] = enter_port()

    if not password:
        print('Password for blackjay encryption not found in config, enter new password')
        config['blackjay']['password'] = enter_password()


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
