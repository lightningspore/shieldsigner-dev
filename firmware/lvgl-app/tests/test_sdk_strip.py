"""Preserve only reviewed runtime files through the actual pinned SDK strip loop."""
import importlib.util,json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE))
from attach_image_bundle import strip_helper
spec=importlib.util.spec_from_file_location('public_camera_overlay',HERE.parents[1]/'scripts/camera-image-overlay.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
SDK_FUNCTION=(HERE/'tests/sdk-release-function.sh.txt').read_text()
SOURCE=SDK_FUNCTION+'\nfunction __COPY_FILES() {\n :\n}\n'
class SdkStripTests(unittest.TestCase):
 def test_helper_replaces_only_known_function(self):
  old=(HERE/'patches/sdk-strip-base.py.txt').read_text()
  result=strip_helper('import json\n'+old+'\nPUBLIC_CONTROL=1\n')
  self.assertTrue(result.startswith('import json\n'));self.assertTrue(result.endswith('\nPUBLIC_CONTROL=1\n'))
  self.assertIn('lvgl_path',result)
  with self.assertRaises(ValueError):strip_helper(old.replace('base_after = after','base_after = before'))
 def test_known_sdk_states_and_only_exact_lvgl_path(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);sdk=root/'sdk';bundle=root/'bundle'
   (sdk/'project').mkdir(parents=True);(bundle/'payload').mkdir(parents=True)
   script=sdk/'project/build.sh';script.write_text(SOURCE)
   (bundle/'payload/kernel-camera-abi.json').write_text(json.dumps(dict(sdkRevision='public-pinned-revision')))
   for lvgl in (False,True):
    (bundle/'manifest.json').write_text(json.dumps(dict(lcdBackend='rust',**({'lvglOverlay':dict(defaultFrontend='lvgl')} if lvgl else {}))))
    for repeat in range(2):
     with patch.object(module.subprocess,'check_output',side_effect=['public-pinned-revision',SOURCE]):receipt=module.configure_sdk_strip(sdk,bundle)
     self.assertEqual('/usr/lib/shieldsigner-lvgl/shieldsigner-lvgl' in receipt['excludedPaths'],lvgl)
     self.assertTrue(receipt['allOtherStripBehaviorPreserved'])
   modified=script.read_text()
   self.assertIn("-path '*/usr/lib/shieldsigner-lvgl/shieldsigner-lvgl'",modified)
   self.assertNotIn("-name 'shieldsigner-lvgl'",modified)
   if sys.platform.startswith('linux'):
    tree=root/'rootfs';paths=['usr/lib/shieldsigner-lvgl/shieldsigner-lvgl','usr/bin/ordinary','usr/lib/shieldsigner-lvgl/ordinary','opt/shieldsigner-lvgl','usr/lib/shieldsigner-camera/camera-probe','usr/lib/shieldsigner-camera/shieldsigner-qr-reader','usr/lib/shieldsigner-camera/python/shieldsigner_lcd.abi3.so']
    for name in paths:
     target=tree/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_text('public executable');target.chmod(0o755)
    tool=root/'public-strip';log=root/'stripped'
    tool.write_text('#!/bin/sh\nfor arg do printf "%s\\n" "$arg" >> "$PUBLIC_STRIP_LOG"; done\n');tool.chmod(0o755)
    invocation='\nmsg_info() { :; }; msg_warn() { :; }; RK_PROJECT_TOOLCHAIN_CROSS='+str(root/'public')+'; __RELEASE_FILESYSTEM_FILES "$PUBLIC_TREE"\n'
    subprocess.run(['bash','-c',modified+invocation],check=True,env=dict(os.environ,PUBLIC_TREE=str(tree),PUBLIC_STRIP_LOG=str(log)))
    stripped={name for name in log.read_text().splitlines() if not name.startswith('--')}
    self.assertEqual(stripped,{str(tree/name) for name in paths[1:4]})
if __name__=='__main__':unittest.main()
