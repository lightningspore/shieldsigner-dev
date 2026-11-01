import hashlib,json,os,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from locale_assets import LocaleAssets
class Host:
 def __init__(self):self.requests=[]
 def send(self,op,**kwargs):self.requests.append((op,kwargs));self.locale=kwargs['locale']
 def next_event(self):return dict(event='locale_ready',locale=self.locale,loaded=True)
class LocaleAssetsTests(unittest.TestCase):
 def make(self,root):
  path=Path(root)/'el';path.mkdir();data=b'{"locale":"el","source_family":"OpenSans"}'
  (path/'manifest.json').write_bytes(data)
  index=dict(kind='shieldsigner-lvgl-locale-assets',schema=1,locales=['en','el'],manifests={'el':{}},files={'el/manifest.json':dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())})
  (Path(root)/'runtime-index.json').write_text(json.dumps(index));return index
 def test_change_and_host_replacement_sync(self):
  with tempfile.TemporaryDirectory() as root:
   self.make(root);assets=LocaleAssets(root);first=Host();second=Host()
   with patch.dict(os.environ,LANGUAGE='en'):
    assets.sync(first);assets.sync(first);self.assertEqual(len(first.requests),1)
    os.environ['LANGUAGE']='el';assets.sync(first)
    self.assertNotIn('root',first.requests[-1][1])
    assets.sync(second);self.assertIn('root',second.requests[-1][1])
 def test_changed_file_rejected(self):
  with tempfile.TemporaryDirectory() as root:
   self.make(root);path=Path(root)/'el/manifest.json';path.write_bytes(b'x'*path.stat().st_size)
   with self.assertRaisesRegex(ValueError,'hash mismatch'):LocaleAssets(root)
 def test_unindexed_manifest_rejected(self):
  with tempfile.TemporaryDirectory() as root:
   index=self.make(root);index['files']={};(Path(root)/'runtime-index.json').write_text(json.dumps(index))
   with self.assertRaisesRegex(ValueError,'Unindexed'):LocaleAssets(root)
 def test_symlink_rejected(self):
  with tempfile.TemporaryDirectory() as root:
   self.make(root);path=Path(root)/'el/manifest.json';data=path.read_bytes();path.unlink();other=Path(root)/'other';other.write_bytes(data);path.symlink_to(other)
   with self.assertRaisesRegex(ValueError,'Unsafe'):LocaleAssets(root)
 def test_absent_language_rejected_before_native_request(self):
  with tempfile.TemporaryDirectory() as root:
   self.make(root);assets=LocaleAssets(root);host=Host()
   with patch.dict(os.environ,LANGUAGE='xx'),self.assertRaisesRegex(ValueError,'absent'):assets.sync(host)
   self.assertEqual(host.requests,[])
