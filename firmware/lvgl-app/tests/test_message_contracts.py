import sys,unittest
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from message_contracts import prepare,configure
class MessageContractsTests(unittest.TestCase):
    def test_original_message_preserved_with_one_scroll_page(self):
        for text in ('',' public  café\nnext ','x'*4096):
            data={'message':text};screen=SimpleNamespace(page_num=0)
            prepare(screen,SimpleNamespace(sign_message_data=data))
            self.assertEqual(data['message'],text);self.assertEqual(data['paged_message'],[text])
            builder,cfg=configure('SeedSignMessageConfirmMessageScreen',vars(screen),{'top_nav':{},'initial_selected_index':0})
            self.assertEqual(builder,'seed_sign_message_confirm_message_screen');self.assertEqual(cfg['message'],text)
            self.assertNotIn('initial_selected_index',cfg)
    def test_cached_pages_and_invalid_data(self):
        data={'message':'public one public two','paged_message':['public one','public two']}
        screen=SimpleNamespace(page_num=1);prepare(screen,SimpleNamespace(sign_message_data=data))
        self.assertEqual(screen.message,'public two')
        screen.page_num=2
        with self.assertRaises(ValueError):prepare(screen,SimpleNamespace(sign_message_data=data))
        with self.assertRaises(ValueError):prepare(SimpleNamespace(page_num=0),SimpleNamespace(sign_message_data={'message':'a\0b'}))
    def test_address_and_path_exact(self):
        _,cfg=configure('SeedSignMessageConfirmAddressScreen',dict(address='bc1public',derivation_path="m/84h/0h/0h/0/0"),{'top_nav':{}})
        self.assertEqual(cfg['address'],'bc1public');self.assertEqual(cfg['derivation_path'],"m/84h/0h/0h/0/0")
        self.assertEqual(cfg['button_list'],['Sign message'])
