import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from contracts import configuration
class PagedInfoTests(unittest.TestCase):
    def test_hardening_titles_and_actions_preserve_pages(self):
        cls=type('HardeningTestScreen',(),{});pages=['[!!] public fail detail','[--] public unknown detail']
        for index,label in [(0,'More'),(1,'Done')]:
            builder,cfg=configuration(cls,dict(paged_info=pages,page_num=index))
            self.assertEqual(builder,'button_list_screen');self.assertEqual(cfg['text'],pages[index])
            self.assertEqual(cfg['button_list'],[label]);self.assertEqual(cfg['top_nav']['title'],f'Test Hardening {index+1}/2')
            self.assertTrue(cfg['read_first']);self.assertNotIn('initial_selected_index',cfg)
    def test_bad_page_fails_closed(self):
        with self.assertRaises(ValueError):configuration(type('HardeningTestScreen',(),{}),dict(paged_info=['public'],page_num=1))

    def test_network_uses_fixed_width_and_original_next_label(self):
        builder,cfg=configuration(type('ToolsNetworkInfoScreen',(),{}),dict(paged_info=['iface   state','adb0    up'],page_num=0))
        self.assertEqual(builder,'button_list_screen');self.assertTrue(cfg['text_monospace'])
        self.assertEqual(cfg['text'],'iface   state');self.assertEqual(cfg['button_list'],['Next'])
        self.assertEqual(cfg['top_nav']['title'],'Network Info 1/2')
