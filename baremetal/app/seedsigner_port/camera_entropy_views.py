# Copyright2021 SeedSigner; MIT, see ../LICENSE.SeedSigner
# Generated original camera Views; reviewed native-only platform boundaries.
from seedsigner_port.decode_platform import dependency as _dependency,FeatureUnavailable
def _make_ToolsMenuView():

    class ToolsMenuView(_dependency('seedsigner.views.view', 'View')):
        IMAGE = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(' New seed', _dependency('seedsigner.gui.components', 'FontAwesomeIconConstants').CAMERA)
        DICE = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('New seed', _dependency('seedsigner.gui.components', 'FontAwesomeIconConstants').DICE)
        SLIP39_IMAGE = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('SLIP39 seed', _dependency('seedsigner.gui.components', 'FontAwesomeIconConstants').CAMERA)
        SLIP39_DICE = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('SLIP39 seed', _dependency('seedsigner.gui.components', 'FontAwesomeIconConstants').DICE)
        KEYBOARD = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Calc 12th/24th word', _dependency('seedsigner.gui.components', 'FontAwesomeIconConstants').KEYBOARD)
        ADDRESS_EXPLORER = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Address explorer')
        VERIFY_ADDRESS = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Verify address')
        TEXTQRCODE = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Text QR Code')
        PASSWORD_GENERATOR = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Password Generator', _dependency('seedsigner.gui.components', 'FontAwesomeIconConstants').LOCK)
        SMARTCARD = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Smartcard Tools', _dependency('seedsigner.gui.components', 'FontAwesomeIconConstants').LOCK)
        MICROSD = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('MicroSD Tools')
        BATTERY_CALIBRATION = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Battery Calibration')
        GPG = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('GPG Tools')
        LUCKFOX_BUILD_TOOLS = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Luckfox Build Tools')
        CLEAR_DESCRIPTOR = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Clear Multisig Descriptor')
        NETWORK_INFO = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('Network Info')

        def __init__(self, include_password_generator=True):
            super().__init__()
            self.include_password_generator = include_password_generator

        def run(self):
            button_data = [self.IMAGE, self.DICE]
            selected_menu_num = self.run_screen(_dependency('seedsigner.gui.screens', 'ButtonListScreen'), title=_dependency('gettext', 'gettext')('Tools'), is_button_text_centered=False, button_data=button_data)
            if selected_menu_num == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            if button_data[selected_menu_num] == self.IMAGE:
                return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('ToolsImageEntropyLivePreviewView'))
            return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('ToolsDiceEntropyMnemonicLengthView'))
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
            ret = self.run_screen(_dependency('seedsigner_port.camera_entropy_screens', 'ToolsImageEntropyLivePreviewScreen'))
            if ret == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            if isinstance(ret, tuple) and len(ret) == 2:
                self.controller.image_entropy_preview_frames, self.controller.image_entropy_final_image = ret
            else:
                self.controller.image_entropy_preview_frames = ret
            frames = self.controller.image_entropy_preview_frames
            if frames is None or len(frames) != _dependency('seedsigner_port.camera_entropy_screens', 'ToolsImageEntropyLivePreviewScreen').PREVIEW_POOL_SIZE:
                num_frames = 0 if frames is None else len(frames)
                raise Exception(_dependency('gettext', 'gettext')('Entropy collection failed. Expected {expected} preview frames, got {actual}').format(expected=_dependency('seedsigner_port.camera_entropy_screens', 'ToolsImageEntropyLivePreviewScreen').PREVIEW_POOL_SIZE, actual=num_frames))
            return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('ToolsImageEntropyFinalImageView'), view_args=dict(next_view=self.next_view, next_view_args=self.next_view_args))
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
            ret = self.run_screen(_dependency('seedsigner_port.camera_entropy_screens', 'ToolsImageEntropyFinalImageScreen'), final_image=self.controller.image_entropy_final_image)
            if ret == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                _dependency('seedsigner_port.camera_entropy', 'clear_controller_images')(self.controller)
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            next_view = self.next_view or _resolve('ToolsImageEntropyMnemonicLengthView')
            return _dependency('seedsigner_port.navigation', 'Destination')(next_view, view_args=self.next_view_args)
    return ToolsImageEntropyFinalImageView

def _make_ToolsImageEntropyMnemonicLengthView():

    class ToolsImageEntropyMnemonicLengthView(_dependency('seedsigner.views.view', 'View')):
        TWELVE_WORDS = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('12 words', return_data=12)
        FIFTEEN_WORDS = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('15 words', return_data=15)
        EIGHTEEN_WORDS = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('18 words', return_data=18)
        TWENTYONE_WORDS = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('21 words', return_data=21)
        TWENTYFOUR_WORDS = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('24 words', return_data=24)

        def run(self):
            owned_previews = self.controller.image_entropy_preview_frames
            owned_final = self.controller.image_entropy_final_image
            release_inputs = True
            try:
                if getattr(self.controller, 'create_slip39', False):
                    twenty = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('20 words', return_data=20)
                    thirty_three = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('33 words', return_data=33)
                    button_data = [twenty, thirty_three]
                else:
                    allowed = self.settings.get_value(_dependency('seedsigner.models.settings_definition', 'SettingsConstants').SETTING__SEED_WORD_LENGTHS)
                    options = {12: self.TWELVE_WORDS, 15: self.FIFTEEN_WORDS, 18: self.EIGHTEEN_WORDS, 21: self.TWENTYONE_WORDS, 24: self.TWENTYFOUR_WORDS}
                    button_data = [options[l] for l in allowed]
                selected_menu_num = self.run_screen(_dependency('seedsigner.gui.screens', 'ButtonListScreen'), title=_dependency('gettext', 'gettext')('Mnemonic Length'), button_data=button_data)
                if selected_menu_num == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                    release_inputs = False
                    return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
                mnemonic_length = button_data[selected_menu_num].return_data
                loading_screen = _dependency('seedsigner.gui.screens.screen', 'LoadingScreenThread')(text=_dependency('gettext', 'gettext')('Processing...'))
                loading_screen.start()
                preview_images = self.controller.image_entropy_preview_frames
                seed_entropy_image = self.controller.image_entropy_final_image
                final_hash = _dependency('seedsigner_port.camera_entropy', 'derive_camera_entropy_bytes')(preview_images, seed_entropy_image)
                if final_hash is None:
                    loading_screen.stop()
                    self.run_screen(_dependency('seedsigner.gui.screens', 'ErrorScreen'), title=_dependency('gettext', 'gettext')('Poor Entropy'), status_headline=None, text=_dependency('gettext', 'gettext')("Camera entropy didn't appear random enough. Please try again."))
                    self.controller.image_entropy_preview_frames = None
                    self.controller.image_entropy_final_image = None
                    return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('ToolsImageEntropyLivePreviewView'), skip_current_view=True)
                if mnemonic_length in _dependency('seedsigner_port.camera_entropy_mnemonic', None).ENTROPY_BYTES_REQUIRED:
                    final_hash = final_hash[:_dependency('seedsigner_port.camera_entropy_mnemonic', None).ENTROPY_BYTES_REQUIRED[mnemonic_length]]
                if getattr(self.controller, 'create_slip39', False):
                    secret = final_hash
                else:
                    mnemonic = _dependency('seedsigner_port.camera_entropy_mnemonic', None).generate_mnemonic_from_bytes(final_hash)
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
                    return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.seed_views', 'SeedSlip39CreateFromBytesView'), view_args=dict(secret=secret), clear_history=True)
                else:
                    seed = _dependency('seedsigner.models.seed', 'Seed')(mnemonic, wordlist_language_code=self.settings.get_value(_dependency('seedsigner.models.settings_definition', 'SettingsConstants').SETTING__WORDLIST_LANGUAGE))
                    self.controller.storage.set_pending_seed(seed)
                    return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.seed_views', 'SeedWordsWarningView'), view_args={'seed': None}, clear_history=True)
            finally:
                if release_inputs:
                    _dependency('seedsigner_port.camera_entropy', 'clear_images')(owned_previews, owned_final)
                    _dependency('seedsigner_port.camera_entropy', 'clear_controller_images')(self.controller)
    return ToolsImageEntropyMnemonicLengthView

def _make_ToolsDiceEntropyMnemonicLengthView():

    class ToolsDiceEntropyMnemonicLengthView(_dependency('seedsigner.views.view', 'View')):
        """Prompt for mnemonic length when using dice entropy."""
        TWELVE = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('12 words', return_data=12)
        FIFTEEN = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('15 words', return_data=15)
        EIGHTEEN = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('18 words', return_data=18)
        TWENTY_ONE = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('21 words', return_data=21)
        TWENTY_FOUR = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')('24 words', return_data=24)
        TWENTY = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(_dependency('gettext', 'gettext')('20 words ({} rolls)').format(_dependency('seedsigner_port.camera_entropy_mnemonic', None).DICE_ROLLS_REQUIRED[12]), return_data=_dependency('seedsigner_port.camera_entropy_mnemonic', None).DICE_ROLLS_REQUIRED[12])
        THIRTY_THREE = _dependency('seedsigner.gui.screens.screen', 'ButtonOption')(_dependency('gettext', 'gettext')('33 words ({} rolls)').format(_dependency('seedsigner_port.camera_entropy_mnemonic', None).DICE_ROLLS_REQUIRED[24]), return_data=_dependency('seedsigner_port.camera_entropy_mnemonic', None).DICE_ROLLS_REQUIRED[24])

        def run(self):
            if getattr(self.controller, 'create_slip39', False):
                button_data = [self.TWENTY, self.THIRTY_THREE]
            else:
                allowed = self.settings.get_value(_dependency('seedsigner.models.settings_definition', 'SettingsConstants').SETTING__SEED_WORD_LENGTHS)
                options = {12: self.TWELVE, 15: self.FIFTEEN, 18: self.EIGHTEEN, 21: self.TWENTY_ONE, 24: self.TWENTY_FOUR}
                button_data = [options[l] for l in allowed]
            selected_menu_num = self.run_screen(_dependency('seedsigner.gui.screens', 'ButtonListScreen'), title=_dependency('gettext', 'gettext')('Mnemonic Length'), is_bottom_list=True, is_button_text_centered=True, button_data=button_data)
            if selected_menu_num == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            if getattr(self.controller, 'create_slip39', False):
                total_rolls = button_data[selected_menu_num].return_data
            else:
                selected_length = button_data[selected_menu_num].return_data
                total_rolls = _dependency('seedsigner_port.camera_entropy_mnemonic', None).DICE_ROLLS_REQUIRED[selected_length]
            return _dependency('seedsigner_port.navigation', 'Destination')(_resolve('ToolsDiceEntropyEntryView'), view_args=dict(total_rolls=total_rolls))
    return ToolsDiceEntropyMnemonicLengthView

def _make_ToolsDiceEntropyEntryView():

    class ToolsDiceEntropyEntryView(_dependency('seedsigner.views.view', 'View')):

        def __init__(self, total_rolls):
            super().__init__()
            self.total_rolls = total_rolls

        def run(self):
            ret = self.run_screen(_dependency('seedsigner_port.camera_entropy_screens', 'ToolsDiceEntropyEntryScreen'), return_after_n_chars=self.total_rolls)
            if ret == _dependency('seedsigner.gui.screens', 'RET_CODE__BACK_BUTTON'):
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            if not _dependency('seedsigner_port.camera_entropy_mnemonic', None).dice_entropy_is_sufficient(ret):
                self.run_screen(_dependency('seedsigner.gui.screens', 'ErrorScreen'), title=_dependency('gettext', 'gettext')('Poor Entropy'), status_headline=None, text=_dependency('gettext', 'gettext')("Dice rolls didn't appear random enough. Please try again."))
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.view', 'BackStackView'))
            loading_screen = _dependency('seedsigner.gui.screens.screen', 'LoadingScreenThread')(text=_dependency('gettext', 'gettext')('Processing...'))
            loading_screen.start()
            if getattr(self.controller, 'create_slip39', False):
                entropy_bytes = _dependency('seedsigner_port.camera_entropy_mnemonic', None).generate_bytes_from_dice(ret)
                self.controller.create_slip39 = False
                loading_screen.stop()
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.seed_views', 'SeedSlip39CreateFromBytesView'), view_args=dict(secret=entropy_bytes), clear_history=True)
            else:
                dice_seed_phrase = _dependency('seedsigner_port.camera_entropy_mnemonic', None).generate_mnemonic_from_dice(ret, wordlist_language_code=self.settings.get_value(_dependency('seedsigner.models.settings_definition', 'SettingsConstants').SETTING__WORDLIST_LANGUAGE))
                seed = _dependency('seedsigner.models.seed', 'Seed')(dice_seed_phrase, wordlist_language_code=self.settings.get_value(_dependency('seedsigner.models.settings_definition', 'SettingsConstants').SETTING__WORDLIST_LANGUAGE))
                self.controller.storage.set_pending_seed(seed)
                loading_screen.stop()
                return _dependency('seedsigner_port.navigation', 'Destination')(_dependency('seedsigner.views.seed_views', 'SeedWordsWarningView'), view_args={'seed': None}, clear_history=True)
    return ToolsDiceEntropyEntryView
_FACTORIES={'ToolsMenuView':_make_ToolsMenuView,'ToolsImageEntropyLivePreviewView':_make_ToolsImageEntropyLivePreviewView,'ToolsImageEntropyFinalImageView':_make_ToolsImageEntropyFinalImageView,'ToolsImageEntropyMnemonicLengthView':_make_ToolsImageEntropyMnemonicLengthView,'ToolsDiceEntropyMnemonicLengthView':_make_ToolsDiceEntropyMnemonicLengthView,'ToolsDiceEntropyEntryView':_make_ToolsDiceEntropyEntryView}
_CACHE={}
def _resolve(name):
    if name not in _CACHE:
        if name not in _FACTORIES:raise AttributeError(name)
        _CACHE[name]=_FACTORIES[name]()
    return _CACHE[name]
def __getattr__(name):return _resolve(name)
