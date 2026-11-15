# Original SeedSigner/Krux source; see LICENSE.SeedSigner and LICENSE.Krux-QR
# Generated format providers; unavailable crypto remains explicit.
from seedsigner_port.decode_platform import dependency as _dependency,FeatureUnavailable
try:
    UnicodeDecodeError
except NameError:
    UnicodeDecodeError=UnicodeError
MODE_ECB = 1
MODE_CBC = 2
MODE_CTR = 6
MODE_GCM = 11
VERSIONS = {0: {'name': 'AES-ECB v1', 'mode': MODE_ECB, 'auth': -16}, 1: {'name': 'AES-CBC v1', 'mode': MODE_CBC, 'auth': -16}, 5: {'name': 'AES-ECB', 'mode': MODE_ECB, 'auth': 3}, 6: {'name': 'AES-ECB +p', 'mode': MODE_ECB, 'pkcs_pad': True, 'auth': -4}, 7: {'name': 'AES-ECB +c', 'mode': MODE_ECB, 'pkcs_pad': True, 'auth': -4, 'compress': True}, 10: {'name': 'AES-CBC', 'mode': MODE_CBC, 'auth': 4}, 11: {'name': 'AES-CBC +p', 'mode': MODE_CBC, 'pkcs_pad': True, 'auth': -4}, 12: {'name': 'AES-CBC +c', 'mode': MODE_CBC, 'pkcs_pad': True, 'auth': -4, 'compress': True}, 15: {'name': 'AES-CTR', 'mode': MODE_CTR, 'pkcs_pad': None, 'auth': -4}, 16: {'name': 'AES-CTR +c', 'mode': MODE_CTR, 'pkcs_pad': None, 'auth': -4, 'compress': True}, 20: {'name': 'AES-GCM', 'mode': MODE_GCM, 'pkcs_pad': None, 'auth': 4}, 21: {'name': 'AES-GCM +c', 'mode': MODE_GCM, 'pkcs_pad': None, 'auth': 4, 'compress': True}}
MODE_NUMBERS = {'AES-ECB': MODE_ECB, 'AES-CBC': MODE_CBC, 'AES-CTR': MODE_CTR, 'AES-GCM': MODE_GCM, 'AES-ECB v1': MODE_ECB, 'AES-CBC v1': MODE_CBC}
MODE_IVS = {MODE_CBC: 16, MODE_CTR: 12, MODE_GCM: 12}
AES_BLOCK_SIZE = 16

class Cipher:
    """More than just a helper for AES encrypt/decrypt. Enforces KEF VERSIONS rules"""

    def __init__(self, key, salt, iterations):
        key = key if isinstance(key, bytes) else _dependency('unicodedata', None).normalize('NFKD', key).encode()
        salt = salt if isinstance(salt, bytes) else _dependency('unicodedata', None).normalize('NFKD', salt).encode()
        self._key = _dependency('hashlib', None).pbkdf2_hmac('sha256', key, salt, iterations)

    def encrypt(self, plain, version, iv=b'', fail_unsafe=True):
        _dependency('Cryptodome.Cipher', 'AES')
        'AES encrypt according to KEF rules defined by version, returns payload bytes'
        mode = VERSIONS[version]['mode']
        v_iv = MODE_IVS.get(mode, 0)
        v_pkcs_pad = VERSIONS[version].get('pkcs_pad', False)
        v_auth = VERSIONS[version].get('auth', 0)
        v_compress = VERSIONS[version].get('compress', False)
        auth = b''
        if iv is None:
            iv = b''
        if not isinstance(plain, bytes):
            raise TypeError('Plaintext is not bytes')
        if v_compress:
            plain = _deflate(plain)
        if fail_unsafe and v_pkcs_pad is False and (v_auth > 0) and (plain[-1] == 0):
            raise ValueError('Cannot validate decryption for this plaintext')
        if v_auth != 0 and mode in (MODE_ECB, MODE_CBC, MODE_CTR):
            if v_auth > 0:
                auth = _dependency('hashlib', None).sha256(bytes([version]) + iv + plain + self._key).digest()[:v_auth]
            elif v_auth < 0:
                auth = _dependency('hashlib', None).sha256(plain).digest()[:-v_auth]
                if fail_unsafe and v_pkcs_pad is False and (auth[-1] == 0):
                    raise ValueError('Cannot validate decryption for this plaintext')
                plain += auth
                auth = b''
        if v_pkcs_pad is True or v_pkcs_pad is False:
            plain = _pad(plain, pkcs_pad=v_pkcs_pad)
        if fail_unsafe and mode == MODE_ECB:
            unique_blocks = len(set((plain[x:x + 16] for x in range(0, len(plain), 16))))
            if unique_blocks != len(plain) // 16:
                raise ValueError('Duplicate blocks in ECB mode')
        if v_iv > 0:
            if not (isinstance(iv, bytes) and len(iv) == v_iv):
                raise ValueError('Wrong IV length')
        elif iv:
            raise ValueError('IV is not required')
        if iv:
            if mode == MODE_CTR:
                encryptor = _dependency('Cryptodome.Cipher', 'AES').new(self._key, mode, nonce=iv)
            elif mode == MODE_GCM:
                encryptor = _dependency('Cryptodome.Cipher', 'AES').new(self._key, mode, iv, mac_len=v_auth)
            else:
                encryptor = _dependency('Cryptodome.Cipher', 'AES').new(self._key, mode, iv)
        else:
            encryptor = _dependency('Cryptodome.Cipher', 'AES').new(self._key, mode)
        encrypted = encryptor.encrypt(plain)
        if mode == MODE_GCM:
            auth = encryptor.digest()[:v_auth]
        return iv + encrypted + auth

    def decrypt(self, payload, version):
        _dependency('Cryptodome.Cipher', 'AES')
        'AES Decrypt according to KEF rules defined by version, returns plaintext bytes'
        mode = VERSIONS[version]['mode']
        v_iv = MODE_IVS.get(mode, 0)
        v_pkcs_pad = VERSIONS[version].get('pkcs_pad', False)
        v_auth = VERSIONS[version].get('auth', 0)
        v_compress = VERSIONS[version].get('compress', False)
        min_payload = 1 if mode in (MODE_CTR, MODE_GCM) else AES_BLOCK_SIZE
        min_payload += min(0, v_auth) + v_iv
        if len(payload) <= min_payload:
            raise ValueError('Invalid Payload')
        if not v_iv:
            iv = b''
            decryptor = _dependency('Cryptodome.Cipher', 'AES').new(self._key, mode)
        else:
            iv = payload[:v_iv]
            if mode == MODE_CTR:
                decryptor = _dependency('Cryptodome.Cipher', 'AES').new(self._key, mode, nonce=iv)
            elif mode == MODE_GCM:
                decryptor = _dependency('Cryptodome.Cipher', 'AES').new(self._key, mode, iv, mac_len=v_auth)
            else:
                decryptor = _dependency('Cryptodome.Cipher', 'AES').new(self._key, mode, iv)
            payload = payload[v_iv:]
        auth = None
        if v_auth > 0:
            auth = payload[-v_auth:]
            payload = payload[:-v_auth]
        decrypted = decryptor.decrypt(payload)
        if v_auth != 0:
            try:
                decrypted = self._authenticate(version, iv, decrypted, decryptor, auth, mode, v_auth, v_pkcs_pad)
            except FeatureUnavailable:
                raise
            except:
                decrypted = None
        if decrypted and v_compress:
            decrypted = _reinflate(decrypted)
        return decrypted

    def _authenticate(self, version, iv, decrypted, aes_object, auth, mode, v_auth, v_pkcs_pad):
        if not (isinstance(version, int) and 0 <= version <= 255 and isinstance(iv, bytes) and isinstance(decrypted, bytes) and (mode != MODE_GCM or (hasattr(aes_object, 'verify') and callable(aes_object.verify))) and (isinstance(auth, bytes) or auth is None) and (mode in MODE_NUMBERS.values()) and (isinstance(v_auth, int) and -32 <= v_auth <= 32) and (v_pkcs_pad is True or v_pkcs_pad is False or v_pkcs_pad is None)):
            raise ValueError('Invalid call to ._authenticate()')
        len_pre_unpad = len(decrypted)
        if v_pkcs_pad in (False, True):
            decrypted = _unpad(decrypted, pkcs_pad=v_pkcs_pad)
        if v_auth < 0:
            auth = decrypted[v_auth:]
            decrypted = decrypted[:v_auth]
        if mode == MODE_GCM:
            try:
                aes_object.verify(auth)
                return decrypted
            except FeatureUnavailable:
                raise
            except:
                return None
        max_attempts = 1
        if v_pkcs_pad is False:
            max_attempts = min(len_pre_unpad - len(decrypted), abs(v_auth) + 1) + 1
        for _ in range(max_attempts):
            if v_auth > 0:
                cksum = _dependency('hashlib', None).sha256(bytes([version]) + iv + decrypted + self._key).digest()[:v_auth]
            else:
                cksum = _dependency('hashlib', None).sha256(decrypted).digest()[:-v_auth]
            if cksum == auth:
                return decrypted
            if v_auth < 0:
                decrypted += auth[:1]
                auth = auth[1:] + b'\x00'
            elif v_auth > 0:
                decrypted += b'\x00'
        return None

def suggest_versions(plaintext, mode_name):
    """Suggests a krux encryption version based on plaintext and preferred mode"""
    small_thresh = 32
    big_thresh = 120
    if not isinstance(plaintext, (bytes, str)):
        raise TypeError('Plaintext is not bytes or str')
    p_length = len(plaintext)
    unique_blocks = len(set((plaintext[x:x + 16] for x in range(0, p_length, 16))))
    p_duplicates = bool(unique_blocks < p_length / 16)
    if isinstance(plaintext, bytes):
        p_nul_suffix = bool(plaintext[-1] == 0)
    else:
        p_nul_suffix = bool(plaintext.encode()[-1] == 0)
    candidates = []
    for version, values in VERSIONS.items():
        if values is None or values['mode'] is None:
            continue
        if values['mode'] != MODE_NUMBERS[mode_name]:
            continue
        v_compress = values.get('compress', False)
        v_auth = values.get('auth', 0)
        v_pkcs_pad = values.get('pkcs_pad', False)
        if p_duplicates and mode_name == 'AES-ECB' and (not v_compress):
            continue
        if mode_name in ('AES-ECB', 'AES-CBC') and v_auth == -16:
            continue
        if p_length <= small_thresh:
            if mode_name == 'AES-ECB' and p_duplicates:
                pass
            else:
                if v_pkcs_pad is True and (not p_nul_suffix):
                    continue
                if v_compress:
                    continue
        else:
            if v_pkcs_pad is False:
                continue
            if mode_name == 'AES-ECB' and p_duplicates:
                pass
            elif p_length < big_thresh:
                if v_compress:
                    continue
            elif not v_compress:
                continue
        if p_nul_suffix and v_pkcs_pad is False:
            continue
        candidates.append(version)
    return candidates

def wrap(id_, version, iterations, payload):
    """
    Wraps inputs into KEF Encryption Format envelope, returns bytes
    """
    try:
        id_ = id_ if isinstance(id_, bytes) else id_.encode()
        if not 0 <= len(id_) <= 252:
            raise ValueError
        len_id = len(id_).to_bytes(1, 'big')
    except FeatureUnavailable:
        raise
    except:
        raise ValueError('Invalid ID')
    try:
        if not (0 <= version <= 255 and VERSIONS[version] is not None and (VERSIONS[version]['mode'] is not None)):
            raise ValueError
    except FeatureUnavailable:
        raise
    except:
        raise ValueError('Invalid version')
    try:
        if not isinstance(iterations, int):
            raise ValueError
        if iterations % 10000 == 0:
            iterations = iterations // 10000
            if not 1 <= iterations <= 10000:
                raise ValueError
        elif not 10000 < iterations < 2 ** 24:
            raise ValueError
        iterations = iterations.to_bytes(3, 'big')
    except FeatureUnavailable:
        raise
    except:
        raise ValueError('Invalid iterations')
    extra = MODE_IVS.get(VERSIONS[version]['mode'], 0)
    if VERSIONS[version].get('auth', 0) > 0:
        extra += VERSIONS[version]['auth']
    if not isinstance(payload, bytes):
        raise ValueError('Payload is not bytes')
    if VERSIONS[version].get('pkcs_pad', False) in (True, False):
        if (len(payload) - extra) % 16 != 0:
            raise ValueError('Ciphertext is not aligned')
        if (len(payload) - extra) // 16 < 1:
            raise ValueError('Ciphertext is too short')
    version = version.to_bytes(1, 'big')
    return b''.join([len_id, id_, version, iterations, payload])

def unwrap(kef_bytes):
    """
    Unwraps KEF Encryption Format bytes, returns tuple of parsed values
    """
    len_id = kef_bytes[0]
    try:
        version = kef_bytes[1 + len_id]
        if VERSIONS[version] is None or VERSIONS[version]['mode'] is None:
            raise ValueError
    except FeatureUnavailable:
        raise
    except:
        raise ValueError('Invalid format')
    id_ = kef_bytes[1:1 + len_id]
    kef_iterations = int.from_bytes(kef_bytes[2 + len_id:5 + len_id], 'big')
    if kef_iterations <= 10000:
        iterations = kef_iterations * 10000
    else:
        iterations = kef_iterations
    payload = kef_bytes[len_id + 5:]
    extra = MODE_IVS.get(VERSIONS[version]['mode'], 0)
    if VERSIONS[version].get('auth', 0) > 0:
        extra += VERSIONS[version]['auth']
    if VERSIONS[version].get('pkcs_pad', False) in (True, False):
        if (len(payload) - extra) % 16 != 0:
            raise ValueError('Ciphertext is not aligned')
        if (len(payload) - extra) // 16 < 1:
            raise ValueError('Ciphertext is too short')
    return (id_, version, iterations, payload)

def _pad(some_bytes, pkcs_pad):
    """
    Pads some_bytes to AES block size of 16 bytes, returns bytes
    pkcs_pad: False=NUL-pad, True=PKCS#7-pad, None=no-pad
    """
    if pkcs_pad is None:
        return some_bytes
    len_padding = (AES_BLOCK_SIZE - len(some_bytes) % AES_BLOCK_SIZE) % AES_BLOCK_SIZE
    if pkcs_pad is True:
        if len_padding == 0:
            len_padding = AES_BLOCK_SIZE
        return some_bytes + len_padding.to_bytes(1, 'big') * len_padding
    if pkcs_pad is False:
        return some_bytes + b'\x00' * len_padding
    raise TypeError('pkcs_pad is not (None, True, False)')

def _unpad(some_bytes, pkcs_pad):
    """
    Strips padding from some_bytes, returns bytes
    pkcs_pad: False=NUL-pad, True=PKCS#7-pad, None=no-pad
    """
    if pkcs_pad is None:
        return some_bytes
    if pkcs_pad is True:
        len_padding = some_bytes[-1]
        return some_bytes[:-len_padding]
    if pkcs_pad is False:
        return some_bytes.rstrip(b'\x00')
    raise TypeError('pkcs_pad is not in (None, True, False)')

def _deflate(data):
    """Compresses the given data using deflate module"""
    try:
        stream = _dependency('io', None).BytesIO()
        compressor = _dependency('zlib', None).compressobj(wbits=-10)
        stream.write(compressor.compress(data) + compressor.flush())
        return stream.getvalue()
    except FeatureUnavailable:
        raise
    except:
        raise ValueError('Error compressing')

def _reinflate(data):
    """Decompresses the given data using deflate module"""
    try:
        decompressor = _dependency('zlib', None).decompressobj(wbits=-10)
        return decompressor.decompress(_dependency('io', None).BytesIO(data).read()) + decompressor.flush()
    except FeatureUnavailable:
        raise
    except:
        raise ValueError('Error decompressing')
