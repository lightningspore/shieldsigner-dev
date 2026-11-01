import importlib.util,json,marshal,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
import import_cache
class ImportCacheTests(unittest.TestCase):
 def test_verified_code_loads_and_tampering_is_rejected(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);cache=root/'import-cache';cache.mkdir()
   policy=root/'dependency_policy.py';policy.write_text('public policy fixture')
   source=b'public source fixture';code=marshal.dumps(compile('result=42','/public/fixture.py','exec'))
   artifact=cache/'fixture.marshal';artifact.write_bytes(code)
   record=dict(magic=importlib.util.MAGIC_NUMBER.hex(),policySha256=import_cache.sha(policy.read_bytes()),modules={'fixture':dict(file=artifact.name,sourceSha256=import_cache.sha(source),codeSha256=import_cache.sha(code))})
   index=cache/'index.json';index.write_text(json.dumps(record))
   with patch.object(import_cache,'HERE',root),patch.object(sys,'pycache_prefix',None):
    namespace={};exec(import_cache.load('fixture',source),namespace);self.assertEqual(namespace['result'],42)
    self.assertIsNone(import_cache.load('fixture',b'changed original source'))
    self.assertIsNone(import_cache.load('fixture',source,filename='/other/application/fixture.py'))
    artifact.write_bytes(code+b'changed');self.assertRaises(ValueError,import_cache.load,'fixture',source)
    artifact.write_bytes(code);policy.write_text('changed adapter');self.assertIsNone(import_cache.load('fixture',source))
 def test_missing_cache_allows_development_fallback(self):
  with tempfile.TemporaryDirectory() as tmp,patch.object(import_cache,'HERE',Path(tmp)),patch.object(sys,'pycache_prefix',None):self.assertIsNone(import_cache.load('fixture',b'public'))
