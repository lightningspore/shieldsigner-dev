# Copyright2021 SeedSigner; MIT, see ../LICENSE.SeedSigner
from seedsigner_port.decode_platform import dependency as _dependency, FeatureUnavailable
class GUIConstants:
    EDGE_PADDING = 8
    COMPONENT_PADDING = 8
    LIST_ITEM_PADDING = 4
    BACKGROUND_COLOR = '#000000'
    INACTIVE_COLOR = '#414141'
    ACCENT_COLOR = '#FF9F0A'
    WARNING_COLOR = '#FFD60A'
    DIRE_WARNING_COLOR = '#FF5700'
    ERROR_COLOR = '#FF1B0A'
    SUCCESS_COLOR = '#30D158'
    INFO_COLOR = '#409CFF'
    TESTNET_COLOR = '#00F100'
    REGTEST_COLOR = '#00CAF1'
    GREEN_INDICATOR_COLOR = '#00FF00'
    ICON_FONT_NAME__FONT_AWESOME = 'Font_Awesome_6_Free-Solid-900'
    ICON_FONT_NAME__SEEDSIGNER = 'seedsigner-icons'
    ICON_FONT_SIZE = 22
    ICON_INLINE_FONT_SIZE = 24
    ICON_LARGE_BUTTON_SIZE = 48
    ICON_TOAST_FONT_SIZE = 30
    ICON_PRIMARY_SCREEN_SIZE = 50
    BASE_LOCALE_FONTS = {'default': 'OpenSans-Regular', _dependency('seedsigner.models.settings_definition', 'SettingsConstants').LOCALE__ARABIC: 'NotoSansAR-Regular', _dependency('seedsigner.models.settings_definition', 'SettingsConstants').LOCALE__CHINESE_SIMPLIFIED: 'NotoSansSC-Regular', _dependency('seedsigner.models.settings_definition', 'SettingsConstants').LOCALE__HINDI: 'NotoSansDevanagari-Regular', _dependency('seedsigner.models.settings_definition', 'SettingsConstants').LOCALE__JAPANESE: 'NotoSansJP-Regular', _dependency('seedsigner.models.settings_definition', 'SettingsConstants').LOCALE__KOREAN: 'NotoSansKR-Regular', _dependency('seedsigner.models.settings_definition', 'SettingsConstants').LOCALE__PERSIAN: 'NotoSansAR-Regular', _dependency('seedsigner.models.settings_definition', 'SettingsConstants').LOCALE__THAI: 'NotoSansTH-Regular'}
    TOP_NAV_TITLE_FONT_NAME = BASE_LOCALE_FONTS.copy()
    TOP_NAV_TITLE_FONT_NAME['default'] = 'OpenSans-SemiBold'
    TOP_NAV_TITLE_FONT_SIZE = {'default': 20, _dependency('seedsigner.models.settings_definition', 'SettingsConstants').LOCALE__CHINESE_SIMPLIFIED: 23, _dependency('seedsigner.models.settings_definition', 'SettingsConstants').LOCALE__HINDI: 22, _dependency('seedsigner.models.settings_definition', 'SettingsConstants').LOCALE__JAPANESE: 22, _dependency('seedsigner.models.settings_definition', 'SettingsConstants').LOCALE__KOREAN: 23}
    TOP_NAV_HEIGHT = 48
    TOP_NAV_BUTTON_SIZE = 32
    BODY_FONT_NAME = BASE_LOCALE_FONTS.copy()
    BODY_FONT_SIZE = {'default': 17, _dependency('seedsigner.models.settings_definition', 'SettingsConstants').LOCALE__CHINESE_SIMPLIFIED: 18, _dependency('seedsigner.models.settings_definition', 'SettingsConstants').LOCALE__HINDI: 18, _dependency('seedsigner.models.settings_definition', 'SettingsConstants').LOCALE__JAPANESE: 18, _dependency('seedsigner.models.settings_definition', 'SettingsConstants').LOCALE__KOREAN: 18}
    BODY_FONT_MAX_SIZE = TOP_NAV_TITLE_FONT_SIZE['default']
    BODY_FONT_MIN_SIZE = 15
    BODY_FONT_COLOR = '#FCFCFC'
    BODY_LINE_SPACING = COMPONENT_PADDING
    FIXED_WIDTH_FONT_NAME = 'Inconsolata-Regular'
    FIXED_WIDTH_EMPHASIS_FONT_NAME = 'Inconsolata-SemiBold'
    FIXED_WIDTH_FONT_NAME_JP = 'PlemolJPConsole-Regular-S'
    FIXED_WIDTH_EMPHASIS_FONT_NAME_JP = 'PlemolJPConsole-SemiBold-S'
    LABEL_FONT_SIZE = BODY_FONT_MIN_SIZE
    LABEL_FONT_COLOR = '#777777'
    BUTTON_FONT_NAME = BASE_LOCALE_FONTS.copy()
    BUTTON_FONT_NAME['default'] = 'OpenSans-SemiBold'
    BUTTON_FONT_SIZE = {'default': 18, 'ar': 18, 'fa': 18, _dependency('seedsigner.models.settings_definition', 'SettingsConstants').LOCALE__HINDI: 20, _dependency('seedsigner.models.settings_definition', 'SettingsConstants').LOCALE__JAPANESE: 20, _dependency('seedsigner.models.settings_definition', 'SettingsConstants').LOCALE__KOREAN: 20, _dependency('seedsigner.models.settings_definition', 'SettingsConstants').LOCALE__CHINESE_SIMPLIFIED: 20}
    BUTTON_FONT_COLOR = '#FCFCFC'
    BUTTON_BACKGROUND_COLOR = '#2C2C2C'
    BUTTON_HEIGHT = 32
    BUTTON_SELECTED_FONT_COLOR = BACKGROUND_COLOR
    NOTIFICATION_COLOR = '#00F100'

    @staticmethod
    def get_body_font_name(locale=None):
        if not locale:
            locale = _dependency('seedsigner.models.settings', 'Settings').get_instance().get_value(_dependency('seedsigner.models.settings_definition', 'SettingsConstants').SETTING__LOCALE)
        if locale in GUIConstants.BODY_FONT_NAME:
            return GUIConstants.BODY_FONT_NAME[locale]
        else:
            return GUIConstants.BODY_FONT_NAME['default']

    @staticmethod
    def get_body_font_size(locale=None):
        if not locale:
            locale = _dependency('seedsigner.models.settings', 'Settings').get_instance().get_value(_dependency('seedsigner.models.settings_definition', 'SettingsConstants').SETTING__LOCALE)
        if locale in GUIConstants.BODY_FONT_SIZE:
            return GUIConstants.BODY_FONT_SIZE[locale]
        else:
            return GUIConstants.BODY_FONT_SIZE['default']

    @staticmethod
    def get_top_nav_title_font_name():
        locale = _dependency('seedsigner.models.settings', 'Settings').get_instance().get_value(_dependency('seedsigner.models.settings_definition', 'SettingsConstants').SETTING__LOCALE)
        if locale in GUIConstants.TOP_NAV_TITLE_FONT_NAME:
            return GUIConstants.TOP_NAV_TITLE_FONT_NAME[locale]
        else:
            return GUIConstants.TOP_NAV_TITLE_FONT_NAME['default']

    @staticmethod
    def get_top_nav_title_font_size():
        locale = _dependency('seedsigner.models.settings', 'Settings').get_instance().get_value(_dependency('seedsigner.models.settings_definition', 'SettingsConstants').SETTING__LOCALE)
        if locale in GUIConstants.TOP_NAV_TITLE_FONT_SIZE:
            return GUIConstants.TOP_NAV_TITLE_FONT_SIZE[locale]
        else:
            return GUIConstants.TOP_NAV_TITLE_FONT_SIZE['default']

    @staticmethod
    def get_button_font_name(locale=None):
        if not locale:
            locale = _dependency('seedsigner.models.settings', 'Settings').get_instance().get_value(_dependency('seedsigner.models.settings_definition', 'SettingsConstants').SETTING__LOCALE)
        if locale in GUIConstants.BUTTON_FONT_NAME:
            return GUIConstants.BUTTON_FONT_NAME[locale]
        else:
            return GUIConstants.BUTTON_FONT_NAME['default']

    @staticmethod
    def get_button_font_size(locale=None):
        if not locale:
            locale = _dependency('seedsigner.models.settings', 'Settings').get_instance().get_value(_dependency('seedsigner.models.settings_definition', 'SettingsConstants').SETTING__LOCALE)
        if locale in GUIConstants.BUTTON_FONT_SIZE:
            return GUIConstants.BUTTON_FONT_SIZE[locale]
        else:
            return GUIConstants.BUTTON_FONT_SIZE['default']

class FontAwesomeIconConstants:
    ANGLE_DOWN = '\uf107'
    ANGLE_LEFT = '\uf104'
    ANGLE_RIGHT = '\uf105'
    ANGLE_UP = '\uf106'
    CAMERA = '\uf030'
    CHEVRON_UP = '\uf077'
    CHEVRON_DOWN = '\uf078'
    CIRCLE = '\uf111'
    CIRCLE_CHEVRON_RIGHT = '\uf138'
    DICE = '\uf522'
    DICE_ONE = '\uf525'
    DICE_TWO = '\uf528'
    DICE_THREE = '\uf527'
    DICE_FOUR = '\uf524'
    DICE_FIVE = '\uf523'
    DICE_SIX = '\uf526'
    KEYBOARD = '\uf11c'
    LOCK = '\uf023'
    MAP = '\uf279'
    PAPER_PLANE = '\uf1d8'
    PEN = '\uf304'
    SQUARE_CARET_DOWN = '\uf150'
    SQUARE_CARET_LEFT = '\uf191'
    SQUARE_CARET_RIGHT = '\uf152'
    SQUARE_CARET_UP = '\uf151'
    UNLOCK = '\uf09c'
    X = 'X'
    BATTERY_FULL = '\uf240'
    BATTERY_THREE_QUARTERS = '\uf241'
    BATTERY_HALF = '\uf242'
    BATTERY_QUARTER = '\uf243'
    BATTERY_EMPTY = '\uf244'
    BATTERY_CHARGING = '\uf0e7'

class SeedSignerIconConstants:
    SCAN = '\ue900'
    SEEDS = '\ue901'
    SETTINGS = '\ue902'
    TOOLS = '\ue903'
    BACK = '\ue904'
    CHECK = '\ue905'
    CHECKBOX = '\ue906'
    CHECKBOX_SELECTED = '\ue907'
    CHEVRON_DOWN = '\ue908'
    CHEVRON_LEFT = '\ue909'
    CHEVRON_RIGHT = '\ue90a'
    CHEVRON_UP = '\ue90b'
    PLUS = '\ue90f'
    POWER = '\ue910'
    RESTART = '\ue911'
    INFO = '\ue912'
    SUCCESS = '\ue913'
    WARNING = '\ue914'
    ERROR = '\ue915'
    CHANGE = '\ue917'
    DERIVATION = '\ue918'
    FINGERPRINT = '\ue91a'
    PASSPHRASE = '\ue91b'
    BITCOIN_ALT = '\ue91d'
    MICROSD = '\ue91f'
    QRCODE = '\ue920'
    SIGN = '\ue921'
    DELETE = '\ue922'
    SPACE = '\ue923'
    MIN_VALUE = SCAN
    MAX_VALUE = SPACE
