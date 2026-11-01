import linecache,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from source_text import getsource

class SourceTextTests(unittest.TestCase):
 def test_real_file_source_is_exact_and_cache_is_released_each_time(self):
  with tempfile.TemporaryDirectory() as temporary:
   path=Path(temporary)/'public_source.py'
   path.write_text('padding=0\n'*10000+'def public():\n    return 42\n')
   module=types.ModuleType('public_source_fixture');module.__file__=str(path)
   sys.modules[module.__name__]=module
   try:
    exec(compile(path.read_text(),str(path),'exec'),module.__dict__)
    for _ in range(2):
     self.assertEqual(getsource(module.public),'def public():\n    return 42\n')
     self.assertNotIn(str(path),linecache.cache)
     self.assertEqual(module.public(),42)
   finally:sys.modules.pop(module.__name__,None);linecache.cache.pop(str(path),None)

 def test_generated_source_remains_available(self):
  name='<public generated adapter>';source='def public():\n    return 42\n'
  entry=(len(source),None,source.splitlines(True),name)
  linecache.cache[name]=entry;namespace={}
  try:
   exec(compile(source,name,'exec'),namespace)
   self.assertEqual(getsource(namespace['public']),source)
   self.assertIs(linecache.cache[name],entry)
  finally:linecache.cache.pop(name,None)

 def test_failed_extraction_also_releases_real_file_cache(self):
  with tempfile.TemporaryDirectory() as temporary:
   path=Path(temporary)/'public.py';path.write_text('public fixture')
   linecache.cache[str(path)]=(1,None,['public fixture'],str(path))
   with patch('source_text.inspect.getsourcefile',return_value=str(path)),patch('source_text.inspect.getsource',side_effect=OSError('fixture')):
    with self.assertRaises(OSError):getsource(object())
   self.assertNotIn(str(path),linecache.cache)
