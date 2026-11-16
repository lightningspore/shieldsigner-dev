# SPDX-License-Identifier: MIT
"""Published BIP32/BIP340 and CPython embit ECDSA/ECDH fixtures for real native C."""

import pyformat  # noqa: F401  (formats generated Python on write)
import csv, hashlib, io, json, urllib.request
from pathlib import Path
from embit import bip32, ec

assert ec.secp256k1.ecdsa_sign.__module__ == 'embit.util.ctypes_secp256k1'
root = Path(__file__).resolve().parents[1]
cache = root / '.tools/secp-vectors'
cache.mkdir(parents=True, exist_ok=True)
sources = {
    'bip32.mediawiki': (
        'https://raw.githubusercontent.com/bitcoin/bips/master/bip-0032.mediawiki',
        'e5e00a8289db2f681052cf24a745320afc225e66b25d1e489a7c884d2fc7f11f',
    ),
    'bip340.csv': (
        'https://raw.githubusercontent.com/bitcoin/bips/master/bip-0340/test-vectors.csv',
        '34c9d1d9c3a88d524bc80778540dc43f8306ec249a7485293063c376db851c2d',
    ),
}
for name, (url, sha) in sources.items():
    p = cache / name
    if not p.exists():
        data = urllib.request.urlopen(url, timeout=60).read()
        assert hashlib.sha256(data).hexdigest() == sha
        p.write_bytes(data)
    assert hashlib.sha256(p.read_bytes()).hexdigest() == sha
code = '''# Generated PUBLIC vectors only; no private wallet data.
import secp256k1 as c
from embit import bip32,bip39,ec
from seedsigner_port.seed import Seed
from seedsigner_port.decode_platform import FeatureUnavailable
import binascii
import camera
import gc
import time
baseline=camera.settings()['rust_heap_bytes']
start=time.ticks_ms()
c.context_randomize(bytes(range(32)))
assert c.context_status()['randomized']
'''


def literal(data):
    return "binascii.unhexlify('" + data.hex() + "')"


# All four valid BIP32 vectors, including retained leading zero bytes.
text = (cache / 'bip32.mediawiki').read_text()
seed = None
path = None
pub = None
count = 0
for line in text.split('===Test vector 5===')[0].splitlines():
    if line.startswith('Seed (hex): '):
        seed = bytes.fromhex(line.split(': ')[1])
    elif line.startswith('* Chain '):
        path = line[8:].replace('<sub>H</sub>', "'")
    elif line.startswith('** ext pub: '):
        pub = line.split(': ')[1]
    elif line.startswith('** ext prv: '):
        prv = line.split(': ')[1]
        reference = bip32.HDKey.from_seed(seed).derive(path)
        assert reference.to_base58() == prv and reference.to_public().to_base58() == pub
        code += f"root=bip32.HDKey.from_seed({literal(seed)})\nkey=root.derive({path!r})\nassert key.to_base58()=={prv!r}\nassert key.to_public().to_base58()=={pub!r}\nassert bip32.HDKey.from_string({prv!r}).serialize()==key.serialize()\nassert bip32.HDKey.from_string({pub!r}).serialize()==key.to_public().serialize()\n"
        if '/' in path and not path.endswith("'"):
            parent_path, index = path.rsplit('/', 1)
            code += f"assert root.derive({parent_path!r}).to_public().child({int(index)}).to_base58()=={pub!r}\n"
        code += 'gc.collect()\n'
        count += 1
invalid = []
for line in text.split('===Test vector 5===')[1].split('==Acknowledgements==')[0].splitlines():
    if line.startswith('* '):
        invalid.append(line[2:].split()[0])
for bad in invalid:
    try:
        bip32.HDKey.from_string(bad)
    except Exception:
        pass
    else:
        raise AssertionError('CPython embit accepted published invalid key')
    code += f"try:\n    bip32.HDKey.from_string({bad!r})\n    assert False\nexcept (ValueError,ec.ECError,bip32.HDError):pass\n"
code += f"print('@@BIP32_PASS',{count},{len(invalid)})\n"
rows = list(csv.DictReader(io.StringIO((cache / 'bip340.csv').read_text())))
for row in rows:
    pub = bytes.fromhex(row['public key'])
    msg = bytes.fromhex(row['message'])
    sig = bytes.fromhex(row['signature'])
    expected = row['verification result'] == 'TRUE'
    code += f"signature={literal(sig)}\nmessage={literal(msg)}\nresult=False\ntry:\n    point=c.xonly_pubkey_parse({literal(pub)})\n    result=c.schnorrsig_verify(signature,message,point)\nexcept ValueError:pass\nassert result is {expected}\n"
    if row['secret key']:
        code += f"secret={literal(bytes.fromhex(row['secret key']))}\nassert c.xonly_pubkey_serialize(c.ec_pubkey_create(secret))=={literal(pub)}\nassert c.schnorrsig_sign(message,secret,extra_data={literal(bytes.fromhex(row['aux_rand']))})==signature\n"
    code += 'gc.collect()\n'
code += f"print('@@BIP340_PASS',{len(rows)})\n"
# Original embit fingerprint result, including the finalization screen's exact API.
bip = json.loads((root / '.tools/bip39-vectors.json').read_text())['english']
for _, mnemonic, seed, xprv in bip:
    reference = bip32.HDKey.from_seed(bytes.fromhex(seed))
    assert reference.to_base58() == xprv
    fingerprint = reference.child(0).fingerprint.hex()
    code += f"s=Seed({mnemonic!r}.split(),passphrase='TREZOR')\nassert s.get_root().to_base58()=={xprv!r}\nassert s.get_fingerprint()=={fingerprint!r}\ns.wipe()\ngc.collect()\n"
# Deterministic ECDSA DER/verify/grinding and default SHA256 ECDH via actual host embit.
for scalar in (1, 2, 3, 17, 256, 65537):
    secret = scalar.to_bytes(32, 'big')
    message = hashlib.sha256(b'public-native-curve-' + secret).digest()
    key = ec.PrivateKey(secret)
    for grind in (False, True):
        der = key.sign(message, grind=grind).serialize()
        code += f"key=ec.PrivateKey({literal(secret)})\nmessage={literal(message)}\nsig=key.sign(message,grind={grind})\nassert sig.serialize()=={literal(der)}\nassert key.verify(sig,message)\nassert not key.verify(sig,bytes(32))\nassert ec.Signature.parse(sig.serialize()).serialize()==sig.serialize()\n"
    peer = ec.PrivateKey((scalar + 1).to_bytes(32, 'big'))
    shared = key.ecdh(peer.to_public())
    code += f"peer=ec.PrivateKey({literal(peer.secret)})\nassert key.ecdh(peer.to_public())=={literal(shared)}\nassert key.ecdh(peer.to_public())==peer.ecdh(key.to_public())\n"
    code += 'recovered=c.ecdsa_sign_recoverable(message,key.secret)\nassert c.ecdsa_recover(recovered,message)==c.ec_pubkey_create(key.secret)\ncompact,recid=c.ecdsa_recoverable_signature_serialize_compact(recovered)\nassert c.ecdsa_recoverable_signature_parse_compact(compact,recid)==recovered\n'
code += '''one=bytes(31)+bytes((1,))
two=bytes(31)+bytes((2,))
p=c.ec_pubkey_create(one)
assert c.ec_privkey_add(one,one)==two
assert c.ec_privkey_mul(two,two)==bytes(31)+bytes((4,))
assert c.ec_pubkey_mul(p,two)==c.ec_pubkey_create(two)
assert c.ec_pubkey_add(p,one)==c.ec_pubkey_create(two)
assert c.ec_pubkey_create(c.ec_privkey_negate(one))==c.ec_pubkey_negate(p)
for length in (0,1,31,33,63,65,96):
    invalid=bytes(length)
    for function in (c.ec_seckey_verify,c.ec_pubkey_create):
        try:function(invalid);assert False
        except ValueError:pass
for invalid in (bytes(32),b'\\xff'*32):assert not c.ec_seckey_verify(invalid)
for invalid in (bytes(64),b'\\xff'*64):
    try:c.ec_pubkey_serialize(invalid);assert False
    except ValueError:pass
for i in range(100):
    for invalid in (b'',b'0',bytes(71)):
        try:c.ecdsa_signature_parse_der(invalid);assert False
        except ValueError:pass
    assert c.ec_pubkey_serialize(c.ec_pubkey_create(one))==c.ec_pubkey_serialize(p)
try:c.ecdsa_sign(bytes(32),one,nonce_function=lambda:None);assert False
except FeatureUnavailable:pass
point=c.ec_pubkey_create(one)
message=bytes(32)
sig=c.ecdsa_sign(message,one)
order=int('fffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364141',16)
high=sig[:32]+(order-int.from_bytes(sig[32:],'big')).to_bytes(32,'big')
assert not c.ecdsa_verify(high,message,point)
assert c.ecdsa_signature_normalize(high)==sig
keypair=c.keypair_create(one)
assert c.schnorrsig_sign(message,keypair)==c.schnorrsig_sign(message,one)
try:c.schnorrsig_sign(message,keypair[:32]+bytes(64));assert False
except ValueError:pass
private=bytearray(one)
c.ec_privkey_tweak_add(private,one)
assert private==two
public=bytearray(point)
c.ec_pubkey_tweak_mul(public,two)
assert public==c.ec_pubkey_create(two)
c.context_randomize(None)
assert not c.context_status()['randomized']
for i in range(3):gc.collect()
assert camera.settings()['rust_heap_bytes']==baseline
print('@@PASS actual-native-curves-bip32-bip340-ecdsa-ecdh',(time.ticks_ms()-start)&0xffffffff)
'''
(root / 'micropython/secp_gate.py').write_text(code)
(root / 'app/secp-vectors-provenance.json').write_text(
    json.dumps(
        {
            'sources': {name: {'url': url, 'sha256': sha} for name, (url, sha) in sources.items()},
            'bip32ValidPaths': count,
            'bip32InvalidKeys': len(invalid),
            'bip340Rows': len(rows),
            'bip39FingerprintCases': 24,
            'ecdsaReference': 'CPython embit0.8.0 '
            + ec.secp256k1.ecdsa_sign.__module__
            + ', public inputs',
            'generatedSha256': hashlib.sha256(
                (root / 'micropython/secp_gate.py').read_bytes()
            ).hexdigest(),
        },
        indent=2,
    )
    + '\n'
)
print('Prepared', count, 'BIP32 paths,', len(invalid), 'invalid keys and', len(rows), 'BIP340 rows')
