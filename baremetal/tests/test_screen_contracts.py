# SPDX-License-Identifier: MIT
"""Differential check against the existing reviewed Linux screen adapter."""
import ast
from dataclasses import dataclass,fields,is_dataclass,MISSING
from pathlib import Path
import sys
import unittest
sys.path.append(str(Path(__file__).resolve().parents[1]/'app'))
sys.path.append(str(Path(__file__).resolve().parents[2]/'firmware/lvgl-app/python'))
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
            if not node.body:node.body=[ast.Pass()]
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
        with self.assertRaises(ValueError):port.configuration('SeedMnemonicEntryScreen',{})
        with self.assertRaises(port.UnmigratedScreen):port.configuration('ButtonListScreen',{'Button_cls':object})
        with self.assertRaises(port.UnmigratedScreen):port.configuration('LargeButtonScreen',{'long_press_key':'KEY3','button_data':['A','B']})
        with self.assertRaises(ValueError):port.configuration('MainMenuScreen',{'button_data':['one']})
        with self.assertRaises(ValueError):port.configuration('ButtonListScreen',{'button_data':['hidden\0suffix']})

    def test_app_status_and_seed_contracts_against_original_linux_adapter(self):
        from dataclasses import field
        from seedsigner_port.gui_constants import GUIConstants,SeedSignerIconConstants
        from seedsigner_port.button_options import ButtonOption
        from seedsigner_port.app_screen_defaults import DEFAULTS as APP_DEFAULTS
        scope=self.reference.copy()
        scope.update(GUIConstants=GUIConstants,SeedSignerIconConstants=SeedSignerIconConstants,field=field,ButtonOption=ButtonOption,_mft=lambda x:x)
        scope['WarningEdgesMixin']=type('WarningEdgesMixin',(),{})
        scope['STATUS']=port.STATUS
        scope['SUPPORTED']=set(port.BASIC)|port.APP_SCREENS
        scope['TRANSCRIPTION_SCREENS']=port.TRANSCRIPTION
        # Reference functions must use this scope, rather than their earlier globals.
        functions=ast.parse((root/'firmware/lvgl-app/python/contracts.py').read_text())
        selected=[n for n in functions.body if isinstance(n,ast.FunctionDef) and n.name in ('arguments','color','button','configuration','result')]
        exec(compile(ast.Module(body=selected,type_ignores=[]),'<original app contracts>','exec'),scope)
        app=root/'dist/firmware/sources/lvgl/application/src/seedsigner/gui/screens'
        classes={n.name:n for file in ('screen.py','seed_screens.py') for n in ast.parse((app/file).read_text()).body if isinstance(n,ast.ClassDef)}
        reviewed=set().union(*(set(v) for v in APP_DEFAULTS.values()))
        # Rebuild actual field defaults including warning factory buttons.
        for name in ('BaseTopNavScreen','ButtonListScreen','LargeIconStatusScreen','WarningScreen','DireWarningScreen','ErrorScreen','SeedFinalizeScreen','SeedOptionsScreen','SeedSelectSeedScreen','SeedAddPassphraseScreen','SeedReviewPassphraseScreen','SeedMnemonicEntryScreen','SeedWordsScreen','SeedWordsBackupTestPromptScreen','SeedTranscribeSeedQRFormatScreen','SeedTranscribeSeedQRWholeQRScreen','SeedTranscribeSeedQRZoomedInScreen','SeedTranscribeSeedQRConfirmQRPromptScreen','SeedExportXpubDetailsScreen','SeedAddressVerificationScreen','SeedAddressVerificationSuccessScreen'):
            node=classes[name]
            node.body=[n for n in node.body if isinstance(n,ast.AnnAssign) and n.target.id in reviewed]
            for n in node.body:n.annotation=ast.Constant('reviewed field')
            if not node.body:node.body=[ast.Pass()]
            node.decorator_list=[ast.Name(id='dataclass',ctx=ast.Load())]
            exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),'<original app fields>','exec'),scope)
        for name in APP_DEFAULTS:
            cases=[{}, {'button_data':['Done','Cancel'],'text':'Public test','selected_button':1}]
            if name=='SeedAddressVerificationScreen':cases=[dict(c,address='bc1 PUBLIC',network='Mainnet',sig_type='Single Sig',script_type='Native Segwit',is_mainnet=True,threadsafe_counter=type('PublicCounter',(),{'cur_count':7})(),button_data=['Skip 10','Cancel']) for c in cases]
            if name=='SeedAddressVerificationSuccessScreen':cases=[dict(c,address='bc1 PUBLIC',verified_index=7,verified_index_is_change=True,derivation_path="m/84'/0'/0'",script_type_display='Native Segwit',is_non_standard=False) for c in cases]
            if name=='SeedExportXpubDetailsScreen':cases=[dict(c,fingerprint='73c5da0a',derivation_path="m/84'/0'/0'",xpub='zpub PUBLIC') for c in cases]
            if name in port.TRANSCRIPTION:cases=[dict(c,qr_data='0000',num_modules=21,is_compactqr=True,is_encryptedqr=False) for c in cases]
            if name=='SeedWordsScreen':cases=[dict(c,words=['abandon','ability','able','about'],page_index=2,num_pages=3) for c in cases]
            if name=='SeedMnemonicEntryScreen':cases=[dict(c,wordlist=['abandon','ability','able','about'],initial_letters=['a','b']) for c in cases]
            if name=='SeedAddPassphraseScreen':cases=[dict(c,passphrase='public  \0\\value',initial_keyboard='ABC') for c in cases]
            if name=='SeedReviewPassphraseScreen':cases=[dict(c,passphrase='public  \0\\value',fingerprint_without='73c5da0a',fingerprint_with='b4e3f5ed') for c in cases]
            if name in ('SeedFinalizeScreen','SeedOptionsScreen'):cases=[dict(c,fingerprint='73c5da0a') for c in cases]
            for arguments in cases:
                actual=port.configuration(name,arguments,scope['_'])
                builder,expected=scope['configuration'](scope[name],arguments)
                if name=='SeedWordsBackupTestPromptScreen':
                    # Original post-init content was not covered by the Linux
                    # adapter; keep its real prompt and disable top-nav Back.
                    expected['top_nav'].update(title=scope['_']('Verify Backup?'),show_back_button=False)
                    expected['is_bottom_list']=True
                    expected['text']=scope['_']('Optionally verify that your mnemonic backup is correct.')
                if name=='SeedOptionsScreen':
                    # Original SeedOptionsScreen.__post_init__ sets these; the
                    # Linux adapter omitted them. Match the actual source screen.
                    expected['top_nav'].update(icon=SeedSignerIconConstants.FINGERPRINT,icon_color=GUIConstants.INFO_COLOR)
                self.assertEqual(actual,(builder,expected),name)

    def test_mnemonic_text_result_and_back(self):
        self.assertEqual(port.result((2,0,'abandon'),0,'SeedMnemonicEntryScreen'),'abandon')
        self.assertEqual(port.result((1,1000,''),0,'SeedMnemonicEntryScreen'),1000)
        self.assertEqual(port.result(1000,0,'SeedMnemonicEntryScreen'),1000)
        for event in ((2,1,'abandon'),(2,0,''),(2,0,'ab\0c'),(2,0,3),(3,0,'abandon')):
            with self.assertRaises(ValueError):port.result(event,0,'SeedMnemonicEntryScreen')

    def test_xpub_review_rejects_missing_or_hidden_fields(self):
        valid={'fingerprint':'73c5da0a','derivation_path':"m/84'/0'/0'",'xpub':'zpub PUBLIC'}
        for key in valid:
            for bad in ('',None,'hidden\0suffix'):
                values=dict(valid);values[key]=bad
                with self.assertRaises(ValueError):port.configuration('SeedExportXpubDetailsScreen',values)
