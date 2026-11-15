# Copyright2021 SeedSigner; MIT, see ../LICENSE.SeedSigner
# Generated original Views; optional providers remain explicit.
from seedsigner_port.decode_platform import dependency as _dependency,FeatureUnavailable
def _make_PSBTSelectSeedView():

    class PSBTSelectSeedView(_dependency('seedsigner.views.view', 'View')):
        SCAN_SEED = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Scan a seed', _dependency('seedsigner.gui.components', 'SeedSignerIconConstants').QRCODE)
        SATOCHIP = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Use Satochip card', _dependency('seedsigner.gui.components', 'SeedSignerIconConstants').FINGERPRINT)
        KEYCARD = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Use Keycard', _dependency('seedsigner.gui.components', 'SeedSignerIconConstants').FINGERPRINT)
        TYPE_12WORD = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Enter 12-word seed', _dependency('seedsigner.gui.components', 'FontAwesomeIconConstants').KEYBOARD, return_data=12)
        TYPE_15WORD = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Enter 15-word seed', _dependency('seedsigner.gui.components', 'FontAwesomeIconConstants').KEYBOARD, return_data=15)
        TYPE_18WORD = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Enter 18-word seed', _dependency('seedsigner.gui.components', 'FontAwesomeIconConstants').KEYBOARD, return_data=18)
        TYPE_21WORD = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Enter 21-word seed', _dependency('seedsigner.gui.components', 'FontAwesomeIconConstants').KEYBOARD, return_data=21)
        TYPE_24WORD = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Enter 24-word seed', _dependency('seedsigner.gui.components', 'FontAwesomeIconConstants').KEYBOARD, return_data=24)
        TYPE_ELECTRUM = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Enter Electrum seed', _dependency('seedsigner.gui.components', 'FontAwesomeIconConstants').KEYBOARD)
        TYPE_WIF = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Enter WIF', _dependency('seedsigner.gui.components', 'FontAwesomeIconConstants').KEYBOARD)
        SCAN_WIF = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Scan WIF', _dependency('seedsigner.gui.components', 'SeedSignerIconConstants').QRCODE)
        TYPE_BIP38 = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Enter BIP38', _dependency('seedsigner.gui.components', 'FontAwesomeIconConstants').KEYBOARD)
        SCAN_BIP38 = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Scan BIP38', _dependency('seedsigner.gui.components', 'SeedSignerIconConstants').QRCODE)

        def run(self):

            def ensure_microsd_seed_warning():
                if not getattr(self.controller, 'psbt_from_microsd', False):
                    return True
                if getattr(self.controller, 'psbt_microsd_seed_warning_shown', False):
                    return True
                ret = self.run_screen(_dependency('seedsigner.gui.screens.screen', 'WarningScreen'), title='WARNING', status_headline=None, text='These tools load data from the microSD card and may expose loaded secrets.', show_back_button=True, button_data=[_dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Continue')])
                if ret == _dependency('seedsigner.gui.screens.screen', 'RET_CODE__BACK_BUTTON'):
                    return False
                self.controller.psbt_microsd_seed_warning_shown = True
                return True
            if not self.controller.psbt:
                raise Exception('No transaction currently loaded')
            if self.controller.psbt_seed:
                if isinstance(self.controller.psbt_seed, _dependency('seedsigner.models.wif', 'WIFKey')):
                    if _dependency('seedsigner.models.psbt_parser', 'PSBTParser').wif_can_sign_any_input(psbt=self.controller.psbt, wif_key=self.controller.psbt_seed):
                        return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('PSBTOverviewView'))
                elif _dependency('seedsigner.models.psbt_parser', 'PSBTParser').has_matching_input_fingerprint(psbt=self.controller.psbt, seed=self.controller.psbt_seed, network=self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__NETWORK)):
                    return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('PSBTOverviewView'))
            seeds = self.controller.storage.seeds
            button_data = []
            for seed in seeds:
                button_str = seed.get_fingerprint(self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__NETWORK))
                if not _dependency('seedsigner.models.psbt_parser', 'PSBTParser').has_matching_input_fingerprint(psbt=self.controller.psbt, seed=seed, network=self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__NETWORK)):
                    button_str = _dependency('gettext', 'gettext')('{} (?)').format(button_str)
                button_data.append(_dependency('seedsigner.gui.screens.screen', 'ButtonOption')(button_str, _dependency('seedsigner.gui.components', 'SeedSignerIconConstants').FINGERPRINT))
            if self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__SATOCHIP_SUPPORT) == _dependency('seedsigner.models.settings', 'SettingsConstants').OPTION__ENABLED:
                button_data.append(self.SATOCHIP)
            if self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__KEYCARD_SUPPORT) == _dependency('seedsigner.models.settings', 'SettingsConstants').OPTION__ENABLED:
                button_data.append(self.KEYCARD)
            button_data.append(self.SCAN_SEED)
            if self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__WIF_KEYS) == _dependency('seedsigner.models.settings', 'SettingsConstants').OPTION__ENABLED:
                button_data.append(self.SCAN_WIF)
            if self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__BIP38_KEYS) == _dependency('seedsigner.models.settings', 'SettingsConstants').OPTION__ENABLED:
                button_data.append(self.SCAN_BIP38)
            seed_lengths = self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__SEED_WORD_LENGTHS)
            options = {12: self.TYPE_12WORD, 15: self.TYPE_15WORD, 18: self.TYPE_18WORD, 21: self.TYPE_21WORD, 24: self.TYPE_24WORD}
            for l in seed_lengths:
                button_data.append(options[l])
            if self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__ELECTRUM_SEEDS) == _dependency('seedsigner.models.settings', 'SettingsConstants').OPTION__ENABLED:
                button_data.append(self.TYPE_ELECTRUM)
            if self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__WIF_KEYS) == _dependency('seedsigner.models.settings', 'SettingsConstants').OPTION__ENABLED:
                button_data.append(self.TYPE_WIF)
            if self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__BIP38_KEYS) == _dependency('seedsigner.models.settings', 'SettingsConstants').OPTION__ENABLED:
                button_data.append(self.TYPE_BIP38)
            selected_menu_num = self.run_screen(_dependency('seedsigner.gui.screens.screen', 'ButtonListScreen'), title=_dependency('gettext', 'gettext')('Select Signer'), is_button_text_centered=False, button_data=button_data)
            if selected_menu_num == _dependency('seedsigner.gui.screens.screen', 'RET_CODE__BACK_BUTTON'):
                if getattr(self.controller, 'psbt_from_microsd', False):
                    self.controller.psbt_from_microsd = False
                    self.controller.psbt_microsd_save_path = None
                    self.controller.psbt_microsd_seed_warning_shown = False
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            if len(seeds) > 0 and selected_menu_num < len(seeds):
                if not ensure_microsd_seed_warning():
                    return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('PSBTSelectSeedView'))
                self.controller.psbt_seed = seeds[selected_menu_num]
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('PSBTOverviewView'))
            self.controller.resume_main_flow = _dependency('seedsigner.controller', 'Controller').FLOW__PSBT
            if button_data[selected_menu_num] == self.SCAN_SEED:
                if not ensure_microsd_seed_warning():
                    return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('PSBTSelectSeedView'))
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.scan_views', 'ScanSeedQRView'))
            elif button_data[selected_menu_num] == self.SCAN_WIF:
                if not ensure_microsd_seed_warning():
                    return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('PSBTSelectSeedView'))
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.scan_views', 'ScanWIFQRView'))
            elif button_data[selected_menu_num] == self.SCAN_BIP38:
                if not ensure_microsd_seed_warning():
                    return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('PSBTSelectSeedView'))
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.scan_views', 'ScanBIP38QRView'))
            elif button_data[selected_menu_num] in [self.SATOCHIP, self.KEYCARD]:
                card_choice = button_data[selected_menu_num]
                if card_choice == self.KEYCARD:
                    backend_preference = 'keycard'
                    card_label = 'Keycard'
                    self.controller.smartcard_backend_preference = 'keycard'
                else:
                    backend_preference = 'pysatochip'
                    card_label = 'Satochip'
                    self.controller.smartcard_backend_preference = 'pysatochip'
                init_kwargs = {'init_card_filter': ['satochip']}
                if backend_preference is not None:
                    init_kwargs['backend_preference'] = backend_preference
                connector = _dependency('seedsigner.helpers', 'seedkeeper_utils').init_satochip(self, **init_kwargs)
                if not connector:
                    return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('PSBTSelectSeedView'), clear_history=True)
                if _dependency('seedsigner.helpers', 'seedkeeper_utils').satochip_2fa_blocks_signing(self, connector):
                    return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('PSBTSelectSeedView'), clear_history=True)
                psbt = self.controller.psbt
                is_multisig_psbt = False
                try:
                    if psbt and psbt.inputs:
                        first_input = psbt.inputs[0]
                        if first_input.witness_utxo:
                            script_pubkey = first_input.witness_utxo.script_pubkey
                        elif first_input.non_witness_utxo:
                            script_pubkey = first_input.script_pubkey
                        else:
                            script_pubkey = None
                        if script_pubkey is not None:
                            policy = _dependency('seedsigner.models.psbt_parser', 'PSBTParser')._get_policy(first_input, script_pubkey, psbt.xpubs, None)
                            is_multisig_psbt = isinstance(policy, dict) and 'm' in policy
                except FeatureUnavailable:
                    raise
                except Exception as exc:
                    pass
                if is_multisig_psbt:
                    try:
                        parser = seedless_multisig_parser(self.controller, self.settings)
                    except FeatureUnavailable:
                        raise
                    except _dependency('seedsigner.models.psbt_parser', 'InvalidPSBTError') as e:
                        pass
                        return refusal_destination(e)
                    except Exception as e:
                        pass
                        self.run_screen(_dependency('seedsigner.gui.screens.screen', 'WarningScreen'), title='Failed', status_headline=None, text=str(e))
                        return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('PSBTSelectSeedView'), clear_history=True)
                    self.controller.psbt_parser = parser
                    self.controller.psbt_seed = None
                    self.controller.psbt_sign_with_satochip = True
                    return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('PSBTOverviewView'))
                network = self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__NETWORK)
                is_mainnet = network == _dependency('seedsigner.models.settings', 'SettingsConstants').MAINNET
                first_der = next(iter(self.controller.psbt.inputs[0].bip32_derivations.values())).derivation
                account_path = []
                HARDENED_INDEX = 2147483648
                for idx in first_der:
                    if idx & HARDENED_INDEX:
                        account_path.append(idx)
                    else:
                        break
                account_path_str = 'm'
                for i in account_path:
                    hardened = bool(i & HARDENED_INDEX)
                    index = i & 2147483647
                    suffix = "'" if hardened else ''
                    account_path_str += '/{0}{1}'.format(index, suffix)
                purpose = account_path[0] & 2147483647 if account_path else 0
                xtype = {44: 'standard', 49: 'p2wpkh-p2sh', 84: 'p2wpkh', 48: 'p2wsh-p2sh' if len(account_path) > 3 and account_path[3] & 2147483647 == 1 else 'p2wsh'}.get(purpose, 'standard')
                loading = _dependency('seedsigner.gui.screens.screen', 'LoadingScreenThread')(text=_dependency('gettext', 'gettext')('Parsing PSBT...'))
                loading.start()
                loading_stopped = False
                try:
                    try:
                        account_xpub = connector.card_bip32_get_xpub(account_path_str, xtype, is_mainnet)
                        master_xpub = connector.card_bip32_get_xpub('', xtype, is_mainnet)
                    except FeatureUnavailable:
                        raise
                    except Exception as e:
                        pass
                        loading.stop()
                        loading_stopped = True
                        self.run_screen(_dependency('seedsigner.gui.screens.screen', 'WarningScreen'), title='Failed', status_headline=None, text=str(e))
                        return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('PSBTSelectSeedView'), clear_history=True)
                    root_key = _dependency('embit.bip32', 'HDKey').from_base58(account_xpub)
                    master_fp = _dependency('embit.bip32', 'HDKey').from_base58(master_xpub).my_fingerprint
                    try:
                        self.controller.psbt_parser = _dependency('seedsigner.models.psbt_parser', 'PSBTParser')(self.controller.psbt, seed=None, root=root_key, root_path=account_path, master_fingerprint=master_fp, network=network)
                    except FeatureUnavailable:
                        raise
                    except _dependency('seedsigner.models.psbt_parser', 'InvalidPSBTError') as e:
                        pass
                        self.controller.psbt_parser = None
                        self.controller.psbt_sign_with_satochip = False
                        loading.stop()
                        loading_stopped = True
                        return refusal_destination(e)
                    except Exception as e:
                        pass
                        loading.stop()
                        loading_stopped = True
                        self.run_screen(_dependency('seedsigner.gui.screens.screen', 'WarningScreen'), title='Failed', status_headline=None, text=str(e))
                        return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('PSBTSelectSeedView'), clear_history=True)
                    card_fingerprints = {_dependency('binascii', 'hexlify')(master_fp).decode()}
                    try:
                        card_fingerprints.add(_dependency('binascii', 'hexlify')(root_key.child(0).fingerprint).decode())
                    except FeatureUnavailable:
                        raise
                    except Exception:
                        pass
                    psbt_fingerprints = set(_dependency('seedsigner.models.psbt_parser', 'PSBTParser').get_input_fingerprints(self.controller.psbt))
                    if not card_fingerprints.intersection(psbt_fingerprints):
                        pass
                        self.controller.psbt_parser = None
                        self.controller.psbt_sign_with_satochip = False
                        loading.stop()
                        loading_stopped = True
                        self.run_screen(_dependency('seedsigner.gui.screens.screen', 'WarningScreen'), title=_dependency('gettext', 'gettext')('Fingerprint mismatch'), status_icon_name=_dependency('seedsigner.gui.components', 'SeedSignerIconConstants').WARNING, status_headline=_dependency('gettext', 'gettext')('Card cannot sign PSBT'), text=_dependency('gettext', 'gettext')('Card fingerprint ({}) not in PSBT signers.').format(sorted(card_fingerprints)[0]))
                        return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('PSBTSelectSeedView'), clear_history=True)
                finally:
                    if not loading_stopped:
                        loading.stop()
                self.controller.psbt_seed = None
                self.controller.psbt_sign_with_satochip = True
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('PSBTOverviewView'))
            elif button_data[selected_menu_num] in [self.TYPE_12WORD, self.TYPE_15WORD, self.TYPE_18WORD, self.TYPE_21WORD, self.TYPE_24WORD]:
                if not ensure_microsd_seed_warning():
                    return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('PSBTSelectSeedView'))
                self.controller.storage.init_pending_mnemonic(num_words=button_data[selected_menu_num].return_data)
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.seed_views', 'SeedMnemonicEntryView'))
            elif button_data[selected_menu_num] == self.TYPE_ELECTRUM:
                if not ensure_microsd_seed_warning():
                    return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('PSBTSelectSeedView'))
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.seed_views', 'SeedElectrumMnemonicStartView'))
            elif button_data[selected_menu_num] == self.TYPE_WIF:
                if not ensure_microsd_seed_warning():
                    return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('PSBTSelectSeedView'))
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('PSBTWIFEntryView'))
            elif button_data[selected_menu_num] == self.TYPE_BIP38:
                if not ensure_microsd_seed_warning():
                    return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('PSBTSelectSeedView'))
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('PSBTBIP38EntryView'))
    return PSBTSelectSeedView

def _make_PSBTWIFEntryView():

    class PSBTWIFEntryView(_dependency('seedsigner.views.view', 'View')):

        def run(self):
            ret = self.run_screen(_dependency('seedsigner.gui.screens', 'seed_screens').SeedAddPassphraseScreen, title=_dependency('gettext', 'gettext')('Private Key (WIF)'), passphrase='')
            if 'is_back_button' in ret:
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            wif = ret['passphrase']
            try:
                key = _dependency('seedsigner.models.wif', 'WIFKey')(wif)
            except _dependency('seedsigner.models.seed', 'InvalidSeedException'):
                self.run_screen(_dependency('seedsigner.gui.screens.screen', 'DireWarningScreen'), status_headline=_dependency('gettext', 'gettext')('Invalid WIF!'), text=_dependency('gettext', 'gettext')('Not a valid WIF-encoded private key.'), button_data=[_dependency('seedsigner.gui.screens.screen', 'ButtonOption')('OK')], show_back_button=False)
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('PSBTSelectSeedView'))
            self.controller.psbt_seed = key
            return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('PSBTOverviewView'))
    return PSBTWIFEntryView

def _make_PSBTBIP38EntryView():

    class PSBTBIP38EntryView(_dependency('seedsigner.views.view', 'View')):

        def run(self):
            ret = self.run_screen(_dependency('seedsigner.gui.screens', 'seed_screens').SeedAddPassphraseScreen, title=_dependency('gettext', 'gettext')('BIP38 Key'), passphrase='')
            if 'is_back_button' in ret:
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            bip38 = ret['passphrase']
            return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('PSBTBIP38PassphraseView'), view_args=dict(encrypted=bip38))
    return PSBTBIP38EntryView

def _make_PSBTBIP38PassphraseView():

    class PSBTBIP38PassphraseView(_dependency('seedsigner.views.view', 'View')):

        def __init__(self, encrypted):
            super().__init__()
            self.encrypted = encrypted

        def run(self):
            ret = self.run_screen(_dependency('seedsigner.gui.screens', 'seed_screens').SeedAddPassphraseScreen, title=_dependency('gettext', 'gettext')('BIP38 Passphrase'), passphrase='')
            if 'is_back_button' in ret:
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            passphrase = ret['passphrase']
            try:
                key = _dependency('seedsigner.models.bip38', 'BIP38Key')(self.encrypted).decrypt(passphrase, self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__NETWORK))
            except _dependency('seedsigner.models.seed', 'InvalidSeedException'):
                self.run_screen(_dependency('seedsigner.gui.screens.screen', 'DireWarningScreen'), status_headline=_dependency('gettext', 'gettext')('Invalid BIP38!'), text=_dependency('gettext', 'gettext')('Could not decrypt BIP38 key.'), button_data=[_dependency('seedsigner.gui.screens.screen', 'ButtonOption')('OK')], show_back_button=False)
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('PSBTSelectSeedView'))
            self.controller.psbt_seed = key
            return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('PSBTOverviewView'))
    return PSBTBIP38PassphraseView

def _make_RejectPresentation():

    class RejectPresentation:
        """
    How one RejectCode is shown to the user, and where the flow goes afterwards.

    Every refusal used to render as the same generic "Invalid PSBT" warning carrying
    the parser's technical message. That is still the default -- `screen` is None and
    the parser's message is the body -- but a code that deserves its own severity,
    headline, or exit route gets an entry here instead of a special case in the flow.

    * screen / title / headline / text / icon / color / button: what is drawn. `text`
      of None means "use the parser's own message", which is right where the message
      names a specific offending value and wrong where fixed prose reads better.
    * tip: appended to the message, for refusals the user can actually act on.
    * clear_psbt: whether the psbt itself is discarded. False only for
      SEED_CANNOT_SIGN, which is a seed/psbt mismatch rather than a bad psbt.
    * clear_history: whether the redirect INTO this screen wipes the back stack, so
      BACK cannot walk into a half-parsed psbt. False only where the user is meant to
      step back into the flow they came from.
    * destination_name: which View to land on once the screen is dismissed. Named as a
      string because the table sits above the Views it points at.
    """

        def __init__(self, screen=None, title='Invalid PSBT', headline=None, text=None, icon=None, color=None, button_label='Done', tip=None, clear_psbt=True, clear_history=True, destination_name='MainMenuView'):
            self.screen = screen
            self.title = title
            self.headline = headline
            self.text = text
            self.icon = icon
            self.color = color
            self.button_label = button_label
            self.tip = tip
            self.clear_psbt = clear_psbt
            self.clear_history = clear_history
            self.destination_name = destination_name
    return RejectPresentation

def _build_presentations():
    return {_dependency('seedsigner.models.psbt_parser', 'RejectCode').CHANGE_INDEX_TOO_FAR: _resolve('RejectPresentation')(tip=_dependency('seedsigner.helpers.l10n', 'mark_for_translation')('See Change Gap Limit in Settings.')), _dependency('seedsigner.models.psbt_parser', 'RejectCode').FORGED_OUTPUT_OWNERSHIP: _resolve('RejectPresentation')(screen=_dependency('seedsigner.gui.screens.screen', 'DireWarningScreen'), title=_dependency('seedsigner.helpers.l10n', 'mark_for_translation')('Suspicious Transaction'), headline=_dependency('seedsigner.helpers.l10n', 'mark_for_translation')('Likely an Attack!'), text=_dependency('seedsigner.helpers.l10n', 'mark_for_translation')("The transaction's change/self-transfer outputs are not going back to your wallet."), button_label=_dependency('seedsigner.helpers.l10n', 'mark_for_translation')('Discard transaction')), _dependency('seedsigner.models.psbt_parser', 'RejectCode').SURPLUS_DERIVATIONS: _resolve('RejectPresentation')(screen=_dependency('seedsigner.gui.screens.screen', 'DireWarningScreen'), title=_dependency('seedsigner.helpers.l10n', 'mark_for_translation')('Suspicious Transaction'), headline=_dependency('seedsigner.helpers.l10n', 'mark_for_translation')('Likely an Attack!'), text=_dependency('seedsigner.helpers.l10n', 'mark_for_translation')('This transaction makes contradictory claims about which keys are yours.'), button_label=_dependency('seedsigner.helpers.l10n', 'mark_for_translation')('Discard transaction')), _dependency('seedsigner.models.psbt_parser', 'RejectCode').MIXED_DERIVATION_MAPS: _resolve('RejectPresentation')(screen=_dependency('seedsigner.gui.screens.screen', 'DireWarningScreen'), title=_dependency('seedsigner.helpers.l10n', 'mark_for_translation')('Suspicious Transaction'), headline=_dependency('seedsigner.helpers.l10n', 'mark_for_translation')('Likely an Attack!'), text=_dependency('seedsigner.helpers.l10n', 'mark_for_translation')('This transaction makes contradictory claims about which keys are yours.'), button_label=_dependency('seedsigner.helpers.l10n', 'mark_for_translation')('Discard transaction')), _dependency('seedsigner.models.psbt_parser', 'RejectCode').MISLABELED_OUTPUT_OWNERSHIP: _resolve('RejectPresentation')(screen=_dependency('seedsigner.gui.screens.screen', 'WarningScreen'), title=_dependency('seedsigner.helpers.l10n', 'mark_for_translation')('Transaction Problem'), text=_dependency('seedsigner.helpers.l10n', 'mark_for_translation')("An output that pays this seed is labelled as another wallet's. The transaction misdescribes itself."), button_label=_dependency('seedsigner.helpers.l10n', 'mark_for_translation')('Discard transaction')), _dependency('seedsigner.models.psbt_parser', 'RejectCode').WRONG_VERSION_FIELD: _resolve('RejectPresentation')(screen=_dependency('seedsigner.gui.screens.screen', 'DireWarningScreen'), title=_dependency('seedsigner.helpers.l10n', 'mark_for_translation')('Suspicious Transaction'), headline=_dependency('seedsigner.helpers.l10n', 'mark_for_translation')('Likely an Attack!'), text=_dependency('seedsigner.helpers.l10n', 'mark_for_translation')('This transaction describes itself twice, and the two versions may not match.'), button_label=_dependency('seedsigner.helpers.l10n', 'mark_for_translation')('Discard transaction')), _dependency('seedsigner.models.psbt_parser', 'RejectCode').MALFORMED_ENCODING: _resolve('RejectPresentation')(screen=_dependency('seedsigner.gui.screens.screen', 'WarningScreen'), title=_dependency('seedsigner.helpers.l10n', 'mark_for_translation')('Transaction Problem'), text=_dependency('seedsigner.helpers.l10n', 'mark_for_translation')('This transaction is encoded in a way that other software could read differently.'), button_label=_dependency('seedsigner.helpers.l10n', 'mark_for_translation')('Discard transaction')), _dependency('seedsigner.models.psbt_parser', 'RejectCode').INCONSISTENT_FINGERPRINTS: _resolve('RejectPresentation')(screen=_dependency('seedsigner.gui.screens.screen', 'WarningScreen'), title=_dependency('seedsigner.helpers.l10n', 'mark_for_translation')('Transaction Problem'), text=_dependency('seedsigner.helpers.l10n', 'mark_for_translation')("This transaction's records disagree about which wallet a key comes from."), button_label=_dependency('seedsigner.helpers.l10n', 'mark_for_translation')('Discard transaction')), _dependency('seedsigner.models.psbt_parser', 'RejectCode').FORGED_INPUT_OWNERSHIP: _resolve('RejectPresentation')(screen=_dependency('seedsigner.gui.screens.screen', 'WarningScreen'), title=_dependency('seedsigner.helpers.l10n', 'mark_for_translation')('Transaction Problem'), text=_dependency('seedsigner.helpers.l10n', 'mark_for_translation')('This transaction incorrectly claims that its input(s) belong to this seed.'), button_label=_dependency('seedsigner.helpers.l10n', 'mark_for_translation')('Discard transaction')), _dependency('seedsigner.models.psbt_parser', 'RejectCode').SEED_CANNOT_SIGN: _resolve('RejectPresentation')(screen=_dependency('seedsigner.gui.screens.screen', 'LargeIconStatusScreen'), title=_dependency('seedsigner.helpers.l10n', 'mark_for_translation')("Seed Can't Sign"), text=_dependency('seedsigner.helpers.l10n', 'mark_for_translation')('None of the inputs in this transaction are controlled by this seed.'), icon=_dependency('seedsigner.gui.components', 'SeedSignerIconConstants').INFO, color=_dependency('seedsigner.gui.components', 'GUIConstants').INFO_COLOR, button_label=_dependency('seedsigner.helpers.l10n', 'mark_for_translation')('Select a different seed'), clear_psbt=False, clear_history=False, destination_name='PSBTSelectSeedView')}

def _make_PSBTRefusalView():

    class PSBTRefusalView(_dependency('seedsigner.views.view', 'View')):
        """
    Renders one refused psbt, per REJECT_PRESENTATION, and routes onward.

    Reached by redirect from PSBTOverviewView, so each refusal is a real View: it can be
    screenshotted, its strings extracted for translation, and its routing asserted in a
    flow test. Subclasses below fix `code` so the named cases can be referred to
    directly.
    """
        code = None

        def __init__(self, code=None, message=None):
            super().__init__()
            self.code = code if code is not None else self.code
            self.message = message
            self.presentation = _presentations().get(self.code, _resolve('RejectPresentation')())

        def run(self):
            p = self.presentation
            if p.text is not None:
                text = _dependency('gettext', 'gettext')(p.text)
            else:
                text = self.message or _dependency('gettext', 'gettext')('This transaction could not be verified.')
                if p.tip:
                    text += '\n' + _dependency('gettext', 'gettext')(p.tip)
            kwargs = dict(title=_dependency('gettext', 'gettext')(p.title), status_headline=_dependency('gettext', 'gettext')(p.headline) if p.headline else None, text=text, button_data=[_dependency('seedsigner.gui.screens.screen', 'ButtonOption')(p.button_label)], show_back_button=False)
            if p.icon:
                kwargs['status_icon_name'] = p.icon
            if p.color:
                kwargs['status_color'] = p.color
            self.run_screen(p.screen or _dependency('seedsigner.gui.screens.screen', 'WarningScreen'), **kwargs)
            if p.clear_psbt:
                self.controller.psbt = None
            self.controller.psbt_parser = None
            self.controller.psbt_seed = None
            self.controller.psbt_sign_with_satochip = False
            return _dependency('seedsigner_port.navigation', 'Destination')(_destination_view(p.destination_name), clear_history=True)
    return PSBTRefusalView

def _make_PSBTOutputOwnershipClaimFailedView():

    class PSBTOutputOwnershipClaimFailedView(_resolve('PSBTRefusalView')):
        """
    An output claims a key this seed does not derive -- how a fake change output is
    dressed up as the user's own. Shows a dire warning and discards the psbt.
    """
        code = _dependency('seedsigner.models.psbt_parser', 'RejectCode').FORGED_OUTPUT_OWNERSHIP
        DISCARD = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Discard transaction')
    return PSBTOutputOwnershipClaimFailedView

def _make_PSBTInputOwnershipClaimFailedView():

    class PSBTInputOwnershipClaimFailedView(_resolve('PSBTRefusalView')):
        """
    An input claims a key this seed does not derive. Unsignable rather than dangerous,
    so a plain warning; the psbt is still discarded.
    """
        code = _dependency('seedsigner.models.psbt_parser', 'RejectCode').FORGED_INPUT_OWNERSHIP
        DISCARD = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Discard transaction')
    return PSBTInputOwnershipClaimFailedView

def _make_PSBTSeedCannotSignView():

    class PSBTSeedCannotSignView(_resolve('PSBTRefusalView')):
        """
    This seed can't sign any of the psbt's inputs. Routes back to seed selection, keeping
    the psbt, so the user can pick another.
    """
        code = _dependency('seedsigner.models.psbt_parser', 'RejectCode').SEED_CANNOT_SIGN
        SELECT_DIFFERENT_SEED = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Select a different seed')
    return PSBTSeedCannotSignView

def refusal_destination(error):
    """Where a refused psbt goes: the View for its code, carrying its message."""
    presentation = _presentations().get(error.code, _resolve('RejectPresentation')())
    return _dependency('seedsigner_port.navigation', 'Destination')(_refusal_views().get(error.code, _resolve('PSBTRefusalView')), view_args=dict(code=error.code, message=str(error)), clear_history=presentation.clear_history)

def seedless_multisig_parser(controller, settings):
    """
    Parse the loaded multisig psbt with no key to verify against, for card signing:
    the card holds the key, so there is no BIP32 tree here. Change can then only be
    identified by the loaded descriptor, if any. Raises InvalidPSBTError on refusal.
    """
    parser = _dependency('seedsigner.models.psbt_parser', 'PSBTParser')(controller.psbt, network=settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__NETWORK), multisig_descriptor=controller.multisig_wallet_descriptor)
    parser.parse()
    return parser

def _make_PSBTOverviewView():

    class PSBTOverviewView(_dependency('seedsigner.views.view', 'View')):

        def __init__(self):
            super().__init__()
            self.loading_screen = None
            if not self.controller.psbt_parser and self.controller.psbt_seed is None and self.controller.psbt_sign_with_satochip:
                try:
                    self.controller.psbt_parser = seedless_multisig_parser(self.controller, self.settings)
                except _dependency('seedsigner.models.psbt_parser', 'InvalidPSBTError') as e:
                    pass
                    self.set_redirect(refusal_destination(e))
                return
            if not self.controller.psbt_parser or self.controller.psbt_parser.seed != self.controller.psbt_seed:
                self.loading_screen = _dependency('seedsigner.gui.screens.screen', 'LoadingScreenThread')(text=_dependency('gettext', 'gettext')('Parsing PSBT...'))
                self.loading_screen.start()
                try:
                    self.controller.psbt_parser = _dependency('seedsigner.models.psbt_parser', 'PSBTParser')(self.controller.psbt, seed=self.controller.psbt_seed, network=self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__NETWORK), reference_time=getattr(self.controller, 'psbt_source_time', None), block_anchor=(_dependency('seedsigner.controller', 'Controller').RELEASE_BLOCK_HEIGHT, _dependency('seedsigner.controller', 'Controller').RELEASE_BLOCK_TIME), multisig_descriptor=self.controller.multisig_wallet_descriptor)
                except _dependency('seedsigner.models.psbt_parser', 'InvalidPSBTError') as e:
                    pass
                    self.set_redirect(refusal_destination(e))
                    return
                finally:
                    self.loading_screen.stop()

        def run(self):
            psbt_parser = self.controller.psbt_parser
            change_data = psbt_parser.change_data
            "\n            change_data = [\n                {\n                    'output_index': 0,\n                    'address': 'bc1q............',\n                    'amount': 397621401,\n                    'verified_derivation_path':\n                        [2147483696, 2147483649, 2147483648, 2147483650, 1, 0],\n                }, {},\n            ]\n        "
            num_change_outputs = 0
            num_self_transfer_outputs = 0
            for change_output in change_data:
                if _dependency('seedsigner.models.psbt_parser', 'PSBTParser').is_change_branch(change_output['verified_derivation_path']):
                    num_change_outputs += 1
                else:
                    num_self_transfer_outputs += 1
            selected_menu_num = self.run_screen(_dependency('seedsigner.gui.screens.psbt_screens', 'PSBTOverviewScreen'), spend_amount=psbt_parser.spend_amount, change_amount=psbt_parser.change_amount, fee_amount=psbt_parser.fee_amount, num_inputs=psbt_parser.num_inputs, num_self_transfer_outputs=num_self_transfer_outputs, num_change_outputs=num_change_outputs, destination_addresses=psbt_parser.destination_addresses, has_op_return=psbt_parser.op_return_data is not None, is_high_fee_tx=psbt_parser.is_high_fee)
            if selected_menu_num == _dependency('seedsigner.gui.screens.screen', 'RET_CODE__BACK_BUTTON'):
                self.controller.psbt_seed = None
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            if psbt_parser.unidentified_change_outputs:
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('PSBTIdentifyChangeView'))
            return post_overview_destination(psbt_parser)
    return PSBTOverviewView

def pending_risk_warnings(psbt_parser):
    """The risk warnings PSBTRiskWarningView still has to show."""
    warnings = psbt_parser.risk_warnings - _dependency('seedsigner.models.psbt_parser', 'RiskWarning').INFORMATIONAL
    if psbt_parser.is_high_fee:
        warnings -= {_dependency('seedsigner.models.psbt_parser', 'RiskWarning').HIGH_FEE}
    return warnings

def post_overview_destination(psbt_parser, skip_current_view=False, high_fee_acknowledged=False):
    """Where review continues once the overview (and any interstitial after it) is done."""
    if psbt_parser.is_high_fee and (not high_fee_acknowledged):
        return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('PSBTHighFeeWarningView'), view_args={'warning_threshold_percent': psbt_parser.HIGH_FEES_WARNING_THRESHOLD}, skip_current_view=skip_current_view)
    if pending_risk_warnings(psbt_parser):
        return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('PSBTRiskWarningView'), skip_current_view=skip_current_view)
    if psbt_parser.policy == None:
        return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('PSBTUnsupportedScriptTypeWarningView'), skip_current_view=skip_current_view)
    elif psbt_parser.change_amount == 0:
        return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('PSBTNoChangeWarningView'), skip_current_view=skip_current_view)
    else:
        return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('PSBTMathView'), skip_current_view=skip_current_view)

def _make_PSBTIdentifyChangeView():

    class PSBTIdentifyChangeView(_dependency('seedsigner.views.view', 'View')):
        """
    Some output looks like this multisig wallet's change, but the psbt carries no global
    xpubs to tie its other cosigner keys to the inputs' wallet. A different wallet that
    shares our key would look the same, so PSBTParser shows it as a payment. Only the
    wallet's descriptor can identify it as change.
    """
        LOAD_DESCRIPTOR = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Load descriptor')
        CONTINUE_AS_PAYMENT = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Continue as payment')
        CONTINUE = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Continue')

        def run(self):
            psbt_parser = self.controller.psbt_parser
            if not psbt_parser:
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'MainMenuView'))
            if self.controller.multisig_wallet_descriptor:
                text = _dependency('gettext', 'gettext')("The loaded descriptor doesn't identify it. Shown as a payment.")
                button_data = [self.CONTINUE]
            else:
                text = _dependency('gettext', 'gettext')('Load descriptor to identify change.')
                button_data = [self.LOAD_DESCRIPTOR, self.CONTINUE_AS_PAYMENT]
            selected_menu_num = self.run_screen(_dependency('seedsigner.gui.screens.screen', 'WarningScreen'), status_headline=_dependency('gettext', 'gettext')('Change Not Identified'), text=text, button_data=button_data)
            if selected_menu_num == _dependency('seedsigner.gui.screens.screen', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            if button_data[selected_menu_num] == self.LOAD_DESCRIPTOR:
                self.controller.resume_main_flow = _dependency('seedsigner.controller', 'Controller').FLOW__PSBT
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.seed_views', 'LoadMultisigWalletDescriptorView'))
            return post_overview_destination(psbt_parser, skip_current_view=True)
    return PSBTIdentifyChangeView

def _make_PSBTRiskWarningView():

    class PSBTRiskWarningView(_dependency('seedsigner.views.view', 'View')):
        """
        Everything PSBTParser flagged for review: conditions that don't make the
        transaction invalid, but that a user would not want to approve without
        being told.
    """
        RISK_TEXT = {_dependency('seedsigner.models.psbt_parser', 'RiskWarning').HIGH_FEE: _dependency('seedsigner.helpers.l10n', 'mark_for_translation')('The fee is an unusually large share of this transaction.'), _dependency('seedsigner.models.psbt_parser', 'RiskWarning').HIGH_FEE_RATE: _dependency('seedsigner.helpers.l10n', 'mark_for_translation')('The fee rate is high compared to recent blocks.'), _dependency('seedsigner.models.psbt_parser', 'RiskWarning').UNVERIFIED_INPUT_AMOUNTS: _dependency('seedsigner.helpers.l10n', 'mark_for_translation')('Input amounts are unproven (no previous transactions); the fee may be higher than shown.'), _dependency('seedsigner.models.psbt_parser', 'RiskWarning').DUST_OUTPUT: _dependency('seedsigner.helpers.l10n', 'mark_for_translation')('One output is below the dust threshold and may be unspendable.'), _dependency('seedsigner.models.psbt_parser', 'RiskWarning').FUTURE_LOCKTIME: _dependency('seedsigner.helpers.l10n', 'mark_for_translation')('This transaction cannot confirm until a future date.'), _dependency('seedsigner.models.psbt_parser', 'RiskWarning').LOCKTIME_FAR_FUTURE: _dependency('seedsigner.helpers.l10n', 'mark_for_translation')('This transaction is locked for years and cannot confirm until then.'), _dependency('seedsigner.models.psbt_parser', 'RiskWarning').RELATIVE_TIMELOCK: _dependency('seedsigner.helpers.l10n', 'mark_for_translation')('An input is time-locked and cannot be spent yet.'), _dependency('seedsigner.models.psbt_parser', 'RiskWarning').SCRIPT_TIMELOCK: _dependency('seedsigner.helpers.l10n', 'mark_for_translation')('An output is time-locked by its script; those funds cannot be spent until later.'), _dependency('seedsigner.models.psbt_parser', 'RiskWarning').RBF: _dependency('seedsigner.helpers.l10n', 'mark_for_translation')('This transaction is marked replaceable (RBF).')}

        def run(self):
            psbt_parser = self.controller.psbt_parser
            if not psbt_parser:
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'MainMenuView'))
            pending = pending_risk_warnings(psbt_parser)
            messages = []
            for code in self.RISK_TEXT:
                if code not in pending:
                    continue
                messages.append(_dependency('gettext', 'gettext')(self.RISK_TEXT[code]))
            selected_menu_num = self.run_screen(_dependency('seedsigner.gui.screens.screen', 'WarningScreen'), status_headline=_dependency('gettext', 'gettext')('Review Carefully!'), text='\n\n'.join(messages), button_data=[_dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Continue')])
            if selected_menu_num == _dependency('seedsigner.gui.screens.screen', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            if psbt_parser.policy == None:
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('PSBTUnsupportedScriptTypeWarningView'), skip_current_view=True)
            elif psbt_parser.change_amount == 0:
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('PSBTNoChangeWarningView'), skip_current_view=True)
            return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('PSBTMathView'), skip_current_view=True)
    return PSBTRiskWarningView

def _make_PSBTUnsupportedScriptTypeWarningView():

    class PSBTUnsupportedScriptTypeWarningView(_dependency('seedsigner.views.view', 'View')):

        def run(self):
            selected_menu_num = self.run_screen(_dependency('seedsigner.gui.screens.screen', 'WarningScreen'), status_headline=_dependency('gettext', 'gettext')('Unsupported Script Type!'), text=_dependency('gettext', 'gettext')('Transaction has unsupported input script type, please verify your change addresses.'), button_data=[_dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Continue')])
            if selected_menu_num == _dependency('seedsigner.gui.screens.screen', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('PSBTAddressDetailsView'), view_args={'address_num': 0}, skip_current_view=True)
    return PSBTUnsupportedScriptTypeWarningView

def _make_PSBTNoChangeWarningView():

    class PSBTNoChangeWarningView(_dependency('seedsigner.views.view', 'View')):

        def run(self):
            selected_menu_num = self.run_screen(_dependency('seedsigner.gui.screens.screen', 'WarningScreen'), status_headline=_dependency('gettext', 'gettext')('Full Spend!'), text=_dependency('gettext', 'gettext')('This transaction spends its entire input value. No change is coming back to your wallet.'), button_data=[_dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Continue')])
            if selected_menu_num == _dependency('seedsigner.gui.screens.screen', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('PSBTMathView'), skip_current_view=True)
    return PSBTNoChangeWarningView

def _make_PSBTHighFeeWarningView():

    class PSBTHighFeeWarningView(_dependency('seedsigner.views.view', 'View')):

        def __init__(self, warning_threshold_percent):
            super().__init__()
            self.warning_threshold_percent = warning_threshold_percent

        def run(self):
            selected_menu_num = self.run_screen(_dependency('seedsigner.gui.screens.screen', 'DireWarningScreen'), status_headline=_dependency('gettext', 'gettext')('High Fee!'), text=_dependency('gettext', 'gettext')('This transaction has a fee higher than {}% of the total output value (excluding change).').format(self.warning_threshold_percent), button_data=[_dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Continue')])
            if selected_menu_num == _dependency('seedsigner.gui.screens.screen', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            return post_overview_destination(self.controller.psbt_parser, skip_current_view=True, high_fee_acknowledged=True)
    return PSBTHighFeeWarningView

def _make_PSBTMathView():

    class PSBTMathView(_dependency('seedsigner.views.view', 'View')):
        """
        Follows the Overview pictogram. Shows:
        + total input value
        - recipients' value
        - fees
        -------------------
        + change value
    """

        def run(self):
            psbt_parser = self.controller.psbt_parser
            if not psbt_parser:
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'MainMenuView'))
            selected_menu_num = self.run_screen(_dependency('seedsigner.gui.screens.psbt_screens', 'PSBTMathScreen'), input_amount=psbt_parser.input_amount, num_inputs=psbt_parser.num_inputs, spend_amount=psbt_parser.spend_amount + psbt_parser.op_return_amount, num_recipients=psbt_parser.num_destinations, fee_amount=psbt_parser.fee_amount, change_amount=psbt_parser.change_amount, is_high_fee_tx=psbt_parser.is_high_fee)
            if selected_menu_num == _dependency('seedsigner.gui.screens.screen', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            if len(psbt_parser.destination_addresses) > 0:
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('PSBTAddressDetailsView'), view_args={'address_num': 0})
            else:
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('PSBTChangeDetailsView'), view_args={'change_address_num': 0})
    return PSBTMathView

def _make_PSBTAddressDetailsView():

    class PSBTAddressDetailsView(_dependency('seedsigner.views.view', 'View')):
        """
        Shows the recipient's address and amount they will receive
    """

        def __init__(self, address_num):
            super().__init__()
            self.address_num = address_num

        def run(self):
            psbt_parser = self.controller.psbt_parser
            if not psbt_parser:
                raise Exception('Routing error')
            title = _dependency('gettext', 'gettext')('Will Send')
            if psbt_parser.num_destinations > 1:
                title += ' (#{0})'.format(self.address_num + 1)
            button_data = []
            if self.address_num < psbt_parser.num_destinations - 1:
                button_data.append(_dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Next recipient'))
            else:
                button_data.append(_dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Next'))
            selected_menu_num = self.run_screen(_dependency('seedsigner.gui.screens.psbt_screens', 'PSBTAddressDetailsScreen'), title=title, button_data=button_data, address=psbt_parser.destination_addresses[self.address_num], amount=psbt_parser.destination_amounts[self.address_num])
            if selected_menu_num == _dependency('seedsigner.gui.screens.screen', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            if self.address_num < len(psbt_parser.destination_addresses) - 1:
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('PSBTAddressDetailsView'), view_args={'address_num': self.address_num + 1})
            elif psbt_parser.change_amount > 0:
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('PSBTChangeDetailsView'), view_args={'change_address_num': 0})
            elif psbt_parser.op_return_data:
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('PSBTOpReturnView'))
            else:
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('PSBTFinalizeView'))
    return PSBTAddressDetailsView

def _make_PSBTChangeDetailsView():

    class PSBTChangeDetailsView(_dependency('seedsigner.views.view', 'View')):
        NEXT = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Next')
        SKIP_VERIFICATION = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Skip verification')
        VERIFY_MULTISIG = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Verify multisig change')

        def __init__(self, change_address_num):
            super().__init__()
            self.change_address_num = change_address_num

        def run(self):
            psbt_parser = self.controller.psbt_parser
            if not psbt_parser:
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'MainMenuView'))
            change_data = psbt_parser.get_change_data(change_num=self.change_address_num)
            "\n            change_data:\n            {\n                'output_index': 0,\n                'address': 'bc1q............',\n                'amount': 397621401,\n                'verified_derivation_path':\n                    [2147483696, 2147483649, 2147483648, 2147483650, 1, 0],\n            }\n        "
            verified_derivation_path = change_data.get('verified_derivation_path')
            path_ints = list(verified_derivation_path) if verified_derivation_path else []
            if self.controller.psbt_seed:
                seed_fingerprint = self.controller.psbt_seed.get_fingerprint(self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__NETWORK))
            else:
                master_fp = getattr(psbt_parser, 'master_fingerprint', None)
                seed_fingerprint = _dependency('binascii', 'hexlify')(master_fp).decode() if master_fp else None
            is_change_derivation_path = _dependency('seedsigner.models.psbt_parser', 'PSBTParser').is_change_branch(path_ints)
            derivation_path_addr_index = path_ints[-1] & 2147483647 if path_ints else 0
            if is_change_derivation_path:
                title = _dependency('gettext', 'gettext')('Your Change')
            else:
                title = _dependency('gettext', 'gettext')('Self-Transfer')
                self.VERIFY_MULTISIG.button_label = _dependency('gettext', 'gettext')('Verify multisig addr')
            is_change_addr_verified = False
            if psbt_parser.is_multisig:
                if self.controller.multisig_wallet_descriptor:
                    is_change_addr_verified = psbt_parser.verify_multisig_output(self.controller.multisig_wallet_descriptor, change_num=self.change_address_num)
                    if not is_change_addr_verified:
                        self.controller.multisig_wallet_descriptor = None
                        self.run_screen(_dependency('seedsigner.gui.screens.screen', 'WarningScreen'), title=_dependency('gettext', 'gettext')('Descriptor mismatch'), status_icon_name=_dependency('seedsigner.gui.components', 'SeedSignerIconConstants').WARNING, status_headline=_dependency('gettext', 'gettext')('Descriptor cleared'), text=_dependency('gettext', 'gettext')('Loaded multisig wallet descriptor does not match this PSBT. Load the correct descriptor or skip verification to continue.'), show_back_button=False, button_data=[_dependency('seedsigner.gui.screens.screen', 'ButtonOption')(_dependency('gettext', 'gettext')('OK'))])
                        return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('PSBTChangeDetailsView'), view_args={'change_address_num': self.change_address_num}, skip_current_view=True)
                    button_data = [self.NEXT]
                else:
                    button_data = [self.VERIFY_MULTISIG, self.SKIP_VERIFICATION]
            else:
                try:
                    if is_change_derivation_path:
                        loading_screen_text = _dependency('gettext', 'gettext')('Verifying Change...')
                    else:
                        loading_screen_text = _dependency('gettext', 'gettext')('Verifying Self-Transfer...')
                    loading_screen = _dependency('seedsigner.gui.screens.screen', 'LoadingScreenThread')(text=loading_screen_text)
                    loading_screen.start()
                    pubkey = _dependency('embit', 'script').address_to_scriptpubkey(change_data['address'])
                    script_type = pubkey.script_type()
                    change_path = _dependency('embit', 'bip32').path_to_str(path_ints[-2:])[2:] if len(path_ints) >= 2 else ''
                    wallet_path_list = path_ints[:-2]
                    wallet_path = _dependency('embit', 'bip32').path_to_str(wallet_path_list)
                    if self.controller.psbt_seed:
                        xpub = self.controller.psbt_seed.get_xpub(wallet_path=wallet_path, network=self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__NETWORK))
                        xpub_key = xpub.derive(change_path).key
                    else:
                        rel_wallet_path_list = wallet_path_list[len(psbt_parser.root_path):]
                        rel_wallet_path = _dependency('embit', 'bip32').path_to_str(rel_wallet_path_list)[2:] if rel_wallet_path_list else ''
                        xpub = psbt_parser.root.derive(rel_wallet_path) if rel_wallet_path else psbt_parser.root
                        xpub_key = xpub.derive(change_path).key
                    network = self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__NETWORK)
                    scriptcall = getattr(_dependency('embit', 'script'), script_type)
                    if script_type == 'p2sh':
                        calc_address = _dependency('embit', 'script').p2sh(_dependency('embit', 'script').p2wpkh(xpub_key)).address(network=_dependency('embit.networks', 'NETWORKS')[_dependency('seedsigner.models.settings', 'SettingsConstants').map_network_to_embit(network)])
                    else:
                        calc_address = scriptcall(xpub_key).address(network=_dependency('embit.networks', 'NETWORKS')[_dependency('seedsigner.models.settings', 'SettingsConstants').map_network_to_embit(network)])
                    if change_data['address'] == calc_address:
                        is_change_addr_verified = True
                        button_data = [self.NEXT]
                finally:
                    loading_screen.stop()
            if is_change_addr_verified == False and (not psbt_parser.is_multisig or self.controller.multisig_wallet_descriptor is not None):
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('PSBTAddressVerificationFailedView'), view_args=dict(is_change=is_change_derivation_path, is_multisig=psbt_parser.is_multisig), clear_history=True)
            selected_menu_num = self.run_screen(_dependency('seedsigner.gui.screens.psbt_screens', 'PSBTChangeDetailsScreen'), title=title, button_data=button_data, address=change_data.get('address'), amount=change_data.get('amount'), is_multisig=psbt_parser.is_multisig, fingerprint=seed_fingerprint or '', derivation_path=_dependency('embit', 'bip32').path_to_str(path_ints) if path_ints else '', is_change_derivation_path=is_change_derivation_path, derivation_path_addr_index=derivation_path_addr_index, is_change_addr_verified=is_change_addr_verified)
            if selected_menu_num == _dependency('seedsigner.gui.screens.screen', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            elif button_data[selected_menu_num] == self.NEXT or button_data[selected_menu_num] == self.SKIP_VERIFICATION:
                if self.change_address_num < psbt_parser.num_change_outputs - 1:
                    return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('PSBTChangeDetailsView'), view_args={'change_address_num': self.change_address_num + 1})
                elif psbt_parser.op_return_data:
                    return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('PSBTOpReturnView'))
                else:
                    return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('PSBTFinalizeView'))
            elif button_data[selected_menu_num] == self.VERIFY_MULTISIG:
                self.controller.resume_main_flow = _dependency('seedsigner.controller', 'Controller').FLOW__PSBT
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.seed_views', 'LoadMultisigWalletDescriptorView'))
    return PSBTChangeDetailsView

def _make_PSBTAddressVerificationFailedView():

    class PSBTAddressVerificationFailedView(_dependency('seedsigner.views.view', 'View')):
        """
    Reached when a change or self-transfer output fails address verification. Shows a dire
    warning and discards the psbt to the main menu.
    """

        def __init__(self, is_change=True, is_multisig=False):
            super().__init__()
            self.is_change = is_change
            self.is_multisig = is_multisig

        def run(self):
            if self.is_multisig:
                text = _dependency('gettext', 'gettext')("Transaction's {} address could not be verified from wallet descriptor.").format(_dependency('gettext', 'gettext')('change') if self.is_change else _dependency('gettext', 'gettext')('self-transfer'))
            else:
                text = _dependency('gettext', 'gettext')("Transaction's {} address could not be generated from your seed.").format(_dependency('gettext', 'gettext')('change') if self.is_change else _dependency('gettext', 'gettext')('self-transfer'))
            self.run_screen(_dependency('seedsigner.gui.screens.screen', 'DireWarningScreen'), title=_dependency('gettext', 'gettext')('Suspicious Transaction'), status_headline=_dependency('gettext', 'gettext')('Address Verification Failed'), text=text, button_data=[_dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Discard transaction')], show_back_button=False)
            return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'MainMenuView'), clear_history=True)
    return PSBTAddressVerificationFailedView

def _make_PSBTOpReturnView():

    class PSBTOpReturnView(_dependency('seedsigner.views.view', 'View')):
        """
        Shows the OP_RETURN data, one output at a time.
    """

        def __init__(self, op_return_num=0):
            super().__init__()
            self.op_return_num = op_return_num

        def run(self):
            psbt_parser = self.controller.psbt_parser
            if not psbt_parser:
                raise Exception('Routing error')
            title = _dependency('gettext', 'gettext')('OP_RETURN')
            button_data = [_dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Next')]
            selected_menu_num = self.run_screen(_dependency('seedsigner.gui.screens.psbt_screens', 'PSBTOpReturnScreen'), title=title, button_data=button_data, op_return_data=psbt_parser.op_return_payloads[self.op_return_num])
            if selected_menu_num == _dependency('seedsigner.gui.screens.screen', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            if self.op_return_num < len(psbt_parser.op_return_payloads) - 1:
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('PSBTOpReturnView'), view_args={'op_return_num': self.op_return_num + 1})
            return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('PSBTFinalizeView'))
    return PSBTOpReturnView

def _make_PSBTFinalizeView():

    class PSBTFinalizeView(_dependency('seedsigner.views.view', 'View')):
        """
    """
        APPROVE_PSBT = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Approve transaction')

        @staticmethod
        def _locktime_text(psbt_parser):
            """
        A one-line, human-readable nLockTime for the approval screen, or None
        when no locktime is actually in force.

        nLockTime comes in two encodings and only one of them was ever visible.
        A timestamp locktime is compared against the clock and warned about; a
        block-height locktime was not checked at all, so an attacker who wanted a
        long lock simply used the height form and nothing was shown. Both forms
        delay confirmation identically, so both are stated here.

        Heights are converted to an approximate date rather than displayed raw:
        "locked until block 1,000,000" is not something a user can act on without
        knowing the current tip, which the device does not have. The conversion
        anchors on Controller.RELEASE_BLOCK_HEIGHT and assumes 10-minute blocks.

        This states rather than judges. The device has no RTC, so it cannot tell
        whether a date is in the future, and a stale anchor means the estimate can
        drift. A user making a payment today can tell that "~Mar 2031" is wrong;
        a heuristic with no trustworthy clock cannot.
        """
            if psbt_parser is None or not psbt_parser.locktime_is_enforced:
                return None
            locktime = psbt_parser.locktime
            if not locktime:
                return None
            if locktime >= _dependency('seedsigner.models.psbt_parser', 'LOCKTIME_TIMESTAMP_THRESHOLD'):
                when = _dependency('seedsigner_port.psbt_clock', None).gmtime(locktime)
                exact = True
            else:
                estimated = _dependency('seedsigner.controller', 'Controller').RELEASE_BLOCK_TIME + (locktime - _dependency('seedsigner.controller', 'Controller').RELEASE_BLOCK_HEIGHT) * _dependency('seedsigner.controller', 'Controller').SECONDS_PER_BLOCK
                if estimated <= 0:
                    return None
                when = _dependency('seedsigner_port.psbt_clock', None).gmtime(estimated)
                exact = False
            stamp = _dependency('seedsigner_port.psbt_clock', None).strftime('%b %Y', when)
            if exact:
                return _dependency('gettext', 'gettext')('Locked until {}').format(stamp)
            return _dependency('gettext', 'gettext')('Locked until ~{}').format(stamp)

        def run(self):
            psbt_parser = self.controller.psbt_parser
            psbt = self.controller.psbt
            if psbt is None:
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'MainMenuView'))
            if not self.controller.psbt_sign_with_satochip and psbt_parser is None:
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'MainMenuView'))
            selected_menu_num = self.run_screen(_dependency('seedsigner.gui.screens.psbt_screens', 'PSBTFinalizeScreen'), button_data=[self.APPROVE_PSBT], is_rbf=psbt_parser is not None and _dependency('seedsigner.models.psbt_parser', 'RiskWarning').RBF in psbt_parser.risk_warnings, locktime_text=self._locktime_text(psbt_parser))
            if selected_menu_num == _dependency('seedsigner.gui.screens.screen', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            sig_cnt = _dependency('seedsigner.models.psbt_parser', 'PSBTParser').sig_count(psbt)
            pass
            connector = None
            if self.controller.psbt_sign_with_satochip:
                connector = _dependency('seedsigner.helpers', 'seedkeeper_utils').init_satochip(self, init_card_filter=['satochip'])
                if not connector:
                    pass
                    return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('PSBTFinalizeView'))
                pass
            loading = _dependency('seedsigner.gui.screens.screen', 'LoadingScreenThread')(text=_dependency('gettext', 'gettext')('Signing PSBT...'))
            loading.start()
            try:
                sign_result = None
                if self.controller.psbt_sign_with_satochip:
                    is_keycard = getattr(connector, 'is_keycard_backend', False)
                    retry_timeout = getattr(self.controller, '_psbt_sign_retry_timeout', None)
                    if is_keycard:
                        sign_result = _dependency('seedsigner.helpers.keycard_signer', 'sign_psbt_with_keycard')(psbt, connector, timeout=retry_timeout)
                    else:
                        sign_result = _dependency('seedsigner.helpers.satochip_signer', 'sign_psbt_with_satochip')(psbt, connector, timeout=retry_timeout)
                    added = sign_result.signed_count
                    pass
                else:
                    psbt.sign_with(psbt_parser.root)
                if isinstance(self.controller.psbt_seed, _dependency('seedsigner.models.wif', 'WIFKey')):
                    tx = _dependency('embit.finalizer', 'finalize_psbt')(psbt)
                    self.controller.signed_tx_hex = tx.serialize().hex() if tx else None
                    pass
                else:
                    self.controller.signed_tx_hex = None
                trimmed_psbt = _dependency('seedsigner.models.psbt_parser', 'PSBTParser').trim(psbt)
                trimmed_sig_cnt = _dependency('seedsigner.models.psbt_parser', 'PSBTParser').sig_count(trimmed_psbt)
                pass
                try:
                    tx_preview = _dependency('embit.finalizer', 'finalize_psbt')(trimmed_psbt)
                    pass
                except FeatureUnavailable:
                    raise
                except Exception as e:
                    pass
            except FeatureUnavailable:
                raise
            except Exception:
                if self.controller.psbt_sign_with_satochip:
                    pass
                    return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('PSBTFinalizeView'))
                raise
            finally:
                loading.stop()
            if sig_cnt == _dependency('seedsigner.models.psbt_parser', 'PSBTParser').sig_count(trimmed_psbt):
                pass
                if hasattr(self.controller, '_psbt_sign_retry_timeout'):
                    delattr(self.controller, '_psbt_sign_retry_timeout')
                if self.controller.psbt_sign_with_satochip:
                    if sign_result and sign_result.timed_out:
                        is_keycard = getattr(connector, 'is_keycard_backend', False)
                        current_timeout = self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__KEYCARD_SIGN_TIMEOUT) if is_keycard else self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__SATOCHIP_SIGN_TIMEOUT)
                        card_label = 'Keycard' if is_keycard else 'Satochip'
                        selected = self.run_screen(_dependency('seedsigner.gui.screens.screen', 'WarningScreen'), title=_dependency('gettext', 'gettext')('Signing Timeout'), status_headline=None, text='{0} signing timed out at {1}s.\n\nRetry with a higher timeout?'.format(card_label, current_timeout), button_data=[_dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Retry (higher timeout)'), _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Cancel')])
                        if selected == 0:
                            new_timeout = current_timeout + 0.75
                            self.controller._psbt_sign_retry_timeout = new_timeout
                            pass
                            return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('PSBTFinalizeView'))
                    return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('PSBTFinalizeView'))
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('PSBTSigningErrorView'))
            pass
            self.controller.psbt = trimmed_psbt
            self.controller.psbt_sign_with_satochip = False
            return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('PSBTSignedQRDisplayView'))
    return PSBTFinalizeView

def _make_PSBTSignedQRDisplayView():

    class PSBTSignedQRDisplayView(_dependency('seedsigner.views.view', 'View')):

        def run(self):
            save_path = getattr(self.controller, 'psbt_microsd_save_path', None)
            if save_path:
                signed_path = save_path.with_name(save_path.name + '.signed')
                try:
                    signed_path.parent.mkdir(parents=True, exist_ok=True)
                    signed_path.write_bytes(self.controller.psbt.serialize())
                    try:
                        display_path = str(signed_path.relative_to(_dependency('seedsigner.hardware.microsd', 'MicroSD').get_microsd_dir()))
                    except ValueError:
                        display_path = signed_path.name
                    self.run_screen(_dependency('seedsigner.gui.screens.screen', 'LargeIconStatusScreen'), title=_dependency('gettext', 'gettext')('Success'), status_headline=None, text=_dependency('gettext', 'gettext')('Saved as {}.').format(display_path), show_back_button=False, button_data=[_dependency('seedsigner.gui.screens.screen', 'ButtonOption')(_dependency('gettext', 'gettext')('Continue'))])
                except FeatureUnavailable:
                    raise
                except Exception as e:
                    pass
                    self.run_screen(_dependency('seedsigner.gui.screens.screen', 'WarningScreen'), title=_dependency('gettext', 'gettext')('Error'), status_headline=None, text=_dependency('gettext', 'gettext')('Failed to save PSBT: {}').format(str(e)), show_back_button=False, button_data=[_dependency('seedsigner.gui.screens.screen', 'ButtonOption')(_dependency('gettext', 'gettext')('OK'))])
                finally:
                    self.controller.psbt_microsd_save_path = None
                    self.controller.psbt_from_microsd = False
                    self.controller.psbt_microsd_seed_warning_shown = False
            if isinstance(self.controller.psbt_seed, _dependency('seedsigner.models.wif', 'WIFKey')) and getattr(self.controller, 'signed_tx_hex', None):
                qr_encoder = _dependency('seedsigner.models.encode_qr', 'GenericStringEncoder')(self.controller.signed_tx_hex)
            else:
                loading = _dependency('seedsigner.gui.screens.screen', 'LoadingScreenThread')(text=_dependency('gettext', 'gettext')('Encoding PSBT...'))
                loading.start()
                try:
                    qr_encoder = _dependency('seedsigner.models.encode_qr', 'UrPsbtQrEncoder')(psbt=self.controller.psbt, qr_density=self.settings.get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__QR_DENSITY))
                finally:
                    loading.stop()
            self.run_screen(_dependency('seedsigner.gui.screens.screen', 'QRDisplayScreen'), qr_encoder=qr_encoder)
            return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'MainMenuView'), clear_history=True)
    return PSBTSignedQRDisplayView

def _make_PSBTSigningErrorView():

    class PSBTSigningErrorView(_dependency('seedsigner.views.view', 'View')):
        SELECT_DIFF_SEED = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Select different seed')

        def run(self):
            psbt_parser = self.controller.psbt_parser
            if not psbt_parser:
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'MainMenuView'))
            selected_menu_num = self.run_screen(_dependency('seedsigner.gui.screens.screen', 'WarningScreen'), title=_dependency('gettext', 'gettext')('Transaction Error'), status_icon_name=_dependency('seedsigner.gui.components', 'SeedSignerIconConstants').WARNING, status_headline=_dependency('gettext', 'gettext')('Signing Failed'), text=_dependency('gettext', 'gettext')('Signing with this seed did not add a valid signature.'), button_data=[self.SELECT_DIFF_SEED])
            if selected_menu_num == 0:
                self.controller.psbt_seed = None
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('PSBTSelectSeedView'), clear_history=True)
            if selected_menu_num == _dependency('seedsigner.gui.screens.screen', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
    return PSBTSigningErrorView

_FACTORIES={'PSBTSelectSeedView':_make_PSBTSelectSeedView,'PSBTWIFEntryView':_make_PSBTWIFEntryView,'PSBTBIP38EntryView':_make_PSBTBIP38EntryView,'PSBTBIP38PassphraseView':_make_PSBTBIP38PassphraseView,'RejectPresentation':_make_RejectPresentation,'PSBTRefusalView':_make_PSBTRefusalView,'PSBTOutputOwnershipClaimFailedView':_make_PSBTOutputOwnershipClaimFailedView,'PSBTInputOwnershipClaimFailedView':_make_PSBTInputOwnershipClaimFailedView,'PSBTSeedCannotSignView':_make_PSBTSeedCannotSignView,'PSBTOverviewView':_make_PSBTOverviewView,'PSBTIdentifyChangeView':_make_PSBTIdentifyChangeView,'PSBTRiskWarningView':_make_PSBTRiskWarningView,'PSBTUnsupportedScriptTypeWarningView':_make_PSBTUnsupportedScriptTypeWarningView,'PSBTNoChangeWarningView':_make_PSBTNoChangeWarningView,'PSBTHighFeeWarningView':_make_PSBTHighFeeWarningView,'PSBTMathView':_make_PSBTMathView,'PSBTAddressDetailsView':_make_PSBTAddressDetailsView,'PSBTChangeDetailsView':_make_PSBTChangeDetailsView,'PSBTAddressVerificationFailedView':_make_PSBTAddressVerificationFailedView,'PSBTOpReturnView':_make_PSBTOpReturnView,'PSBTFinalizeView':_make_PSBTFinalizeView,'PSBTSignedQRDisplayView':_make_PSBTSignedQRDisplayView,'PSBTSigningErrorView':_make_PSBTSigningErrorView}
_CACHE={}
_PRESENTATIONS=None
_REFUSALS=None
def _resolve(name):
 if name not in _CACHE:
  if name not in _FACTORIES:raise AttributeError(name)
  _CACHE[name]=_FACTORIES[name]()
 return _CACHE[name]
def _destination_view(name):
 return _resolve(name) if name in _FACTORIES else _dependency('seedsigner.views.view',name)
def _presentations():
 global _PRESENTATIONS
 if _PRESENTATIONS is None:_PRESENTATIONS=_build_presentations()
 return _PRESENTATIONS
def _refusal_views():
 global _REFUSALS
 if _REFUSALS is None:
  classes=[_resolve(name) for name in ['PSBTOutputOwnershipClaimFailedView', 'PSBTInputOwnershipClaimFailedView', 'PSBTSeedCannotSignView']]
  _REFUSALS={cls.code:cls for cls in classes}
 return _REFUSALS
def __getattr__(name):
 if name=='REJECT_PRESENTATION':return _presentations()
 if name=='REFUSAL_VIEWS':return _refusal_views()
 return _resolve(name)
