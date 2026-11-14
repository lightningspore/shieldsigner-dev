# Copyright2020 Stepan Snigirev; MIT, see ../LICENSE.embit

from seedsigner_port.decode_platform import FeatureUnavailable
import hashlib
try:
    hashlib.new('ripemd160')

    def ripemd160(msg):
        return hashlib.new('ripemd160', msg).digest()
except FeatureUnavailable:
    raise
except:
    from .util.py_ripemd160 import ripemd160

def double_sha256(msg):
    """sha256(sha256(msg)) -> bytes"""
    return hashlib.sha256(hashlib.sha256(msg).digest()).digest()

def hash160(msg):
    """ripemd160(sha256(msg)) -> bytes"""
    return ripemd160(hashlib.sha256(msg).digest())

def sha256(msg):
    """one-line sha256(msg) -> bytes"""
    return hashlib.sha256(msg).digest()

def tagged_hash(tag, data):
    """BIP-Schnorr tag-specific key derivation"""
    hashtag = hashlib.sha256(tag.encode()).digest()
    return hashlib.sha256(hashtag + hashtag + data).digest()

def tagged_hash_init(tag, data=b''):
    """Prepares a tagged hash function to digest extra data"""
    hashtag = hashlib.sha256(tag.encode()).digest()
    h = hashlib.sha256(hashtag + hashtag + data)
    return h
