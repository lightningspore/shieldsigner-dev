# Copyright2021 SeedSigner; MIT, see ../LICENSE.SeedSigner
from seedsigner_port.decode_platform import dependency as _dependency, FeatureUnavailable
class SeedStorage:

    def __init__(self):
        self.seeds = []
        self.pending_seed = None
        self._pending_mnemonic = []
        self._pending_is_electrum = False
        self._pending_is_aezeed = False
        self._pending_is_slip39 = False
        self._pending_slip39_share = []
        self._pending_slip39_shares = []
        self._slip39_share_length = None
        self._slip39_first_share = None

    def set_pending_seed(self, seed):
        self.pending_seed = seed

    def get_pending_seed(self):
        return self.pending_seed

    def finalize_pending_seed(self):
        seed = self.pending_seed
        if seed not in self.seeds:
            self.seeds.append(seed)
        self.pending_seed = None
        return seed

    def clear_pending_seed(self):
        if self.pending_seed is not None:
            self.pending_seed.wipe()
        self.pending_seed = None

    def validate_mnemonic(self, mnemonic):
        try:
            _dependency('seedsigner.models.seed', 'Seed')(mnemonic=mnemonic)
        except _dependency('seedsigner.models.seed', 'InvalidSeedException') as e:
            return False
        return True

    def num_seeds(self):
        return len(self.seeds)

    @property
    def pending_mnemonic(self):
        return list(self._pending_mnemonic)

    @property
    def pending_mnemonic_length(self):
        return len(self._pending_mnemonic)

    def init_pending_mnemonic(self, num_words=12, is_electrum=False, is_aezeed=False):
        self._pending_mnemonic = [None] * num_words
        self._pending_is_electrum = is_electrum
        self._pending_is_aezeed = is_aezeed

    def update_pending_mnemonic(self, word, index):
        """
        Replaces the nth word in the pending mnemonic.

        * may specify a negative `index` (e.g. -1 is the last word).
        """
        if index >= len(self._pending_mnemonic):
            raise Exception(f'index {index} is too high')
        self._pending_mnemonic[index] = ''.join(word) if word is not None else None

    def get_pending_mnemonic_word(self, index):
        if index < len(self._pending_mnemonic):
            return self._pending_mnemonic[index]
        return None

    def get_pending_mnemonic_fingerprint(self, network=_dependency('seedsigner.models.settings_definition', 'SettingsConstants').MAINNET, wordlist_language_code=_dependency('seedsigner.models.settings_definition', 'SettingsConstants').WORDLIST_LANGUAGE__ENGLISH):
        try:
            if self._pending_is_electrum:
                seed = _dependency('seedsigner.models.seed', 'ElectrumSeed')(self._pending_mnemonic)
            elif self._pending_is_aezeed:
                seed = _dependency('seedsigner.models.seed', 'AezeedSeed')(self._pending_mnemonic)
                if seed.seed_bytes is None:
                    return None
            else:
                seed = _dependency('seedsigner.models.seed', 'Seed')(self._pending_mnemonic, wordlist_language_code=wordlist_language_code)
            return seed.get_fingerprint(network)
        except _dependency('seedsigner.models.seed', 'InvalidSeedException'):
            return None

    def convert_pending_mnemonic_to_pending_seed(self, wordlist_language_code=_dependency('seedsigner.models.settings_definition', 'SettingsConstants').WORDLIST_LANGUAGE__ENGLISH):
        if self._pending_is_electrum:
            self.pending_seed = _dependency('seedsigner.models.seed', 'ElectrumSeed')(self._pending_mnemonic)
        elif self._pending_is_aezeed:
            self.pending_seed = _dependency('seedsigner.models.seed', 'AezeedSeed')(self._pending_mnemonic)
        else:
            self.pending_seed = _dependency('seedsigner.models.seed', 'Seed')(self._pending_mnemonic, wordlist_language_code=wordlist_language_code)
        self.discard_pending_mnemonic()

    @property
    def pending_is_aezeed(self):
        return self._pending_is_aezeed

    def discard_pending_mnemonic(self):
        _dependency('seedsigner.helpers.secure_delete', 'wipe_list')(self._pending_mnemonic)
        self._pending_mnemonic = []
        self._pending_is_electrum = False
        self._pending_is_aezeed = False
    'Slip39 share handling'

    def init_pending_slip39_share(self, num_words=None):
        if num_words is None:
            num_words = self._slip39_share_length or 33
        self._pending_slip39_share = [None] * num_words
        self._slip39_share_length = num_words
        self._pending_is_slip39 = True

    def update_pending_slip39_share(self, word, index):
        if index >= len(self._pending_slip39_share):
            raise Exception(f'index {index} is too high')
        self._pending_slip39_share[index] = ''.join(word)

    def get_pending_slip39_word(self, index):
        if index < len(self._pending_slip39_share):
            return self._pending_slip39_share[index]
        return None

    @property
    def pending_slip39_share_length(self):
        return len(self._pending_slip39_share)

    def finalize_current_slip39_share(self):
        mnemonic = ' '.join(self._pending_slip39_share)
        Slip39Share = _dependency('shamir_mnemonic', 'Share')
        try:
            share_obj = Slip39Share.from_mnemonic(mnemonic)
        except FeatureUnavailable:
            raise
        except Exception:
            self._pending_slip39_share = []
            raise _dependency('seedsigner.models.seed', 'InvalidSeedException')('Invalid SLIP-39 share')
        if self._slip39_first_share is None:
            self._slip39_first_share = share_obj
        self._pending_slip39_shares.append(list(self._pending_slip39_share))
        self._pending_slip39_share = []

    def add_slip39_share_mnemonic(self, mnemonic):
        """Add a share mnemonic directly."""
        Slip39Share = _dependency('shamir_mnemonic', 'Share')
        try:
            share_obj = Slip39Share.from_mnemonic(mnemonic)
        except FeatureUnavailable:
            raise
        except Exception:
            raise _dependency('seedsigner.models.seed', 'InvalidSeedException')('Invalid SLIP-39 share')
        if self._slip39_first_share is None:
            self._slip39_first_share = share_obj
        self._pending_slip39_shares.append([''.join(w) for w in mnemonic.split()])
        self._slip39_share_length = len(self._pending_slip39_shares[-1])
        self._pending_is_slip39 = True

    def convert_pending_slip39_shares_to_pending_seed(self, passphrase=''):
        mnemonics = [' '.join(share) for share in self._pending_slip39_shares]
        self.pending_seed = _dependency('seedsigner.models.seed', 'Slip39Seed')(mnemonics=mnemonics, slip39_passphrase=passphrase)
        self.discard_pending_slip39_shares()

    def discard_pending_slip39_shares(self):
        _dependency('seedsigner.helpers.secure_delete', 'wipe_list')(self._pending_slip39_share)
        for share in self._pending_slip39_shares:
            _dependency('seedsigner.helpers.secure_delete', 'wipe_list')(share)
        self._pending_slip39_share = []
        self._pending_slip39_shares = []
        self._pending_is_slip39 = False
        self._slip39_share_length = None
        self._slip39_first_share = None

    @property
    def slip39_shares_entered(self):
        return len(self._pending_slip39_shares)

    @property
    def slip39_total_needed(self):
        if self._slip39_first_share is None:
            return None
        g = self._slip39_first_share.group_threshold
        m = self._slip39_first_share.member_threshold
        return m * g if g > 1 else m
