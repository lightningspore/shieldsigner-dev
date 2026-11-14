# SPDX-License-Identifier: MIT
"""Native imports/image boundary for the original QR model.

Unported feature dependencies fail explicitly, even inside original broad parse
handlers. They must never turn a supported-looking payload into a false INVALID.
"""
class FeatureUnavailable(RuntimeError):
    pass

def dependency(module,attribute=None):
    aliases={'seedsigner.models.psbt_framing':'seedsigner_port.psbt_framing',
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
