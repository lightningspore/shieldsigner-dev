# SPDX-License-Identifier: MIT
import json,sys,unittest
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]/'tools'))
from review_pages_gate import verify
class ReviewReceiptTest(unittest.TestCase):
 def output(self,first='ab',header='Chars 1-2/2'):
  fixtures=[('ab','ab','public')]*3
  records=[]
  for i,mode in ((0,'revisit'),(1,'accept'),(2,'accept')):
   records.append('@@PUBLIC_REVIEW_PAGES %d %s %s'%(i,mode,json.dumps([header+'\n'+first] if i==0 else ['Chars 1-2/2\nab'])))
  for i,mode in ((0,'revisit'),(0,'exit'),(0,'wipe'),(1,'accept'),(2,'accept')):records.append('@@PASS original-paged-review %d %s 1 1'%(i,mode))
  return '\n'.join(records),'fixtures='+repr(fixtures)
 def test_complete_display_receipt_verifies(self):
  output,script=self.output();self.assertEqual(len(verify(output,script)),3)
 def test_unchanged_fingerprint_cannot_hide_wrong_display_text(self):
  output,script=self.output(first='ac')
  with self.assertRaisesRegex(ValueError,'Displayed characters differ'):verify(output,script)
 def test_invisible_data_cannot_be_claimed_visible(self):
  output,script=self.output(first='a\0')
  with self.assertRaisesRegex(ValueError,'geometry'):verify(output,script)
 def test_missing_actual_view_flow_does_not_pass(self):
  output,script=self.output();output=output.replace('@@PASS original-paged-review 0 wipe','omitted')
  with self.assertRaisesRegex(ValueError,'Missing actual original View flow'):verify(output,script)
