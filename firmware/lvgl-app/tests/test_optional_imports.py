import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from optional_imports import REFERENCE,validate
class OptionalImportTests(unittest.TestCase):
 def test_initializer_matches_reviewed_source(self):validate(compile(REFERENCE,'/public/path/__init__.py','exec'))
 def test_changed_export_or_extra_code_is_rejected(self):
  for source in (REFERENCE.replace('from .utils import MnemonicError','from .utils import OtherError'),REFERENCE+'\nraise RuntimeError()'):
   with self.assertRaises(ValueError):validate(compile(source,'<public changed initializer>','exec'))
