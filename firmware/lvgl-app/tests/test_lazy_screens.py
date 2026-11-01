import hashlib,importlib,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from screen_bridge import install_modules

class LazyScreenTests(unittest.TestCase):
    def test_deferred_import_identity_fields_and_restoration(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'lvgl_public_screen_fixture.py'
            path.write_text('from dataclasses import dataclass\n@dataclass\nclass PublicScreen:\n value: str=""\n def __post_init__(self): raise AssertionError("legacy rendering")\n def display(self): return "legacy"\n')
            name=path.stem;sys.path.insert(0,directory)
            backend=SimpleNamespace(last_scroll_y=0,run=lambda cls,args:args['value'])
            before=list(sys.meta_path)
            restore=install_modules(backend,{'PublicScreen'},{name:(path,hashlib.sha256(path.read_bytes()).hexdigest())})
            try:
                self.assertNotIn(name,sys.modules)
                module=importlib.import_module(name);cls=module.PublicScreen
                self.assertIs(importlib.import_module(name).PublicScreen,cls)
                self.assertEqual(cls('public fixture').display(),'public fixture')
            finally:
                restore();sys.path.remove(directory);sys.modules.pop(name,None)
            self.assertEqual(sys.meta_path,before)
            self.assertEqual(cls.display(None),'legacy')
            with self.assertRaisesRegex(AssertionError,'legacy'):cls()

    def test_changed_source_rejected_before_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'lvgl_changed_screen_fixture.py';path.write_text('raise AssertionError("executed")\n')
            name=path.stem;digest=hashlib.sha256(path.read_bytes()).hexdigest();sys.path.insert(0,directory)
            restore=install_modules(SimpleNamespace(),set(),{name:(path,digest)})
            path.write_text(path.read_text()+'# changed\n')
            try:
                with self.assertRaisesRegex(ValueError,'Changed'):importlib.import_module(name)
                self.assertNotIn(name,sys.modules)
            finally:restore();sys.path.remove(directory);sys.modules.pop(name,None)
