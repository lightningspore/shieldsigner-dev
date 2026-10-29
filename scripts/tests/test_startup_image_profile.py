"""Exact upstream app-startup selection, independent of USB/memory/GPIO."""
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('startup_overlay',ROOT/'scripts/camera-image-overlay.py')
overlay=importlib.util.module_from_spec(spec);spec.loader.exec_module(overlay)

class StartupTests(unittest.TestCase):
    def test_defaults_and_explicit_choices(self):
        self.assertEqual(overlay.app_startup({'imageVariant':'dev'}),'held')
        self.assertEqual(overlay.app_startup({'imageVariant':'production'}),'automatic')
        self.assertEqual(overlay.app_startup({'imageVariant':'dev','appStartup':'automatic'}),'automatic')
        self.assertEqual(overlay.app_startup({'imageVariant':'production','appStartup':'held'}),'held')
        with self.assertRaises(ValueError):overlay.app_startup({'appStartup':'unknown'})

    def test_exact_pinned_automatic_template_and_hold_are_distinct(self):
        self.assertEqual(hashlib.sha256(overlay.AUTOMATIC_APP_INIT).hexdigest(),overlay.AUTOMATIC_APP_INIT_SHA256)
        for variant in ['dev','production']:
            for policy in ['automatic','held']:
                with tempfile.TemporaryDirectory() as directory:
                    root=Path(directory);path=root/'etc/init.d/S99seedsigner'
                    path.parent.mkdir(parents=True);path.write_bytes(overlay.AUTOMATIC_APP_INIT)
                    data={'imageVariant':variant,'appStartup':policy}
                    overlay.install_app_startup(root,data);overlay.verify_app_startup(root,data)
                    self.assertEqual(path.read_bytes(),overlay.AUTOMATIC_APP_INIT if policy=='automatic' else overlay.DEV_APP_HOLD_INIT.encode())
                    path.chmod(0o644)
                    with self.assertRaises(ValueError):overlay.verify_app_startup(root,data)
                    path.chmod(0o755);path.write_bytes(path.read_bytes()+b'\n')
                    with self.assertRaises(ValueError):overlay.verify_app_startup(root,data)

    def test_foreign_startup_rejected_before_mutation(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);path=root/'etc/init.d/S99seedsigner'
            path.parent.mkdir(parents=True);path.write_bytes(b'foreign startup')
            with self.assertRaises(ValueError):overlay.install_app_startup(root,{'appStartup':'automatic'})
            self.assertEqual(path.read_bytes(),b'foreign startup')

if __name__=='__main__':unittest.main()
