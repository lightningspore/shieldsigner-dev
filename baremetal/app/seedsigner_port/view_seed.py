# Copyright2021 SeedSigner; MIT, see ../LICENSE.SeedSigner
# Generated from pinned original source; optional class bases resolve only on use.
from seedsigner_port.decode_platform import dependency as _dependency, FeatureUnavailable
from seedsigner_port.navigation import Destination
def _make_SeedsMenuView():

    class SeedsMenuView(_dependency('seedsigner.views.view', 'View')):
        LOAD = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Load a seed')

        def __init__(self):
            super().__init__()
            self.seeds = []
            for seed in self.controller.storage.seeds:
                self.seeds.append({'fingerprint': seed.get_fingerprint(self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__NETWORK)), 'seed_type': self.get_seed_type_label(seed)})

        @staticmethod
        def get_seed_type_label(seed):
            if isinstance(seed, _dependency('seedsigner.models.seed', 'Slip39Seed')):
                return 'SLIP39'
            if isinstance(seed, _dependency('seedsigner.models.seed', 'XprvSeed')):
                return 'XPRV'
            if isinstance(seed, _dependency('seedsigner.models.seed', 'ElectrumSeed')):
                return 'ELEC'
            if isinstance(seed, _dependency('seedsigner.models.seed', 'AezeedSeed')):
                return 'Aezeed'
            return 'BIP39'

        def run(self):
            if not self.seeds:
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('LoadSeedView'), clear_history=True)
            button_data = []
            for seed in self.seeds:
                button_data.append(_dependency('seedsigner.gui.screens.screen', 'ButtonOption')('{0} ({1})'.format(seed['fingerprint'], seed['seed_type']), _dependency('seedsigner.gui.components', 'SeedSignerIconConstants').FINGERPRINT))
            button_data.append(self.LOAD)
            selected_menu_num = self.run_screen(_dependency('seedsigner.gui.screens', 'ButtonListScreen'), title=_dependency('gettext', 'gettext')('In-Memory Seeds'), is_button_text_centered=False, button_data=button_data)
            if selected_menu_num == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            elif len(self.seeds) > 0 and selected_menu_num < len(self.seeds):
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedOptionsView'), view_args={'seed': self.controller.storage.seeds[selected_menu_num]})
            elif button_data[selected_menu_num] == self.LOAD:
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('LoadSeedView'))
    return SeedsMenuView

def _make_SeedSelectSeedView():

    class SeedSelectSeedView(_dependency('seedsigner.views.view', 'View')):
        """
    Reusable seed selection UI. Prompts the user to select amongst the already-loaded
    seeds OR to load a seed.

    * `flow`: indicates which user flow is in progress during seed selection (e.g.
                verify single sig addr or sign message).
    """
        SCAN_SEED = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Scan a seed', _dependency('seedsigner.gui.components', 'SeedSignerIconConstants').QRCODE)
        BITBOX_BACKUP = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('BitBox02 backup', _dependency('seedsigner.gui.components', 'SeedSignerIconConstants').MICROSD)
        PASSPORT_BACKUP = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Passport backup', _dependency('seedsigner.gui.components', 'SeedSignerIconConstants').MICROSD)
        TAPSIGNER_BACKUP = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('TAPSIGNER backup', _dependency('seedsigner.gui.components', 'SeedSignerIconConstants').MICROSD)
        SATOCHIP = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Use Satochip card', _dependency('seedsigner.gui.components', 'SeedSignerIconConstants').FINGERPRINT)
        TYPE_12WORD = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Enter 12-word seed', _dependency('seedsigner.gui.components', 'FontAwesomeIconConstants').KEYBOARD, return_data=12)
        TYPE_15WORD = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Enter 15-word seed', _dependency('seedsigner.gui.components', 'FontAwesomeIconConstants').KEYBOARD, return_data=15)
        TYPE_18WORD = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Enter 18-word seed', _dependency('seedsigner.gui.components', 'FontAwesomeIconConstants').KEYBOARD, return_data=18)
        TYPE_21WORD = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Enter 21-word seed', _dependency('seedsigner.gui.components', 'FontAwesomeIconConstants').KEYBOARD, return_data=21)
        TYPE_24WORD = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Enter 24-word seed', _dependency('seedsigner.gui.components', 'FontAwesomeIconConstants').KEYBOARD, return_data=24)
        TYPE_ELECTRUM = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Enter Electrum seed', _dependency('seedsigner.gui.components', 'FontAwesomeIconConstants').KEYBOARD)
        TYPE_AEZEED = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Enter Aezeed seed', _dependency('seedsigner.gui.components', 'FontAwesomeIconConstants').KEYBOARD)
        TYPE_SLIP39 = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('SLIP-39 Shares', _dependency('seedsigner.gui.components', 'FontAwesomeIconConstants').KEYBOARD)

        def __init__(self, flow):
            super().__init__()
            self.flow = flow

        def run(self):
            seeds = self.controller.storage.seeds
            if self.flow == _dependency('seedsigner.controller', 'Controller').FLOW__VERIFY_SINGLESIG_ADDR:
                title = _dependency('gettext', 'gettext')('Verify Address')
                if not seeds:
                    text = _dependency('gettext', 'gettext')('Load the seed to verify')
                else:
                    text = _dependency('gettext', 'gettext')('Select seed to verify')
            elif self.flow == _dependency('seedsigner.controller', 'Controller').FLOW__SIGN_MESSAGE:
                title = _dependency('gettext', 'gettext')('Sign Message')
                if not seeds:
                    text = _dependency('gettext', 'gettext')('Load the seed to sign with')
                else:
                    text = _dependency('gettext', 'gettext')('Select seed to sign with')
            else:
                raise Exception('Unsupported `flow` specified: {0}'.format(self.flow))
            button_data = []
            for seed in seeds:
                button_str = seed.get_fingerprint(self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__NETWORK))
                button_data.append(_dependency('seedsigner.gui.screens.screen', 'ButtonOption')(button_str, _dependency('seedsigner.gui.components', 'SeedSignerIconConstants').FINGERPRINT, icon_color='blue'))
            if self.flow in [_dependency('seedsigner.controller', 'Controller').FLOW__SIGN_MESSAGE, _dependency('seedsigner.controller', 'Controller').FLOW__VERIFY_SINGLESIG_ADDR] and self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__SATOCHIP_SUPPORT) == _dependency('seedsigner.models.settings', 'SettingsConstants').OPTION__ENABLED:
                button_data.append(self.SATOCHIP)
            button_data.append(self.SCAN_SEED)
            if self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__BITBOX_BACKUP) == _dependency('seedsigner.models.settings', 'SettingsConstants').OPTION__ENABLED:
                button_data.append(self.BITBOX_BACKUP)
            if self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__PASSPORT_BACKUP) == _dependency('seedsigner.models.settings', 'SettingsConstants').OPTION__ENABLED:
                button_data.append(self.PASSPORT_BACKUP)
            if self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__TAPSIGNER_BACKUP) == _dependency('seedsigner.models.settings', 'SettingsConstants').OPTION__ENABLED:
                button_data.append(self.TAPSIGNER_BACKUP)
            seed_lengths = self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__SEED_WORD_LENGTHS)
            options = {12: self.TYPE_12WORD, 15: self.TYPE_15WORD, 18: self.TYPE_18WORD, 21: self.TYPE_21WORD, 24: self.TYPE_24WORD}
            for l in seed_lengths:
                button_data.append(options[l])
            if self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__ELECTRUM_SEEDS) == _dependency('seedsigner.models.settings', 'SettingsConstants').OPTION__ENABLED:
                button_data.append(self.TYPE_ELECTRUM)
            if self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__AEZEED_SEEDS) == _dependency('seedsigner.models.settings', 'SettingsConstants').OPTION__ENABLED:
                button_data.append(self.TYPE_AEZEED)
            if self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__SLIP39_SEEDS) == _dependency('seedsigner.models.settings', 'SettingsConstants').OPTION__ENABLED:
                button_data.append(self.TYPE_SLIP39)
            selected_menu_num = self.run_screen(_dependency('seedsigner.gui.screens', 'seed_screens').SeedSelectSeedScreen, title=title, text=text, is_button_text_centered=False, button_data=button_data)
            if selected_menu_num == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            if len(seeds) > 0 and selected_menu_num < len(seeds):
                view_args = dict(seed=seeds[selected_menu_num])
                if self.flow == _dependency('seedsigner.controller', 'Controller').FLOW__VERIFY_SINGLESIG_ADDR:
                    return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedAddressVerificationView'), view_args=view_args)
                elif self.flow == _dependency('seedsigner.controller', 'Controller').FLOW__SIGN_MESSAGE:
                    self.controller.sign_message_data['seed'] = seeds[selected_menu_num]
                    return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedSignMessageConfirmMessageView'))
            self.controller.resume_main_flow = self.flow
            if self.flow == _dependency('seedsigner.controller', 'Controller').FLOW__VERIFY_SINGLESIG_ADDR and button_data[selected_menu_num] == self.SATOCHIP:
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.tools_views', 'SatochipLoadDescriptorScriptTypeView'))
            if self.flow == _dependency('seedsigner.controller', 'Controller').FLOW__SIGN_MESSAGE and button_data[selected_menu_num] == self.SATOCHIP:
                connector = _dependency('seedsigner.helpers', 'seedkeeper_utils').init_satochip(self, init_card_filter=['satochip'])
                if not connector:
                    return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
                if _dependency('seedsigner.helpers', 'seedkeeper_utils').satochip_2fa_blocks_signing(self, connector):
                    return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
                self.controller.sign_message_with_satochip = True
                self.controller.sign_message_data['seed'] = None
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedSignMessageConfirmMessageView'))
            if button_data[selected_menu_num] == self.SCAN_SEED:
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.scan_views', 'ScanView'))
            if button_data[selected_menu_num] == self.BITBOX_BACKUP:
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedBitbox02BackupSelectView'))
            if button_data[selected_menu_num] == self.PASSPORT_BACKUP:
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedPassportBackupSelectView'))
            if button_data[selected_menu_num] == self.TAPSIGNER_BACKUP:
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedTapsignerBackupSelectView'))
            elif button_data[selected_menu_num] in [self.TYPE_12WORD, self.TYPE_15WORD, self.TYPE_18WORD, self.TYPE_21WORD, self.TYPE_24WORD]:
                self.controller.storage.init_pending_mnemonic(num_words=button_data[selected_menu_num].return_data)
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.seed_views', 'SeedMnemonicEntryView'))
            elif button_data[selected_menu_num] == self.TYPE_ELECTRUM:
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedElectrumMnemonicStartView'))
            elif button_data[selected_menu_num] == self.TYPE_AEZEED:
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedAezeedMnemonicStartView'))
            elif button_data[selected_menu_num] == self.TYPE_SLIP39:
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedSlip39MnemonicStartView'))
    return SeedSelectSeedView

def _make_LoadSeedView():

    class LoadSeedView(_dependency('seedsigner.views.view', 'View')):
        SEED_QR = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(' Scan a SeedQR', _dependency('seedsigner.gui.components', 'SeedSignerIconConstants').QRCODE)
        TYPE_12WORD = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Enter 12-word seed', _dependency('seedsigner.gui.components', 'FontAwesomeIconConstants').KEYBOARD, return_data=12)
        TYPE_15WORD = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Enter 15-word seed', _dependency('seedsigner.gui.components', 'FontAwesomeIconConstants').KEYBOARD, return_data=15)
        TYPE_18WORD = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Enter 18-word seed', _dependency('seedsigner.gui.components', 'FontAwesomeIconConstants').KEYBOARD, return_data=18)
        TYPE_21WORD = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Enter 21-word seed', _dependency('seedsigner.gui.components', 'FontAwesomeIconConstants').KEYBOARD, return_data=21)
        TYPE_24WORD = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Enter 24-word seed', _dependency('seedsigner.gui.components', 'FontAwesomeIconConstants').KEYBOARD, return_data=24)
        TYPE_ELECTRUM = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Enter Electrum seed', _dependency('seedsigner.gui.components', 'FontAwesomeIconConstants').KEYBOARD)
        TYPE_AEZEED = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Enter Aezeed seed', _dependency('seedsigner.gui.components', 'FontAwesomeIconConstants').KEYBOARD)
        TYPE_SLIP39 = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('SLIP-39 Shares', _dependency('seedsigner.gui.components', 'FontAwesomeIconConstants').KEYBOARD)
        IMPORT_SEEDKEEPER = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('From SeedKeeper', _dependency('seedsigner.gui.components', 'FontAwesomeIconConstants').LOCK)
        IMPORT_SPECTER_DIY = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('From Specter-DIY', _dependency('seedsigner.gui.components', 'FontAwesomeIconConstants').LOCK)
        BITBOX_BACKUP = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('BitBox02 backup', _dependency('seedsigner.gui.components', 'SeedSignerIconConstants').MICROSD)
        PASSPORT_BACKUP = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Passport backup', _dependency('seedsigner.gui.components', 'SeedSignerIconConstants').MICROSD)
        TAPSIGNER_BACKUP = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('TAPSIGNER backup', _dependency('seedsigner.gui.components', 'SeedSignerIconConstants').MICROSD)
        CREATE = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(' Create a seed', _dependency('seedsigner.gui.components', 'SeedSignerIconConstants').PLUS)

        def run(self):
            seed_lengths = self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__SEED_WORD_LENGTHS)
            options = {12: self.TYPE_12WORD, 15: self.TYPE_15WORD, 18: self.TYPE_18WORD, 21: self.TYPE_21WORD, 24: self.TYPE_24WORD}
            button_data = [self.SEED_QR]
            button_data.extend([options[l] for l in seed_lengths])
            if self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__SMARTCARD_SUPPORT) == _dependency('seedsigner.models.settings', 'SettingsConstants').OPTION__ENABLED:
                button_data.append(self.IMPORT_SEEDKEEPER)
            if self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__SPECTER_DIY_SUPPORT) == _dependency('seedsigner.models.settings', 'SettingsConstants').OPTION__ENABLED:
                button_data.append(self.IMPORT_SPECTER_DIY)
            if self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__SLIP39_SEEDS) == _dependency('seedsigner.models.settings', 'SettingsConstants').OPTION__ENABLED:
                button_data.append(self.TYPE_SLIP39)
            if self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__AEZEED_SEEDS) == _dependency('seedsigner.models.settings', 'SettingsConstants').OPTION__ENABLED:
                button_data.append(self.TYPE_AEZEED)
            if self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__BITBOX_BACKUP) == _dependency('seedsigner.models.settings', 'SettingsConstants').OPTION__ENABLED:
                button_data.append(self.BITBOX_BACKUP)
            if self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__PASSPORT_BACKUP) == _dependency('seedsigner.models.settings', 'SettingsConstants').OPTION__ENABLED:
                button_data.append(self.PASSPORT_BACKUP)
            if self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__TAPSIGNER_BACKUP) == _dependency('seedsigner.models.settings', 'SettingsConstants').OPTION__ENABLED:
                button_data.append(self.TAPSIGNER_BACKUP)
            button_data.append(self.CREATE)
            if self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__ELECTRUM_SEEDS) == _dependency('seedsigner.models.settings', 'SettingsConstants').OPTION__ENABLED:
                button_data.append(self.TYPE_ELECTRUM)
            selected_menu_num = self.run_screen(_dependency('seedsigner.gui.screens', 'ButtonListScreen'), title=_dependency('gettext', 'gettext')('Load a Seed'), is_button_text_centered=False, button_data=button_data)
            if selected_menu_num == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            if button_data[selected_menu_num] == self.SEED_QR:
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.scan_views', 'ScanSeedQRView'))
            elif button_data[selected_menu_num] in [self.TYPE_12WORD, self.TYPE_15WORD, self.TYPE_18WORD, self.TYPE_21WORD, self.TYPE_24WORD]:
                self.controller.storage.init_pending_mnemonic(num_words=button_data[selected_menu_num].return_data)
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedMnemonicEntryView'))
            elif button_data[selected_menu_num] == self.IMPORT_SEEDKEEPER:
                self.controller.smartcard_backend_preference = 'pysatochip'
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedKeeperSelectView'))
            elif button_data[selected_menu_num] == self.IMPORT_SPECTER_DIY:
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.tools_views', 'ToolsJavacardLoadMnemonicView'))
            elif button_data[selected_menu_num] == self.TYPE_ELECTRUM:
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedElectrumMnemonicStartView'))
            elif button_data[selected_menu_num] == self.TYPE_AEZEED:
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedAezeedMnemonicStartView'))
            elif button_data[selected_menu_num] == self.TYPE_SLIP39:
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedSlip39MnemonicStartView'))
            elif button_data[selected_menu_num] == self.BITBOX_BACKUP:
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedBitbox02BackupSelectView'))
            elif button_data[selected_menu_num] == self.PASSPORT_BACKUP:
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedPassportBackupSelectView'))
            elif button_data[selected_menu_num] == self.TAPSIGNER_BACKUP:
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedTapsignerBackupSelectView'))
            elif button_data[selected_menu_num] == self.CREATE:
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.tools_views', 'ToolsMenuView'), view_args={'include_password_generator': False})
    return LoadSeedView

def _make_SeedKeeperSelectView():

    class SeedKeeperSelectView(_dependency('seedsigner.views.view', 'View')):

        def entropy_to_mnemonic(self, entropy_bytes, wordlist):
            if wordlist not in (None, 'english'):
                raise ValueError('Unsupported BIP-39 wordlist: {0}. Only English is supported.'.format(wordlist))
            return _dependency('embit', 'bip39').mnemonic_from_bytes(bytes(entropy_bytes))

        @staticmethod
        def _decode_seedkeeper_text(secret_hex):
            """Decode a Seedkeeper UTF-8 payload with optional 1/2-byte length prefix."""
            raw = bytes.fromhex(secret_hex)
            if len(raw) >= 2 and int.from_bytes(raw[:2], 'big') == len(raw[2:]):
                return raw[2:].decode('utf-8')
            if len(raw) >= 1 and raw[0] == len(raw[1:]):
                return raw[1:].decode('utf-8')
            return raw.decode('utf-8')

        @staticmethod
        def _extract_xprv_from_masterseed_secret(secret_hex):
            """Load legacy xprv payloads stored in a Masterseed subtype 0 secret."""
            secret_raw_bytes = bytes.fromhex(secret_hex)
            candidates = []
            if secret_raw_bytes:
                size = secret_raw_bytes[0]
                if len(secret_raw_bytes) >= 1 + size:
                    try:
                        candidates.append(secret_raw_bytes[1:1 + size].decode('utf-8'))
                    except UnicodeDecodeError:
                        pass
            for decode_attempt in (lambda: _resolve('SeedKeeperSelectView')._decode_seedkeeper_text(secret_hex), lambda: secret_raw_bytes.decode('utf-8')):
                try:
                    candidates.append(decode_attempt())
                except UnicodeDecodeError:
                    continue
            for candidate in candidates:
                if candidate.startswith(('xprv', 'tprv')):
                    return candidate
            raise ValueError('Unsupported Masterseed subtype 0 payload')

        def run(self):
            try:
                Satochip_Connector = _dependency('seedsigner.helpers', 'seedkeeper_utils').init_satochip(self, init_card_filter=['seedkeeper'])
                if not Satochip_Connector:
                    return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
                self.loading_screen = _dependency('seedsigner.gui.screens.screen', 'LoadingScreenThread')(text='Listing Seeds\n\n\n\n\n\n')
                self.loading_screen.start()
                headers = Satochip_Connector.seedkeeper_list_secret_headers()
                self.loading_screen.stop()
                headers_parsed = []
                button_data = []
                for header in headers:
                    sid = header['id']
                    label = header['label']
                    stype = _dependency('pysatochip.JCconstants', 'SEEDKEEPER_DIC_TYPE').get(header['type'], hex(header['type']))
                    subtype = header['subtype']
                    export_rights = _dependency('pysatochip.JCconstants', 'SEEDKEEPER_DIC_EXPORT_RIGHTS').get(header['export_rights'], hex(header['export_rights']))
                    if stype == 'BIP39 mnemonic' and export_rights == 'Plaintext export allowed' or (stype == 'Masterseed' and subtype == 1) or (stype == 'Masterseed' and subtype == 0) or (stype == 'Data' and label.startswith('XPRV:') and (export_rights == 'Plaintext export allowed')) or (stype == 'Electrum mnemonic' and export_rights == 'Plaintext export allowed') or (stype == 'Password' and label.startswith('aezeed:') and (export_rights == 'Plaintext export allowed')):
                        if not label:
                            label = 'Unnamed Secret'
                        headers_parsed.append({'sid': sid, 'label': label, 'stype': stype, 'subtype': subtype})
                        button_data.append(_dependency('seedsigner.gui.screens.screen', 'ButtonOption')(label))
                if len(headers_parsed) < 1:
                    self.run_screen(_dependency('seedsigner.gui.screens', 'WarningScreen'), title='No Secrets to Load', status_headline=None, text='No BIP39 Secrets to Load from Seedkeeper', show_back_button=False)
                    if isinstance(getattr(self, 'seed', None), _dependency('seedsigner.models.seed', 'AezeedSeed')):
                        return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedAezeedPassphraseModeView'))
                    return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
                selected_menu_num = self.run_screen(_dependency('seedsigner.gui.screens', 'ButtonListScreen'), title='Select Secret', is_button_text_centered=False, button_data=button_data, show_back_button=True)
                if selected_menu_num == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                    if isinstance(getattr(self, 'seed', None), _dependency('seedsigner.models.seed', 'AezeedSeed')):
                        return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedAezeedPassphraseModeView'))
                    return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
                selected_header = headers_parsed[selected_menu_num]
                sid = selected_header['sid']
                stype = selected_header['stype']
                subtype = selected_header['subtype']
                label = selected_header['label']
                self.loading_screen = _dependency('seedsigner.gui.screens.screen', 'LoadingScreenThread')(text='Loading Seed\n\n\n\n\n\n')
                self.loading_screen.start()
                secret_dict = Satochip_Connector.seedkeeper_export_secret(sid, None)
                self.loading_screen.stop()
                assert stype == _dependency('pysatochip.JCconstants', 'SEEDKEEPER_DIC_TYPE').get(secret_dict['type'], hex(secret_dict['type']))
                if stype == 'BIP39 mnemonic' or stype == 'Electrum mnemonic':
                    secret_dict['secret'] = _dependency('binascii', 'unhexlify')(secret_dict['secret'])[1:].decode().rstrip('\x00')
                    bip39_secret = secret_dict['secret']
                    secret_size = secret_dict['secret_list'][0]
                    secret_mnemonic = bip39_secret[:secret_size]
                    secret_passphrase = bip39_secret[secret_size + 1:]
                elif stype == 'Password' and label.startswith('aezeed:'):
                    aezeed_secret = self._decode_seedkeeper_text(secret_dict['secret']).strip()
                    secret_mnemonic = aezeed_secret
                    secret_passphrase = ''
                    if '\n' in aezeed_secret:
                        lines = [line.strip() for line in aezeed_secret.splitlines() if line.strip()]
                        if len(lines) > 0:
                            secret_mnemonic = lines[0]
                        for line in lines[1:]:
                            if line.startswith('passphrase:'):
                                secret_passphrase = line[len('passphrase:'):]
                                break
                elif stype == 'Masterseed' and subtype == 1:
                    secret_raw_bytes = bytes.fromhex(secret_dict['secret'])
                    offset = 0
                    masterseed_size = secret_raw_bytes[offset]
                    offset += 1
                    masterseed_bytes = secret_raw_bytes[offset:offset + masterseed_size]
                    offset += masterseed_size
                    wordlist_byte = secret_raw_bytes[offset]
                    offset += 1
                    wordlist = _dependency('pysatochip.JCconstants', 'BIP39_WORDLIST_DIC').get(wordlist_byte)
                    entropy_size = secret_raw_bytes[offset]
                    offset += 1
                    entropy_bytes = secret_raw_bytes[offset:offset + entropy_size]
                    offset += entropy_size
                    bip39_mnemonic = self.entropy_to_mnemonic(entropy_bytes, wordlist)
                    passphrase_size = secret_raw_bytes[offset]
                    offset += 1
                    passphrase_bytes = secret_raw_bytes[offset:offset + passphrase_size]
                    offset += passphrase_size
                    passphrase = passphrase_bytes.decode('utf-8')
                    secret_mnemonic = bip39_mnemonic
                    secret_passphrase = passphrase
                elif stype == 'Masterseed' and subtype == 0:
                    xprv = self._extract_xprv_from_masterseed_secret(secret_dict['secret'])
                    self.controller.storage.set_pending_seed(_dependency('seedsigner.models.seed', 'XprvSeed')(xprv))
                    return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedFinalizeView'))
                elif stype == 'Data':
                    xprv = self._decode_seedkeeper_text(secret_dict['secret']).strip()
                    if not xprv.startswith(('xprv', 'tprv')):
                        raise ValueError('Selected Seedkeeper data entry is not an xprv')
                    self.controller.storage.set_pending_seed(_dependency('seedsigner.models.seed', 'XprvSeed')(xprv))
                    return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedFinalizeView'))
                else:
                    raise ValueError('Unsupported secret type: {0}, subtype: {1}'.format(stype, subtype))
            except FeatureUnavailable:
                raise
            except Exception as e:
                print('General Exception Loading Seed:', str(e))
                if hasattr(self, 'loading_screen'):
                    self.loading_screen.stop()
                _dependency('seedsigner_port.clock', None).sleep(0.1)
                self.run_screen(_dependency('seedsigner.gui.screens', 'WarningScreen'), title='Error', status_headline=None, text=str(e), show_back_button=True)
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            is_aezeed = False
            if secret_mnemonic.startswith('aezeed:'):
                is_aezeed = True
                secret_mnemonic = secret_mnemonic[len('aezeed:'):]
            mnemonic = secret_mnemonic.split(' ')
            self.controller.storage.init_pending_mnemonic(num_words=len(mnemonic), is_electrum=stype == 'Electrum mnemonic' and (not is_aezeed), is_aezeed=is_aezeed)
            for i, word in enumerate(mnemonic):
                self.controller.storage.update_pending_mnemonic(word, i)
            try:
                self.controller.storage.convert_pending_mnemonic_to_pending_seed(wordlist_language_code=self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__WORDLIST_LANGUAGE))
            except _dependency('seedsigner.models.seed', 'InvalidSeedException'):
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedMnemonicInvalidView'))
            self.seed = self.controller.storage.get_pending_seed()
            if isinstance(self.seed, _dependency('seedsigner.models.seed', 'AezeedSeed')):
                if len(secret_passphrase) > 0:
                    try:
                        self.seed.set_passphrase(secret_passphrase)
                    except _dependency('seedsigner.models.seed', 'InvalidSeedException') as e:
                        if str(e) == 'InvalidPassphraseError':
                            self.seed.set_passphrase('')
                            return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedAezeedPassphraseModeView'))
                        raise
                if self.seed.seed_bytes is None:
                    return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedAezeedPassphraseModeView'))
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedFinalizeView'))
            if len(secret_passphrase) > 0:
                self.seed.set_passphrase(secret_passphrase)
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedReviewPassphraseView'))
            return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedFinalizeView'))
    return SeedKeeperSelectView

def _make_SeedBitbox02BackupSelectView():

    class SeedBitbox02BackupSelectView(_dependency('seedsigner.views.view', 'View')):

        def __init__(self):
            super().__init__()
            self.microsd_dir = _dependency('seedsigner.hardware.microsd', 'MicroSD').get_microsd_dir()
            self.extensions = {'.bin', '.dat', '.bb02', '.backup'}

        def _get_backup_files(self):
            backup_files = []
            if not self.microsd_dir.exists():
                raise _dependency('seedsigner.helpers.bitbox02_backup', 'Bitbox02BackupError')(_dependency('gettext', 'gettext')('microSD card not detected.'))
            for path in self.microsd_dir.rglob('*'):
                if not path.is_file():
                    continue
                try:
                    rel_parts = path.relative_to(self.microsd_dir).parts
                except ValueError:
                    continue
                if any((part.startswith('.') for part in rel_parts)):
                    continue
                if path.suffix.lower() in self.extensions:
                    backup_files.append(path)
            backup_files.sort(key=lambda p: p.relative_to(self.microsd_dir).as_posix().lower())
            return backup_files

        def run(self):
            if len(self.controller.storage.seeds) > 0:
                ret = self.run_screen(_dependency('seedsigner.gui.screens', 'WarningScreen'), title='WARNING', status_headline=None, text='These tools load data from the microSD card and may expose loaded secrets.', show_back_button=True, button_data=[_dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Continue')])
                if ret == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                    return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            try:
                backup_files = self._get_backup_files()
            except FeatureUnavailable:
                raise
            except Exception as e:
                pass
                self.run_screen(_dependency('seedsigner.gui.screens', 'WarningScreen'), title='Error', status_headline=None, text=str(e), show_back_button=False, button_data=[_dependency('seedsigner.gui.screens.screen', 'ButtonOption')('OK')])
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            if not backup_files:
                self.run_screen(_dependency('seedsigner.gui.screens', 'WarningScreen'), title=_dependency('gettext', 'gettext')('No Backups Found'), status_headline=None, text=_dependency('gettext', 'gettext')('No BitBox02 backups (.bin, .bb02, .dat, .backup) were found on the microSD card.'), show_back_button=False, button_data=[_dependency('seedsigner.gui.screens.screen', 'ButtonOption')('OK')])
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            button_data = [_dependency('seedsigner.gui.screens.screen', 'ButtonOption')(path.relative_to(self.microsd_dir).as_posix(), _dependency('seedsigner.gui.components', 'SeedSignerIconConstants').MICROSD) for path in backup_files]
            selected_menu_num = self.run_screen(_dependency('seedsigner.gui.screens', 'ButtonListScreen'), title=_dependency('gettext', 'gettext')('Select BitBox02 backup'), is_button_text_centered=False, button_data=button_data)
            if selected_menu_num == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            selected_path = backup_files[selected_menu_num]
            try:
                details = _dependency('seedsigner.helpers.bitbox02_backup', 'decode_bitbox02_backup')(selected_path.read_bytes())
            except (OSError, _dependency('seedsigner.helpers.bitbox02_backup', 'Bitbox02BackupError'), ValueError) as e:
                pass
                self.run_screen(_dependency('seedsigner.gui.screens', 'WarningScreen'), title='Error', status_headline=None, text=str(e), show_back_button=False, button_data=[_dependency('seedsigner.gui.screens.screen', 'ButtonOption')('OK')])
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedBitbox02BackupSelectView'))
            try:
                seed = _dependency('seedsigner.models.seed', 'Seed')(details.mnemonic)
            except _dependency('seedsigner.models.seed', 'InvalidSeedException'):
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedMnemonicInvalidView'))
            self.controller.storage.set_pending_seed(seed)
            return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedBitbox02BackupSummaryView'), view_args={'details': details})
    return SeedBitbox02BackupSelectView

def _make_SeedBitbox02BackupSummaryView():

    class SeedBitbox02BackupSummaryView(_dependency('seedsigner.views.view', 'View')):
        CONTINUE = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(_dependency('gettext', 'gettext')('Continue'))

        def __init__(self, details):
            super().__init__()
            self.details = details

        def run(self):
            text_lines = []
            if self.details.name:
                text_lines.append(_dependency('gettext', 'gettext')('Backup name: {}').format(self.details.name))
            if self.details.timestamp:
                text_lines.append(_dependency('gettext', 'gettext')('Created: {}').format(_dependency('seedsigner.helpers.bitbox02_backup', 'format_timestamp')(self.details.timestamp)))
            if self.details.generator:
                text_lines.append(_dependency('gettext', 'gettext')('Firmware: {}').format(self.details.generator))
            if self.details.birthdate:
                text_lines.append(_dependency('gettext', 'gettext')('Birthdate: {}').format(_dependency('seedsigner.helpers.bitbox02_backup', 'format_timestamp')(self.details.birthdate)))
            text_lines.append(_dependency('gettext', 'gettext')('Seed length: {} words').format(len(self.details.mnemonic)))
            self.run_screen(_dependency('seedsigner.gui.screens', 'LargeIconStatusScreen'), title=_dependency('gettext', 'gettext')('BitBox02 backup'), status_headline=_dependency('gettext', 'gettext')('Seed loaded'), text='\n'.join(text_lines), show_back_button=False, button_data=[self.CONTINUE])
            return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedFinalizeView'))
    return SeedBitbox02BackupSummaryView

def _make_SeedPassportBackupSelectView():

    class SeedPassportBackupSelectView(_dependency('seedsigner.views.view', 'View')):

        def __init__(self):
            super().__init__()
            self.microsd_dir = _dependency('seedsigner.hardware.microsd', 'MicroSD').get_microsd_dir()
            self.extensions = {'.7z'}

        def _get_backup_files(self):
            backup_files = []
            if not self.microsd_dir.exists():
                raise _dependency('seedsigner.helpers.passport_backup', 'PassportBackupError')(_dependency('gettext', 'gettext')('microSD card not detected.'))
            for path in self.microsd_dir.rglob('*'):
                if not path.is_file():
                    continue
                try:
                    rel_parts = path.relative_to(self.microsd_dir).parts
                except ValueError:
                    continue
                if any((part.startswith('.') for part in rel_parts)):
                    continue
                if path.suffix.lower() in self.extensions:
                    backup_files.append(path)
            backup_files.sort(key=lambda p: p.relative_to(self.microsd_dir).as_posix().lower())
            return backup_files

        def run(self):
            if len(self.controller.storage.seeds) > 0:
                ret = self.run_screen(_dependency('seedsigner.gui.screens', 'WarningScreen'), title='WARNING', status_headline=None, text='These tools load data from the microSD card and may expose loaded secrets.', show_back_button=True, button_data=[_dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Continue')])
                if ret == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                    return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            try:
                backup_files = self._get_backup_files()
            except FeatureUnavailable:
                raise
            except Exception as e:
                pass
                self.run_screen(_dependency('seedsigner.gui.screens', 'WarningScreen'), title='Error', status_headline=None, text=str(e), show_back_button=False, button_data=[_dependency('seedsigner.gui.screens.screen', 'ButtonOption')('OK')])
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            if not backup_files:
                self.run_screen(_dependency('seedsigner.gui.screens', 'WarningScreen'), title=_dependency('gettext', 'gettext')('No Backups Found'), status_headline=None, text=_dependency('gettext', 'gettext')('No Passport backups (.7z) were found on the microSD card.'), show_back_button=False, button_data=[_dependency('seedsigner.gui.screens.screen', 'ButtonOption')('OK')])
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            button_data = [_dependency('seedsigner.gui.screens.screen', 'ButtonOption')(path.relative_to(self.microsd_dir).as_posix(), _dependency('seedsigner.gui.components', 'SeedSignerIconConstants').MICROSD) for path in backup_files]
            selected_menu_num = self.run_screen(_dependency('seedsigner.gui.screens', 'ButtonListScreen'), title=_dependency('gettext', 'gettext')('Select Passport backup'), is_button_text_centered=False, button_data=button_data)
            if selected_menu_num == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            selected_path = backup_files[selected_menu_num]
            return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedPassportBackupCodeEntryView'), view_args={'backup_path': selected_path})
    return SeedPassportBackupSelectView

def _make_SeedPassportBackupCodeEntryView():

    class SeedPassportBackupCodeEntryView(_dependency('seedsigner.views.view', 'View')):

        def __init__(self, backup_path):
            super().__init__()
            self.backup_path = _dependency('pathlib', 'Path')(backup_path)

        def run(self):
            backup_code = self.run_screen(_dependency('seedsigner.gui.screens.screen', 'KeyboardScreen'), title=_dependency('gettext', 'gettext')('Passport backup code'), rows=4, cols=5, keys_charset='0123456789', show_save_button=True)
            if backup_code == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            backup_code = str(backup_code).strip()
            if not backup_code:
                self.run_screen(_dependency('seedsigner.gui.screens', 'WarningScreen'), title='Error', status_headline=None, text=_dependency('gettext', 'gettext')('Backup code cannot be empty.'), show_back_button=False, button_data=[_dependency('seedsigner.gui.screens.screen', 'ButtonOption')('OK')])
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedPassportBackupCodeEntryView'), view_args={'backup_path': self.backup_path})
            try:
                details = _dependency('seedsigner.helpers.passport_backup', 'decode_passport_backup')(self.backup_path, backup_code)
            except (OSError, _dependency('seedsigner.helpers.passport_backup', 'PassportBackupError'), ValueError) as e:
                pass
                self.run_screen(_dependency('seedsigner.gui.screens', 'WarningScreen'), title='Error', status_headline=None, text=str(e), show_back_button=False, button_data=[_dependency('seedsigner.gui.screens.screen', 'ButtonOption')('OK')])
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedPassportBackupCodeEntryView'), view_args={'backup_path': self.backup_path})
            try:
                seed = _dependency('seedsigner.models.seed', 'Seed')(details.mnemonic)
            except _dependency('seedsigner.models.seed', 'InvalidSeedException'):
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedMnemonicInvalidView'))
            self.controller.storage.set_pending_seed(seed)
            return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedPassportBackupSummaryView'), view_args={'details': details})
    return SeedPassportBackupCodeEntryView

def _make_SeedPassportBackupSummaryView():

    class SeedPassportBackupSummaryView(_dependency('seedsigner.views.view', 'View')):
        CONTINUE = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(_dependency('gettext', 'gettext')('Continue'))

        def __init__(self, details):
            super().__init__()
            self.details = details

        def run(self):
            text_lines = []
            if self.details.chain:
                text_lines.append(_dependency('gettext', 'gettext')('Chain: {}'.format(self.details.chain)))
            if self.details.xfp:
                text_lines.append(_dependency('gettext', 'gettext')('XFP: {}'.format(self.details.xfp)))
            if self.details.firmware:
                text_lines.append(_dependency('gettext', 'gettext')('Firmware: {}'.format(self.details.firmware)))
            text_lines.append(_dependency('gettext', 'gettext')('Seed length: {} words').format(len(self.details.mnemonic)))
            self.run_screen(_dependency('seedsigner.gui.screens', 'LargeIconStatusScreen'), title=_dependency('gettext', 'gettext')('Passport backup'), status_headline=_dependency('gettext', 'gettext')('Seed loaded'), text='\n'.join(text_lines), show_back_button=False, button_data=[self.CONTINUE])
            return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedFinalizeView'))
    return SeedPassportBackupSummaryView

def _make_SeedTapsignerBackupSelectView():

    class SeedTapsignerBackupSelectView(_dependency('seedsigner.views.view', 'View')):

        def __init__(self):
            super().__init__()
            self.microsd_dir = _dependency('seedsigner.hardware.microsd', 'MicroSD').get_microsd_dir()

        def _get_backup_files(self):
            backup_files = []
            if not self.microsd_dir.exists():
                raise _dependency('seedsigner.helpers.tapsigner_backup', 'TapsignerBackupError')(_dependency('gettext', 'gettext')('microSD card not detected.'))
            for path in self.microsd_dir.rglob('*'):
                if not path.is_file():
                    continue
                if path.suffix.lower() == '.aes':
                    backup_files.append(path)
            backup_files.sort(key=lambda p: p.relative_to(self.microsd_dir).as_posix().lower())
            return backup_files

        def run(self):
            try:
                backup_files = self._get_backup_files()
            except FeatureUnavailable:
                raise
            except Exception as e:
                self.run_screen(_dependency('seedsigner.gui.screens', 'WarningScreen'), title='Error', status_headline=None, text=str(e), show_back_button=False, button_data=[_dependency('seedsigner.gui.screens.screen', 'ButtonOption')('OK')])
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            if not backup_files:
                self.run_screen(_dependency('seedsigner.gui.screens', 'WarningScreen'), title=_dependency('gettext', 'gettext')('No Backups Found'), status_headline=None, text=_dependency('gettext', 'gettext')('No TAPSIGNER backups (.aes) were found on the microSD card.'), show_back_button=False, button_data=[_dependency('seedsigner.gui.screens.screen', 'ButtonOption')('OK')])
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            selected = self.run_screen(_dependency('seedsigner.gui.screens', 'ButtonListScreen'), title=_dependency('gettext', 'gettext')('Select TAPSIGNER backup'), is_button_text_centered=False, button_data=[_dependency('seedsigner.gui.screens.screen', 'ButtonOption')(path.relative_to(self.microsd_dir).as_posix(), _dependency('seedsigner.gui.components', 'SeedSignerIconConstants').MICROSD) for path in backup_files])
            if selected == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedTapsignerBackupKeyEntryView'), view_args={'backup_path': backup_files[selected]})
    return SeedTapsignerBackupSelectView

def _make_SeedTapsignerBackupKeyEntryView():

    class SeedTapsignerBackupKeyEntryView(_dependency('seedsigner.views.view', 'View')):

        def __init__(self, backup_path):
            super().__init__()
            self.backup_path = backup_path

        def run(self):
            key_hex = self.run_screen(_dependency('seedsigner.gui.screens.screen', 'KeyboardScreen'), title=_dependency('gettext', 'gettext')('Backup key (hex)'), rows=4, cols=8, keys_charset='0123456789abcdef', show_save_button=True)
            if key_hex == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            try:
                xprv, derivation_path = _dependency('seedsigner.helpers.tapsigner_backup', 'decode_tapsigner_backup')(self.backup_path, str(key_hex))
                self.controller.storage.set_pending_seed(_dependency('seedsigner.models.seed', 'XprvSeed')(xprv))
            except (OSError, _dependency('seedsigner.helpers.tapsigner_backup', 'TapsignerBackupError'), _dependency('seedsigner.models.seed', 'InvalidSeedException')) as e:
                self.run_screen(_dependency('seedsigner.gui.screens', 'WarningScreen'), title='Error', status_headline=None, text=str(e), show_back_button=False, button_data=[_dependency('seedsigner.gui.screens.screen', 'ButtonOption')('OK')])
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedTapsignerBackupKeyEntryView'), view_args={'backup_path': self.backup_path})
            return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedTapsignerBackupSummaryView'), view_args={'derivation_path': derivation_path})
    return SeedTapsignerBackupKeyEntryView

def _make_SeedTapsignerBackupSummaryView():

    class SeedTapsignerBackupSummaryView(_dependency('seedsigner.views.view', 'View')):

        def __init__(self, derivation_path):
            super().__init__()
            self.derivation_path = derivation_path

        def run(self):
            text = _dependency('gettext', 'gettext')('xprv loaded from TAPSIGNER backup.')
            if self.derivation_path:
                text = text + '\n' + _dependency('gettext', 'gettext')('Path: {}'.format(self.derivation_path))
            self.run_screen(_dependency('seedsigner.gui.screens', 'LargeIconStatusScreen'), title=_dependency('gettext', 'gettext')('TAPSIGNER backup'), status_headline=_dependency('gettext', 'gettext')('Seed loaded'), text=text, show_back_button=False, button_data=[_dependency('seedsigner.gui.screens.screen', 'ButtonOption')(_dependency('gettext', 'gettext')('Continue'))])
            return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedFinalizeView'))
    return SeedTapsignerBackupSummaryView

def _make_SeedMnemonicEntryView():

    class SeedMnemonicEntryView(_dependency('seedsigner.views.view', 'View')):

        def __init__(self, cur_word_index=0, is_calc_final_word=False):
            super().__init__()
            self.cur_word_index = cur_word_index
            self.cur_word = self.controller.storage.get_pending_mnemonic_word(cur_word_index)
            self.is_calc_final_word = is_calc_final_word

        def run(self):
            ret = self.run_screen(_dependency('seedsigner.gui.screens', 'seed_screens').SeedMnemonicEntryScreen, title=_dependency('gettext', 'gettext')('Seed Word #{}').format(self.cur_word_index + 1), initial_letters=list(self.cur_word) if self.cur_word else ['a'], wordlist=_dependency('seedsigner.models.seed', 'Seed').get_wordlist(wordlist_language_code=self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__WORDLIST_LANGUAGE)))
            if ret == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                if self.cur_word_index == 0:
                    self.controller.storage.discard_pending_mnemonic()
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            self.controller.storage.update_pending_mnemonic(ret, self.cur_word_index)
            if self.is_calc_final_word and self.cur_word_index == self.controller.storage.pending_mnemonic_length - 2:
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.tools_views', 'ToolsCalcFinalWordFinalizePromptView'))
            if self.is_calc_final_word and self.cur_word_index == self.controller.storage.pending_mnemonic_length - 1:
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.tools_views', 'ToolsCalcFinalWordShowFinalWordView'))
            if self.cur_word_index < self.controller.storage.pending_mnemonic_length - 1:
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedMnemonicEntryView'), view_args={'cur_word_index': self.cur_word_index + 1, 'is_calc_final_word': self.is_calc_final_word})
            else:
                try:
                    self.controller.storage.convert_pending_mnemonic_to_pending_seed(wordlist_language_code=self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__WORDLIST_LANGUAGE))
                except _dependency('seedsigner.models.seed', 'InvalidSeedException') as e:
                    if self.controller.storage.pending_is_aezeed and str(e) == 'InvalidPassphraseError':
                        return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedAezeedPassphraseModeView'))
                    return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedMnemonicInvalidView'))
                pending_seed = self.controller.storage.get_pending_seed()
                if isinstance(pending_seed, _dependency('seedsigner.models.seed', 'AezeedSeed')) and pending_seed.seed_bytes is None:
                    return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedAezeedPassphraseModeView'))
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedFinalizeView'))
    return SeedMnemonicEntryView

def _make_SeedMnemonicInvalidView():

    class SeedMnemonicInvalidView(_dependency('seedsigner.views.view', 'View')):
        EDIT = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Review & edit')
        DISCARD = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Discard', button_label_color='red')

        def __init__(self):
            super().__init__()
            self.mnemonic = self.controller.storage.pending_mnemonic

        def run(self):
            button_data = [self.EDIT, self.DISCARD]
            selected_menu_num = self.run_screen(_dependency('seedsigner.gui.screens', 'DireWarningScreen'), title=_dependency('gettext', 'gettext')('Invalid Mnemonic!'), status_icon_name=_dependency('seedsigner.gui.components', 'SeedSignerIconConstants').ERROR, status_headline=None, text=_dependency('gettext', 'gettext')('Checksum failure; not a valid seed phrase.'), show_back_button=False, button_data=button_data)
            if button_data[selected_menu_num] == self.EDIT:
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedMnemonicEntryView'), view_args={'cur_word_index': 0})
            elif button_data[selected_menu_num] == self.DISCARD:
                self.controller.storage.discard_pending_mnemonic()
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'MainMenuView'))
    return SeedMnemonicInvalidView

def _make_SeedFinalizeView():

    class SeedFinalizeView(_dependency('seedsigner.views.view', 'View')):
        FINALIZE = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Done')
        LOAD_SEEDKEEPER = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Load Passphrase')
        TYPE_PASSPHRASE = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Type Passphrase')
        SCAN_PASSPHRASE = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Scan Passphrase')

        def __init__(self):
            super().__init__()
            self.seed = self.controller.storage.get_pending_seed()
            if isinstance(self.seed, _dependency('seedsigner.models.seed', 'XprvSeed')):
                self.fingerprint = self.seed.get_fingerprint(network=self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__NETWORK))
                return
            if self.seed.get_fingerprint == '':
                self.fingerprint = self.seed.get_fingerprint(network=self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__NETWORK))
            elif isinstance(self.seed, _dependency('seedsigner.models.seed', 'AezeedSeed')):
                self.fingerprint = self.seed.get_fingerprint(network=self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__NETWORK))
            else:
                passphrase = self.seed.passphrase
                if isinstance(self.seed, _dependency('seedsigner.models.seed', 'Slip39Seed')):
                    self.seed.set_slip39_passphrase('')
                else:
                    self.seed.set_passphrase('')
                self.fingerprint = self.seed.get_fingerprint(network=self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__NETWORK))
                if isinstance(self.seed, _dependency('seedsigner.models.seed', 'Slip39Seed')):
                    self.seed.set_slip39_passphrase(passphrase)
                else:
                    self.seed.set_passphrase(passphrase)

        def run(self):
            button_data = [self.FINALIZE]
            if isinstance(self.seed, (_dependency('seedsigner.models.seed', 'XprvSeed'), _dependency('seedsigner.models.seed', 'AezeedSeed'))):
                pass
            elif self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__PASSPHRASE) != _dependency('seedsigner.models.settings', 'SettingsConstants').OPTION__DISABLED:
                button_data.append(self.TYPE_PASSPHRASE)
                button_data.append(self.SCAN_PASSPHRASE)
                if self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__SMARTCARD_SUPPORT) == _dependency('seedsigner.models.settings', 'SettingsConstants').OPTION__ENABLED:
                    button_data.append(self.LOAD_SEEDKEEPER)
            selected_menu_num = self.run_screen(_dependency('seedsigner.gui.screens', 'seed_screens').SeedFinalizeScreen, fingerprint=self.fingerprint, button_data=button_data)
            if button_data[selected_menu_num] == self.FINALIZE:
                seed = self.controller.storage.finalize_pending_seed()
                if self.controller.resume_main_flow == _dependency('seedsigner.controller', 'Controller').FLOW__SATOCHIP_IMPORT_SEED:
                    self.controller.resume_main_flow = None
                    return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.tools_views', 'ToolsSatochipImportSeedView'), clear_history=True)
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedOptionsView'), view_args={'seed': seed}, clear_history=True)
            elif button_data[selected_menu_num] == self.TYPE_PASSPHRASE:
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedAddPassphraseView'))
            elif button_data[selected_menu_num] == self.SCAN_PASSPHRASE:
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedScanPassphraseView'))
            elif button_data[selected_menu_num] == self.LOAD_SEEDKEEPER:
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedLoadSeedKeeperPassphraseView'))
            elif selected_menu_num == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
    return SeedFinalizeView

def _make_SeedAezeedPassphraseModeView():

    class SeedAezeedPassphraseModeView(_dependency('seedsigner.views.view', 'View')):
        LOAD_SEEDKEEPER = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Load from SeedKeeper')
        TYPE_PASSPHRASE = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Type Passphrase')
        SCAN_PASSPHRASE = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Scan Passphrase')

        def __init__(self):
            super().__init__()
            self.seed = self.controller.storage.get_pending_seed()

        def run(self):
            if not isinstance(self.seed, _dependency('seedsigner.models.seed', 'AezeedSeed')):
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedAddPassphraseView'))
            button_data = [self.TYPE_PASSPHRASE, self.SCAN_PASSPHRASE]
            if self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__SMARTCARD_SUPPORT) == _dependency('seedsigner.models.settings', 'SettingsConstants').OPTION__ENABLED:
                button_data.append(self.LOAD_SEEDKEEPER)
            selected_menu_num = self.run_screen(_dependency('seedsigner.gui.screens', 'LargeIconStatusScreen'), title=_dependency('gettext', 'gettext')('Aezeed passphrase'), status_icon_name=_dependency('seedsigner.gui.components', 'SeedSignerIconConstants').FINGERPRINT, status_icon_size=_dependency('seedsigner.gui.components', 'GUIConstants').ICON_LARGE_BUTTON_SIZE, status_color=_dependency('seedsigner.gui.components', 'GUIConstants').INFO_COLOR, text=_dependency('gettext', 'gettext')('Passphrase required\nfor this mnemonic.'), is_button_text_centered=False, button_data=button_data, show_back_button=True)
            if selected_menu_num == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                self.controller.storage.clear_pending_seed()
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'MainMenuView'), clear_history=True)
            if button_data[selected_menu_num] == self.TYPE_PASSPHRASE:
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedAddPassphraseView'))
            if button_data[selected_menu_num] == self.SCAN_PASSPHRASE:
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedScanPassphraseView'))
            if button_data[selected_menu_num] == self.LOAD_SEEDKEEPER:
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedLoadSeedKeeperPassphraseView'))
            return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
    return SeedAezeedPassphraseModeView

def _make_SeedAddPassphraseView():

    class SeedAddPassphraseView(_dependency('seedsigner.views.view', 'View')):
        """
    initial_keyboard: used by the screenshot generator to render each different keyboard layout.
    """

        def __init__(self, initial_keyboard=_dependency('seedsigner.gui.screens', 'seed_screens').SeedAddPassphraseScreen.KEYBOARD__LOWERCASE_BUTTON_TEXT):
            super().__init__()
            self.initial_keyboard = initial_keyboard
            self.seed = self.controller.storage.get_pending_seed()

        def run(self):
            passphrase_title = self.seed.passphrase_label
            ret_dict = self.run_screen(_dependency('seedsigner.gui.screens', 'seed_screens').SeedAddPassphraseScreen, passphrase=self.seed.passphrase_display, title=passphrase_title, initial_keyboard=self.initial_keyboard)
            passphrase = ret_dict['passphrase']
            try:
                if isinstance(self.seed, _dependency('seedsigner.models.seed', 'Slip39Seed')):
                    self.seed.set_slip39_passphrase(passphrase)
                else:
                    self.seed.set_passphrase(passphrase)
            except _dependency('seedsigner.models.seed', 'InvalidSeedException') as e:
                if isinstance(self.seed, _dependency('seedsigner.models.seed', 'AezeedSeed')):
                    if passphrase == '':
                        self.run_screen(_dependency('seedsigner.gui.screens', 'WarningScreen'), title=_dependency('gettext', 'gettext')('Invalid passphrase'), status_headline=None, text=_dependency('gettext', 'gettext')('Aezeed passphrase required.\nTry again.'), show_back_button=False, button_data=[_dependency('seedsigner.gui.screens.screen', 'ButtonOption')('OK')])
                        return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedAddPassphraseView'))
                    if str(e) == 'InvalidPassphraseError':
                        self.seed.set_passphrase('')
                        self.run_screen(_dependency('seedsigner.gui.screens', 'WarningScreen'), title=_dependency('gettext', 'gettext')('Invalid passphrase'), status_headline=None, text=_dependency('gettext', 'gettext')('Wrong Aezeed passphrase.\nTry again.'), show_back_button=False, button_data=[_dependency('seedsigner.gui.screens.screen', 'ButtonOption')('OK')])
                        return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedAddPassphraseView'))
                raise
            if 'is_back_button' in ret_dict:
                if isinstance(self.seed, _dependency('seedsigner.models.seed', 'AezeedSeed')):
                    return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedAezeedPassphraseModeView'))
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedAddPassphraseExitDialogView'))
            elif len(self.seed.passphrase) > 0:
                if isinstance(self.seed, _dependency('seedsigner.models.seed', 'AezeedSeed')):
                    return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedFinalizeView'))
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedReviewPassphraseView'))
            else:
                if isinstance(self.seed, _dependency('seedsigner.models.seed', 'AezeedSeed')) and self.seed.seed_bytes is None:
                    self.run_screen(_dependency('seedsigner.gui.screens', 'WarningScreen'), title=_dependency('gettext', 'gettext')('Invalid passphrase'), status_headline=None, text=_dependency('gettext', 'gettext')('Aezeed passphrase required.\nTry again.'), show_back_button=False, button_data=[_dependency('seedsigner.gui.screens.screen', 'ButtonOption')('OK')])
                    return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedAddPassphraseView'))
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedAddPassphraseExitDialogView'))
    return SeedAddPassphraseView

def _make_SeedAddPassphraseExitDialogView():

    class SeedAddPassphraseExitDialogView(_dependency('seedsigner.views.view', 'View')):
        EDIT = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Edit passphrase')
        DISCARD = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Discard passphrase', button_label_color='red')
        SKIP = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Skip passphrase')

        def __init__(self):
            super().__init__()
            self.seed = self.controller.storage.get_pending_seed()

        def run(self):
            if self.seed.passphrase:
                title = _dependency('gettext', 'gettext')('Discard passphrase?')
                message = _dependency('gettext', 'gettext')('Your current passphrase entry will be erased.')
                button_data = [self.EDIT, self.DISCARD]
            else:
                title = _dependency('gettext', 'gettext')('Skip passphrase?')
                message = _dependency('gettext', 'gettext')('You have not entered a passphrase yet.')
                button_data = [self.EDIT, self.SKIP]
            selected_menu_num = self.run_screen(_dependency('seedsigner.gui.screens', 'WarningScreen'), title=title, status_headline=None, text=message, show_back_button=False, button_data=button_data)
            if button_data[selected_menu_num] == self.EDIT:
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedAddPassphraseView'))
            elif button_data[selected_menu_num] in [self.DISCARD, self.SKIP]:
                if isinstance(self.seed, _dependency('seedsigner.models.seed', 'Slip39Seed')):
                    self.seed.set_slip39_passphrase('')
                else:
                    self.seed.set_passphrase('')
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedFinalizeView'))
    return SeedAddPassphraseExitDialogView

def _make_SeedScanPassphraseView():

    class SeedScanPassphraseView(_dependency('seedsigner.views.view', 'View')):

        def __init__(self):
            super().__init__()
            self.seed = self.controller.storage.get_pending_seed()

        def run(self):
            decoder = _dependency('seedsigner.models.decode_qr', 'DecodeQR')(is_passphrase=True)
            self.run_screen(_dependency('seedsigner.gui.screens.scan_screens', 'ScanScreen'), instructions_text=_dependency('gettext', 'gettext')('Scan Passphrase'), decoder=decoder)
            self.controller.reset_screensaver_timeout()
            _dependency('seedsigner_port.clock', None).sleep(0.1)
            if decoder.is_complete:
                passphrase = self.seed.passphrase_display + decoder.get_passphrase()
                if isinstance(self.seed, _dependency('seedsigner.models.seed', 'Slip39Seed')):
                    self.controller.storage.get_pending_seed().set_slip39_passphrase(passphrase)
                    return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedReviewPassphraseView'))
                try:
                    self.controller.storage.get_pending_seed().set_passphrase(passphrase)
                except _dependency('seedsigner.models.seed', 'InvalidSeedException') as e:
                    if isinstance(self.seed, _dependency('seedsigner.models.seed', 'AezeedSeed')) and str(e) == 'InvalidPassphraseError':
                        self.seed.set_passphrase('')
                        self.run_screen(_dependency('seedsigner.gui.screens', 'WarningScreen'), title=_dependency('gettext', 'gettext')('Invalid passphrase'), status_headline=None, text=_dependency('gettext', 'gettext')('Wrong Aezeed passphrase.\nTry again.'), show_back_button=False, button_data=[_dependency('seedsigner.gui.screens.screen', 'ButtonOption')('OK')])
                        return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedAezeedPassphraseModeView'))
                    raise
                if isinstance(self.seed, _dependency('seedsigner.models.seed', 'AezeedSeed')):
                    return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedFinalizeView'))
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedReviewPassphraseView'))
            elif decoder.is_nonUTF8:
                _dependency('seedsigner.gui.screens', 'DireWarningScreen')(title=_dependency('gettext', 'gettext')('Error!'), show_back_button=False, status_headline=_dependency('gettext', 'gettext')('Invalid Text QR Code'), text=_dependency('gettext', 'gettext')('Non UTF-8 data detected.')).display()
                if isinstance(self.seed, _dependency('seedsigner.models.seed', 'AezeedSeed')):
                    return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedAezeedPassphraseModeView'))
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            else:
                if isinstance(self.seed, _dependency('seedsigner.models.seed', 'AezeedSeed')):
                    return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedAezeedPassphraseModeView'))
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
    return SeedScanPassphraseView

def _make_SeedLoadSeedKeeperPassphraseView():

    class SeedLoadSeedKeeperPassphraseView(_dependency('seedsigner.views.view', 'View')):

        def __init__(self):
            super().__init__()
            self.seed = self.controller.storage.get_pending_seed()

        def run(self):
            try:
                Satochip_Connector = _dependency('seedsigner.helpers', 'seedkeeper_utils').init_satochip(self, init_card_filter=['seedkeeper'])
                if not Satochip_Connector:
                    if isinstance(self.seed, _dependency('seedsigner.models.seed', 'AezeedSeed')):
                        return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedAezeedPassphraseModeView'))
                    return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
                self.loading_screen = _dependency('seedsigner.gui.screens.screen', 'LoadingScreenThread')(text='Listing Secrets\n\n\n\n\n\n')
                self.loading_screen.start()
                headers = Satochip_Connector.seedkeeper_list_secret_headers()
                self.loading_screen.stop()
                headers_parsed = []
                button_data = []
                for header in headers:
                    sid = header['id']
                    label = header['label']
                    stype = _dependency('pysatochip.JCconstants', 'SEEDKEEPER_DIC_TYPE').get(header['type'], hex(header['type']))
                    origin = _dependency('pysatochip.JCconstants', 'SEEDKEEPER_DIC_ORIGIN').get(header['origin'], hex(header['origin']))
                    export_rights = _dependency('pysatochip.JCconstants', 'SEEDKEEPER_DIC_EXPORT_RIGHTS').get(header['export_rights'], hex(header['export_rights']))
                    export_nbplain = str(header['export_nbplain'])
                    export_nbsecure = str(header['export_nbsecure'])
                    export_nbcounter = str(header['export_counter']) if header['type'] == 112 else 'N/A'
                    fingerprint = header['fingerprint']
                    if stype == 'Password' and export_rights == 'Plaintext export allowed':
                        headers_parsed.append((sid, label))
                        button_data.append(_dependency('seedsigner.gui.screens.screen', 'ButtonOption')(label))
                print(headers_parsed)
                if len(headers_parsed) < 1:
                    self.run_screen(_dependency('seedsigner.gui.screens', 'WarningScreen'), title='No Secrets to Load', status_headline=None, text='No Password Secrets to Load from Seedkeeper'.format(), show_back_button=False)
                    if isinstance(self.seed, _dependency('seedsigner.models.seed', 'AezeedSeed')):
                        return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedAezeedPassphraseModeView'))
                    return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
                selected_menu_num = self.run_screen(_dependency('seedsigner.gui.screens', 'ButtonListScreen'), title='Select Secret', is_button_text_centered=False, button_data=button_data, show_back_button=True)
                if selected_menu_num == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                    if isinstance(self.seed, _dependency('seedsigner.models.seed', 'AezeedSeed')):
                        return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedAezeedPassphraseModeView'))
                    return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
                self.loading_screen = _dependency('seedsigner.gui.screens.screen', 'LoadingScreenThread')(text='Loading Secret\n\n\n\n\n\n')
                self.loading_screen.start()
                secret_dict = Satochip_Connector.seedkeeper_export_secret(headers_parsed[selected_menu_num][0], None)
                self.loading_screen.stop()
                password_length = secret_dict['secret_list'][0]
                secret_passphrase = _dependency('binascii', None).unhexlify(secret_dict['secret'])[1:password_length + 1].decode()
            except FeatureUnavailable:
                raise
            except Exception as e:
                print(e)
                self.loading_screen.stop()
                _dependency('seedsigner_port.clock', None).sleep(0.1)
                self.run_screen(_dependency('seedsigner.gui.screens', 'WarningScreen'), title='Error', status_headline=None, text=str(e), show_back_button=True)
                if isinstance(self.seed, _dependency('seedsigner.models.seed', 'AezeedSeed')):
                    return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedAezeedPassphraseModeView'))
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            if isinstance(self.seed, _dependency('seedsigner.models.seed', 'Slip39Seed')):
                self.seed.set_slip39_passphrase(secret_passphrase)
                if len(self.seed.passphrase) > 0:
                    return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedReviewPassphraseView'))
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedFinalizeView'))
            try:
                self.seed.set_passphrase(secret_passphrase)
            except _dependency('seedsigner.models.seed', 'InvalidSeedException') as e:
                if isinstance(self.seed, _dependency('seedsigner.models.seed', 'AezeedSeed')) and str(e) == 'InvalidPassphraseError':
                    self.seed.set_passphrase('')
                    self.run_screen(_dependency('seedsigner.gui.screens', 'WarningScreen'), title=_dependency('gettext', 'gettext')('Invalid passphrase'), status_headline=None, text=_dependency('gettext', 'gettext')('Wrong Aezeed passphrase.\nTry again.'), show_back_button=False, button_data=[_dependency('seedsigner.gui.screens.screen', 'ButtonOption')('OK')])
                    return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedAezeedPassphraseModeView'))
                raise
            if isinstance(self.seed, _dependency('seedsigner.models.seed', 'AezeedSeed')):
                if len(self.seed.passphrase) > 0:
                    return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedFinalizeView'))
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedAezeedPassphraseModeView'))
            if len(self.seed.passphrase) > 0:
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedReviewPassphraseView'))
            return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedFinalizeView'))
    return SeedLoadSeedKeeperPassphraseView

def _make_SeedReviewPassphraseView():

    class SeedReviewPassphraseView(_dependency('seedsigner.views.view', 'View')):
        """
        Display the completed passphrase back to the user.
    """
        DONE = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Done')
        EDIT = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Edit passphrase')
        SCAN = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Scan & Append Another')

        def __init__(self):
            super().__init__()
            self.seed = self.controller.storage.get_pending_seed()

        def run(self):
            network = self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__NETWORK)
            passphrase = self.seed.passphrase
            fingerprint_with = self.seed.get_fingerprint(network=network)
            if isinstance(self.seed, _dependency('seedsigner.models.seed', 'Slip39Seed')):
                self.seed.set_slip39_passphrase('')
            else:
                self.seed.set_passphrase('')
            fingerprint_without = self.seed.get_fingerprint(network=network)
            if isinstance(self.seed, _dependency('seedsigner.models.seed', 'Slip39Seed')):
                self.seed.set_slip39_passphrase(passphrase)
            else:
                self.seed.set_passphrase(passphrase)
            button_data = [self.DONE, self.EDIT, self.SCAN]
            selected_menu_num = self.run_screen(_dependency('seedsigner.gui.screens', 'seed_screens').SeedReviewPassphraseScreen, fingerprint_without=fingerprint_without, fingerprint_with=fingerprint_with, passphrase=self.seed.passphrase_display, button_data=button_data)
            if selected_menu_num == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                if isinstance(self.seed, _dependency('seedsigner.models.seed', 'Slip39Seed')):
                    self.seed.set_slip39_passphrase('')
                else:
                    self.seed.set_passphrase('')
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedFinalizeView'))
            elif button_data[selected_menu_num] == self.DONE:
                seed = self.controller.storage.finalize_pending_seed()
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedOptionsView'), view_args={'seed': seed}, clear_history=True)
            elif button_data[selected_menu_num] == self.EDIT:
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedAddPassphraseView'))
            elif button_data[selected_menu_num] == self.SCAN:
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedScanPassphraseView'))
    return SeedReviewPassphraseView

def _make_SeedDiscardView():

    class SeedDiscardView(_dependency('seedsigner.views.view', 'View')):
        KEEP = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Keep seed')
        DISCARD = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Discard', button_label_color='red')

        def __init__(self, seed=None):
            super().__init__()
            if seed is None:
                self.is_pending_seed = True
                self.seed = self.controller.storage.pending_seed
            else:
                self.is_pending_seed = False
                self.seed = seed

        def run(self):
            button_data = [self.KEEP, self.DISCARD]
            fingerprint = self.seed.get_fingerprint(self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__NETWORK))
            text = _dependency('gettext', 'gettext')('Wipe seed {} from the device?').format(fingerprint)
            selected_menu_num = self.run_screen(_dependency('seedsigner.gui.screens', 'WarningScreen'), title=_dependency('gettext', 'gettext')('Discard Seed?'), status_headline=None, text=text, show_back_button=False, button_data=button_data)
            if button_data[selected_menu_num] == self.KEEP:
                if self.is_pending_seed:
                    return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedFinalizeView'), skip_current_view=True)
                else:
                    return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedOptionsView'), view_args={'seed': self.seed}, skip_current_view=True)
            elif button_data[selected_menu_num] == self.DISCARD:
                if self.is_pending_seed:
                    self.controller.storage.clear_pending_seed()
                else:
                    self.controller.discard_seed(self.seed)
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'MainMenuView'), clear_history=True)
    return SeedDiscardView

def _make_SeedAezeedMnemonicStartView():

    class SeedAezeedMnemonicStartView(_dependency('seedsigner.views.view', 'View')):

        def run(self):
            self.run_screen(_dependency('seedsigner.gui.screens', 'WarningScreen'), title=_dependency('gettext', 'gettext')('Aezeed support'), status_headline=None, text=_dependency('gettext', 'gettext')('Aezeed entry is experimental.\nUse only with known-good backups.'), show_back_button=False)
            self.controller.storage.init_pending_mnemonic(num_words=24, is_aezeed=True)
            return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedMnemonicEntryView'))
    return SeedAezeedMnemonicStartView

def _make_SeedElectrumMnemonicStartView():

    class SeedElectrumMnemonicStartView(_dependency('seedsigner.views.view', 'View')):
        """
    Currently just a warning display before entering an Electrum seed.

    Could be expanded with a follow-up View to specify Electrum seed type.
    """

        def run(self):
            self.run_screen(_dependency('seedsigner.gui.screens', 'WarningScreen'), title=_dependency('gettext', 'gettext')('Electrum Warning'), status_headline=None, text=_dependency('gettext', 'gettext')('Some features are disabled for Electrum seeds.'), show_back_button=False)
            self.controller.storage.init_pending_mnemonic(num_words=12, is_electrum=True)
            return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedMnemonicEntryView'))
    return SeedElectrumMnemonicStartView

def _make_SeedSlip39MnemonicStartView():

    class SeedSlip39MnemonicStartView(_dependency('seedsigner.views.view', 'View')):
        """Prompt before entering SLIP-39 shares."""

        def run(self):
            self.controller.storage.discard_pending_slip39_shares()
            TWENTY = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Enter 20 words')
            THIRTYTHREE = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Enter 33 words')
            SCAN = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Scan QR', _dependency('seedsigner.gui.components', 'SeedSignerIconConstants').QRCODE)
            SEEDKEEPER = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('From SeedKeeper', _dependency('seedsigner.gui.components', 'FontAwesomeIconConstants').LOCK)
            button_data = [TWENTY, THIRTYTHREE, SCAN]
            if self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__SMARTCARD_SUPPORT) == _dependency('seedsigner.models.settings', 'SettingsConstants').OPTION__ENABLED:
                button_data.append(SEEDKEEPER)
            selected = self.run_screen(_dependency('seedsigner.gui.screens', 'ButtonListScreen'), title=_dependency('gettext', 'gettext')('Load Share'), is_button_text_centered=False, button_data=button_data)
            if selected == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            if button_data[selected] == SCAN:
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.scan_views', 'ScanSlip39ShareQRView'))
            if button_data[selected] == SEEDKEEPER:
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.seed_views', 'SeedSlip39LoadFromSeedkeeperView'))
            length = 20 if button_data[selected] == TWENTY else 33
            self.controller.storage.init_pending_slip39_share(num_words=length)
            return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedSlip39ShareEntryView'))
    return SeedSlip39MnemonicStartView

def _make_SeedSlip39ShareEntryView():

    class SeedSlip39ShareEntryView(_dependency('seedsigner.views.view', 'View')):

        def __init__(self, cur_word_index=0):
            super().__init__()
            self.cur_word_index = cur_word_index
            self.cur_word = self.controller.storage.get_pending_slip39_word(cur_word_index)

        def run(self):
            slip39_wordlist = _dependency('importlib', 'import_module')('shamir_mnemonic.wordlist').WORDLIST
            ret = self.run_screen(_dependency('seedsigner.gui.screens', 'seed_screens').SeedMnemonicEntryScreen, title=_dependency('gettext', 'gettext')('Share Word #{}').format(self.cur_word_index + 1), initial_letters=list(self.cur_word) if self.cur_word else ['a'], wordlist=slip39_wordlist)
            if ret == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            self.controller.storage.update_pending_slip39_share(ret, self.cur_word_index)
            if self.cur_word_index < self.controller.storage.pending_slip39_share_length - 1:
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedSlip39ShareEntryView'), view_args={'cur_word_index': self.cur_word_index + 1})
            else:
                try:
                    self.controller.storage.finalize_current_slip39_share()
                except _dependency('seedsigner.models.seed', 'InvalidSeedException'):
                    length = self.controller.storage.pending_slip39_share_length
                    self.controller.storage.init_pending_slip39_share(num_words=length)
                    return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedSlip39ShareInvalidView'), view_args={'length': length, 'retry_scan': False}, skip_current_view=True)
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedSlip39MoreSharesView'))
    return SeedSlip39ShareEntryView

def _make_SeedSlip39MoreSharesView():

    class SeedSlip39MoreSharesView(_dependency('seedsigner.views.view', 'View')):
        ADD = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Enter share')
        SCAN = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Scan share', _dependency('seedsigner.gui.components', 'SeedSignerIconConstants').QRCODE)
        SEEDKEEPER = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('From SeedKeeper', _dependency('seedsigner.gui.components', 'FontAwesomeIconConstants').LOCK)
        DONE = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Combine shares')

        def run(self):
            entered = self.controller.storage.slip39_shares_entered
            needed = self.controller.storage.slip39_total_needed
            if needed > entered:
                button_data = [self.ADD, self.SCAN]
                if self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__SMARTCARD_SUPPORT) == _dependency('seedsigner.models.settings', 'SettingsConstants').OPTION__ENABLED:
                    button_data.append(self.SEEDKEEPER)
            else:
                button_data = [self.DONE]
            info_text = None
            if needed:
                info_text = _dependency('gettext', 'gettext')('{} of {} needed').format(entered, needed)
            selected_menu_num = self.run_screen(_dependency('seedsigner.gui.screens', 'ButtonListScreen'), title=info_text, is_button_text_centered=False, button_data=button_data)
            if button_data[selected_menu_num] == self.ADD:
                self.controller.storage.init_pending_slip39_share()
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedSlip39ShareEntryView'))
            elif button_data[selected_menu_num] == self.SCAN:
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.scan_views', 'ScanSlip39ShareQRView'))
            elif button_data[selected_menu_num] == self.SEEDKEEPER:
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.seed_views', 'SeedSlip39LoadFromSeedkeeperView'))
            self.loading_screen = _dependency('seedsigner.gui.screens.screen', 'LoadingScreenThread')(text='Combining Shares\n\n\n\n\n\n')
            self.loading_screen.start()
            try:
                self.controller.storage.convert_pending_slip39_shares_to_pending_seed()
            finally:
                _dependency('seedsigner_port.clock', None).sleep(1)
                self.loading_screen.stop()
            return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedFinalizeView'))
    return SeedSlip39MoreSharesView

def _make_SeedSlip39ShareInvalidView():

    class SeedSlip39ShareInvalidView(_dependency('seedsigner.views.view', 'View')):

        def __init__(self, length, retry_scan):
            super().__init__()
            self.length = length
            self.retry_scan = retry_scan

        def run(self):
            button = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Try Again')
            self.run_screen(_dependency('seedsigner.gui.screens.screen', 'DireWarningScreen'), title=_dependency('gettext', 'gettext')('Invalid SLIP-39 Share'), show_back_button=False, status_icon_name=_dependency('seedsigner.gui.components', 'SeedSignerIconConstants').ERROR, status_headline=None, text=_dependency('gettext', 'gettext')('Checksum failure; not a valid SLIP-39 share.'), button_data=[button])
            if self.retry_scan:
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.scan_views', 'ScanSlip39ShareQRView'), skip_current_view=True)
            else:
                self.controller.storage.init_pending_slip39_share(num_words=self.length)
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedSlip39ShareEntryView'), skip_current_view=True)
    return SeedSlip39ShareInvalidView

def _make_SeedSlip39SelectShareView():

    class SeedSlip39SelectShareView(_dependency('seedsigner.views.view', 'View')):

        def __init__(self, seed, next_view, **next_args):
            super().__init__()
            self.seed = seed
            self.next_view = next_view
            self.next_args = next_args

        def run(self):
            seed = self.seed
            button_data = [_dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Share {0}'.format(i + 1)) for i in range(len(seed.mnemonic_list))]
            selected = self.run_screen(_dependency('seedsigner.gui.screens', 'ButtonListScreen'), title='Select Share', is_button_text_centered=False, button_data=button_data, show_back_button=True)
            if selected == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            self.next_args.update({'seed': self.seed, 'share_index': selected})
            return _dependency('seedsigner_port.navigation', 'Destination')(self.next_view, view_args=self.next_args)
    return SeedSlip39SelectShareView

def _make_SeedSlip39LoadFromSeedkeeperView():

    class SeedSlip39LoadFromSeedkeeperView(_dependency('seedsigner.views.view', 'View')):
        """Load a SLIP-39 share from a SeedKeeper card."""

        def run(self):
            try:
                Satochip_Connector = _dependency('seedsigner.helpers', 'seedkeeper_utils').init_satochip(self, init_card_filter=['seedkeeper'])
                if not Satochip_Connector:
                    return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
                self.loading_screen = _dependency('seedsigner.gui.screens.screen', 'LoadingScreenThread')(text='Listing Secrets\n\n\n\n\n\n')
                self.loading_screen.start()
                headers = Satochip_Connector.seedkeeper_list_secret_headers()
                self.loading_screen.stop()
                headers_parsed = []
                button_data = []
                for header in headers:
                    stype = _dependency('pysatochip.JCconstants', 'SEEDKEEPER_DIC_TYPE').get(header['type'], hex(header['type']))
                    rights = _dependency('pysatochip.JCconstants', 'SEEDKEEPER_DIC_EXPORT_RIGHTS').get(header['export_rights'], hex(header['export_rights']))
                    label = header['label']
                    if stype == 'Password' and rights == 'Plaintext export allowed' and label.startswith('SLIP39:'):
                        headers_parsed.append(header['id'])
                        button_data.append(_dependency('seedsigner.gui.screens.screen', 'ButtonOption')(label[len('SLIP39:'):]))
                if not headers_parsed:
                    self.run_screen(_dependency('seedsigner.gui.screens', 'WarningScreen'), title='No Secrets to Load', status_headline=None, text='No SLIP39 Shares on SeedKeeper', show_back_button=False)
                    return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
                selected = self.run_screen(_dependency('seedsigner.gui.screens', 'ButtonListScreen'), title='Select Share', is_button_text_centered=False, button_data=button_data, show_back_button=True)
                if selected == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                    return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
                self.loading_screen = _dependency('seedsigner.gui.screens.screen', 'LoadingScreenThread')(text='Loading Secret\n\n\n\n\n\n')
                self.loading_screen.start()
                secret_dict = Satochip_Connector.seedkeeper_export_secret(headers_parsed[selected], None)
                self.loading_screen.stop()
                length = secret_dict['secret_list'][0]
                share = _dependency('binascii', None).unhexlify(secret_dict['secret'])[1:length + 1].decode()
                try:
                    self.controller.storage.add_slip39_share_mnemonic(share)
                except _dependency('seedsigner.models.seed', 'InvalidSeedException'):
                    return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedSlip39ShareInvalidView'), view_args={'length': len(share.split()), 'retry_scan': False}, skip_current_view=True)
            except FeatureUnavailable:
                raise
            except Exception as e:
                print(e)
                if hasattr(self, 'loading_screen'):
                    self.loading_screen.stop()
                self.run_screen(_dependency('seedsigner.gui.screens', 'WarningScreen'), title='Error', status_headline=None, text=str(e), show_back_button=True)
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedSlip39MoreSharesView'), skip_current_view=True)
    return SeedSlip39LoadFromSeedkeeperView

def _make_SeedSlip39CreateFromBytesView():

    class SeedSlip39CreateFromBytesView(_dependency('seedsigner.views.view', 'View')):
        """Create a SLIP-39 seed from entropy bytes and start backup."""

        def __init__(self, secret):
            super().__init__()
            self.secret = secret

        def run(self):
            ret = _dependency('seedsigner.gui.screens', 'seed_screens').SeedBIP85SelectChildIndexScreen(title='Num Shares').display()
            if ret == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            num_shares = int(ret)
            ret = _dependency('seedsigner.gui.screens', 'seed_screens').SeedBIP85SelectChildIndexScreen(title='Threshold').display()
            if ret == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            threshold = int(ret)
            if threshold > num_shares:
                raise _dependency('seedsigner.models.seed', 'InvalidSeedException')('The requested threshold must not exceed the number of shares.')
            if threshold == 1 and num_shares > 1:
                raise _dependency('seedsigner.models.seed', 'InvalidSeedException')('Multi-Share with threshold of 1 not allowed.')
            extendable = self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__SLIP39_EXTENDABLE) == _dependency('seedsigner.models.settings', 'SettingsConstants').OPTION__ENABLED
            shares = _dependency('shamir_mnemonic', None).generate_mnemonics(1, [(threshold, num_shares)], self.secret, extendable=extendable)[0]
            seed = _dependency('seedsigner.models.seed', 'Slip39Seed')(mnemonics=shares)
            self.controller.storage.set_pending_seed(seed)
            return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedWordsWarningView'), view_args={'seed': None, 'share_index': 0}, clear_history=True)
    return SeedSlip39CreateFromBytesView

def _make_SeedSlip39RegenerateSharesView():

    class SeedSlip39RegenerateSharesView(_dependency('seedsigner.views.view', 'View')):
        """Regenerate SLIP-39 shares for an existing seed."""

        def __init__(self, seed):
            super().__init__()
            self.seed = seed

        def run(self):
            if not self.seed.extendable:
                self.run_screen(_dependency('seedsigner.gui.screens.screen', 'WarningScreen'), title=_dependency('gettext', 'gettext')('Non-extendable Seed'), show_back_button=False, status_icon_name=_dependency('seedsigner.gui.components', 'SeedSignerIconConstants').ERROR, status_headline=None, text=_dependency('gettext', 'gettext')('This SLIP-39 seed cannot regenerate new shares.'), button_data=[_dependency('seedsigner.gui.screens.screen', 'ButtonOption')('OK')])
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            ret = _dependency('seedsigner.gui.screens', 'seed_screens').SeedBIP85SelectChildIndexScreen(title='Num Shares').display()
            if ret == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            num_shares = int(ret)
            ret = _dependency('seedsigner.gui.screens', 'seed_screens').SeedBIP85SelectChildIndexScreen(title='Threshold').display()
            if ret == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            threshold = int(ret)
            self.seed.regenerate_shares(threshold, num_shares)
            return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedWordsWarningView'), view_args={'seed': self.seed, 'share_index': 0})
    return SeedSlip39RegenerateSharesView

def _make_SeedOptionsView():

    class SeedOptionsView(_dependency('seedsigner.views.view', 'View')):
        SCAN_PSBT = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Scan transaction', _dependency('seedsigner.gui.components', 'SeedSignerIconConstants').QRCODE)
        EXPORT_XPUB = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Export xpub')
        EXPLORER = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Address explorer')
        SIGN_MESSAGE = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Sign message')
        BACKUP = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Backup seed', right_icon_name=_dependency('seedsigner.gui.components', 'SeedSignerIconConstants').CHEVRON_RIGHT)
        BIP85_CHILD_SEED = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('BIP-85 child seed')
        DISCARD = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Discard seed', button_label_color='red')

        def __init__(self, seed):
            super().__init__()
            self.seed = seed

        def run(self):
            if self.controller.unverified_address:
                if self.controller.resume_main_flow == _dependency('seedsigner.controller', 'Controller').FLOW__VERIFY_SINGLESIG_ADDR:
                    self.controller.resume_main_flow = None
                    return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedAddressVerificationView'), view_args=dict(seed=self.seed), skip_current_view=True)
            if self.controller.resume_main_flow == _dependency('seedsigner.controller', 'Controller').FLOW__ADDRESS_EXPLORER:
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedExportXpubScriptTypeView'), view_args=dict(seed=self.seed, sig_type=_dependency('seedsigner.models.settings', 'SettingsConstants').SINGLE_SIG), skip_current_view=True)
            elif self.controller.resume_main_flow == _dependency('seedsigner.controller', 'Controller').FLOW__SIGN_MESSAGE:
                self.controller.sign_message_data['seed'] = self.seed
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedSignMessageConfirmMessageView'), skip_current_view=True)
            if self.controller.psbt:
                if _dependency('seedsigner.models.psbt_parser', 'PSBTParser').has_matching_input_fingerprint(self.controller.psbt, self.seed, network=self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__NETWORK)):
                    if self.controller.resume_main_flow and self.controller.resume_main_flow == _dependency('seedsigner.controller', 'Controller').FLOW__PSBT:
                        self.controller.resume_main_flow = None
                        self.controller.psbt_seed = self.seed
                        return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.psbt_views', 'PSBTOverviewView'), skip_current_view=True)
            button_data = []
            button_data.append(self.SCAN_PSBT)
            button_data.append(self.EXPORT_XPUB)
            button_data.append(self.EXPLORER)
            button_data.append(self.BACKUP)
            if self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__MESSAGE_SIGNING) == _dependency('seedsigner.models.settings', 'SettingsConstants').OPTION__ENABLED:
                button_data.append(self.SIGN_MESSAGE)
            if self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__BIP85_CHILD_SEEDS) == _dependency('seedsigner.models.settings', 'SettingsConstants').OPTION__ENABLED and self.seed.bip85_supported:
                button_data.append(self.BIP85_CHILD_SEED)
            button_data.append(self.DISCARD)
            selected_menu_num = self.run_screen(_dependency('seedsigner.gui.screens', 'seed_screens').SeedOptionsScreen, button_data=button_data, fingerprint=self.seed.get_fingerprint(self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__NETWORK)))
            if selected_menu_num == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'MainMenuView'))
            if button_data[selected_menu_num] == self.SCAN_PSBT:
                self.controller.psbt_seed = self.seed
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.scan_views', 'ScanPSBTView'))
            elif button_data[selected_menu_num] == self.EXPORT_XPUB:
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedExportXpubSigTypeView'), view_args=dict(seed=self.seed))
            elif button_data[selected_menu_num] == self.EXPLORER:
                self.controller.resume_main_flow = _dependency('seedsigner.controller', 'Controller').FLOW__ADDRESS_EXPLORER
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedExportXpubScriptTypeView'), view_args=dict(seed=self.seed, sig_type=_dependency('seedsigner.models.settings', 'SettingsConstants').SINGLE_SIG))
            elif button_data[selected_menu_num] == self.SIGN_MESSAGE:
                self.controller.sign_message_data = dict(seed=self.seed)
                self.controller.resume_main_flow = _dependency('seedsigner.controller', 'Controller').FLOW__SIGN_MESSAGE
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.scan_views', 'ScanView'))
            elif button_data[selected_menu_num] == self.BACKUP:
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedBackupView'), view_args=dict(seed=self.seed))
            elif button_data[selected_menu_num] == self.BIP85_CHILD_SEED:
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedBIP85SelectNumWordsView'), view_args={'seed': self.seed})
            elif button_data[selected_menu_num] == self.DISCARD:
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedDiscardView'), view_args=dict(seed=self.seed))
    return SeedOptionsView

def _make_SeedBackupView():

    class SeedBackupView(_dependency('seedsigner.views.view', 'View')):
        VIEW_WORDS = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('View seed words')
        EXPORT_SEEDQR = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Export as SeedQR')
        EXPORT_PLAINTEXTQR = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Export as Plaintext QR')
        TO_SEEDKEEPER = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('To SeedKeeper')
        TO_SPECTER_DIY = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('To Specter-DIY')
        REGENERATE_SHARES = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Regenerate Shares')

        def __init__(self, seed):
            super().__init__()
            self.seed = seed

        def run(self):
            button_data = [self.VIEW_WORDS]
            if self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__SMARTCARD_SUPPORT) == _dependency('seedsigner.models.settings', 'SettingsConstants').OPTION__ENABLED:
                button_data.append(self.TO_SEEDKEEPER)
            if self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__SPECTER_DIY_SUPPORT) == _dependency('seedsigner.models.settings', 'SettingsConstants').OPTION__ENABLED:
                button_data.append(self.TO_SPECTER_DIY)
            if isinstance(self.seed, _dependency('seedsigner.models.seed', 'Slip39Seed')):
                button_data.append(self.REGENERATE_SHARES)
            if self.seed.seedqr_supported:
                button_data.append(self.EXPORT_SEEDQR)
            if self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__PLAINTEXTQR) == _dependency('seedsigner.models.settings', 'SettingsConstants').OPTION__ENABLED and (not isinstance(self.seed, _dependency('seedsigner.models.seed', 'AezeedSeed'))):
                button_data.append(self.EXPORT_PLAINTEXTQR)
            selected_menu_num = self.run_screen(_dependency('seedsigner.gui.screens', 'ButtonListScreen'), title=_dependency('gettext', 'gettext')('Backup Seed'), button_data=button_data, is_bottom_list=True)
            if selected_menu_num == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            elif button_data[selected_menu_num] == self.VIEW_WORDS:
                if isinstance(self.seed, _dependency('seedsigner.models.seed', 'Slip39Seed')):
                    return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedSlip39SelectShareView'), view_args={'seed': self.seed, 'next_view': _resolve('SeedWordsWarningView')})
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedWordsWarningView'), view_args={'seed': self.seed})
            elif button_data[selected_menu_num] == self.EXPORT_PLAINTEXTQR:
                if isinstance(self.seed, _dependency('seedsigner.models.seed', 'Slip39Seed')):
                    return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedSlip39SelectShareView'), view_args={'seed': self.seed, 'next_view': _resolve('SeedExportPlaintextQRView')})
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedExportPlaintextQRView'), view_args={'seed': self.seed})
            elif button_data[selected_menu_num] == self.EXPORT_SEEDQR:
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedTranscribeSeedQRFormatView'), view_args={'seed': self.seed})
            elif button_data[selected_menu_num] == self.TO_SEEDKEEPER:
                if isinstance(self.seed, _dependency('seedsigner.models.seed', 'Slip39Seed')):
                    return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedSlip39SelectShareView'), view_args={'seed': self.seed, 'next_view': _resolve('SaveToSeedkeeperView')})
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SaveToSeedkeeperView'), view_args={'seed': self.seed})
            elif button_data[selected_menu_num] == self.TO_SPECTER_DIY:
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.tools_views', 'ToolsJavacardSaveMnemonicView'))
            elif button_data[selected_menu_num] == self.REGENERATE_SHARES:
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedSlip39RegenerateSharesView'), view_args={'seed': self.seed})
    return SeedBackupView

def _make_SeedExportXpubSigTypeView():

    class SeedExportXpubSigTypeView(_dependency('seedsigner.views.view', 'View')):
        SINGLE_SIG = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Single Sig', return_data=_dependency('seedsigner.models.settings', 'SettingsConstants').SINGLE_SIG)
        MULTISIG = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Multisig', return_data=_dependency('seedsigner.models.settings', 'SettingsConstants').MULTISIG)

        def __init__(self, seed):
            super().__init__()
            self.seed = seed

        def run(self):
            if len(self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__SIG_TYPES)) == 1:
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedExportXpubScriptTypeView'), view_args={'seed': self.seed, 'sig_type': self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__SIG_TYPES)[0]}, skip_current_view=True)
            button_data = [self.SINGLE_SIG, self.MULTISIG]
            selected_menu_num = self.run_screen(_dependency('seedsigner.gui.screens', 'ButtonListScreen'), title=_dependency('gettext', 'gettext')('Export Xpub'), button_data=button_data)
            if selected_menu_num == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedExportXpubScriptTypeView'), view_args={'seed': self.seed, 'sig_type': button_data[selected_menu_num].return_data})
    return SeedExportXpubSigTypeView

def _make_SeedExportXpubScriptTypeView():

    class SeedExportXpubScriptTypeView(_dependency('seedsigner.views.view', 'View')):

        def __init__(self, seed, sig_type):
            super().__init__()
            self.seed = seed
            self.sig_type = sig_type

        def run(self):
            args = {'seed': self.seed, 'sig_type': self.sig_type}
            script_types = self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__SCRIPT_TYPES)
            seed = self.seed
            if seed.script_override:
                script_types = [seed.script_override]
            if len(script_types) == 1:
                args['script_type'] = script_types[0]
                if args['script_type'] == _dependency('seedsigner.models.settings', 'SettingsConstants').CUSTOM_DERIVATION:
                    return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedExportXpubCustomDerivationView'), view_args=args, skip_current_view=True)
                if self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__ACCOUNT_PROMPT) == _dependency('seedsigner.models.settings', 'SettingsConstants').OPTION__ENABLED:
                    if self.controller.resume_main_flow == _dependency('seedsigner.controller', 'Controller').FLOW__ADDRESS_EXPLORER:
                        del args['sig_type']
                        return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('AccountNumberView'), view_args=dict(next_view_cls=_dependency('seedsigner.views.tools_views', 'ToolsAddressExplorerAddressTypeView'), next_view_args=args), skip_current_view=True)
                    else:
                        return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('AccountNumberView'), view_args=dict(next_view_cls=_resolve('SeedExportXpubQRFormatView'), next_view_args=args), skip_current_view=True)
                elif self.controller.resume_main_flow == _dependency('seedsigner.controller', 'Controller').FLOW__ADDRESS_EXPLORER:
                    del args['sig_type']
                    return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.tools_views', 'ToolsAddressExplorerAddressTypeView'), view_args=args, skip_current_view=True)
                else:
                    return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedExportXpubQRFormatView'), view_args=args, skip_current_view=True)
            title = _dependency('gettext', 'gettext')('Export Xpub')
            if self.controller.resume_main_flow == _dependency('seedsigner.controller', 'Controller').FLOW__ADDRESS_EXPLORER:
                title = _dependency('gettext', 'gettext')('Address Explorer')
            button_data = []
            for script_type, display_name in _dependency('seedsigner.models.settings', 'SettingsConstants').ALL_SCRIPT_TYPES:
                if script_type in self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__SCRIPT_TYPES):
                    button_data.append(_dependency('seedsigner.gui.screens.screen', 'ButtonOption')(display_name, return_data=script_type))
            selected_menu_num = self.run_screen(_dependency('seedsigner.gui.screens', 'ButtonListScreen'), title=title, is_button_text_centered=False, button_data=button_data, is_bottom_list=True)
            if selected_menu_num == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                if len(self.controller.back_stack) >= 2 and self.controller.back_stack[-2].View_cls == _resolve('SeedOptionsView'):
                    self.controller.resume_main_flow = None
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            else:
                args['script_type'] = button_data[selected_menu_num].return_data
                if args['script_type'] == _dependency('seedsigner.models.settings', 'SettingsConstants').CUSTOM_DERIVATION:
                    return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedExportXpubCustomDerivationView'), view_args=args)
                if self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__ACCOUNT_PROMPT) == _dependency('seedsigner.models.settings', 'SettingsConstants').OPTION__ENABLED:
                    if self.controller.resume_main_flow == _dependency('seedsigner.controller', 'Controller').FLOW__ADDRESS_EXPLORER:
                        del args['sig_type']
                        return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('AccountNumberView'), view_args=dict(next_view_cls=_dependency('seedsigner.views.tools_views', 'ToolsAddressExplorerAddressTypeView'), next_view_args=args))
                    else:
                        return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('AccountNumberView'), view_args=dict(next_view_cls=_resolve('SeedExportXpubQRFormatView'), next_view_args=args))
                elif self.controller.resume_main_flow == _dependency('seedsigner.controller', 'Controller').FLOW__ADDRESS_EXPLORER:
                    del args['sig_type']
                    return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.tools_views', 'ToolsAddressExplorerAddressTypeView'), view_args=args)
                else:
                    return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedExportXpubQRFormatView'), view_args=args)
    return SeedExportXpubScriptTypeView

def _make_SeedExportXpubCustomDerivationView():

    class SeedExportXpubCustomDerivationView(_dependency('seedsigner.views.view', 'View')):

        def __init__(self, seed, sig_type, script_type):
            super().__init__()
            self.seed = seed
            self.sig_type = sig_type
            self.script_type = script_type
            self.custom_derivation_path = 'm/'

        def run(self):
            ret = self.run_screen(_dependency('seedsigner.gui.screens', 'seed_screens').SeedExportXpubCustomDerivationScreen, initial_value=self.custom_derivation_path)
            if ret == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            custom_derivation = ret
            if self.controller.resume_main_flow == _dependency('seedsigner.controller', 'Controller').FLOW__ADDRESS_EXPLORER:
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.tools_views', 'ToolsAddressExplorerAddressTypeView'), view_args=dict(seed=self.seed, script_type=self.script_type, custom_derivation=custom_derivation))
            return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedExportXpubQRFormatView'), view_args={'seed': self.seed, 'sig_type': self.sig_type, 'script_type': self.script_type, 'custom_derivation': custom_derivation})
    return SeedExportXpubCustomDerivationView

def _make_AccountNumberView():

    class AccountNumberView(_dependency('seedsigner.views.view', 'View')):

        def __init__(self, next_view_cls, next_view_args):
            super().__init__()
            self.next_view_cls = next_view_cls
            self.next_view_args = next_view_args

        def run(self):
            ret = self.run_screen(_dependency('seedsigner.gui.screens', 'seed_screens').SeedExportXpubAccountNumberScreen, initial_value='0')
            if ret == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            self.next_view_args['account'] = int(ret)
            return _dependency('seedsigner_port.navigation', 'Destination')(self.next_view_cls, view_args=self.next_view_args)
    return AccountNumberView

def _make_SeedExportXpubQRFormatView():

    class SeedExportXpubQRFormatView(_dependency('seedsigner.views.view', 'View')):

        def __init__(self, seed, sig_type, script_type, custom_derivation=None, account=0):
            super().__init__()
            self.seed = seed
            self.sig_type = sig_type
            self.script_type = script_type
            self.custom_derivation = custom_derivation
            self.account = account

        def run(self):
            args = {'seed': self.seed, 'sig_type': self.sig_type, 'script_type': self.script_type, 'custom_derivation': self.custom_derivation, 'account': self.account}
            if len(self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__XPUB_QR_FORMAT)) == 1:
                args['xpub_qr_format'] = self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__XPUB_QR_FORMAT)[0]
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedExportXpubWarningView'), view_args=args, skip_current_view=True)
            button_data = []
            for display_name, setting_option in zip(self.settings.get_multiselect_value_display_names(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__XPUB_QR_FORMAT), self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__XPUB_QR_FORMAT)):
                button_data.append(_dependency('seedsigner.gui.screens.screen', 'ButtonOption')(display_name, return_data=setting_option))
            selected_menu_num = self.run_screen(_dependency('seedsigner.gui.screens', 'ButtonListScreen'), title=_dependency('gettext', 'gettext')('Xpub QR Format'), is_button_text_centered=False, button_data=button_data, is_bottom_list=True)
            if selected_menu_num == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            args['xpub_qr_format'] = button_data[selected_menu_num].return_data
            return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedExportXpubWarningView'), view_args=args)
    return SeedExportXpubQRFormatView

def _make_SeedExportXpubWarningView():

    class SeedExportXpubWarningView(_dependency('seedsigner.views.view', 'View')):

        def __init__(self, seed, sig_type, script_type, xpub_qr_format, custom_derivation, coordinator_label='', account=0):
            super().__init__()
            self.seed = seed
            self.sig_type = sig_type
            self.script_type = script_type
            self.xpub_qr_format = xpub_qr_format
            self.custom_derivation = custom_derivation
            self.coordinator_label = coordinator_label
            self.account = account

        def run(self):
            destination = _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedExportXpubDetailsView'), view_args={'seed': self.seed, 'sig_type': self.sig_type, 'script_type': self.script_type, 'xpub_qr_format': self.xpub_qr_format, 'custom_derivation': self.custom_derivation, 'coordinator_label': self.coordinator_label, 'account': self.account}, skip_current_view=True)
            if self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__PRIVACY_WARNINGS) == _dependency('seedsigner.models.settings', 'SettingsConstants').OPTION__DISABLED:
                return destination
            selected_menu_num = self.run_screen(_dependency('seedsigner.gui.screens', 'WarningScreen'), status_headline=_dependency('gettext', 'gettext')('Privacy Leak!'), text=_dependency('gettext', 'gettext')('Xpub can be used to view all future transactions.'))
            if selected_menu_num == 0:
                return destination
            elif selected_menu_num == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
    return SeedExportXpubWarningView

def _make_SeedExportXpubDetailsView():

    class SeedExportXpubDetailsView(_dependency('seedsigner.views.view', 'View')):
        """
        Collects the user input from all the previous screens leading up to this and
        finally calculates the xpub and displays the summary view to the user.
    """

        def __init__(self, seed, sig_type, script_type, xpub_qr_format, custom_derivation, coordinator_label='', account=0):
            super().__init__()
            self.sig_type = sig_type
            self.script_type = script_type
            self.xpub_qr_format = xpub_qr_format
            self.custom_derivation = custom_derivation
            self.coordinator_label = coordinator_label
            self.account = account
            self.seed = seed

        def run(self):
            seed_derivation_override = self.seed.derivation_override(self.sig_type)
            if self.script_type == _dependency('seedsigner.models.settings', 'SettingsConstants').CUSTOM_DERIVATION:
                derivation_path = self.custom_derivation
            elif seed_derivation_override:
                derivation_path = seed_derivation_override
            else:
                derivation_path = _dependency('seedsigner.helpers', 'embit_utils').get_standard_derivation_path(network=self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__NETWORK), wallet_type=self.sig_type, script_type=self.script_type, account=self.account)
            if self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__XPUB_DETAILS) == _dependency('seedsigner.models.settings', 'SettingsConstants').OPTION__DISABLED:
                selected_menu_num = 0
            else:
                self.loading_screen = _dependency('seedsigner.gui.screens.screen', 'LoadingScreenThread')(text=_dependency('gettext', 'gettext')('Generating xpub...'))
                self.loading_screen.start()
                try:
                    embit_network = _dependency('embit.networks', 'NETWORKS')[_dependency('seedsigner.models.settings', 'SettingsConstants').map_network_to_embit(self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__NETWORK))]
                    version = self.seed.detect_version(derivation_path, self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__NETWORK), self.sig_type)
                    root = self.seed.get_root(self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__NETWORK))
                    fingerprint = _dependency('binascii', 'hexlify')(root.child(0).fingerprint).decode('utf-8')
                    xprv = root.derive(derivation_path)
                    xpub = xprv.to_public()
                    xpub_base58 = xpub.to_string(version=version)
                finally:
                    self.loading_screen.stop()
                selected_menu_num = self.run_screen(_dependency('seedsigner.gui.screens', 'seed_screens').SeedExportXpubDetailsScreen, fingerprint=fingerprint, derivation_path=derivation_path, xpub=xpub_base58)
            if selected_menu_num == 0:
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedExportXpubQRDisplayView'), dict(seed=self.seed, xpub_qr_format=self.xpub_qr_format, derivation_path=derivation_path, sig_type=self.sig_type, script_type=self.script_type, coordinator_label=self.coordinator_label))
            elif selected_menu_num == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
    return SeedExportXpubDetailsView

def _make_SeedExportXpubQRDisplayView():

    class SeedExportXpubQRDisplayView(_dependency('seedsigner.views.view', 'View')):

        def __init__(self, seed, xpub_qr_format, derivation_path, sig_type=_dependency('seedsigner.models.settings', 'SettingsConstants').SINGLE_SIG, script_type=_dependency('seedsigner.models.settings', 'SettingsConstants').NATIVE_SEGWIT, coordinator_label=''):
            super().__init__()
            self.seed = seed
            self.seed = seed
            self.script_type = script_type
            self.sig_type = sig_type
            self.derivation_path = derivation_path
            self.coordinator_label = coordinator_label
            encoder_args = dict(seed=self.seed, derivation=derivation_path, network=self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__NETWORK), qr_density=self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__QR_DENSITY), sig_type=sig_type)
            if xpub_qr_format == _dependency('seedsigner.models.settings', 'SettingsConstants').XPUB_QR_FORMAT__STATIC:
                self.qr_encoder = _dependency('seedsigner.models.encode_qr', 'StaticXpubQrEncoder')(**encoder_args)
            elif xpub_qr_format == _dependency('seedsigner.models.settings', 'SettingsConstants').XPUB_QR_FORMAT__SPECTER_LEGACY:
                self.qr_encoder = _dependency('seedsigner.models.encode_qr', 'SpecterLegacyXPubQrEncoder')(**encoder_args)
            else:
                self.qr_encoder = _dependency('seedsigner.models.encode_qr', 'UrXpubQrEncoder')(**encoder_args)

        def run(self):
            self.run_screen(_dependency('seedsigner.gui.screens.screen', 'QRDisplayScreen'), qr_encoder=self.qr_encoder)
            if self.sig_type == _dependency('seedsigner.models.settings', 'SettingsConstants').SINGLE_SIG:
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedExportXpubVerifyAddressView'), view_args=dict(seed=self.seed, derivation_path=self.derivation_path, script_type=self.script_type, sig_type=self.sig_type, coordinator_label=self.coordinator_label), skip_current_view=True)
            return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'MainMenuView'))
    return SeedExportXpubQRDisplayView

def _make_SeedExportXpubVerifyAddressView():

    class SeedExportXpubVerifyAddressView(_dependency('seedsigner.views.view', 'View')):

        def __init__(self, seed, derivation_path, script_type, sig_type, coordinator_label):
            super().__init__()
            self.seed = seed
            self.derivation_path = derivation_path
            self.script_type = script_type
            self.sig_type = sig_type
            self.coordinator_label = coordinator_label

        def run(self):
            self.run_screen(_dependency('seedsigner.gui.screens', 'LargeIconStatusScreen'), title=_dependency('gettext', 'gettext')('Verify Address'), status_icon_name=_dependency('seedsigner.gui.components', 'SeedSignerIconConstants').QRCODE, status_headline=None, text=_dependency('gettext', 'gettext')('Open {} and display a receive address from the wallet you just exported.').format(self.coordinator_label or _dependency('gettext', 'gettext')('your wallet software')), button_data=[_dependency('seedsigner.gui.screens.screen', 'ButtonOption')(_dependency('gettext', 'gettext')('Scan'))], show_back_button=False)
            return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.scan_views', 'ScanXpubAddressView'), view_args=dict(seed=self.seed, derivation_path=self.derivation_path, script_type=self.script_type, sig_type=self.sig_type, coordinator_label=self.coordinator_label), skip_current_view=True)
    return SeedExportXpubVerifyAddressView

def _make_SeedWordsWarningView():

    class SeedWordsWarningView(_dependency('seedsigner.views.view', 'View')):

        def __init__(self, seed, bip85_data=None, share_index=None):
            super().__init__()
            self.seed = seed
            self.bip85_data = bip85_data
            self.share_index = share_index

        def run(self):
            destination = _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedWordsView'), view_args=dict(seed=self.seed, page_index=0, bip85_data=self.bip85_data, share_index=self.share_index), skip_current_view=True)
            if self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__DIRE_WARNINGS) == _dependency('seedsigner.models.settings', 'SettingsConstants').OPTION__DISABLED:
                return destination
            warning_text = _dependency('gettext', 'gettext')('You must keep your seed words private & away from all online devices.')
            if self.seed is not None:
                seed = self.seed
                if isinstance(seed, _dependency('seedsigner.models.seed', 'AezeedSeed')) and len(seed.passphrase) > 0:
                    warning_text = _dependency('gettext', 'gettext')("Passphrase was used.\nYou'll need words + passphrase.")
            selected_menu_num = self.run_screen(_dependency('seedsigner.gui.screens', 'DireWarningScreen'), text=warning_text)
            if selected_menu_num == 0:
                return destination
            elif selected_menu_num == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
    return SeedWordsWarningView

def _make_SeedWordsView():

    class SeedWordsView(_dependency('seedsigner.views.view', 'View')):
        NEXT = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Next')
        DONE = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Done')

        def __init__(self, seed, bip85_data=None, page_index=0, share_index=None):
            super().__init__()
            if seed is None:
                self.is_pending_seed = True
                self.seed = self.controller.storage.get_pending_seed()
            else:
                self.is_pending_seed = False
                self.seed = seed
            self.bip85_data = bip85_data
            self.page_index = page_index
            self.share_index = share_index

        def run(self):
            words_per_page = 4
            if self.bip85_data is not None:
                mnemonic = self.seed.get_bip85_child_mnemonic(self.bip85_data['child_index'], self.bip85_data['num_words']).split()
                title = _dependency('gettext', 'gettext')('Child #{}').format(self.bip85_data['child_index'])
            else:
                if isinstance(self.seed, _dependency('seedsigner.models.seed', 'Slip39Seed')) and self.share_index is not None:
                    mnemonic = self.seed.mnemonic_list[self.share_index].split()
                else:
                    try:
                        mnemonic = self.seed.mnemonic_display_list
                    except _dependency('seedsigner.models.seed', 'SeedWordsUnavailableException') as e:
                        self.run_screen(_dependency('seedsigner.gui.screens', 'WarningScreen'), title=_dependency('gettext', 'gettext')('Seed Words'), status_headline=None, text=str(e), show_back_button=False, button_data=[_dependency('seedsigner.gui.screens.screen', 'ButtonOption')(_dependency('gettext', 'gettext')('OK'))])
                        return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
                title = _dependency('gettext', 'gettext')('Seed Words')
            words = mnemonic[self.page_index * words_per_page:(self.page_index + 1) * words_per_page]
            button_data = []
            num_pages = (len(mnemonic) + words_per_page - 1) // words_per_page
            if self.page_index < num_pages - 1 or self.is_pending_seed:
                button_data.append(self.NEXT)
            else:
                button_data.append(self.DONE)
            selected_menu_num = self.run_screen(_dependency('seedsigner.gui.screens', 'seed_screens').SeedWordsScreen, title='{0}: {1}/{2}'.format(title, self.page_index + 1, num_pages), words=words, page_index=self.page_index, num_pages=num_pages, button_data=button_data)
            if selected_menu_num == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            if self.is_pending_seed:
                self.seed = None
            if button_data[selected_menu_num] == self.NEXT:
                if self.is_pending_seed and self.page_index == num_pages - 1:
                    return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedWordsBackupTestPromptView'), view_args=dict(seed=self.seed, bip85_data=self.bip85_data, share_index=self.share_index))
                else:
                    return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedWordsView'), view_args=dict(seed=self.seed, page_index=self.page_index + 1, bip85_data=self.bip85_data, share_index=self.share_index))
            elif button_data[selected_menu_num] == self.DONE:
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedWordsBackupTestPromptView'), view_args=dict(seed=self.seed, bip85_data=self.bip85_data, share_index=self.share_index))
    return SeedWordsView

def _make_SeedBIP85SelectNumWordsView():

    class SeedBIP85SelectNumWordsView(_dependency('seedsigner.views.view', 'View')):
        WORDS_12 = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('12 Words')
        WORDS_18 = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('18 Words')
        WORDS_24 = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('24 Words')

        def __init__(self, seed):
            super().__init__()
            self.seed = seed
            self.num_words = 0

        def run(self):
            button_data = [self.WORDS_12, self.WORDS_18, self.WORDS_24]
            selected_menu_num = self.run_screen(_dependency('seedsigner.gui.screens', 'ButtonListScreen'), title=_dependency('gettext', 'gettext')('BIP-85 Num Words'), button_data=button_data)
            if selected_menu_num == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            if button_data[selected_menu_num] == self.WORDS_12:
                self.num_words = 12
            elif button_data[selected_menu_num] == self.WORDS_18:
                self.num_words = 18
            elif button_data[selected_menu_num] == self.WORDS_24:
                self.num_words = 24
            return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedBIP85SelectChildIndexView'), view_args=dict(seed=self.seed, num_words=self.num_words))
    return SeedBIP85SelectNumWordsView

def _make_SeedBIP85SelectChildIndexView():

    class SeedBIP85SelectChildIndexView(_dependency('seedsigner.views.view', 'View')):

        def __init__(self, seed, num_words):
            super().__init__()
            self.seed = seed
            self.num_words = num_words

        def run(self):
            ret = self.run_screen(_dependency('seedsigner.gui.screens', 'seed_screens').SeedBIP85SelectChildIndexScreen)
            if ret == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            if not 0 <= int(ret) < 2 ** 31:
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedBIP85InvalidChildIndexView'), view_args=dict(seed=self.seed, num_words=self.num_words), skip_current_view=True)
            return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedWordsBackupTestPromptView'), view_args=dict(seed=self.seed, bip85_data=dict(child_index=int(ret), num_words=self.num_words)))
    return SeedBIP85SelectChildIndexView

def _make_SeedBIP85InvalidChildIndexView():

    class SeedBIP85InvalidChildIndexView(_dependency('seedsigner.views.view', 'View')):

        def __init__(self, seed, num_words):
            super().__init__()
            self.seed = seed
            self.num_words = num_words

        def run(self):
            self.run_screen(_dependency('seedsigner.gui.screens', 'DireWarningScreen'), title=_dependency('gettext', 'gettext')('BIP-85 Index Error'), show_back_button=False, status_icon_name=_dependency('seedsigner.gui.components', 'SeedSignerIconConstants').ERROR, status_headline=_dependency('gettext', 'gettext')('Invalid Child Index'), text=_dependency('gettext', 'gettext')('BIP-85 Child Index must be between 0 and 2^31-1.'), button_data=[_dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Try again')])
            return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedBIP85SelectChildIndexView'), view_args=dict(seed=self.seed, num_words=self.num_words), skip_current_view=True)
    return SeedBIP85InvalidChildIndexView

def _make_SeedWordsBackupTestPromptView():

    class SeedWordsBackupTestPromptView(_dependency('seedsigner.views.view', 'View')):
        VERIFY = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Verify')
        REVIEW = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Review')
        SKIP = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Skip')
        FINALIZE = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Finalize child')

        def __init__(self, seed, bip85_data=None, share_index=None):
            super().__init__()
            self.seed = seed
            self.bip85_data = bip85_data
            self.share_index = share_index

        def run(self):
            button_data = [self.VERIFY, self.REVIEW, self.SKIP]
            if self.seed is not None and self.bip85_data:
                button_data.append(self.FINALIZE)
            selected_menu_num = self.run_screen(_dependency('seedsigner.gui.screens', 'seed_screens').SeedWordsBackupTestPromptScreen, button_data=button_data)
            if button_data[selected_menu_num] == self.VERIFY:
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedWordsBackupTestView'), view_args=dict(seed=self.seed, bip85_data=self.bip85_data, share_index=self.share_index))
            elif button_data[selected_menu_num] == self.REVIEW:
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedWordsWarningView'), view_args=dict(seed=self.seed, bip85_data=self.bip85_data, share_index=self.share_index))
            elif button_data[selected_menu_num] == self.SKIP:
                seed = self.controller.storage.get_pending_seed() if self.seed is None else self.seed
                if isinstance(seed, _dependency('seedsigner.models.seed', 'Slip39Seed')) and self.share_index is not None and (self.share_index < len(seed.mnemonic_list) - 1):
                    return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedWordsWarningView'), view_args=dict(seed=self.seed, share_index=self.share_index + 1))
                if self.seed is not None:
                    return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedOptionsView'), view_args=dict(seed=self.seed))
                else:
                    return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedFinalizeView'))
            elif button_data[selected_menu_num] == self.FINALIZE:
                parent = self.seed
                child = _dependency('seedsigner.models.seed', 'Seed')(parent.get_bip85_child_mnemonic(self.bip85_data['child_index'], self.bip85_data['num_words']).split())
                self.controller.storage.set_pending_seed(child)
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedFinalizeView'))
    return SeedWordsBackupTestPromptView

def _make_SeedWordsBackupTestView():

    class SeedWordsBackupTestView(_dependency('seedsigner.views.view', 'View')):

        def __init__(self, seed, bip85_data=None, confirmed_list=None, cur_index=None, rand_seed=None, share_index=None):
            """
        Note: `rand_seed` is ONLY USED BY THE SCREENSHOT GENERATOR!!! (to ensure
        consistent screenshot results).
        """
            super().__init__()
            if seed is None:
                self.is_pending_seed = True
                self.seed = self.controller.storage.get_pending_seed()
            else:
                self.is_pending_seed = False
                self.seed = seed
            self.bip85_data = bip85_data
            self.share_index = share_index
            if self.bip85_data is not None:
                self.mnemonic_list = self.seed.get_bip85_child_mnemonic(self.bip85_data['child_index'], self.bip85_data['num_words']).split()
            elif isinstance(self.seed, _dependency('seedsigner.models.seed', 'Slip39Seed')) and self.share_index is not None:
                self.mnemonic_list = self.seed.mnemonic_list[self.share_index].split()
            else:
                self.mnemonic_list = self.seed.mnemonic_display_list
            self.confirmed_list = confirmed_list
            if not self.confirmed_list:
                self.confirmed_list = []
            self.cur_index = cur_index
            self.rand_seed = rand_seed

        def run(self):
            if self.rand_seed is not None:
                _dependency('seedsigner_port.quiz_random', None).seed(self.rand_seed + self.cur_index if self.cur_index is not None else 0)
            if self.cur_index is None:
                self.cur_index = int(_dependency('seedsigner_port.quiz_random', None).random() * len(self.mnemonic_list))
                while self.cur_index in self.confirmed_list:
                    self.cur_index = int(_dependency('seedsigner_port.quiz_random', None).random() * len(self.mnemonic_list))
            real_word = _dependency('seedsigner.gui.screens.screen', 'ButtonOptionWithoutTranslation')(self.mnemonic_list[self.cur_index])
            fake_word1 = _dependency('seedsigner.gui.screens.screen', 'ButtonOptionWithoutTranslation')(''.join(_dependency('embit', 'bip39').WORDLIST[int(_dependency('seedsigner_port.quiz_random', None).random() * 2047)]))
            fake_word2 = _dependency('seedsigner.gui.screens.screen', 'ButtonOptionWithoutTranslation')(''.join(_dependency('embit', 'bip39').WORDLIST[int(_dependency('seedsigner_port.quiz_random', None).random() * 2047)]))
            fake_word3 = _dependency('seedsigner.gui.screens.screen', 'ButtonOptionWithoutTranslation')(''.join(_dependency('embit', 'bip39').WORDLIST[int(_dependency('seedsigner_port.quiz_random', None).random() * 2047)]))
            button_data = [real_word, fake_word1, fake_word2, fake_word3]
            _dependency('seedsigner_port.quiz_random', None).shuffle(button_data)
            title = _dependency('gettext', 'gettext')('Verify Word #{}').format(self.cur_index + 1)
            selected_menu_num = self.run_screen(_dependency('seedsigner.gui.screens', 'ButtonListScreen'), title=title, show_back_button=False, button_data=button_data, is_bottom_list=True, is_button_text_centered=True)
            if self.is_pending_seed:
                self.seed = None
            if button_data[selected_menu_num] == real_word:
                self.confirmed_list.append(self.cur_index)
                if len(self.confirmed_list) == len(self.mnemonic_list):
                    return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedWordsBackupTestSuccessView'), view_args=dict(seed=self.seed, bip85_data=self.bip85_data, share_index=self.share_index))
                else:
                    return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedWordsBackupTestView'), view_args=dict(seed=self.seed, confirmed_list=list(self.confirmed_list), bip85_data=self.bip85_data, share_index=self.share_index))
            else:
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedWordsBackupTestMistakeView'), view_args=dict(seed=self.seed, bip85_data=self.bip85_data, cur_index=self.cur_index, wrong_word=button_data[selected_menu_num].button_label, confirmed_list=list(self.confirmed_list), share_index=self.share_index))
    return SeedWordsBackupTestView

def _make_SeedWordsBackupTestMistakeView():

    class SeedWordsBackupTestMistakeView(_dependency('seedsigner.views.view', 'View')):
        REVIEW = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Review seed words')
        RETRY = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Try again')

        def __init__(self, seed, bip85_data=None, cur_index=None, wrong_word=None, confirmed_list=None, share_index=None):
            super().__init__()
            self.seed = seed
            self.bip85_data = bip85_data
            self.cur_index = cur_index
            self.wrong_word = wrong_word
            self.confirmed_list = confirmed_list
            self.share_index = share_index

        def run(self):
            button_data = [self.REVIEW, self.RETRY]
            text = _dependency('gettext', 'gettext')('Word #{} is not "{}"!').format(self.cur_index + 1, self.wrong_word)
            status_headline = _dependency('gettext', 'gettext')('Wrong Word!')
            selected_menu_num = self.run_screen(_dependency('seedsigner.gui.screens', 'DireWarningScreen'), title=_dependency('gettext', 'gettext')('Verification Error'), show_back_button=False, status_icon_name=_dependency('seedsigner.gui.components', 'SeedSignerIconConstants').ERROR, status_headline=status_headline, button_data=button_data, text=text)
            if button_data[selected_menu_num] == self.REVIEW:
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedWordsView'), view_args=dict(seed=self.seed, bip85_data=self.bip85_data, share_index=self.share_index))
            elif button_data[selected_menu_num] == self.RETRY:
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedWordsBackupTestView'), view_args=dict(seed=self.seed, confirmed_list=self.confirmed_list, cur_index=self.cur_index, bip85_data=self.bip85_data, share_index=self.share_index))
    return SeedWordsBackupTestMistakeView

def _make_SeedWordsBackupTestSuccessView():

    class SeedWordsBackupTestSuccessView(_dependency('seedsigner.views.view', 'View')):

        def __init__(self, seed, bip85_data=None, share_index=None):
            super().__init__()
            self.seed = seed
            self.bip85_data = bip85_data
            self.share_index = share_index

        def run(self):
            self.run_screen(_dependency('seedsigner.gui.screens.screen', 'LargeIconStatusScreen'), title=_dependency('gettext', 'gettext')('Backup Verified'), show_back_button=False, status_headline=_dependency('gettext', 'gettext')('Success!'), text=_dependency('gettext', 'gettext')('All mnemonic backup words were successfully verified!'), button_data=[_dependency('seedsigner.gui.screens.screen', 'ButtonOption')('OK')])
            if self.seed is not None and self.bip85_data:
                parent = self.seed
                child = _dependency('seedsigner.models.seed', 'Seed')(parent.get_bip85_child_mnemonic(self.bip85_data['child_index'], self.bip85_data['num_words']).split())
                self.controller.storage.set_pending_seed(child)
                self.seed = None
            if self.seed is not None:
                seed = self.seed
                if isinstance(seed, _dependency('seedsigner.models.seed', 'Slip39Seed')) and self.share_index is not None and (self.share_index < len(seed.mnemonic_list) - 1):
                    return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedWordsWarningView'), view_args={'seed': self.seed, 'share_index': self.share_index + 1})
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedOptionsView'), view_args=dict(seed=self.seed), clear_history=True)
            else:
                seed = self.controller.storage.get_pending_seed()
                if isinstance(seed, _dependency('seedsigner.models.seed', 'Slip39Seed')) and self.share_index is not None and (self.share_index < len(seed.mnemonic_list) - 1):
                    return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedWordsWarningView'), view_args={'seed': None, 'share_index': self.share_index + 1})
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedFinalizeView'))
    return SeedWordsBackupTestSuccessView

def _make_SeedTranscribeSeedQRFormatView():

    class SeedTranscribeSeedQRFormatView(_dependency('seedsigner.views.view', 'View')):

        def __init__(self, seed):
            super().__init__()
            self.seed = seed

        def run(self):
            seed = self.seed
            encoder_args = dict(mnemonic=seed.mnemonic_list, wordlist_language_code=self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__WORDLIST_LANGUAGE))
            qr_helper = _dependency('seedsigner.helpers.qr', 'QR')()
            button_data = []
            standard_encoder = _dependency('seedsigner.models.encode_qr', 'SeedQrEncoder')(**encoder_args)
            standard_modules = qr_helper.qrsize(standard_encoder.next_part())
            button_data.append(_dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Standard: {0}x{1}'.format(standard_modules, standard_modules), return_data=(_dependency('seedsigner.models.qr_type', 'QRType').SEED__SEEDQR, standard_modules)))
            if self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__COMPACT_SEEDQR) == _dependency('seedsigner.models.settings', 'SettingsConstants').OPTION__ENABLED:
                compact_encoder = _dependency('seedsigner.models.encode_qr', 'CompactSeedQrEncoder')(**encoder_args)
                compact_modules = qr_helper.qrsize(compact_encoder.next_part())
                button_data.append(_dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Compact: {0}x{1}'.format(compact_modules, compact_modules), return_data=(_dependency('seedsigner.models.qr_type', 'QRType').SEED__COMPACTSEEDQR, compact_modules)))
            if self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__ENCRYPTED_QR) == _dependency('seedsigner.models.settings', 'SettingsConstants').OPTION__ENABLED:
                button_data.append(_dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Encrypted', return_data=(_dependency('seedsigner.models.qr_type', 'QRType').SEED__ENCRYPTEDQR, 0)))
            if len(button_data) == 1:
                seedqr_format, num_modules = button_data[0].return_data
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedTranscribeSeedQRWarningView'), view_args={'seed': self.seed, 'seedqr_format': seedqr_format, 'num_modules': num_modules}, skip_current_view=True)
            selected_menu_num = self.run_screen(_dependency('seedsigner.gui.screens', 'seed_screens').SeedTranscribeSeedQRFormatScreen, title=_dependency('gettext', 'gettext')('SeedQR Format'), is_compactqr=self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__COMPACT_SEEDQR) == _dependency('seedsigner.models.settings', 'SettingsConstants').OPTION__ENABLED, is_encryptedqr=self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__ENCRYPTED_QR) == _dependency('seedsigner.models.settings', 'SettingsConstants').OPTION__ENABLED, button_data=button_data)
            if selected_menu_num == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            seedqr_format, num_modules = button_data[selected_menu_num].return_data
            return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedTranscribeSeedQRWarningView'), view_args={'seed': self.seed, 'seedqr_format': seedqr_format, 'num_modules': num_modules})
    return SeedTranscribeSeedQRFormatView

def _make_SeedTranscribeSeedQRWarningView():

    class SeedTranscribeSeedQRWarningView(_dependency('seedsigner.views.view', 'View')):

        def __init__(self, seed, seedqr_format=_dependency('seedsigner.models.qr_type', 'QRType').SEED__SEEDQR, num_modules=29):
            super().__init__()
            self.seed = seed
            self.seedqr_format = seedqr_format
            self.num_modules = num_modules

        def run(self):
            destination = _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedTranscribeSeedQRWholeQRView'), view_args={'seed': self.seed, 'seedqr_format': self.seedqr_format, 'num_modules': self.num_modules}, skip_current_view=True)
            if self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__DIRE_WARNINGS) == _dependency('seedsigner.models.settings', 'SettingsConstants').OPTION__DISABLED:
                return destination
            selected_menu_num = self.run_screen(_dependency('seedsigner.gui.screens', 'DireWarningScreen'), status_headline=_dependency('gettext', 'gettext')('SeedQR is your private key!'), text=_dependency('gettext', 'gettext')('Never photograph or scan it into a device that connects to the internet.'))
            if selected_menu_num == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            else:
                return destination
    return SeedTranscribeSeedQRWarningView

def _make_SeedTranscribeSeedQRWholeQRView():

    class SeedTranscribeSeedQRWholeQRView(_dependency('seedsigner.views.view', 'View')):

        def __init__(self, seed, seedqr_format, num_modules):
            super().__init__()
            self.seed = seed
            self.seedqr_format = seedqr_format
            self.num_modules = num_modules
            self.seed = seed

        def run(self):
            if self.seedqr_format == _dependency('seedsigner.models.qr_type', 'QRType').SEED__ENCRYPTEDQR:
                TYPE = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Type encryption key')
                SCAN = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Scan encryption key')
                button_data = [TYPE, SCAN]
                selected_menu_num = self.run_screen(_dependency('seedsigner.gui.screens', 'ButtonListScreen'), title=_dependency('gettext', 'gettext')('Input Encryption Key'), button_data=button_data)
                if selected_menu_num == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                    return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
                elif button_data[selected_menu_num] == TYPE:
                    return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedEncryptedQRTypeEncryptionKeyView'), view_args=dict(seed=self.seed))
                elif button_data[selected_menu_num] == SCAN:
                    return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedEncryptedQRScanEncryptionKeyView'), view_args=dict(seed=self.seed))
            else:
                encoder_args = dict(mnemonic=self.seed.mnemonic_list, wordlist_language_code=self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__WORDLIST_LANGUAGE))
                if self.seedqr_format == _dependency('seedsigner.models.qr_type', 'QRType').SEED__SEEDQR:
                    e = _dependency('seedsigner.models.encode_qr', 'SeedQrEncoder')(**encoder_args)
                elif self.seedqr_format == _dependency('seedsigner.models.qr_type', 'QRType').SEED__COMPACTSEEDQR:
                    e = _dependency('seedsigner.models.encode_qr', 'CompactSeedQrEncoder')(**encoder_args)
                data = e.next_part()
                ret = self.run_screen(_dependency('seedsigner.gui.screens', 'seed_screens').SeedTranscribeSeedQRWholeQRScreen, qr_data=data, num_modules=self.num_modules)
                if ret == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                    return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
                else:
                    return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedTranscribeSeedQRZoomedInView'), view_args={'seed': self.seed, 'seedqr_format': self.seedqr_format})
    return SeedTranscribeSeedQRWholeQRView

def _make_SeedEncryptedQRTypeEncryptionKeyView():

    class SeedEncryptedQRTypeEncryptionKeyView(_dependency('seedsigner.views.view', 'View')):

        def __init__(self, seed, encryption_key=''):
            super().__init__()
            self.seed = seed
            self.encryption_key = encryption_key

        def run(self):
            ret_dict = self.run_screen(_dependency('seedsigner.gui.screens.scan_screens', 'ScanTypeEncryptionKeyScreen'), encryptionkey=self.encryption_key)
            encryption_key = ret_dict['encryptionkey']
            if 'is_back_button' in ret_dict:
                if len(encryption_key) > 0:
                    return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedEncryptedQRTypeEncryptionKeyExitDialogView'), view_args=dict(encryption_key=encryption_key, seed=self.seed), skip_current_view=True)
                else:
                    return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            else:
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedEncryptedQRReviewEncryptionKeyView'), view_args=dict(encryption_key=encryption_key, seed=self.seed), skip_current_view=True)
    return SeedEncryptedQRTypeEncryptionKeyView

def _make_SeedEncryptedQRTypeEncryptionKeyExitDialogView():

    class SeedEncryptedQRTypeEncryptionKeyExitDialogView(_dependency('seedsigner.views.view', 'View')):
        EDIT = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Edit encryption key')
        DISCARD = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Discard encryption key', button_label_color='red')

        def __init__(self, encryption_key, seed):
            super().__init__()
            self.encryption_key = encryption_key
            self.seed = seed

        def run(self):
            button_data = [self.EDIT, self.DISCARD]
            selected_menu_num = self.run_screen(_dependency('seedsigner.gui.screens', 'WarningScreen'), title=_dependency('gettext', 'gettext')('Discard encryption key?'), status_headline=None, text=_dependency('gettext', 'gettext')('Your current key entry will be erased'), show_back_button=False, button_data=button_data)
            if button_data[selected_menu_num] == self.EDIT:
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedEncryptedQRTypeEncryptionKeyView'), view_args=dict(seed=self.seed, encryption_key=self.encryption_key), skip_current_view=True)
            elif button_data[selected_menu_num] == self.DISCARD:
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
    return SeedEncryptedQRTypeEncryptionKeyExitDialogView

def _make_SeedEncryptedQRScanEncryptionKeyView():

    class SeedEncryptedQRScanEncryptionKeyView(_dependency('seedsigner.views.view', 'View')):

        def __init__(self, seed, encryption_key=''):
            super().__init__()
            self.seed = seed
            self.encryption_key = encryption_key

        def run(self):
            decoder = _dependency('seedsigner.models.decode_qr', 'DecodeQR')(is_encryptionkey=True)
            self.run_screen(_dependency('seedsigner.gui.screens.scan_screens', 'ScanScreen'), instructions_text=_dependency('gettext', 'gettext')('Scan encryption key'), decoder=decoder)
            self.controller.reset_screensaver_timeout()
            _dependency('seedsigner_port.clock', None).sleep(0.1)
            if decoder.is_complete:
                self.encryption_key += decoder.get_encryption_key()
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedEncryptedQRReviewEncryptionKeyView'), view_args=dict(encryption_key=self.encryption_key, seed=self.seed), skip_current_view=True)
            elif decoder.is_nonUTF8:
                _dependency('seedsigner.gui.screens', 'DireWarningScreen')(title=_dependency('gettext', 'gettext')('Error!'), show_back_button=False, status_headline=_dependency('gettext', 'gettext')('Invalid Text QR Code'), text=_dependency('gettext', 'gettext')('Non UTF-8 data detected.')).display()
                if isinstance(self.seed, _dependency('seedsigner.models.seed', 'AezeedSeed')):
                    return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedAezeedPassphraseModeView'))
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            else:
                if isinstance(self.seed, _dependency('seedsigner.models.seed', 'AezeedSeed')):
                    return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedAezeedPassphraseModeView'))
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
    return SeedEncryptedQRScanEncryptionKeyView

def _make_SeedEncryptedQRReviewEncryptionKeyView():

    class SeedEncryptedQRReviewEncryptionKeyView(_dependency('seedsigner.views.view', 'View')):

        def __init__(self, encryption_key, seed):
            super().__init__()
            self.encryption_key = encryption_key
            self.seed = seed
            self.mode_name = self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__ENCRYPTION_MODE)

        def run(self):
            if len(self.encryption_key) > 200:
                _dependency('seedsigner.gui.screens', 'WarningScreen')(title=_dependency('gettext', 'gettext')('Error'), show_back_button=False, status_headline=_dependency('gettext', 'gettext')('Invalid Key'), text=_dependency('gettext', 'gettext')('Key length is too long.')).display()
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            PROCEED = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Proceed')
            EDIT = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Edit encryption key')
            SCAN = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Scan & Append Another')
            button_data = [PROCEED, EDIT, SCAN]
            selected_menu_num = self.run_screen(_dependency('seedsigner.gui.screens.scan_screens', 'ScanReviewEncryptionKeyScreen'), encryptionkey=self.encryption_key, button_data=button_data)
            if selected_menu_num == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            elif button_data[selected_menu_num] == PROCEED:
                if self.mode_name in (_dependency('seedsigner.models.settings', 'SettingsConstants').ENCRYPTION_MODE_ECB, _dependency('seedsigner.models.settings', 'SettingsConstants').ENCRYPTION_MODE_ECBV1):
                    return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedEncryptedQRMnemonicIDPromptView'), view_args=dict(encryption_key=self.encryption_key, i_vector=None, seed=self.seed))
                else:
                    return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedEncryptedQRnonECBModeView'), view_args=dict(encryption_key=self.encryption_key, seed=self.seed, mode_name=self.mode_name))
            elif button_data[selected_menu_num] == EDIT:
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedEncryptedQRTypeEncryptionKeyView'), view_args=dict(seed=self.seed, encryption_key=self.encryption_key), skip_current_view=True)
            elif button_data[selected_menu_num] == SCAN:
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedEncryptedQRScanEncryptionKeyView'), view_args=dict(seed=self.seed, encryption_key=self.encryption_key), skip_current_view=True)
    return SeedEncryptedQRReviewEncryptionKeyView

def _make_SeedEncryptedQRnonECBModeView():

    class SeedEncryptedQRnonECBModeView(_dependency('seedsigner.views.view', 'View')):

        def __init__(self, encryption_key, seed, mode_name):
            super().__init__()
            self.encryption_key = encryption_key
            self.seed = seed
            self.mode_name = mode_name

        def run(self):
            CANCEL = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Cancel')
            button_data = [_dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Input from Camera'), CANCEL]
            selected_menu_num = self.run_screen(_dependency('seedsigner.gui.screens', 'ButtonListScreen'), title='Additional Entropy for {0} mode'.format(self.mode_name), button_data=button_data)
            if selected_menu_num == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            elif button_data[selected_menu_num] == CANCEL:
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            self.controller.image_entropy_preview_frames = None
            ret = _dependency('seedsigner.gui.screens.tools_screens', 'ToolsImageEntropyLivePreviewScreen')().display()
            if ret == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            camera = _dependency('seedsigner.hardware.camera', 'Camera').get_instance()
            entropy_image = None
            try:
                camera.start_video_stream_mode()
                _dependency('seedsigner_port.clock', None).sleep(1.0)
                for attempt in range(10):
                    entropy_image = camera.read_video_stream(as_image=True)
                    if entropy_image is not None:
                        break
                    _dependency('seedsigner_port.clock', None).sleep(0.2)
            finally:
                camera.stop_video_stream_mode()
            if entropy_image is None:
                raise Exception('Failed to capture additional entropy image')
            display_version = _dependency('PIL.ImageOps', 'autocontrast')(entropy_image, cutoff=2).crop((120, 0, 600, 480)).resize((self.canvas_width, self.canvas_height), _dependency('PIL', 'Image').BICUBIC)
            ret = _dependency('seedsigner.gui.screens.tools_screens', 'ToolsImageEntropyFinalImageScreen')(final_image=display_version).display()
            if ret == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            entropy_hash = _dependency('hashlib', None).sha256(entropy_image.tobytes()).digest()
            iv_len = _dependency('seedsigner.helpers', 'kef').MODE_IVS.get(_dependency('seedsigner.helpers', 'kef').MODE_NUMBERS[self.mode_name], 0)
            i_vector = entropy_hash[:iv_len]
            return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedEncryptedQRMnemonicIDPromptView'), view_args=dict(encryption_key=self.encryption_key, i_vector=i_vector, seed=self.seed))
    return SeedEncryptedQRnonECBModeView

def _make_SeedEncryptedQRMnemonicIDPromptView():

    class SeedEncryptedQRMnemonicIDPromptView(_dependency('seedsigner.views.view', 'View')):

        def __init__(self, encryption_key, i_vector, seed):
            super().__init__()
            self.encryption_key = encryption_key
            self.i_vector = i_vector
            self.seed = seed
            self.seed = seed

        def run(self):
            DEFAULT = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Use fingerprint')
            CUSTOM_ID = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Assign custom ID')
            button_data = [DEFAULT, CUSTOM_ID]
            selected_menu_num = self.run_screen(_dependency('seedsigner.gui.screens', 'ButtonListScreen'), title=_dependency('gettext', 'gettext')('Input Mnemonic ID'), button_data=button_data)
            if selected_menu_num == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            elif button_data[selected_menu_num] == CUSTOM_ID:
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedEncryptedQRMnemonicIDEntryView'), view_args=dict(encryption_key=self.encryption_key, i_vector=self.i_vector, seed=self.seed))
            elif button_data[selected_menu_num] == DEFAULT:
                mnemonic_id = self.seed.get_fingerprint(network=self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__NETWORK))
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedEncryptedQRReviewMnemonicIDView'), view_args=dict(encryption_key=self.encryption_key, i_vector=self.i_vector, mnemonic_id=mnemonic_id, seed=self.seed))
    return SeedEncryptedQRMnemonicIDPromptView

def _make_SeedEncryptedQRMnemonicIDEntryView():

    class SeedEncryptedQRMnemonicIDEntryView(_dependency('seedsigner.views.view', 'View')):

        def __init__(self, encryption_key, i_vector, seed, custom_id=''):
            super().__init__()
            self.encryption_key = encryption_key
            self.i_vector = i_vector
            self.seed = seed
            self.custom_id = custom_id

        def run(self):
            ret_dict = self.run_screen(_dependency('seedsigner.gui.screens.seed_screens', 'SeedEncryptedQRMnemonicIDScreen'), mnemonic_id=self.custom_id)
            mnemonic_id = ret_dict['mnemonic_id']
            if 'is_back_button' in ret_dict:
                if len(mnemonic_id) > 0:
                    return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedEncryptedQRMnemonicIDEntryExitDialogView'), view_args=dict(encryption_key=self.encryption_key, i_vector=self.i_vector, mnemonic_id=mnemonic_id, seed=self.seed), skip_current_view=True)
                else:
                    return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            else:
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedEncryptedQRReviewMnemonicIDView'), view_args=dict(encryption_key=self.encryption_key, i_vector=self.i_vector, mnemonic_id=mnemonic_id, seed=self.seed), skip_current_view=True)
    return SeedEncryptedQRMnemonicIDEntryView

def _make_SeedEncryptedQRMnemonicIDEntryExitDialogView():

    class SeedEncryptedQRMnemonicIDEntryExitDialogView(_dependency('seedsigner.views.view', 'View')):
        EDIT = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Edit mnemonic ID')
        DISCARD = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Discard mnemonic ID', button_label_color='red')

        def __init__(self, encryption_key, i_vector, mnemonic_id, seed):
            super().__init__()
            self.encryption_key = encryption_key
            self.i_vector = i_vector
            self.mnemonic_id = mnemonic_id
            self.seed = seed

        def run(self):
            button_data = [self.EDIT, self.DISCARD]
            selected_menu_num = self.run_screen(_dependency('seedsigner.gui.screens', 'WarningScreen'), title=_dependency('gettext', 'gettext')('Discard mnemonic ID?'), status_headline=None, text=_dependency('gettext', 'gettext')('Your current mnemonic ID entry will be erased'), show_back_button=False, button_data=button_data)
            if button_data[selected_menu_num] == self.EDIT:
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedEncryptedQRMnemonicIDEntryView'), view_args=dict(encryption_key=self.encryption_key, i_vector=self.i_vector, seed=self.seed, custom_id=self.mnemonic_id), skip_current_view=True)
            elif button_data[selected_menu_num] == self.DISCARD:
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
    return SeedEncryptedQRMnemonicIDEntryExitDialogView

def _make_SeedEncryptedQRReviewMnemonicIDView():

    class SeedEncryptedQRReviewMnemonicIDView(_dependency('seedsigner.views.view', 'View')):

        def __init__(self, encryption_key, i_vector, mnemonic_id, seed):
            super().__init__()
            self.encryption_key = encryption_key
            self.i_vector = i_vector
            self.mnemonic_id = mnemonic_id
            self.seed = seed
            self.seed = seed

        def run(self):
            PROCEED = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Proceed')
            EDIT = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Edit mnemonic ID')
            button_data = [PROCEED, EDIT]
            selected_menu_num = self.run_screen(_dependency('seedsigner.gui.screens.seed_screens', 'SeedEncryptedQRReviewMnemonicIDScreen'), mnemonic_id=self.mnemonic_id, button_data=button_data)
            if selected_menu_num == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            elif button_data[selected_menu_num] == EDIT:
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedEncryptedQRMnemonicIDEntryView'), view_args=dict(encryption_key=self.encryption_key, i_vector=self.i_vector, seed=self.seed, custom_id=self.mnemonic_id), skip_current_view=True)
            elif button_data[selected_menu_num] == PROCEED:
                loading_screen = _dependency('seedsigner.gui.screens.screen', 'LoadingScreenThread')(text=_dependency('gettext', 'gettext')('Processing...'))
                loading_screen.start()
                try:
                    encrypted_qr = _dependency('seedsigner.models.encryption', 'EncryptedQRCode')()
                    encrypted_qr.add_delta()
                    qr_data = encrypted_qr.create(key=self.encryption_key, mnemonic_id=self.mnemonic_id, mnemonic=self.seed.mnemonic_str, i_vector=self.i_vector)
                    version_number = encrypted_qr.version
                    del encrypted_qr
                    if version_number > 1:
                        qr_data = _dependency('seedsigner.helpers.base43', 'base43_encode')(qr_data)
                    if not qr_data:
                        _dependency('seedsigner.gui.screens', 'WarningScreen')(title=_dependency('gettext', 'gettext')('Error'), show_back_button=False, status_headline=_dependency('gettext', 'gettext')('Encryption failure'), text='').display()
                        return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
                finally:
                    loading_screen.stop()
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedEncryptedQRTranscribeModePromptView'), view_args=dict(data=qr_data, seed=self.seed))
    return SeedEncryptedQRReviewMnemonicIDView

def _make_SeedEncryptedQRTranscribeModePromptView():

    class SeedEncryptedQRTranscribeModePromptView(_dependency('seedsigner.views.view', 'View')):

        def __init__(self, data, seed):
            super().__init__()
            self.data = data
            self.seed = seed

        def run(self):
            num_modules = _dependency('seedsigner.helpers.qr', 'QR')().qrsize(data=self.data)
            if num_modules <= 33:
                TRANSCRIBE = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Transcribe mode')
                FULLSCREEN = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('FullScreen mode')
                button_data = [TRANSCRIBE, FULLSCREEN]
                selected_menu_num = self.run_screen(_dependency('seedsigner.gui.screens', 'seed_screens').SeedEncryptedQRTranscribeModePromptScreen, title=_dependency('gettext', 'gettext')('Transcribe Mode ?'), is_button_text_centered=False, button_data=button_data)
                if selected_menu_num == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                    return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
                elif button_data[selected_menu_num] == TRANSCRIBE:
                    return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedEncryptedQRTranscribeModeView'), view_args=dict(data=self.data, num_modules=num_modules, seed=self.seed))
            return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedEncryptedQRFullScreenModeView'), view_args=dict(data=self.data, seed=self.seed))
    return SeedEncryptedQRTranscribeModePromptView

def _make_SeedEncryptedQRTranscribeModeView():

    class SeedEncryptedQRTranscribeModeView(_dependency('seedsigner.views.view', 'View')):

        def __init__(self, data, num_modules, seed):
            super().__init__()
            self.data = data
            self.num_modules = num_modules
            self.seed = seed

        def run(self):
            ret = _dependency('seedsigner.gui.screens', 'seed_screens').SeedTranscribeEncryptedQRWholeQRScreen(qr_data=self.data, num_modules=self.num_modules).display()
            if ret == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            else:
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedTranscribeEncryptedQRZoomedInView'), view_args=dict(data=self.data, num_modules=self.num_modules, seed=self.seed))
    return SeedEncryptedQRTranscribeModeView

def _make_SeedTranscribeEncryptedQRZoomedInView():

    class SeedTranscribeEncryptedQRZoomedInView(_dependency('seedsigner.views.view', 'View')):

        def __init__(self, data, num_modules, seed):
            super().__init__()
            self.data = data
            self.num_modules = num_modules
            self.seed = seed

        def run(self):
            _dependency('seedsigner.gui.screens', 'seed_screens').SeedTranscribeEncryptedQRZoomedInScreen(qr_data=self.data, num_modules=self.num_modules).display()
            return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedOptionsView'), view_args=dict(seed=self.seed), clear_history=True)
    return SeedTranscribeEncryptedQRZoomedInView

def _make_SeedEncryptedQRFullScreenModeView():

    class SeedEncryptedQRFullScreenModeView(_dependency('seedsigner.views.view', 'View')):

        def __init__(self, data, seed):
            super().__init__()
            self.data = data
            self.seed = seed

        def run(self):
            encoder_args = dict(data=self.data)
            e = _dependency('seedsigner.models.encode_qr', 'GenericStaticQrEncoder')(**encoder_args)
            _dependency('seedsigner.gui.screens.screen', 'QRDisplayScreen')(qr_encoder=e).display()
            return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedOptionsView'), view_args=dict(seed=self.seed), clear_history=True)
    return SeedEncryptedQRFullScreenModeView

def _make_SeedTranscribeSeedQRZoomedInView():

    class SeedTranscribeSeedQRZoomedInView(_dependency('seedsigner.views.view', 'View')):
        """
    intial_zone_x, initial_zone_y: Used by the screenshot generator to shift the view
    to a more interesting part of the QR code template.
    """

        def __init__(self, seed, seedqr_format, initial_zone_x=0, initial_zone_y=0):
            super().__init__()
            self.seed = seed
            self.seedqr_format = seedqr_format
            self.seed = seed
            self.initial_zone_x = initial_zone_x
            self.initial_zone_y = initial_zone_y
            self.is_screensaver_allowed = False

        def run(self):
            encoder_args = dict(mnemonic=self.seed.mnemonic_list, wordlist_language_code=self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__WORDLIST_LANGUAGE))
            if self.seedqr_format == _dependency('seedsigner.models.qr_type', 'QRType').SEED__SEEDQR:
                e = _dependency('seedsigner.models.encode_qr', 'SeedQrEncoder')(**encoder_args)
            elif self.seedqr_format == _dependency('seedsigner.models.qr_type', 'QRType').SEED__COMPACTSEEDQR:
                e = _dependency('seedsigner.models.encode_qr', 'CompactSeedQrEncoder')(**encoder_args)
            data = e.next_part()
            num_modules = _dependency('seedsigner.helpers.qr', 'QR')().qrsize(data)
            self.run_screen(_dependency('seedsigner.gui.screens', 'seed_screens').SeedTranscribeSeedQRZoomedInScreen, qr_data=data, num_modules=num_modules, initial_zone_x=self.initial_zone_x, initial_zone_y=self.initial_zone_y)
            return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedTranscribeSeedQRConfirmQRPromptView'), view_args={'seed': self.seed})
    return SeedTranscribeSeedQRZoomedInView

def _make_SeedTranscribeSeedQRConfirmQRPromptView():

    class SeedTranscribeSeedQRConfirmQRPromptView(_dependency('seedsigner.views.view', 'View')):
        SCAN = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Confirm SeedQR', _dependency('seedsigner.gui.components', 'SeedSignerIconConstants').QRCODE)
        DONE = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Done')

        def __init__(self, seed):
            super().__init__()
            self.seed = seed
            self.seed = seed

        def run(self):
            button_data = [self.SCAN, self.DONE]
            selected_menu_option = self.run_screen(_dependency('seedsigner.gui.screens', 'seed_screens').SeedTranscribeSeedQRConfirmQRPromptScreen, title=_dependency('gettext', 'gettext')('Confirm SeedQR?'), button_data=button_data)
            if selected_menu_option == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            elif button_data[selected_menu_option] == self.SCAN:
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedTranscribeSeedQRConfirmScanView'), view_args={'seed': self.seed})
            elif button_data[selected_menu_option] == self.DONE:
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedOptionsView'), view_args={'seed': self.seed}, clear_history=True)
    return SeedTranscribeSeedQRConfirmQRPromptView

def _make_SeedTranscribeSeedQRConfirmScanView():

    class SeedTranscribeSeedQRConfirmScanView(_dependency('seedsigner.views.view', 'View')):

        def __init__(self, seed):
            super().__init__()
            self.seed = seed
            self.seed = seed
            wordlist_language_code = self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__WORDLIST_LANGUAGE)
            self.decoder = _dependency('seedsigner.models.decode_qr', 'DecodeQR')(wordlist_language_code=wordlist_language_code)

        def run(self):
            scanning_done = self.run_screen(_dependency('seedsigner.gui.screens.scan_screens', 'ScanScreen'), decoder=self.decoder, instructions_text=_dependency('gettext', 'gettext')('Scan your SeedQR'))
            if scanning_done == False:
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'), skip_current_view=False)
            if self.decoder.is_complete:
                if self.decoder.is_seed:
                    seed_mnemonic = self.decoder.get_seed_phrase()
                    if seed_mnemonic != self.seed.mnemonic_list:
                        return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedTranscribeSeedQRConfirmWrongSeedView'), skip_current_view=True)
                    else:
                        return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedTranscribeSeedQRConfirmSuccessView'), view_args={'seed': self.seed})
            return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedTranscribeSeedQRConfirmInvalidQRView'), skip_current_view=True)
    return SeedTranscribeSeedQRConfirmScanView

def _make_SeedTranscribeSeedQRConfirmWrongSeedView():

    class SeedTranscribeSeedQRConfirmWrongSeedView(_dependency('seedsigner.views.view', 'View')):
        """
    A valid SeedQR was scanned but it did NOT match the one we just transcribed!
    """

        def run(self):
            self.run_screen(_dependency('seedsigner.gui.screens', 'DireWarningScreen'), title=_dependency('gettext', 'gettext')('Confirm SeedQR'), status_headline=_dependency('gettext', 'gettext')('Error!'), text=_dependency('gettext', 'gettext')('Your transcribed SeedQR does not match your original seed!'), show_back_button=False, button_data=[_dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Review SeedQR')])
            return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'), skip_current_view=True)
    return SeedTranscribeSeedQRConfirmWrongSeedView

def _make_SeedTranscribeSeedQRConfirmInvalidQRView():

    class SeedTranscribeSeedQRConfirmInvalidQRView(_dependency('seedsigner.views.view', 'View')):
        """
    A QR code was scanned but it was not a SeedQR and certainly not the SeedQR we just
    transcribed!
    """

        def run(self):
            self.run_screen(_dependency('seedsigner.gui.screens', 'DireWarningScreen'), title=_dependency('gettext', 'gettext')('Confirm SeedQR'), status_headline=_dependency('gettext', 'gettext')('Error!'), text=_dependency('gettext', 'gettext')('Your transcribed SeedQR could not be read!'), show_back_button=False, button_data=[_dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Review SeedQR')])
            return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'), skip_current_view=True)
    return SeedTranscribeSeedQRConfirmInvalidQRView

def _make_SeedTranscribeSeedQRConfirmSuccessView():

    class SeedTranscribeSeedQRConfirmSuccessView(_dependency('seedsigner.views.view', 'View')):
        """
    The SeedQR we just scanned matched the one we just transcribed.
    """

        def __init__(self, seed):
            super().__init__()
            self.seed = seed

        def run(self):
            self.run_screen(_dependency('seedsigner.gui.screens.screen', 'LargeIconStatusScreen'), title=_dependency('gettext', 'gettext')('Confirm SeedQR'), status_headline=_dependency('gettext', 'gettext')('Success!'), text=_dependency('gettext', 'gettext')('Your transcribed SeedQR successfully scanned and yielded the same seed.'), show_back_button=False, button_data=[_dependency('seedsigner.gui.screens.screen', 'ButtonOption')('OK')])
            return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedOptionsView'), view_args={'seed': self.seed})
    return SeedTranscribeSeedQRConfirmSuccessView

def _make_AddressVerificationStartView():

    class AddressVerificationStartView(_dependency('seedsigner.views.view', 'View')):

        def __init__(self, address, script_type, network):
            super().__init__()
            self.controller.unverified_address = dict(address=address, script_type=script_type, network=network)

        def run(self):
            pass
            if self.controller.unverified_address['script_type'] == _dependency('seedsigner.models.settings', 'SettingsConstants').LEGACY_P2PKH:
                sig_type = _dependency('seedsigner.models.settings', 'SettingsConstants').SINGLE_SIG
                destination = _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedSelectSeedView'), view_args=dict(flow=_dependency('seedsigner.controller', 'Controller').FLOW__VERIFY_SINGLESIG_ADDR), skip_current_view=True)
            if self.controller.unverified_address['script_type'] == _dependency('seedsigner.models.settings', 'SettingsConstants').NESTED_SEGWIT:
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('AddressVerificationSigTypeView'), skip_current_view=True)
            if self.controller.unverified_address['script_type'] == _dependency('seedsigner.models.settings', 'SettingsConstants').NATIVE_SEGWIT:
                if len(self.controller.unverified_address['address']) >= 62:
                    sig_type = _dependency('seedsigner.models.settings', 'SettingsConstants').MULTISIG
                    if self.controller.multisig_wallet_descriptor:
                        destination = _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedAddressVerificationView'), skip_current_view=True)
                    else:
                        self.controller.resume_main_flow = _dependency('seedsigner.controller', 'Controller').FLOW__VERIFY_MULTISIG_ADDR
                        destination = _dependency('seedsigner_port.navigation', 'Destination')(_resolve('LoadMultisigWalletDescriptorView'), skip_current_view=True)
                else:
                    sig_type = _dependency('seedsigner.models.settings', 'SettingsConstants').SINGLE_SIG
                    destination = _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedSelectSeedView'), view_args=dict(flow=_dependency('seedsigner.controller', 'Controller').FLOW__VERIFY_SINGLESIG_ADDR), skip_current_view=True)
            elif self.controller.unverified_address['script_type'] == _dependency('seedsigner.models.settings', 'SettingsConstants').TAPROOT:
                sig_type = _dependency('seedsigner.models.settings', 'SettingsConstants').SINGLE_SIG
                destination = _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedSelectSeedView'), view_args=dict(flow=_dependency('seedsigner.controller', 'Controller').FLOW__VERIFY_SINGLESIG_ADDR), skip_current_view=True)
            derivation_path = _dependency('seedsigner.helpers', 'embit_utils').get_standard_derivation_path(network=self.controller.unverified_address['network'], wallet_type=sig_type, script_type=self.controller.unverified_address['script_type'])
            self.controller.unverified_address['sig_type'] = sig_type
            self.controller.unverified_address['derivation_path'] = derivation_path
            return destination
    return AddressVerificationStartView

def _make_AddressVerificationSigTypeView():

    class AddressVerificationSigTypeView(_dependency('seedsigner.views.view', 'View')):
        SINGLE_SIG = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Single Sig')
        MULTISIG = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Multisig')

        def run(self):
            button_data = [self.SINGLE_SIG, self.MULTISIG]
            selected_menu_num = self.run_screen(_dependency('seedsigner.gui.screens', 'seed_screens').AddressVerificationSigTypeScreen, title=_dependency('gettext', 'gettext')('Verify Address'), text=_dependency('gettext', 'gettext')("Sig type can't be auto-detected from this address. Please specify:"), button_data=button_data, is_bottom_list=True)
            if selected_menu_num == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                self.controller.unverified_address = None
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            elif button_data[selected_menu_num] == self.SINGLE_SIG:
                sig_type = _dependency('seedsigner.models.settings', 'SettingsConstants').SINGLE_SIG
                destination = _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedSelectSeedView'), view_args=dict(flow=_dependency('seedsigner.controller', 'Controller').FLOW__VERIFY_SINGLESIG_ADDR))
            elif button_data[selected_menu_num] == self.MULTISIG:
                sig_type = _dependency('seedsigner.models.settings', 'SettingsConstants').MULTISIG
                if self.controller.multisig_wallet_descriptor:
                    destination = _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedAddressVerificationView'))
                else:
                    self.controller.resume_main_flow = _dependency('seedsigner.controller', 'Controller').FLOW__VERIFY_MULTISIG_ADDR
                    destination = _dependency('seedsigner_port.navigation', 'Destination')(_resolve('LoadMultisigWalletDescriptorView'))
            self.controller.unverified_address['sig_type'] = sig_type
            derivation_path = _dependency('seedsigner.helpers', 'embit_utils').get_standard_derivation_path(network=self.controller.unverified_address['network'], wallet_type=sig_type, script_type=self.controller.unverified_address['script_type'])
            self.controller.unverified_address['derivation_path'] = derivation_path
            return destination
    return AddressVerificationSigTypeView

def _make_SeedAddressVerificationView():

    class SeedAddressVerificationView(_dependency('seedsigner.views.view', 'View')):
        """
        Creates a worker thread to brute-force calculate addresses. Writes its
        iteration status to a shared `ThreadsafeCounter`.

        The `ThreadsafeCounter` is sent to the display Screen which is monitored in
        its own `ProgressThread` to show the current iteration onscreen.

        Performs single sig verification on `seed` if specified, otherwise assumes
        multisig.

        For singlesig with a seed, first searches the detected derivation path in
        batches of SIMPLE_SEARCH_BATCH_SIZE addresses (fast, handles the common
        case).  If not found, the user is prompted to continue, run an expanded
        search across all paths/script-types, or cancel.
    """
        SKIP_10 = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Skip 10')
        CANCEL = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Cancel')
        MAX_ITERATIONS_EXPORT_XPUB = 1000
        EXPANDED_ADDRS_PER_PATH = 10
        SIMPLE_SEARCH_BATCH_SIZE = 100

        def __init__(self, seed=None, export_for_xpub=False, expanded_start_index=0, use_expanded=False, simple_start_index=0):
            super().__init__()
            self.seed = seed
            self.expanded_start_index = expanded_start_index
            self.simple_start_index = simple_start_index
            self.export_for_xpub = export_for_xpub
            self.is_multisig = self.controller.unverified_address['sig_type'] == _dependency('seedsigner.models.settings', 'SettingsConstants').MULTISIG
            self.seed_derivation_override = ''
            if not self.is_multisig:
                if seed is not None:
                    self.seed = seed
                    self.seed_derivation_override = self.seed.derivation_override(sig_type=_dependency('seedsigner.models.settings', 'SettingsConstants').SINGLE_SIG)
                else:
                    self.seed = None
            else:
                self.seed = None
            self.address = self.controller.unverified_address['address']
            self.derivation_path = self.seed_derivation_override if self.seed_derivation_override else self.controller.unverified_address['derivation_path']
            self.script_type = self.controller.unverified_address['script_type']
            self.sig_type = self.controller.unverified_address['sig_type']
            self.network = self.controller.unverified_address['network']
            embit_network = _dependency('seedsigner.models.settings', 'SettingsConstants').map_network_to_embit(self.network)
            self.is_expanded = use_expanded and self.seed is not None and (not self.is_multisig) and (not self.export_for_xpub)
            self.is_singlesig_simple = self.seed is not None and (not self.is_multisig) and (not self.export_for_xpub) and (not self.is_expanded)
            if self.is_singlesig_simple:
                self.threadsafe_counter = _dependency('seedsigner.models.threads', 'ThreadsafeCounter')(initial_value=simple_start_index)
            else:
                self.threadsafe_counter = _dependency('seedsigner.models.threads', 'ThreadsafeCounter')()
            self.verified_index = _dependency('seedsigner.models.threads', 'ThreadsafeCounter')(initial_value=None)
            self.verified_index_is_change = _dependency('seedsigner.models.threads', 'ThreadsafeCounter')(initial_value=None)
            pass
            pass
            self.display_index_counter = None
            if self.is_expanded:
                derivation_paths = _dependency('seedsigner.helpers', 'embit_utils').get_expanded_search_derivation_paths(network=self.network)
                self.display_index_counter = _dependency('seedsigner.models.threads', 'ThreadsafeCounter')(initial_value=self.expanded_start_index)
                self.addr_verification_thread = self.ExpandedBruteForceAddressVerificationThread(address=self.address, seed=self.seed, embit_network=embit_network, network=self.network, derivation_paths=derivation_paths, addrs_per_path=self.EXPANDED_ADDRS_PER_PATH, start_index=self.expanded_start_index, threadsafe_counter=self.threadsafe_counter, verified_index=self.verified_index, verified_index_is_change=self.verified_index_is_change, address_index_counter=self.display_index_counter)
            else:
                self.addr_verification_thread = self.BruteForceAddressVerificationThread(address=self.address, seed=self.seed, descriptor=self.controller.multisig_wallet_descriptor, script_type=self.script_type, embit_network=embit_network, derivation_path=self.derivation_path, threadsafe_counter=self.threadsafe_counter, verified_index=self.verified_index, verified_index_is_change=self.verified_index_is_change)

        def run(self):
            try:
                pass
                self.addr_verification_thread.start()
                if self.is_expanded:
                    button_data = [self.CANCEL]
                else:
                    button_data = [self.SKIP_10, self.CANCEL]
                script_type_settings_entry = _dependency('seedsigner.models.settings_definition', 'SettingsDefinition').get_settings_entry(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__SCRIPT_TYPES)
                script_type_display = script_type_settings_entry.get_selection_option_display_name_by_value(self.script_type)
                sig_type_settings_entry = _dependency('seedsigner.models.settings_definition', 'SettingsDefinition').get_settings_entry(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__SIG_TYPES)
                sig_type_display = sig_type_settings_entry.get_selection_option_display_name_by_value(self.sig_type)
                network_settings_entry = _dependency('seedsigner.models.settings_definition', 'SettingsDefinition').get_settings_entry(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__NETWORK)
                network_display = network_settings_entry.get_selection_option_display_name_by_value(self.network)
                mainnet = network_settings_entry.get_selection_option_display_name_by_value(_dependency('seedsigner.models.settings', 'SettingsConstants').MAINNET)
                if self.export_for_xpub:
                    max_iterations = self.MAX_ITERATIONS_EXPORT_XPUB
                elif self.is_expanded:
                    num_paths = len(_dependency('seedsigner.helpers', 'embit_utils').get_expanded_search_derivation_paths(network=self.network))
                    num_script_types = len(self.ExpandedBruteForceAddressVerificationThread.SCRIPT_TYPES)
                    max_iterations = num_paths * self.EXPANDED_ADDRS_PER_PATH * num_script_types
                elif self.is_singlesig_simple:
                    max_iterations = self.simple_start_index + self.SIMPLE_SEARCH_BATCH_SIZE
                else:
                    max_iterations = None
                pass
                while True:
                    selected_menu_num = self.run_screen(_dependency('seedsigner.gui.screens', 'seed_screens').SeedAddressVerificationScreen, address=self.address, derivation_path=self.derivation_path, script_type=script_type_display, sig_type=sig_type_display, network=network_display, is_mainnet=network_display == mainnet, threadsafe_counter=self.threadsafe_counter, verified_index=self.verified_index, button_data=button_data, max_iterations=max_iterations, display_index_counter=self.display_index_counter)
                    if self.verified_index.cur_count is not None:
                        break
                    if selected_menu_num == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                        break
                    if selected_menu_num is None:
                        _dependency('seedsigner_port.clock', None).sleep(0.1)
                    elif button_data[selected_menu_num] == self.SKIP_10:
                        self.threadsafe_counter.increment(10)
                    elif button_data[selected_menu_num] == self.CANCEL:
                        break
                    if max_iterations is not None and self.threadsafe_counter.cur_count >= max_iterations:
                        break
                if self.verified_index.cur_count is not None:
                    self.controller.unverified_address['verified_index'] = self.verified_index.cur_count
                    self.controller.unverified_address['verified_index_is_change'] = self.verified_index_is_change.cur_count == 1
                    if self.is_expanded and self.addr_verification_thread.matched_derivation_path:
                        self.controller.unverified_address['derivation_path'] = self.addr_verification_thread.matched_derivation_path
                    if self.is_expanded and self.addr_verification_thread.matched_script_type:
                        self.controller.unverified_address['script_type'] = self.addr_verification_thread.matched_script_type
                    if self.export_for_xpub:
                        return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedExportXpubVerificationSuccessView'))
                    return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedAddressVerificationSuccessView'), view_args=dict(seed=self.seed))
                if self.export_for_xpub and max_iterations is not None and (self.threadsafe_counter.cur_count >= max_iterations):
                    return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedExportXpubVerificationFailedView'), view_args=dict(reason='no_match'))
                if self.is_singlesig_simple and max_iterations is not None and (self.threadsafe_counter.cur_count >= max_iterations):
                    return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedAddressVerificationSimpleNotFoundView'), view_args=dict(seed=self.seed, addrs_checked=self.threadsafe_counter.cur_count, next_start_index=self.threadsafe_counter.cur_count))
                if self.is_expanded and max_iterations is not None and (self.threadsafe_counter.cur_count >= max_iterations):
                    next_start = self.expanded_start_index + self.EXPANDED_ADDRS_PER_PATH
                    return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedAddressVerificationNotFoundView'), view_args=dict(seed=self.seed, addrs_per_path_checked=next_start, next_start_index=next_start))
            finally:
                self.addr_verification_thread.stop()
                while self.addr_verification_thread.is_alive():
                    _dependency('seedsigner_port.clock', None).sleep(0.01)
            return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'MainMenuView'))

        class BruteForceAddressVerificationThread(_dependency('seedsigner.models.threads', 'BaseThread')):

            def __init__(self, address, seed, descriptor, script_type, embit_network, derivation_path, threadsafe_counter, verified_index, verified_index_is_change):
                """
                Either seed or descriptor will be None
            """
                super().__init__()
                self.address = address
                self.seed = seed
                self.descriptor = descriptor
                self.script_type = script_type
                self.embit_network = embit_network
                self.derivation_path = derivation_path
                self.threadsafe_counter = threadsafe_counter
                self.verified_index = verified_index
                self.verified_index_is_change = verified_index_is_change
                if self.seed:
                    self.xpub = self.seed.get_xpub(wallet_path=self.derivation_path, network=_dependency('seedsigner.models.settings', 'Settings').get_instance().get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__NETWORK))

            def run(self):
                while self.keep_running:
                    if self.threadsafe_counter.cur_count % 10 == 0:
                        pass
                    i = self.threadsafe_counter.cur_count
                    if self.descriptor:
                        receive_address = _dependency('seedsigner.helpers', 'embit_utils').get_multisig_address(descriptor=self.descriptor, index=i, is_change=False, embit_network=self.embit_network)
                        change_address = _dependency('seedsigner.helpers', 'embit_utils').get_multisig_address(descriptor=self.descriptor, index=i, is_change=True, embit_network=self.embit_network)
                    else:
                        receive_address = _dependency('seedsigner.helpers', 'embit_utils').get_single_sig_address(xpub=self.xpub, script_type=self.script_type, index=i, is_change=False, embit_network=self.embit_network)
                        change_address = _dependency('seedsigner.helpers', 'embit_utils').get_single_sig_address(xpub=self.xpub, script_type=self.script_type, index=i, is_change=True, embit_network=self.embit_network)
                    if self.address == receive_address:
                        self.verified_index.set_value(i)
                        self.verified_index_is_change.set_value(0)
                        self.keep_running = False
                        break
                    elif self.address == change_address:
                        self.verified_index.set_value(i)
                        self.verified_index_is_change.set_value(1)
                        self.keep_running = False
                        break
                    self.threadsafe_counter.increment()

        class ExpandedBruteForceAddressVerificationThread(_dependency('seedsigner.models.threads', 'BaseThread')):
            """
            Recovery-oriented search that tries ALL supported script types for
            every derivation path (BIP44/49/84/86 × accounts 0-9 plus
            non-standard wallet paths).  This catches addresses produced by
            any script-type / derivation-path combination, even non-standard
            ones, regardless of which script types are enabled in Settings.
        """
            SCRIPT_TYPES = [_dependency('seedsigner.models.settings', 'SettingsConstants').NATIVE_SEGWIT, _dependency('seedsigner.models.settings', 'SettingsConstants').NESTED_SEGWIT, _dependency('seedsigner.models.settings', 'SettingsConstants').LEGACY_P2PKH, _dependency('seedsigner.models.settings', 'SettingsConstants').TAPROOT]

            def __init__(self, address, seed, embit_network, network, derivation_paths, addrs_per_path, start_index, threadsafe_counter, verified_index, verified_index_is_change, address_index_counter=None):
                super().__init__()
                self.address = address
                self.seed = seed
                self.embit_network = embit_network
                self.network = network
                self.derivation_paths = derivation_paths
                self.addrs_per_path = addrs_per_path
                self.start_index = start_index
                self.threadsafe_counter = threadsafe_counter
                self.verified_index = verified_index
                self.verified_index_is_change = verified_index_is_change
                self.address_index_counter = address_index_counter
                self.matched_derivation_path = None
                self.matched_script_type = None

            def run(self):
                pass
                pass
                pass
                pass
                xpubs = {}
                skipped_paths = set()
                for path in self.derivation_paths:
                    if not self.keep_running:
                        return
                    try:
                        xpubs[path] = self.seed.get_xpub(wallet_path=path, network=self.network)
                    except FeatureUnavailable:
                        raise
                    except Exception as e:
                        pass
                        skipped_paths.add(path)
                total_addrs_checked = 0
                for i in range(self.start_index, self.start_index + self.addrs_per_path):
                    if self.address_index_counter:
                        self.address_index_counter.set_value(i)
                    for path in self.derivation_paths:
                        if not self.keep_running:
                            pass
                            return
                        if path in skipped_paths:
                            self.threadsafe_counter.increment(len(self.SCRIPT_TYPES))
                            continue
                        xpub = xpubs[path]
                        for script_type in self.SCRIPT_TYPES:
                            if not self.keep_running:
                                pass
                                return
                            receive_address = _dependency('seedsigner.helpers', 'embit_utils').get_single_sig_address(xpub=xpub, script_type=script_type, index=i, is_change=False, embit_network=self.embit_network)
                            change_address = _dependency('seedsigner.helpers', 'embit_utils').get_single_sig_address(xpub=xpub, script_type=script_type, index=i, is_change=True, embit_network=self.embit_network)
                            total_addrs_checked += 1
                            if self.address == receive_address:
                                pass
                                pass
                                self.matched_derivation_path = path
                                self.matched_script_type = script_type
                                self.verified_index.set_value(i)
                                self.verified_index_is_change.set_value(0)
                                self.keep_running = False
                                return
                            elif self.address == change_address:
                                pass
                                pass
                                self.matched_derivation_path = path
                                self.matched_script_type = script_type
                                self.verified_index.set_value(i)
                                self.verified_index_is_change.set_value(1)
                                self.keep_running = False
                                return
                            self.threadsafe_counter.increment()
                pass
                pass
    return SeedAddressVerificationView

def _make_SeedAddressVerificationSuccessView():

    class SeedAddressVerificationSuccessView(_dependency('seedsigner.views.view', 'View')):

        def __init__(self, seed):
            super().__init__()
            self.seed = seed
            if self.seed is not None:
                self.seed = seed

        def run(self):
            derivation_path = self.controller.unverified_address.get('derivation_path')
            script_type = self.controller.unverified_address.get('script_type')
            network = self.controller.unverified_address.get('network')
            is_non_standard = False
            if derivation_path and script_type and network:
                is_non_standard = not _dependency('seedsigner.helpers', 'embit_utils').is_standard_derivation(derivation_path=derivation_path, script_type=script_type, network=network)
            script_type_settings_entry = _dependency('seedsigner.models.settings_definition', 'SettingsDefinition').get_settings_entry(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__SCRIPT_TYPES)
            script_type_display = script_type_settings_entry.get_selection_option_display_name_by_value(script_type) if script_type else None
            self.run_screen(_dependency('seedsigner.gui.screens', 'seed_screens').SeedAddressVerificationSuccessScreen, address=self.controller.unverified_address['address'], verified_index=self.controller.unverified_address['verified_index'], verified_index_is_change=self.controller.unverified_address['verified_index_is_change'], derivation_path=derivation_path, script_type_display=script_type_display, is_non_standard=is_non_standard)
            return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'MainMenuView'))
    return SeedAddressVerificationSuccessView

def _make_SeedAddressVerificationSimpleNotFoundView():

    class SeedAddressVerificationSimpleNotFoundView(_dependency('seedsigner.views.view', 'View')):
        """Shown when the simple (single path/type) search runs out of addresses.
    Offers: Next 100 (continue simple), Expanded Search, Cancel."""
        NEXT_100 = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Next 100')
        EXPANDED_SEARCH = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Expanded Search')
        CANCEL = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Cancel')

        def __init__(self, seed, addrs_checked, next_start_index):
            super().__init__()
            self.seed = seed
            self.addrs_checked = addrs_checked
            self.next_start_index = next_start_index

        def run(self):
            button_data = [self.NEXT_100, self.EXPANDED_SEARCH, self.CANCEL]
            selected_menu_num = self.run_screen(_dependency('seedsigner.gui.screens.screen', 'WarningScreen'), title=_dependency('gettext', 'gettext')('Not Found'), status_headline=_dependency('gettext', 'gettext')('Address Not Verified'), text=_dependency('gettext', 'gettext')('Checked {} addresses with no match.').format(self.addrs_checked), button_data=button_data, show_back_button=False)
            if selected_menu_num == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON') or button_data[selected_menu_num] == self.CANCEL:
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'MainMenuView'))
            if button_data[selected_menu_num] == self.NEXT_100:
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedAddressVerificationView'), view_args=dict(seed=self.seed, simple_start_index=self.next_start_index))
            return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedAddressVerificationView'), view_args=dict(seed=self.seed, use_expanded=True))
    return SeedAddressVerificationSimpleNotFoundView

def _make_SeedAddressVerificationNotFoundView():

    class SeedAddressVerificationNotFoundView(_dependency('seedsigner.views.view', 'View')):
        """Shown when the expanded address search completes without finding a match.
    Offers the user a chance to search the next batch of addresses."""
        CHECK_NEXT = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Check Next 10')
        DONE = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Done')

        def __init__(self, seed, addrs_per_path_checked, next_start_index):
            super().__init__()
            self.seed = seed
            self.addrs_per_path_checked = addrs_per_path_checked
            self.next_start_index = next_start_index

        def run(self):
            button_data = [self.CHECK_NEXT, self.DONE]
            selected_menu_num = self.run_screen(_dependency('seedsigner.gui.screens.screen', 'WarningScreen'), title=_dependency('gettext', 'gettext')('Not Found'), status_headline=_dependency('gettext', 'gettext')('Address Not Verified'), text=_dependency('gettext', 'gettext')('Checked {} addresses per path with no match.').format(self.addrs_per_path_checked), button_data=button_data, show_back_button=False)
            if selected_menu_num == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON') or button_data[selected_menu_num] == self.DONE:
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'MainMenuView'))
            return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedAddressVerificationView'), view_args=dict(seed=self.seed, expanded_start_index=self.next_start_index, use_expanded=True))
    return SeedAddressVerificationNotFoundView

def _make_SeedExportXpubVerificationSuccessView():

    class SeedExportXpubVerificationSuccessView(_dependency('seedsigner.views.view', 'View')):

        def run(self):
            self.run_screen(_dependency('seedsigner.gui.screens', 'LargeIconStatusScreen'), title=_dependency('gettext', 'gettext')('Wallet Export'), status_icon_name=_dependency('seedsigner.gui.components', 'SeedSignerIconConstants').SUCCESS, text=_dependency('gettext', 'gettext')('Wallet export successful.'), button_data=[_dependency('seedsigner.gui.screens.screen', 'ButtonOption')(_dependency('gettext', 'gettext')('OK'))], show_back_button=False)
            self.controller.multisig_wallet_descriptor = None
            return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'MainMenuView'))
    return SeedExportXpubVerificationSuccessView

def _make_SeedExportXpubVerificationFailedView():

    class SeedExportXpubVerificationFailedView(_dependency('seedsigner.views.view', 'View')):

        def __init__(self, reason='no_match'):
            super().__init__()
            self.reason = reason

        def run(self):
            if self.reason == 'script_mismatch':
                text = _dependency('gettext', 'gettext')("Address format doesn't match exported script type. Wallet export unsuccessful.")
            else:
                text = _dependency('gettext', 'gettext')('Unable to match wallet to current seed. Wallet export unsuccessful.')
            self.run_screen(_dependency('seedsigner.gui.screens.screen', 'WarningScreen'), title=_dependency('gettext', 'gettext')('Export Failed'), status_icon_name=_dependency('seedsigner.gui.components', 'SeedSignerIconConstants').ERROR, status_headline=None, text=text, button_data=[_dependency('seedsigner.gui.screens.screen', 'ButtonOption')(_dependency('gettext', 'gettext')('OK'))], show_back_button=False)
            self.controller.multisig_wallet_descriptor = None
            return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'MainMenuView'))
    return SeedExportXpubVerificationFailedView

def _make_LoadMultisigWalletDescriptorView():

    class LoadMultisigWalletDescriptorView(_dependency('seedsigner.views.view', 'View')):
        SCAN = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Scan descriptor', _dependency('seedsigner.gui.components', 'SeedSignerIconConstants').QRCODE)
        FROM_SEEDKEEPER = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Load SeedKeeper', _dependency('seedsigner.gui.components', 'FontAwesomeIconConstants').LOCK)
        CANCEL = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Cancel')

        def run(self):
            button_data = [self.SCAN]
            if self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__SMARTCARD_SUPPORT) == _dependency('seedsigner.models.settings', 'SettingsConstants').OPTION__ENABLED:
                button_data.append(self.FROM_SEEDKEEPER)
            button_data.append(self.CANCEL)
            selected_menu_num = self.run_screen(_dependency('seedsigner.gui.screens', 'seed_screens').LoadMultisigWalletDescriptorScreen, button_data=button_data, show_back_button=False)
            if button_data[selected_menu_num] == self.SCAN:
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.scan_views', 'ScanWalletDescriptorView'))
            elif button_data[selected_menu_num] == self.CANCEL:
                if self.controller.resume_main_flow == _dependency('seedsigner.controller', 'Controller').FLOW__PSBT:
                    return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
                else:
                    return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'MainMenuView'))
            elif button_data[selected_menu_num] == self.FROM_SEEDKEEPER:
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.tools_views', 'ToolsSeedkeeperLoadDescriptorView'))
    return LoadMultisigWalletDescriptorView

def _make_MultisigWalletDescriptorView():

    class MultisigWalletDescriptorView(_dependency('seedsigner.views.view', 'View')):
        RETURN = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Return to transaction')
        VERIFY_ADDR = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Verify addr')
        ADDRESS_EXPLORER = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Address explorer')
        OK = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('OK')

        def run(self):
            descriptor = self.controller.multisig_wallet_descriptor
            fingerprints = []
            for key in descriptor.keys:
                fingerprint = _dependency('binascii', 'hexlify')(key.fingerprint).decode()
                fingerprints.append(fingerprint)
            if descriptor.is_basic_multisig:
                threshold, n = _dependency('seedsigner.helpers.embit_utils', 'get_multisig_policy')(descriptor)
                policy = _dependency('gettext', 'gettext')('{threshold} of {n}').format(threshold=threshold, n=n)
            else:
                policy = descriptor.brief_policy.split('multisig')[0].strip()
            button_data = [self.OK]
            if self.controller.resume_main_flow:
                if self.controller.resume_main_flow == _dependency('seedsigner.controller', 'Controller').FLOW__PSBT:
                    button_data = [self.RETURN]
                elif self.controller.resume_main_flow == _dependency('seedsigner.controller', 'Controller').FLOW__VERIFY_MULTISIG_ADDR and self.controller.unverified_address:
                    verify_addr_display = '{0} {1}'.format(_dependency('gettext', 'gettext')(self.VERIFY_ADDR.button_label), self.controller.unverified_address['address'][:7])
                    button_data = [_dependency('seedsigner.gui.screens.screen', 'ButtonOption')(verify_addr_display)]
                elif self.controller.resume_main_flow == _dependency('seedsigner.controller', 'Controller').FLOW__ADDRESS_EXPLORER:
                    button_data = [self.ADDRESS_EXPLORER]
            selected_menu_num = self.run_screen(_dependency('seedsigner.gui.screens', 'seed_screens').MultisigWalletDescriptorScreen, policy=policy, fingerprints=fingerprints, button_data=button_data)
            if selected_menu_num == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                self.controller.multisig_wallet_descriptor = None
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            elif button_data[selected_menu_num] == self.RETURN:
                self.controller.resume_main_flow = None
                psbt_parser = self.controller.psbt_parser
                if psbt_parser and psbt_parser.unidentified_change_outputs:
                    self.controller.psbt_parser = None
                    return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.psbt_views', 'PSBTOverviewView'), skip_current_view=True)
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.psbt_views', 'PSBTChangeDetailsView'), view_args=dict(change_address_num=0))
            elif button_data[selected_menu_num].button_label.startswith(_dependency('gettext', 'gettext')(self.VERIFY_ADDR.button_label)):
                self.controller.resume_main_flow = None
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedAddressVerificationView'))
            elif button_data[selected_menu_num] == self.ADDRESS_EXPLORER:
                self.controller.resume_main_flow = None
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.tools_views', 'ToolsAddressExplorerAddressTypeView'))
            return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'MainMenuView'))
    return MultisigWalletDescriptorView

def _make_SeedSignMessageStartView():

    class SeedSignMessageStartView(_dependency('seedsigner.views.view', 'View')):
        """
    Routes users straight through to the "Sign" screen if a signing `seed` has
    already been selected. Otherwise routes to `SeedSelectSeedView` to select or
    load a seed first.
    """

        def __init__(self, derivation_path, message):
            super().__init__()
            self.derivation_path = derivation_path
            self.message = message
            if self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__MESSAGE_SIGNING) == _dependency('seedsigner.models.settings', 'SettingsConstants').OPTION__DISABLED:
                self.set_redirect(_dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'OptionDisabledView'), view_args=dict(settings_attr=_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__MESSAGE_SIGNING)))
                return
            addr_format = _dependency('seedsigner.helpers', 'embit_utils').parse_derivation_path(derivation_path)
            if not addr_format['clean_match']:
                self.set_redirect(_dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'NotYetImplementedView'), view_args=dict(text='Signing messages for custom derivation paths not supported'.format())))
                self.controller.resume_main_flow = None
                return
            if self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__NETWORK) not in addr_format['network']:
                self.set_redirect(_dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'NetworkMismatchErrorView'), view_args=dict(derivation_path=self.derivation_path)))
                self.controller.resume_main_flow = None
                return
            data = self.controller.sign_message_data
            if not data:
                data = {}
                self.controller.sign_message_data = data
            data['derivation_path'] = derivation_path
            data['message'] = message
            data['addr_format'] = addr_format
            self.seed = data.get('seed')
            if self.seed is not None:
                self.set_redirect(_dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedSignMessageConfirmMessageView'), skip_current_view=True))
            else:
                self.set_redirect(_dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedSelectSeedView'), view_args=dict(flow=_dependency('seedsigner.controller', 'Controller').FLOW__SIGN_MESSAGE), skip_current_view=True))
    return SeedSignMessageStartView

def _make_SeedSignMessageConfirmMessageView():

    class SeedSignMessageConfirmMessageView(_dependency('seedsigner.views.view', 'View')):

        def __init__(self, page_num=0):
            super().__init__()
            self.page_num = page_num

        def run(self):
            selected_menu_num = self.run_screen(_dependency('seedsigner.gui.screens.seed_screens', 'SeedSignMessageConfirmMessageScreen'), page_num=self.page_num)
            if selected_menu_num == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                if self.page_num == 0:
                    self.controller.resume_main_flow = None
                    self.controller.sign_message_data = None
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            if self.page_num == len(self.controller.sign_message_data['paged_message']) - 1:
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedSignMessageConfirmAddressView'))
            else:
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedSignMessageConfirmMessageView'), view_args=dict(page_num=self.page_num + 1))
    return SeedSignMessageConfirmMessageView

def _make_SeedSignMessageConfirmAddressView():

    class SeedSignMessageConfirmAddressView(_dependency('seedsigner.views.view', 'View')):

        def __init__(self):
            super().__init__()
            data = self.controller.sign_message_data
            self.seed = data.get('seed')
            self.derivation_path = data.get('derivation_path')
            if not self.derivation_path:
                raise Exception("Routing error: sign_message_data hasn't been set")
            addr_format = _dependency('seedsigner.helpers', 'embit_utils').parse_derivation_path(self.derivation_path)
            if not addr_format['clean_match'] or addr_format['script_type'] == _dependency('seedsigner.models.settings', 'SettingsConstants').CUSTOM_DERIVATION:
                raise Exception(_dependency('gettext', 'gettext')('Signing messages for custom derivation paths not supported'))
            if addr_format['network'] != _dependency('seedsigner.models.settings', 'SettingsConstants').MAINNET:
                if self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__NETWORK) in [_dependency('seedsigner.models.settings', 'SettingsConstants').TESTNET, _dependency('seedsigner.models.settings', 'SettingsConstants').REGTEST]:
                    addr_format['network'] = self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__NETWORK)
                else:
                    self.set_redirect(_dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'NetworkMismatchErrorView'), view_args=dict(derivation_path=self.derivation_path)))
                    self.controller.resume_main_flow = None
                    self.controller.sign_message_data = None
                    return
            if self.controller.sign_message_with_satochip:
                connector = self.controller.Satochip_Connector
                script_type = addr_format['script_type']
                if script_type == _dependency('seedsigner.models.settings', 'SettingsConstants').NATIVE_SEGWIT:
                    xtype = 'p2wpkh'
                elif script_type == _dependency('seedsigner.models.settings', 'SettingsConstants').NESTED_SEGWIT:
                    xtype = 'p2wpkh-p2sh'
                elif script_type == _dependency('seedsigner.models.settings', 'SettingsConstants').LEGACY_P2PKH:
                    xtype = 'standard'
                elif script_type == _dependency('seedsigner.models.settings', 'SettingsConstants').TAPROOT:
                    xtype = 'standard'
                else:
                    xtype = 'p2wpkh'
                is_mainnet = addr_format['network'] == _dependency('seedsigner.models.settings', 'SettingsConstants').MAINNET
                wallet_path = _dependency('seedsigner.helpers.satochip_signer', 'format_path_string')(addr_format['wallet_derivation_path'])
                loading = _dependency('seedsigner.gui.screens.screen', 'LoadingScreenThread')(text=_dependency('gettext', 'gettext')('Exporting xpub...'))
                loading.start()
                try:
                    xpub_base58 = connector.card_bip32_get_xpub(wallet_path, xtype, is_mainnet)
                    xpub = _dependency('embit', 'bip32').HDKey.from_base58(xpub_base58)
                finally:
                    loading.stop()
            else:
                if self.seed is None:
                    raise Exception("Routing error: sign_message_data hasn't been set")
                seed = self.seed
                xpub = seed.get_xpub(wallet_path=addr_format['wallet_derivation_path'], network=addr_format['network'])
            data['addr_format'] = addr_format
            embit_network = _dependency('seedsigner.helpers', 'embit_utils').get_embit_network_name(addr_format['network'])
            self.address = _dependency('seedsigner.helpers', 'embit_utils').get_single_sig_address(xpub=xpub, script_type=addr_format['script_type'], index=addr_format['index'], is_change=addr_format['is_change'], embit_network=embit_network)
            data['address'] = self.address

        def run(self):
            selected_menu_num = self.run_screen(_dependency('seedsigner.gui.screens.seed_screens', 'SeedSignMessageConfirmAddressScreen'), derivation_path=self.derivation_path, address=self.address)
            if selected_menu_num == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedSignMessageSignedMessageQRView'))
    return SeedSignMessageConfirmAddressView

def _make_SeedSignMessageSignedMessageQRView():

    class SeedSignMessageSignedMessageQRView(_dependency('seedsigner.views.view', 'View')):
        """
    Displays the signed message as a QR code.
    """

        def __init__(self):
            super().__init__()
            data = self.controller.sign_message_data
            derivation_path = data['derivation_path']
            message = data['message']
            if self.controller.sign_message_with_satochip:
                loading = _dependency('seedsigner.gui.screens.screen', 'LoadingScreenThread')(text=_dependency('gettext', 'gettext')('Signing message...'))
                loading.start()
                error = None
                try:
                    _dependency('seedsigner.helpers.satochip_signer', 'verify_satochip_message_address')(self.controller.Satochip_Connector, data.get('addr_format', {}), data.get('address'))
                    self.signed_message = _dependency('seedsigner.helpers.satochip_signer', 'sign_message_with_satochip')(derivation_path, message, self.controller.Satochip_Connector)
                except FeatureUnavailable:
                    raise
                except Exception as exc:
                    error = str(exc)
                finally:
                    loading.stop()
                if error:
                    self.set_redirect(_dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedSignMessageSatochipVerificationFailedView'), view_args=dict(error=error), skip_current_view=True))
                    return
            else:
                self.seed = data['seed']
                seed = self.seed
                self.signed_message = _dependency('seedsigner.helpers', 'embit_utils').sign_message(root=seed.get_root(), derivation=derivation_path, msg=message.encode())

        def run(self):
            qr_encoder = _dependency('seedsigner.models.encode_qr', 'GenericStaticQrEncoder')(data=self.signed_message)
            self.run_screen(_dependency('seedsigner.gui.screens.screen', 'QRDisplayScreen'), qr_encoder=qr_encoder)
            self.controller.resume_main_flow = None
            self.controller.sign_message_data = None
            self.controller.sign_message_with_satochip = False
            return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'MainMenuView'), skip_current_view=True)
    return SeedSignMessageSignedMessageQRView

def _make_SeedSignMessageSatochipVerificationFailedView():

    class SeedSignMessageSatochipVerificationFailedView(_dependency('seedsigner.views.view', 'View')):

        def __init__(self, error):
            super().__init__()
            self.error = error

        def run(self):
            self.run_screen(_dependency('seedsigner.gui.screens.screen', 'WarningScreen'), title=_dependency('gettext', 'gettext')('Verification Failed'), status_headline=None, text=self.error, button_data=[_dependency('seedsigner.gui.screens.screen', 'ButtonOption')(_dependency('gettext', 'gettext')('OK'))], show_back_button=False)
            self.controller.resume_main_flow = None
            self.controller.sign_message_data = None
            self.controller.sign_message_with_satochip = False
            return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'MainMenuView'), skip_current_view=True)
    return SeedSignMessageSatochipVerificationFailedView

def _make_SeedExportPlaintextQRView():

    class SeedExportPlaintextQRView(_dependency('seedsigner.views.view', 'View')):

        def __init__(self, seed, share_index=None):
            super().__init__()
            self.seed = seed
            self.seed = seed
            self.share_index = share_index

        def run(self):
            data = self.seed.mnemonic_str
            if isinstance(self.seed, _dependency('seedsigner.models.seed', 'AezeedSeed')):
                data = 'aezeed:{0}\npassphrase:{1}'.format(self.seed.mnemonic_str, self.seed.passphrase)
            if isinstance(self.seed, _dependency('seedsigner.models.seed', 'XprvSeed')):
                data = self.seed.get_root().to_base58()
            if isinstance(self.seed, _dependency('seedsigner.models.seed', 'Slip39Seed')) and self.share_index is not None:
                data = self.seed.mnemonic_list[self.share_index]
            encoder_args = dict(data=data)
            e = _dependency('seedsigner.models.encode_qr', 'GenericStaticQrEncoder')(**encoder_args)
            self.run_screen(_dependency('seedsigner.gui.screens.screen', 'QRDisplayScreen'), qr_encoder=e)
            return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedOptionsView'), view_args={'seed': self.seed})
    return SeedExportPlaintextQRView

def _make_SaveToSeedkeeperView():

    class SaveToSeedkeeperView(_dependency('seedsigner.views.view', 'View')):

        def mnemonic_to_entropy(self, bip39_mnemonic, wordlist):
            if wordlist not in (None, 'english'):
                raise ValueError('Unsupported BIP-39 wordlist: {0}. Only English is supported.'.format(wordlist))
            return _dependency('embit', 'bip39').mnemonic_to_bytes(bip39_mnemonic)

        def __init__(self, seed, bip85_data=None, share_index=None):
            super().__init__()
            self.seed = seed
            self.bip85_data = bip85_data
            self.share_index = share_index

        def run(self):
            Satochip_Connector = None
            try:
                Satochip_Connector = _dependency('seedsigner.helpers', 'seedkeeper_utils').init_satochip(self, init_card_filter=['seedkeeper'])
                if not Satochip_Connector:
                    return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
                seed = self.seed
                if isinstance(seed, _dependency('seedsigner.models.seed', 'Slip39Seed')):
                    if self.share_index is None:
                        button_data = [_dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Share {0}'.format(i + 1)) for i in range(len(seed.mnemonic_list))]
                        share_sel = self.run_screen(_dependency('seedsigner.gui.screens', 'ButtonListScreen'), title='Select Share', is_button_text_centered=False, button_data=button_data, show_back_button=True)
                        if share_sel == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                            return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
                    else:
                        share_sel = self.share_index
                    share = seed.mnemonic_list[share_sel]
                    fingerprint = seed.get_fingerprint(network=self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__NETWORK))
                    ret = _dependency('seedsigner.gui.screens', 'seed_screens').SeedAddPassphraseScreen(title='Secret Label', passphrase=fingerprint).display()
                    if 'is_back_button' in ret:
                        return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
                    label = 'SLIP39:' + ret['passphrase']
                    export_rights = 'Plaintext export allowed'
                    header = Satochip_Connector.make_header('Password', export_rights, label)
                    share_list = list(bytes(share, 'utf-8'))
                    secret_list = [len(share_list)] + share_list
                    secret_dic = {'header': header, 'secret_list': secret_list}
                else:
                    fingerprint = seed.get_fingerprint(network=self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__NETWORK))
                    ret = _dependency('seedsigner.gui.screens', 'seed_screens').SeedAddPassphraseScreen(title='Seed Label', passphrase=fingerprint).display()
                    if 'is_back_button' in ret:
                        return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
                    status = Satochip_Connector.card_get_status()[3]
                    print(status)
                    if isinstance(seed, _dependency('seedsigner.models.seed', 'ElectrumSeed')):
                        print('Saving Electrum seed')
                        label = ret['passphrase']
                        export_rights = 'Plaintext export allowed'
                        type = 'Electrum mnemonic'
                        subtype = 0
                        electrum_mnemonic_list = list(bytes(seed.mnemonic_str, 'utf-8'))
                        electrum_passphrase_list = list(bytes(seed.passphrase, 'utf-8'))
                        secret_list = [len(electrum_mnemonic_list)] + electrum_mnemonic_list + [len(electrum_passphrase_list)] + electrum_passphrase_list
                        header = Satochip_Connector.make_header(type, export_rights, label, subtype=subtype)
                        secret_dic = {'header': header, 'secret_list': secret_list}
                    elif isinstance(seed, _dependency('seedsigner.models.seed', 'AezeedSeed')):
                        print('Saving Aezeed seed')
                        label = 'aezeed:{0}'.format(ret['passphrase'])
                        export_rights = 'Plaintext export allowed'
                        type = 'Password'
                        aezeed_secret = 'aezeed:{0}'.format(seed.mnemonic_str)
                        if seed.passphrase:
                            aezeed_secret += '\npassphrase:{0}'.format(seed.passphrase)
                        aezeed_secret_list = list(bytes(aezeed_secret, 'utf-8'))
                        secret_list = [len(aezeed_secret_list)] + aezeed_secret_list
                        header = Satochip_Connector.make_header(type, export_rights, label)
                        secret_dic = {'header': header, 'secret_list': secret_list}
                    else:
                        if isinstance(seed, _dependency('seedsigner.models.seed', 'XprvSeed')) and status['protocol_minor_version'] == 1:
                            self.run_screen(_dependency('seedsigner.gui.screens', 'WarningScreen'), title='Error', status_headline=None, text='SeedKeeper v1 cannot store xprv seeds.', show_back_button=True)
                            return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
                        if status['protocol_minor_version'] == 1:
                            print('Saving to SeedKeeper V1')
                            label = ret['passphrase']
                            export_rights = 'Plaintext export allowed'
                            type = 'BIP39 mnemonic'
                            subtype = 0
                            bip39_mnemonic = seed.mnemonic_str
                            bip39_mnemonic_list = list(bytes(bip39_mnemonic, 'utf-8'))
                            bip39_passphrase = seed.passphrase
                            bip39_passphrase_list = list(bytes(bip39_passphrase, 'utf-8'))
                            secret_list = [len(bip39_mnemonic_list)] + bip39_mnemonic_list + [len(bip39_passphrase_list)] + bip39_passphrase_list
                        else:
                            print('Saving to SeedKeeper V2')
                            label = ret['passphrase']
                            export_rights = 'Plaintext export allowed'
                            if isinstance(seed, _dependency('seedsigner.models.seed', 'XprvSeed')):
                                type = 'Data'
                                label = 'XPRV:{0}'.format(label)
                                xprv_list = list(bytes(seed.get_root().to_base58(), 'utf-8'))
                                secret_list = list(len(xprv_list).to_bytes(2, 'big')) + xprv_list
                            else:
                                type = 'Masterseed'
                                subtype = 1
                                wordlist_byte = _dependency('pysatochip.util', 'dict_swap_keys_values')(_dependency('pysatochip.JCconstants', 'BIP39_WORDLIST_DIC')).get('english')
                                bip39_entropy_bytes = self.mnemonic_to_entropy(seed.mnemonic_str, 'english')
                                bip39_entropy_list = list(bip39_entropy_bytes)
                                bip39_passphrase_list = list(bytes(seed.passphrase, 'utf-8'))
                                masterseed_bytes = seed.seed_bytes
                                masterseed_list = list(masterseed_bytes)
                                secret_list = [len(masterseed_list)] + masterseed_list + [wordlist_byte] + [len(bip39_entropy_list)] + bip39_entropy_list + [len(bip39_passphrase_list)] + bip39_passphrase_list
                        if type == 'Data':
                            header = Satochip_Connector.make_header(type, export_rights, label)
                        else:
                            header = Satochip_Connector.make_header(type, export_rights, label, subtype=subtype)
                        secret_dic = {'header': header, 'secret_list': secret_list}
                try:
                    fits, required_bytes, free_bytes = _dependency('seedsigner.helpers', 'seedkeeper_utils').ensure_seedkeeper_capacity(Satochip_Connector, secret_dic)
                except FeatureUnavailable:
                    raise
                except Exception as e:
                    self.run_screen(_dependency('seedsigner.gui.screens', 'WarningScreen'), title='Error', status_headline=None, text=str(e), show_back_button=True)
                    return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
                if not fits:
                    self.run_screen(_dependency('seedsigner.gui.screens', 'WarningScreen'), title='Not Enough Space', status_headline=None, text=_dependency('seedsigner.helpers', 'seedkeeper_utils').format_seedkeeper_space_error(required_bytes, free_bytes), show_back_button=True)
                    return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
                self.loading_screen = _dependency('seedsigner.gui.screens.screen', 'LoadingScreenThread')(text='Saving Seed\n\n\n\n\n\n')
                self.loading_screen.start()
                sid, fingerprint = Satochip_Connector.seedkeeper_import_secret(secret_dic)
                print('Imported - SID:', sid, ' Fingerprint:', fingerprint)
                self.loading_screen.stop()
                _dependency('seedsigner_port.clock', None).sleep(0.1)
                self.run_screen(_dependency('seedsigner.gui.screens', 'LargeIconStatusScreen'), title='Secret Saved', status_headline=None, text='Secret Successfully Saved to Seedkeeper'.format(), show_back_button=True)
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('SeedOptionsView'), view_args={'seed': self.seed}, clear_history=True)
            except FeatureUnavailable:
                raise
            except Exception as e:
                pass
                self.loading_screen.stop()
                _dependency('seedsigner_port.clock', None).sleep(0.1)
                self.run_screen(_dependency('seedsigner.gui.screens', 'WarningScreen'), title='Error', status_headline=None, text=_dependency('seedsigner.helpers', 'seedkeeper_utils').describe_seedkeeper_error(e, Satochip_Connector), show_back_button=True)
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
    return SaveToSeedkeeperView

_FACTORIES={'SeedsMenuView':_make_SeedsMenuView,'SeedSelectSeedView':_make_SeedSelectSeedView,'LoadSeedView':_make_LoadSeedView,'SeedKeeperSelectView':_make_SeedKeeperSelectView,'SeedBitbox02BackupSelectView':_make_SeedBitbox02BackupSelectView,'SeedBitbox02BackupSummaryView':_make_SeedBitbox02BackupSummaryView,'SeedPassportBackupSelectView':_make_SeedPassportBackupSelectView,'SeedPassportBackupCodeEntryView':_make_SeedPassportBackupCodeEntryView,'SeedPassportBackupSummaryView':_make_SeedPassportBackupSummaryView,'SeedTapsignerBackupSelectView':_make_SeedTapsignerBackupSelectView,'SeedTapsignerBackupKeyEntryView':_make_SeedTapsignerBackupKeyEntryView,'SeedTapsignerBackupSummaryView':_make_SeedTapsignerBackupSummaryView,'SeedMnemonicEntryView':_make_SeedMnemonicEntryView,'SeedMnemonicInvalidView':_make_SeedMnemonicInvalidView,'SeedFinalizeView':_make_SeedFinalizeView,'SeedAezeedPassphraseModeView':_make_SeedAezeedPassphraseModeView,'SeedAddPassphraseView':_make_SeedAddPassphraseView,'SeedAddPassphraseExitDialogView':_make_SeedAddPassphraseExitDialogView,'SeedScanPassphraseView':_make_SeedScanPassphraseView,'SeedLoadSeedKeeperPassphraseView':_make_SeedLoadSeedKeeperPassphraseView,'SeedReviewPassphraseView':_make_SeedReviewPassphraseView,'SeedDiscardView':_make_SeedDiscardView,'SeedAezeedMnemonicStartView':_make_SeedAezeedMnemonicStartView,'SeedElectrumMnemonicStartView':_make_SeedElectrumMnemonicStartView,'SeedSlip39MnemonicStartView':_make_SeedSlip39MnemonicStartView,'SeedSlip39ShareEntryView':_make_SeedSlip39ShareEntryView,'SeedSlip39MoreSharesView':_make_SeedSlip39MoreSharesView,'SeedSlip39ShareInvalidView':_make_SeedSlip39ShareInvalidView,'SeedSlip39SelectShareView':_make_SeedSlip39SelectShareView,'SeedSlip39LoadFromSeedkeeperView':_make_SeedSlip39LoadFromSeedkeeperView,'SeedSlip39CreateFromBytesView':_make_SeedSlip39CreateFromBytesView,'SeedSlip39RegenerateSharesView':_make_SeedSlip39RegenerateSharesView,'SeedOptionsView':_make_SeedOptionsView,'SeedBackupView':_make_SeedBackupView,'SeedExportXpubSigTypeView':_make_SeedExportXpubSigTypeView,'SeedExportXpubScriptTypeView':_make_SeedExportXpubScriptTypeView,'SeedExportXpubCustomDerivationView':_make_SeedExportXpubCustomDerivationView,'AccountNumberView':_make_AccountNumberView,'SeedExportXpubQRFormatView':_make_SeedExportXpubQRFormatView,'SeedExportXpubWarningView':_make_SeedExportXpubWarningView,'SeedExportXpubDetailsView':_make_SeedExportXpubDetailsView,'SeedExportXpubQRDisplayView':_make_SeedExportXpubQRDisplayView,'SeedExportXpubVerifyAddressView':_make_SeedExportXpubVerifyAddressView,'SeedWordsWarningView':_make_SeedWordsWarningView,'SeedWordsView':_make_SeedWordsView,'SeedBIP85SelectNumWordsView':_make_SeedBIP85SelectNumWordsView,'SeedBIP85SelectChildIndexView':_make_SeedBIP85SelectChildIndexView,'SeedBIP85InvalidChildIndexView':_make_SeedBIP85InvalidChildIndexView,'SeedWordsBackupTestPromptView':_make_SeedWordsBackupTestPromptView,'SeedWordsBackupTestView':_make_SeedWordsBackupTestView,'SeedWordsBackupTestMistakeView':_make_SeedWordsBackupTestMistakeView,'SeedWordsBackupTestSuccessView':_make_SeedWordsBackupTestSuccessView,'SeedTranscribeSeedQRFormatView':_make_SeedTranscribeSeedQRFormatView,'SeedTranscribeSeedQRWarningView':_make_SeedTranscribeSeedQRWarningView,'SeedTranscribeSeedQRWholeQRView':_make_SeedTranscribeSeedQRWholeQRView,'SeedEncryptedQRTypeEncryptionKeyView':_make_SeedEncryptedQRTypeEncryptionKeyView,'SeedEncryptedQRTypeEncryptionKeyExitDialogView':_make_SeedEncryptedQRTypeEncryptionKeyExitDialogView,'SeedEncryptedQRScanEncryptionKeyView':_make_SeedEncryptedQRScanEncryptionKeyView,'SeedEncryptedQRReviewEncryptionKeyView':_make_SeedEncryptedQRReviewEncryptionKeyView,'SeedEncryptedQRnonECBModeView':_make_SeedEncryptedQRnonECBModeView,'SeedEncryptedQRMnemonicIDPromptView':_make_SeedEncryptedQRMnemonicIDPromptView,'SeedEncryptedQRMnemonicIDEntryView':_make_SeedEncryptedQRMnemonicIDEntryView,'SeedEncryptedQRMnemonicIDEntryExitDialogView':_make_SeedEncryptedQRMnemonicIDEntryExitDialogView,'SeedEncryptedQRReviewMnemonicIDView':_make_SeedEncryptedQRReviewMnemonicIDView,'SeedEncryptedQRTranscribeModePromptView':_make_SeedEncryptedQRTranscribeModePromptView,'SeedEncryptedQRTranscribeModeView':_make_SeedEncryptedQRTranscribeModeView,'SeedTranscribeEncryptedQRZoomedInView':_make_SeedTranscribeEncryptedQRZoomedInView,'SeedEncryptedQRFullScreenModeView':_make_SeedEncryptedQRFullScreenModeView,'SeedTranscribeSeedQRZoomedInView':_make_SeedTranscribeSeedQRZoomedInView,'SeedTranscribeSeedQRConfirmQRPromptView':_make_SeedTranscribeSeedQRConfirmQRPromptView,'SeedTranscribeSeedQRConfirmScanView':_make_SeedTranscribeSeedQRConfirmScanView,'SeedTranscribeSeedQRConfirmWrongSeedView':_make_SeedTranscribeSeedQRConfirmWrongSeedView,'SeedTranscribeSeedQRConfirmInvalidQRView':_make_SeedTranscribeSeedQRConfirmInvalidQRView,'SeedTranscribeSeedQRConfirmSuccessView':_make_SeedTranscribeSeedQRConfirmSuccessView,'AddressVerificationStartView':_make_AddressVerificationStartView,'AddressVerificationSigTypeView':_make_AddressVerificationSigTypeView,'SeedAddressVerificationView':_make_SeedAddressVerificationView,'SeedAddressVerificationSuccessView':_make_SeedAddressVerificationSuccessView,'SeedAddressVerificationSimpleNotFoundView':_make_SeedAddressVerificationSimpleNotFoundView,'SeedAddressVerificationNotFoundView':_make_SeedAddressVerificationNotFoundView,'SeedExportXpubVerificationSuccessView':_make_SeedExportXpubVerificationSuccessView,'SeedExportXpubVerificationFailedView':_make_SeedExportXpubVerificationFailedView,'LoadMultisigWalletDescriptorView':_make_LoadMultisigWalletDescriptorView,'MultisigWalletDescriptorView':_make_MultisigWalletDescriptorView,'SeedSignMessageStartView':_make_SeedSignMessageStartView,'SeedSignMessageConfirmMessageView':_make_SeedSignMessageConfirmMessageView,'SeedSignMessageConfirmAddressView':_make_SeedSignMessageConfirmAddressView,'SeedSignMessageSignedMessageQRView':_make_SeedSignMessageSignedMessageQRView,'SeedSignMessageSatochipVerificationFailedView':_make_SeedSignMessageSatochipVerificationFailedView,'SeedExportPlaintextQRView':_make_SeedExportPlaintextQRView,'SaveToSeedkeeperView':_make_SaveToSeedkeeperView}
_CACHE={}
def _resolve(name):
    if name not in _CACHE:
        if name not in _FACTORIES:raise AttributeError(name)
        _CACHE[name]=_FACTORIES[name]()
    return _CACHE[name]
def __getattr__(name):return _resolve(name)
