# Original SeedSigner/Krux source; see LICENSE.SeedSigner and LICENSE.Krux-QR
# Generated format providers; unavailable crypto remains explicit.
from seedsigner_port.decode_platform import dependency as _dependency,FeatureUnavailable
try:
    UnicodeDecodeError
except NameError:
    UnicodeDecodeError=UnicodeError
QR_CODE_ITER_MULTIPLE = 10000

class EncryptedQRCode:
    """Creates and decrypts encrypted mnemonic QR codes"""

    def __init__(self):
        self.settings = _dependency('seedsigner.models.settings', 'Settings').get_instance()
        self.mnemonic_id = None
        self.version = None
        self.iterations = self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__ENCRYPTION_ITER) * QR_CODE_ITER_MULTIPLE
        self.encrypted_data = None

    def add_delta(self, delta=None):
        """Add a small delta to the number of PBKDF2 iterations as extra bits of entropy"""
        if delta:
            self.iterations += delta
        else:
            max_delta = self.iterations // 10
            self.iterations += int(_dependency('time', None).time() * 1000) % max_delta

    def create(self, key, mnemonic_id, mnemonic, i_vector=None):
        _dependency('Cryptodome.Cipher', 'AES')
        'encrypted mnemonic QR codes'
        mode_name = self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__ENCRYPTION_MODE)
        encryptor = _dependency('seedsigner.helpers', 'kef').Cipher(key, mnemonic_id, self.iterations)
        bytes_to_encrypt = _dependency('embit', 'bip39').mnemonic_to_bytes(mnemonic)
        self.version = _dependency('seedsigner.helpers', 'kef').suggest_versions(bytes_to_encrypt, mode_name)[0]
        bytes_encrypted = encryptor.encrypt(bytes_to_encrypt, self.version, i_vector)
        return _dependency('seedsigner.helpers', 'kef').wrap(mnemonic_id, self.version, self.iterations, bytes_encrypted)

    def public_data(self, data):
        """Parse and returns encrypted mnemonic QR codes public data"""
        try:
            self.mnemonic_id, self.version, self.iterations, self.encrypted_data = _dependency('seedsigner.helpers', 'kef').unwrap(data)
            version_name = _dependency('seedsigner.helpers', 'kef').VERSIONS[self.version]['name']
        except FeatureUnavailable:
            raise
        except:
            return None
        try:
            displayable_id = self.mnemonic_id.decode()
        except UnicodeDecodeError:
            displayable_id = repr(self.mnemonic_id)
        return '\n'.join(['Encrypted QR Code:', 'ID: ' + displayable_id, 'Version: ' + version_name, 'PBKDF2 iter.: ' + str(self.iterations)])

    def decrypt(self, key):
        _dependency('Cryptodome.Cipher', 'AES')
        'Decrypts encrypted mnemonic QR codes'
        decryptor = _dependency('seedsigner.helpers', 'kef').Cipher(key, self.mnemonic_id, self.iterations)
        decrypted_data = decryptor.decrypt(self.encrypted_data, self.version)
        return decrypted_data
