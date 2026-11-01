import ast,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from stream_imports import deferred
SOURCE=Path(__file__).resolve().parents[2]/'rkaiq-rs/python/shieldsigner_video_stream.py'
class StreamImportTests(unittest.TestCase):
 def test_only_import_location_changes(self):
  original=SOURCE.read_bytes();changed=deferred(original)
  marker='    def _frame_from_payload(self, width, height, payload):\n'
  restored=changed.replace(marker+'        from PIL import Image  #',marker+'        #').replace('\n\nfrom shieldsigner_process_log import','\nfrom PIL import Image\nfrom shieldsigner_process_log import',1)
  self.assertEqual(restored,original.decode())
  with self.assertRaises(ValueError):deferred(original+b'\n# unknown revision')
 def test_legacy_rgb_and_luma_pixels_remain_exact(self):
  tree=ast.parse(deferred(SOURCE.read_bytes()));cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='PiVideoStream')
  methods=[n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name in ('_validate_frame_header','_frame_from_payload')]
  scope={};exec(compile(ast.Module(body=methods,type_ignores=[]),'<public original stream methods>','exec'),scope)
  fixture=type('PublicStream',(),{name:scope[name] for name in ('_validate_frame_header','_frame_from_payload')})()
  for transport,payload,expected,mode in [('rgb',bytes(range(12)),bytes(range(12)),'RGB'),('nv12',bytes(range(6)),bytes(range(4)),'L')]:
   fixture.transport=transport;fixture.width=fixture.height=2;image=fixture._frame_from_payload(2,2,payload)
   try:self.assertEqual(image.tobytes(),expected);self.assertEqual(image.mode,mode)
   finally:image.close()
