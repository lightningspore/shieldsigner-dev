import hashlib,os,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
import startup_policy
class StartupPolicyTests(unittest.TestCase):
    def test_unreviewed_shared_dependency_never_imported(self):
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory)/'shieldsigner_integration.py').write_text('raise RuntimeError("must not execute")')
            with patch.dict(os.environ,{'SHIELDSIGNER_SMALL_RAM':'0'}),patch('startup_policy.importlib.import_module') as importer:
                with self.assertRaises(ValueError):startup_policy.install('/app',directory)
                importer.assert_not_called()
                self.assertEqual(os.environ['SHIELDSIGNER_SMALL_RAM'],'0')
    def test_existing_storage_and_lazy_import_policy_are_reused(self):
        original_path=list(sys.path);calls=[]
        try:
            with tempfile.TemporaryDirectory() as directory:
                path=Path(directory)/'shieldsigner_integration.py';path.write_bytes(b'public test module')
                module=SimpleNamespace(__file__=str(path),install_small_ram_profile=lambda root:calls.append(('storage',root)) or {'mandatoryStorageInitializers':['SeedStorage','EncryptedQRStorage']},install_lazy_scan_views=lambda root:calls.append(('scan',root)) or {'featuresRemoved':False})
                with patch.dict(os.environ,{'SHIELDSIGNER_SMALL_RAM':'0'}),patch('startup_policy.INTEGRATION_SHA256',hashlib.sha256(path.read_bytes()).hexdigest()),patch('startup_policy.importlib.import_module',return_value=module):
                    info=startup_policy.install('/app',directory)
                    self.assertEqual(os.environ['SHIELDSIGNER_SMALL_RAM'],'1')
                    self.assertTrue(info['cameraSmallRamEnabled'])
                self.assertEqual(calls,[('storage','/app'),('scan','/app')])
                self.assertFalse(info['lazyScan']['featuresRemoved'])
        finally:sys.path[:]=original_path
    def test_packaging_source_matches_shared_policy_pin(self):
        source=Path(__file__).resolve().parents[2]/'rkaiq-rs/python/shieldsigner_integration.py'
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),startup_policy.INTEGRATION_SHA256)
