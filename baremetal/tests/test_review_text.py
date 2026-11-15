# SPDX-License-Identifier: MIT
"""Independent Python escape decoding proves lossless display identities."""
import codecs,sys,unittest
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]/'app'))
from seedsigner_port.review_text import pages,character,short_visible,COLUMNS,LINES,page_config
class ReviewTextTest(unittest.TestCase):
 def assert_roundtrip(self,value):
  content=pages(value);encoded='';position=0
  for first,end,rows in content:
   self.assertEqual(first,position);position=end
   self.assertLessEqual(len(rows),LINES)
   for row in rows:self.assertLessEqual(len(row),COLUMNS)
   encoded+=''.join(rows)
  self.assertEqual(position,len(value))
  self.assertEqual(codecs.decode(encoded,'unicode_escape'),value)
 def test_all_valid_scalar_identities_decode_independently(self):
  for cp in range(0x110000):
   if 0xd800<=cp<=0xdfff:continue
   c=chr(cp);escaped=character(c)
   self.assertTrue(escaped.isascii())
   self.assertTrue(all(33<=ord(c)<=126 for c in escaped))
   self.assertEqual(codecs.decode(escaped,'unicode_escape'),c)
 def test_pages_cover_long_and_hidden_values_without_truncation(self):
  for value in ('','x'*255,' '*255,'é🙂\0\\\n\t end  ','\\u0020 literal \\U0001F642','🙂'*63,chr(0x10ffff)*25):self.assert_roundtrip(value)
 def test_visible_short_path_requires_no_ambiguous_characters(self):
  for value in ('','k','password123!','x'*16):self.assertTrue(short_visible(value))
  for value in ('x'*17,'a b','a\\b','é','\0','\n','a\u200bb'):self.assertFalse(short_visible(value))
 def test_indices_and_page_text_are_presentation_only(self):
  value='x'*255;content=pages(value)
  for i,page in enumerate(content):
   cfg=page_config(value,page,i,len(content))
   self.assertEqual(cfg['button_list'],['Next'])
   self.assertTrue(cfg['read_first'])
   self.assertTrue(cfg['text'].isascii())
   self.assertIn('Chars %d-%d/255'%(page[0]+1,page[1]),cfg['text'])
