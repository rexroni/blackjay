import os, sys
import binascii
from Crypto.Cipher import Blowfish
from Crypto.Hash import HMAC,SHA512

def get_hmac(plainf, password):
    hmacer = HMAC.new(password, digestmod=SHA512)
    BLOCKSIZE = 65536
    with open(plainf,'rb') as plain:
        buf = 'empty'
        while len(buf) > 0:
            buf = plain.read(BLOCKSIZE)
            hmacer.update(buf)
    return hmacer.hexdigest()

def add_hmacs_to_metadata(push,password):
    for name,meta in push.items():
        if meta['del_flag'] is False:
            push[name]['hmac'] = get_hmac(name, password)
    return push

def fresh_cipher(password, iv):
    return Blowfish.new(password, Blowfish.MODE_CBC, iv)

def gen_iv(name,mtime):
    hasher = SHA512.new()
    hasher.update(('%s-%d'%(name,mtime)).encode('utf8'))
    return binascii.unhexlify(hasher.hexdigest())[:Blowfish.block_size]

def encrypt_file(plainf,secretf,iv,password):
    size = os.stat(plainf).st_size
    BLOCKSIZE = 65536
    # figure out which the last block is (that we need to pad)
    lastblock = int(size/BLOCKSIZE) if size % BLOCKSIZE != 0 else int(size / BLOCKSIZE) - 1
    if lastblock < 0: lastblock = 0
    # open files
    plain = open(plainf,'rb')
    secret = open(secretf,'wb')
    cipher = fresh_cipher(password, iv)
    # write all but the last block without padding
    block = 0;
    print('encrypting',plainf)
    while block < lastblock:
        buf = plain.read(BLOCKSIZE)
        secret.write(cipher.encrypt(buf))
        sys.stdout.write('reading %d bytes, %d%% complete     \r'%(len(buf),
                                        (block+1)/(lastblock+1)*100))
        block += 1
    buf = plain.read()
    secret.write(cipher.encrypt(pad_data(buf,8)))
    sys.stdout.write('reading %d bytes, %d%% complete     \r'%(len(buf),
                                    (block+1)/(lastblock+1)*100))
    print('')
    plain.close()
    secret.close()
    # preserve access times
    st = os.stat(plainf)
    os.utime(secretf,(st.st_atime,st.st_mtime))

def decrypt_file(secretf,plainf,iv,password):
    size = os.stat(secretf).st_size
    BLOCKSIZE = 65536
    # figure out which the last block is (that we need to pad)
    lastblock = int(size/BLOCKSIZE) if size % BLOCKSIZE != 0 else int(size / BLOCKSIZE) - 1
    if lastblock < 0: lastblock = 0
    # open files
    secret = open(secretf,'rb')
    plain = open(plainf,'wb')
    cipher = fresh_cipher(password, iv)
    # all but the last block are without padding
    block = 0;
    print('decrypting',plainf)
    while block < lastblock:
        buf = secret.read(BLOCKSIZE)
        plain.write(cipher.decrypt(buf))
        sys.stdout.write('writing %d bytes, %d%% complete     \r'%(len(buf),
                                        (block+1)/(lastblock+1)*100))
        block += 1
    buf = secret.read()
    plain.write(unpad_data(cipher.decrypt(buf)))
    print('writing %d bytes, %d%% complete     \r'%(len(buf),
                                    (block+1)/(lastblock+1)*100))
    plain.close()
    secret.close()
    # preserve access times
    st = os.stat(secretf)
    os.utime(plainf,(st.st_atime,st.st_mtime))

def pad_data(data, bs):
    pad_len = bs - (len(data) % bs)
    #print('pad_len %d'%pad_len)
    return data + chr(pad_len)*pad_len

def unpad_data(data):
    pad_len = ord(data[-1])
    #print('un pad_len %d'%pad_len)
    return data[:-pad_len]
