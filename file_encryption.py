import blowfish
from zipfile import ZipFile
import shutil
from time import time
from metadata import *
import os

# protocol steps:
#    client says:                  server says:
#--------------------------------------------------------------
#    give me metadata
#                                  Here is metadata
#    here are changes/pullreqs
#                                  Here are files / I am honoring these changes
#                     (both write to files)

# takes push, pull, and conflicts, returns name of zipfile
def prep_push_archive(push, pull, conflicts):
    # start with a clean directory
    shutil.rmtree('.blackjay/temp',ignore_errors=True)
    os.mkdir('.blackjay/temp')
    # make a json file with all of the meta data
    write_metadata(push,'.blackjay/temp/push')
    write_metadata(pull,'.blackjay/temp/pull')
    write_metadata(conflicts,'.blackjay/temp/conflicts')
    # now prep the zip archive
    zipname = str(int(time()))+'.zip'
    with ZipFile(os.path.join('.blackjay/temp',zipname),'w') as z:
        z.write('.blackjay/temp/push')
        z.write('.blackjay/temp/pull')
        z.write('.blackjay/temp/conflicts')
        for name,meta in push.items():
            if meta['del_flag'] is False:
                z.write(name)
    return zipname

def extract_pushed_archive(zipname):
    # make the temp directory
    temp = '.blackjay/temp'+zipname[:-4]
    os.mkdir(temp)
    # extract the zip file
    with ZipFile(os.path.join('.blackjay/temp',zipname),'r') as z:
        z.extractall(temp)
    push = load_metadata('.blackjay/temp/push')
    pull = load_metadata('.blackjay/temp/pull')
    conflicts = load_metadata('.blackjay/temp/conflicts')
    return push, pull, conflicts

def encrypt_file(plainf,secretf,cipher):
    size = os.stat(plainf)
    BLOCKSIZE = 65536
    # figure out which the last block is (that we need to pad)
    lastblock = int(size/BLOCKSIZE) if size % BLOCKSIZE != 0 else int(size / BLOCKSIZE) - 1
    # open files
    plain = open(plainf,'rb')
    secret = open(secretf,'wb')
    # write all but the last block without padding
    block = 0;
    while block < lastblock:
        buf = plain.read(BLOCKSIZE)
        secret.write(encrypt_data(buf,cipher))
        block += 1
    buf = plain.read(BLOCKSIZE)
    secret.write(encrypt_data(pad_data(buf),cipher))
    plain.close()
    secret.close()

def decrypt_file(secretf,plainf,cipher):
    size = os.stat(plainf)
    BLOCKSIZE = 65536
    # figure out which the last block is (that we need to pad)
    lastblock = int(size/BLOCKSIZE) if size % BLOCKSIZE != 0 else int(size / BLOCKSIZE) - 1
    # open files
    plain = open(plainf,'rb')
    secret = open(secretf,'wb')
    # write all but the last block without padding
    block = 0;
    while block < lastblock:
        buf = plain.read(BLOCKSIZE)
        secret.write(encrypt_data(buf,cipher))
        block += 1
    buf = plain.read(BLOCKSIZE)
    secret.write(encrypt_data(pad_data(buf),cipher))
    plain.close()
    secret.close()

def pad_data(data):
    pad_len = 8 - (len(data) % 8)
    return data + (bytes([pad_len])*pad_len)

def unpad_data(data):
    pad_len = data[-1]
    return data[:-pad_len]

def encrypt_data(data,cipher):
    return b''.join([i for i in cipher.encrypt_ecb(pad_data(data))])

def decrypt_data(data,cipher):
    return unpad_data(b''.join([i for i in cipher.decrypt_ecb(data)]))

def blowfish_test():
    cipher= blowfish.Cipher(b'password')

    data = b'akeihfoai 3jo823up 8u3pro8u23n ocqumpoa93 urao3wu5vq2'

    print(data)
    secret = encrypt_data(data,cipher)
    print(decrypt_data(secret,cipher))
