import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from contracts import configuration
class DonateTests(unittest.TestCase):
    def test_upstream_builder_and_original_attribution(self):
        builder,cfg=configuration(type('DonateScreen',(),{}),{})
        self.assertEqual(builder,'donate_screen');self.assertEqual(cfg['url'],'seedsigner.com')
        self.assertEqual(cfg['text'],'SeedSigner is 100% free & open source, funded solely by the Bitcoin community.\n\nDonate onchain or LN at:')
        self.assertEqual(cfg['top_nav']['title'],'Donate');self.assertNotIn('button_list',cfg)
