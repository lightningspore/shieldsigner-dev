# SPDX-License-Identifier: MIT
"""Original QR matrix encoder boundary, with explicit image-backend exclusion."""

from seedsigner_port.decode_platform import FeatureUnavailable


class QR:
    STYLE__DEFAULT = 1
    STYLE__ROUNDED = 2
    STYLE__GRID = 3

    def qrsize(self, data):
        return len(matrix(data))

    def qrimage(self, *args, **kwargs):
        raise FeatureUnavailable('Use native QR screen matrix; no PIL image')

    qrimage_io = qrimage


def matrix(data):
    if type(data) not in (str, bytes) or not data or len(data) > 256:
        raise ValueError('QR payload outside reviewed256-byte bound')
    if type(data) is str and len(data.encode('utf-8')) > 256:
        raise ValueError('QR UTF8 payload exceeds reviewed byte bound')
    import qrcode

    q = qrcode.QRCode(
        version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=5, border=0
    )
    q.add_data(data)
    q.make(fit=True)
    if q.modules_count > 33:
        raise ValueError('QR exceeds reviewed transcription templates')
    return q.modules
