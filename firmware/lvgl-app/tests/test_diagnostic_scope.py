import sys,unittest
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from diagnostic_scope import attribute
class DiagnosticScopeTests(unittest.TestCase):
    def test_original_identity_restored_after_success_and_failure(self):
        original=object();replacement=object();target=SimpleNamespace(value=original)
        with attribute(target,'value',replacement):self.assertIs(target.value,replacement)
        self.assertIs(target.value,original)
        with self.assertRaises(RuntimeError):
            with attribute(target,'value',replacement):raise RuntimeError('fixture')
        self.assertIs(target.value,original)

    def test_classmethod_and_inherited_descriptor_restored(self):
        class Parent:
            @classmethod
            def value(cls):return cls.__name__
        class Child(Parent):pass
        descriptor=vars(Parent)['value']
        with attribute(Parent,'value',classmethod(lambda cls:'fixture')):self.assertEqual(Parent.value(),'fixture')
        self.assertIs(vars(Parent)['value'],descriptor)
        with attribute(Child,'value',classmethod(lambda cls:'child fixture')):self.assertEqual(Child.value(),'child fixture')
        self.assertNotIn('value',vars(Child));self.assertEqual(Child.value(),'Child')
