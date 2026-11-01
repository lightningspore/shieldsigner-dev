import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from word_pagination import compile_run
from contracts import configuration
class WordPaginationTests(unittest.TestCase):
 def test_partial_and_full_wordsets_preserved_in_order(self):
  source='''def run(self):
    mnemonic=self.words
    words_per_page=4
    num_pages=int(len(mnemonic)/words_per_page)
    return [mnemonic[i*words_per_page:(i+1)*words_per_page] for i in range(num_pages)]
'''
  fixed=compile_run(source,{},'<public-word-pages>')
  for count in (12,15,18,20,21,24,33):
   with self.subTest(count=count):
    owner=type('PublicWords',(),{'words':[str(n) for n in range(count)]})()
    pages=fixed(owner)
    self.assertEqual(sum(pages,[]),owner.words)
    for index,page in enumerate(pages):
     _,cfg=configuration(type('SeedWordsScreen',(),{}),dict(words=page,page_index=index,num_pages=len(pages)))
     self.assertEqual(cfg['start_number'],index*4+1)
 def test_changed_calculation_fails_closed(self):
  with self.assertRaises(ValueError):compile_run('def run(self):\n num_pages=3',{},'<changed>')
