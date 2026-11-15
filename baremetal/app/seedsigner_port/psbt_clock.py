# SPDX-License-Identifier: MIT
"""Actual standard wall-clock/date boundary; never substitute boot uptime."""
import time as _time
from seedsigner_port.decode_platform import FeatureUnavailable

def _provider(name):
    value=getattr(_time,name,None)
    if value is None:raise FeatureUnavailable('PSBT wall-clock/date provider unavailable: time.'+name)
    return value

def time():return _provider('time')()
def gmtime(stamp):return _provider('gmtime')(stamp)
def strftime(pattern,value):return _provider('strftime')(pattern,value)
