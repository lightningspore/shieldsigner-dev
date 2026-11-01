import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from contracts import configuration,result
class ExplorerContractsTests(unittest.TestCase):
    def test_complete_page_result_count_and_navigation_state(self):
        cls=type('ToolsAddressExplorerAddressListScreen',(),{})
        addresses=['public'+str(n) for n in range(10)]
        _,cfg=configuration(cls,dict(addresses=addresses,start_index=10,selected_button=7,scroll_y_initial_offset=-120))
        self.assertEqual(cfg['addresses'],addresses);self.assertEqual(cfg['start_index'],10)
        self.assertEqual(cfg['initial_selected_index'],7);self.assertEqual(cfg['initial_scroll_y'],-120)
        self.assertEqual(cfg['next_label'],'Next 10')
        self.assertEqual(result({'event':'button_selected','index':10},len(cfg['button_list'])),10)
        with self.assertRaises(ValueError):result({'event':'button_selected','index':11},len(cfg['button_list']))
        for values in ([],['a\0b'],[None]):
            with self.assertRaises(ValueError):configuration(cls,dict(addresses=values))
    def test_descriptor_context_exact(self):
        _,cfg=configuration(type('ToolsAddressExplorerAddressTypeScreen',(),{}),dict(wallet_descriptor_display_name='2 / 3 multisig',button_data=['Receive addresses','Change addresses']))
        self.assertEqual(cfg['wallet_descriptor_text'],'2 / 3 multisig');self.assertEqual(len(cfg['button_list']),2)
