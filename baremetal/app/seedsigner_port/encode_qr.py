# Copyright2021 SeedSigner; MIT, see ../LICENSE.SeedSigner
# Generated original encoders; optional providers fail on use.
from seedsigner_port.decode_platform import dependency as _dependency,FeatureUnavailable
def _make_BaseQrEncoder():

    class BaseQrEncoder:

        def __post_init__(self):
            self.qr = _dependency('seedsigner.helpers.qr', 'QR')()

        @property
        def is_complete(self):
            raise Exception('Not implemented in child class')

        @property
        def qr_max_fragment_size(self):
            raise Exception('Not implemented in child class')

        def seq_len(self):
            raise Exception('Not implemented in child class')

        def next_part(self):
            raise Exception('Not implemented in child class')

        def cur_part(self):
            raise Exception('Not implemented in child class')

        def restart(self):
            pass

        def _create_parts(self):
            raise Exception('Not implemented in child class')

        def part_to_image(self, part, width, height, border=3, background_color='ffffff'):
            return self.qr.qrimage_io(part, width, height, border, background_color=background_color)

        def next_part_image(self, width=240, height=240, border=3, background_color='bdbdbd'):
            part = self.next_part()
            return self.part_to_image(part, width, height, border, background_color=background_color)

        def __init__(self, qr_density=_dependency('seedsigner.models.settings', 'SettingsConstants').DENSITY__MEDIUM):
            self.qr_density = qr_density
            self.__post_init__()
    return BaseQrEncoder

def _make_BaseStaticQrEncoder():

    class BaseStaticQrEncoder(_resolve('BaseQrEncoder')):

        def seq_len(self):
            return 1

        def cur_part(self):
            """ static QRs only have a single part, which `next_part` always returns """
            return self.next_part()

        @property
        def is_complete(self):
            return True

        def __init__(self, qr_density=_dependency('seedsigner.models.settings', 'SettingsConstants').DENSITY__MEDIUM):
            self.qr_density = qr_density
            self.__post_init__()
    return BaseStaticQrEncoder

def _make_SeedQrEncoder():

    class SeedQrEncoder(_resolve('BaseStaticQrEncoder')):

        def __post_init__(self):
            self.wordlist = _dependency('seedsigner.models.seed', 'Seed').get_wordlist(self.wordlist_language_code)
            super().__post_init__()
            self.data = ''
            for word in self.mnemonic:
                index = self.wordlist.index(word)
                self.data += str('%04d' % index)

        def next_part(self):
            return self.data

        def __init__(self, qr_density=_dependency('seedsigner.models.settings', 'SettingsConstants').DENSITY__MEDIUM, mnemonic=None, wordlist_language_code=_dependency('seedsigner.models.settings', 'SettingsConstants').WORDLIST_LANGUAGE__ENGLISH):
            self.qr_density = qr_density
            self.mnemonic = mnemonic
            self.wordlist_language_code = wordlist_language_code
            self.__post_init__()
    return SeedQrEncoder

def _make_CompactSeedQrEncoder():

    class CompactSeedQrEncoder(_resolve('SeedQrEncoder')):

        def next_part(self):
            binary_str = ''
            for word in self.mnemonic:
                index = self.wordlist.index(word)
                binary_str += _dependency('seedsigner_port.qr_strings', None).zfill(bin(index).split('b')[1], 11)
            checksum_bits = len(self.mnemonic) // 3
            binary_str = binary_str[:-checksum_bits]
            as_bytes = bytearray()
            for i in range(0, _dependency('math', None).ceil(len(binary_str) / 8)):
                as_bytes.append(int('0b' + binary_str[i * 8:(i + 1) * 8], 2))
            return bytes(as_bytes)

        def __init__(self, qr_density=_dependency('seedsigner.models.settings', 'SettingsConstants').DENSITY__MEDIUM, mnemonic=None, wordlist_language_code=_dependency('seedsigner.models.settings', 'SettingsConstants').WORDLIST_LANGUAGE__ENGLISH):
            self.qr_density = qr_density
            self.mnemonic = mnemonic
            self.wordlist_language_code = wordlist_language_code
            self.__post_init__()
    return CompactSeedQrEncoder

def _make_GenericStaticQrEncoder():

    class GenericStaticQrEncoder(_resolve('BaseStaticQrEncoder')):

        def next_part(self):
            return self.data

        def __init__(self, qr_density=_dependency('seedsigner.models.settings', 'SettingsConstants').DENSITY__MEDIUM, data=None):
            self.qr_density = qr_density
            self.data = data
            self.__post_init__()
    return GenericStaticQrEncoder

def _make_BaseXpubQrEncoder():

    class BaseXpubQrEncoder(_resolve('BaseQrEncoder')):
        """
    Base Xpub QrEncoder for static and animated formats
    """

        def prep_xpub(self):
            version = self.seed.detect_version(self.derivation, self.network, self.sig_type)
            self.root = self.seed.get_root(self.network)
            self.fingerprint = self.root.child(0).fingerprint
            self.xprv = self.root.derive(self.derivation)
            self.xpub = self.xprv.to_public()
            self.xpub_base58 = self.xpub.to_string(version=version)
            self.xpubstring = '[{}{}]{}'.format(_dependency('binascii', 'hexlify')(self.fingerprint).decode('utf-8'), self.derivation[1:], self.xpub_base58)

        def __init__(self, qr_density=_dependency('seedsigner.models.settings', 'SettingsConstants').DENSITY__MEDIUM, seed=None, derivation=None, network=_dependency('seedsigner.models.settings', 'SettingsConstants').MAINNET, sig_type=None):
            self.qr_density = qr_density
            self.seed = seed
            self.derivation = derivation
            self.network = network
            self.sig_type = sig_type
            self.__post_init__()
    return BaseXpubQrEncoder

def _make_StaticXpubQrEncoder():

    class StaticXpubQrEncoder(_resolve('BaseXpubQrEncoder'), _resolve('BaseStaticQrEncoder')):

        def __post_init__(self):
            super().__post_init__()
            self.prep_xpub()

        def next_part(self):
            self.prep_xpub()
            return self.xpubstring
    return StaticXpubQrEncoder

def _make_BaseSimpleAnimatedQREncoder():

    class BaseSimpleAnimatedQREncoder(_resolve('BaseQrEncoder')):

        def __post_init__(self):
            super().__post_init__()
            self.parts = []
            self.part_num_sent = 0
            self.sent_complete = False
            self._create_parts()

        @property
        def is_complete(self):
            return self.sent_complete

        def seq_len(self):
            return len(self.parts)

        def next_part(self):
            if self.part_num_sent > len(self.parts) - 1:
                self.part_num_sent = 0
            part = self.parts[self.part_num_sent]
            if self.part_num_sent == len(self.parts) - 1:
                self.sent_complete = True
            self.part_num_sent += 1
            return part

        def cur_part(self):
            if self.part_num_sent == 0:
                self.part_num_sent = len(self.parts) - 1
            else:
                self.part_num_sent -= 1
            return self.next_part()

        def restart(self):
            self.part_num_sent = 0

        def __init__(self, qr_density=_dependency('seedsigner.models.settings', 'SettingsConstants').DENSITY__MEDIUM):
            self.qr_density = qr_density
            self.__post_init__()
    return BaseSimpleAnimatedQREncoder

def _make_SpecterLegacyXPubQrEncoder():

    class SpecterLegacyXPubQrEncoder(_resolve('BaseSimpleAnimatedQREncoder'), _resolve('BaseXpubQrEncoder')):
        """
    Legacy "pXofY" format. Included here for compatibility with much older versions of
    Specter Desktop. Can probably eventually be removed.
    """

        @property
        def qr_max_fragment_size(self):
            density_mapping = {_dependency('seedsigner.models.settings', 'SettingsConstants').DENSITY__LOW: 40, _dependency('seedsigner.models.settings', 'SettingsConstants').DENSITY__MEDIUM: 65, _dependency('seedsigner.models.settings', 'SettingsConstants').DENSITY__HIGH: 90}
            return density_mapping.get(self.qr_density, 65)

        def _create_parts(self):
            self.prep_xpub()
            start = 0
            stop = self.qr_max_fragment_size
            qr_cnt = (len(self.xpubstring) - 1) // self.qr_max_fragment_size + 1
            if qr_cnt == 1:
                self.parts.append(self.xpubstring[start:stop])
            cnt = 0
            while cnt < qr_cnt and qr_cnt != 1:
                part = 'p' + str(cnt + 1) + 'of' + str(qr_cnt) + ' ' + self.xpubstring[start:stop]
                self.parts.append(part)
                start = start + self.qr_max_fragment_size
                stop = stop + self.qr_max_fragment_size
                if stop > len(self.xpubstring):
                    stop = len(self.xpubstring)
                cnt += 1

        def __init__(self, qr_density=_dependency('seedsigner.models.settings', 'SettingsConstants').DENSITY__MEDIUM, seed=None, derivation=None, network=_dependency('seedsigner.models.settings', 'SettingsConstants').MAINNET, sig_type=None):
            self.qr_density = qr_density
            self.seed = seed
            self.derivation = derivation
            self.network = network
            self.sig_type = sig_type
            self.__post_init__()
    return SpecterLegacyXPubQrEncoder

def _make_BaseFountainQrEncoder():

    class BaseFountainQrEncoder(_resolve('BaseQrEncoder')):

        def __post_init__(self):
            super().__post_init__()
            self.ur2_encode = None

        @property
        def is_complete(self):
            return self.ur2_encode.is_complete()

        @property
        def qr_max_fragment_size(self):
            density_mapping = {_dependency('seedsigner.models.settings', 'SettingsConstants').DENSITY__LOW: 10, _dependency('seedsigner.models.settings', 'SettingsConstants').DENSITY__MEDIUM: 30, _dependency('seedsigner.models.settings', 'SettingsConstants').DENSITY__HIGH: 120}
            return density_mapping.get(self.qr_density, 30)

        def _create_parts(self):
            """ parts are dynamically generated by the fountain encoder """
            pass

        def seq_len(self):
            return self.ur2_encode.fountain_encoder.seq_len()

        def next_part(self):
            return self.ur2_encode.next_part().upper()

        def cur_part(self):
            return self.ur2_encode.current_part().upper()

        def restart(self):
            self.ur2_encode.fountain_encoder.restart()

        def __init__(self, qr_density=_dependency('seedsigner.models.settings', 'SettingsConstants').DENSITY__MEDIUM):
            self.qr_density = qr_density
            self.__post_init__()
    return BaseFountainQrEncoder

def _make_UrXpubQrEncoder():

    class UrXpubQrEncoder(_resolve('BaseFountainQrEncoder'), _resolve('BaseXpubQrEncoder')):

        def __post_init__(self):
            super().__post_init__()
            self.prep_xpub()

            def derivation_to_keypath(path):
                arr = path.split('/')
                if arr[0] == 'm':
                    arr = arr[1:]
                if len(arr) == 0:
                    return _dependency('urtypes.crypto', 'Keypath')([], self.root.my_fingerprint, None)
                if arr[-1] == '':
                    arr = arr[:-1]
                for i, e in enumerate(arr):
                    if e[-1] == 'h' or e[-1] == "'":
                        arr[i] = _dependency('urtypes.crypto', 'PathComponent')(int(e[:-1]), True)
                    else:
                        arr[i] = _dependency('urtypes.crypto', 'PathComponent')(int(e), False)
                return _dependency('urtypes.crypto', 'Keypath')(arr, self.root.my_fingerprint, len(arr))
            origin = derivation_to_keypath(self.derivation)
            self.use_info = None if self.network == _dependency('seedsigner.models.settings', 'SettingsConstants').MAINNET else _dependency('urtypes.crypto', 'CoinInfo')(type=None, network=1)
            self.ur_hdkey = _dependency('urtypes.crypto', 'HDKey')({'key': self.xpub.key.serialize(), 'chain_code': self.xpub.chain_code, 'origin': origin, 'parent_fingerprint': self.xpub.fingerprint, 'use_info': self.use_info})
            ur_outputs = []
            if len(origin.components) > 0:
                if origin.components[0].index == 84:
                    ur_outputs.append(_dependency('urtypes.crypto', 'Output')([_dependency('urtypes.crypto', 'SCRIPT_EXPRESSION_TAG_MAP')[404]], self.ur_hdkey))
                elif origin.components[0].index == 49:
                    ur_outputs.append(_dependency('urtypes.crypto', 'Output')([_dependency('urtypes.crypto', 'SCRIPT_EXPRESSION_TAG_MAP')[400], _dependency('urtypes.crypto', 'SCRIPT_EXPRESSION_TAG_MAP')[404]], self.ur_hdkey))
                elif origin.components[0].index == 48:
                    if len(origin.components) >= 4:
                        if origin.components[3].index == 2:
                            ur_outputs.append(_dependency('urtypes.crypto', 'Output')([_dependency('urtypes.crypto', 'SCRIPT_EXPRESSION_TAG_MAP')[401]], self.ur_hdkey))
                        elif origin.components[3].index == 1:
                            ur_outputs.append(_dependency('urtypes.crypto', 'Output')([_dependency('urtypes.crypto', 'SCRIPT_EXPRESSION_TAG_MAP')[400], _dependency('urtypes.crypto', 'SCRIPT_EXPRESSION_TAG_MAP')[401]], self.ur_hdkey))
                elif origin.components[0].index == 86:
                    ur_outputs.append(_dependency('urtypes.crypto', 'Output')([_dependency('urtypes.crypto', 'SCRIPT_EXPRESSION_TAG_MAP')[409]], self.ur_hdkey))
                elif origin.components[0].index == 44:
                    ur_outputs.append(_dependency('urtypes.crypto', 'Output')([_dependency('urtypes.crypto', 'SCRIPT_EXPRESSION_TAG_MAP')[403]], self.ur_hdkey))
                elif origin.components[0].index == 45:
                    ur_outputs.append(_dependency('urtypes.crypto', 'Output')([_dependency('urtypes.crypto', 'SCRIPT_EXPRESSION_TAG_MAP')[400]], self.ur_hdkey))
            if len(ur_outputs) == 0:
                ur_outputs.append(_dependency('urtypes.crypto', 'Output')([_dependency('urtypes.crypto', 'SCRIPT_EXPRESSION_TAG_MAP')[404]], self.ur_hdkey))
                ur_outputs.append(_dependency('urtypes.crypto', 'Output')([_dependency('urtypes.crypto', 'SCRIPT_EXPRESSION_TAG_MAP')[400], _dependency('urtypes.crypto', 'SCRIPT_EXPRESSION_TAG_MAP')[404]], self.ur_hdkey))
                ur_outputs.append(_dependency('urtypes.crypto', 'Output')([_dependency('urtypes.crypto', 'SCRIPT_EXPRESSION_TAG_MAP')[401]], self.ur_hdkey))
                ur_outputs.append(_dependency('urtypes.crypto', 'Output')([_dependency('urtypes.crypto', 'SCRIPT_EXPRESSION_TAG_MAP')[400], _dependency('urtypes.crypto', 'SCRIPT_EXPRESSION_TAG_MAP')[401]], self.ur_hdkey))
                ur_outputs.append(_dependency('urtypes.crypto', 'Output')([_dependency('urtypes.crypto', 'SCRIPT_EXPRESSION_TAG_MAP')[403]], self.ur_hdkey))
                ur_outputs.append(_dependency('urtypes.crypto', 'Output')([_dependency('urtypes.crypto', 'SCRIPT_EXPRESSION_TAG_MAP')[400]], self.ur_hdkey))
            ur_account = _dependency('urtypes.crypto', 'Account')(self.root.my_fingerprint, ur_outputs)
            qr_ur_bytes = _dependency('seedsigner.helpers.ur2.ur', 'UR')('crypto-account', ur_account.to_cbor())
            self.ur2_encode = _dependency('seedsigner.helpers.ur2.ur_encoder', 'UREncoder')(ur=qr_ur_bytes, max_fragment_len=self.qr_max_fragment_size)

        def __init__(self, qr_density=_dependency('seedsigner.models.settings', 'SettingsConstants').DENSITY__MEDIUM, seed=None, derivation=None, network=_dependency('seedsigner.models.settings', 'SettingsConstants').MAINNET, sig_type=None):
            self.qr_density = qr_density
            self.seed = seed
            self.derivation = derivation
            self.network = network
            self.sig_type = sig_type
            self.__post_init__()
    return UrXpubQrEncoder

def _make_UrPsbtQrEncoder():

    class UrPsbtQrEncoder(_resolve('BaseFountainQrEncoder')):

        def __post_init__(self):
            super().__post_init__()
            qr_ur_bytes = _dependency('seedsigner.helpers.ur2.ur', 'UR')('crypto-psbt', _dependency('urtypes.crypto', 'PSBT')(self.psbt.serialize()).to_cbor())
            self.ur2_encode = _dependency('seedsigner.helpers.ur2.ur_encoder', 'UREncoder')(ur=qr_ur_bytes, max_fragment_len=self.qr_max_fragment_size)

        def __init__(self, qr_density=_dependency('seedsigner.models.settings', 'SettingsConstants').DENSITY__MEDIUM, psbt=None):
            self.qr_density = qr_density
            self.psbt = psbt
            self.__post_init__()
    return UrPsbtQrEncoder

def _make_UrBytesQrEncoder():

    class UrBytesQrEncoder(_resolve('BaseFountainQrEncoder')):

        def __post_init__(self):
            super().__post_init__()
            qr_ur_bytes = _dependency('seedsigner.helpers.ur2.ur', 'UR')('bytes', _dependency('urtypes.bytes', 'Bytes')(self.data).to_cbor())
            self.ur2_encode = _dependency('seedsigner.helpers.ur2.ur_encoder', 'UREncoder')(ur=qr_ur_bytes, max_fragment_len=self.qr_max_fragment_size)

        def __init__(self, qr_density=_dependency('seedsigner.models.settings', 'SettingsConstants').DENSITY__MEDIUM, data=None):
            self.qr_density = qr_density
            self.data = data
            self.__post_init__()
    return UrBytesQrEncoder

def _make_UrTextQrEncoder():

    class UrTextQrEncoder(_resolve('BaseFountainQrEncoder')):

        def __post_init__(self):
            super().__post_init__()
            cbor_encoder = _dependency('seedsigner.helpers.ur2.cbor_lite', 'CBOREncoder')()
            cbor_encoder.encodeText(self.text)
            qr_ur_text = _dependency('seedsigner.helpers.ur2.ur', 'UR')('text', cbor_encoder.get_bytes())
            self.ur2_encode = _dependency('seedsigner.helpers.ur2.ur_encoder', 'UREncoder')(ur=qr_ur_text, max_fragment_len=self.qr_max_fragment_size)

        def __init__(self, qr_density=_dependency('seedsigner.models.settings', 'SettingsConstants').DENSITY__MEDIUM, text=None):
            self.qr_density = qr_density
            self.text = text
            self.__post_init__()
    return UrTextQrEncoder

def _make_GenericStringEncoder():

    class GenericStringEncoder(_resolve('BaseStaticQrEncoder')):

        def __init__(self, generic_string):
            super().__init__()
            self.generic_string = generic_string

        def next_part(self):
            return self.generic_string
    return GenericStringEncoder
_FACTORIES={'BaseQrEncoder':_make_BaseQrEncoder,'BaseStaticQrEncoder':_make_BaseStaticQrEncoder,'SeedQrEncoder':_make_SeedQrEncoder,'CompactSeedQrEncoder':_make_CompactSeedQrEncoder,'GenericStaticQrEncoder':_make_GenericStaticQrEncoder,'BaseXpubQrEncoder':_make_BaseXpubQrEncoder,'StaticXpubQrEncoder':_make_StaticXpubQrEncoder,'BaseSimpleAnimatedQREncoder':_make_BaseSimpleAnimatedQREncoder,'SpecterLegacyXPubQrEncoder':_make_SpecterLegacyXPubQrEncoder,'BaseFountainQrEncoder':_make_BaseFountainQrEncoder,'UrXpubQrEncoder':_make_UrXpubQrEncoder,'UrPsbtQrEncoder':_make_UrPsbtQrEncoder,'UrBytesQrEncoder':_make_UrBytesQrEncoder,'UrTextQrEncoder':_make_UrTextQrEncoder,'GenericStringEncoder':_make_GenericStringEncoder}
_CACHE={}
def _resolve(name):
    if name not in _CACHE:
        if name not in _FACTORIES:raise AttributeError(name)
        _CACHE[name]=_FACTORIES[name]()
    return _CACHE[name]
def __getattr__(name):return _resolve(name)
