# Copyright2021 SeedSigner; MIT, see ../LICENSE.SeedSigner
# Generated original camera Views; reviewed native-only platform boundaries.
from seedsigner_port.decode_platform import dependency as _dependency, FeatureUnavailable


def _make_ToolsMenuView():

    class ToolsMenuView(_dependency('seedsigner.views.view', 'View')):
        IMAGE = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
            ' New seed', _dependency('seedsigner.gui.components', 'FontAwesomeIconConstants').CAMERA
        )
        DICE = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
            'New seed', _dependency('seedsigner.gui.components', 'FontAwesomeIconConstants').DICE
        )
        SLIP39_IMAGE = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
            'SLIP39 seed',
            _dependency('seedsigner.gui.components', 'FontAwesomeIconConstants').CAMERA,
        )
        SLIP39_DICE = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
            'SLIP39 seed', _dependency('seedsigner.gui.components', 'FontAwesomeIconConstants').DICE
        )
        KEYBOARD = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
            'Calc 12th/24th word',
            _dependency('seedsigner.gui.components', 'FontAwesomeIconConstants').KEYBOARD,
        )
        ADDRESS_EXPLORER = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
            'Address explorer'
        )
        VERIFY_ADDRESS = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
            'Verify address'
        )
        TEXTQRCODE = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Text QR Code')
        PASSWORD_GENERATOR = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
            'Password Generator',
            _dependency('seedsigner.gui.components', 'FontAwesomeIconConstants').LOCK,
        )
        SMARTCARD = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
            'Smartcard Tools',
            _dependency('seedsigner.gui.components', 'FontAwesomeIconConstants').LOCK,
        )
        MICROSD = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('MicroSD Tools')
        BATTERY_CALIBRATION = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
            'Battery Calibration'
        )
        GPG = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('GPG Tools')
        LUCKFOX_BUILD_TOOLS = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
            'Luckfox Build Tools'
        )
        CLEAR_DESCRIPTOR = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
            'Clear Multisig Descriptor'
        )
        NETWORK_INFO = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Network Info')

        def __init__(self, include_password_generator=True):
            super().__init__()
            self.include_password_generator = include_password_generator

        def run(self):
            button_data = [self.IMAGE, self.DICE]
            if getattr(self, 'include_password_generator', True):
                button_data.append(self.PASSWORD_GENERATOR)
            button_data.extend(
                [self.KEYBOARD, self.ADDRESS_EXPLORER, self.VERIFY_ADDRESS, self.TEXTQRCODE]
            )
            selected_menu_num = self.run_screen(
                _dependency('seedsigner.gui.screens', 'ButtonListScreen'),
                title=_dependency('gettext', 'gettext')('Tools'),
                is_button_text_centered=False,
                button_data=button_data,
            )
            if selected_menu_num == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _dependency('seedsigner.views.view', 'BackStackView')
                )
            if button_data[selected_menu_num] == self.IMAGE:
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('ToolsImageEntropyLivePreviewView')
                )
            if button_data[selected_menu_num] == self.KEYBOARD:
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('ToolsCalcFinalWordNumWordsView')
                )
            if button_data[selected_menu_num] == self.ADDRESS_EXPLORER:
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('ToolsAddressExplorerSelectSourceView')
                )
            if button_data[selected_menu_num] == self.VERIFY_ADDRESS:
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _dependency('seedsigner.views.scan_views', 'ScanAddressView')
                )
            if button_data[selected_menu_num] == self.SLIP39_IMAGE:
                self.controller.create_slip39 = True
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('ToolsImageEntropyLivePreviewView')
                )
            if button_data[selected_menu_num] == self.SLIP39_DICE:
                self.controller.create_slip39 = True
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('ToolsDiceEntropyMnemonicLengthView')
                )
            if button_data[selected_menu_num] == self.TEXTQRCODE:
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _dependency('seedsigner_port.view_tools_extra', 'ToolsTextQRView')
                )
            if button_data[selected_menu_num] == self.PASSWORD_GENERATOR:
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _dependency(
                        'seedsigner_port.view_tools_extra', 'ToolsPasswordGeneratorTypeView'
                    )
                )
            return _dependency('seedsigner_port.navigation', 'Destination')(
                _resolve('ToolsDiceEntropyMnemonicLengthView')
            )

    return ToolsMenuView


def _make_ToolsImageEntropyLivePreviewView():

    class ToolsImageEntropyLivePreviewView(_dependency('seedsigner.views.view', 'View')):
        def __init__(self, next_view=None, next_view_args=None):
            super().__init__()
            self.next_view = next_view
            self.next_view_args = next_view_args

        def run(self):
            self.controller.image_entropy_preview_frames = None
            self.controller.image_entropy_final_image = None
            ret = self.run_screen(
                _dependency(
                    'seedsigner_port.camera_entropy_screens', 'ToolsImageEntropyLivePreviewScreen'
                )
            )
            if ret == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _dependency('seedsigner.views.view', 'BackStackView')
                )
            if isinstance(ret, tuple) and len(ret) == 2:
                (
                    self.controller.image_entropy_preview_frames,
                    self.controller.image_entropy_final_image,
                ) = ret
            else:
                self.controller.image_entropy_preview_frames = ret
            frames = self.controller.image_entropy_preview_frames
            if (
                frames is None
                or len(frames)
                != _dependency(
                    'seedsigner_port.camera_entropy_screens', 'ToolsImageEntropyLivePreviewScreen'
                ).PREVIEW_POOL_SIZE
            ):
                num_frames = 0 if frames is None else len(frames)
                raise Exception(
                    _dependency('gettext', 'gettext')(
                        'Entropy collection failed. Expected {expected} preview frames, got {actual}'
                    ).format(
                        expected=_dependency(
                            'seedsigner_port.camera_entropy_screens',
                            'ToolsImageEntropyLivePreviewScreen',
                        ).PREVIEW_POOL_SIZE,
                        actual=num_frames,
                    )
                )
            return _dependency('seedsigner_port.navigation', 'Destination')(
                _resolve('ToolsImageEntropyFinalImageView'),
                view_args=dict(next_view=self.next_view, next_view_args=self.next_view_args),
            )

    return ToolsImageEntropyLivePreviewView


def _make_ToolsImageEntropyFinalImageView():

    class ToolsImageEntropyFinalImageView(_dependency('seedsigner.views.view', 'View')):
        def __init__(self, next_view=None, next_view_args=None):
            super().__init__()
            self.next_view = next_view
            self.next_view_args = next_view_args

        def run(self):
            if self.controller.image_entropy_final_image is None:
                raise RuntimeError('Camera did not return a final capture')
            ret = self.run_screen(
                _dependency(
                    'seedsigner_port.camera_entropy_screens', 'ToolsImageEntropyFinalImageScreen'
                ),
                final_image=self.controller.image_entropy_final_image,
            )
            if ret == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                _dependency('seedsigner_port.camera_entropy', 'clear_controller_images')(
                    self.controller
                )
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _dependency('seedsigner.views.view', 'BackStackView')
                )
            next_view = self.next_view or _resolve('ToolsImageEntropyMnemonicLengthView')
            return _dependency('seedsigner_port.navigation', 'Destination')(
                next_view, view_args=self.next_view_args
            )

    return ToolsImageEntropyFinalImageView


def _make_ToolsImageEntropyMnemonicLengthView():

    class ToolsImageEntropyMnemonicLengthView(_dependency('seedsigner.views.view', 'View')):
        TWELVE_WORDS = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
            '12 words', return_data=12
        )
        FIFTEEN_WORDS = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
            '15 words', return_data=15
        )
        EIGHTEEN_WORDS = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
            '18 words', return_data=18
        )
        TWENTYONE_WORDS = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
            '21 words', return_data=21
        )
        TWENTYFOUR_WORDS = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
            '24 words', return_data=24
        )

        def run(self):
            owned_previews = self.controller.image_entropy_preview_frames
            owned_final = self.controller.image_entropy_final_image
            release_inputs = True
            try:
                if getattr(self.controller, 'create_slip39', False):
                    twenty = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
                        '20 words', return_data=20
                    )
                    thirty_three = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
                        '33 words', return_data=33
                    )
                    button_data = [twenty, thirty_three]
                else:
                    allowed = self.settings.get_value(
                        _dependency(
                            'seedsigner.models.settings_definition', 'SettingsConstants'
                        ).SETTING__SEED_WORD_LENGTHS
                    )
                    options = {
                        12: self.TWELVE_WORDS,
                        15: self.FIFTEEN_WORDS,
                        18: self.EIGHTEEN_WORDS,
                        21: self.TWENTYONE_WORDS,
                        24: self.TWENTYFOUR_WORDS,
                    }
                    button_data = [options[l] for l in allowed]
                selected_menu_num = self.run_screen(
                    _dependency('seedsigner.gui.screens', 'ButtonListScreen'),
                    title=_dependency('gettext', 'gettext')('Mnemonic Length'),
                    button_data=button_data,
                )
                if selected_menu_num == _dependency(
                    'seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'
                ):
                    release_inputs = False
                    return _dependency('seedsigner_port.navigation', 'Destination')(
                        _dependency('seedsigner.views.view', 'BackStackView')
                    )
                mnemonic_length = button_data[selected_menu_num].return_data
                loading_screen = _dependency(
                    'seedsigner.gui.screens.screen', 'LoadingScreenThread'
                )(text=_dependency('gettext', 'gettext')('Processing...'))
                loading_screen.start()
                preview_images = self.controller.image_entropy_preview_frames
                seed_entropy_image = self.controller.image_entropy_final_image
                final_hash = _dependency(
                    'seedsigner_port.camera_entropy', 'derive_camera_entropy_bytes'
                )(preview_images, seed_entropy_image)
                if final_hash is None:
                    loading_screen.stop()
                    self.run_screen(
                        _dependency('seedsigner.gui.screens', 'ErrorScreen'),
                        title=_dependency('gettext', 'gettext')('Poor Entropy'),
                        status_headline=None,
                        text=_dependency('gettext', 'gettext')(
                            "Camera entropy didn't appear random enough. Please try again."
                        ),
                    )
                    self.controller.image_entropy_preview_frames = None
                    self.controller.image_entropy_final_image = None
                    return _dependency('seedsigner_port.navigation', 'Destination')(
                        _resolve('ToolsImageEntropyLivePreviewView'), skip_current_view=True
                    )
                if (
                    mnemonic_length
                    in _dependency(
                        'seedsigner_port.camera_entropy_mnemonic', None
                    ).ENTROPY_BYTES_REQUIRED
                ):
                    final_hash = final_hash[
                        : _dependency(
                            'seedsigner_port.camera_entropy_mnemonic', None
                        ).ENTROPY_BYTES_REQUIRED[mnemonic_length]
                    ]
                if getattr(self.controller, 'create_slip39', False):
                    secret = final_hash
                else:
                    mnemonic = _dependency(
                        'seedsigner_port.camera_entropy_mnemonic', None
                    ).generate_mnemonic_from_bytes(final_hash)
                loading_screen.stop()
                seed_entropy_image = None
                preview_images = None
                if not getattr(self.controller, 'create_slip39', False):
                    final_hash = None
                hash_bytes = None
                self.controller.image_entropy_preview_frames = None
                self.controller.image_entropy_final_image = None
                if getattr(self.controller, 'create_slip39', False):
                    self.controller.create_slip39 = False
                    return _dependency('seedsigner_port.navigation', 'Destination')(
                        _dependency('seedsigner.views.seed_views', 'SeedSlip39CreateFromBytesView'),
                        view_args=dict(secret=secret),
                        clear_history=True,
                    )
                else:
                    seed = _dependency('seedsigner.models.seed', 'Seed')(
                        mnemonic,
                        wordlist_language_code=self.settings.get_value(
                            _dependency(
                                'seedsigner.models.settings_definition', 'SettingsConstants'
                            ).SETTING__WORDLIST_LANGUAGE
                        ),
                    )
                    self.controller.storage.set_pending_seed(seed)
                    return _dependency('seedsigner_port.navigation', 'Destination')(
                        _dependency('seedsigner.views.seed_views', 'SeedWordsWarningView'),
                        view_args={'seed': None},
                        clear_history=True,
                    )
            finally:
                if release_inputs:
                    _dependency('seedsigner_port.camera_entropy', 'clear_images')(
                        owned_previews, owned_final
                    )
                    _dependency('seedsigner_port.camera_entropy', 'clear_controller_images')(
                        self.controller
                    )

    return ToolsImageEntropyMnemonicLengthView


def _make_ToolsDiceEntropyMnemonicLengthView():

    class ToolsDiceEntropyMnemonicLengthView(_dependency('seedsigner.views.view', 'View')):
        """Prompt for mnemonic length when using dice entropy."""

        TWELVE = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
            '12 words', return_data=12
        )
        FIFTEEN = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
            '15 words', return_data=15
        )
        EIGHTEEN = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
            '18 words', return_data=18
        )
        TWENTY_ONE = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
            '21 words', return_data=21
        )
        TWENTY_FOUR = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
            '24 words', return_data=24
        )
        TWENTY = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
            _dependency('gettext', 'gettext')('20 words ({} rolls)').format(
                _dependency('seedsigner_port.camera_entropy_mnemonic', None).DICE_ROLLS_REQUIRED[12]
            ),
            return_data=_dependency(
                'seedsigner_port.camera_entropy_mnemonic', None
            ).DICE_ROLLS_REQUIRED[12],
        )
        THIRTY_THREE = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
            _dependency('gettext', 'gettext')('33 words ({} rolls)').format(
                _dependency('seedsigner_port.camera_entropy_mnemonic', None).DICE_ROLLS_REQUIRED[24]
            ),
            return_data=_dependency(
                'seedsigner_port.camera_entropy_mnemonic', None
            ).DICE_ROLLS_REQUIRED[24],
        )

        def run(self):
            if getattr(self.controller, 'create_slip39', False):
                button_data = [self.TWENTY, self.THIRTY_THREE]
            else:
                allowed = self.settings.get_value(
                    _dependency(
                        'seedsigner.models.settings_definition', 'SettingsConstants'
                    ).SETTING__SEED_WORD_LENGTHS
                )
                options = {
                    12: self.TWELVE,
                    15: self.FIFTEEN,
                    18: self.EIGHTEEN,
                    21: self.TWENTY_ONE,
                    24: self.TWENTY_FOUR,
                }
                button_data = [options[l] for l in allowed]
            selected_menu_num = self.run_screen(
                _dependency('seedsigner.gui.screens', 'ButtonListScreen'),
                title=_dependency('gettext', 'gettext')('Mnemonic Length'),
                is_bottom_list=True,
                is_button_text_centered=True,
                button_data=button_data,
            )
            if selected_menu_num == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _dependency('seedsigner.views.view', 'BackStackView')
                )
            if getattr(self.controller, 'create_slip39', False):
                total_rolls = button_data[selected_menu_num].return_data
            else:
                selected_length = button_data[selected_menu_num].return_data
                total_rolls = _dependency(
                    'seedsigner_port.camera_entropy_mnemonic', None
                ).DICE_ROLLS_REQUIRED[selected_length]
            return _dependency('seedsigner_port.navigation', 'Destination')(
                _resolve('ToolsDiceEntropyEntryView'), view_args=dict(total_rolls=total_rolls)
            )

    return ToolsDiceEntropyMnemonicLengthView


def _make_ToolsDiceEntropyEntryView():

    class ToolsDiceEntropyEntryView(_dependency('seedsigner.views.view', 'View')):
        def __init__(self, total_rolls):
            super().__init__()
            self.total_rolls = total_rolls

        def run(self):
            ret = self.run_screen(
                _dependency(
                    'seedsigner_port.camera_entropy_screens', 'ToolsDiceEntropyEntryScreen'
                ),
                return_after_n_chars=self.total_rolls,
            )
            if ret == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _dependency('seedsigner.views.view', 'BackStackView')
                )
            if not _dependency(
                'seedsigner_port.camera_entropy_mnemonic', None
            ).dice_entropy_is_sufficient(ret):
                self.run_screen(
                    _dependency('seedsigner.gui.screens', 'ErrorScreen'),
                    title=_dependency('gettext', 'gettext')('Poor Entropy'),
                    status_headline=None,
                    text=_dependency('gettext', 'gettext')(
                        "Dice rolls didn't appear random enough. Please try again."
                    ),
                )
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _dependency('seedsigner.views.view', 'BackStackView')
                )
            loading_screen = _dependency('seedsigner.gui.screens.screen', 'LoadingScreenThread')(
                text=_dependency('gettext', 'gettext')('Processing...')
            )
            loading_screen.start()
            if getattr(self.controller, 'create_slip39', False):
                entropy_bytes = _dependency(
                    'seedsigner_port.camera_entropy_mnemonic', None
                ).generate_bytes_from_dice(ret)
                self.controller.create_slip39 = False
                loading_screen.stop()
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _dependency('seedsigner.views.seed_views', 'SeedSlip39CreateFromBytesView'),
                    view_args=dict(secret=entropy_bytes),
                    clear_history=True,
                )
            else:
                dice_seed_phrase = _dependency(
                    'seedsigner_port.camera_entropy_mnemonic', None
                ).generate_mnemonic_from_dice(
                    ret,
                    wordlist_language_code=self.settings.get_value(
                        _dependency(
                            'seedsigner.models.settings_definition', 'SettingsConstants'
                        ).SETTING__WORDLIST_LANGUAGE
                    ),
                )
                seed = _dependency('seedsigner.models.seed', 'Seed')(
                    dice_seed_phrase,
                    wordlist_language_code=self.settings.get_value(
                        _dependency(
                            'seedsigner.models.settings_definition', 'SettingsConstants'
                        ).SETTING__WORDLIST_LANGUAGE
                    ),
                )
                self.controller.storage.set_pending_seed(seed)
                loading_screen.stop()
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _dependency('seedsigner.views.seed_views', 'SeedWordsWarningView'),
                    view_args={'seed': None},
                    clear_history=True,
                )

    return ToolsDiceEntropyEntryView


def _make_ToolsCalcFinalWordNumWordsView():

    class ToolsCalcFinalWordNumWordsView(_dependency('seedsigner.views.view', 'View')):
        TWELVE = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
            '12 words', return_data=12
        )
        FIFTEEN = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
            '15 words', return_data=15
        )
        EIGHTEEN = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
            '18 words', return_data=18
        )
        TWENTY_ONE = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
            '21 words', return_data=21
        )
        TWENTY_FOUR = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
            '24 words', return_data=24
        )

        def run(self):
            allowed = self.settings.get_value(
                _dependency(
                    'seedsigner.models.settings_definition', 'SettingsConstants'
                ).SETTING__SEED_WORD_LENGTHS
            )
            options = {
                12: self.TWELVE,
                15: self.FIFTEEN,
                18: self.EIGHTEEN,
                21: self.TWENTY_ONE,
                24: self.TWENTY_FOUR,
            }
            button_data = [options[l] for l in allowed]
            selected_menu_num = self.run_screen(
                _dependency('seedsigner.gui.screens', 'ButtonListScreen'),
                title=_dependency('gettext', 'gettext')('Mnemonic Length'),
                is_bottom_list=True,
                is_button_text_centered=True,
                button_data=button_data,
            )
            if selected_menu_num == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _dependency('seedsigner.views.view', 'BackStackView')
                )
            self.controller.storage.init_pending_mnemonic(
                button_data[selected_menu_num].return_data
            )
            return _dependency('seedsigner_port.navigation', 'Destination')(
                _dependency('seedsigner.views.seed_views', 'SeedMnemonicEntryView'),
                view_args=dict(is_calc_final_word=True),
            )

    return ToolsCalcFinalWordNumWordsView


def _make_ToolsCalcFinalWordFinalizePromptView():

    class ToolsCalcFinalWordFinalizePromptView(_dependency('seedsigner.views.view', 'View')):
        COIN_FLIPS = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
            'Coin flip entropy'
        )
        SELECT_WORD = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
            'Word selection entropy'
        )
        ZEROS = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Finalize with zeros')

        def run(self):
            mnemonic = self.controller.storage.pending_mnemonic
            mnemonic_length = len(mnemonic)
            total_bits = (
                _dependency('seedsigner_port.camera_entropy_mnemonic', None).ENTROPY_BYTES_REQUIRED[
                    mnemonic_length
                ]
                * 8
            )
            num_entropy_bits = total_bits - (mnemonic_length - 1) * 11
            button_data = [self.COIN_FLIPS, self.SELECT_WORD, self.ZEROS]
            selected_menu_num = self.run_screen(
                _dependency(
                    'seedsigner.gui.screens.tools_screens', 'ToolsCalcFinalWordFinalizePromptScreen'
                ),
                mnemonic_length=mnemonic_length,
                num_entropy_bits=num_entropy_bits,
                button_data=button_data,
            )
            if selected_menu_num == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _dependency('seedsigner.views.view', 'BackStackView')
                )
            elif button_data[selected_menu_num] == self.COIN_FLIPS:
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('ToolsCalcFinalWordCoinFlipsView')
                )
            elif button_data[selected_menu_num] == self.SELECT_WORD:
                self.controller.storage.update_pending_mnemonic(None, mnemonic_length - 1)
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _dependency('seedsigner.views.seed_views', 'SeedMnemonicEntryView'),
                    view_args=dict(is_calc_final_word=True, cur_word_index=mnemonic_length - 1),
                )
            elif button_data[selected_menu_num] == self.ZEROS:
                wordlist_language_code = self.settings.get_value(
                    _dependency(
                        'seedsigner.models.settings_definition', 'SettingsConstants'
                    ).SETTING__WORDLIST_LANGUAGE
                )
                self.controller.storage.update_pending_mnemonic(
                    _dependency('seedsigner.models.seed', 'Seed').get_wordlist(
                        wordlist_language_code
                    )[0],
                    mnemonic_length - 1,
                )
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('ToolsCalcFinalWordShowFinalWordView'),
                    view_args=dict(coin_flips='0' * num_entropy_bits),
                )

    return ToolsCalcFinalWordFinalizePromptView


def _make_ToolsCalcFinalWordCoinFlipsView():

    class ToolsCalcFinalWordCoinFlipsView(_dependency('seedsigner.views.view', 'View')):
        def run(self):
            mnemonic_length = len(self.controller.storage.pending_mnemonic)
            total_bits = (
                _dependency('seedsigner_port.camera_entropy_mnemonic', None).ENTROPY_BYTES_REQUIRED[
                    mnemonic_length
                ]
                * 8
            )
            total_flips = total_bits - (mnemonic_length - 1) * 11
            ret_val = self.run_screen(
                _dependency('seedsigner.gui.screens.tools_screens', 'ToolsCoinFlipEntryScreen'),
                return_after_n_chars=total_flips,
            )
            if ret_val == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _dependency('seedsigner.views.view', 'BackStackView')
                )
            else:
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('ToolsCalcFinalWordShowFinalWordView'),
                    view_args=dict(coin_flips=ret_val),
                )

    return ToolsCalcFinalWordCoinFlipsView


def _make_ToolsCalcFinalWordShowFinalWordView():

    class ToolsCalcFinalWordShowFinalWordView(_dependency('seedsigner.views.view', 'View')):
        NEXT = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Next')

        def __init__(self, coin_flips=None):
            super().__init__()
            wordlist_language_code = self.settings.get_value(
                _dependency(
                    'seedsigner.models.settings_definition', 'SettingsConstants'
                ).SETTING__WORDLIST_LANGUAGE
            )
            wordlist = _dependency('seedsigner.models.seed', 'Seed').get_wordlist(
                wordlist_language_code
            )
            if coin_flips:
                self.selected_final_word = None
                self.selected_final_bits = coin_flips
            else:
                self.selected_final_word = self.controller.storage.pending_mnemonic[-1]
                self.selected_final_bits = _dependency(
                    'seedsigner_port.final_word', 'builtin_format'
                )(wordlist.index(self.selected_final_word), '011b')
            if coin_flips:
                binary_string = coin_flips + '0' * (11 - len(coin_flips))
                wordlist_index = int(binary_string, 2)
                wordlist = _dependency('seedsigner.models.seed', 'Seed').get_wordlist(
                    self.controller.settings.get_value(
                        _dependency(
                            'seedsigner.models.settings_definition', 'SettingsConstants'
                        ).SETTING__WORDLIST_LANGUAGE
                    )
                )
                word = wordlist[wordlist_index]
                self.controller.storage.update_pending_mnemonic(word, -1)
            final_mnemonic = _dependency(
                'seedsigner.helpers', 'mnemonic_generation'
            ).calculate_checksum(
                mnemonic=self.controller.storage.pending_mnemonic,
                wordlist_language_code=wordlist_language_code,
            )
            self.controller.storage.update_pending_mnemonic(final_mnemonic[-1], -1)
            mnemonic = self.controller.storage.pending_mnemonic
            mnemonic_length = len(mnemonic)
            self.actual_final_word = self.controller.storage.pending_mnemonic[-1]
            total_bits = (
                _dependency('seedsigner.helpers', 'mnemonic_generation').ENTROPY_BYTES_REQUIRED[
                    mnemonic_length
                ]
                * 8
            )
            num_entropy_bits = total_bits - (mnemonic_length - 1) * 11
            num_checksum_bits = 11 - num_entropy_bits
            self.checksum_bits = _dependency('seedsigner_port.final_word', 'builtin_format')(
                wordlist.index(self.actual_final_word), '011b'
            )[-num_checksum_bits:]

        def run(self):
            button_data = [self.NEXT]
            title = _dependency('gettext', 'gettext')('Final Word Calc')
            selected_menu_num = self.run_screen(
                _dependency('seedsigner.gui.screens.tools_screens', 'ToolsCalcFinalWordScreen'),
                title=title,
                button_data=button_data,
                selected_final_word=self.selected_final_word,
                selected_final_bits=self.selected_final_bits,
                checksum_bits=self.checksum_bits,
                actual_final_word=self.actual_final_word,
            )
            if selected_menu_num == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _dependency('seedsigner.views.view', 'BackStackView')
                )
            elif button_data[selected_menu_num] == self.NEXT:
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('ToolsCalcFinalWordDoneView')
                )

    return ToolsCalcFinalWordShowFinalWordView


def _make_ToolsCalcFinalWordDoneView():

    class ToolsCalcFinalWordDoneView(_dependency('seedsigner.views.view', 'View')):
        LOAD = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Load seed')
        DISCARD = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
            'Discard', button_label_color='red'
        )

        def run(self):
            mnemonic = self.controller.storage.pending_mnemonic
            mnemonic_word_length = len(mnemonic)
            final_word = mnemonic[-1]
            button_data = [self.LOAD, self.DISCARD]
            selected_menu_num = self.run_screen(
                _dependency('seedsigner.gui.screens.tools_screens', 'ToolsCalcFinalWordDoneScreen'),
                final_word=final_word,
                mnemonic_word_length=mnemonic_word_length,
                fingerprint=self.controller.storage.get_pending_mnemonic_fingerprint(
                    self.settings.get_value(
                        _dependency(
                            'seedsigner.models.settings_definition', 'SettingsConstants'
                        ).SETTING__NETWORK
                    ),
                    wordlist_language_code=self.settings.get_value(
                        _dependency(
                            'seedsigner.models.settings_definition', 'SettingsConstants'
                        ).SETTING__WORDLIST_LANGUAGE
                    ),
                ),
                button_data=button_data,
            )
            if selected_menu_num == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _dependency('seedsigner.views.view', 'BackStackView')
                )
            self.controller.storage.convert_pending_mnemonic_to_pending_seed(
                wordlist_language_code=self.settings.get_value(
                    _dependency(
                        'seedsigner.models.settings_definition', 'SettingsConstants'
                    ).SETTING__WORDLIST_LANGUAGE
                )
            )
            if button_data[selected_menu_num] == self.LOAD:
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _dependency('seedsigner.views.seed_views', 'SeedFinalizeView')
                )
            elif button_data[selected_menu_num] == self.DISCARD:
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _dependency('seedsigner.views.seed_views', 'SeedDiscardView')
                )

    return ToolsCalcFinalWordDoneView


def _make_ToolsAddressExplorerSelectSourceView():

    class ToolsAddressExplorerSelectSourceView(_dependency('seedsigner.views.view', 'View')):
        SCAN_SEED = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
            'Scan a seed',
            _dependency('seedsigner.gui.components', 'SeedSignerIconConstants').QRCODE,
        )
        SCAN_DESCRIPTOR = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
            'Scan wallet descriptor',
            _dependency('seedsigner.gui.components', 'SeedSignerIconConstants').QRCODE,
        )
        TYPE_12WORD = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
            'Enter 12-word seed',
            _dependency('seedsigner.gui.components', 'FontAwesomeIconConstants').KEYBOARD,
            return_data=12,
        )
        TYPE_15WORD = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
            'Enter 15-word seed',
            _dependency('seedsigner.gui.components', 'FontAwesomeIconConstants').KEYBOARD,
            return_data=15,
        )
        TYPE_18WORD = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
            'Enter 18-word seed',
            _dependency('seedsigner.gui.components', 'FontAwesomeIconConstants').KEYBOARD,
            return_data=18,
        )
        TYPE_21WORD = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
            'Enter 21-word seed',
            _dependency('seedsigner.gui.components', 'FontAwesomeIconConstants').KEYBOARD,
            return_data=21,
        )
        TYPE_24WORD = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
            'Enter 24-word seed',
            _dependency('seedsigner.gui.components', 'FontAwesomeIconConstants').KEYBOARD,
            return_data=24,
        )
        LOADED_DESCRIPTOR = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
            'Loaded Multisig Descriptor'
        )
        SATOCHIP = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
            'Load from Satochip',
            _dependency('seedsigner.gui.components', 'SeedSignerIconConstants').FINGERPRINT,
        )
        TYPE_ELECTRUM = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
            'Electrum Seed',
            _dependency('seedsigner.gui.components', 'FontAwesomeIconConstants').KEYBOARD,
        )

        def run(self):
            seeds = self.controller.storage.seeds
            button_data = []
            for seed in seeds:
                button_str = seed.get_fingerprint(
                    self.settings.get_value(
                        _dependency(
                            'seedsigner.models.settings_definition', 'SettingsConstants'
                        ).SETTING__NETWORK
                    )
                )
                button_data.append(
                    _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
                        button_str,
                        _dependency(
                            'seedsigner.gui.components', 'SeedSignerIconConstants'
                        ).FINGERPRINT,
                    )
                )
            if self.controller.multisig_wallet_descriptor:
                button_data.append(self.LOADED_DESCRIPTOR)
            seed_lengths = self.settings.get_value(
                _dependency(
                    'seedsigner.models.settings_definition', 'SettingsConstants'
                ).SETTING__SEED_WORD_LENGTHS
            )
            options = {
                12: self.TYPE_12WORD,
                15: self.TYPE_15WORD,
                18: self.TYPE_18WORD,
                21: self.TYPE_21WORD,
                24: self.TYPE_24WORD,
            }
            button_data = button_data + [self.SCAN_SEED, self.SCAN_DESCRIPTOR]
            if (
                self.settings.get_value(
                    _dependency(
                        'seedsigner.models.settings_definition', 'SettingsConstants'
                    ).SETTING__SATOCHIP_SUPPORT
                )
                == _dependency(
                    'seedsigner.models.settings_definition', 'SettingsConstants'
                ).OPTION__ENABLED
            ):
                button_data.append(self.SATOCHIP)
            button_data += [options[l] for l in seed_lengths]
            if (
                self.settings.get_value(
                    _dependency(
                        'seedsigner.models.settings_definition', 'SettingsConstants'
                    ).SETTING__ELECTRUM_SEEDS
                )
                == _dependency(
                    'seedsigner.models.settings_definition', 'SettingsConstants'
                ).OPTION__ENABLED
            ):
                button_data.append(self.TYPE_ELECTRUM)
            selected_menu_num = self.run_screen(
                _dependency('seedsigner.gui.screens', 'ButtonListScreen'),
                title=_dependency('gettext', 'gettext')('Address Explorer'),
                button_data=button_data,
                is_button_text_centered=False,
                is_bottom_list=True,
            )
            if selected_menu_num == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _dependency('seedsigner.views.view', 'BackStackView')
                )
            self.controller.resume_main_flow = self.controller.FLOW__ADDRESS_EXPLORER
            if len(seeds) > 0 and selected_menu_num < len(seeds):
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _dependency('seedsigner.views.seed_views', 'SeedExportXpubScriptTypeView'),
                    view_args=dict(
                        seed=seeds[selected_menu_num],
                        sig_type=_dependency(
                            'seedsigner.models.settings_definition', 'SettingsConstants'
                        ).SINGLE_SIG,
                    ),
                )
            elif button_data[selected_menu_num] == self.LOADED_DESCRIPTOR:
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('ToolsAddressExplorerAddressTypeView')
                )
            elif button_data[selected_menu_num] == self.SCAN_SEED:
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _dependency('seedsigner.views.scan_views', 'ScanSeedQRView')
                )
            elif button_data[selected_menu_num] == self.SCAN_DESCRIPTOR:
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _dependency('seedsigner.views.scan_views', 'ScanWalletDescriptorView')
                )
            elif button_data[selected_menu_num] == self.SATOCHIP:
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    SatochipLoadDescriptorScriptTypeView
                )
            elif button_data[selected_menu_num] in [
                self.TYPE_12WORD,
                self.TYPE_15WORD,
                self.TYPE_18WORD,
                self.TYPE_21WORD,
                self.TYPE_24WORD,
            ]:
                self.controller.storage.init_pending_mnemonic(
                    num_words=button_data[selected_menu_num].return_data
                )
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _dependency('seedsigner.views.seed_views', 'SeedMnemonicEntryView')
                )
            elif button_data[selected_menu_num] == self.TYPE_ELECTRUM:
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _dependency('seedsigner.views.seed_views', 'SeedElectrumMnemonicStartView')
                )

    return ToolsAddressExplorerSelectSourceView


def _make_ToolsAddressExplorerAddressTypeView():

    class ToolsAddressExplorerAddressTypeView(_dependency('seedsigner.views.view', 'View')):
        RECEIVE = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Receive addresses')
        CHANGE = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Change addresses')

        def __init__(self, seed=None, script_type=None, custom_derivation=None, account=0):
            """
            If the explorer source is a seed, `seed` and `script_type` must be
            specified. `custom_derivation` can be specified as needed.

            If the source is a multisig or single sig wallet descriptor, `seed`,
            `script_type`, and `custom_derivation` should be `None`.
            """
            super().__init__()
            self.seed = seed
            self.script_type = script_type
            self.custom_derivation = custom_derivation
            self.account = account
            network = self.settings.get_value(
                _dependency(
                    'seedsigner.models.settings_definition', 'SettingsConstants'
                ).SETTING__NETWORK
            )
            data = dict(
                seed=seed,
                network=self.settings.get_value(
                    _dependency(
                        'seedsigner.models.settings_definition', 'SettingsConstants'
                    ).SETTING__NETWORK
                ),
                embit_network=_dependency(
                    'seedsigner.models.settings_definition', 'SettingsConstants'
                ).map_network_to_embit(network),
                script_type=script_type,
                account=account,
            )
            if self.seed is not None:
                data['seed'] = self.seed
                seed_derivation_override = self.seed.derivation_override(
                    sig_type=_dependency(
                        'seedsigner.models.settings_definition', 'SettingsConstants'
                    ).SINGLE_SIG
                )
                if (
                    self.script_type
                    == _dependency(
                        'seedsigner.models.settings_definition', 'SettingsConstants'
                    ).CUSTOM_DERIVATION
                ):
                    derivation_path = self.custom_derivation
                elif seed_derivation_override:
                    derivation_path = seed_derivation_override
                else:
                    derivation_path = _dependency(
                        'seedsigner.helpers', 'embit_utils'
                    ).get_standard_derivation_path(
                        network=self.settings.get_value(
                            _dependency(
                                'seedsigner.models.settings_definition', 'SettingsConstants'
                            ).SETTING__NETWORK
                        ),
                        wallet_type=_dependency(
                            'seedsigner.models.settings_definition', 'SettingsConstants'
                        ).SINGLE_SIG,
                        script_type=self.script_type,
                        account=self.account,
                    )
                data['derivation_path'] = derivation_path
                data['xpub'] = self.seed.get_xpub(derivation_path, network=network)
            else:
                data['wallet_descriptor'] = self.controller.multisig_wallet_descriptor
            self.controller.address_explorer_data = data

        def run(self):
            data = self.controller.address_explorer_data
            wallet_descriptor_display_name = None
            if 'wallet_descriptor' in data:
                if data['wallet_descriptor'].is_basic_multisig:
                    threshold, n = _dependency(
                        'seedsigner.helpers.embit_utils', 'get_multisig_policy'
                    )(data['wallet_descriptor'])
                    wallet_descriptor_display_name = _dependency('gettext', 'gettext')(
                        '{threshold} / {n} multisig'
                    ).format(threshold=threshold, n=n)
                else:
                    wallet_descriptor_display_name = (
                        data['wallet_descriptor'].brief_policy.split('multisig')[0].strip()
                    )
            script_type = data['script_type'] if 'script_type' in data else None
            button_data = [self.RECEIVE, self.CHANGE]
            selected_menu_num = self.run_screen(
                _dependency(
                    'seedsigner.gui.screens.tools_screens', 'ToolsAddressExplorerAddressTypeScreen'
                ),
                button_data=button_data,
                fingerprint=self.seed.get_fingerprint() if self.seed is not None else None,
                wallet_descriptor_display_name=wallet_descriptor_display_name,
                script_type=script_type,
                custom_derivation_path=self.custom_derivation,
            )
            if selected_menu_num == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                if len(self.controller.back_stack) > 1 and self.controller.back_stack[
                    -2
                ].View_cls == _dependency('seedsigner.views.seed_views', 'SeedOptionsView'):
                    self.controller.resume_main_flow = None
                    self.controller.address_explorer_data = None
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _dependency('seedsigner.views.view', 'BackStackView')
                )
            elif button_data[selected_menu_num] in [self.RECEIVE, self.CHANGE]:
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('ToolsAddressExplorerAddressListView'),
                    view_args=dict(is_change=button_data[selected_menu_num] == self.CHANGE),
                )

    return ToolsAddressExplorerAddressTypeView


def _make_ToolsAddressExplorerAddressListView():

    class ToolsAddressExplorerAddressListView(_dependency('seedsigner.views.view', 'View')):
        def __init__(
            self, is_change=False, start_index=0, selected_button_index=0, initial_scroll=0
        ):
            super().__init__()
            self.is_change = is_change
            self.start_index = start_index
            self.selected_button_index = selected_button_index
            self.initial_scroll = initial_scroll

        def run(self):
            self.loading_screen = None
            addresses = []
            button_data = []
            data = self.controller.address_explorer_data
            addrs_per_screen = 10
            addr_storage_key = 'receive_addrs'
            if self.is_change:
                addr_storage_key = 'change_addrs'
            if (
                addr_storage_key in data
                and len(data[addr_storage_key]) >= self.start_index + addrs_per_screen
            ):
                addresses = data[addr_storage_key][
                    self.start_index : self.start_index + addrs_per_screen
                ]
            else:
                try:
                    self.loading_screen = _dependency(
                        'seedsigner.gui.screens.screen', 'LoadingScreenThread'
                    )(text=_dependency('gettext', 'gettext')('Calculating addrs...'))
                    self.loading_screen.start()
                    if addr_storage_key not in data:
                        data[addr_storage_key] = []
                    if 'xpub' in data:
                        if (
                            'script_type' in data
                            and data['script_type']
                            != _dependency(
                                'seedsigner.models.settings_definition', 'SettingsConstants'
                            ).CUSTOM_DERIVATION
                        ):
                            for i in range(self.start_index, self.start_index + addrs_per_screen):
                                address = _dependency(
                                    'seedsigner.helpers', 'embit_utils'
                                ).get_single_sig_address(
                                    xpub=data['xpub'],
                                    script_type=data['script_type'],
                                    index=i,
                                    is_change=self.is_change,
                                    embit_network=data['embit_network'],
                                )
                                addresses.append(address)
                                data[addr_storage_key].append(address)
                        else:
                            raise Exception(
                                _dependency('gettext', 'gettext')(
                                    'Custom Derivation address explorer not yet implemented'
                                )
                            )
                    elif 'wallet_descriptor' in data:
                        descriptor = data['wallet_descriptor']
                        for i in range(self.start_index, self.start_index + addrs_per_screen):
                            address = _dependency(
                                'seedsigner.helpers', 'embit_utils'
                            ).get_multisig_address(
                                descriptor=descriptor,
                                index=i,
                                is_change=self.is_change,
                                embit_network=data['embit_network'],
                            )
                            addresses.append(address)
                            data[addr_storage_key].append(address)
                finally:
                    self.loading_screen.stop()
            selected_menu_num = self.run_screen(
                _dependency(
                    'seedsigner.gui.screens.tools_screens', 'ToolsAddressExplorerAddressListScreen'
                ),
                title=_dependency('gettext', 'gettext')('Receive Addrs')
                if not self.is_change
                else _dependency('gettext', 'gettext')('Change Addrs'),
                start_index=self.start_index,
                addresses=addresses,
                selected_button=self.selected_button_index,
                scroll_y_initial_offset=self.initial_scroll,
            )
            if selected_menu_num == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _dependency('seedsigner.views.view', 'BackStackView')
                )
            if selected_menu_num == len(addresses):
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('ToolsAddressExplorerAddressListView'),
                    view_args=dict(
                        is_change=self.is_change, start_index=self.start_index + addrs_per_screen
                    ),
                )
            initial_scroll = self.screen.buttons[0].scroll_y
            index = selected_menu_num + self.start_index
            return _dependency('seedsigner_port.navigation', 'Destination')(
                _resolve('ToolsAddressExplorerAddressView'),
                view_args=dict(
                    index=index,
                    address=addresses[selected_menu_num],
                    is_change=self.is_change,
                    start_index=self.start_index,
                    parent_initial_scroll=initial_scroll,
                ),
                skip_current_view=True,
            )

    return ToolsAddressExplorerAddressListView


def _make_ToolsAddressExplorerAddressView():

    class ToolsAddressExplorerAddressView(_dependency('seedsigner.views.view', 'View')):
        def __init__(self, index, address, is_change, start_index, parent_initial_scroll=0):
            super().__init__()
            self.index = index
            self.address = address
            self.is_change = is_change
            self.start_index = start_index
            self.parent_initial_scroll = parent_initial_scroll

        def run(self):
            qr_encoder = _dependency('seedsigner.models.encode_qr', 'GenericStaticQrEncoder')(
                data=self.address
            )
            self.run_screen(
                _dependency('seedsigner.gui.screens.screen', 'QRDisplayScreen'),
                qr_encoder=qr_encoder,
            )
            return _dependency('seedsigner_port.navigation', 'Destination')(
                _resolve('ToolsAddressExplorerAddressListView'),
                view_args=dict(
                    is_change=self.is_change,
                    start_index=self.start_index,
                    selected_button_index=self.index - self.start_index,
                    initial_scroll=self.parent_initial_scroll,
                ),
                skip_current_view=True,
            )

    return ToolsAddressExplorerAddressView


_FACTORIES = {
    'ToolsMenuView': _make_ToolsMenuView,
    'ToolsImageEntropyLivePreviewView': _make_ToolsImageEntropyLivePreviewView,
    'ToolsImageEntropyFinalImageView': _make_ToolsImageEntropyFinalImageView,
    'ToolsImageEntropyMnemonicLengthView': _make_ToolsImageEntropyMnemonicLengthView,
    'ToolsDiceEntropyMnemonicLengthView': _make_ToolsDiceEntropyMnemonicLengthView,
    'ToolsDiceEntropyEntryView': _make_ToolsDiceEntropyEntryView,
    'ToolsCalcFinalWordNumWordsView': _make_ToolsCalcFinalWordNumWordsView,
    'ToolsCalcFinalWordFinalizePromptView': _make_ToolsCalcFinalWordFinalizePromptView,
    'ToolsCalcFinalWordCoinFlipsView': _make_ToolsCalcFinalWordCoinFlipsView,
    'ToolsCalcFinalWordShowFinalWordView': _make_ToolsCalcFinalWordShowFinalWordView,
    'ToolsCalcFinalWordDoneView': _make_ToolsCalcFinalWordDoneView,
    'ToolsAddressExplorerSelectSourceView': _make_ToolsAddressExplorerSelectSourceView,
    'ToolsAddressExplorerAddressTypeView': _make_ToolsAddressExplorerAddressTypeView,
    'ToolsAddressExplorerAddressListView': _make_ToolsAddressExplorerAddressListView,
    'ToolsAddressExplorerAddressView': _make_ToolsAddressExplorerAddressView,
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
