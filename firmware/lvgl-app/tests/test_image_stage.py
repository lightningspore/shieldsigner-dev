import ast,json,os,shlex,subprocess,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from image_stage import selector,HERE
class ImageSelectorTests(unittest.TestCase):
 def exercise(self,default='pil',override=None,rollback=False,fail=False):
  with tempfile.TemporaryDirectory(prefix='public image selector ') as tmp:
   root=Path(tmp);marker=root/'setup';flag=root/'rollback'
   for name in ('pil','lvgl'):
    path=root/name;path.write_text('#!/bin/sh\nprintf '+shlex.quote(name)+'\nprintf "<%s>" "$@"\n'+('exit 17\n' if fail and name=='lvgl' else ''))
    path.chmod(0o755)
   script=root/'selector';script.write_text(selector('printf setup > '+shlex.quote(str(marker)),default,pil=root/'pil',lvgl=root/'lvgl',rollback=flag))
   if rollback:flag.touch()
   environment=dict(os.environ);environment.pop('SHIELDSIGNER_FRONTEND_OVERRIDE',None)
   if override is not None:environment['SHIELDSIGNER_FRONTEND_OVERRIDE']=override
   args=['public argument with spaces','$literal']
   result=subprocess.run(['sh',str(script),*args],env=environment,capture_output=True,text=True)
   return result,marker.exists()
 def test_draft_defaults_to_existing_frontend_without_new_setup(self):
  result,setup=self.exercise();self.assertEqual(result.stdout,'pil<public argument with spaces><$literal>');self.assertFalse(setup);self.assertEqual(result.returncode,0)
 def test_lvgl_runs_reviewed_setup_and_preserves_arguments(self):
  result,setup=self.exercise(override='lvgl');self.assertTrue(setup);self.assertEqual(result.stdout,'lvgl<public argument with spaces><$literal>');self.assertEqual(result.returncode,0)
 def test_persistent_rollback_has_priority_over_lvgl_default_and_override(self):
  result,setup=self.exercise(default='lvgl',override='lvgl',rollback=True);self.assertTrue(result.stdout.startswith('pil<'));self.assertFalse(setup)
 def test_failed_lvgl_is_not_masked_by_second_frontend(self):
  result,setup=self.exercise(override='lvgl',fail=True);self.assertEqual(result.returncode,17);self.assertTrue(result.stdout.startswith('lvgl<'));self.assertNotIn('pil',result.stdout)
 def test_invalid_selection_does_not_start_either_frontend(self):
  result,setup=self.exercise(override='invalid');self.assertEqual(result.returncode,64);self.assertEqual(result.stdout,'');self.assertFalse(setup)

class OriginalVersionFileTests(unittest.TestCase):
 def test_original_readers_accept_draft_identity(self):
  import logging,traceback
  source=HERE.parents[1]/'dist/firmware/sources/lvgl/application/src/seedsigner/helpers/version.py'
  tree=ast.parse(source.read_text());cls=next(node for node in tree.body if isinstance(node,ast.ClassDef) and node.name=='VersionUtils')
  methods={'_get_version_file_path','_read_version_file','_get_version_name_from_version_file','_get_version_fork_from_version_file','_get_short_commit_hash_from_version_file','_get_version_timestamp_from_version_file'}
  cls.body=[node for node in cls.body if isinstance(node,ast.FunctionDef) and node.name in methods or isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id.startswith('VERSIONFILE') for t in node.targets)]
  self.assertEqual(sum(isinstance(n,ast.FunctionDef) for n in cls.body),len(methods))
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)/'seedsigner';(root/'helpers').mkdir(parents=True)
   expected=dict(name='lvgl-dev.publicfixture',fork='lightningspore',short_commit_hash='1234567-dirty',timestamp='2026-10-30T00:00:00+00:00')
   (root/'version.json').write_text(json.dumps(expected))
   namespace=dict(os=os,json=json,logger=logging.getLogger('public-version-test'),traceback=traceback,__file__=str(root/'helpers/version.py'))
   exec(compile(ast.Module(body=[cls],type_ignores=[]),str(source),'exec'),namespace)
   reader=namespace['VersionUtils']
   for key in ('name','fork','short_commit_hash','timestamp'):
    method={'name':'_get_version_name_from_version_file','fork':'_get_version_fork_from_version_file','short_commit_hash':'_get_short_commit_hash_from_version_file','timestamp':'_get_version_timestamp_from_version_file'}[key]
    self.assertEqual(getattr(reader,method)(),expected[key])
