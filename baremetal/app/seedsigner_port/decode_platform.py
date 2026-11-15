# SPDX-License-Identifier: MIT
"""Native imports/image boundary for the original QR model.

Unported feature dependencies fail explicitly, even inside original broad parse
handlers. They must never turn a supported-looking payload into a false INVALID.
"""
class FeatureUnavailable(RuntimeError):
    pass

def dependency(module,attribute=None):
    special={('seedsigner.helpers','hardening'):('seedsigner_port.app_services',None),
             ('seedsigner.views.screensaver','ScreensaverScreen'):('seedsigner_port.app_services','ScreensaverScreen')}
    if (module,attribute) in special:module,attribute=special[(module,attribute)]
    aliases={'seedsigner.models.encode_qr':'seedsigner_port.encode_qr','seedsigner.helpers.qr':'seedsigner_port.qr_helper',
             'seedsigner.controller':'seedsigner_port.controller',
             'seedsigner.views':'seedsigner_port.view_core',
             'seedsigner.views.view':'seedsigner_port.view_core',
             'seedsigner.views.scan_views':'seedsigner_port.view_scan',
             'seedsigner.views.seed_views':'seedsigner_port.view_seed',
             'seedsigner.views.resign_views':'seedsigner_port.session_keys',
             'seedsigner.gui':'seedsigner_port.renderer',
             'seedsigner.gui.renderer':'seedsigner_port.renderer',
             'seedsigner.gui.toast':'seedsigner_port.app_services',
             'seedsigner.gui.screens':'seedsigner_port.app_screens',
             'seedsigner.gui.screens.screen':'seedsigner_port.app_screens',
             'seedsigner.gui.screens.seed_screens':'seedsigner_port.app_screens',
             'seedsigner.gui.screens.scan_screens':'seedsigner_port.app_screens',
             'seedsigner.models.encryptedqr':'seedsigner_port.encrypted_storage',
             'seedsigner.models.decode_qr':'seedsigner_port.decode_qr',
             'seedsigner.hardware.buttons':'seedsigner_port.hardware_buttons',
             'seedsigner.hardware.camera':'seedsigner_port.app_services',
             'seedsigner.helpers.l10n':'seedsigner_port.localization',
             'seedsigner.helpers.seedsigner_os':'seedsigner_port.app_services','seedsigner.models.settings_definition':'seedsigner_port.settings_schema',
             'seedsigner.models.seed_storage':'seedsigner_port.seed_storage',
             'seedsigner.models.singleton':'seedsigner_port.singleton',
             'seedsigner.gui.components':'seedsigner_port.gui_constants',
             'gettext':'seedsigner_port.localization',
             'seedsigner.models.aezeed':'seedsigner_port.aezeed',
             'seedsigner.models.psbt_framing':'seedsigner_port.psbt_framing',
             'seedsigner.models.psbt_parser':'seedsigner_port.psbt_errors',
             'seedsigner.models.seed':'seedsigner_port.seed',
             'seedsigner.helpers.secure_delete':'seedsigner_port.secure_delete',
             'seedsigner.models.settings':'seedsigner_port.settings_store',
             'seedsigner.models.qr_type':'seedsigner_port.qr_type'}
    module=aliases.get(module,module)
    try:
        value=__import__(module,None,None,('*',))
        return getattr(value,attribute) if attribute is not None else value
    except (ImportError,AttributeError):
        raise FeatureUnavailable('Native app dependency unavailable: '+module+('.'+attribute if attribute else ''))

def available():
    try:dependency('qr')
    except FeatureUnavailable:return False
    return True

def extract(image,is_binary=False):
    if image is None:return None
    if len(image) not in (640*480,640*480*3//2):
        raise ValueError('Expected640x480 luma or NV12 camera frame')
    return dependency('qr').decode(image[:640*480],640,480)
