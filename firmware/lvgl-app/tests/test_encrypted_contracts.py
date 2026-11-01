import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from contracts import configuration
from encrypted_contracts import TEXT_FIELDS,typed_result
class EncryptedContractsTests(unittest.TestCase):
    def test_exact_text_and_typed_save_back(self):
        for name,field in TEXT_FIELDS.items():
            cls=type(name,(),{})
            for value in ('','  café e\u0301  ','line\r\nnext','public \\ !@#'):
                builder,cfg=configuration(cls,{field:value})
                self.assertEqual(builder,'seed_add_passphrase_screen');self.assertEqual(cfg['initial_text'],value)
                self.assertEqual(typed_result(name,{'passphrase':value}),{field:value})
                self.assertEqual(typed_result(name,{'passphrase':value,'is_back_button':True}),{field:value,'is_back_button':True})
            _,cfg=configuration(cls,{field:'a\0b'})
            self.assertEqual(cfg['initial_text'],'a\0b');self.assertIn('NUL',cfg['top_nav']['title'])
    def test_public_data_prompts_have_original_buttons_and_no_back(self):
        for name,field in [('ScanEncryptedQRScreen','public_data'),('ScanAmbiguousQRScreen','message')]:
            builder,cfg=configuration(type(name,(),{}),{field:'Public fixture', 'button_data':['First','Second']})
            self.assertEqual(builder,'button_list_screen');self.assertEqual(cfg['text'],'Public fixture')
            self.assertEqual(cfg['button_list'],['First','Second']);self.assertFalse(cfg['top_nav']['show_back_button'])

    def test_custom_entry_title_keeps_common_translation(self):
        from unittest.mock import patch
        with patch('contracts._',lambda text:'translated:'+text):
            _,cfg=configuration(type('ScanTypeEncryptionKeyScreen',(),{}),dict(title='Custom title',encryptionkey='public'))
        self.assertEqual(cfg['top_nav']['title'],'translated:Custom title')

    def test_review_preserves_full_text_and_space_policy(self):
        for name,field in [('ScanReviewEncryptionKeyScreen','encryptionkey'),('SeedEncryptedQRReviewMnemonicIDScreen','mnemonic_id')]:
            for text in ('a b',' a  b ','public'*32):
                _,cfg=configuration(type(name,(),{}),{field:text,'button_data':['Proceed','Edit'],'selected_button':0})
                self.assertEqual(cfg['text'],text);self.assertTrue(cfg['read_first'])
                self.assertNotIn('initial_selected_index',cfg)
                self.assertEqual(cfg['review_spaces'],True if text==' a  b ' else (name=='ScanReviewEncryptionKeyScreen' and ' ' in text))
            _,cfg=configuration(type(name,(),{}),{field:'a\0b'})
            self.assertEqual(cfg['text'],r'a\0b');self.assertIn('NUL',cfg['top_nav']['title'])
    def test_empty_review_is_explicit_without_changing_original_argument(self):
        args={'encryptionkey':'','button_data':['Proceed']}
        _,cfg=configuration(type('ScanReviewEncryptionKeyScreen',(),{}),args)
        self.assertEqual(cfg['text'],'(empty)');self.assertEqual(args['encryptionkey'],'')
