import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from startup_splash import configuration,install
class SplashTests(unittest.TestCase):
    def test_exact_version_fork_caption_and_nondismissible(self):
        cfg=configuration('v0.1.0-dev-123',True)
        self.assertEqual(cfg['version'],'v0.1.0-dev-123')
        self.assertEqual(cfg['sponsor_text'],'An unofficial fork of:')
        self.assertFalse(cfg['dismissible']);self.assertFalse(cfg['allow_screensaver'])
        self.assertTrue(cfg['show_partner_logos'])
        self.assertFalse(configuration('version',True,False)['show_partner_logos'])
        with self.assertRaises(ValueError):configuration('version',False,'false')
    def test_custom_screen_constructor_never_allocates_pil(self):
        class Splash:
            def __init__(self,force_partner_logos=None):raise AssertionError('PIL logo loaded')
            def display(self):return 'original'
        from types import SimpleNamespace
        calls=[];original=Splash.__init__
        restore=install(SimpleNamespace(run=lambda cls,args:calls.append((cls,args))),Splash)
        try:
            screen=Splash(force_partner_logos=False);screen.display()
            self.assertEqual(calls,[(Splash,{'force_partner_logos':False})])
        finally:restore()
        self.assertIs(Splash.__init__,original)
