import binascii
import os


def generate_token(n=24):
    return str(binascii.hexlify(os.urandom(n)), 'utf-8')
