# Copyright2021 SeedSigner; MIT, see ../LICENSE.SeedSigner
# Generated original Text QR / Password Generator Views; reviewed native boundaries.
import math
from seedsigner_port.decode_platform import dependency as _dependency, FeatureUnavailable
from seedsigner_port.password_support import capitalize as _capitalize

PASSWORD_TYPE_RANDOM = 'random'
PASSWORD_TYPE_DICEWARE_EFF_SHORT = 'diceware_eff_short'
PASSWORD_TYPE_DICEWARE_EFF_LONG = 'diceware_eff_long'
PASSWORD_TYPE_DICEWARE_BIP39 = 'diceware_bip39'
PASSWORD_TYPE_DICE_ROLLS = 'dice_rolls'
PASSWORD_TYPE_HEX = 'hex'
PASSWORD_TYPE_BASE64 = 'base64'
PASSWORD_TYPE_BASE85 = 'base85'
PASSWORD_WORD_SEPARATOR_NONE = 'none'
PASSWORD_WORD_SEPARATOR_CAPITALISE = 'capitalise'
PASSWORD_WORD_SEPARATOR_SPACE = 'space'
PASSWORD_WORD_SEPARATOR_DOT = 'dot'
PASSWORD_ENTROPY_CAMERA = 'camera'
PASSWORD_ENTROPY_DICE = 'dice'
PASSWORD_ENTROPY_BIP85 = 'bip85'
PASSWORD_ENTROPY_HARDWARE_RNG = 'hardware_rng'
BIP85_APP_HEX = 128169
BIP85_APP_BASE64 = 707764
BIP85_APP_BASE85 = 707785
BIP85_APP_DICE = 89101


def _make_ToolsTextQRTextEntryView():

    class ToolsTextQRTextEntryView(_dependency('seedsigner.views.view', 'View')):
        """
        initial_keyboard: used by the screenshot generator to render each different keyboard layout.
        """

        def __init__(self, textToEncode='', initial_keyboard=None):
            super().__init__()
            self.textToEncode = textToEncode
            self.initial_keyboard = initial_keyboard

        def run(self):
            ret_dict = _dependency('seedsigner.gui.screens', 'ToolsTextQRTextEntryScreen')(
                textToEncode=self.textToEncode,
                title=_dependency('gettext', 'gettext')('Text to Encode'),
                initial_keyboard=self.initial_keyboard,
            ).display()
            self.textToEncode = _dependency('seedsigner_port.password_support', 'text_unescape')(
                ret_dict['textToEncode']
            )
            if 'is_back_button' in ret_dict:
                if len(self.textToEncode) > 0:
                    return _dependency('seedsigner_port.navigation', 'Destination')(
                        _resolve('ToolsTextQRTextEntryExitDialogView'),
                        view_args=dict(text=self.textToEncode),
                        skip_current_view=True,
                    )
                else:
                    return _dependency('seedsigner_port.navigation', 'Destination')(
                        _dependency('seedsigner.views.view', 'BackStackView')
                    )
            else:
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('ToolsTextQRReviewTextView'),
                    view_args=dict(text=self.textToEncode),
                    skip_current_view=True,
                )

    return ToolsTextQRTextEntryView


def _make_ToolsTextQRTextEntryExitDialogView():

    class ToolsTextQRTextEntryExitDialogView(_dependency('seedsigner.views.view', 'View')):
        EDIT = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Edit text')
        DISCARD = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
            'Discard text', button_label_color='red'
        )

        def __init__(self, text):
            super().__init__()
            self.text = text

        def run(self):
            button_data = [self.EDIT, self.DISCARD]
            selected_menu_num = self.run_screen(
                _dependency('seedsigner.gui.screens', 'WarningScreen'),
                title=_dependency('gettext', 'gettext')('Discard text?'),
                status_headline=None,
                text='Your current text entry will be erased'.format(),
                show_back_button=False,
                button_data=button_data,
            )
            if button_data[selected_menu_num] == self.EDIT:
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('ToolsTextQRTextEntryView'),
                    view_args=dict(textToEncode=self.text),
                    skip_current_view=True,
                )
            elif button_data[selected_menu_num] == self.DISCARD:
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _dependency('seedsigner.views.view', 'BackStackView')
                )

    return ToolsTextQRTextEntryExitDialogView


def _make_ToolsTextQRReviewTextView():

    class ToolsTextQRReviewTextView(_dependency('seedsigner.views.view', 'View')):
        def __init__(self, text):
            super().__init__()
            self.text = text

        def run(self):
            ENCODE = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
                'Generate QR code'
            )
            EDIT = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Edit text')
            button_data = [ENCODE, EDIT]
            selected_menu_num = self.run_screen(
                _dependency('seedsigner.gui.screens', 'ToolsTextQRReviewTextScreen'),
                textToEncode=self.text,
                title=_dependency('gettext', 'gettext')('Text to Encode'),
                button_data=button_data,
            )
            if selected_menu_num == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _dependency('seedsigner.views.view', 'BackStackView')
                )
            if button_data[selected_menu_num] == ENCODE:
                num_modules = _dependency('seedsigner.helpers.qr', 'QR')().qrsize(data=self.text)
                if num_modules <= 33:
                    return _dependency('seedsigner_port.navigation', 'Destination')(
                        _resolve('ToolsTextQRTranscribeModePromptView'),
                        view_args=dict(text=self.text, num_modules=num_modules),
                    )
                else:
                    return _dependency('seedsigner_port.navigation', 'Destination')(
                        _resolve('ToolsTextQRFullScreenModeView'), view_args=dict(text=self.text)
                    )
            elif button_data[selected_menu_num] == EDIT:
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('ToolsTextQRTextEntryView'),
                    view_args=dict(textToEncode=self.text),
                    skip_current_view=True,
                )

    return ToolsTextQRReviewTextView


def _text_qr_done_destination(return_to_home=False):
    if return_to_home:
        return _dependency('seedsigner_port.navigation', 'Destination')(
            _dependency('seedsigner.views.tools_views', 'ToolsMenuView'), clear_history=True
        )
    return _dependency('seedsigner_port.navigation', 'Destination')(
        _resolve('ToolsTextQRView'), clear_history=True
    )


def _make_ToolsTextQRTranscribeModePromptView():

    class ToolsTextQRTranscribeModePromptView(_dependency('seedsigner.views.view', 'View')):
        def __init__(self, text, num_modules, return_to_home=False):
            super().__init__()
            self.text = text
            self.num_modules = num_modules
            self.return_to_home = return_to_home

        def run(self):
            TRANSCRIBE = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
                'Transcribe mode'
            )
            FULLSCREEN = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
                'FullScreen mode'
            )
            button_data = [TRANSCRIBE, FULLSCREEN]
            selected_menu_num = self.run_screen(
                _dependency('seedsigner.gui.screens', 'ToolsTextQRTranscribeModePromptScreen'),
                title=_dependency('gettext', 'gettext')('Transcribe Mode ?'),
                is_button_text_centered=False,
                button_data=button_data,
            )
            if selected_menu_num == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _dependency('seedsigner.views.view', 'BackStackView')
                )
            elif button_data[selected_menu_num] == TRANSCRIBE:
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('ToolsTextQRTranscribeModeView'),
                    view_args=dict(
                        text=self.text,
                        num_modules=self.num_modules,
                        return_to_home=self.return_to_home,
                    ),
                )
            elif button_data[selected_menu_num] == FULLSCREEN:
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('ToolsTextQRFullScreenModeView'),
                    view_args=dict(text=self.text, return_to_home=self.return_to_home),
                )

    return ToolsTextQRTranscribeModePromptView


def _make_ToolsTextQRTranscribeModeView():

    class ToolsTextQRTranscribeModeView(_dependency('seedsigner.views.view', 'View')):
        def __init__(self, text, num_modules, return_to_home=False):
            super().__init__()
            self.text = text
            self.num_modules = num_modules
            self.return_to_home = return_to_home

        def run(self):
            ret = _dependency('seedsigner.gui.screens', 'ToolsTranscribeTextQRWholeQRScreen')(
                qr_data=self.text, num_modules=self.num_modules
            ).display()
            if ret == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _dependency('seedsigner.views.view', 'BackStackView')
                )
            else:
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('ToolsTranscribeTextQRZoomedInView'),
                    view_args=dict(
                        text=self.text,
                        num_modules=self.num_modules,
                        return_to_home=self.return_to_home,
                    ),
                )

    return ToolsTextQRTranscribeModeView


def _make_ToolsTextQRFullScreenModeView():

    class ToolsTextQRFullScreenModeView(_dependency('seedsigner.views.view', 'View')):
        def __init__(self, text, return_to_home=False):
            super().__init__()
            self.text = text
            self.return_to_home = return_to_home

        def run(self):
            encoder_args = dict(data=self.text)
            e = _dependency('seedsigner.models.encode_qr', 'GenericStaticQrEncoder')(**encoder_args)
            _dependency('seedsigner.gui.screens.screen', 'QRDisplayScreen')(qr_encoder=e).display()
            return _resolve('_text_qr_done_destination')(self.return_to_home)

    return ToolsTextQRFullScreenModeView


def _make_ToolsTranscribeTextQRZoomedInView():

    class ToolsTranscribeTextQRZoomedInView(_dependency('seedsigner.views.view', 'View')):
        def __init__(self, text, num_modules, return_to_home=False):
            super().__init__()
            self.text = text
            self.num_modules = num_modules
            self.return_to_home = return_to_home

        def run(self):
            _dependency('seedsigner.gui.screens', 'ToolsTranscribeTextQRZoomedInScreen')(
                qr_data=self.text, num_modules=self.num_modules
            ).display()
            return _dependency('seedsigner_port.navigation', 'Destination')(
                _resolve('ToolsTranscribeTextQRConfirmQRPromptView'),
                view_args=dict(text=self.text, return_to_home=self.return_to_home),
            )

    return ToolsTranscribeTextQRZoomedInView


def _make_ToolsTranscribeTextQRConfirmQRPromptView():

    class ToolsTranscribeTextQRConfirmQRPromptView(_dependency('seedsigner.views.view', 'View')):
        def __init__(self, text, return_to_home=False):
            super().__init__()
            self.text = text
            self.return_to_home = return_to_home

        def run(self):
            SCAN = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
                'Confirm text QR code'
            )
            DONE = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Done')
            button_data = [SCAN, DONE]
            selected_menu_option = _dependency(
                'seedsigner.gui.screens', 'ToolsTranscribeTextQRConfirmQRPromptScreen'
            )(
                title=_dependency('gettext', 'gettext')('Confirm Text QR ?'),
                button_data=button_data,
            ).display()
            if selected_menu_option == _dependency(
                'seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'
            ):
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _dependency('seedsigner.views.view', 'BackStackView')
                )
            elif button_data[selected_menu_option] == SCAN:
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('ToolsTranscribeTextQRConfirmScanView'),
                    view_args=dict(text=self.text, return_to_home=self.return_to_home),
                )
            elif button_data[selected_menu_option] == DONE:
                return _resolve('_text_qr_done_destination')(self.return_to_home)

    return ToolsTranscribeTextQRConfirmQRPromptView


def _make_ToolsTranscribeTextQRConfirmScanView():

    class ToolsTranscribeTextQRConfirmScanView(_dependency('seedsigner.views.view', 'View')):
        def __init__(self, text, return_to_home=False):
            super().__init__()
            self.text = text
            self.return_to_home = return_to_home

        def run(self):
            decoder = _dependency('seedsigner.models.decode_qr', 'DecodeQR')(is_text=True)
            _dependency('seedsigner.gui.screens.scan_screens', 'ScanScreen')(
                instructions_text=_dependency('gettext', 'gettext')('Scan text QR code'),
                decoder=decoder,
            ).display()
            self.controller.reset_screensaver_timeout()
            _dependency('seedsigner_port.clock', None).sleep(0.1)
            if decoder.is_complete:
                if decoder.get_text() != self.text:
                    _dependency('seedsigner.gui.screens', 'DireWarningScreen')(
                        title=_dependency('gettext', 'gettext')('Confirm Text QR Code'),
                        status_headline=_dependency('gettext', 'gettext')('Error!'),
                        text=_dependency('gettext', 'gettext')(
                            'Your transcribed text QR code does not match your original text!'
                        ),
                        show_back_button=False,
                        button_data=[
                            _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
                                'Review text QR code'
                            )
                        ],
                    ).display()
                    return _dependency('seedsigner_port.navigation', 'Destination')(
                        _dependency('seedsigner.views.view', 'BackStackView')
                    )
                else:
                    _dependency('seedsigner.gui.screens', 'LargeIconStatusScreen')(
                        title=_dependency('gettext', 'gettext')('Confirm Text QR Code'),
                        status_headline=_dependency('gettext', 'gettext')('Success!'),
                        text=_dependency('gettext', 'gettext')(
                            'Your transcribed text QR code successfully scanned and yielded the same text.'
                        ),
                        show_back_button=False,
                        button_data=[
                            _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('OK')
                        ],
                    ).display()
                    return _resolve('_text_qr_done_destination')(self.return_to_home)
            else:
                _dependency('seedsigner.gui.screens', 'DireWarningScreen')(
                    title=_dependency('gettext', 'gettext')('Confirm Text QR'),
                    status_headline=_dependency('gettext', 'gettext')('Error!'),
                    text=_dependency('gettext', 'gettext')(
                        'Your transcribed text QR code could not be read!'
                    ),
                    show_back_button=False,
                    button_data=[
                        _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
                            'Review text QR code'
                        )
                    ],
                ).display()
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _dependency('seedsigner.views.view', 'BackStackView')
                )

    return ToolsTranscribeTextQRConfirmScanView


def _make_ToolsTextQRScanQRCodeView():

    class ToolsTextQRScanQRCodeView(_dependency('seedsigner.views.view', 'View')):
        def run(self):
            decoder = _dependency('seedsigner.models.decode_qr', 'DecodeQR')(is_text=True)
            _dependency('seedsigner.gui.screens.scan_screens', 'ScanScreen')(
                decoder=decoder,
                instructions_text=_dependency('gettext', 'gettext')('Scan text QR code'),
            ).display()
            self.controller.reset_screensaver_timeout()
            _dependency('seedsigner_port.clock', None).sleep(0.1)
            if decoder.is_complete:
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('ToolsTextQRReviewTextView2'),
                    view_args=dict(text=decoder.get_text()),
                    skip_current_view=True,
                )
            elif decoder.is_nonUTF8:
                _dependency('seedsigner.gui.screens', 'DireWarningScreen')(
                    title=_dependency('gettext', 'gettext')('Error!'),
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

    return ToolsTextQRScanQRCodeView


def _make_ToolsTextQRReviewTextView2():

    class ToolsTextQRReviewTextView2(_dependency('seedsigner.views.view', 'View')):
        def __init__(self, text):
            super().__init__()
            self.text = text

        def run(self):
            EDIT = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
                'Edit & Generate QR code'
            )
            DONE = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Done')
            button_data = [EDIT, DONE]
            selected_menu_num = self.run_screen(
                _dependency('seedsigner.gui.screens', 'ToolsTextQRReviewTextScreen'),
                textToEncode=self.text,
                title=_dependency('gettext', 'gettext')('Decoded Text'),
                button_data=button_data,
                show_back_button=False,
            )
            if button_data[selected_menu_num] == EDIT:
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('ToolsTextQRTextEntryView'), view_args=dict(textToEncode=self.text)
                )
            elif button_data[selected_menu_num] == DONE:
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _dependency('seedsigner.views.view', 'BackStackView')
                )

    return ToolsTextQRReviewTextView2


def _clear_password_entropy_cache(controller):
    controller.password_generator_entropy_cache = None


def _cache_password_entropy(
    controller,
    *,
    password_type,
    strength_bits,
    entropy_source,
    word_count,
    roll_data=None,
    entropy_bytes=None,
):
    controller.password_generator_entropy_cache = {
        'password_type': password_type,
        'strength_bits': strength_bits,
        'entropy_source': entropy_source,
        'word_count': word_count,
        'roll_data': roll_data,
        'entropy_bytes': entropy_bytes,
    }


def _get_password_entropy_cache(controller):
    return getattr(controller, 'password_generator_entropy_cache', None)


def _random_charset(random_options):
    keys_lower = 'abcdefghijklmnopqrstuvwxyz'
    keys_upper = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    keys_number = '0123456789'
    keys_symbol_1 = '!@#$%&();:,.-+=\'"?'
    keys_symbol_2 = '^*[]{}_\\|<>/`~'
    charset = ''
    if random_options.get('lower'):
        charset += keys_lower
    if random_options.get('upper'):
        charset += keys_upper
    if random_options.get('digits'):
        charset += keys_number
    if random_options.get('special'):
        charset += keys_symbol_1 + keys_symbol_2
    return charset


def _bip85_supported_password_type(password_type):
    return password_type in {
        PASSWORD_TYPE_DICEWARE_EFF_SHORT,
        PASSWORD_TYPE_DICEWARE_EFF_LONG,
        PASSWORD_TYPE_DICEWARE_BIP39,
        PASSWORD_TYPE_DICE_ROLLS,
        PASSWORD_TYPE_HEX,
        PASSWORD_TYPE_BASE64,
        PASSWORD_TYPE_BASE85,
    }


def _strength_to_length(entropy_bits, alphabet_size):
    return max(
        1,
        _dependency('math', None).ceil(
            entropy_bits / _dependency('math', None).log2(alphabet_size)
        ),
    )


def _dice_rolls_for_strength(entropy_bits):
    return max(1, _dependency('math', None).ceil(entropy_bits / _dependency('math', None).log2(6)))


def _is_diceware_password_type(password_type):
    return password_type in {
        PASSWORD_TYPE_DICEWARE_EFF_SHORT,
        PASSWORD_TYPE_DICEWARE_EFF_LONG,
        PASSWORD_TYPE_DICEWARE_BIP39,
    }


def _diceware_word_count(password_type, entropy_bits):
    if password_type == PASSWORD_TYPE_DICEWARE_EFF_SHORT:
        word_bits = _dependency('math', None).log2(1296)
    elif password_type == PASSWORD_TYPE_DICEWARE_EFF_LONG:
        word_bits = _dependency('math', None).log2(7776)
    else:
        word_bits = 11
    return max(1, _dependency('math', None).ceil(entropy_bits / word_bits))


def _format_word_password(words, separator):
    if separator == PASSWORD_WORD_SEPARATOR_CAPITALISE:
        return ''.join((_capitalize(word) for word in words))
    if separator == PASSWORD_WORD_SEPARATOR_SPACE:
        return ' '.join(words)
    if separator == PASSWORD_WORD_SEPARATOR_DOT:
        return '.'.join(words)
    return ''.join(words)


def _make_ToolsTextQRView():

    class ToolsTextQRView(_dependency('seedsigner.views.view', 'View')):
        def run(self):
            ENCODE = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Encode text')
            DECODE = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Decode QR code')
            button_data = [ENCODE, DECODE]
            selected_menu_num = self.run_screen(
                _dependency('seedsigner.gui.screens', 'ButtonListScreen'),
                title=_dependency('gettext', 'gettext')('Text QR Code'),
                is_button_text_centered=False,
                button_data=button_data,
            )
            if selected_menu_num == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _dependency('seedsigner.views.view', 'BackStackView')
                )
            elif button_data[selected_menu_num] == ENCODE:
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('ToolsTextQRTextEntryView')
                )
            elif button_data[selected_menu_num] == DECODE:
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('ToolsTextQRScanQRCodeView')
                )

    return ToolsTextQRView


def _make_ToolsPasswordGeneratorTypeView():

    class ToolsPasswordGeneratorTypeView(_dependency('seedsigner.views.view', 'View')):
        def run(self):
            options = [
                (
                    _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Custom'),
                    PASSWORD_TYPE_RANDOM,
                ),
                (
                    _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
                        'Diceware-EFF Short'
                    ),
                    PASSWORD_TYPE_DICEWARE_EFF_SHORT,
                ),
                (
                    _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
                        'Diceware-EFF Long'
                    ),
                    PASSWORD_TYPE_DICEWARE_EFF_LONG,
                ),
                (
                    _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Diceware-BIP39'),
                    PASSWORD_TYPE_DICEWARE_BIP39,
                ),
                (
                    _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Base85'),
                    PASSWORD_TYPE_BASE85,
                ),
                (
                    _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Base64'),
                    PASSWORD_TYPE_BASE64,
                ),
                (
                    _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Hex'),
                    PASSWORD_TYPE_HEX,
                ),
                (
                    _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Dice Rolls'),
                    PASSWORD_TYPE_DICE_ROLLS,
                ),
            ]
            button_data = [button for button, _unused in options]
            selected_menu_num = self.run_screen(
                _dependency('seedsigner.gui.screens', 'ButtonListScreen'),
                title=_dependency('gettext', 'gettext')('Password Type'),
                is_button_text_centered=False,
                button_data=button_data,
            )
            if selected_menu_num == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _dependency('seedsigner.views.view', 'BackStackView')
                )
            password_type = options[selected_menu_num][1]
            if password_type == PASSWORD_TYPE_DICE_ROLLS:
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('ToolsPasswordDiceRollCountView'),
                    view_args=dict(
                        password_type=password_type, strength_bits=64, entropy_source=None
                    ),
                )
            return _dependency('seedsigner_port.navigation', 'Destination')(
                _resolve('ToolsPasswordStrengthView'), view_args=dict(password_type=password_type)
            )

    return ToolsPasswordGeneratorTypeView


def _make_ToolsPasswordStrengthView():

    class ToolsPasswordStrengthView(_dependency('seedsigner.views.view', 'View')):
        def __init__(self, password_type):
            super().__init__()
            self.password_type = password_type

        def run(self):
            options = [
                _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
                    '64 bits', return_data=64
                ),
                _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
                    '128 bits', return_data=128
                ),
                _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
                    '256 bits', return_data=256
                ),
            ]
            selected_menu_num = self.run_screen(
                _dependency('seedsigner.gui.screens', 'ButtonListScreen'),
                title=_dependency('gettext', 'gettext')('Password Strength'),
                is_button_text_centered=False,
                selected_button=1,
                button_data=options,
            )
            if selected_menu_num == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _dependency('seedsigner.views.view', 'BackStackView')
                )
            strength_bits = options[selected_menu_num].return_data
            if self.password_type == PASSWORD_TYPE_RANDOM:
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('ToolsPasswordRandomOptionsView'),
                    view_args=dict(password_type=self.password_type, strength_bits=strength_bits),
                )
            return _dependency('seedsigner_port.navigation', 'Destination')(
                _resolve('ToolsPasswordEntropySourceView'),
                view_args=dict(password_type=self.password_type, strength_bits=strength_bits),
            )

    return ToolsPasswordStrengthView


def _make_ToolsPasswordRandomOptionsView():

    class ToolsPasswordRandomOptionsView(_dependency('seedsigner.views.view', 'View')):
        def __init__(self, password_type, strength_bits):
            super().__init__()
            self.password_type = password_type
            self.strength_bits = strength_bits

        def _prompt_choice(self, title):
            yes = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Yes')
            no = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('No')
            selected = self.run_screen(
                _dependency('seedsigner.gui.screens', 'ButtonListScreen'),
                title=title,
                is_button_text_centered=True,
                button_data=[yes, no],
            )
            if selected == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                return None
            return selected == 0

        def run(self):
            while True:
                lower = self._prompt_choice('Lowercase?')
                if lower is None:
                    return _dependency('seedsigner_port.navigation', 'Destination')(
                        _dependency('seedsigner.views.view', 'BackStackView')
                    )
                upper = self._prompt_choice('Uppercase?')
                if upper is None:
                    return _dependency('seedsigner_port.navigation', 'Destination')(
                        _dependency('seedsigner.views.view', 'BackStackView')
                    )
                digits = self._prompt_choice('Numbers?')
                if digits is None:
                    return _dependency('seedsigner_port.navigation', 'Destination')(
                        _dependency('seedsigner.views.view', 'BackStackView')
                    )
                special = self._prompt_choice('Specials?')
                if special is None:
                    return _dependency('seedsigner_port.navigation', 'Destination')(
                        _dependency('seedsigner.views.view', 'BackStackView')
                    )
                random_options = {
                    'lower': lower,
                    'upper': upper,
                    'digits': digits,
                    'special': special,
                }
                if any(random_options.values()):
                    return _dependency('seedsigner_port.navigation', 'Destination')(
                        _resolve('ToolsPasswordEntropySourceView'),
                        view_args=dict(
                            password_type=self.password_type,
                            strength_bits=self.strength_bits,
                            random_options=random_options,
                        ),
                    )
                self.run_screen(
                    _dependency('seedsigner.gui.screens', 'WarningScreen'),
                    title=_dependency('gettext', 'gettext')('Select Options'),
                    status_headline=None,
                    text=_dependency('gettext', 'gettext')('Choose at least one character set.'),
                    show_back_button=False,
                    button_data=[
                        _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('I Understand')
                    ],
                )

    return ToolsPasswordRandomOptionsView


def _make_ToolsPasswordEntropySourceView():

    class ToolsPasswordEntropySourceView(_dependency('seedsigner.views.view', 'View')):
        def __init__(
            self,
            password_type,
            strength_bits,
            random_options=None,
            dice_sides=None,
            roll_count=None,
        ):
            super().__init__()
            self.password_type = password_type
            self.strength_bits = strength_bits
            self.random_options = random_options or {}
            self.dice_sides = dice_sides
            self.roll_count = roll_count

        def _hardware_rng_available(self):
            if self.controller.hardware_rng_is_healthy:
                return True
            reason = self.controller.hardware_rng_failure_reason or _dependency(
                'gettext', 'gettext'
            )('System RNG health check failed.')
            self.run_screen(
                _dependency('seedsigner.gui.screens', 'WarningScreen'),
                title=_dependency('gettext', 'gettext')('System RNG Error'),
                status_headline=None,
                text=reason,
                show_back_button=False,
                button_data=[
                    _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('I Understand')
                ],
            )
            return False

        def run(self):
            _resolve('_clear_password_entropy_cache')(self.controller)
            camera = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Camera')
            dice = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Dice')
            hardware_rng = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
                'System RNG'
            )
            bip85 = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('BIP85')
            if self.password_type == PASSWORD_TYPE_DICE_ROLLS:
                button_data = [camera, hardware_rng, bip85]
            else:
                button_data = [camera, dice, hardware_rng, bip85]
            selected_menu_num = self.run_screen(
                _dependency('seedsigner.gui.screens', 'ButtonListScreen'),
                title=_dependency('gettext', 'gettext')('Entropy Source'),
                is_button_text_centered=False,
                button_data=button_data,
            )
            if selected_menu_num == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _dependency('seedsigner.views.view', 'BackStackView')
                )
            selected = button_data[selected_menu_num]
            if selected == bip85 and (
                not _resolve('_bip85_supported_password_type')(self.password_type)
            ):
                self.run_screen(
                    _dependency('seedsigner.gui.screens', 'WarningScreen'),
                    title=_dependency('gettext', 'gettext')('Not Supported'),
                    status_headline=None,
                    text=_dependency('gettext', 'gettext')(
                        'BIP85 supports Diceware, Dice Rolls, Hex, Base64, and Base85.'
                    ),
                    show_back_button=False,
                    button_data=[
                        _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('I Understand')
                    ],
                )
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('ToolsPasswordEntropySourceView'),
                    view_args=dict(
                        password_type=self.password_type,
                        strength_bits=self.strength_bits,
                        random_options=self.random_options,
                    ),
                )
            if selected == camera:
                if self.password_type in {
                    PASSWORD_TYPE_DICEWARE_EFF_SHORT,
                    PASSWORD_TYPE_DICEWARE_EFF_LONG,
                    PASSWORD_TYPE_DICEWARE_BIP39,
                }:
                    return _dependency('seedsigner_port.navigation', 'Destination')(
                        _dependency(
                            'seedsigner.views.tools_views', 'ToolsImageEntropyLivePreviewView'
                        ),
                        view_args=dict(
                            next_view=_resolve('ToolsPasswordWordSeparatorView'),
                            next_view_args=dict(
                                password_type=self.password_type,
                                strength_bits=self.strength_bits,
                                random_options=self.random_options,
                                entropy_source=PASSWORD_ENTROPY_CAMERA,
                            ),
                        ),
                    )
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _dependency('seedsigner.views.tools_views', 'ToolsImageEntropyLivePreviewView'),
                    view_args=dict(
                        next_view=_resolve('ToolsPasswordGenerateView'),
                        next_view_args=dict(
                            password_type=self.password_type,
                            strength_bits=self.strength_bits,
                            entropy_source=PASSWORD_ENTROPY_CAMERA,
                            random_options=self.random_options,
                            roll_count=self.roll_count,
                            dice_sides=self.dice_sides or 6,
                        ),
                    ),
                )
            if selected == dice:
                if (
                    self.password_type == PASSWORD_TYPE_DICE_ROLLS
                    and self.dice_sides is not None
                    and (self.roll_count is not None)
                ):
                    return _dependency('seedsigner_port.navigation', 'Destination')(
                        _resolve('ToolsPasswordDiceEntryView'),
                        view_args=dict(
                            password_type=self.password_type,
                            random_options=self.random_options,
                            strength_bits=self.strength_bits,
                            total_rolls=self.roll_count,
                            word_count=None,
                            entropy_source=PASSWORD_ENTROPY_DICE,
                            dice_sides=self.dice_sides,
                        ),
                        skip_current_view=True,
                    )
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('ToolsPasswordDiceRollCountView'),
                    view_args=dict(
                        password_type=self.password_type,
                        strength_bits=self.strength_bits,
                        random_options=self.random_options,
                        entropy_source=PASSWORD_ENTROPY_DICE,
                    ),
                )
            if selected == hardware_rng:
                if not self._hardware_rng_available():
                    return _dependency('seedsigner_port.navigation', 'Destination')(
                        _dependency('seedsigner.views.view', 'BackStackView')
                    )
                if _resolve('_is_diceware_password_type')(getattr(self, 'password_type', None)):
                    return _dependency('seedsigner_port.navigation', 'Destination')(
                        _resolve('ToolsPasswordHardwareRngEntropyView'),
                        view_args=dict(
                            password_type=self.password_type,
                            strength_bits=self.strength_bits,
                            random_options=self.random_options,
                        ),
                    )
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('ToolsPasswordGenerateView'),
                    view_args=dict(
                        password_type=self.password_type,
                        strength_bits=self.strength_bits,
                        entropy_source=PASSWORD_ENTROPY_HARDWARE_RNG,
                        random_options=self.random_options,
                        roll_count=self.roll_count,
                        dice_sides=self.dice_sides or 6,
                    ),
                )
            return _dependency('seedsigner_port.navigation', 'Destination')(
                _resolve('ToolsPasswordBIP85GenerateView'),
                view_args=dict(
                    password_type=self.password_type,
                    strength_bits=self.strength_bits,
                    random_options=self.random_options,
                    dice_sides=self.dice_sides,
                    roll_count=self.roll_count,
                ),
            )

    return ToolsPasswordEntropySourceView


def _make_ToolsPasswordHardwareRngEntropyView():

    class ToolsPasswordHardwareRngEntropyView(_dependency('seedsigner.views.view', 'View')):
        def __init__(self, password_type, strength_bits, random_options=None):
            super().__init__()
            self.password_type = password_type
            self.strength_bits = strength_bits
            self.random_options = random_options or {}

        def run(self):
            if not self.controller.hardware_rng_is_healthy:
                self.run_screen(
                    _dependency('seedsigner.gui.screens', 'WarningScreen'),
                    title=_dependency('gettext', 'gettext')('System RNG Error'),
                    status_headline=None,
                    text=self.controller.hardware_rng_failure_reason
                    or _dependency('gettext', 'gettext')('System RNG health check failed.'),
                    show_back_button=False,
                    button_data=[
                        _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('I Understand')
                    ],
                )
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _dependency('seedsigner.views.view', 'BackStackView')
                )
            entropy_bytes = _dependency(
                'seedsigner_port.password_support', 'hardware_rng_unavailable'
            )()
            _resolve('_cache_password_entropy')(
                self.controller,
                password_type=self.password_type,
                strength_bits=self.strength_bits,
                entropy_source=PASSWORD_ENTROPY_HARDWARE_RNG,
                word_count=_resolve('_diceware_word_count')(self.password_type, self.strength_bits),
                roll_data=None,
                entropy_bytes=entropy_bytes,
            )
            return _dependency('seedsigner_port.navigation', 'Destination')(
                _resolve('ToolsPasswordWordSeparatorView'),
                view_args=dict(
                    password_type=self.password_type,
                    strength_bits=self.strength_bits,
                    random_options=self.random_options,
                    entropy_source=PASSWORD_ENTROPY_HARDWARE_RNG,
                ),
                skip_current_view=True,
            )

    return ToolsPasswordHardwareRngEntropyView


def _make_ToolsPasswordWordSeparatorView():

    class ToolsPasswordWordSeparatorView(_dependency('seedsigner.views.view', 'View')):
        def __init__(
            self,
            password_type,
            strength_bits,
            random_options=None,
            entropy_source=PASSWORD_ENTROPY_DICE,
        ):
            super().__init__()
            self.password_type = password_type
            self.strength_bits = strength_bits
            self.random_options = random_options or {}
            self.entropy_source = entropy_source

        def run(self):
            cached_entropy = _resolve('_get_password_entropy_cache')(self.controller)
            separator_options = [
                (
                    _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('None'),
                    PASSWORD_WORD_SEPARATOR_NONE,
                ),
                (
                    _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Capitalise'),
                    PASSWORD_WORD_SEPARATOR_CAPITALISE,
                ),
                (
                    _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Space'),
                    PASSWORD_WORD_SEPARATOR_SPACE,
                ),
                (
                    _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('.'),
                    PASSWORD_WORD_SEPARATOR_DOT,
                ),
            ]
            selected_menu_num = self.run_screen(
                _dependency('seedsigner.gui.screens', 'ButtonListScreen'),
                title=_dependency('gettext', 'gettext')('Separator'),
                is_button_text_centered=False,
                selected_button=1,
                button_data=[button for button, _unused in separator_options],
            )
            if selected_menu_num == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                _resolve('_clear_password_entropy_cache')(self.controller)
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('ToolsPasswordEntropySourceView'),
                    view_args=dict(
                        password_type=self.password_type,
                        strength_bits=self.strength_bits,
                        random_options=self.random_options,
                    ),
                    skip_current_view=True,
                )
            word_separator = separator_options[selected_menu_num][1]
            if (
                cached_entropy
                and cached_entropy.get('password_type') == self.password_type
                and (cached_entropy.get('strength_bits') == self.strength_bits)
                and (cached_entropy.get('entropy_source') == self.entropy_source)
            ):
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('ToolsPasswordGenerateView'),
                    view_args=dict(
                        password_type=self.password_type,
                        entropy_source=self.entropy_source,
                        random_options=self.random_options,
                        strength_bits=self.strength_bits,
                        word_count=cached_entropy.get('word_count'),
                        word_separator=word_separator,
                        roll_data=cached_entropy.get('roll_data'),
                        entropy_bytes_override=cached_entropy.get('entropy_bytes'),
                    ),
                    skip_current_view=True,
                )
            return _dependency('seedsigner_port.navigation', 'Destination')(
                _resolve('ToolsPasswordDiceRollCountView'),
                view_args=dict(
                    password_type=self.password_type,
                    strength_bits=self.strength_bits,
                    random_options=self.random_options,
                    word_separator=word_separator,
                    entropy_source=self.entropy_source,
                ),
            )

    return ToolsPasswordWordSeparatorView


def _make_ToolsPasswordDiceRollCountView():

    class ToolsPasswordDiceRollCountView(_dependency('seedsigner.views.view', 'View')):
        def __init__(
            self,
            password_type,
            strength_bits,
            random_options=None,
            word_separator=PASSWORD_WORD_SEPARATOR_NONE,
            entropy_source=PASSWORD_ENTROPY_DICE,
        ):
            super().__init__()
            self.password_type = password_type
            self.strength_bits = strength_bits
            self.random_options = random_options or {}
            self.word_separator = word_separator
            self.entropy_source = entropy_source

        def _prompt_dice_sides(self):
            side_options = [
                _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
                    '6 sides', return_data=6
                ),
                _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
                    '10 sides', return_data=10
                ),
                _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
                    '20 sides', return_data=20
                ),
            ]
            selected_menu_num = self.run_screen(
                _dependency('seedsigner.gui.screens', 'ButtonListScreen'),
                title=_dependency('gettext', 'gettext')('Dice Sides'),
                is_button_text_centered=False,
                selected_button=0,
                button_data=side_options,
            )
            if selected_menu_num == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                return None
            return int(side_options[selected_menu_num].return_data)

        def _prompt_roll_count(self):
            ret = (
                _dependency('seedsigner.gui.screens', 'seed_screens')
                .SeedBIP85SelectChildIndexScreen(
                    title=_dependency('gettext', 'gettext')('Number of Rolls')
                )
                .display()
            )
            if ret == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                return None
            if not ret:
                return 0
            return int(ret)

        def run(self):
            if self.password_type in {
                PASSWORD_TYPE_DICEWARE_EFF_SHORT,
                PASSWORD_TYPE_DICEWARE_EFF_LONG,
                PASSWORD_TYPE_DICEWARE_BIP39,
            } and self.entropy_source in {PASSWORD_ENTROPY_CAMERA, PASSWORD_ENTROPY_HARDWARE_RNG}:
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('ToolsPasswordGenerateView'),
                    view_args=dict(
                        password_type=self.password_type,
                        entropy_source=self.entropy_source,
                        random_options=self.random_options,
                        strength_bits=self.strength_bits,
                        word_count=_resolve('_diceware_word_count')(
                            self.password_type, self.strength_bits
                        ),
                        word_separator=self.word_separator,
                    ),
                    skip_current_view=True,
                )
            if self.password_type == PASSWORD_TYPE_DICE_ROLLS:
                dice_sides = self._prompt_dice_sides()
                if dice_sides is None:
                    return _dependency('seedsigner_port.navigation', 'Destination')(
                        _dependency('seedsigner.views.view', 'BackStackView')
                    )
                roll_count = self._prompt_roll_count()
                if roll_count is None:
                    return _dependency('seedsigner_port.navigation', 'Destination')(
                        _dependency('seedsigner.views.view', 'BackStackView')
                    )
                if roll_count < 1:
                    self.run_screen(
                        _dependency('seedsigner.gui.screens', 'WarningScreen'),
                        title=_dependency('gettext', 'gettext')('Invalid Input'),
                        status_headline=None,
                        text=_dependency('gettext', 'gettext')(
                            'Number of rolls must be at least 1.'
                        ),
                        show_back_button=False,
                        button_data=[
                            _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
                                'I Understand'
                            )
                        ],
                    )
                    return _dependency('seedsigner_port.navigation', 'Destination')(
                        _dependency('seedsigner.views.view', 'BackStackView')
                    )
                if self.entropy_source is None:
                    return _dependency('seedsigner_port.navigation', 'Destination')(
                        _resolve('ToolsPasswordEntropySourceView'),
                        view_args=dict(
                            password_type=self.password_type,
                            strength_bits=self.strength_bits,
                            random_options=self.random_options,
                            dice_sides=dice_sides,
                            roll_count=roll_count,
                        ),
                        skip_current_view=True,
                    )
                if self.entropy_source == PASSWORD_ENTROPY_DICE:
                    return _dependency('seedsigner_port.navigation', 'Destination')(
                        _resolve('ToolsPasswordDiceEntryView'),
                        view_args=dict(
                            password_type=self.password_type,
                            random_options=self.random_options,
                            strength_bits=self.strength_bits,
                            total_rolls=roll_count,
                            word_count=None,
                            word_separator=self.word_separator,
                            entropy_source=PASSWORD_ENTROPY_DICE,
                            dice_sides=dice_sides,
                        ),
                        skip_current_view=True,
                    )
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('ToolsPasswordGenerateView'),
                    view_args=dict(
                        password_type=self.password_type,
                        entropy_source=self.entropy_source,
                        random_options=self.random_options,
                        strength_bits=self.strength_bits,
                        roll_count=roll_count,
                        word_count=None,
                        word_separator=self.word_separator,
                        dice_sides=dice_sides,
                    ),
                    skip_current_view=True,
                )
            word_count = None
            if self.password_type in {
                PASSWORD_TYPE_DICEWARE_EFF_SHORT,
                PASSWORD_TYPE_DICEWARE_EFF_LONG,
                PASSWORD_TYPE_DICEWARE_BIP39,
            }:
                word_count = _resolve('_diceware_word_count')(
                    self.password_type, self.strength_bits
                )
                if self.password_type == PASSWORD_TYPE_DICEWARE_EFF_SHORT:
                    total_rolls = word_count * 4
                elif self.password_type == PASSWORD_TYPE_DICEWARE_EFF_LONG:
                    total_rolls = word_count * 5
                else:
                    total_rolls = max(
                        1,
                        _dependency('math', None).ceil(
                            word_count * 11 / _dependency('math', None).log2(6)
                        ),
                    )
            else:
                total_rolls = _resolve('_dice_rolls_for_strength')(self.strength_bits)
            return _dependency('seedsigner_port.navigation', 'Destination')(
                _resolve('ToolsPasswordDiceEntryView'),
                view_args=dict(
                    password_type=self.password_type,
                    random_options=self.random_options,
                    strength_bits=self.strength_bits,
                    total_rolls=total_rolls,
                    word_count=word_count,
                    word_separator=self.word_separator,
                    entropy_source=self.entropy_source,
                ),
                skip_current_view=True,
            )

    return ToolsPasswordDiceRollCountView


def _make_ToolsPasswordDiceEntryView():

    class ToolsPasswordDiceEntryView(_dependency('seedsigner.views.view', 'View')):
        def __init__(
            self,
            password_type,
            strength_bits,
            total_rolls,
            random_options=None,
            word_count=None,
            word_separator=PASSWORD_WORD_SEPARATOR_NONE,
            entropy_source=PASSWORD_ENTROPY_DICE,
            dice_sides=6,
        ):
            super().__init__()
            self.password_type = password_type
            self.strength_bits = strength_bits
            self.total_rolls = total_rolls
            self.random_options = random_options or {}
            self.word_count = word_count
            self.word_separator = word_separator
            self.entropy_source = entropy_source
            self.dice_sides = dice_sides

        def run(self):
            ret = _dependency('seedsigner_port.password_support', 'PasswordDiceEntryScreen')(
                return_after_n_chars=self.total_rolls
            ).display()
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
            if _resolve('_is_diceware_password_type')(getattr(self, 'password_type', None)):
                _resolve('_cache_password_entropy')(
                    self.controller,
                    password_type=self.password_type,
                    strength_bits=self.strength_bits,
                    entropy_source=self.entropy_source,
                    word_count=self.word_count,
                    roll_data=ret,
                    entropy_bytes=None,
                )
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('ToolsPasswordWordSeparatorView'),
                    view_args=dict(
                        password_type=self.password_type,
                        strength_bits=self.strength_bits,
                        random_options=self.random_options,
                        entropy_source=self.entropy_source,
                    ),
                    skip_current_view=True,
                )
            return _dependency('seedsigner_port.navigation', 'Destination')(
                _resolve('ToolsPasswordGenerateView'),
                view_args=dict(
                    password_type=self.password_type,
                    entropy_source=self.entropy_source,
                    random_options=self.random_options,
                    strength_bits=self.strength_bits,
                    roll_data=ret,
                    roll_count=self.total_rolls,
                    word_count=self.word_count,
                    word_separator=self.word_separator,
                    dice_sides=self.dice_sides,
                ),
            )

    return ToolsPasswordDiceEntryView


def _make_ToolsPasswordGenerateView():

    class ToolsPasswordGenerateView(_dependency('seedsigner.views.view', 'View')):
        def __init__(
            self,
            password_type,
            entropy_source,
            strength_bits,
            random_options=None,
            roll_data=None,
            roll_count=None,
            word_count=None,
            word_separator=PASSWORD_WORD_SEPARATOR_NONE,
            entropy_bytes_override=None,
            dice_sides=6,
        ):
            super().__init__()
            self.password_type = password_type
            self.entropy_source = entropy_source
            self.strength_bits = strength_bits
            self.random_options = random_options or {}
            self.roll_data = roll_data
            self.roll_count = roll_count
            self.word_count = word_count
            self.word_separator = word_separator
            self.entropy_bytes_override = entropy_bytes_override
            self.dice_sides = dice_sides

        def _bip39_words_from_entropy(self, seed, word_count):
            wordlist = _dependency('seedsigner.models.seed', 'Seed').get_wordlist(
                self.settings.get_value(
                    _dependency(
                        'seedsigner.models.settings_definition', 'SettingsConstants'
                    ).SETTING__WORDLIST_LANGUAGE
                )
            )
            total_bits = word_count * 11
            num_bytes = _dependency('math', None).ceil(total_bits / 8)
            data = (
                _dependency('seedsigner_port.password_generation', None)
                .shake_stream(seed)
                .read(num_bytes)
            )
            bit_string = ''.join(('{0:08b}'.format(byte) for byte in data))
            words = []
            for i in range(word_count):
                idx = int(bit_string[i * 11 : (i + 1) * 11], 2)
                words.append(''.join(wordlist[idx]))
            return words

        def _dice_length_for_charset(self, alphabet_size):
            return _resolve('_strength_to_length')(self.strength_bits, alphabet_size)

        def _diceware_rolls_from_entropy(self, entropy_seed):
            if self.word_count is None:
                raise ValueError('Word count is required for diceware')
            if self.password_type == PASSWORD_TYPE_DICEWARE_EFF_SHORT:
                sides = 6
                rolls_per_word = 4
            elif self.password_type == PASSWORD_TYPE_DICEWARE_EFF_LONG:
                sides = 6
                rolls_per_word = 5
            else:
                sides = 2048
                rolls_per_word = 1
            roll_count = self.word_count * rolls_per_word
            return _dependency('seedsigner_port.password_generation', None).dice_rolls_from_seed(
                entropy_seed, sides, roll_count
            )

        def _diceware_words(self, entropy_bytes=None):
            if self.password_type == PASSWORD_TYPE_DICEWARE_BIP39 and self.entropy_source in {
                PASSWORD_ENTROPY_CAMERA,
                PASSWORD_ENTROPY_HARDWARE_RNG,
                PASSWORD_ENTROPY_BIP85,
            }:
                if self.word_count is None:
                    raise ValueError('Word count is required for words')
                return self._bip39_words_from_entropy(entropy_bytes, self.word_count)
            roll_data = self.roll_data
            if self.password_type in {
                PASSWORD_TYPE_DICEWARE_EFF_SHORT,
                PASSWORD_TYPE_DICEWARE_EFF_LONG,
            } and self.entropy_source in {
                PASSWORD_ENTROPY_CAMERA,
                PASSWORD_ENTROPY_HARDWARE_RNG,
                PASSWORD_ENTROPY_BIP85,
            }:
                if entropy_bytes is None:
                    raise ValueError('Entropy is required for diceware')
                roll_data = self._diceware_rolls_from_entropy(entropy_bytes)
            if self.password_type == PASSWORD_TYPE_DICEWARE_EFF_SHORT:
                return _dependency(
                    'seedsigner_port.password_support', None
                ).diceware_words_from_rolls(
                    roll_data,
                    _dependency('seedsigner_port.password_support', None).eff_short_map(),
                    4,
                )
            if self.password_type == PASSWORD_TYPE_DICEWARE_EFF_LONG:
                return _dependency(
                    'seedsigner_port.password_support', None
                ).diceware_words_from_rolls(
                    roll_data,
                    _dependency('seedsigner_port.password_support', None).eff_large_map(),
                    5,
                )
            word_count = self.word_count
            if word_count is None:
                entropy_bits = _dependency(
                    'seedsigner_port.password_generation', None
                ).dice_roll_entropy_bits(self.roll_count)
                word_count = int(entropy_bits // 11)
            if word_count < 1:
                raise ValueError('Not enough entropy for words')
            entropy_seed = (
                entropy_bytes
                if entropy_bytes is not None
                else _dependency('seedsigner_port.camera_entropy_mnemonic', None)._hash_dice_rolls(
                    roll_data
                )
            )
            return self._bip39_words_from_entropy(entropy_seed, word_count)

        def run(self):
            entropy_bytes_override = getattr(self, 'entropy_bytes_override', None)
            if entropy_bytes_override is not None:
                entropy_bytes = entropy_bytes_override
            elif self.entropy_source == PASSWORD_ENTROPY_CAMERA:
                entropy_bytes = _dependency(
                    'seedsigner_port.camera_entropy', 'derive_camera_entropy_bytes'
                )(
                    self.controller.image_entropy_preview_frames,
                    self.controller.image_entropy_final_image,
                )
                _dependency('seedsigner_port.camera_entropy', 'clear_controller_images')(
                    self.controller
                )
                if entropy_bytes is None:
                    self.run_screen(
                        _dependency('seedsigner.gui.screens', 'ErrorScreen'),
                        title=_dependency('gettext', 'gettext')('Poor Entropy'),
                        status_headline=None,
                        text=_dependency('gettext', 'gettext')(
                            "Camera entropy didn't appear random enough. Please try again."
                        ),
                    )
                    return _dependency('seedsigner_port.navigation', 'Destination')(
                        _dependency('seedsigner.views.view', 'BackStackView')
                    )
            elif self.entropy_source == PASSWORD_ENTROPY_HARDWARE_RNG:
                if not self.controller.hardware_rng_is_healthy:
                    self.run_screen(
                        _dependency('seedsigner.gui.screens', 'WarningScreen'),
                        title=_dependency('gettext', 'gettext')('System RNG Error'),
                        status_headline=None,
                        text=self.controller.hardware_rng_failure_reason
                        or _dependency('gettext', 'gettext')('System RNG health check failed.'),
                        show_back_button=False,
                        button_data=[
                            _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
                                'I Understand'
                            )
                        ],
                    )
                    return _dependency('seedsigner_port.navigation', 'Destination')(
                        _dependency('seedsigner.views.view', 'BackStackView')
                    )
                entropy_bytes = _dependency(
                    'seedsigner_port.password_support', 'hardware_rng_unavailable'
                )()
            else:
                entropy_bytes = (
                    self.roll_data
                    if self.entropy_source == PASSWORD_ENTROPY_BIP85
                    else _dependency(
                        'seedsigner_port.camera_entropy_mnemonic', None
                    )._hash_dice_rolls(self.roll_data)
                )
            if self.password_type in {
                PASSWORD_TYPE_DICEWARE_EFF_SHORT,
                PASSWORD_TYPE_DICEWARE_EFF_LONG,
                PASSWORD_TYPE_DICEWARE_BIP39,
            }:
                _resolve('_cache_password_entropy')(
                    self.controller,
                    password_type=self.password_type,
                    strength_bits=self.strength_bits,
                    entropy_source=self.entropy_source,
                    word_count=self.word_count,
                    roll_data=self.roll_data
                    if self.entropy_source == PASSWORD_ENTROPY_DICE
                    else None,
                    entropy_bytes=entropy_bytes
                    if self.entropy_source != PASSWORD_ENTROPY_DICE
                    else None,
                )
            try:
                if self.password_type in {
                    PASSWORD_TYPE_DICEWARE_EFF_SHORT,
                    PASSWORD_TYPE_DICEWARE_EFF_LONG,
                    PASSWORD_TYPE_DICEWARE_BIP39,
                }:
                    words = self._diceware_words(entropy_bytes=entropy_bytes)
                    password = _resolve('_format_word_password')(words, self.word_separator)
                elif self.password_type == PASSWORD_TYPE_RANDOM:
                    charset = _resolve('_random_charset')(self.random_options)
                    if self.entropy_source == PASSWORD_ENTROPY_DICE:
                        length = self._dice_length_for_charset(len(charset))
                    else:
                        length = _resolve('_strength_to_length')(self.strength_bits, len(charset))
                    password = _dependency(
                        'seedsigner_port.password_generation', None
                    ).random_string_from_charset(entropy_bytes, length, charset)
                elif self.password_type == PASSWORD_TYPE_DICE_ROLLS:
                    if self.roll_count is None:
                        raise ValueError('Roll count is required')
                    rolls = _dependency(
                        'seedsigner_port.password_generation', None
                    ).dice_roll_values_from_seed(
                        entropy_bytes, sides=self.dice_sides, roll_count=self.roll_count, base=0
                    )
                    password = ','.join((str(roll) for roll in rolls))
                elif self.password_type == PASSWORD_TYPE_HEX:
                    if self.entropy_source == PASSWORD_ENTROPY_DICE:
                        length = self._dice_length_for_charset(16)
                        password = _dependency(
                            'seedsigner_port.password_generation', None
                        ).hex_password_from_seed(entropy_bytes, length)
                    elif self.entropy_source == PASSWORD_ENTROPY_BIP85:
                        num_bytes = _resolve('_strength_to_length')(self.strength_bits, 256)
                        password = _dependency(
                            'seedsigner_port.password_generation', None
                        ).bip85_hex_password(entropy_bytes, num_bytes)
                    else:
                        length = _resolve('_strength_to_length')(self.strength_bits, 16)
                        password = _dependency(
                            'seedsigner_port.password_generation', None
                        ).hex_password_from_seed(entropy_bytes, length)
                elif self.password_type == PASSWORD_TYPE_BASE64:
                    if self.entropy_source == PASSWORD_ENTROPY_DICE:
                        length = self._dice_length_for_charset(64)
                        password = _dependency(
                            'seedsigner_port.password_generation', None
                        ).base64_password_from_seed(entropy_bytes, length)
                    elif self.entropy_source == PASSWORD_ENTROPY_BIP85:
                        length = _resolve('_strength_to_length')(self.strength_bits, 64)
                        password = _dependency(
                            'seedsigner_port.password_generation', None
                        ).bip85_base64_password(entropy_bytes, length)
                    else:
                        length = _resolve('_strength_to_length')(self.strength_bits, 64)
                        password = _dependency(
                            'seedsigner_port.password_generation', None
                        ).base64_password_from_seed(entropy_bytes, length)
                elif self.entropy_source == PASSWORD_ENTROPY_DICE:
                    length = self._dice_length_for_charset(85)
                    password = _dependency(
                        'seedsigner_port.password_generation', None
                    ).base85_password_from_seed(entropy_bytes, length)
                elif self.entropy_source == PASSWORD_ENTROPY_BIP85:
                    length = _resolve('_strength_to_length')(self.strength_bits, 85)
                    password = _dependency(
                        'seedsigner_port.password_generation', None
                    ).bip85_base85_password(entropy_bytes, length)
                else:
                    length = _resolve('_strength_to_length')(self.strength_bits, 85)
                    password = _dependency(
                        'seedsigner_port.password_generation', None
                    ).base85_password_from_seed(entropy_bytes, length)
            except ValueError as exc:
                self.run_screen(
                    _dependency('seedsigner.gui.screens', 'WarningScreen'),
                    title=_dependency('gettext', 'gettext')('Invalid Input'),
                    status_headline=None,
                    text=str(exc),
                    show_back_button=False,
                    button_data=[
                        _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('I Understand')
                    ],
                )
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _dependency('seedsigner.views.view', 'BackStackView')
                )
            return _dependency('seedsigner_port.navigation', 'Destination')(
                _resolve('ToolsPasswordReviewView'),
                view_args=dict(
                    password=password,
                    password_type=self.password_type,
                    strength_bits=self.strength_bits,
                    random_options=self.random_options,
                    entropy_source=self.entropy_source,
                ),
                skip_current_view=True,
            )

    return ToolsPasswordGenerateView


def _make_ToolsPasswordBIP85GenerateView():

    class ToolsPasswordBIP85GenerateView(_dependency('seedsigner.views.view', 'View')):
        def __init__(
            self,
            password_type,
            strength_bits,
            random_options=None,
            dice_sides=None,
            roll_count=None,
        ):
            super().__init__()
            self.password_type = password_type
            self.strength_bits = strength_bits
            self.random_options = random_options or {}
            self.dice_sides = dice_sides
            self.roll_count = roll_count

        def _prompt_dice_sides(self):
            side_options = [
                _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
                    '6 sides', return_data=6
                ),
                _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
                    '10 sides', return_data=10
                ),
                _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
                    '20 sides', return_data=20
                ),
            ]
            selected_menu_num = self.run_screen(
                _dependency('seedsigner.gui.screens', 'ButtonListScreen'),
                title=_dependency('gettext', 'gettext')('Dice Sides'),
                is_button_text_centered=False,
                selected_button=0,
                button_data=side_options,
            )
            if selected_menu_num == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                return None
            return int(side_options[selected_menu_num].return_data)

        def _prompt_roll_count(self):
            ret = (
                _dependency('seedsigner.gui.screens', 'seed_screens')
                .SeedBIP85SelectChildIndexScreen(
                    title=_dependency('gettext', 'gettext')('Number of Rolls')
                )
                .display()
            )
            if ret == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                return None
            if not ret:
                return 0
            return int(ret)

        def run(self):
            if len(self.controller.storage.seeds) == 0:
                self.run_screen(
                    _dependency('seedsigner.gui.screens', 'WarningScreen'),
                    title=_dependency('gettext', 'gettext')('WARNING'),
                    status_headline=None,
                    text=_dependency('gettext', 'gettext')('Load a seed before using BIP85.'),
                    show_back_button=False,
                    button_data=[
                        _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('I Understand')
                    ],
                )
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _dependency('seedsigner.views.view', 'BackStackView')
                )
            if len(self.controller.storage.seeds) > 1:
                seed_buttons = []
                for seed in self.controller.storage.seeds:
                    button_str = seed.get_fingerprint(
                        self.settings.get_value(
                            _dependency(
                                'seedsigner.models.settings_definition', 'SettingsConstants'
                            ).SETTING__NETWORK
                        )
                    )
                    seed_buttons.append(
                        _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
                            button_str,
                            _dependency(
                                'seedsigner.gui.components', 'SeedSignerIconConstants'
                            ).FINGERPRINT,
                            icon_color='blue',
                        )
                    )
                selected_seed = self.run_screen(
                    _dependency('seedsigner.gui.screens', 'seed_screens').SeedSelectSeedScreen,
                    title=_dependency('gettext', 'gettext')('Select Seed'),
                    text=_dependency('gettext', 'gettext')('Choose seed for BIP85'),
                    is_button_text_centered=False,
                    button_data=seed_buttons,
                )
                if selected_seed == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                    return _dependency('seedsigner_port.navigation', 'Destination')(
                        _dependency('seedsigner.views.view', 'BackStackView')
                    )
                seed = self.controller.storage.seeds[selected_seed]
            else:
                seed = self.controller.storage.seeds[0]
            ret = (
                _dependency('seedsigner.gui.screens', 'seed_screens')
                .SeedBIP85SelectChildIndexScreen(
                    title=_dependency('gettext', 'gettext')('BIP85 Index')
                )
                .display()
            )
            if ret == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _dependency('seedsigner.views.view', 'BackStackView')
                )
            index = int(ret)
            root = seed.get_root(
                self.settings.get_value(
                    _dependency(
                        'seedsigner.models.settings_definition', 'SettingsConstants'
                    ).SETTING__NETWORK
                )
            )
            if self.password_type in {
                PASSWORD_TYPE_DICEWARE_EFF_SHORT,
                PASSWORD_TYPE_DICEWARE_EFF_LONG,
                PASSWORD_TYPE_DICEWARE_BIP39,
            }:
                if self.password_type == PASSWORD_TYPE_DICEWARE_BIP39:
                    sides = 2048
                    rolls = _resolve('_diceware_word_count')(self.password_type, self.strength_bits)
                elif self.password_type == PASSWORD_TYPE_DICEWARE_EFF_SHORT:
                    sides = 6
                    rolls = (
                        _resolve('_diceware_word_count')(self.password_type, self.strength_bits) * 4
                    )
                else:
                    sides = 6
                    rolls = (
                        _resolve('_diceware_word_count')(self.password_type, self.strength_bits) * 5
                    )
                entropy = _dependency('embit', 'bip85').derive_entropy(
                    root,
                    _dependency('seedsigner_port.view_tools_extra', 'BIP85_APP_DICE'),
                    [sides, rolls, index],
                )
                _resolve('_cache_password_entropy')(
                    self.controller,
                    password_type=self.password_type,
                    strength_bits=self.strength_bits,
                    entropy_source=PASSWORD_ENTROPY_BIP85,
                    word_count=_resolve('_diceware_word_count')(
                        self.password_type, self.strength_bits
                    ),
                    roll_data=None,
                    entropy_bytes=entropy,
                )
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('ToolsPasswordWordSeparatorView'),
                    view_args=dict(
                        password_type=self.password_type,
                        strength_bits=self.strength_bits,
                        random_options=self.random_options,
                        entropy_source=PASSWORD_ENTROPY_BIP85,
                    ),
                )
            if self.password_type == PASSWORD_TYPE_DICE_ROLLS:
                sides = getattr(self, 'dice_sides', None)
                if sides is None:
                    sides = self._prompt_dice_sides()
                    if sides is None:
                        return _dependency('seedsigner_port.navigation', 'Destination')(
                            _dependency('seedsigner.views.view', 'BackStackView')
                        )
                rolls = getattr(self, 'roll_count', None)
                if rolls is None:
                    rolls = self._prompt_roll_count()
                    if rolls is None:
                        return _dependency('seedsigner_port.navigation', 'Destination')(
                            _dependency('seedsigner.views.view', 'BackStackView')
                        )
                if rolls < 1:
                    self.run_screen(
                        _dependency('seedsigner.gui.screens', 'WarningScreen'),
                        title=_dependency('gettext', 'gettext')('Invalid Input'),
                        status_headline=None,
                        text=_dependency('gettext', 'gettext')(
                            'Number of rolls must be at least 1.'
                        ),
                        show_back_button=False,
                        button_data=[
                            _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
                                'I Understand'
                            )
                        ],
                    )
                    return _dependency('seedsigner_port.navigation', 'Destination')(
                        _dependency('seedsigner.views.view', 'BackStackView')
                    )
                entropy = _dependency('embit', 'bip85').derive_entropy(
                    root,
                    _dependency('seedsigner_port.view_tools_extra', 'BIP85_APP_DICE'),
                    [sides, rolls, index],
                )
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('ToolsPasswordGenerateView'),
                    view_args=dict(
                        password_type=self.password_type,
                        entropy_source=PASSWORD_ENTROPY_BIP85,
                        strength_bits=self.strength_bits,
                        random_options=self.random_options,
                        roll_data=entropy,
                        roll_count=rolls,
                        dice_sides=sides,
                    ),
                )
            if self.password_type == PASSWORD_TYPE_HEX:
                num_bytes = _resolve('_strength_to_length')(self.strength_bits, 256)
                if num_bytes < 16 or num_bytes > 64:
                    self.run_screen(
                        _dependency('seedsigner.gui.screens', 'WarningScreen'),
                        title=_dependency('gettext', 'gettext')('Invalid Length'),
                        status_headline=None,
                        text=_dependency('gettext', 'gettext')(
                            'BIP85 Hex supports 128 or 256 bits.'
                        ),
                        show_back_button=False,
                        button_data=[
                            _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
                                'I Understand'
                            )
                        ],
                    )
                    return _dependency('seedsigner_port.navigation', 'Destination')(
                        _dependency('seedsigner.views.view', 'BackStackView')
                    )
                entropy = _dependency('embit', 'bip85').derive_entropy(
                    root,
                    _dependency('seedsigner_port.view_tools_extra', 'BIP85_APP_HEX'),
                    [num_bytes, index],
                )
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('ToolsPasswordGenerateView'),
                    view_args=dict(
                        password_type=self.password_type,
                        entropy_source=PASSWORD_ENTROPY_BIP85,
                        strength_bits=self.strength_bits,
                        random_options=self.random_options,
                        roll_data=entropy,
                    ),
                )
            elif self.password_type == PASSWORD_TYPE_BASE64:
                length = _resolve('_strength_to_length')(self.strength_bits, 64)
                if length < 20 or length > 86:
                    self.run_screen(
                        _dependency('seedsigner.gui.screens', 'WarningScreen'),
                        title=_dependency('gettext', 'gettext')('Invalid Length'),
                        status_headline=None,
                        text=_dependency('gettext', 'gettext')('BIP85 Base64 needs 120+ bits.'),
                        show_back_button=False,
                        button_data=[
                            _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
                                'I Understand'
                            )
                        ],
                    )
                    return _dependency('seedsigner_port.navigation', 'Destination')(
                        _dependency('seedsigner.views.view', 'BackStackView')
                    )
                entropy = _dependency('embit', 'bip85').derive_entropy(
                    root,
                    _dependency('seedsigner_port.view_tools_extra', 'BIP85_APP_BASE64'),
                    [length, index],
                )
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('ToolsPasswordGenerateView'),
                    view_args=dict(
                        password_type=self.password_type,
                        entropy_source=PASSWORD_ENTROPY_BIP85,
                        strength_bits=self.strength_bits,
                        random_options=self.random_options,
                        roll_data=entropy,
                    ),
                )
            else:
                length = _resolve('_strength_to_length')(self.strength_bits, 85)
                if length < 10 or length > 80:
                    self.run_screen(
                        _dependency('seedsigner.gui.screens', 'WarningScreen'),
                        title=_dependency('gettext', 'gettext')('Invalid Length'),
                        status_headline=None,
                        text=_dependency('gettext', 'gettext')('BIP85 Base85 needs 64-512 bits.'),
                        show_back_button=False,
                        button_data=[
                            _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
                                'I Understand'
                            )
                        ],
                    )
                    return _dependency('seedsigner_port.navigation', 'Destination')(
                        _dependency('seedsigner.views.view', 'BackStackView')
                    )
                entropy = _dependency('embit', 'bip85').derive_entropy(
                    root,
                    _dependency('seedsigner_port.view_tools_extra', 'BIP85_APP_BASE85'),
                    [length, index],
                )
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('ToolsPasswordGenerateView'),
                    view_args=dict(
                        password_type=self.password_type,
                        entropy_source=PASSWORD_ENTROPY_BIP85,
                        strength_bits=self.strength_bits,
                        random_options=self.random_options,
                        roll_data=entropy,
                    ),
                )

    return ToolsPasswordBIP85GenerateView


def _make_ToolsPasswordReviewView():

    class ToolsPasswordReviewView(_dependency('seedsigner.views.view', 'View')):
        def __init__(
            self,
            password,
            password_type=None,
            strength_bits=None,
            random_options=None,
            entropy_source=None,
        ):
            super().__init__()
            self.password = password
            self.password_type = password_type
            self.strength_bits = strength_bits
            self.random_options = random_options or {}
            self.entropy_source = entropy_source

        def run(self):
            while True:
                edit = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Edit')
                next_button = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Next')
                button_data = [edit, next_button]
                selected_menu_num = self.run_screen(
                    _dependency('seedsigner.gui.screens', 'ToolsTextQRReviewTextScreen'),
                    textToEncode=self.password,
                    title=_dependency('gettext', 'gettext')('Password'),
                    button_data=button_data,
                    show_back_button=True,
                )
                if selected_menu_num == _dependency(
                    'seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'
                ):
                    if _resolve('_is_diceware_password_type')(getattr(self, 'password_type', None)):
                        return _dependency('seedsigner_port.navigation', 'Destination')(
                            _resolve('ToolsPasswordWordSeparatorView'),
                            view_args=dict(
                                password_type=self.password_type,
                                strength_bits=self.strength_bits,
                                random_options=self.random_options,
                                entropy_source=self.entropy_source,
                            ),
                            skip_current_view=True,
                        )
                    return _dependency('seedsigner_port.navigation', 'Destination')(
                        _dependency('seedsigner.views.view', 'BackStackView')
                    )
                if button_data[selected_menu_num] == edit:
                    ret_dict = _dependency('seedsigner.gui.screens', 'ToolsTextQRTextEntryScreen')(
                        textToEncode=self.password,
                        title=_dependency('gettext', 'gettext')('Password'),
                    ).display()
                    if 'is_back_button' in ret_dict:
                        continue
                    self.password = ret_dict['textToEncode']
                    continue
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('ToolsPasswordSaveView'), view_args=dict(password=self.password)
                )

    return ToolsPasswordReviewView


def _make_ToolsPasswordSaveView():

    class ToolsPasswordSaveView(_dependency('seedsigner.views.view', 'View')):
        def __init__(self, password):
            super().__init__()
            self.password = password

        def run(self):
            show_qr = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Show as QR')
            seedkeeper = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(
                'Save to Seedkeeper'
            )
            button_data = [show_qr]
            selected_menu_num = self.run_screen(
                _dependency('seedsigner.gui.screens', 'ButtonListScreen'),
                title=_dependency('gettext', 'gettext')('Save Password'),
                is_button_text_centered=False,
                button_data=button_data,
                show_back_button=True,
            )
            if selected_menu_num == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _dependency('seedsigner.views.view', 'BackStackView')
                )
            if button_data[selected_menu_num] == show_qr:
                num_modules = _dependency('seedsigner.helpers.qr', 'QR')().qrsize(
                    data=self.password
                )
                if num_modules <= 33:
                    return _dependency('seedsigner_port.navigation', 'Destination')(
                        _resolve('ToolsTextQRTranscribeModePromptView'),
                        view_args=dict(
                            text=self.password, num_modules=num_modules, return_to_home=True
                        ),
                    )
                return _dependency('seedsigner_port.navigation', 'Destination')(
                    _resolve('ToolsTextQRFullScreenModeView'),
                    view_args=dict(text=self.password, return_to_home=True),
                )
            raise RuntimeError('Unexpected password save option')
            return _dependency('seedsigner_port.navigation', 'Destination')(
                _dependency('seedsigner.views.view', 'BackStackView')
            )

    return ToolsPasswordSaveView


_FACTORIES = {
    'ToolsTextQRTextEntryView': _make_ToolsTextQRTextEntryView,
    'ToolsTextQRTextEntryExitDialogView': _make_ToolsTextQRTextEntryExitDialogView,
    'ToolsTextQRReviewTextView': _make_ToolsTextQRReviewTextView,
    'ToolsTextQRTranscribeModePromptView': _make_ToolsTextQRTranscribeModePromptView,
    'ToolsTextQRTranscribeModeView': _make_ToolsTextQRTranscribeModeView,
    'ToolsTextQRFullScreenModeView': _make_ToolsTextQRFullScreenModeView,
    'ToolsTranscribeTextQRZoomedInView': _make_ToolsTranscribeTextQRZoomedInView,
    'ToolsTranscribeTextQRConfirmQRPromptView': _make_ToolsTranscribeTextQRConfirmQRPromptView,
    'ToolsTranscribeTextQRConfirmScanView': _make_ToolsTranscribeTextQRConfirmScanView,
    'ToolsTextQRScanQRCodeView': _make_ToolsTextQRScanQRCodeView,
    'ToolsTextQRReviewTextView2': _make_ToolsTextQRReviewTextView2,
    'ToolsTextQRView': _make_ToolsTextQRView,
    'ToolsPasswordGeneratorTypeView': _make_ToolsPasswordGeneratorTypeView,
    'ToolsPasswordStrengthView': _make_ToolsPasswordStrengthView,
    'ToolsPasswordRandomOptionsView': _make_ToolsPasswordRandomOptionsView,
    'ToolsPasswordEntropySourceView': _make_ToolsPasswordEntropySourceView,
    'ToolsPasswordHardwareRngEntropyView': _make_ToolsPasswordHardwareRngEntropyView,
    'ToolsPasswordWordSeparatorView': _make_ToolsPasswordWordSeparatorView,
    'ToolsPasswordDiceRollCountView': _make_ToolsPasswordDiceRollCountView,
    'ToolsPasswordDiceEntryView': _make_ToolsPasswordDiceEntryView,
    'ToolsPasswordGenerateView': _make_ToolsPasswordGenerateView,
    'ToolsPasswordBIP85GenerateView': _make_ToolsPasswordBIP85GenerateView,
    'ToolsPasswordReviewView': _make_ToolsPasswordReviewView,
    'ToolsPasswordSaveView': _make_ToolsPasswordSaveView,
}
_CACHE = {}
_FUNCS = {
    '_bip85_supported_password_type': _bip85_supported_password_type,
    '_cache_password_entropy': _cache_password_entropy,
    '_clear_password_entropy_cache': _clear_password_entropy_cache,
    '_dice_rolls_for_strength': _dice_rolls_for_strength,
    '_diceware_word_count': _diceware_word_count,
    '_format_word_password': _format_word_password,
    '_get_password_entropy_cache': _get_password_entropy_cache,
    '_is_diceware_password_type': _is_diceware_password_type,
    '_random_charset': _random_charset,
    '_strength_to_length': _strength_to_length,
    '_text_qr_done_destination': _text_qr_done_destination,
}


def _resolve(name):
    if name in _FUNCS:
        return _FUNCS[name]
    if name not in _CACHE:
        if name not in _FACTORIES:
            raise AttributeError(name)
        _CACHE[name] = _FACTORIES[name]()
    return _CACHE[name]


def __getattr__(name):
    return _resolve(name)
