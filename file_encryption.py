import os
from Crypto.Cipher import Blowfish,AES
from Crypto.Hash import HMAC,SHA512

def get_hash_HMAC(password, plainf):
    hasher = SHA512.new()
    hmacer = HMAC.new(password, hasher)
    BLOCKSIZE = 65536
    with open(plainf,'rb') as plain:
        buf = plain.read(BLOCKSIZE)
        while len(buf) > 0:
            hasher.update(buf)
            hmacer.update(buf)
    return hasher.hexdigest(),hmacer.hexdigest()

def fresh_cipher(password, iv):
    return Blowfish.new(password, Blowfish.MODE_CBC, iv)

def fresh_aes_cipher(password, iv):
    return Blowfish.new(password, Blowfish.MODE_CBC, iv)
############################## you are testing AES file encryption
    return AES.new(password*4, AES.MODE_CBC, iv*2)

def encrypt_file(plainf,secretf,password):
    size = os.stat(plainf).st_size
    BLOCKSIZE = 65536
    # figure out which the last block is (that we need to pad)
    lastblock = int(size/BLOCKSIZE) if size % BLOCKSIZE != 0 else int(size / BLOCKSIZE) - 1
    # open files
    plain = open(plainf,'rb')
    secret = open(secretf,'wb')
    # init cipher
    iv = b'init-vec'
    cipher = fresh_cipher(password, iv)
    # write all but the last block without padding
    block = 0;
    while block < lastblock:
        buf = plain.read(BLOCKSIZE)
        secret.write(cipher.encrypt(buf))
        print('reading %d bytes, %d%% complete     \r'%(len(buf),block/lastblock*100),end='')
        block += 1
    buf = plain.read()
    secret.write(cipher.encrypt(pad_data(buf,8)))
    print('reading %d bytes, %d%% complete     \r'%(len(buf),block/lastblock*100),end='')
    plain.close()
    secret.close()

def decrypt_file(secretf,plainf,password):
    size = os.stat(secretf).st_size
    BLOCKSIZE = 65536
    # figure out which the last block is (that we need to pad)
    lastblock = int(size/BLOCKSIZE) if size % BLOCKSIZE != 0 else int(size / BLOCKSIZE) - 1
    # open files
    secret = open(secretf,'rb')
    plain = open(plainf,'wb')
    # init cipher
    iv = b'init-vec'
    cipher = fresh_cipher(password, iv)
    # all but the last block are without padding
    block = 0;
    while block < lastblock:
        buf = secret.read(BLOCKSIZE)
        plain.write(cipher.decrypt(buf))
        print('writing %d bytes, %d%% complete     \r'%(len(buf),block/lastblock*100),end='')
        block += 1
    buf = secret.read()
    plain.write(unpad_data(cipher.decrypt(buf)))
    print('writing %d bytes, %d%% complete     \r'%(len(buf),block/lastblock*100),end='')
    plain.close()
    secret.close()

def pad_data(data, bs):
    pad_len = bs - (len(data) % bs)
    #print('pad_len %d'%pad_len)
    return data + (bytes([pad_len])*pad_len)

def unpad_data(data):
    pad_len = data[-1]
    #print('un pad_len %d'%pad_len)
    return data[:-pad_len]

def blowfish_test():
    bs = Blowfish.block_size
    # this is just for testing:
    iv = b'init-vec'
    cipher= Blowfish.new(b'password', Blowfish.MODE_CBC, iv)

    data = b'akeihfoai 3jo823up 8u3pro8u23n ocqumpoa93 urao3wu5vq2'

    print(data)
    secret = cipher.encrypt(pad_data(data,bs))

    cipher= Blowfish.new(b'password', Blowfish.MODE_CBC, iv)
    print(unpad_data(cipher.decrypt(secret)))

def AES_test():
    bs = AES.block_size
    # this is just for testing:
    iv = b'init-vecinit-vec'
    cipher= AES.new(b'passwordpasswordpasswordpassword',AES.MODE_CBC, iv)

    data = b'akeihfoai 3jo823up 8u3pro8u23n ocqumpoa93 urao3wu5vq2'

    print(data)
    secret = cipher.encrypt(pad_data(data,bs))

    cipher= AES.new(b'passwordpasswordpasswordpassword',AES.MODE_CBC, iv)
    print(unpad_data(cipher.decrypt(secret)))
