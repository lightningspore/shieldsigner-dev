# Copyright2021 SeedSigner; MIT, see ../LICENSE.SeedSigner
# Generated from pinned original source; optional class bases resolve only on use.
from seedsigner_port.decode_platform import dependency as _dependency, FeatureUnavailable
from seedsigner_port.navigation import Destination


def finalize_mnemonic_seed(
    controller, settings, seed_mnemonic, seed_type, wordlist_language_code, skip_current_view=False
):
    if seed_type == 'aezeed':
        seed = _dependency('seedsigner.models.seed', 'AezeedSeed')(mnemonic=seed_mnemonic)
        controller.storage.set_pending_seed(seed)
        if seed.seed_bytes is None:
            return _dependency('seedsigner_port.navigation', 'Destination')(
                _dependency('seedsigner.views.seed_views', 'SeedAezeedPassphraseModeView')
            )
    else:
        controller.storage.set_pending_seed(
            _dependency('seedsigner.models.seed', 'Seed')(
                mnemonic=seed_mnemonic, wordlist_language_code=wordlist_language_code
            )
        )
        if (
            settings.get_value(
                _dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__PASSPHRASE
            )
            == _dependency('seedsigner.models.settings', 'SettingsConstants').OPTION__REQUIRED
        ):
            return _dependency('seedsigner_port.navigation', 'Destination')(
                _dependency('seedsigner.views.seed_views', 'SeedAddPassphraseView')
            )
    return _dependency('seedsigner_port.navigation', 'Destination')(
        _dependency('seedsigner.views.seed_views', 'SeedFinalizeView'),
        skip_current_view=skip_current_view,
    )


def finalize_xprv_seed(controller, candidate, skip_current_view=False):
    try:
        hdkey = _dependency('embit', 'bip32').HDKey.from_string(candidate)
    except FeatureUnavailable:
        raise
    except Exception:
        return _dependency('seedsigner_port.navigation', 'Destination')(
            _resolve('ScanInvalidQRTypeView')
        )
    if not hdkey.is_private:
        return _dependency('seedsigner_port.navigation', 'Destination')(
            _resolve('ScanInvalidQRTypeView')
        )
    try:
        controller.storage.set_pending_seed(
            _dependency('seedsigner.models.seed', 'XprvSeed')(candidate)
        )
    except _dependency('seedsigner.models.seed', 'InvalidSeedException'):
        return _dependency('seedsigner_port.navigation', 'Destination')(
            _resolve('ScanInvalidQRTypeView')
        )
    return _dependency('seedsigner_port.navigation', 'Destination')(
        _dependency('seedsigner.views.seed_views', 'SeedFinalizeView'),
        skip_current_view=skip_current_view,
    )


def _make_ScanView():

    class ScanView(_dependency('seedsigner.views.view', 'View')):
        """
        The catch-all generic scanning View that will accept any of our supported QR
        formats and will route to the most sensible next step.

        Can also be used as a base class for more specific scanning flows with
        dedicated errors when an unexpected QR type is scanned (e.g. Scan PSBT was
        selected but a SeedQR was scanned).
        """

        instructions_text = _dependency('seedsigner.helpers.l10n', 'mark_for_translation')(
            'Scan a QR code'
        )
        invalid_qr_type_message = _dependency('seedsigner.helpers.l10n', 'mark_for_translation')(
            'QRCode not recognized or not yet supported.'
        )

        def __init__(self):
            super().__init__()
            self.wordlist_language_code = self.settings.get_value(
                _dependency(
                    'seedsigner.models.settings', 'SettingsConstants'
                ).SETTING__WORDLIST_LANGUAGE
            )
            self.decoder = _dependency('seedsigner.models.decode_qr', 'DecodeQR')(
                wordlist_language_code=self.wordlist_language_code
            )

        @property
        def is_valid_qr_type(self):
            return True

        def _finalize_mnemonic_seed(self, seed_mnemonic, seed_type):
            return finalize_mnemonic_seed(
                controller=self.controller,
                settings=self.settings,
                seed_mnemonic=seed_mnemonic,
                seed_type=seed_type,
                wordlist_language_code=self.wordlist_language_code,
            )

        def _finalize_xprv_seed(self, xprv):
            return finalize_xprv_seed(controller=self.controller, candidate=xprv)

        def _scanner_unavailable_destination(self):
            if _dependency('seedsigner.models.decode_qr', 'DecodeQR').is_qr_scanner_available():
                return None
            return _dependency('seedsigner_port.navigation', 'Destination')(
                _dependency('seedsigner.views.view', 'ErrorView'),
                view_args=dict(
                    title='Error',
                    status_headline=_dependency('gettext', 'gettext')('QR Scanner Unavailable'),
                    text=_dependency('gettext', 'gettext')(
                        'QR scanning backend missing. Install zbar (or OpenCV on desktop) and restart.'
                    ),
                    button_text=_dependency('gettext', 'gettext')('Back'),
                    next_destination=_dependency('seedsigner_port.navigation', 'Destination')(
                        _dependency('seedsigner.views.view', 'BackStackView'),
                        skip_current_view=True,
                    ),
                ),
                skip_current_view=True,
            )

        def run(self):
            unavailable = self._scanner_unavailable_destination()
            if unavailable is not None:
                return unavailable
            self.run_screen(
                _dependency('seedsigner.gui.screens.scan_screens', 'ScanScreen'),
                instructions_text=self.instructions_text,
                decoder=self.decoder,
            )
            self.controller.reset_screensaver_timeout()
            _dependency('seedsigner_port.clock', None).sleep(0.1)
            if self.decoder.is_complete:
                if not self.is_valid_qr_type:
                    return _dependency('seedsigner_port.navigation', 'Destination')(
                        _dependency('seedsigner.views.view', 'ErrorView'),
                        view_args=dict(
                            title='Error',
                            status_headline=_dependency('gettext', 'gettext')('Wrong QR Type'),
                            text=_dependency('gettext', 'gettext')(self.invalid_qr_type_message)
                            + ', received "{0}" format'.format(
                                self.decoder.qr_type.replace('__', ': ').replace('_', ' ')
                            ),
                            button_text=_dependency('gettext', 'gettext')('Back'),
                            next_destination=_dependency(
                                'seedsigner_port.navigation', 'Destination'
                            )(
                                _dependency('seedsigner.views.view', 'BackStackView'),
                                skip_current_view=True,
                            ),
                        ),
                    )
                if self.decoder.is_seed:
                    seed_mnemonic = self.decoder.get_seed_phrase()
                    seed_type = self.decoder.get_seed_type()
                    if not seed_mnemonic:
                        return _dependency('seedsigner_port.navigation', 'Destination')(
                            _dependency('seedsigner.views.view', 'NotYetImplementedView')
                        )
                    if seed_type == 'ambiguous':
                        TYPE_BIP39 = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
                            'BIP39'
                        )
                        TYPE_AEZEED = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
                            'Aezeed'
                        )
                        button_data = [TYPE_BIP39, TYPE_AEZEED]
                        selected = self.run_screen(
                            _dependency('seedsigner.gui.screens.screen', 'ButtonListScreen'),
                            title=_dependency('gettext', 'gettext')('Select Seed Type'),
                            is_button_text_centered=True,
                            button_data=button_data,
                        )
                        if selected == _dependency(
                            'seedsigner.gui.screens.screen', 'RET_CODE__BACK_BUTTON'
                        ):
                            return _dependency('seedsigner_port.navigation', 'Destination')(
                                _dependency('seedsigner.views.view', 'BackStackView')
                            )
                        seed_type = 'aezeed' if button_data[selected] == TYPE_AEZEED else 'bip39'
                    return self._finalize_mnemonic_seed(seed_mnemonic, seed_type)
                elif self.decoder.is_slip39_share:
                    share = self.decoder.get_slip39_share()
                    words = share.split()
                    self.controller.storage.init_pending_slip39_share(num_words=len(words))
                    for i, w in enumerate(words):
                        self.controller.storage.update_pending_slip39_share(w, i)
                    self.controller.storage.finalize_current_slip39_share()
                    return _dependency('seedsigner_port.navigation', 'Destination')(
                        _dependency('seedsigner.views.seed_views', 'SeedSlip39MoreSharesView')
                    )
                elif self.decoder.is_xprv:
                    return self._finalize_xprv_seed(self.decoder.get_xprv())
                elif self.decoder.is_ambiguous_qr:
                    return _dependency('seedsigner_port.navigation', 'Destination')(
                        _resolve('ScanAmbiguousQRPromptView'),
                        view_args=dict(
                            segment=self.decoder.get_ambiguous_segment(),
                            candidate_types=self.decoder.get_ambiguous_candidate_types(),
                            public_data=self.decoder.get_ambiguous_public_data(),
                        ),
                        skip_current_view=True,
                    )
                elif self.decoder.is_psbt:
                    try:
                        psbt = self.decoder.get_psbt()
                    except _dependency('seedsigner.models.psbt_parser', 'InvalidPSBTError') as e:
                        pass
                        return _dependency('seedsigner.views.psbt_views', 'refusal_destination')(e)
                    if psbt is None:
                        pass
                        self.run_screen(
                            _dependency('seedsigner.gui.screens.screen', 'WarningScreen'),
                            title=_dependency('gettext', 'gettext')('Invalid PSBT'),
                            status_headline=None,
                            text=_dependency('gettext', 'gettext')(
                                'This transaction could not be read. It may be corrupted or malformed.'
                            ),
                            button_data=[
                                _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Done')
                            ],
                            show_back_button=False,
                        )
                        return _dependency('seedsigner_port.navigation', 'Destination')(
                            _dependency('seedsigner.views.view', 'MainMenuView'), clear_history=True
                        )
                    self.controller.psbt = psbt
                    self.controller.psbt_parser = None
                    self.controller.psbt_source_time = None
                    return _dependency('seedsigner_port.navigation', 'Destination')(
                        _dependency('seedsigner.views.psbt_views', 'PSBTSelectSeedView'),
                        skip_current_view=True,
                    )
                elif self.decoder.is_settings:
                    data = self.decoder.get_settings_data()
                    return _dependency('seedsigner_port.navigation', 'Destination')(
                        _dependency(
                            'seedsigner.views.settings_views', 'SettingsIngestSettingsQRView'
                        ),
                        view_args=dict(data=data),
                    )
                elif self.decoder.is_wallet_descriptor:
                    descriptor_str = self.decoder.get_wallet_descriptor()
                    descriptor_str = _dependency(
                        'seedsigner.helpers', 'embit_utils'
                    ).normalize_descriptor_str(descriptor_str)
                    descriptor = _dependency('embit.descriptor', 'Descriptor').from_string(
                        descriptor_str
                    )
                    self.controller.multisig_wallet_descriptor = descriptor
                    return _dependency('seedsigner_port.navigation', 'Destination')(
                        _dependency('seedsigner.views.seed_views', 'MultisigWalletDescriptorView'),
                        skip_current_view=True,
                    )
                elif self.decoder.is_address:
                    address = self.decoder.get_address()
                    script_type, network = self.decoder.get_address_type()
                    return _dependency('seedsigner_port.navigation', 'Destination')(
                        _dependency('seedsigner.views.seed_views', 'AddressVerificationStartView'),
                        skip_current_view=True,
                        view_args={
                            'address': address,
                            'script_type': script_type,
                            'network': network,
                        },
                    )
                elif self.decoder.is_sign_message:
                    qr_data = self.decoder.get_qr_data()
                    return _dependency('seedsigner_port.navigation', 'Destination')(
                        _dependency('seedsigner.views.seed_views', 'SeedSignMessageStartView'),
                        view_args=dict(
                            derivation_path=qr_data['derivation_path'], message=qr_data['message']
                        ),
                    )
                elif self.decoder.is_time:
                    dt = self.decoder.get_time()
                    if dt:
                        if _dependency('seedsigner.hardware.microsd', 'MicroSD').is_desktop_mode():
                            self.run_screen(
                                _dependency('seedsigner.gui.screens.screen', 'WarningScreen'),
                                title='Unavailable',
                                status_headline=None,
                                text='Setting the system time is not supported on desktop.',
                                show_back_button=False,
                                button_data=[
                                    _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
                                        'OK'
                                    )
                                ],
                            )
                            return _dependency('seedsigner_port.navigation', 'Destination')(
                                _dependency('seedsigner.views.view', 'MainMenuView')
                            )
                        try:
                            _dependency('subprocess', None).run(
                                ['date', '-s', dt.strftime('%Y-%m-%d %H:%M:%S')], check=True
                            )
                            self.controller.reset_screensaver_timeout()
                            self.run_screen(
                                _dependency('seedsigner.gui.screens', 'LargeIconStatusScreen'),
                                title='Success',
                                status_headline=None,
                                text=_dependency('gettext', 'gettext')('Time set to:')
                                + ' {0}'.format(dt.strftime('%Y-%m-%d %H:%M:%S')),
                                show_back_button=False,
                            )
                        except FeatureUnavailable:
                            raise
                        except Exception as e:
                            return _dependency('seedsigner_port.navigation', 'Destination')(
                                _dependency('seedsigner.views.view', 'ErrorView'),
                                view_args=dict(
                                    title='Error',
                                    status_headline=_dependency('gettext', 'gettext')(
                                        'Set Time Failed'
                                    ),
                                    text=str(e),
                                    button_text=_dependency('gettext', 'gettext')('Back'),
                                    next_destination=_dependency(
                                        'seedsigner_port.navigation', 'Destination'
                                    )(
                                        _dependency('seedsigner.views.view', 'MainMenuView'),
                                        skip_current_view=True,
                                    ),
                                ),
                            )
                        return _dependency('seedsigner_port.navigation', 'Destination')(
                            _dependency('seedsigner.views.view', 'MainMenuView')
                        )
                    else:
                        return _dependency('seedsigner_port.navigation', 'Destination')(
                            _dependency('seedsigner.views.view', 'ErrorView'),
                            view_args=dict(
                                title='Error',
                                status_headline=_dependency('gettext', 'gettext')('Invalid Time'),
                                text=_dependency('gettext', 'gettext')(
                                    'Could not parse time from QR'
                                ),
                                button_text=_dependency('gettext', 'gettext')('Back'),
                                next_destination=_dependency(
                                    'seedsigner_port.navigation', 'Destination'
                                )(
                                    _dependency('seedsigner.views.view', 'MainMenuView'),
                                    skip_current_view=True,
                                ),
                            ),
                        )
                elif self.decoder.is_bip38:
                    if (
                        self.settings.get_value(
                            _dependency(
                                'seedsigner.models.settings', 'SettingsConstants'
                            ).SETTING__BIP38_KEYS
                        )
                        == _dependency(
                            'seedsigner.models.settings', 'SettingsConstants'
                        ).OPTION__ENABLED
                    ):
                        bip38 = self.decoder.get_bip38()
                        return _dependency('seedsigner_port.navigation', 'Destination')(
                            _dependency('seedsigner.views.psbt_views', 'PSBTBIP38PassphraseView'),
                            view_args=dict(encrypted=bip38),
                            skip_current_view=True,
                        )
                    else:
                        return _dependency('seedsigner_port.navigation', 'Destination')(
                            _resolve('ScanInvalidQRTypeView')
                        )
                elif self.decoder.is_wif:
                    if (
                        self.settings.get_value(
                            _dependency(
                                'seedsigner.models.settings', 'SettingsConstants'
                            ).SETTING__WIF_KEYS
                        )
                        == _dependency(
                            'seedsigner.models.settings', 'SettingsConstants'
                        ).OPTION__ENABLED
                    ):
                        wif = self.decoder.get_wif()
                        self.controller.psbt_seed = _dependency('seedsigner.models.wif', 'WIFKey')(
                            wif
                        )
                        return _dependency('seedsigner_port.navigation', 'Destination')(
                            _dependency('seedsigner.views.psbt_views', 'PSBTOverviewView'),
                            skip_current_view=True,
                        )
                    else:
                        return _dependency('seedsigner_port.navigation', 'Destination')(
                            _resolve('ScanInvalidQRTypeView')
                        )
                elif self.decoder.is_encrypted_seedqr:
                    DECRYPT = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
                        'Decrypt'
                    )
                    CANCEL = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Cancel')
                    button_data = [DECRYPT, CANCEL]
                    public_data = self.decoder.get_public_data()
                    selected_menu_num = self.run_screen(
                        _dependency('seedsigner.gui.screens.scan_screens', 'ScanEncryptedQRScreen'),
                        public_data=public_data,
                        button_data=button_data,
                    )
                    if button_data[selected_menu_num] == DECRYPT:
                        return _dependency('seedsigner_port.navigation', 'Destination')(
                            _resolve('ScanEncryptedQREncryptionKeyView')
                        )
                    elif button_data[selected_menu_num] == CANCEL:
                        self.controller.storage2.clear_encryptedqr()
                        return _dependency('seedsigner_port.navigation', 'Destination')(
                            _dependency('seedsigner.views.view', 'MainMenuView')
                        )
                else:
                    return _dependency('seedsigner_port.navigation', 'Destination')(
                        _dependency('seedsigner.views.view', 'NotYetImplementedView')
                    )
            elif self.decoder.is_invalid:
                self.controller.resume_main_flow = None
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('ScanInvalidQRTypeView')
                )
            return _dependency('seedsigner_port.navigation', 'Destination')(
                _dependency('seedsigner.views.view', 'MainMenuView')
            )

    return ScanView


def _make_ScanPSBTView():

    class ScanPSBTView(_resolve('ScanView')):
        instructions_text = _dependency('seedsigner.helpers.l10n', 'mark_for_translation')(
            'Scan Transaction'
        )
        invalid_qr_type_message = _dependency('seedsigner.helpers.l10n', 'mark_for_translation')(
            'Expected a transaction'
        )

        @property
        def is_valid_qr_type(self):
            return self.decoder.is_psbt

    return ScanPSBTView


def _make_ScanSeedQRView():

    class ScanSeedQRView(_resolve('ScanView')):
        instructions_text = _dependency('seedsigner.helpers.l10n', 'mark_for_translation')(
            'Scan SeedQR'
        )
        invalid_qr_type_message = _dependency('seedsigner.helpers.l10n', 'mark_for_translation')(
            'Expected a SeedQR'
        )

        @property
        def is_valid_qr_type(self):
            return (
                self.decoder.is_seed
                or self.decoder.is_encrypted_seedqr
                or self.decoder.is_xprv
                or self.decoder.is_ambiguous_qr
            )

    return ScanSeedQRView


def _make_ScanSlip39ShareQRView():

    class ScanSlip39ShareQRView(_resolve('ScanView')):
        instructions_text = _dependency('seedsigner.helpers.l10n', 'mark_for_translation')(
            'Scan SLIP-39 Share'
        )
        invalid_qr_type_message = _dependency('seedsigner.helpers.l10n', 'mark_for_translation')(
            'Expected a SLIP-39 share QR'
        )

        @property
        def is_valid_qr_type(self):
            return self.decoder.is_slip39_share

        def run(self):
            unavailable = self._scanner_unavailable_destination()
            if unavailable is not None:
                return unavailable
            self.run_screen(
                _dependency('seedsigner.gui.screens.scan_screens', 'ScanScreen'),
                instructions_text=self.instructions_text,
                decoder=self.decoder,
            )
            self.controller.reset_screensaver_timeout()
            _dependency('seedsigner_port.clock', None).sleep(0.1)
            if self.decoder.is_complete:
                share = self.decoder.get_slip39_share()
                words = share.split()
                self.controller.storage.init_pending_slip39_share(num_words=len(words))
                for i, w in enumerate(words):
                    self.controller.storage.update_pending_slip39_share(w, i)
                try:
                    self.controller.storage.finalize_current_slip39_share()
                except _dependency('seedsigner.models.seed', 'InvalidSeedException'):
                    return _dependency('seedsigner_port.navigation', 'Destination')(
                        _dependency('seedsigner.views.seed_views', 'SeedSlip39ShareInvalidView'),
                        view_args={'length': len(words), 'retry_scan': True},
                        skip_current_view=True,
                    )
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _dependency('seedsigner.views.seed_views', 'SeedSlip39MoreSharesView')
                )
            elif (
                self.decoder.qr_type
                == _dependency('seedsigner.models.qr_type', 'QRType').SEED__SLIP39
            ):
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _dependency('seedsigner.views.seed_views', 'SeedSlip39ShareInvalidView'),
                    view_args={'length': 33, 'retry_scan': True},
                    skip_current_view=True,
                )
            elif self.decoder.is_invalid:
                self.controller.resume_main_flow = None
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('ScanInvalidQRTypeView')
                )
            return _dependency('seedsigner_port.navigation', 'Destination')(
                _dependency('seedsigner.views.view', 'BackStackView')
            )

    return ScanSlip39ShareQRView


def _make_ScanWIFQRView():

    class ScanWIFQRView(_resolve('ScanView')):
        instructions_text = _dependency('seedsigner.helpers.l10n', 'mark_for_translation')(
            'Scan WIF'
        )
        invalid_qr_type_message = _dependency('seedsigner.helpers.l10n', 'mark_for_translation')(
            'Expected a WIF private key'
        )

        @property
        def is_valid_qr_type(self):
            return (
                self.settings.get_value(
                    _dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__WIF_KEYS
                )
                == _dependency('seedsigner.models.settings', 'SettingsConstants').OPTION__ENABLED
                and self.decoder.is_wif
            )

    return ScanWIFQRView


def _make_ScanBIP38QRView():

    class ScanBIP38QRView(_resolve('ScanView')):
        instructions_text = _dependency('seedsigner.helpers.l10n', 'mark_for_translation')(
            'Scan BIP38'
        )
        invalid_qr_type_message = _dependency('seedsigner.helpers.l10n', 'mark_for_translation')(
            'Expected a BIP38 private key'
        )

        @property
        def is_valid_qr_type(self):
            return (
                self.settings.get_value(
                    _dependency(
                        'seedsigner.models.settings', 'SettingsConstants'
                    ).SETTING__BIP38_KEYS
                )
                == _dependency('seedsigner.models.settings', 'SettingsConstants').OPTION__ENABLED
                and self.decoder.is_bip38
            )

    return ScanBIP38QRView


def _make_ScanWalletDescriptorView():

    class ScanWalletDescriptorView(_resolve('ScanView')):
        instructions_text = _dependency('seedsigner.helpers.l10n', 'mark_for_translation')(
            'Scan descriptor'
        )
        invalid_qr_type_message = _dependency('seedsigner.helpers.l10n', 'mark_for_translation')(
            'Expected a wallet descriptor QR'
        )

        @property
        def is_valid_qr_type(self):
            return self.decoder.is_wallet_descriptor

    return ScanWalletDescriptorView


def _make_ScanAddressView():

    class ScanAddressView(_resolve('ScanView')):
        instructions_text = _dependency('seedsigner.helpers.l10n', 'mark_for_translation')(
            'Scan address QR'
        )
        invalid_qr_type_message = _dependency('seedsigner.helpers.l10n', 'mark_for_translation')(
            'Expected an address QR'
        )

        @property
        def is_valid_qr_type(self):
            return self.decoder.is_address

    return ScanAddressView


def _make_ScanXpubAddressView():

    class ScanXpubAddressView(_resolve('ScanAddressView')):
        def __init__(self, seed, derivation_path, script_type, sig_type, coordinator_label):
            super().__init__()
            self.seed = seed
            self.derivation_path = derivation_path
            self.script_type = script_type
            self.sig_type = sig_type
            self.instructions_text = _dependency('gettext', 'gettext')(
                'Scan {} receive address from the wallet you just exported'
            ).format(coordinator_label)

        def run(self):
            destination = super().run()
            if destination.View_cls == _dependency(
                'seedsigner.views.seed_views', 'AddressVerificationStartView'
            ):
                address = self.decoder.get_address()
                scanned_script_type, network = self.decoder.get_address_type()
                if scanned_script_type != self.script_type:
                    return _dependency('seedsigner_port.navigation', 'Destination')(
                        _dependency(
                            'seedsigner.views.seed_views', 'SeedExportXpubVerificationFailedView'
                        ),
                        view_args=dict(reason='script_mismatch'),
                        skip_current_view=True,
                    )
                self.controller.unverified_address = dict(
                    address=address,
                    script_type=self.script_type,
                    network=network,
                    sig_type=self.sig_type,
                    derivation_path=self.derivation_path,
                )
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _dependency('seedsigner.views.seed_views', 'SeedAddressVerificationView'),
                    view_args=dict(seed=self.seed, export_for_xpub=True),
                    skip_current_view=True,
                )
            return destination

    return ScanXpubAddressView


def _make_ScanAmbiguousQRPromptView():

    class ScanAmbiguousQRPromptView(_dependency('seedsigner.views.view', 'View')):
        COMPACT = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('CompactSeedQR')
        ENCRYPTED = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('EncryptedQR')
        XPRV = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('xprv')
        CANCEL = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Cancel')

        def __init__(self, segment, candidate_types, public_data=None):
            super().__init__()
            self.segment = segment
            self.candidate_types = candidate_types
            self.public_data = public_data
            self.wordlist_language_code = self.settings.get_value(
                _dependency(
                    'seedsigner.models.settings', 'SettingsConstants'
                ).SETTING__WORDLIST_LANGUAGE
            )

        def run(self):
            button_data = []
            if (
                _dependency('seedsigner.models.qr_type', 'QRType').SEED__COMPACTSEEDQR
                in self.candidate_types
            ):
                button_data.append(self.COMPACT)
            if (
                _dependency('seedsigner.models.qr_type', 'QRType').SEED__ENCRYPTEDQR
                in self.candidate_types
            ):
                button_data.append(self.ENCRYPTED)
            if (
                _dependency('seedsigner.models.qr_type', 'QRType').SEED__XPRV
                in self.candidate_types
            ):
                button_data.append(self.XPRV)
            button_data.append(self.CANCEL)
            selected_menu_num = self.run_screen(
                _dependency('seedsigner.gui.screens.scan_screens', 'ScanAmbiguousQRScreen'),
                message=_dependency('gettext', 'gettext')('Data matches multiple\nQR types.'),
                button_data=button_data,
            )
            selected_option = button_data[selected_menu_num]
            if selected_option == self.ENCRYPTED:
                analysis = _dependency(
                    'seedsigner.models.decode_qr', 'DecodeQR'
                ).analyze_bytedata_payload(self.segment)
                if analysis.encrypted_qr and analysis.public_data:
                    DECRYPT = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
                        'Decrypt'
                    )
                    CANCEL = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Cancel')
                    button_data = [DECRYPT, CANCEL]
                    selected_menu_num = self.run_screen(
                        _dependency('seedsigner.gui.screens.scan_screens', 'ScanEncryptedQRScreen'),
                        public_data=analysis.public_data,
                        button_data=button_data,
                    )
                    if button_data[selected_menu_num] == DECRYPT:
                        _dependency(
                            'seedsigner.models.decode_qr', 'DecodeQR'
                        ).store_encrypted_qr_candidate(analysis.encrypted_qr, analysis.public_data)
                        return _dependency('seedsigner_port.navigation', 'Destination')(
                            _resolve('ScanEncryptedQREncryptionKeyView'), skip_current_view=True
                        )
                    elif button_data[selected_menu_num] == CANCEL:
                        return _dependency('seedsigner_port.navigation', 'Destination')(
                            _dependency('seedsigner.views.view', 'MainMenuView')
                        )
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('ScanInvalidQRTypeView')
                )
            if selected_option == self.COMPACT:
                return finalize_mnemonic_seed(
                    controller=self.controller,
                    settings=self.settings,
                    seed_mnemonic=[
                        ''.join(w)
                        for w in _dependency('embit', 'bip39')
                        .mnemonic_from_bytes(self.segment)
                        .split()
                    ],
                    seed_type='bip39',
                    wordlist_language_code=self.wordlist_language_code,
                )
            if selected_option == self.XPRV:
                return finalize_xprv_seed(
                    controller=self.controller, candidate=self.segment.decode('utf-8').strip()
                )
            return _dependency('seedsigner_port.navigation', 'Destination')(
                _dependency('seedsigner.views.view', 'MainMenuView')
            )

    return ScanAmbiguousQRPromptView


def _make_ScanEncryptedQREncryptionKeyView():

    class ScanEncryptedQREncryptionKeyView(_dependency('seedsigner.views.view', 'View')):
        def run(self):
            TYPE = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
                'Type encryption key'
            )
            SCAN = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
                'Scan encryption key'
            )
            CANCEL = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Cancel')
            button_data = [TYPE, SCAN, CANCEL]
            selected_menu_num = self.run_screen(
                _dependency('seedsigner.gui.screens.screen', 'ButtonListScreen'),
                title='Input Encryption Key',
                show_back_button=False,
                button_data=button_data,
            )
            if button_data[selected_menu_num] == TYPE:
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('ScanEncryptedQRTypeEncryptionKeyView')
                )
            elif button_data[selected_menu_num] == SCAN:
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('ScanEncryptedQRScanEncryptionKeyView')
                )
            elif button_data[selected_menu_num] == CANCEL:
                self.controller.storage2.clear_encryptedqr()
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _dependency('seedsigner.views.view', 'MainMenuView')
                )

    return ScanEncryptedQREncryptionKeyView


def _make_ScanEncryptedQRTypeEncryptionKeyView():

    class ScanEncryptedQRTypeEncryptionKeyView(_dependency('seedsigner.views.view', 'View')):
        def __init__(self, encryption_key=''):
            super().__init__()
            self.encryption_key = encryption_key

        def run(self):
            ret_dict = self.run_screen(
                _dependency('seedsigner.gui.screens.scan_screens', 'ScanTypeEncryptionKeyScreen'),
                encryptionkey=self.encryption_key,
            )
            encryption_key = ret_dict['encryptionkey']
            if 'is_back_button' in ret_dict:
                if len(encryption_key) > 0:
                    return _dependency('seedsigner_port.navigation', 'Destination')(
                        _resolve('ScanEncryptedQRTypeEncryptionKeyExitDialogView'),
                        view_args=dict(encryption_key=encryption_key),
                        skip_current_view=True,
                    )
                else:
                    return _dependency('seedsigner_port.navigation', 'Destination')(
                        _dependency('seedsigner.views.view', 'BackStackView')
                    )
            else:
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('ScanEncryptedQRReviewEncryptionKeyView'),
                    view_args=dict(encryption_key=encryption_key),
                    skip_current_view=True,
                )

    return ScanEncryptedQRTypeEncryptionKeyView


def _make_ScanEncryptedQRTypeEncryptionKeyExitDialogView():

    class ScanEncryptedQRTypeEncryptionKeyExitDialogView(
        _dependency('seedsigner.views.view', 'View')
    ):
        EDIT = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Edit encryption key')
        DISCARD = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
            'Discard encryption key', button_label_color='red'
        )

        def __init__(self, encryption_key):
            super().__init__()
            self.encryption_key = encryption_key

        def run(self):
            button_data = [self.EDIT, self.DISCARD]
            selected_menu_num = self.run_screen(
                _dependency('seedsigner.gui.screens.screen', 'WarningScreen'),
                title='Discard encryption key?',
                status_headline=None,
                text='Your current key entry will be erased'.format(),
                show_back_button=False,
                button_data=button_data,
            )
            if button_data[selected_menu_num] == self.EDIT:
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('ScanEncryptedQRTypeEncryptionKeyView'),
                    view_args=dict(encryption_key=self.encryption_key),
                    skip_current_view=True,
                )
            elif button_data[selected_menu_num] == self.DISCARD:
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _dependency('seedsigner.views.view', 'BackStackView')
                )

    return ScanEncryptedQRTypeEncryptionKeyExitDialogView


def _make_ScanEncryptedQRScanEncryptionKeyView():

    class ScanEncryptedQRScanEncryptionKeyView(_dependency('seedsigner.views.view', 'View')):
        def __init__(self, encryption_key=''):
            super().__init__()
            self.encryption_key = encryption_key

        def run(self):
            decoder = _dependency('seedsigner.models.decode_qr', 'DecodeQR')(is_encryptionkey=True)
            self.run_screen(
                _dependency('seedsigner.gui.screens.scan_screens', 'ScanScreen'),
                instructions_text=_dependency('gettext', 'gettext')('Scan encryption key'),
                decoder=decoder,
            )
            self.controller.reset_screensaver_timeout()
            _dependency('seedsigner_port.clock', None).sleep(0.1)
            if decoder.is_complete:
                self.encryption_key += decoder.get_encryption_key()
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('ScanEncryptedQRReviewEncryptionKeyView'),
                    view_args=dict(encryption_key=self.encryption_key),
                    skip_current_view=True,
                )
            elif decoder.is_nonUTF8:
                _dependency('seedsigner.gui.screens.screen', 'DireWarningScreen')(
                    title='Error!',
                    show_back_button=False,
                    status_headline='Invalid Text QR Code',
                    text='Non UTF-8 data detected.'.format(),
                ).display()
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _dependency('seedsigner.views.view', 'BackStackView')
                )
            else:
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _dependency('seedsigner.views.view', 'BackStackView')
                )

    return ScanEncryptedQRScanEncryptionKeyView


def _make_ScanEncryptedQRReviewEncryptionKeyView():

    class ScanEncryptedQRReviewEncryptionKeyView(_dependency('seedsigner.views.view', 'View')):
        def __init__(self, encryption_key):
            super().__init__()
            self.encryption_key = encryption_key

        def run(self):
            if len(self.encryption_key) > 200:
                _dependency('seedsigner.gui.screens.screen', 'WarningScreen')(
                    title='Error',
                    show_back_button=False,
                    status_headline='Invalid Key',
                    text='Key length is too long.',
                ).display()
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _dependency('seedsigner.views.view', 'BackStackView')
                )
            PROCEED = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Proceed')
            EDIT = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Edit')
            SCAN = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
                'Scan & Append Another'
            )
            button_data = [PROCEED, EDIT, SCAN]
            selected_menu_num = self.run_screen(
                _dependency('seedsigner.gui.screens.scan_screens', 'ScanReviewEncryptionKeyScreen'),
                encryptionkey=self.encryption_key,
                button_data=button_data,
            )
            if selected_menu_num == _dependency(
                'seedsigner.gui.screens.screen', 'RET_CODE__BACK_BUTTON'
            ):
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _dependency('seedsigner.views.view', 'BackStackView')
                )
            elif button_data[selected_menu_num] == PROCEED:
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('ScanDecryptEncryptedQRView'),
                    view_args=dict(encryption_key=self.encryption_key),
                )
            elif button_data[selected_menu_num] == EDIT:
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('ScanEncryptedQRTypeEncryptionKeyView'),
                    view_args=dict(encryption_key=self.encryption_key),
                    skip_current_view=True,
                )
            elif button_data[selected_menu_num] == SCAN:
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('ScanEncryptedQRScanEncryptionKeyView'),
                    view_args=dict(encryption_key=self.encryption_key),
                    skip_current_view=True,
                )

    return ScanEncryptedQRReviewEncryptionKeyView


def _make_ScanDecryptEncryptedQRView():

    class ScanDecryptEncryptedQRView(_dependency('seedsigner.views.view', 'View')):
        """
        Decrypt an encrypted QR
        """

        def __init__(self, encryption_key, encrypted_data=None):
            super().__init__()
            self.encryption_key = encryption_key
            self.encrypted_data = encrypted_data
            self.wordlist_language_code = self.settings.get_value(
                _dependency(
                    'seedsigner.models.settings', 'SettingsConstants'
                ).SETTING__WORDLIST_LANGUAGE
            )

        def _route_decrypted_payload(self, word_bytes):
            analysis = _dependency(
                'seedsigner.models.decode_qr', 'DecodeQR'
            ).analyze_bytedata_payload(word_bytes)
            resolved_qr_type = _dependency(
                'seedsigner.models.decode_qr', 'DecodeQR'
            ).resolve_payload_type(analysis)
            if (
                resolved_qr_type
                == _dependency('seedsigner.models.qr_type', 'QRType').SEED__COMPACTSEEDQR
            ):
                return finalize_mnemonic_seed(
                    controller=self.controller,
                    settings=self.settings,
                    seed_mnemonic=[
                        ''.join(w)
                        for w in _dependency('embit', 'bip39')
                        .mnemonic_from_bytes(word_bytes)
                        .split()
                    ],
                    seed_type='bip39',
                    wordlist_language_code=self.wordlist_language_code,
                    skip_current_view=True,
                )
            if resolved_qr_type == _dependency('seedsigner.models.qr_type', 'QRType').SEED__XPRV:
                candidate = word_bytes.decode('utf-8').strip()
                return finalize_xprv_seed(
                    controller=self.controller, candidate=candidate, skip_current_view=True
                )
            if (
                resolved_qr_type
                == _dependency('seedsigner.models.qr_type', 'QRType').SEED__ENCRYPTEDQR
            ):
                if analysis.encrypted_qr and analysis.public_data:
                    DECRYPT = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
                        'Decrypt'
                    )
                    CANCEL = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Cancel')
                    button_data = [DECRYPT, CANCEL]
                    selected_menu_num = self.run_screen(
                        _dependency('seedsigner.gui.screens.scan_screens', 'ScanEncryptedQRScreen'),
                        public_data=analysis.public_data,
                        button_data=button_data,
                    )
                    if button_data[selected_menu_num] == DECRYPT:
                        _dependency(
                            'seedsigner.models.decode_qr', 'DecodeQR'
                        ).store_encrypted_qr_candidate(analysis.encrypted_qr, analysis.public_data)
                        return _dependency('seedsigner_port.navigation', 'Destination')(
                            _resolve('ScanEncryptedQREncryptionKeyView'), skip_current_view=True
                        )
                    elif button_data[selected_menu_num] == CANCEL:
                        return _dependency('seedsigner_port.navigation', 'Destination')(
                            _dependency('seedsigner.views.view', 'MainMenuView')
                        )
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('ScanInvalidQRTypeView')
                )
            if (
                resolved_qr_type
                == _dependency('seedsigner.models.qr_type', 'QRType').SEED__AMBIGUOUS_QR
            ):
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('ScanAmbiguousQRPromptView'),
                    view_args=dict(
                        segment=word_bytes,
                        candidate_types=analysis.candidate_types,
                        public_data=analysis.public_data,
                    ),
                    skip_current_view=True,
                )
            try:
                decoded_text = word_bytes.decode('utf-8')
            except _dependency('builtins', 'UnicodeError'):
                decoded_text = None
            if decoded_text:
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('ScanDecryptedTextView'),
                    view_args=dict(text=decoded_text),
                    skip_current_view=True,
                )
            return _dependency('seedsigner_port.navigation', 'Destination')(
                _resolve('ScanInvalidQRTypeView')
            )

        def run(self):
            self.loading_screen = _dependency(
                'seedsigner.gui.screens.screen', 'LoadingScreenThread'
            )(text='Processing...')
            self.loading_screen.start()
            status = _dependency('seedsigner.models.decode_qr', 'DecodeQRStatus').INVALID
            word_bytes = None
            encryptedqr = None
            try:
                decoder = _dependency('seedsigner.models.decode_qr', 'EncryptedQrDecoder')()
                status = decoder.add(
                    self.encrypted_data,
                    qr_type=_dependency('seedsigner.models.qr_type', 'QRType').SEED__ENCRYPTEDQR,
                )
                if status == _dependency('seedsigner.models.decode_qr', 'DecodeQRStatus').COMPLETE:
                    encryptedqr = self.controller.storage2.encryptedqr
                    if encryptedqr:
                        word_bytes = encryptedqr.encrypted_qr.decrypt(self.encryption_key)
            finally:
                self.loading_screen.stop()
            if status == _dependency('seedsigner.models.decode_qr', 'DecodeQRStatus').COMPLETE:
                if not encryptedqr:
                    return _dependency('seedsigner_port.navigation', 'Destination')(
                        _resolve('ScanInvalidQRTypeView')
                    )
                if not word_bytes:
                    _dependency('seedsigner.gui.screens.screen', 'WarningScreen')(
                        title='Error',
                        show_back_button=False,
                        status_headline='decryption failure',
                        text='Review your encryption key.',
                    ).display()
                    return _dependency('seedsigner_port.navigation', 'Destination')(
                        _dependency('seedsigner.views.view', 'BackStackView')
                    )
                self.controller.storage2.clear_encryptedqr()
                return self._route_decrypted_payload(word_bytes)
            else:
                self.controller.storage2.clear_encryptedqr()
                _dependency('seedsigner.gui.screens.screen', 'WarningScreen')(
                    title='Error',
                    show_back_button=False,
                    status_headline='decryption failure',
                    text='Unknown error',
                ).display()
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _dependency('seedsigner.views.view', 'BackStackView')
                )

    return ScanDecryptEncryptedQRView


def _make_ScanInvalidQRTypeView():

    class ScanInvalidQRTypeView(_dependency('seedsigner.views.view', 'View')):
        def run(self):
            self.run_screen(
                _dependency('seedsigner.gui.screens', 'WarningScreen'),
                title=_dependency('gettext', 'gettext')('Error'),
                status_headline=_dependency('gettext', 'gettext')('Unknown QR Type'),
                text=_dependency('gettext', 'gettext')(
                    'QRCode is invalid or is a data format not yet supported.'
                ),
                button_data=[
                    _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
                        'Back to Main Menu'
                    )
                ],
            )
            return _dependency('seedsigner_port.navigation', 'Destination')(
                _dependency('seedsigner.views.view', 'MainMenuView'), clear_history=True
            )

    return ScanInvalidQRTypeView


def _make_ScanDecryptedTextView():

    class ScanDecryptedTextView(_dependency('seedsigner.views.view', 'View')):
        def __init__(self, text):
            super().__init__()
            self.text = text

        def run(self):
            DONE = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Done')
            self.run_screen(
                _dependency('seedsigner.gui.screens.tools_screens', 'ToolsTextQRReviewTextScreen'),
                title=_dependency('gettext', 'gettext')('Decrypted Text'),
                textToEncode=self.text,
                max_lines=8,
                visible_space=False,
                button_data=[DONE],
                show_back_button=False,
            )
            return _dependency('seedsigner_port.navigation', 'Destination')(
                _dependency('seedsigner.views.view', 'MainMenuView'), clear_history=True
            )

    return ScanDecryptedTextView


_FACTORIES = {
    'ScanView': _make_ScanView,
    'ScanPSBTView': _make_ScanPSBTView,
    'ScanSeedQRView': _make_ScanSeedQRView,
    'ScanSlip39ShareQRView': _make_ScanSlip39ShareQRView,
    'ScanWIFQRView': _make_ScanWIFQRView,
    'ScanBIP38QRView': _make_ScanBIP38QRView,
    'ScanWalletDescriptorView': _make_ScanWalletDescriptorView,
    'ScanAddressView': _make_ScanAddressView,
    'ScanXpubAddressView': _make_ScanXpubAddressView,
    'ScanAmbiguousQRPromptView': _make_ScanAmbiguousQRPromptView,
    'ScanEncryptedQREncryptionKeyView': _make_ScanEncryptedQREncryptionKeyView,
    'ScanEncryptedQRTypeEncryptionKeyView': _make_ScanEncryptedQRTypeEncryptionKeyView,
    'ScanEncryptedQRTypeEncryptionKeyExitDialogView': _make_ScanEncryptedQRTypeEncryptionKeyExitDialogView,
    'ScanEncryptedQRScanEncryptionKeyView': _make_ScanEncryptedQRScanEncryptionKeyView,
    'ScanEncryptedQRReviewEncryptionKeyView': _make_ScanEncryptedQRReviewEncryptionKeyView,
    'ScanDecryptEncryptedQRView': _make_ScanDecryptEncryptedQRView,
    'ScanInvalidQRTypeView': _make_ScanInvalidQRTypeView,
    'ScanDecryptedTextView': _make_ScanDecryptedTextView,
}
_CACHE = {}


def _resolve(name):
    if name not in _CACHE:
        if name not in _FACTORIES:
            raise AttributeError(name)
        _CACHE[name] = _FACTORIES[name]()
    return _CACHE[name]


def __getattr__(name):
    return _resolve(name)
