# Copyright2020 Stepan Snigirev; MIT, see ../LICENSE.embit

from seedsigner_port.decode_platform import FeatureUnavailable
from collections import OrderedDict
from .transaction import Transaction, TransactionOutput, TransactionInput, SIGHASH
from . import compact
from . import bip32
from . import ec
from . import hashes
from . import script
from .script import Script, Witness
from .base import EmbitBase, EmbitError
from binascii import b2a_base64, a2b_base64, hexlify, unhexlify
from io import BytesIO

class PSBTError(EmbitError):
    pass

class CompressMode:
    KEEP_ALL = 0
    CLEAR_ALL = 1
    PARTIAL = 2

def ser_string(stream, s):
    return stream.write(compact.to_bytes(len(s))) + stream.write(s)

def read_string(stream):
    l = compact.read_from(stream)
    s = stream.read(l)
    if len(s) != l:
        raise PSBTError('Failed to read %d bytes' % l)
    return s

def skip_string(stream):
    l = compact.read_from(stream)
    stream.seek(l, 1)
    return len(compact.to_bytes(l)) + l

class DerivationPath(EmbitBase):

    def __init__(self, fingerprint, derivation):
        self.fingerprint = fingerprint
        self.derivation = derivation

    def write_to(self, stream):
        r = stream.write(self.fingerprint)
        for idx in self.derivation:
            r += stream.write(idx.to_bytes(4, 'little'))
        return r

    @classmethod
    def read_from(cls, stream):
        fingerprint = stream.read(4)
        derivation = []
        while True:
            r = stream.read(4)
            if len(r) == 0:
                break
            if len(r) < 4:
                raise PSBTError('Invalid length')
            derivation.append(int.from_bytes(r, 'little'))
        return cls(fingerprint, derivation)

class PSBTScope(EmbitBase):

    def __init__(self, unknown={}):
        self.unknown = unknown
        self.parse_unknowns()

    def write_to(self, stream, skip_separator=False, **kwargs):
        r = 0
        for key in self.unknown:
            r += ser_string(stream, key)
            r += ser_string(stream, self.unknown[key])
        if not skip_separator:
            r += stream.write(b'\x00')
        return r

    def parse_unknowns(self):
        for k in list(self.unknown):
            s = BytesIO()
            ser_string(s, self.unknown[k])
            s.seek(0)
            self.read_value(s, k)

    def read_value(self, stream, key, *args, **kwargs):
        if len(key) == 0:
            return
        value = read_string(stream)
        if key in self.unknown:
            raise PSBTError('Duplicated key')
        self.unknown[key] = value

    def update(self, other):
        self.unknown.update(other.unknown)

    @classmethod
    def read_from(cls, stream, *args, **kwargs):
        res = cls({}, *args, **kwargs)
        while True:
            key = read_string(stream)
            if len(key) == 0:
                break
            res.read_value(stream, key)
        return res

class InputScope(PSBTScope):
    TX_CLS = Transaction
    TXOUT_CLS = TransactionOutput

    def __init__(self, unknown={}, vin=None, compress=CompressMode.KEEP_ALL):
        self.compress = compress
        self.txid = None
        self.vout = None
        self.sequence = None
        if vin is not None:
            self.txid = vin.txid
            self.vout = vin.vout
            self.sequence = vin.sequence
        self.unknown = unknown
        self.non_witness_utxo = None
        self.witness_utxo = None
        self._utxo = None
        self._txhash = None
        self._verified = False
        self.partial_sigs = OrderedDict()
        self.sighash_type = None
        self.redeem_script = None
        self.witness_script = None
        self.bip32_derivations = OrderedDict()
        self.taproot_bip32_derivations = OrderedDict()
        self.taproot_internal_key = None
        self.taproot_merkle_root = None
        self.taproot_sigs = OrderedDict()
        self.taproot_scripts = OrderedDict()
        self.final_scriptsig = None
        self.final_scriptwitness = None
        self.parse_unknowns()

    def clear_metadata(self, compress=CompressMode.CLEAR_ALL):
        """Removes metadata like derivations, utxos etc except final or partial sigs"""
        if compress == CompressMode.KEEP_ALL:
            return
        self.unknown = {}
        if compress == CompressMode.CLEAR_ALL:
            self.non_witness_utxo = None
            self.witness_utxo = None
            self.sighash_type = None
            self.redeem_script = None
            self.witness_script = None
        elif self.witness_utxo is not None:
            self.non_witness_utxo = None
        self.bip32_derivations = OrderedDict()
        self.taproot_bip32_derivations = OrderedDict()
        self.taproot_internal_key = None
        self.taproot_merkle_root = None
        self.taproot_scripts = OrderedDict()

    def update(self, other):
        self.txid = other.txid or self.txid
        self.vout = other.vout if other.vout is not None else self.vout
        self.sequence = other.sequence if other.sequence is not None else self.sequence
        self.unknown.update(other.unknown)
        self.non_witness_utxo = other.non_witness_utxo or self.non_witness_utxo
        self.witness_utxo = other.witness_utxo or self.witness_utxo
        self._utxo = other._utxo or self._utxo
        self.partial_sigs.update(other.partial_sigs)
        self.sighash_type = other.sighash_type if other.sighash_type is not None else self.sighash_type
        self.redeem_script = other.redeem_script or self.redeem_script
        self.witness_script = other.witness_script or self.witness_script
        self.bip32_derivations.update(other.bip32_derivations)
        self.taproot_bip32_derivations.update(other.taproot_bip32_derivations)
        self.taproot_internal_key = other.taproot_internal_key
        self.taproot_merkle_root = other.taproot_merkle_root or self.taproot_merkle_root
        self.taproot_sigs.update(other.taproot_sigs)
        self.taproot_scripts.update(other.taproot_scripts)
        self.final_scriptsig = other.final_scriptsig or self.final_scriptsig
        self.final_scriptwitness = other.final_scriptwitness or self.final_scriptwitness

    @property
    def vin(self):
        return TransactionInput(self.txid, self.vout, sequence=self.sequence or 4294967295)

    @property
    def utxo(self):
        return self._utxo or self.witness_utxo or (self.non_witness_utxo.vout[self.vout] if self.non_witness_utxo else None)

    @property
    def script_pubkey(self):
        return self.utxo.script_pubkey if self.utxo else None

    @property
    def is_verified(self):
        """Check if prev txid was verified using non_witness_utxo. See `verify()`"""
        return self._verified

    @property
    def is_taproot(self):
        return self.utxo.script_pubkey.script_type() == 'p2tr'

    def verify(self, ignore_missing=False):
        """Verifies the hash of previous transaction provided in non_witness_utxo.
        We must verify on a hardware wallet even on segwit transactions to avoid
        miner fee attack described here:
        https://blog.trezor.io/details-of-firmware-updates-for-trezor-one-version-1-9-1-and-trezor-model-t-version-2-3-1-1eba8f60f2dd
        For legacy txs we need to verify it to calculate fee.
        """
        if self.non_witness_utxo or self._txhash:
            txid = bytes(reversed(self._txhash)) if self._txhash else self.non_witness_utxo.txid()
            if self.txid == txid:
                self._verified = True
                return True
            else:
                raise PSBTError("Previous txid doesn't match non_witness_utxo txid")
        if not ignore_missing:
            raise PSBTError('Missing non_witness_utxo')
        return False

    def read_value(self, stream, k):
        if len(k) == 0:
            return
        if k[0] == 0:
            if len(k) != 1:
                raise PSBTError('Invalid non-witness utxo key')
            elif self.non_witness_utxo is not None:
                raise PSBTError('Duplicated utxo value')
            else:
                l = compact.read_from(stream)
                if self.compress and self.txid and (self.vout is not None):
                    txout, txhash = self.TX_CLS.read_vout(stream, self.vout)
                    self._txhash = txhash
                    self._utxo = txout
                else:
                    tx = self.TX_CLS.read_from(stream)
                    self.non_witness_utxo = tx
            return
        v = read_string(stream)
        if k[0] == 1:
            if len(k) != 1:
                raise PSBTError('Invalid witness utxo key')
            elif self.witness_utxo is not None:
                raise PSBTError('Duplicated utxo value')
            else:
                self.witness_utxo = self.TXOUT_CLS.parse(v)
        elif k[0] == 2:
            if self.compress:
                return
            pub = ec.PublicKey.parse(k[1:])
            if pub in self.partial_sigs:
                raise PSBTError('Duplicated partial sig')
            else:
                self.partial_sigs[pub] = v
        elif k[0] == 3:
            if len(k) != 1:
                raise PSBTError('Invalid sighash type key')
            elif self.sighash_type is None:
                if len(v) != 4:
                    raise PSBTError('Sighash type should be 4 bytes long')
                self.sighash_type = int.from_bytes(v, 'little')
            else:
                raise PSBTError('Duplicated sighash type')
        elif k[0] == 4:
            if len(k) != 1:
                raise PSBTError('Invalid redeem script key')
            elif self.redeem_script is None:
                self.redeem_script = Script(v)
            else:
                raise PSBTError('Duplicated redeem script')
        elif k[0] == 5:
            if len(k) != 1:
                raise PSBTError('Invalid witness script key')
            elif self.witness_script is None:
                self.witness_script = Script(v)
            else:
                raise PSBTError('Duplicated witness script')
        elif k[0] == 6:
            pub = ec.PublicKey.parse(k[1:])
            if pub in self.bip32_derivations:
                raise PSBTError('Duplicated derivation path')
            else:
                self.bip32_derivations[pub] = DerivationPath.parse(v)
        elif k[0] == 7:
            if self.compress:
                return
            if len(k) != 1:
                raise PSBTError('Invalid final scriptsig key')
            elif self.final_scriptsig is None:
                self.final_scriptsig = Script(v)
            else:
                raise PSBTError('Duplicated final scriptsig')
        elif k[0] == 8:
            if self.compress:
                return
            if len(k) != 1:
                raise PSBTError('Invalid final scriptwitness key')
            elif self.final_scriptwitness is None:
                self.final_scriptwitness = Witness.parse(v)
            else:
                raise PSBTError('Duplicated final scriptwitness')
        elif k == b'\x0e':
            self.txid = bytes(reversed(v))
        elif k == b'\x0f':
            self.vout = int.from_bytes(v, 'little')
        elif k == b'\x10':
            self.sequence = int.from_bytes(v, 'little')
        elif k[0] == 20:
            if len(k) != 65:
                raise PSBTError('Invalid key length')
            pub = ec.PublicKey.from_xonly(k[1:33])
            leaf = k[33:]
            if (pub, leaf) in self.taproot_sigs:
                raise PSBTError('Duplicated taproot sig')
            self.taproot_sigs[pub, leaf] = v
        elif k[0] == 21:
            control_block = k[1:]
            if control_block in self.taproot_scripts:
                raise PSBTError('Duplicated taproot script')
            self.taproot_scripts[control_block] = v
        elif k[0] == 22:
            pub = ec.PublicKey.from_xonly(k[1:])
            if pub not in self.taproot_bip32_derivations:
                b = BytesIO(v)
                num_leaf_hashes = compact.read_from(b)
                leaf_hashes = [b.read(32) for i in range(num_leaf_hashes)]
                if not all([len(leaf) == 32 for leaf in leaf_hashes]):
                    raise PSBTError('Invalid length of taproot leaf hashes')
                der = DerivationPath.read_from(b)
                self.taproot_bip32_derivations[pub] = (leaf_hashes, der)
        elif k[0] == 23:
            self.taproot_internal_key = ec.PublicKey.from_xonly(v)
        elif k[0] == 24:
            self.taproot_merkle_root = v
        else:
            if k in self.unknown:
                raise PSBTError('Duplicated key')
            self.unknown[k] = v

    def write_to(self, stream, skip_separator=False, version=None, **kwargs):
        r = 0
        if self.non_witness_utxo is not None:
            r += stream.write(b'\x01\x00')
            r += ser_string(stream, self.non_witness_utxo.serialize())
        if self.witness_utxo is not None:
            r += stream.write(b'\x01\x01')
            r += ser_string(stream, self.witness_utxo.serialize())
        for pub in self.partial_sigs:
            r += ser_string(stream, b'\x02' + pub.serialize())
            r += ser_string(stream, self.partial_sigs[pub])
        if self.sighash_type is not None:
            r += stream.write(b'\x01\x03')
            r += ser_string(stream, self.sighash_type.to_bytes(4, 'little'))
        if self.redeem_script is not None:
            r += stream.write(b'\x01\x04')
            r += self.redeem_script.write_to(stream)
        if self.witness_script is not None:
            r += stream.write(b'\x01\x05')
            r += self.witness_script.write_to(stream)
        for pub in self.bip32_derivations:
            r += ser_string(stream, b'\x06' + pub.serialize())
            r += ser_string(stream, self.bip32_derivations[pub].serialize())
        if self.final_scriptsig is not None:
            r += stream.write(b'\x01\x07')
            r += self.final_scriptsig.write_to(stream)
        if self.final_scriptwitness is not None:
            r += stream.write(b'\x01\x08')
            r += ser_string(stream, self.final_scriptwitness.serialize())
        if version == 2:
            if self.txid is not None:
                r += ser_string(stream, b'\x0e')
                r += ser_string(stream, bytes(reversed(self.txid)))
            if self.vout is not None:
                r += ser_string(stream, b'\x0f')
                r += ser_string(stream, self.vout.to_bytes(4, 'little'))
            if self.sequence is not None:
                r += ser_string(stream, b'\x10')
                r += ser_string(stream, self.sequence.to_bytes(4, 'little'))
        for pub, leaf in self.taproot_sigs:
            r += ser_string(stream, b'\x14' + pub.xonly() + leaf)
            r += ser_string(stream, self.taproot_sigs[pub, leaf])
        for control_block in self.taproot_scripts:
            r += ser_string(stream, b'\x15' + control_block)
            r += ser_string(stream, self.taproot_scripts[control_block])
        for pub in self.taproot_bip32_derivations:
            r += ser_string(stream, b'\x16' + pub.xonly())
            leaf_hashes, derivation = self.taproot_bip32_derivations[pub]
            r += ser_string(stream, compact.to_bytes(len(leaf_hashes)) + b''.join(leaf_hashes) + derivation.serialize())
        if self.taproot_internal_key is not None:
            r += ser_string(stream, b'\x17')
            r += ser_string(stream, self.taproot_internal_key.xonly())
        if self.taproot_merkle_root is not None:
            r += ser_string(stream, b'\x18')
            r += ser_string(stream, self.taproot_merkle_root)
        for key in self.unknown:
            r += ser_string(stream, key)
            r += ser_string(stream, self.unknown[key])
        if not skip_separator:
            r += stream.write(b'\x00')
        return r

class OutputScope(PSBTScope):

    def __init__(self, unknown={}, vout=None, compress=CompressMode.KEEP_ALL):
        self.compress = compress
        self.value = None
        self.script_pubkey = None
        if vout is not None:
            self.value = vout.value
            self.script_pubkey = vout.script_pubkey
        self.unknown = unknown
        self.redeem_script = None
        self.witness_script = None
        self.bip32_derivations = OrderedDict()
        self.taproot_bip32_derivations = OrderedDict()
        self.taproot_internal_key = None
        self.parse_unknowns()

    def clear_metadata(self, compress=CompressMode.CLEAR_ALL):
        """Removes metadata like derivations, utxos etc except final or partial sigs"""
        if compress == CompressMode.KEEP_ALL:
            return
        self.unknown = {}
        self.redeem_script = None
        self.witness_script = None
        self.bip32_derivations = OrderedDict()
        self.taproot_bip32_derivations = OrderedDict()
        self.taproot_internal_key = None

    def update(self, other):
        self.value = other.value if other.value is not None else self.value
        self.script_pubkey = other.script_pubkey or self.script_pubkey
        self.unknown.update(other.unknown)
        self.redeem_script = other.redeem_script or self.redeem_script
        self.witness_script = other.witness_script or self.witness_script
        self.bip32_derivations.update(other.bip32_derivations)
        self.taproot_bip32_derivations.update(other.taproot_bip32_derivations)
        self.taproot_internal_key = other.taproot_internal_key

    @property
    def vout(self):
        return TransactionOutput(self.value, self.script_pubkey)

    def read_value(self, stream, k):
        if len(k) == 0:
            return
        v = read_string(stream)
        if k[0] == 0:
            if len(k) != 1:
                raise PSBTError('Invalid redeem script key')
            elif self.redeem_script is None:
                self.redeem_script = Script(v)
            else:
                raise PSBTError('Duplicated redeem script')
        elif k[0] == 1:
            if len(k) != 1:
                raise PSBTError('Invalid witness script key')
            elif self.witness_script is None:
                self.witness_script = Script(v)
            else:
                raise PSBTError('Duplicated witness script')
        elif k[0] == 2:
            pub = ec.PublicKey.parse(k[1:])
            if pub in self.bip32_derivations:
                raise PSBTError('Duplicated derivation path')
            else:
                self.bip32_derivations[pub] = DerivationPath.parse(v)
        elif k == b'\x03':
            self.value = int.from_bytes(v, 'little')
        elif k == b'\x04':
            self.script_pubkey = Script(v)
        elif k[0] == 5:
            self.taproot_internal_key = ec.PublicKey.from_xonly(v)
        elif k[0] == 7:
            pub = ec.PublicKey.from_xonly(k[1:])
            if pub not in self.taproot_bip32_derivations:
                b = BytesIO(v)
                num_leaf_hashes = compact.read_from(b)
                leaf_hashes = [b.read(32) for i in range(num_leaf_hashes)]
                if not all([len(leaf) == 32 for leaf in leaf_hashes]):
                    raise PSBTError('Invalid length of taproot leaf hashes')
                der = DerivationPath.read_from(b)
                self.taproot_bip32_derivations[pub] = (leaf_hashes, der)
        else:
            if k in self.unknown:
                raise PSBTError('Duplicated key')
            self.unknown[k] = v

    def write_to(self, stream, skip_separator=False, version=None, **kwargs):
        r = 0
        if self.redeem_script is not None:
            r += stream.write(b'\x01\x00')
            r += self.redeem_script.write_to(stream)
        if self.witness_script is not None:
            r += stream.write(b'\x01\x01')
            r += self.witness_script.write_to(stream)
        for pub in self.bip32_derivations:
            r += ser_string(stream, b'\x02' + pub.serialize())
            r += ser_string(stream, self.bip32_derivations[pub].serialize())
        if version == 2:
            if self.value is not None:
                r += ser_string(stream, b'\x03')
                r += ser_string(stream, self.value.to_bytes(8, 'little'))
            if self.script_pubkey is not None:
                r += ser_string(stream, b'\x04')
                r += self.script_pubkey.write_to(stream)
        if self.taproot_internal_key is not None:
            r += ser_string(stream, b'\x05')
            r += ser_string(stream, self.taproot_internal_key.xonly())
        for pub in self.taproot_bip32_derivations:
            r += ser_string(stream, b'\x07' + pub.xonly())
            leaf_hashes, derivation = self.taproot_bip32_derivations[pub]
            r += ser_string(stream, compact.to_bytes(len(leaf_hashes)) + b''.join(leaf_hashes) + derivation.serialize())
        for key in self.unknown:
            r += ser_string(stream, key)
            r += ser_string(stream, self.unknown[key])
        if not skip_separator:
            r += stream.write(b'\x00')
        return r

class PSBT(EmbitBase):
    MAGIC = b'psbt\xff'
    PSBTIN_CLS = InputScope
    PSBTOUT_CLS = OutputScope
    TX_CLS = Transaction

    def __init__(self, tx=None, unknown={}, version=None):
        self.version = version
        self.inputs = []
        self.outputs = []
        self.tx_version = None
        self.locktime = None
        if tx is not None:
            self.parse_tx(tx)
        self.unknown = unknown
        self.xpubs = OrderedDict()
        self.parse_unknowns()

    def parse_tx(self, tx):
        self.tx_version = tx.version
        self.locktime = tx.locktime
        self.inputs = [self.PSBTIN_CLS(vin=vin) for vin in tx.vin]
        self.outputs = [self.PSBTOUT_CLS(vout=vout) for vout in tx.vout]

    @property
    def tx(self):
        return self.TX_CLS(version=self.tx_version or 2, locktime=self.locktime or 0, vin=[inp.vin for inp in self.inputs], vout=[out.vout for out in self.outputs])

    def sighash_segwit(self, *args, **kwargs):
        return self.tx.sighash_segwit(*args, **kwargs)

    def sighash_legacy(self, *args, **kwargs):
        return self.tx.sighash_legacy(*args, **kwargs)

    def sighash_taproot(self, *args, **kwargs):
        return self.tx.sighash_taproot(*args, **kwargs)

    @property
    def is_verified(self):
        return all([inp.is_verified for inp in self.inputs])

    def verify(self, ignore_missing=False):
        for i, inp in enumerate(self.inputs):
            inp.verify(ignore_missing)
        return self.is_verified

    def utxo(self, i):
        if self.inputs[i].is_verified:
            return self.inputs[i].utxo
        if not (self.inputs[i].witness_utxo or self.inputs[i].non_witness_utxo):
            raise PSBTError('Missing previous utxo on input %d' % i)
        return self.inputs[i].witness_utxo or self.inputs[i].non_witness_utxo.vout[self.inputs[i].vout]

    def fee(self):
        fee = sum([self.utxo(i).value for i in range(len(self.inputs))])
        fee -= sum([out.value for out in self.tx.vout])
        return fee

    def write_to(self, stream):
        r = stream.write(self.MAGIC)
        if self.version != 2:
            r += stream.write(b'\x01\x00')
            tx = self.tx.serialize()
            r += ser_string(stream, tx)
        for xpub in self.xpubs:
            r += ser_string(stream, b'\x01' + xpub.serialize())
            r += ser_string(stream, self.xpubs[xpub].serialize())
        if self.version == 2:
            if self.tx_version is not None:
                r += ser_string(stream, b'\x02')
                r += ser_string(stream, self.tx_version.to_bytes(4, 'little'))
            if self.locktime is not None:
                r += ser_string(stream, b'\x03')
                r += ser_string(stream, self.locktime.to_bytes(4, 'little'))
            r += ser_string(stream, b'\x04')
            r += ser_string(stream, compact.to_bytes(len(self.inputs)))
            r += ser_string(stream, b'\x05')
            r += ser_string(stream, compact.to_bytes(len(self.outputs)))
            r += ser_string(stream, b'\xfb')
            r += ser_string(stream, self.version.to_bytes(4, 'little'))
        for key in self.unknown:
            r += ser_string(stream, key)
            r += ser_string(stream, self.unknown[key])
        r += stream.write(b'\x00')
        for inp in self.inputs:
            r += inp.write_to(stream, version=self.version)
        for out in self.outputs:
            r += out.write_to(stream, version=self.version)
        return r

    @classmethod
    def from_base64(cls, b64, compress=CompressMode.KEEP_ALL):
        raw = a2b_base64(b64)
        return cls.parse(raw, compress=compress)

    def to_base64(self):
        return b2a_base64(self.serialize()).strip().decode()

    def to_string(self, encoding='base64'):
        if encoding == 'base64':
            return self.to_base64()
        else:
            return hexlify(self.serialize()).decode()

    @classmethod
    def from_string(cls, s, compress=CompressMode.KEEP_ALL):
        if s.startswith(hexlify(cls.MAGIC).decode()):
            return cls.parse(unhexlify(s), compress=compress)
        else:
            return cls.from_base64(s, compress=compress)

    @classmethod
    def read_from(cls, stream, compress=CompressMode.KEEP_ALL):
        """
        Compress flag allows to load and verify non_witness_utxo
        without storing them in memory and save the utxo internally for signing.
        This helps against out-of-memory errors.
        """
        tx = None
        unknown = {}
        version = None
        if stream.read(len(cls.MAGIC)) != cls.MAGIC:
            raise PSBTError('Invalid PSBT magic')
        while True:
            key = read_string(stream)
            if len(key) == 0:
                break
            value = read_string(stream)
            if key == b'\x00':
                if tx is None:
                    tx = cls.TX_CLS.parse(value)
                else:
                    raise PSBTError('Failed to parse PSBT - duplicated transaction field')
            elif key == b'\xfb':
                version = int.from_bytes(value, 'little')
            else:
                if key in unknown:
                    raise PSBTError('Duplicated key')
                unknown[key] = value
        if tx and version == 2:
            raise PSBTError('Global TX field is not allowed in PSBTv2')
        psbt = cls(tx, unknown, version=version)
        for i, vin in enumerate(psbt.tx.vin):
            psbt.inputs[i] = cls.PSBTIN_CLS.read_from(stream, compress=compress, vin=vin)
        for i, vout in enumerate(psbt.tx.vout):
            psbt.outputs[i] = cls.PSBTOUT_CLS.read_from(stream, compress=compress, vout=vout)
        return psbt

    def parse_unknowns(self):
        for k in list(self.unknown):
            if k[0] == 1:
                xpub = bip32.HDKey.parse(k[1:])
                self.xpubs[xpub] = DerivationPath.parse(self.unknown.pop(k))
            elif k == b'\x02':
                self.tx_version = int.from_bytes(self.unknown.pop(k), 'little')
            elif k == b'\x03':
                self.locktime = int.from_bytes(self.unknown.pop(k), 'little')
            elif k == b'\x04':
                if len(self.inputs) > 0:
                    raise PSBTError('Inputs already initialized')
                self.inputs = [self.PSBTIN_CLS() for _ in range(compact.from_bytes(self.unknown.pop(k)))]
            elif k == b'\x05':
                if len(self.outputs) > 0:
                    raise PSBTError('Outputs already initialized')
                self.outputs = [self.PSBTOUT_CLS() for _ in range(compact.from_bytes(self.unknown.pop(k)))]

    def sighash(self, i, sighash=SIGHASH.ALL, **kwargs):
        inp = self.inputs[i]
        if inp.is_taproot:
            values = [inp.utxo.value for inp in self.inputs]
            scripts = [inp.utxo.script_pubkey for inp in self.inputs]
            return self.sighash_taproot(i, script_pubkeys=scripts, values=values, sighash=sighash, **kwargs)
        value = inp.utxo.value
        sc = inp.witness_script or inp.redeem_script or inp.utxo.script_pubkey
        is_segwit = inp.witness_script or inp.witness_utxo or inp.utxo.script_pubkey.script_type() in {'p2wpkh', 'p2wsh'} or (inp.redeem_script and inp.redeem_script.script_type() in {'p2wpkh', 'p2wsh'})
        if sc.script_type() == 'p2wpkh':
            sc = script.p2pkh_from_p2wpkh(sc)
        if is_segwit:
            h = self.sighash_segwit(i, sc, value, sighash=sighash)
        else:
            h = self.sighash_legacy(i, sc, sighash=sighash)
        return h

    def sign_input_with_tapkey(self, key, input_index, inp=None, sighash=SIGHASH.DEFAULT):
        """Sign taproot input with key. Signs with internal or leaf key."""
        inp = inp or self.inputs[input_index]
        if not inp.is_taproot:
            return 0
        pk = key.taproot_tweak(inp.taproot_merkle_root or b'')
        if pk.xonly() in inp.utxo.script_pubkey.data:
            h = self.sighash(input_index, sighash=sighash)
            sig = pk.schnorr_sign(h)
            wit = sig.serialize()
            if sighash != SIGHASH.DEFAULT:
                wit += bytes([sighash])
            inp.final_scriptwitness = Witness([wit])
            return 1
        counter = 0
        pub = ec.PublicKey.from_xonly(key.xonly())
        for ctrl, sc in inp.taproot_scripts.items():
            if pub.xonly() not in sc:
                continue
            leaf_version = sc[-1]
            script = Script(sc[:-1])
            h = self.sighash(input_index, sighash=sighash, ext_flag=1, script=script, leaf_version=leaf_version)
            sig = key.schnorr_sign(h)
            leaf = hashes.tagged_hash('TapLeaf', bytes([leaf_version]) + script.serialize())
            sigdata = sig.serialize()
            if sighash != SIGHASH.DEFAULT:
                sigdata += bytes([sighash])
            inp.taproot_sigs[pub, leaf] = sigdata
            counter += 1
        return counter

    def sign_with(self, root, sighash=SIGHASH.DEFAULT):
        """
        Signs psbt with root key (HDKey or similar).
        Returns number of signatures added to PSBT.
        Sighash kwarg is set to SIGHASH.DEFAULT,
        for segwit and legacy it's replaced to SIGHASH.ALL
        so if PSBT is asking to sign with a different sighash this function won't sign.
        If you want to sign with sighashes provided in the PSBT - set sighash=None.
        """
        counter = 0
        if hasattr(root, 'keys'):
            for k in root.keys:
                if hasattr(k, 'is_private') and k.is_private:
                    counter += self.sign_with(k, sighash)
            return counter
        fingerprint = None
        if hasattr(root, 'origin'):
            if not root.is_private:
                return 0
            if root.is_extended:
                fingerprint = root.fingerprint
            else:
                root = root.key
        if not fingerprint and hasattr(root, 'my_fingerprint'):
            fingerprint = root.my_fingerprint
        rootpub = root.get_public_key()
        sec = rootpub.sec()
        pkh = hashes.hash160(sec)
        counter = 0
        for i, inp in enumerate(self.inputs):
            required_sighash = sighash
            if not inp.is_taproot and required_sighash == SIGHASH.DEFAULT:
                required_sighash = SIGHASH.ALL
            inp_sighash = inp.sighash_type
            if inp_sighash is None:
                inp_sighash = required_sighash or SIGHASH.DEFAULT
            if not inp.is_taproot and inp_sighash == SIGHASH.DEFAULT:
                inp_sighash = SIGHASH.ALL
            if required_sighash is not None and inp_sighash != required_sighash:
                if inp_sighash not in {SIGHASH.DEFAULT, SIGHASH.ALL} or required_sighash not in {SIGHASH.DEFAULT, SIGHASH.ALL}:
                    continue
            bip32_derivations = set()
            if fingerprint:
                for pub in inp.taproot_bip32_derivations:
                    _leafs, derivation = inp.taproot_bip32_derivations[pub]
                    if derivation.fingerprint == fingerprint:
                        bip32_derivations.add((pub, derivation))
                for pub in inp.bip32_derivations:
                    derivation = inp.bip32_derivations[pub]
                    if derivation.fingerprint == fingerprint:
                        bip32_derivations.add((pub, derivation))
            derived_keypairs = set()
            for pub, derivation in bip32_derivations:
                der = derivation.derivation
                if hasattr(root, 'origin'):
                    if root.origin:
                        if root.origin.derivation != der[:len(root.origin.derivation)]:
                            continue
                        der = der[len(root.origin.derivation):]
                    hdkey = root.key.derive(der)
                else:
                    hdkey = root.derive(der)
                if hdkey.xonly() != pub.xonly():
                    raise PSBTError("Derivation path doesn't look right")
                derived_keypairs.add((hdkey.key, pub))
            if inp.is_taproot:
                counter += self.sign_input_with_tapkey(root, i, inp, sighash=inp_sighash)
                for prv, pub in derived_keypairs:
                    counter += self.sign_input_with_tapkey(prv, i, inp, sighash=inp_sighash)
                continue
            h = self.sighash(i, sighash=inp_sighash)
            sc = inp.witness_script or inp.redeem_script or inp.utxo.script_pubkey
            if sec in sc.data or pkh in sc.data:
                sig = root.sign(h)
                inp.partial_sigs[rootpub] = sig.serialize() + bytes([inp_sighash])
                counter += 1
            for prv, pub in derived_keypairs:
                sig = prv.sign(h)
                inp.partial_sigs[pub] = sig.serialize() + bytes([inp_sighash])
                counter += 1
        return counter
