# SPDX-License-Identifier: MIT
# Behavioral platform port of SeedSigner helpers/secure_delete.py.
# Copyright2021 SeedSigner; see ../LICENSE.SeedSigner.
"""Best effort clear of discarded caller-owned buffers, then drop references.

Native GC allocation checks protect frozen/qstr/external storage. MicroPython
has no CPython refcounts: callers must discard aliases and never wipe dictionary
keys. Copies/temporaries/interned strings are not promised erased.
"""
import _native_memory

def wipe_bytes(value):
    if isinstance(value,(bytes,bytearray)):
        _native_memory.wipe(value)

def wipe_string(value):
    if value is not None and isinstance(value,str):
        _native_memory.wipe(value)

def wipe_list(value):
    if value is None:return
    # Shared wordlist contents must remain usable after a Seed is discarded.
    from embit import bip39
    from shamir_mnemonic import wordlist
    if value is wordlist.WORDLIST:raise ValueError('Cannot clear shared wordlist')
    if value is bip39.WORDLIST:raise ValueError('Cannot clear shared wordlist')
    for item in value:
        if isinstance(item,(bytes,bytearray)):wipe_bytes(item)
        elif isinstance(item,str):wipe_string(item)
    value.clear()
