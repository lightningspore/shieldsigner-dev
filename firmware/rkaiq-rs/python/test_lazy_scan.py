"""Exercise lazy class identity, branch metadata, and strict import-hook guards."""
import ast
import hashlib
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
from shieldsigner_integration import lazy_scan_source, install_lazy_scan_views

FIXTURE = '''from seedsigner.views.seed_views import SeedSlip39MoreSharesView, SeedSlip39ShareInvalidView

def more():
    return Destination(SeedSlip39MoreSharesView)

def more_again():
    return Destination(SeedSlip39MoreSharesView)

def invalid(which):
    if which:
        if True:
            if True:
                return Destination(
                    SeedSlip39ShareInvalidView,
                    view_args={"length": 20, "retry_scan": True}, skip_current_view=True)
    else:
        if True:
            return Destination(
                SeedSlip39ShareInvalidView,
                view_args={"length": 33, "retry_scan": True}, skip_current_view=True)
'''


class LazyScanTests(unittest.TestCase):
    def test_original_classes_loaded_only_for_destination_branches(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root)/'seedsigner/views/scan_views.py'
            path.parent.mkdir(parents=True); path.write_text(FIXTURE)
            with patch('shieldsigner_integration.SCAN_VIEWS_SOURCE_SHA256', hashlib.sha256(path.read_bytes()).hexdigest()):
                _, original, source = lazy_scan_source(root)
            more, invalid = type('More', (), {}), type('Invalid', (), {})
            optional = types.ModuleType('seedsigner.views.seed_views')
            optional.SeedSlip39MoreSharesView, optional.SeedSlip39ShareInvalidView = more, invalid
            def destination(cls, **kwargs): return cls, kwargs
            namespace = {'Destination': destination}
            real_import = __import__('importlib').import_module
            calls = []
            def import_module(name):
                calls.append(name)
                return optional if name == optional.__name__ else real_import(name)
            with patch('importlib.import_module', side_effect=import_module):
                exec(compile(source, str(path), 'exec'), namespace)
                self.assertFalse(calls)  # executing module itself never imports seed_views
                self.assertIs(namespace['more']()[0], more)
                self.assertIs(namespace['more_again']()[0], more)
                for branch, length in [(True,20), (False,33)]:
                    cls, kwargs = namespace['invalid'](branch)
                    self.assertIs(cls, invalid)
                    self.assertEqual(kwargs, {'view_args': {'length': length, 'retry_scan': True}, 'skip_current_view': True})
            self.assertEqual(calls, [optional.__name__]*4)
            self.assertEqual(path.read_text(), original)
            self.assertIn('from seedsigner.views.seed_views import', original)

    def test_guarded_hook_is_idempotent_refuses_late_import_and_foreign_root(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root)/'seedsigner/views/scan_views.py'
            path.parent.mkdir(parents=True); path.write_text(FIXTURE)
            package = types.SimpleNamespace(__path__=[str(path.parent)])
            before = list(sys.meta_path)
            try:
                with patch('shieldsigner_integration.SCAN_VIEWS_SOURCE_SHA256',hashlib.sha256(path.read_bytes()).hexdigest()), patch('shieldsigner_integration.importlib.import_module',return_value=package):
                    first = install_lazy_scan_views(root)
                    self.assertIs(install_lazy_scan_views(root),first)
                    finder = sys.meta_path[0]
                    self.assertIsNone(finder.find_spec('another.module'))
                    self.assertEqual(finder.find_spec('seedsigner.views.scan_views').origin,str(path.resolve()))
                    late = types.ModuleType('seedsigner.views.scan_views')
                    with patch.dict(sys.modules, {late.__name__:late}):
                        with self.assertRaisesRegex(RuntimeError,'before scan_views'):install_lazy_scan_views(root)
                    path.write_text(FIXTURE+'# changed\n')
                    with self.assertRaises(ValueError): finder.exec_module(types.ModuleType('test'))
            finally: sys.meta_path[:] = before

    def test_unknown_source_rejected_without_hook(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root)/'seedsigner/views/scan_views.py'
            path.parent.mkdir(parents=True); path.write_text(FIXTURE)
            before = list(sys.meta_path)
            with self.assertRaises(ValueError):install_lazy_scan_views(root)
            self.assertEqual(sys.meta_path,before)

    def test_actual_pinned_source_has_four_lazy_routes_and_no_eager_seed_views(self):
        root = Path(__file__).resolve().parents[3]/'dist/os/camera-review/pinned-app-src'
        if not root.exists():self.skipTest('Pinned public app checkout not staged')
        _, original, source = lazy_scan_source(root)
        tree = ast.parse(source)
        self.assertFalse(any(isinstance(n,ast.ImportFrom) and n.module=='seedsigner.views.seed_views' for n in tree.body))
        calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='_shieldsigner_slip39_view']
        self.assertEqual(len(calls),4)
        self.assertEqual([n.args[0].value for n in calls].count('SeedSlip39MoreSharesView'),2)
        compile(source,'actual-pinned-scan','exec')
        self.assertIn('from seedsigner.views.seed_views import',original)

if __name__=='__main__':unittest.main()
