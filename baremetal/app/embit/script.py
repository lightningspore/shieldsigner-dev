# Copyright2020 Stepan Snigirev; MIT, see ../LICENSE.embit

from seedsigner_port.decode_platform import FeatureUnavailable
from .networks import NETWORKS
from . import base58
from . import bech32
from . import hashes
from . import compact
from .base import EmbitBase, EmbitError
SIGHASH_ALL = 1

class Script(EmbitBase):

    def __init__(self, data=b''):
        self.data = data

    def address(self, network=NETWORKS['main']):
        script_type = self.script_type()
        data = self.data
        if script_type is None:
            raise ValueError("This type of script doesn't have address representation")
        if script_type == 'p2pkh':
            d = network['p2pkh'] + data[3:23]
            return base58.encode_check(d)
        if script_type == 'p2sh':
            d = network['p2sh'] + data[2:22]
            return base58.encode_check(d)
        if script_type in ['p2wpkh', 'p2wsh', 'p2tr']:
            ver = data[0]
            if ver > 0:
                ver = ver % 80
            return bech32.encode(network['bech32'], ver, data[2:])
        raise ValueError('Unsupported script type')

    def push(self, data):
        self.data += compact.to_bytes(len(data)) + data

    def script_type(self):
        data = self.data
        if len(data) == 25 and data[:3] == b'v\xa9\x14' and (data[-2:] == b'\x88\xac'):
            return 'p2pkh'
        if len(data) == 23 and data[:2] == b'\xa9\x14' and (data[-1] == 135):
            return 'p2sh'
        if len(data) == 22 and data[:2] == b'\x00\x14':
            return 'p2wpkh'
        if len(data) == 34 and data[:2] == b'\x00 ':
            return 'p2wsh'
        if len(data) == 34 and data[:2] == b'Q ':
            return 'p2tr'
        return None

    def write_to(self, stream):
        res = stream.write(compact.to_bytes(len(self.data)))
        res += stream.write(self.data)
        return res

    @classmethod
    def read_from(cls, stream):
        l = compact.read_from(stream)
        data = stream.read(l)
        if len(data) != l:
            raise ValueError('Cant read %d bytes' % l)
        return cls(data)

    @classmethod
    def from_address(cls, addr):
        """
        Decodes a bitcoin address and returns corresponding scriptpubkey.
        """
        return address_to_scriptpubkey(addr)

    def __eq__(self, other):
        return self.data == other.data

    def __ne__(self, other):
        return self.data != other.data

    def __hash__(self):
        return hash(self.data)

    def __len__(self):
        return len(self.data)

class Witness(EmbitBase):

    def __init__(self, items=[]):
        self.items = items[:]

    def write_to(self, stream):
        res = stream.write(compact.to_bytes(len(self.items)))
        for item in self.items:
            res += stream.write(compact.to_bytes(len(item)))
            res += stream.write(item)
        return res

    @classmethod
    def read_from(cls, stream):
        num = compact.read_from(stream)
        items = []
        for i in range(num):
            l = compact.read_from(stream)
            data = stream.read(l)
            items.append(data)
        return cls(items)

    def __hash__(self):
        return hash(self.items)

    def __len__(self):
        return len(self.items)

def p2pkh(pubkey):
    """Return Pay-To-Pubkey-Hash ScriptPubkey"""
    return Script(b'v\xa9\x14' + hashes.hash160(pubkey.sec()) + b'\x88\xac')

def p2sh(script):
    """Return Pay-To-Script-Hash ScriptPubkey"""
    return Script(b'\xa9\x14' + hashes.hash160(script.data) + b'\x87')

def p2wpkh(pubkey):
    """Return Pay-To-Witness-Pubkey-Hash ScriptPubkey"""
    return Script(b'\x00\x14' + hashes.hash160(pubkey.sec()))

def p2wsh(script):
    """Return Pay-To-Witness-Pubkey-Hash ScriptPubkey"""
    return Script(b'\x00 ' + hashes.sha256(script.data))

def p2tr(pubkey, script_tree=None):
    """Return Pay-To-Taproot ScriptPubkey"""
    if script_tree is None:
        h = b''
    else:
        h = script_tree.tweak()
    output_pubkey = pubkey.taproot_tweak(h)
    return Script(b'Q ' + output_pubkey.xonly())

def p2pkh_from_p2wpkh(script):
    """Convert p2wpkh to p2pkh script"""
    return Script(b'v\xa9' + script.serialize()[2:] + b'\x88\xac')

def multisig(m, pubkeys):
    if m <= 0 or m > 16:
        raise ValueError('m must be between 1 and 16')
    n = len(pubkeys)
    if n < m or n > 16:
        raise ValueError('Number of pubkeys must be between %d and 16' % m)
    data = bytes([80 + m])
    for pubkey in pubkeys:
        sec = pubkey.sec()
        data += bytes([len(sec)]) + sec
    data += bytes([80 + n, 174])
    return Script(data)

def address_to_scriptpubkey(addr):
    try:
        data = base58.decode_check(addr)
        prefix = data[:1]
        for net in NETWORKS.values():
            if prefix == net['p2pkh']:
                return Script(b'v\xa9\x14' + data[1:] + b'\x88\xac')
            elif prefix == net['p2sh']:
                return Script(b'\xa9\x14' + data[1:] + b'\x87')
    except FeatureUnavailable:
        raise
    except:
        hrp = addr.split('1')[0]
        ver, data = bech32.decode(hrp, addr)
        if ver not in [0, 1] or len(data) not in [20, 32]:
            raise EmbitError('Invalid bech32 address')
        if ver == 1 and len(data) != 32:
            raise EmbitError('Invalid bech32 address')
        if ver > 0:
            ver += 80
        return Script(bytes([ver, len(data)] + data))

def script_sig_p2pkh(signature, pubkey, sighash=SIGHASH_ALL):
    sec = pubkey.sec()
    der = signature.serialize() + bytes([sighash])
    data = compact.to_bytes(len(der)) + der + compact.to_bytes(len(sec)) + sec
    return Script(data)

def script_sig_p2sh(redeem_script):
    """Creates scriptsig for p2sh"""
    return Script(redeem_script.serialize())

def witness_p2wpkh(signature, pubkey, sighash=SIGHASH_ALL):
    return Witness([signature.serialize() + bytes([sighash]), pubkey.sec()])
