# Copyright2021 SeedSigner; MIT, see ../LICENSE.SeedSigner
from seedsigner_port.decode_platform import dependency as _dependency, FeatureUnavailable


class EncryptedQRStorage:
    def __init__(self):
        self._encryptedqr = None

    @property
    def encryptedqr(self):
        return self._encryptedqr

    def set_encryptedqr(self, encryptedqr):
        self._encryptedqr = encryptedqr

    def clear_encryptedqr(self):
        self._encryptedqr = None
