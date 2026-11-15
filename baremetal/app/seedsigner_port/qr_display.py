# SPDX-License-Identifier: MIT
"""Foreground static QR facade using the original native QR screen and events."""
from seedsigner_port.decode_platform import FeatureUnavailable
class QRDisplayScreen:
    def __init__(self,qr_encoder,cancel_on_back=False,**kwargs):
        self.encoder=qr_encoder;self.cancel_on_back=cancel_on_back
        if kwargs:raise FeatureUnavailable('QR screen arguments not reviewed')
    def display(self):
        if self.cancel_on_back:raise FeatureUnavailable('Native QR exit key identity not yet exposed')
        if self.encoder.seq_len()!=1:raise FeatureUnavailable('Animated QR frame transport not yet ported')
        data=self.encoder.next_part()
        if type(data) not in (str,bytes) or not data or len(data)>512:raise ValueError('Static QR payload outside reviewed512-byte bound')
        if type(data) is str:
            data=data.encode('utf-8')
            if len(data)>512:raise ValueError('Static QR UTF8 payload too large')
        from seedsigner_port.renderer import Renderer
        from seedsigner_port.settings_store import Settings,SettingsConstants as C
        from seedsigner_port.localization import gettext as _
        renderer=Renderer.get_instance();settings=Settings.get_instance()
        brightness=settings.get_value(C.SETTING__QR_BRIGHTNESS)
        cfg={'qr_data':data.hex(),'data_encoding':'hex','qr_mode':'auto','border':2,
             'initial_brightness':brightness,'density_control':False,
             'show_brightness_tips':settings.get_value(C.SETTING__QR_BRIGHTNESS_TIPS)==C.OPTION__ENABLED,
             'brighter_text':_('Brighter'),'darker_text':_('Darker')}
        renderer.session.show('qr_display_screen',cfg)
        while True:
            event=renderer.session.wait()
            if event==1000:
                settings.set_value(C.SETTING__QR_BRIGHTNESS,brightness,save=False);return None
            if event[0]==4:
                if not 31<=event[1]<=255:raise ValueError('Invalid native QR brightness')
                brightness=event[1]
            elif event[0]==1 and event[1]==1000:
                settings.set_value(C.SETTING__QR_BRIGHTNESS,brightness,save=False)
                return None
            else:raise ValueError('Unexpected native static QR event')
