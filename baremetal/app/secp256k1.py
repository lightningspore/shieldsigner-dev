# SPDX-License-Identifier: MIT
"""Actual libsecp256k1 operations with portable private Python token encodings.

Point tokens are big-endian X||Y, signature tokens compact R||S. They are not C
struct blobs and must not be persisted as an external format. Serialized keys,
DER/compact signatures, BIP32 and BIP340 retain their standard wire formats.
"""

import _native_secp as _n
from seedsigner_port.decode_platform import FeatureUnavailable

CONTEXT_NONE = 1
CONTEXT_VERIFY = 257
CONTEXT_SIGN = 513
EC_UNCOMPRESSED = 2
EC_COMPRESSED = 258


def _context(value):
    if value is not None:
        raise FeatureUnavailable('Only one native foreground curve context is supplied')


def _nonce(value):
    if value is not None:
        raise FeatureUnavailable('Python nonce callbacks are unavailable')


def context_randomize(seed, context=None):
    _context(context)
    return _n.randomize(seed)


def context_status():
    return _n.status()


def ec_seckey_verify(secret, context=None):
    _context(context)
    return _n.key_valid(secret)


def ec_pubkey_create(secret, context=None):
    _context(context)
    return _n.point_create(secret)


def ec_pubkey_parse(sec, context=None):
    _context(context)
    return _n.point_parse(sec)


def ec_pubkey_serialize(point, flag=EC_COMPRESSED, context=None):
    _context(context)
    return _n.point_serialize(point, flag)


def ec_privkey_negate(secret, context=None):
    _context(context)
    return _n.scalar_op(0, secret, None)


def ec_privkey_add(secret, tweak, context=None):
    _context(context)
    return _n.scalar_op(1, secret, tweak)


def ec_privkey_mul(secret, tweak, context=None):
    _context(context)
    return _n.scalar_op(2, secret, tweak)


def ec_pubkey_negate(point, context=None):
    _context(context)
    return _n.point_op(0, point, None)


def ec_pubkey_add(point, tweak, context=None):
    _context(context)
    return _n.point_op(1, point, tweak)


def ec_pubkey_mul(point, tweak, context=None):
    _context(context)
    return _n.point_op(2, point, tweak)


def ec_privkey_tweak_add(secret, tweak, context=None):
    memoryview(secret)[:] = ec_privkey_add(secret, tweak, context)


def ec_privkey_tweak_mul(secret, tweak, context=None):
    memoryview(secret)[:] = ec_privkey_mul(secret, tweak, context)


def ec_pubkey_tweak_add(point, tweak, context=None):
    memoryview(point)[:] = ec_pubkey_add(point, tweak, context)


def ec_pubkey_tweak_mul(point, tweak, context=None):
    memoryview(point)[:] = ec_pubkey_mul(point, tweak, context)


def ecdsa_signature_parse_der(data, context=None):
    _context(context)
    return _n.signature_parse(data, False)


def ecdsa_signature_parse_compact(data, context=None):
    _context(context)
    return _n.signature_parse(data, True)


def ecdsa_signature_serialize_der(sig, context=None):
    _context(context)
    return _n.signature_serialize(sig, False)


def ecdsa_signature_serialize_compact(sig, context=None):
    _context(context)
    return _n.signature_serialize(sig, True)


def ecdsa_signature_normalize(sig, context=None):
    _context(context)
    return _n.signature_normalize(sig)


def ecdsa_sign(msg, secret, nonce_function=None, extra_data=None, context=None):
    _context(context)
    _nonce(nonce_function)
    return _n.ecdsa_sign(msg, secret, extra_data, False)


def ecdsa_verify(sig, msg, point, context=None):
    _context(context)
    return _n.ecdsa_verify(sig, msg, point)


def ecdsa_sign_recoverable(msg, secret, context=None):
    _context(context)
    return _n.ecdsa_sign(msg, secret, None, True)


def ecdsa_recoverable_signature_parse_compact(data, recid, context=None):
    _context(context)
    if not 0 <= recid <= 3:
        raise ValueError('invalid recovery id')
    return _n.signature_parse(data, True) + bytes((recid,))


def ecdsa_recoverable_signature_serialize_compact(sig, context=None):
    _context(context)
    if len(sig) != 65 or sig[64] > 3:
        raise ValueError('invalid recoverable signature')
    return _n.signature_serialize(sig[:64], True), sig[64]


def ecdsa_recoverable_signature_convert(sig, context=None):
    return ecdsa_recoverable_signature_serialize_compact(sig, context)[0]


def ecdsa_recover(sig, msg, context=None):
    _context(context)
    return _n.recover(sig, msg)


def xonly_pubkey_from_pubkey(point, context=None):
    _context(context)
    return _n.xonly(point)


def xonly_pubkey_parse(data, context=None):
    _context(context)
    if isinstance(data, str) or len(data) != 32:
        raise ValueError('x-only public key requires32bytes')
    return _n.point_parse(b'\x02' + bytes(data))


def xonly_pubkey_serialize(point, context=None):
    return ec_pubkey_serialize(point, EC_COMPRESSED, context)[1:33]


def keypair_create(secret, context=None):
    point = ec_pubkey_create(secret, context)
    return bytes(secret) + point


def schnorrsig_sign(msg, keypair, nonce_function=None, extra_data=None, context=None):
    _context(context)
    _nonce(nonce_function)
    if len(keypair) == 96:
        if ec_pubkey_create(keypair[:32]) != keypair[32:]:
            raise ValueError('incoherent keypair')
        keypair = keypair[:32]
    return _n.schnorr_sign(msg, keypair, extra_data)


def schnorrsig_verify(sig, msg, point, context=None):
    _context(context)
    return _n.schnorr_verify(sig, msg, point)


def ecdh(point, secret, hashfn=None, data=None, context=None):
    _context(context)
    if hashfn is not None or data is not None:
        raise FeatureUnavailable('Custom ECDH hash callbacks are unavailable')
    return _n.ecdh(point, secret)


def __getattr__(name):
    if name.startswith('__'):
        raise AttributeError(name)
    raise FeatureUnavailable('Native curve API unavailable: ' + name)
