import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from contracts import configuration
from textqr_contracts import typed_result
class TextQRTests(unittest.TestCase):
    def test_exact_entry_and_back_contract(self):
        value='  café \\u0041\n '
        builder,cfg=configuration(type('ToolsTextQRTextEntryScreen',(),{}),{'textToEncode':value})
        self.assertEqual(builder,'seed_add_passphrase_screen');self.assertEqual(cfg['initial_text'],value)
        self.assertEqual(typed_result({'passphrase':value}),{'textToEncode':value})
        self.assertEqual(typed_result({'passphrase':value,'is_back_button':True}),{'textToEncode':value,'is_back_button':True})
    def test_review_keeps_whitespace_and_requires_reading(self):
        value=' space  café\n'
        _,cfg=configuration(type('ToolsTextQRReviewTextScreen',(),{}),{'textToEncode':value,'button_data':['Generate','Edit']})
        self.assertEqual(cfg['text'],value);self.assertTrue(cfg['review_spaces']);self.assertTrue(cfg['read_first'])
    def test_embedded_nul_and_bad_results_fail_explicitly(self):
        with self.assertRaises(ValueError):configuration(type('ToolsTextQRTextEntryScreen',(),{}),{'textToEncode':'a\0b'})
        with self.assertRaises(ValueError):typed_result({'passphrase':42})
