# Copyright2020 Stepan Snigirev; MIT, see ../LICENSE.embit

from seedsigner_port.decode_platform import FeatureUnavailable
from . import base58
from . import hashes
from .misc import secp256k1
from .networks import NETWORKS
from .base import EmbitBase, EmbitError, EmbitKey
from binascii import hexlify, unhexlify

class ECError(EmbitError):
    pass

class Signature(EmbitBase):

    def __init__(self, sig):
        self._sig = sig

    def write_to(self, stream):
        return stream.write(secp256k1.ecdsa_signature_serialize_der(self._sig))

    @classmethod
    def read_from(cls, stream):
        der = stream.read(2)
        der += stream.read(der[1])
        return cls(secp256k1.ecdsa_signature_parse_der(der))

class SchnorrSig(EmbitBase):

    def __init__(self, sig):
        assert len(sig) == 64
        self._sig = sig

    def write_to(self, stream):
        return stream.write(self._sig)

    @classmethod
    def read_from(cls, stream):
        return cls(stream.read(64))

class PublicKey(EmbitKey):

    def __init__(self, point, compressed=True):
        self._point = point
        self.compressed = compressed

    @classmethod
    def read_from(cls, stream):
        b = stream.read(1)
        if b not in [b'\x02', b'\x03', b'\x04']:
            raise ECError('Invalid public key')
        if b == b'\x04':
            b += stream.read(64)
        else:
            b += stream.read(32)
        try:
            point = secp256k1.ec_pubkey_parse(b)
        except FeatureUnavailable:
            raise
        except Exception as e:
            raise ECError(str(e))
        compressed = b[0] != 4
        return cls(point, compressed)

    def sec(self):
        """Sec representation of the key"""
        flag = secp256k1.EC_COMPRESSED if self.compressed else secp256k1.EC_UNCOMPRESSED
        return secp256k1.ec_pubkey_serialize(self._point, flag)

    def xonly(self):
        return self.sec()[1:33]

    def taproot_tweak(self, h=b''):
        """Returns a tweaked public key"""
        x = self.xonly()
        tweak = hashes.tagged_hash('TapTweak', x + h)
        if not secp256k1.ec_seckey_verify(tweak):
            raise EmbitError('Tweak is too large')
        point = secp256k1.ec_pubkey_parse(b'\x02' + x)
        pub = secp256k1.ec_pubkey_add(point, tweak)
        sec = secp256k1.ec_pubkey_serialize(pub)
        return PublicKey.from_xonly(sec[1:33])

    def write_to(self, stream):
        return stream.write(self.sec())

    def serialize(self):
        return self.sec()

    def verify(self, sig, msg_hash):
        return bool(secp256k1.ecdsa_verify(sig._sig, msg_hash, self._point))

    def _xonly(self):
        """Returns internal representation of the xonly-pubkey (64 bytes)"""
        pub, _ = secp256k1.xonly_pubkey_from_pubkey(self._point)
        return pub

    @classmethod
    def from_xonly(cls, data):
        assert len(data) == 32
        return cls.parse(b'\x02' + data)

    def schnorr_verify(self, sig, msg_hash):
        return bool(secp256k1.schnorrsig_verify(sig._sig, msg_hash, self._xonly()))

    @classmethod
    def from_string(cls, s):
        return cls.parse(unhexlify(s))

    @property
    def is_private(self):
        return False

    def to_string(self):
        return hexlify(self.sec()).decode()

    def __lt__(self, other):
        return self.sec() < other.sec()

    def __gt__(self, other):
        return self.sec() > other.sec()

    def __eq__(self, other):
        return self.sec() == other.sec()

    def __hash__(self):
        return hash(self._point)

class PrivateKey(EmbitKey):

    def __init__(self, secret, compressed=True, network=NETWORKS['main']):
        """Creates a private key from 32-byte array"""
        if len(secret) != 32:
            raise ECError('Secret should be 32-byte array')
        if not secp256k1.ec_seckey_verify(secret):
            raise ECError('Secret is not valid (larger then N?)')
        self.compressed = compressed
        self._secret = secret
        self.network = network

    def wif(self, network=None):
        """Export private key as Wallet Import Format string.
        Prefix 0x80 is used for mainnet, 0xEF for testnet.
        This class doesn't store this information though.
        """
        if network is None:
            network = self.network
        prefix = network['wif']
        b = prefix + self._secret
        if self.compressed:
            b += bytes([1])
        return base58.encode_check(b)

    @property
    def secret(self):
        return self._secret

    def sec(self):
        """Sec representation of the corresponding public key"""
        return self.get_public_key().sec()

    def xonly(self):
        return self.sec()[1:]

    def taproot_tweak(self, h=b''):
        """Returns a tweaked private key"""
        sec = self.sec()
        negate = sec[0] != 2
        x = sec[1:33]
        tweak = hashes.tagged_hash('TapTweak', x + h)
        if not secp256k1.ec_seckey_verify(tweak):
            raise EmbitError('Tweak is too large')
        if negate:
            secret = secp256k1.ec_privkey_negate(self._secret)
        else:
            secret = self._secret
        res = secp256k1.ec_privkey_add(secret, tweak)
        pk = PrivateKey(res)
        if pk.sec()[0] == 3:
            pk = PrivateKey(secp256k1.ec_privkey_negate(res))
        return pk

    @classmethod
    def from_wif(cls, s):
        """Import private key from Wallet Import Format string."""
        b = base58.decode_check(s)
        prefix = b[:1]
        network = None
        for net in NETWORKS:
            if NETWORKS[net]['wif'] == prefix:
                network = NETWORKS[net]
        secret = b[1:33]
        compressed = False
        if len(b) not in [33, 34]:
            raise ECError('Wrong WIF length')
        if len(b) == 34:
            if b[-1] == 1:
                compressed = True
            else:
                raise ECError('Wrong WIF compressed flag')
        return cls(secret, compressed, network)

    def to_base58(self, network=None):
        return self.wif(network)

    @classmethod
    def from_base58(cls, s):
        return cls.from_wif(s)

    def get_public_key(self):
        return PublicKey(secp256k1.ec_pubkey_create(self._secret), self.compressed)

    def to_public(self):
        """Alias to get_public_key for API consistency"""
        return self.get_public_key()

    def sign(self, msg_hash, grind=True):
        sig = Signature(secp256k1.ecdsa_sign(msg_hash, self._secret))
        if grind:
            counter = 1
            while len(sig.serialize()) > 70:
                sig = Signature(secp256k1.ecdsa_sign(msg_hash, self._secret, None, counter.to_bytes(32, 'little')))
                counter += 1
                if counter > 200:
                    break
        return sig

    def schnorr_sign(self, msg_hash):
        return SchnorrSig(secp256k1.schnorrsig_sign(msg_hash, self._secret))

    def verify(self, sig, msg_hash):
        return self.get_public_key().verify(sig, msg_hash)

    def schnorr_verify(self, sig, msg_hash):
        return self.get_public_key().schnorr_verify(sig, msg_hash)

    def write_to(self, stream):
        return stream.write(self._secret)

    def ecdh(self, public_key, hashfn=None, data=None):
        pubkey_point = secp256k1.ec_pubkey_parse(public_key.sec())
        return secp256k1.ecdh(pubkey_point, self._secret, hashfn, data)

    @classmethod
    def read_from(cls, stream):
        return cls(stream.read(32))

    @property
    def is_private(self):
        return True

def __getattr__(name):
    if name != 'NUMS_PUBKEY':
        raise AttributeError(name)
    global NUMS_PUBKEY
    NUMS_PUBKEY = PublicKey.from_string('0250929b74c1a04954b78b4b6035e97a5e078a5a0f28ec96d547bfee9ace803ac0')
    return NUMS_PUBKEY
