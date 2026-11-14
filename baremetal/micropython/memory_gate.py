# SPDX-License-Identifier: MIT
# Public synthetic data only. Erased objects/aliases are not reused as dict keys.
import _native_memory as memory
from seedsigner_port.memory_fixtures import FROZEN_BYTES,FROZEN_TEXT
import gc
import camera
from embit import bip39
from shamir_mnemonic import wordlist
from seedsigner_port.secure_delete import wipe_bytes,wipe_string,wipe_list
baseline=camera.settings()['rust_heap_bytes']
for size in (1,15,16,17,63,64,65,4096):
    b=bytearray((i%251+1 for i in range(size)))
    assert memory.wipe(b) is True
    assert b==bytearray(size)
    b=bytes(bytearray((i%251+1 for i in range(size))))
    alias=b
    wipe_bytes(b)
    assert alias==bytes(size)
    b=''.join(('public-wipe-',str(size),'-',bytearray((i%251+1 for i in range(size))).hex(),'-synthetic'))
    n=len(b.encode())
    wipe_string(b)
    assert b=='\x00'*n
    s=bytes((0xe3,0x82,0xac,0xc3,0xa9,0x61)).decode()
    wipe_string(s)
    assert s=='\x00'*6
# Static/frozen and interned storage is protected, including public wordlists.
for word in bip39.WORDLIST:
    assert memory.wipe(word) is False
assert len(bip39.WORDLIST)==2048 and bip39.WORDLIST[0]=='abandon' and bip39.WORDLIST[-1]=='zoo'
items=list(bip39.WORDLIST)
wipe_list(items)
assert items==[] and len(bip39.WORDLIST)==2048 and bip39.WORDLIST[0]=='abandon'
try:
    wipe_list(bip39.WORDLIST)
    assert False
except ValueError:pass
for word in wordlist.WORDLIST:assert memory.wipe(word) is False
try:
    wipe_list(wordlist.WORDLIST)
    assert False
except ValueError:pass
assert len(wordlist.WORDLIST)==1024
assert memory.wipe(FROZEN_TEXT) is False
assert memory.wipe(FROZEN_BYTES) is False
assert FROZEN_TEXT=='public-frozen-text-wipe-guard' and FROZEN_BYTES==b'public-frozen-bytes-wipe-guard'
assert memory.wipe(None) is False
for value in (1,[],{},memoryview(bytearray(5))):
    try:memory.wipe(value);assert False
    except TypeError:pass
# Adjacent/live allocations remain intact after clearing repeatedly.
for i in range(100):
    left=bytearray(b'L'*63)
    target=bytearray(b'T'*65)
    right=bytearray(b'R'*63)
    wipe_bytes(target)
    assert left==b'L'*63 and right==b'R'*63 and target==bytes(65)
    del left,target,right
    gc.collect()
assert bip39.mnemonic_is_valid('abandon '*11+'about')
assert camera.settings()['rust_heap_bytes']==baseline
print('@@PASS native-memory-owned-buffer-and-frozen-guards')
