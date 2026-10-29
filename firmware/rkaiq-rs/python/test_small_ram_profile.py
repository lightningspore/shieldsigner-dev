"""Strict controller profile and mandatory-storage lifecycle checks."""
import hashlib
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch
from shieldsigner_integration import install_small_ram_profile


class SmallRamProfileTests(unittest.TestCase):
    def fixture(self, directory):
        path = Path(directory) / 'seedsigner/controller.py'
        path.parent.mkdir()
        path.write_text('# reviewed controller fixture\n')
        storage = types.SimpleNamespace(_storage=None, _storage2=None)
        controller = type('Controller', (), {'_instance': None,
                          'get_instance': staticmethod(lambda: storage)})
        calls = []
        class Background:
            def run(self):
                raise AssertionError('Optional eager imports must not execute')
        module = types.SimpleNamespace(__file__=str(path), Controller=controller,
            BackgroundImportThread=Background,
            SeedStorage=lambda: calls.append('seed') or object(),
            EncryptedQRStorage=lambda: calls.append('encrypted') or object())
        return path, module, storage, calls

    def test_preserves_both_stores_order_and_idempotence_without_optional_imports(self):
        with tempfile.TemporaryDirectory() as root:
            path, module, storage, calls = self.fixture(root)
            before = path.read_bytes()
            with patch('shieldsigner_integration.SMALL_RAM_CONTROLLER_SHA256', hashlib.sha256(before).hexdigest()), patch('shieldsigner_integration.importlib.import_module', return_value=module) as imports:
                first = install_small_ram_profile(root)
                self.assertIs(install_small_ram_profile(root), first)
                self.assertFalse(calls)
                module.BackgroundImportThread().run()
                self.assertEqual(calls, ['seed', 'encrypted'])
                self.assertIsNotNone(storage._storage)
                self.assertIsNotNone(storage._storage2)
                self.assertTrue(all(call.args == ('seedsigner.controller',) for call in imports.call_args_list))
            self.assertEqual(path.read_bytes(), before)

    def test_unknown_source_fails_before_import(self):
        with tempfile.TemporaryDirectory() as root:
            self.fixture(root)
            with patch('shieldsigner_integration.importlib.import_module') as imports:
                with self.assertRaisesRegex(ValueError, 'Unsupported controller'):
                    install_small_ram_profile(root)
                imports.assert_not_called()

    def test_refuses_late_initialization_and_foreign_controller(self):
        with tempfile.TemporaryDirectory() as root:
            path, module, _, _ = self.fixture(root)
            with patch('shieldsigner_integration.SMALL_RAM_CONTROLLER_SHA256', hashlib.sha256(path.read_bytes()).hexdigest()), patch('shieldsigner_integration.importlib.import_module', return_value=module):
                module.Controller._instance = object()
                with self.assertRaisesRegex(RuntimeError, 'before Controller'):
                    install_small_ram_profile(root)
                module.Controller._instance = None
                module.__file__ = '/foreign/controller.py'
                with self.assertRaisesRegex(RuntimeError, 'does not match'):
                    install_small_ram_profile(root)


if __name__ == '__main__':
    unittest.main()
