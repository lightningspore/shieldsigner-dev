# SPDX-License-Identifier: MIT
"""Monotonic time for native inactivity/elapsed measurements; no claimed RTC."""

import time as _time

_last = _time.ticks_ms()
_total = _last


def time():
    global _last, _total
    now = _time.ticks_ms()
    _total += (now - _last) & 0xFFFFFFFF
    _last = now
    return _total / 1000


def sleep(seconds):
    if seconds < 0 or seconds > 0x7FFFFFFF / 1000:
        raise ValueError("Sleep interval out of range")
    _time.sleep_ms(int(seconds * 1000))


sleep_ms = _time.sleep_ms
ticks_ms = _time.ticks_ms
