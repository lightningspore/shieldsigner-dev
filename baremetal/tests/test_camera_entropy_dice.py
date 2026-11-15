# SPDX-License-Identifier: MIT
"""Original manual-dice hash semantics and native keyboard value boundary."""
import hashlib,sys,types,unittest
from pathlib import Path
from unittest.mock import patch
root=Path(__file__).resolve().parents[1];sys.path.append(str(root/'app'))
from seedsigner_port.camera_entropy_mnemonic import DICE_ROLLS_REQUIRED,ENTROPY_BYTES_REQUIRED,generate_bytes_from_dice,dice_entropy_is_sufficient
from seedsigner_port.camera_entropy_dice import ToolsDiceEntropyEntryScreen
class DiceEntropyTest(unittest.TestCase):
 def test_original_roll_counts_sha256_and_entropy_truncation(self):
    for words,count in DICE_ROLLS_REQUIRED.items():
        rolls=('123456'*20)[:count]
        self.assertEqual(generate_bytes_from_dice(rolls),hashlib.sha256(rolls.encode()).digest()[:ENTROPY_BYTES_REQUIRED[words]])
        self.assertTrue(dice_entropy_is_sufficient(rolls));self.assertFalse(dice_entropy_is_sufficient('1'*count))
 def display(self,total,event):
    captured={}
    class Session:
        def show(self,builder,cfg):captured.update(builder=builder,config=cfg)
        def wait(self):return event
    renderer=types.SimpleNamespace(session=Session())
    module=types.SimpleNamespace(Renderer=type('Renderer',(),{'get_instance':classmethod(lambda cls:renderer)}))
    with patch.dict(sys.modules,{'seedsigner_port.renderer':module}):value=ToolsDiceEntropyEntryScreen(total).display()
    return value,captured
 def test_native_dice_keyboard_uses_original_six_face_mapping_and_count(self):
    rolls=('123456'*9)[:50];value,seen=self.display(50,(2,0,rolls))
    self.assertEqual(value,rolls);self.assertEqual(seen['builder'],'keyboard_screen')
    cfg=seen['config'];self.assertEqual(cfg['return_after_n_chars'],50)
    self.assertEqual(list(cfg['keys_to_values'].values()),list('123456'))
    self.assertEqual(cfg['title_keystroke_template'],'Dice Roll {n}/{total}')
    self.assertEqual(cfg['top_nav']['title'],'Dice Roll 1/50');self.assertEqual(cfg['cols'],3)
    self.assertFalse(cfg['show_save_button']);self.assertFalse(cfg['show_cursor_keys'])
 def test_back_cancels_and_invalid_or_short_native_text_is_rejected(self):
    for event in (1000,(1,1000,'')):
        self.assertEqual(self.display(50,event)[0],1000)
    for event in ((2,0,'123'),(2,0,'1'*49+'0'),(2,0,'1'*49+'7'),(2,1,'1'*50),(1,0,'')):
        with self.assertRaises(ValueError):self.display(50,event)
    for count in (0,49,51,100,True):
        with self.assertRaises(ValueError):ToolsDiceEntropyEntryScreen(count)
