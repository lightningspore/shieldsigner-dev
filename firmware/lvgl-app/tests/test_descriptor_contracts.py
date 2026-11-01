import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from contracts import configuration
class DescriptorContractsTests(unittest.TestCase):
    def test_policy_and_all_fingerprints_preserved(self):
        cls=type('MultisigWalletDescriptorScreen',(),{})
        keys=[f'{n:08x}' for n in range(15)]
        builder,cfg=configuration(cls,dict(policy='8 of 15',fingerprints=keys,button_data=['OK'],selected_button=0))
        self.assertEqual(builder,'multisig_wallet_descriptor_screen');self.assertEqual(cfg['fingerprints'],keys)
        self.assertEqual(cfg['policy'],'8 of 15');self.assertEqual(cfg['button_list'],['OK']);self.assertTrue(cfg['read_first'])
        self.assertNotIn('initial_selected_index',cfg)
        for bad in ([None],['valid',''],[],['a\0b']):
            with self.assertRaises(ValueError):configuration(cls,dict(policy='public',fingerprints=bad))
    def test_load_preserves_original_actions_and_back_policy(self):
        _,cfg=configuration(type('LoadMultisigWalletDescriptorScreen',(),{}),dict(button_data=['Scan descriptor','Load SeedKeeper','Cancel'],show_back_button=False))
        self.assertEqual(cfg['button_list'],['Scan descriptor','Load SeedKeeper','Cancel'])
        self.assertFalse(cfg['top_nav']['show_back_button']);self.assertTrue(cfg['read_first'])
