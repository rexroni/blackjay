#!/usr/bin/python3

import blowfish

cipher= blowfish.Cipher(b'password')

data = b'akeihfoai 3jo823up 8u3pro8u23n ocqumpoa93 urao3wu5vq2'

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


print(data)
secret = encrypt_data(data,cipher)
print(decrypt_data(secret,cipher))
