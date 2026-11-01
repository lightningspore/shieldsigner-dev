import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from locale_supplement import expand,FINAL,WARNINGS
class LocaleSupplementTests(unittest.TestCase):
 def test_hindi_exact_bip39_pairs_and_other_strings_unchanged(self):
  template='{mnemonic_length}वां {num_bits}'
  entries,proof=expand('hi',[(FINAL,template),('Keep','अक्षर')])
  self.assertEqual([row['text'] for row in proof],['12वां 7','24वां 3'])
  self.assertIn(('Keep','अक्षर'),entries)
  self.assertTrue(all('{' not in msgid for msgid,text in entries))
 def test_thai_uses_translated_semantics_and_both_denominations(self):
  entries=[(item,'คำ\n{}') for item in WARNINGS]+[('{} change','{}เงินทอน'),('change','เงินทอน'),('self-transfer','โอนให้ตัวเอง'),('btc','btc'),('sats','sats')]
  result,proof=expand('th',entries)
  self.assertEqual(len(proof),6)
  for warning in WARNINGS:
   self.assertEqual({row['text'] for row in proof if row['msgid']==warning},{'คำ\nเงินทอน','คำ\nโอนให้ตัวเอง'})
  self.assertEqual({row['text'] for row in proof if row['msgid']=='{} change'},{'btcเงินทอน','satsเงินทอน'})
  self.assertIn(('self-transfer','โอนให้ตัวเอง'),result)
 def test_other_locales_unchanged(self):
  data=[('arbitrary {}','translated {}')];self.assertEqual(expand('ja',data),(data,[]))
 def test_missing_pinned_template_fails_closed(self):
  with self.assertRaises(ValueError):expand('hi',[])
  with self.assertRaises(ValueError):expand('th',[])
