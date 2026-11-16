# SPDX-License-Identifier: MIT
"""Resolve actual optional module methods; never synthesize implementation results."""

from seedsigner_port.decode_platform import dependency


class DeferredModule:
    def __init__(self, name):
        self.name = name

    def __getattr__(self, name):
        return getattr(dependency(self.name), name)
