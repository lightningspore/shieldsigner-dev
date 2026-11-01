import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from contracts import configuration
class FinalWordContractsTests(unittest.TestCase):
    def test_entropy_bits_are_not_recalculated_or_truncated(self):
        for selected,checksum in [('1010101','0011'),('101','00110011'),('10101010101','0011')]:
            _,cfg=configuration(type('ToolsCalcFinalWordScreen',(),{}),dict(selected_final_bits=selected,checksum_bits=checksum,actual_final_word='public',selected_final_word=None,button_data=['Next']))
            self.assertEqual(cfg['selected_final_bits'],selected);self.assertEqual(cfg['checksum_bits'],checksum)
            self.assertFalse(cfg['has_selected_word']);self.assertEqual(cfg['button_list'],['Next'])
    def test_sizes_and_done_values(self):
        for length,bits in [(12,7),(24,3)]:
            _,cfg=configuration(type('ToolsCalcFinalWordFinalizePromptScreen',(),{}),dict(mnemonic_length=length,num_entropy_bits=bits,button_data=['Coin','Word','Zeros']))
            self.assertIn(str(bits),cfg['text']);self.assertEqual(len(cfg['button_list']),3)
            _,cfg=configuration(type('ToolsCalcFinalWordDoneScreen',(),{}),dict(mnemonic_word_length=length,final_word='public',fingerprint='12345678',button_data=['Load','Discard']))
            self.assertEqual(cfg['final_word'],'public');self.assertEqual(cfg['fingerprint'],'12345678')
        with self.assertRaises(ValueError):configuration(type('ToolsCalcFinalWordScreen',(),{}),dict(selected_final_bits='10x',checksum_bits='0011',actual_final_word='public'))
