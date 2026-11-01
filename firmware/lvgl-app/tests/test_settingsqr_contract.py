import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from contracts import configuration
class SettingsQRContractTests(unittest.TestCase):
    def test_review_has_apply_cancel_and_preserves_user_name(self):
        cls=type('SettingsQRReviewScreen',(),{})
        builder,cfg=configuration(cls,{'config_name':'Public café','show_back_button':True})
        self.assertEqual(builder,'button_list_screen');self.assertEqual(cfg['button_list'],['Apply','Cancel'])
        self.assertTrue(cfg['text'].startswith('"Public café"\n\n'));self.assertFalse(cfg['top_nav']['show_back_button'])
    def test_confirmation_reuses_upstream_and_requires_home(self):
        builder,cfg=configuration(type('SettingsQRConfirmationScreen',(),{}),{'config_name':'Public','status_message':'Temporary settings'})
        self.assertEqual(builder,'settings_qr_confirmation_screen');self.assertEqual(cfg['button_list'],['Home'])
        self.assertEqual(cfg['config_name'],'Public');self.assertEqual(cfg['status_message'],'Temporary settings')
    def test_invalid_content_rejected(self):
        for args in ({'config_name':'bad\0name'},{'status_message':42}):
            with self.assertRaises(ValueError):configuration(type('SettingsQRReviewScreen',(),{}),args)
