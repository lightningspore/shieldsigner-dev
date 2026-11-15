# SPDX-License-Identifier: MIT
"""The sorted lower-bound operation needed by the pinned QR encoder."""
def bisect_left(values,value,lo=0,hi=None):
    if lo<0:raise ValueError('lo must be nonnegative')
    if hi is None:hi=len(values)
    while lo<hi:
        mid=(lo+hi)//2
        if values[mid]<value:lo=mid+1
        else:hi=mid
    return lo
