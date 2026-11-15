# Copyright2021 SeedSigner; MIT, see ../LICENSE.SeedSigner
# Generated from pinned original source; optional class bases resolve only on use.
from seedsigner_port.decode_platform import dependency as _dependency, FeatureUnavailable
from seedsigner_port.navigation import Destination
def load_boot_logo_image():
    default_logo = _dependency('seedsigner.gui.components', 'load_image')(DEFAULT_LOGO_IMAGE)
    try:
        custom_logo_path = _dependency('seedsigner.hardware.microsd', 'MicroSD').get_microsd_dir() / CUSTOM_LOGO_FILENAME
        if not custom_logo_path.is_file():
            return default_logo
        with _dependency('PIL', 'Image').open(custom_logo_path) as custom_logo:
            custom_logo = custom_logo.convert('RGB')
        if custom_logo.size != default_logo.size:
            pass
            return default_logo
        return custom_logo
    except FeatureUnavailable:
        raise
    except Exception:
        pass
        return default_logo

def _make_OpeningSplashView():

    class OpeningSplashView(_dependency('seedsigner.views.view', 'View')):

        def run(self):
            self.run_screen(_dependency('seedsigner_port.app_screens', 'OpeningSplashScreen'), force_partner_logos=self.force_partner_logos)

        def __init__(self, force_partner_logos=None):
            self.force_partner_logos = force_partner_logos
            self.__post_init__()
    return OpeningSplashView

_FACTORIES={'OpeningSplashView':_make_OpeningSplashView}
_CACHE={}
def _resolve(name):
    if name not in _CACHE:
        if name not in _FACTORIES:raise AttributeError(name)
        _CACHE[name]=_FACTORIES[name]()
    return _CACHE[name]
def __getattr__(name):return _resolve(name)
