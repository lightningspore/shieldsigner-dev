import unittest
from types import SimpleNamespace
from unittest.mock import patch
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from address_search import monitor
from contracts import configuration
class SeedAddressVerificationScreen:
    @staticmethod
    def _run_callback(s):
        if s.verified_index.cur_count is not None:return 1
        if s.max_iterations is not None and s.threadsafe_counter.cur_count>=s.max_iterations:return 1000
class AddressSearchTests(unittest.TestCase):
    def state(self):
        return dict(address='public-address',network='Testnet',is_mainnet=False,sig_type='Single Sig',script_type='Native Segwit',threadsafe_counter=SimpleNamespace(cur_count=0),display_index_counter=None,verified_index=SimpleNamespace(cur_count=None),max_iterations=20,button_data=['Skip 10','Cancel'])
    def test_configuration_and_counter_stay_out_of_json(self):
        builder,cfg=configuration(SeedAddressVerificationScreen,self.state())
        self.assertEqual(builder,'seed_address_verification_screen')
        self.assertEqual(cfg['type_network'],'Single Sig - Native Segwit (Testnet)')
        self.assertFalse(cfg['top_nav']['show_back_button'])
        import json
        json.dumps(cfg)
    def test_success_before_limit_and_progress_throttled(self):
        state=self.state();sent=[]
        runtime=SimpleNamespace(host=SimpleNamespace(send=lambda *a,**kw:sent.append((a,kw))))
        poll=monitor(runtime,SeedAddressVerificationScreen,state)
        with patch('address_search.time.monotonic',side_effect=[0,.01,.11]):
            self.assertIsNone(poll());state['threadsafe_counter'].cur_count=1
            self.assertIsNone(poll());self.assertIsNone(poll())
        self.assertEqual(len(sent),2)
        state['threadsafe_counter'].cur_count=20
        self.assertEqual(poll(),1000)
        state['verified_index'].cur_count=0
        self.assertEqual(poll(),1)
    def test_success_retains_nonstandard_path_warning(self):
        cls=type('SeedAddressVerificationSuccessScreen',(),{})
        builder,cfg=configuration(cls,dict(address='public-address',verified_index=7,verified_index_is_change=True,derivation_path="m/44'/0'/9'",script_type_display='Native Segwit',is_non_standard=True))
        self.assertEqual(builder,'seed_address_verification_success_screen')
        self.assertEqual(cfg['address_type_text'],'change address')
        self.assertEqual(cfg['index_text'],'index 7')
        self.assertEqual(cfg['derivation_text'],"m/44'/0'/9' (Native Segwit)")
        self.assertEqual(cfg['non_standard_text'],'Non-standard path!')
        self.assertNotIn('initial_selected_index',cfg)
        self.assertFalse(cfg['top_nav']['show_back_button'])
