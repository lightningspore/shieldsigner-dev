# SPDX-License-Identifier: MIT
# Copyright2021 SeedSigner; upstream notice: ../LICENSE.SeedSigner.
# Generated from all original Seed classes; unported features fail explicitly.
import unicodedata
import hashlib
import hmac
from seedsigner_port.settings_schema import SettingsConstants
from seedsigner_port.decode_platform import dependency as _dependency, FeatureUnavailable
from seedsigner_port.secure_delete import wipe_bytes, wipe_string, wipe_list
from seedsigner_port.passphrase import normalize_passphrase as _normalize_passphrase


class InvalidSeedException(Exception):
    pass


class SeedWordsUnavailableException(Exception):
    pass


class Seed:
    def __init__(
        self,
        mnemonic=None,
        passphrase='',
        wordlist_language_code=SettingsConstants.WORDLIST_LANGUAGE__ENGLISH,
    ):
        self._wordlist_language_code = wordlist_language_code
        if not mnemonic:
            raise Exception('Must initialize a Seed with a mnemonic List[str]')
        self._mnemonic = unicodedata.normalize('NFKD', ' '.join(mnemonic).strip()).lower().split()
        self._passphrase = ''
        self.set_passphrase(passphrase, regenerate_seed=False)
        self.seed_bytes = None
        self.master_secret = None
        self._generate_seed()

    @staticmethod
    def get_wordlist(wordlist_language_code=SettingsConstants.WORDLIST_LANGUAGE__ENGLISH):
        if wordlist_language_code == SettingsConstants.WORDLIST_LANGUAGE__ENGLISH:
            return _dependency('embit', 'bip39').WORDLIST
        else:
            raise Exception(f'Unrecognized wordlist_language_code {wordlist_language_code}')

    def _generate_seed(self):
        try:
            self.seed_bytes = _dependency('embit', 'bip39').mnemonic_to_seed(
                self.mnemonic_str, password=self._passphrase, wordlist=self.wordlist
            )
        except FeatureUnavailable:
            raise
        except Exception as e:
            pass
            raise InvalidSeedException(type(e).__name__)

    @property
    def mnemonic_str(self):
        return ' '.join(self._mnemonic)

    @property
    def mnemonic_list(self):
        return self._mnemonic

    @property
    def wordlist_language_code(self):
        return self._wordlist_language_code

    @property
    def mnemonic_display_str(self):
        return unicodedata.normalize('NFC', ' '.join(self._mnemonic))

    @property
    def mnemonic_display_list(self):
        return unicodedata.normalize('NFC', ' '.join(self._mnemonic)).split()

    @property
    def has_passphrase(self):
        return self._passphrase != ''

    @property
    def passphrase(self):
        return self._passphrase

    @property
    def passphrase_display(self):
        return unicodedata.normalize('NFC', self._passphrase)

    def set_passphrase(self, passphrase, regenerate_seed=True):
        self._passphrase = _normalize_passphrase(passphrase)
        if regenerate_seed:
            self._generate_seed()

    @property
    def wordlist(self):
        return Seed.get_wordlist(self.wordlist_language_code)

    def set_wordlist_language_code(self, language_code):
        raise Exception('Not yet implemented!')

    @property
    def script_override(self):
        return None

    def get_root(self, network=SettingsConstants.MAINNET):
        return _dependency('embit', 'bip32').HDKey.from_seed(
            self.seed_bytes,
            version=_dependency('embit.networks', 'NETWORKS')[
                SettingsConstants.map_network_to_embit(network)
            ]['xprv'],
        )

    def derivation_override(self, sig_type=SettingsConstants.SINGLE_SIG):
        return None

    def detect_version(
        self,
        derivation_path,
        network=SettingsConstants.MAINNET,
        sig_type=SettingsConstants.SINGLE_SIG,
    ):
        embit_network = _dependency('embit.networks', 'NETWORKS')[
            SettingsConstants.map_network_to_embit(network)
        ]
        return _dependency('embit', 'bip32').detect_version(
            derivation_path, default='xpub', network=embit_network
        )

    @property
    def passphrase_label(self):
        return SettingsConstants.LABEL__BIP39_PASSPHRASE

    @property
    def seedqr_supported(self):
        return True

    @property
    def bip85_supported(self):
        return True

    def get_fingerprint(self, network=SettingsConstants.MAINNET):
        root = self.get_root(network)
        return _dependency('binascii', 'hexlify')(root.child(0).fingerprint).decode('utf-8')

    def get_xpub(self, wallet_path='/', network=SettingsConstants.MAINNET):
        root = self.get_root(network)
        return root.derive(wallet_path).to_public()

    def get_bip85_child_mnemonic(
        self, bip85_index, bip85_num_words, network=SettingsConstants.MAINNET
    ):
        """Derives the seed's nth BIP-85 child mnemonic"""
        root = self.get_root(network)
        return _dependency('embit', 'bip85').derive_mnemonic(root, bip85_num_words, bip85_index)

    def ensure_seed_words_available(self):
        """Raise if this seed type does not expose mnemonic words."""
        return

    def wipe(self):
        """Best-effort secure clearing of all sensitive fields."""
        wipe_bytes(self.seed_bytes)
        self.seed_bytes = None
        wipe_bytes(self.master_secret)
        self.master_secret = None
        wipe_list(self._mnemonic)
        self._mnemonic = []
        wipe_string(self._passphrase)
        self._passphrase = ''

    def __eq__(self, other):
        if isinstance(other, Seed):
            return self.seed_bytes == other.seed_bytes
        return False


class AezeedSeed(Seed):
    def _generate_seed(self):
        words = self._mnemonic
        word_to_index = {word: idx for idx, word in enumerate(self.wordlist)}
        try:
            deciphered = _dependency('seedsigner.models', 'aezeed').decode_mnemonic(
                words, self._passphrase, word_to_index
            )
        except FeatureUnavailable:
            raise
        except _dependency('seedsigner.models', 'aezeed').InvalidPassphraseError as e:
            pass
            if self._passphrase == '':
                self.seed_bytes = None
                return
            raise InvalidSeedException(type(e).__name__)
        except Exception as e:
            pass
            raise InvalidSeedException(type(e).__name__)
        self.seed_bytes = deciphered.entropy

    @property
    def passphrase_label(self):
        return SettingsConstants.LABEL__AEZEED_PASSPHRASE

    @property
    def script_override(self):
        return SettingsConstants.NATIVE_SEGWIT

    def derivation_override(self, sig_type=SettingsConstants.SINGLE_SIG):
        return 'm/84h/0h/0h' if sig_type == SettingsConstants.SINGLE_SIG else None

    @property
    def seedqr_supported(self):
        return False


class ElectrumSeed(Seed):
    def _generate_seed(self):
        if len(self._mnemonic) != 12:
            raise InvalidSeedException(f'Unsupported Electrum seed length: {len(self._mnemonic)}')
        s = hmac.digest(b'Seed version', self.mnemonic_str.encode('utf8'), hashlib.sha512).hex()
        prefix = s[0:3]
        if SettingsConstants.ELECTRUM_SEED_SEGWIT == prefix:
            self.seed_bytes = hashlib.pbkdf2_hmac(
                'sha512',
                self.mnemonic_str.encode('utf-8'),
                b'electrum' + self._passphrase.encode('utf-8'),
                iterations=SettingsConstants.ELECTRUM_PBKDF2_ROUNDS,
            )
        else:
            raise InvalidSeedException(f'Unsupported Electrum seed format: {prefix}')

    def set_passphrase(self, passphrase, regenerate_seed=True):
        self._passphrase = ElectrumSeed.normalize_electrum_passphrase(
            _normalize_passphrase(passphrase)
        )
        if regenerate_seed:
            self._generate_seed()

    @staticmethod
    def normalize_electrum_passphrase(passphrase):
        passphrase = unicodedata.normalize('NFKD', passphrase)
        passphrase = passphrase.lower()
        passphrase = ' '.join(passphrase.split())
        return passphrase

    @property
    def script_override(self):
        return SettingsConstants.NATIVE_SEGWIT

    def derivation_override(self, sig_type=SettingsConstants.SINGLE_SIG):
        return 'm/0h' if sig_type == SettingsConstants.SINGLE_SIG else 'm/1h'

    def detect_version(
        self,
        derivation_path,
        network=SettingsConstants.MAINNET,
        sig_type=SettingsConstants.SINGLE_SIG,
    ):
        embit_network = _dependency('embit.networks', 'NETWORKS')[
            SettingsConstants.map_network_to_embit(network)
        ]
        return (
            embit_network['zpub']
            if sig_type == SettingsConstants.SINGLE_SIG
            else embit_network['Zpub']
        )

    @property
    def passphrase_label(self):
        return SettingsConstants.LABEL__CUSTOM_EXTENSION

    @property
    def seedqr_supported(self):
        return False

    @property
    def bip85_supported(self):
        return True


class Slip39Seed(Seed):
    """Seed derived from SLIP-39 mnemonic shares."""

    def __init__(self, mnemonics, slip39_passphrase=''):
        self._wordlist_language_code = SettingsConstants.WORDLIST_LANGUAGE__ENGLISH
        if not mnemonics:
            raise Exception('Must provide at least one SLIP-39 share')
        self._shares = [unicodedata.normalize('NFKD', m.strip()) for m in mnemonics]
        first_share = _dependency('shamir_mnemonic', None).Share.from_mnemonic(self._shares[0])
        self.extendable = first_share.extendable
        self._member_threshold = first_share.member_threshold
        self._group_threshold = first_share.group_threshold
        self._slip39_passphrase = (
            unicodedata.normalize('NFKD', slip39_passphrase) if slip39_passphrase else ''
        )
        self.seed_bytes = None
        self.master_secret = None
        self._initial_master_secret = None
        self._creation_passphrase = self._slip39_passphrase
        self._generate_seed()

    def _generate_seed(self):
        """This takes 4-5 seconds on a Pi0, so need to show a loading screen rather than hang the UI"""
        LoadingScreenThread = _dependency('seedsigner.gui.screens.screen', 'LoadingScreenThread')
        self.loading_screen = LoadingScreenThread(text='Generating Seed\n\n\n\n\n\n')
        self.loading_screen.start()
        try:
            try:
                secret = _dependency('shamir_mnemonic', None).combine_mnemonics(
                    self._shares, self._slip39_passphrase.encode('utf-8')
                )
            except FeatureUnavailable:
                raise
            except Exception as e:
                if 'Wrong number of mnemonics' not in str(e):
                    raise
                groups = {}
                for share in self._shares:
                    s = _dependency('shamir_mnemonic', None).Share.from_mnemonic(share)
                    grp = groups.setdefault(s.group_index, [])
                    if len(grp) < self._member_threshold:
                        grp.append(share)
                    if len(groups) >= self._group_threshold and all(
                        (len(v) >= self._member_threshold for v in groups.values())
                    ):
                        break
                combine_list = []
                for grp_index in sorted(groups.keys())[: self._group_threshold]:
                    combine_list.extend(groups[grp_index][: self._member_threshold])
                secret = _dependency('shamir_mnemonic', None).combine_mnemonics(
                    combine_list, self._slip39_passphrase.encode('utf-8')
                )
            self.master_secret = secret
            if self._initial_master_secret is None:
                self._initial_master_secret = secret
            self.seed_bytes = secret
        except FeatureUnavailable:
            raise
        except Exception as e:
            pass
            raise InvalidSeedException(type(e).__name__)
        finally:
            self.loading_screen.stop()

    @property
    def mnemonic_list(self):
        return list(self._shares)

    @property
    def mnemonic_str(self):
        return '\n'.join(self._shares)

    def set_slip39_passphrase(self, passphrase, regenerate_seed=True):
        """Set or update the passphrase used to decrypt the SLIP-39 shares."""
        normalized_passphrase = unicodedata.normalize('NFKD', passphrase) if passphrase else ''
        if normalized_passphrase == self._slip39_passphrase:
            return
        self._slip39_passphrase = normalized_passphrase
        if regenerate_seed:
            self._generate_seed()

    @property
    def has_passphrase(self):
        return self._slip39_passphrase != ''

    @property
    def passphrase(self):
        return self._slip39_passphrase

    @property
    def passphrase_display(self):
        return unicodedata.normalize('NFC', self._slip39_passphrase)

    @property
    def passphrase_label(self):
        return 'SLIP-39 Passphrase'

    @property
    def seedqr_supported(self):
        return False

    @property
    def bip85_supported(self):
        return True

    def wipe(self):
        """Securely clear SLIP-39-specific fields, then delegate to parent."""
        wipe_list(self._shares)
        self._shares = []
        wipe_string(self._slip39_passphrase)
        self._slip39_passphrase = ''
        wipe_bytes(self._initial_master_secret)
        self._initial_master_secret = None
        wipe_string(self._creation_passphrase)
        self._creation_passphrase = ''
        super().wipe()

    def regenerate_shares(self, threshold, num_shares):
        """Generate new SLIP-39 shares from the original master secret."""
        if not self.extendable:
            raise InvalidSeedException('This SLIP-39 seed is not extendable')
        if threshold > num_shares:
            raise InvalidSeedException(
                'The requested threshold must not exceed the number of shares.'
            )
        if threshold == 1 and num_shares > 1:
            raise InvalidSeedException(
                'Multi-Share with threshold of 1 is not allowed, create 1-1 instead.'
            )
        first_share = _dependency('shamir_mnemonic', None).Share.from_mnemonic(self._shares[0])
        new_groups = _dependency('shamir_mnemonic', None).generate_mnemonics(
            self._group_threshold,
            [(threshold, num_shares)],
            self._initial_master_secret,
            passphrase=self._creation_passphrase.encode('utf-8'),
            extendable=True,
            iteration_exponent=first_share.iteration_exponent,
        )
        shares = new_groups[0]
        self._shares = shares
        self._member_threshold = threshold
        return shares


class XprvSeed(Seed):
    def __init__(self, xprv):
        normalized = unicodedata.normalize('NFKD', xprv.strip())
        try:
            root = _dependency('embit', 'bip32').HDKey.from_string(normalized)
        except FeatureUnavailable:
            raise
        except Exception as e:
            raise InvalidSeedException(repr(e))
        if not root.is_private:
            raise InvalidSeedException('Provided key is not a private extended key')
        self._xprv = normalized
        self._root = root
        self._wordlist_language_code = SettingsConstants.WORDLIST_LANGUAGE__ENGLISH
        self._passphrase = ''
        self.seed_bytes = None
        self.master_secret = None

    def get_root(self, network=SettingsConstants.MAINNET):
        return self._root

    @property
    def mnemonic_list(self):
        return []

    @property
    def mnemonic_str(self):
        return ''

    @property
    def mnemonic_display_str(self):
        self.ensure_seed_words_available()

    @property
    def mnemonic_display_list(self):
        self.ensure_seed_words_available()

    def ensure_seed_words_available(self):
        raise SeedWordsUnavailableException('This seed type does not have seed words.')

    @property
    def has_passphrase(self):
        return False

    @property
    def seedqr_supported(self):
        return False

    @property
    def bip85_supported(self):
        return True

    def get_bip85_child_mnemonic(
        self, bip85_index, bip85_num_words, network=SettingsConstants.MAINNET
    ):
        return _dependency('embit', 'bip85').derive_mnemonic(
            self.get_root(network), bip85_num_words, bip85_index
        )

    def wipe(self):
        """Securely clear xprv-specific fields, then delegate to parent."""
        wipe_string(self._xprv)
        self._xprv = ''
        self._root = None
        super().wipe()

    def __eq__(self, other):
        if isinstance(other, XprvSeed):
            return self._xprv == other._xprv
        return False
