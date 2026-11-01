import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from contracts import configuration
class PowerContractTests(unittest.TestCase):
    def test_restart_and_loader_have_no_interactive_exit(self):
        for name,title in [('ResetScreen','Restarting'),('RebootToLoaderScreen','Flash Mode')]:
            builder,cfg=configuration(type(name,(),{}),{})
            self.assertEqual(builder,'reset_screen');self.assertEqual(cfg['top_nav']['title'],title)
            self.assertFalse(cfg['top_nav']['show_back_button']);self.assertFalse(cfg['top_nav']['show_power_button'])
            self.assertNotIn('button_list',cfg)
        self.assertIn('All in-memory data will be wiped.',configuration(type('ResetScreen',(),{}),{})[1]['text'])
    def test_unplug_has_original_text_and_back(self):
        builder,cfg=configuration(type('PowerOffNotRequiredScreen',(),{}),{})
        self.assertEqual(builder,'power_off_not_required_screen');self.assertTrue(cfg['top_nav']['show_back_button'])
        self.assertEqual(cfg['text'],'It is safe to disconnect power at any time.')
