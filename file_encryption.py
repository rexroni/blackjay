import blowfish
import os

def encrypt_file(plainf,secretf,cipher):
    size = os.stat(plainf).st_size
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
        print('reading %d bytes'%len(buf))
        block += 1
    buf = plain.read()
    secret.write(encrypt_data(pad_data(buf),cipher))
    print('reading %d bytes'%len(buf))
    plain.close()
    secret.close()

def decrypt_file(secretf,plainf,cipher):
    size = os.stat(secretf).st_size
    BLOCKSIZE = 65536
    # figure out which the last block is (that we need to pad)
    lastblock = int(size/BLOCKSIZE) if size % BLOCKSIZE != 0 else int(size / BLOCKSIZE) - 1
    # open files
    secret = open(secretf,'rb')
    plain = open(plainf,'wb')
    block = 0;
    while block < lastblock:
        buf = secret.read(BLOCKSIZE)
        plain.write(decrypt_data(buf,cipher))
        print('writing %d bytes'%len(decrypt_data(buf,cipher)))
    buf = secret.read()
    plain.write(unpad_data(decrypt_data(buf,cipher)))
    print('writing %d bytes'%len(decrypt_data(buf,cipher)))
    plain.close()
    secret.close()

def pad_data(data):
    pad_len = 8 - (len(data) % 8)
    print('pad_len %d'%pad_len)
    return data + (bytes([pad_len])*pad_len)

def unpad_data(data):
    pad_len = data[-1]
    print('un pad_len %d'%pad_len)
    return data[:-pad_len]

def encrypt_data(data,cipher):
    return b''.join([i for i in cipher.encrypt_ecb(data)])

def decrypt_data(data,cipher):
    return b''.join([i for i in cipher.decrypt_ecb(data)])

def blowfish_test():
    cipher= blowfish.Cipher(b'password')

    data = b'akeihfoai 3jo823up 8u3pro8u23n ocqumpoa93 urao3wu5vq2'

    print(data)
    secret = encrypt_data(data,cipher)
    print(decrypt_data(secret,cipher))
