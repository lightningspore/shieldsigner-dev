# SPDX-License-Identifier: MIT
"""Compare the complete ported schema/parser to original app classes."""
import ast
from dataclasses import dataclass
import logging
import os
from pathlib import Path
import sys
from typing import Any,List
import unittest
root=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(root/'baremetal/app'))
from seedsigner_port import settings_schema as port

class SchemaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source=root/'dist/firmware/sources/lvgl/application/src/seedsigner'
        if not source.is_dir():raise unittest.SkipTest('Pinned app source cache required')
        path=source/'models/settings_definition.py'
        scope={'dataclass':dataclass,'Any':Any,'List':List,'os':os,'pathlib':__import__('pathlib'),'USING_MOCK_GPIO':False,'__file__':str(path),'logger':logging.getLogger('reference-settings')}
        exec(compile(ast.parse((source/'helpers/l10n.py').read_text()),'<original l10n>','exec'),scope)
        scope['_mft']=scope['mark_for_translation']
        nodes=[n for n in ast.parse(path.read_text()).body if isinstance(n,ast.ClassDef) and n.name in ('SettingsConstants','SettingsEntry','SettingsDefinition')]
        exec(compile(ast.Module(body=nodes,type_ignores=[]),'<original schema>','exec'),scope)
        settings=ast.parse((source/'models/settings.py').read_text())
        invalid=next(n for n in settings.body if isinstance(n,ast.ClassDef) and n.name=='InvalidSettingsQRData')
        original=next(n for n in settings.body if isinstance(n,ast.ClassDef) and n.name=='Settings')
        parser=next(n for n in original.body if isinstance(n,ast.FunctionDef) and n.name=='parse_settingsqr')
        wrapper=ast.ClassDef(name='SettingsQR',bases=[],keywords=[],body=[parser],decorator_list=[])
        exec(compile(ast.fix_missing_locations(ast.Module(body=[invalid,wrapper],type_ignores=[])),'<original parser>','exec'),scope)
        cls.reference=scope
    def test_all_entries_and_defaults(self):
        expected=self.reference['SettingsDefinition'].to_dict()
        # Explicit capability difference: only English translation assets frozen.
        for e in expected['settings_entries']:
            if e['attr_name']==port.SettingsConstants.SETTING__LOCALE:e['selection_options']=[{'display_name':'English','value':'en'}]
        self.assertEqual(port.SettingsDefinition.to_dict(),expected)
        for abbreviated in (False,True):
            for hidden in (False,True):
                self.assertEqual(port.SettingsDefinition.get_defaults(abbreviated,hidden),self.reference['SettingsDefinition'].get_defaults(abbreviated,hidden))
        self.assertEqual(len(port.SettingsDefinition.settings_entries),60)
    def test_entry_lookup_bounds_copy_and_comparison(self):
        for a,b in zip(port.SettingsDefinition.settings_entries,self.reference['SettingsDefinition'].settings_entries):
            self.assertEqual((a.min_value,a.max_value),(b.min_value,b.max_value))
            self.assertEqual(repr(a),repr(b))
            self.assertEqual(port.SettingsDefinition.get_settings_entry_by_abbreviated_name(a.abbreviated_name),a)
            if a.selection_options:
                for n in range(len(a.selection_options)):
                    self.assertEqual(a.get_selection_option_value(n),b.get_selection_option_value(n))
                    value=a.get_selection_option_value(n)
                    self.assertEqual(a.get_selection_option_display_name_by_value(value),b.get_selection_option_display_name_by_value(value))
        values=port.SettingsDefinition.get_defaults()
        name=next(k for k,v in values.items() if isinstance(v,list))
        original=port.SettingsDefinition.get_defaults()[name]
        values[name].append('test-copy')
        self.assertEqual(port.SettingsDefinition.get_defaults()[name],original)
        self.assertIs(port.SettingsEntry.__eq__(port.SettingsDefinition.settings_entries[0],object()),NotImplemented)
    def test_original_settingsqr_parity(self):
        cases=['settings::v1 name=Public_Test network=T','settings::v1 network=M sigs=ss,ms','settings::v1 qr_brightness=62','settings::v1 qr_brightness=1.5','settings::v1 pbkdf2_iterations=0','settings::v1 unknown_option=E network=R','settings::v1 persistent=E','settings::v2 network=M','invalid','settings::v1 network=','settings::v1 network=invalid','settings::v1']
        for data in cases:
            def outcome(cls,data):
                try:return ('ok',cls.parse_settingsqr(data))
                except Exception as error:return ('error',type(error).__name__,str(error))
            self.assertEqual(outcome(port.SettingsQR,data),outcome(self.reference['SettingsQR'],data),data)
