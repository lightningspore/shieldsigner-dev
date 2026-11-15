# Original SeedSigner/Krux source; see LICENSE.SeedSigner and LICENSE.Krux-QR
# Generated format providers; unavailable crypto remains explicit.
from seedsigner_port.decode_platform import dependency as _dependency,FeatureUnavailable
try:
    UnicodeDecodeError
except NameError:
    UnicodeDecodeError=UnicodeError
class WIFKey:
    """Container for a single WIF-encoded private key."""

    def __init__(self, wif):
        try:
            self.privkey = _dependency('embit', 'ec').PrivateKey.from_wif(wif)
        except FeatureUnavailable:
            raise
        except Exception as e:
            raise _dependency('seedsigner.models.seed', 'InvalidSeedException')('Invalid WIF') from e
        self.wif = wif

    def get_fingerprint(self, network=_dependency('seedsigner.models.settings', 'SettingsConstants').MAINNET):
        """Return BIP32-style fingerprint for the key's public key."""
        pub = self.privkey.get_public_key()
        fp = _dependency('embit', 'hashes').hash160(pub.sec())[:4]
        return _dependency('binascii', 'hexlify')(fp).decode()
