# SPDX-License-Identifier: MIT
"""CPython zero-padding semantics used by the original compact SeedQR encoder."""


def zfill(value, width):
    count = max(0, width - len(value))
    if value[:1] in ('+', '-'):
        return value[:1] + '0' * count + value[1:]
    return '0' * count + value
