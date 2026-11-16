# SPDX-License-Identifier: MIT
"""Source QR models pass ASCII text to binascii; MicroPython needs a buffer."""

import binascii


def a2b_base64(value):
    if isinstance(value, str):
        if any(ord(char) > 127 for char in value):
            raise ValueError('Base64 text must contain only ASCII characters')
        value = value.encode('utf-8')
    return binascii.a2b_base64(value)
