# SPDX-License-Identifier: MIT
"""Compare actual data algorithms; test I/O boundaries never perform OS actions."""
import ast
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from seedsigner_port.settings_schema import SettingsConstants as C,SettingsDefinition as D
from seedsigner_port.settings_store import Settings
from seedsigner_port.settings_platform import NativeSettingsPlatform,UnsupportedSettingsAction
import test_settings_schema as original_schema_tests

class StoreTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        original_schema_tests.SchemaTest.setUpClass()
        scope=original_schema_tests.SchemaTest.reference.copy()
        path=Path(__file__).resolve().parents[2]/'dist/firmware/sources/lvgl/application/src/seedsigner/models/settings.py'
        original=next(n for n in ast.parse(path.read_text()).body if isinstance(n,ast.ClassDef) and n.name=='Settings')
        keep={'set_value','update','get_value','get_value_display_name','get_multiselect_value_display_names'}
        node=ast.ClassDef(name='ReferenceSettings',bases=[],keywords=[],body=[n for n in original.body if isinstance(n,ast.FunctionDef) and n.name in keep],decorator_list=[])
        # Full original methods, including side-effect branches. The chosen general
        # settings must never enter those branches; no fake OS module is provided.
        node.body+=ast.parse('def __init__(self):\n self._data=SettingsDefinition.get_defaults()\n self.saves=0\ndef save(self):\n self.saves+=1\ndef load_locale(self):\n raise AssertionError("Unexpected locale action in reference fixture")').body
        exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),'<original Settings methods>','exec'),scope)
        cls.reference=scope['ReferenceSettings']
    def setUp(self):
        Settings._instance=None
        self.store=Settings.get_instance()
        self.original=self.reference()
    def test_original_numeric_and_multiselect_validation(self):
        key=C.SETTING__ENCRYPTION_ITER
        for value in (0,9,10,1000,1001,True,False,10.5,'12','bad','999999999999999999999999999999'):
            self.store.set_value(key,value,save=False)
            self.original.set_value(key,value,save=False)
            self.assertEqual(self.store.get_value(key),self.original.get_value(key),value)
        for item in (self.store,self.original):
            with self.assertRaises(Exception):item.set_value(C.SETTING__SIG_TYPES,('ss',),save=False)
    def test_original_bulk_data_semantics_and_getters(self):
        fixed=set(NativeSettingsPlatform().defaults())
        for values in ({C.SETTING__NETWORK:'T',C.SETTING__SIG_TYPES:'ss,ms'}, {C.SETTING__SIG_TYPES:[['ss','Single']]}, {C.SETTING__NETWORK:'not-a-network'}, {C.SETTING__SIG_TYPES:[],C.SETTING__ENCRYPTION_ITER:0}):
            self.store.update(copy.deepcopy(values),persist=False,validate=True)
            self.original.update(copy.deepcopy(values),persist=False,validate=True)
            self.assertEqual({k:v for k,v in self.store._data.items() if k not in fixed},{k:v for k,v in self.original._data.items() if k not in fixed})
        self.assertEqual(self.store.get_value_display_name(C.SETTING__NETWORK),self.original.get_value_display_name(C.SETTING__NETWORK))
        self.assertEqual(self.store.get_multiselect_value_display_names(C.SETTING__SIG_TYPES),self.original.get_multiselect_value_display_names(C.SETTING__SIG_TYPES))
    def test_platform_defaults_and_unsupported_actions_are_explicit(self):
        with self.assertRaises(Exception):Settings()
        self.assertIs(Settings.get_instance(),self.store)
        self.assertEqual(self.store.get_value(C.SETTING__SMARTCARD_INTERFACES),[])
        self.assertEqual(self.store.get_value(C.SETTING__CAMERA_ROTATION),270)
        self.assertFalse(self.store.is_seedsigner_os())
        self.assertEqual(self.store.get_platform_default_hardware_config(),'mini-pcb240')
        for key,value in [(C.SETTING__PERSISTENT_SETTINGS,'E'),(C.SETTING__SMARTCARD_INTERFACES,['usb']),(C.SETTING__DISPLAY_CONFIGURATION,'st7735_128x128'),(C.SETTING__LOCALE,'es')]:
            before=copy.deepcopy(self.store._data)
            with self.assertRaises(UnsupportedSettingsAction):self.store.update({C.SETTING__NETWORK:'T',key:value})
            self.assertEqual(self.store._data,before)
        self.store.update({C.SETTING__NETWORK:'T'})
        self.store.save();self.store.flush_save()
        self.assertEqual(self.store.get_value(C.SETTING__PERSISTENT_SETTINGS),'D')
        self.assertEqual(self.store.get_value(C.SETTING__SMARTCARD_INTERFACES),[])
        with self.assertRaises(UnsupportedSettingsAction):self.store.get_default_settings_filename()
        del self.store._data[C.SETTING__SMARTCARD_INTERFACES]
        self.assertEqual(self.store.get_value(C.SETTING__SMARTCARD_INTERFACES,True),[])
    def test_instances_have_independent_initial_lists(self):
        values=self.store.get_value(C.SETTING__SIG_TYPES)
        Settings._instance=None
        another=Settings.get_instance()
        values.append('public-copy-test')
        self.assertNotIn('public-copy-test',another.get_value(C.SETTING__SIG_TYPES))
        self.assertNotIn('public-copy-test',D.get_defaults()[C.SETTING__SIG_TYPES])
