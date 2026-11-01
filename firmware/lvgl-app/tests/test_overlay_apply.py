import hashlib,json,shutil,stat,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from overlay_apply import apply,verify,root_check
from image_stage import HERE,ROOT,BASE
class OverlayApplyTests(unittest.TestCase):
 def setUp(self):
  temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
  self.draft=Path(temporary.name)/'draft';self.draft.mkdir()
  self.source=b'Public original View fixture\n'
  guards={'views/view.py':hashlib.sha256(self.source).hexdigest()}
  contents={
   'usr/bin/shieldsigner-launch':b'#!/bin/sh\nexit 0\n',
   'usr/bin/shieldsigner-launch.pil':BASE.read_bytes(),
   'usr/lib/shieldsigner-lvgl/python/source-guards.json':json.dumps(guards).encode(),
  }
  files={}
  for relative,data in contents.items():
   path=self.draft/'payload'/relative;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data);path.chmod(0o644)
   files['payload/'+relative]=dict(sha256=hashlib.sha256(data).hexdigest(),bytes=len(data),mode=0o644)
  plan=dict(kind='shieldsigner-lvgl-image-overlay-draft',schema=1,imageBuilt=False,installed=False,releaseReady=False,defaultFrontend='pil',baseLauncherSha256=hashlib.sha256(BASE.read_bytes()).hexdigest(),files=files)
  (self.draft/'integration-plan.json').write_text(json.dumps(plan))
 def fixture(self,root):
  (root/'etc').mkdir(parents=True);(root/'etc/seedsigner-os-release').write_text('Public offline fixture\n')
  (root/'usr/bin').mkdir(parents=True);shutil.copyfile(BASE,root/'usr/bin/shieldsigner-launch')
  path=root/'usr/lib/shieldsigner-camera/image-installation.json';path.parent.mkdir(parents=True)
  path.write_text(json.dumps(dict(startupSha256={'usr/bin/shieldsigner-launch':hashlib.sha256(BASE.read_bytes()).hexdigest()},startupModes={'usr/bin/shieldsigner-launch':0o644})))
  (root/'start-seedsigner.sh').write_text('Public supervisor fixture\n')
  path=root/'opt/src/seedsigner/views/view.py';path.parent.mkdir(parents=True);path.write_bytes(self.source)
 def test_success_preserves_supervisor_and_exact_rollback(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);self.fixture(root);result=apply(root,self.draft)
   self.assertTrue(result['verified']);self.assertEqual(result['defaultFrontend'],'pil')
   self.assertEqual((root/'usr/bin/shieldsigner-launch.pil').read_bytes(),BASE.read_bytes())
   self.assertEqual((root/'start-seedsigner.sh').read_text(),'Public supervisor fixture\n')
   self.assertFalse(result['deviceInstalled']);self.assertFalse(result['imageBuilt'])
   self.assertEqual(verify(root,self.draft),result)
 def test_changed_app_fails_before_any_overlay_write(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);self.fixture(root);(root/'opt/src/seedsigner/views/view.py').write_text('Changed public fixture')
   with self.assertRaisesRegex(ValueError,'application source differs'):apply(root,self.draft)
   self.assertFalse((root/'usr/lib/shieldsigner-lvgl').exists())
   self.assertFalse((root/'usr/bin/shieldsigner-launch.pil').exists())
 def test_changed_camera_launcher_fails_before_any_overlay_write(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);self.fixture(root);(root/'usr/bin/shieldsigner-launch').write_text('Changed public launcher')
   with self.assertRaisesRegex(ValueError,'camera launcher differs|Camera startup provenance changed'):apply(root,self.draft)
   self.assertFalse((root/'usr/lib/shieldsigner-lvgl').exists())
 def test_symlink_parent_is_rejected_before_writes(self):
  with tempfile.TemporaryDirectory() as tmp,tempfile.TemporaryDirectory() as outside:
   root=Path(tmp);self.fixture(root);(root/'usr/share').symlink_to(outside,target_is_directory=True)
   with self.assertRaisesRegex(ValueError,'escapes rootfs|Symlink'):apply(root,self.draft)
   self.assertEqual(list(Path(outside).iterdir()),[])
 def test_modified_copied_launcher_fails_verification(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);self.fixture(root);apply(root,self.draft);(root/'usr/bin/shieldsigner-launch').write_text('Changed public fixture')
   with self.assertRaisesRegex(ValueError,'overlay changed|Camera startup provenance changed'):verify(root,self.draft)
 def test_draft_root_alias_is_normalized(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)/'rootfs';root.mkdir();self.fixture(root)
   alias=Path(tmp)/'draft-alias';alias.symlink_to(self.draft,target_is_directory=True)
   self.assertTrue(apply(root,alias)['verified'])
 def test_live_root_is_refused(self):
  with self.assertRaisesRegex(ValueError,'live root'):root_check(Path('/'))
