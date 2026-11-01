import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from slip39_lifecycle import initialize_fields
class Slip39LifecycleTests(unittest.TestCase):
 def test_parent_wipe_contract_and_original_constructor_parameters(self):
  class Parent:
   def wipe(self):self._mnemonic.clear();self._passphrase=''
  class Child(Parent):
   def __init__(self,shares,passphrase=''):
    self.shares=shares;self.passphrase=passphrase
  original=Child.__init__;Child.__init__=initialize_fields(original)
  shares=['public share'];child=Child(shares,passphrase='public extension')
  self.assertIs(child.shares,shares);self.assertEqual(child.passphrase,'public extension')
  child.wipe();child.wipe()
  self.assertEqual(child._mnemonic,[]);self.assertEqual(child._passphrase,'')
  self.assertIs(Child.__init__.__wrapped__,original)
 def test_constructor_failure_still_has_parent_fields(self):
  class Child:pass
  def broken(owner):raise RuntimeError('Public fixture failure')
  child=Child()
  with self.assertRaises(RuntimeError):initialize_fields(broken)(child)
  self.assertEqual(child._mnemonic,[]);self.assertEqual(child._passphrase,'')

class Slip39InstallTests(unittest.TestCase):
 def exercise(self,loaded=False,tampered=False):
  import hashlib,importlib,json,tempfile,types
  from unittest.mock import patch
  from slip39_lifecycle import install
  with tempfile.TemporaryDirectory() as root:
   models=Path(root)/'seedsigner/models';models.mkdir(parents=True)
   path=models/'seed.py';path.write_text('class Slip39Seed:\n def __init__(self, shares):self.shares=shares\n')
   manifest=Path(root)/'guards.json';manifest.write_text(json.dumps({'models/seed.py':hashlib.sha256(path.read_bytes()).hexdigest()}))
   packages={name:types.ModuleType(name) for name in ('seedsigner','seedsigner.models')}
   packages['seedsigner'].__path__=[str(models.parent)];packages['seedsigner.models'].__path__=[str(models)]
   with patch.dict(sys.modules,packages):
    sys.modules.pop('seedsigner.models.seed',None)
    if loaded:module=importlib.import_module('seedsigner.models.seed');cls=module.Slip39Seed;original=cls.__init__
    if tampered:
     path.write_text(path.read_text()+'# Changed after pinning\n')
     with self.assertRaisesRegex(ValueError,'Unreviewed'):
      restore=install(root,manifest)
      try:importlib.import_module('seedsigner.models.seed')
      finally:restore()
     return
    restore=install(root,manifest)
    try:
     if not loaded:
      self.assertNotIn('seedsigner.models.seed',sys.modules)
      module=importlib.import_module('seedsigner.models.seed');cls=module.Slip39Seed;original=cls.__init__.__wrapped__
     self.assertIs(module.Slip39Seed,cls)
     seed=cls(['public']);self.assertEqual(seed._mnemonic,[]);self.assertEqual(seed._passphrase,'')
    finally:restore()
    self.assertIs(cls.__init__,original)
 def test_lazy_import_and_restore(self):self.exercise()
 def test_already_loaded_class_identity_and_restore(self):self.exercise(loaded=True)
 def test_changed_lazy_source_rejected(self):self.exercise(tampered=True)
 def test_changed_loaded_source_rejected(self):self.exercise(loaded=True,tampered=True)
