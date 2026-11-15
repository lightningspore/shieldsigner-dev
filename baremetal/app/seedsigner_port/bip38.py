# Original SeedSigner/Krux source; see LICENSE.SeedSigner and LICENSE.Krux-QR
# Generated format providers; unavailable crypto remains explicit.
from seedsigner_port.decode_platform import dependency as _dependency,FeatureUnavailable
try:
    UnicodeDecodeError
except NameError:
    UnicodeDecodeError=UnicodeError
class BIP38Key:
    """Container for a BIP38 encrypted private key."""

    def __init__(self, encrypted):
        self.encrypted = encrypted
        try:
            data = _dependency('embit', 'base58').decode_check(encrypted)
        except FeatureUnavailable:
            raise
        except Exception as e:
            raise _dependency('seedsigner.models.seed', 'InvalidSeedException')('Invalid BIP38') from e
        if len(data) != 39 or data[0] != 1 or data[1] != 66:
            raise _dependency('seedsigner.models.seed', 'InvalidSeedException')('Invalid BIP38')
        flagbyte = data[2]
        self.compressed = bool(flagbyte & 32)
        self.address_hash = data[3:7]
        self.encrypted_half1 = data[7:23]
        self.encrypted_half2 = data[23:39]

    def decrypt(self, passphrase, network=_dependency('seedsigner.models.settings', 'SettingsConstants').MAINNET):
        _dependency('hashlib', 'scrypt')
        _dependency('Cryptodome.Cipher', 'AES')
        'Decrypt the BIP38 key using the given passphrase.'
        derived = _dependency('hashlib', None).scrypt(passphrase.encode('utf-8'), salt=self.address_hash, n=16384, r=8, p=8, dklen=64)
        derivedhalf1 = derived[:32]
        derivedhalf2 = derived[32:]
        aes = _dependency('Cryptodome.Cipher', 'AES').new(derivedhalf2, _dependency('Cryptodome.Cipher', 'AES').MODE_ECB)
        decrypted_half1 = aes.decrypt(self.encrypted_half1)
        decrypted_half2 = aes.decrypt(self.encrypted_half2)
        priv = bytearray(32)
        for i in range(16):
            priv[i] = decrypted_half1[i] ^ derivedhalf1[i]
            priv[i + 16] = decrypted_half2[i] ^ derivedhalf1[i + 16]
        priv = bytes(priv)
        pub = _dependency('embit', 'ec').PrivateKey(priv).get_public_key()
        if not self.compressed:
            pub.compressed = False
        prefix = b'\x00' if network == _dependency('seedsigner.models.settings', 'SettingsConstants').MAINNET else b'o'
        h160 = _dependency('embit', 'hashes').hash160(pub.sec())
        addr = _dependency('embit', 'base58').encode_check(prefix + h160)
        if _dependency('embit', 'hashes').double_sha256(addr.encode('ascii'))[:4] != self.address_hash:
            raise _dependency('seedsigner.models.seed', 'InvalidSeedException')('Invalid passphrase')
        wif_prefix = b'\x80' if network == _dependency('seedsigner.models.settings', 'SettingsConstants').MAINNET else b'\xef'
        wif_bytes = wif_prefix + priv + (b'\x01' if self.compressed else b'')
        wif = _dependency('embit', 'base58').encode_check(wif_bytes)
        return _dependency('seedsigner.models.wif', 'WIFKey')(wif)
