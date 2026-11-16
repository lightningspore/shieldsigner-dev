# SPDX-License-Identifier: MIT
# Public secp256k1 generator fixtures; actual native library, no private wallet data.
import secp256k1 as c
import binascii
import time

one = bytes(31) + b'\x01'
two = bytes(31) + b'\x02'
start = time.ticks_ms()
p = c.ec_pubkey_create(one)
assert (
    c.ec_pubkey_serialize(p).hex()
    == '0279be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798'
)
assert c.ec_pubkey_parse(c.ec_pubkey_serialize(p)) == p
assert c.ec_privkey_add(one, one) == two
assert c.ec_pubkey_add(p, one) == c.ec_pubkey_create(two)
assert (
    c.ec_pubkey_serialize(c.ec_pubkey_create(two)).hex()
    == '02c6047f9441ed7d6d3045406e95c07cd85c778e4b8cef3ca7abac09b95c709ee5'
)
assert c.context_status()['context_bytes'] <= 4096
print(
    '@@PASS actual-secp256k1-generator', (time.ticks_ms() - start) & 0xFFFFFFFF, c.context_status()
)
