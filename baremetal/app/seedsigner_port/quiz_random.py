# SPDX-License-Identifier: MIT
"""Non-secret backup quiz ordering using the pinned MicroPython PRNG.

Predictably seeded from a clock on import. Not an entropy source; never use for
keys, nonces or seed generation. The original seed Views bind only their random
import here; secrets/hardware entropy APIs and their health state are unchanged.
Deterministic integer seeds repeat on this runtime, not CPython's MT sequence.
"""
import random as _random
import time

def seed(value=None):
    if value is None:value=time.ticks_ms()
    _random.seed(value)

def random():return _random.random()

def shuffle(items):
    # Fisher-Yates with rejection sampling rather than biased modulo reduction.
    for end in range(len(items)-1,0,-1):
        bits=1;limit=end+1
        while limit>>bits:bits+=1
        choice=_random.getrandbits(bits)
        while choice>end:choice=_random.getrandbits(bits)
        items[end],items[choice]=items[choice],items[end]
seed()
