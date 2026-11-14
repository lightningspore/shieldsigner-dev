# SPDX-License-Identifier: MIT
"""Differential check against the existing reviewed Linux screen adapter."""
import ast
from dataclasses import dataclass,fields,is_dataclass,MISSING
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from seedsigner_port import screen_contracts as port
from seedsigner_port.screen_defaults import DEFAULTS
root=Path(__file__).resolve().parents[2]
class ContractsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app=root/'dist/firmware/sources/lvgl/application/src/seedsigner'
        if not app.is_dir():raise unittest.SkipTest('Pinned source cache required for differential check')
        reviewed=set().union(*(set(v) for v in DEFAULTS.values()))
        constants=next(n for n in ast.parse((app/'gui/components.py').read_text()).body if isinstance(n,ast.ClassDef) and n.name=='GUIConstants')
        accent=next(ast.literal_eval(n.value) for n in constants.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='ACCENT_COLOR' for t in n.targets))
        scope={'dataclass':dataclass,'BaseScreen':object,'GUIConstants':type('GUIConstants',(),{'ACCENT_COLOR':accent}), 'fields':fields,'is_dataclass':is_dataclass,'MISSING':MISSING,'_':lambda x:'T:'+x,'BASIC':port.BASIC,'SUPPORTED':set(port.BASIC),'UnmigratedScreen':NotImplementedError,'KEYBOARDS':set(),'STATUS':{}}
        for name in ('CALIBRATION_SCREENS','TEXTQR_SCREENS','FINAL_WORD_SCREENS','EXPLORER_SCREENS','DESCRIPTOR_SCREENS','MESSAGE_SCREENS','ENCRYPTED_SCREENS','TRANSCRIPTION_SCREENS','PSBT_SCREENS'):scope[name]=set()
        classes={n.name:n for n in ast.parse((app/'gui/screens/screen.py').read_text()).body if isinstance(n,ast.ClassDef)}
        for name in ('BaseTopNavScreen','ButtonListScreen','LargeButtonScreen','MainMenuScreen'):
            node=classes[name]
            node.body=[n for n in node.body if isinstance(n,ast.AnnAssign) and n.target.id in reviewed]
            for n in node.body:n.annotation=ast.Constant('reviewed field')
            node.decorator_list=[ast.Name(id='dataclass',ctx=ast.Load())]
            exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),'<original fields>','exec'),scope)
        funcs=ast.parse((root/'firmware/lvgl-app/python/contracts.py').read_text())
        selected=[n for n in funcs.body if isinstance(n,ast.FunctionDef) and n.name in ('arguments','color','button','configuration','result')]
        exec(compile(ast.Module(body=selected,type_ignores=[]),'<original Linux contracts>','exec'),scope)
        cls.reference=scope
    def test_original_defaults_and_configs(self):
        cases=[{}, {'title':'Quoted "é"','selected_button':1,'is_bottom_list':True,'scroll_y_initial_offset':0}, {'top_nav_icon_name':'x','top_nav_icon_color':'#abc','scroll_y_initial_offset':19}]
        for name in port.BASIC:
            screen=self.reference[name]
            expected={f.name:f.default for f in fields(screen)}
            self.assertEqual(DEFAULTS[name],expected)
            count=4 if name=='MainMenuScreen' else 2
            for args in cases:
                args=dict(args,button_data=['A','B','C','D'][:count])
                self.assertEqual(port.configuration(name,args,self.reference['_']),self.reference['configuration'](screen,args))
    def test_button_objects_and_opt_out(self):
        class ButtonOption:
            button_label='Label';icon_name='icon';right_icon_name='right';icon_color='red';button_label_color='#abc'
        class ButtonOptionWithoutTranslation(ButtonOption):pass
        args={'button_data':[ButtonOption(),ButtonOptionWithoutTranslation()]}
        self.assertEqual(port.configuration('ButtonListScreen',args,self.reference['_']),self.reference['configuration'](self.reference['ButtonListScreen'],args))
    def test_result_bounds_and_rejected_contracts(self):
        for value in (0,1,1000,1001):
            self.assertEqual(port.result((1,value,''),2),self.reference['result']({'event':'button_selected','index':value},2))
        for value in (-1,2,True,'0'):
            with self.assertRaises(ValueError):port.result((1,value,''),2)
        with self.assertRaises(port.UnmigratedScreen):port.configuration('SeedFinalizeScreen',{})
        with self.assertRaises(port.UnmigratedScreen):port.configuration('ButtonListScreen',{'Button_cls':object})
        with self.assertRaises(port.UnmigratedScreen):port.configuration('LargeButtonScreen',{'long_press_key':'KEY3','button_data':['A','B']})
        with self.assertRaises(ValueError):port.configuration('MainMenuScreen',{'button_data':['one']})
        with self.assertRaises(ValueError):port.configuration('ButtonListScreen',{'button_data':['hidden\0suffix']})
