"""Reject inconsistent or tampered frontend selection, preserving legacy bundles."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('frontend_overlay',ROOT/'scripts/camera-image-overlay.py')
overlay=importlib.util.module_from_spec(spec);spec.loader.exec_module(overlay)

class FrontendTests(unittest.TestCase):
    def test_native_requires_extension_and_unknown_values_fail(self):
        for data in [{'frontendBackend':'rust'},{'frontendBackend':'rust','lcdBackend':'python'},{'frontendBackend':'unknown'}]:
            with self.assertRaises(ValueError):overlay.frontend_environment(data)
        self.assertEqual(overlay.frontend_environment({}),'')
        self.assertEqual(overlay.frontend_environment({'frontendBackend':'rust','lcdBackend':'rust'}),'export SHIELDSIGNER_FRONTEND_BACKEND=rust\n')

    def test_exact_launcher_and_receipt_selection(self):
        for backend in ['python','rust']:
            with tempfile.TemporaryDirectory() as directory:
                root=Path(directory);launcher=root/'usr/bin/shieldsigner-launch';launcher.parent.mkdir(parents=True)
                data={'frontendBackend':backend,'lcdBackend':'rust'};record={'frontendBackend':backend}
                expected=overlay.frontend_environment(data)
                launcher.write_text('#!/bin/sh\nset -eu\n'+expected+'exec python3 app.py\n')
                overlay.verify_frontend(root,data,record)
                launcher.write_text('#!/bin/sh\n'+expected+expected)
                with self.assertRaises(ValueError):overlay.verify_frontend(root,data,record)
                launcher.write_text('#!/bin/sh\n')
                with self.assertRaises(ValueError):overlay.verify_frontend(root,data,record)
                launcher.write_text(expected)
                with self.assertRaises(ValueError):overlay.verify_frontend(root,data,{'frontendBackend':'foreign'})

    def test_legacy_manifest_remains_python_without_new_export(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);launcher=root/'usr/bin/shieldsigner-launch';launcher.parent.mkdir(parents=True);launcher.write_text('#!/bin/sh\n')
            overlay.verify_frontend(root,{},{} )
            launcher.write_text('export SHIELDSIGNER_FRONTEND_BACKEND=rust\n')
            with self.assertRaises(ValueError):overlay.verify_frontend(root,{},{} )

if __name__=='__main__':unittest.main()
