"""Explicit LCD selection, fail-closed behavior and pre-Controller ordering."""
import json
import subprocess
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
from shieldsigner_integration import configure_lcd_backend, ensure_app_import_root, main


class LcdSelectionTests(unittest.TestCase):
    def test_python_default_does_not_import_native_runtime(self):
        with patch('shieldsigner_integration.importlib.import_module') as imports:
            self.assertEqual(configure_lcd_backend('/opt/src','python')['lcdBackend'],'python')
            imports.assert_not_called()

    def test_rust_uses_reviewed_idempotent_installer_and_propagates_failure(self):
        info={'kind':'already-installed-reviewed-native-driver'}
        driver=types.SimpleNamespace(install=lambda root:info)
        with patch('shieldsigner_integration.importlib.import_module',return_value=driver) as imports:
            self.assertEqual(configure_lcd_backend('/opt/src','rust')['driver'],info)
            self.assertEqual(configure_lcd_backend('/opt/src','rust')['driver'],info)
            imports.assert_called_with('shieldsigner_lcd_driver')
        with patch('shieldsigner_integration.importlib.import_module',side_effect=ImportError('missing')):
            with self.assertRaisesRegex(RuntimeError,'unavailable'):configure_lcd_backend('/opt/src','rust')
        driver.install=lambda root:(_ for _ in ()).throw(ValueError('Unreviewed ST7789 source'))
        with patch('shieldsigner_integration.importlib.import_module',return_value=driver):
            with self.assertRaisesRegex(ValueError,'Unreviewed'):configure_lcd_backend('/opt/src','rust')
        with self.assertRaises(ValueError):configure_lcd_backend('/opt/src','automatic')

    def test_flag_env_and_order_precede_camera_main_controller(self):
        for environment, cli, expected in [({}, [], 'python'),
                ({'SHIELDSIGNER_LCD_BACKEND':'rust'},[], 'rust'),
                ({'SHIELDSIGNER_LCD_BACKEND':'rust'},['--lcd-backend','python'],'python')]:
            with tempfile.TemporaryDirectory() as root, patch.dict(os.environ,environment,clear=True):
                config=Path(root)/'owner.json'
                config.write_text(json.dumps({k:'/absolute/'+k for k in ('binary','plan','iq','parameters','image','statistics','output_directory')}))
                events=[]
                module=types.SimpleNamespace(__shieldsigner_camera_patch__={}, Camera=types.SimpleNamespace(_instance=None))
                def lcd(path, backend):events.append(('lcd',backend));return {}
                def camera(path):events.append(('camera',None));return module
                with patch.object(sys,'argv',['entry','--app-root',root,'--config',str(config),*cli]), patch('shieldsigner_integration.camera_source',return_value=(None,'original','patched')), patch('shieldsigner_integration.configure_lcd_backend',side_effect=lcd), patch('shieldsigner_integration.install_camera_backend',side_effect=camera), patch('shieldsigner_integration.runpy.run_path',side_effect=lambda *a,**k:events.append(('application/Controller',None))):
                    main()
                self.assertEqual(events,[('lcd',expected),('camera',None),('application/Controller',None)])


    def test_script_entry_imports_app_before_real_shim_import_in_fresh_interpreter(self):
        with tempfile.TemporaryDirectory() as directory:
            base=Path(directory); app=base/'app'; runtime=base/'runtime'; runtime.mkdir()
            package=app/'seedsigner/hardware/displays';package.mkdir(parents=True)
            for path in [app/'seedsigner', app/'seedsigner/hardware', package]:
                (path/'__init__.py').write_text('')
            (package/'ST7789.py').write_text('IMPORTED_FROM_REQUESTED_ROOT = True\n')
            (runtime/'shieldsigner_lcd_driver.py').write_text('''
import importlib
from pathlib import Path
def install(root):
    module=importlib.import_module('seedsigner.hardware.displays.ST7789')
    assert module.IMPORTED_FROM_REQUESTED_ROOT
    assert Path(module.__file__).resolve()==Path(root).resolve()/'seedsigner/hardware/displays/ST7789.py'
    return {'isolatedActualAppImport':True}
''')
            config=base/'owner.json';config.write_text(json.dumps({key:'/absolute/'+key for key in ('binary','plan','iq','parameters','image','statistics','output_directory')}))
            helper=Path(__file__).resolve().parent
            script='''
import os,sys,types
from pathlib import Path
import shieldsigner_integration as m
root=Path(os.environ['TEST_APP_ROOT']).resolve()
assert str(root) not in sys.path
assert 'seedsigner' not in sys.modules
m.camera_source=lambda root:(None,'original','patched')
def camera(root):
    assert sys.modules['seedsigner.hardware.displays.ST7789'].IMPORTED_FROM_REQUESTED_ROOT
    return types.SimpleNamespace(__shieldsigner_camera_patch__={},Camera=types.SimpleNamespace(_instance=None))
m.install_camera_backend=camera
m.runpy.run_path=lambda *args,**kwargs:None
sys.argv=['entry','--app-root',str(root),'--config',os.environ['TEST_CONFIG'],'--lcd-backend','rust']
m.main()
assert sys.path[0]==str(root)
print('ISOLATED_REAL_SHIM_APP_IMPORT_PASS')
'''
            environment=dict(os.environ,PYTHONPATH=os.pathsep.join([str(runtime),str(helper)]),TEST_APP_ROOT=str(app),TEST_CONFIG=str(config))
            environment.pop('SHIELDSIGNER_SMALL_RAM',None)
            result=subprocess.run([sys.executable,'-c',script],cwd=runtime,env=environment,text=True,capture_output=True,check=True)
            self.assertIn('ISOLATED_REAL_SHIM_APP_IMPORT_PASS',result.stdout)

    def test_foreign_loaded_package_rejected_before_native_import(self):
        foreign=types.ModuleType('seedsigner');foreign.__path__=['/foreign/app/seedsigner']
        before=list(sys.path)
        try:
            with patch.dict(sys.modules,{'seedsigner':foreign}):
                with self.assertRaisesRegex(RuntimeError,'differs from requested root'):
                    ensure_app_import_root('/opt/src')
            self.assertEqual(sys.path,before)
        finally:sys.path[:]=before

if __name__=='__main__':unittest.main()
