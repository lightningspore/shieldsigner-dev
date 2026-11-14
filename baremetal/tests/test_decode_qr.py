# SPDX-License-Identifier: MIT
"""Compare the port with whole original model classes, not a replacement parser."""
import ast,base64,json,logging,re,sys,types
from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path
import unittest
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'app'))
from seedsigner_port import decode_qr as port
from seedsigner_port.decode_platform import FeatureUnavailable
from seedsigner_port.qr_type import QRType
from seedsigner_port.settings_schema import SettingsConstants
source=root.parent/'dist/firmware/sources/lvgl/application/src/seedsigner/models/decode_qr.py'
class ModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not source.exists():raise RuntimeError('Pinned app source required for model parity')
        module=types.ModuleType('_original_decode_qr_test');sys.modules[module.__name__]=module
        module.__dict__.update(dataclass=dataclass,IntEnum=IntEnum,base64=base64,json=json,re=re,QRType=QRType,SettingsConstants=SettingsConstants,logger=logging.getLogger('decode-reference'))
        tree=ast.parse(source.read_text())
        nodes=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0)]+[n for n in tree.body if isinstance(n,ast.ClassDef)]
        exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),'<whole original QR model>','exec'),module.__dict__)
        cls.reference=module
    def states(self,model,values,**kwargs):
        d=model.DecodeQR(**kwargs);results=[]
        for value in values:
            status=d.add_data(value)
            results.append((int(status),d.qr_type,d.is_complete,d.is_invalid,d.get_percent_complete(),d.is_nonUTF8))
        return d,results
    def test_text_passphrase_and_invalid_utf8(self):
        for mode,getter in [('is_text','get_text'),('is_passphrase','get_passphrase')]:
            for value in [b'public\x00text','é🙂 public'.encode(),b'',b'\xff']:
                with self.subTest(mode=mode,value=value):
                    a,x=self.states(self.reference,[value],**{mode:True});b,y=self.states(port,[value],**{mode:True})
                    self.assertEqual(x,y);self.assertEqual(getattr(a,getter)(),getattr(b,getter)())
    def test_generic_settings_and_fragment_type_change(self):
        values=[b'settings::v1 name=public lang=en']
        a,x=self.states(self.reference,values);b,y=self.states(port,values)
        self.assertEqual(x,y);self.assertEqual(a.get_settings_data(),b.get_settings_data())
        for d in (a,b):
            with self.assertRaisesRegex(Exception,'Unexpected Type Change'):d.add_data('p1of2 {')
    def test_original_animated_wallet_assembly(self):
        parts=['p2of2 "descriptor":"public fixture"}','p2of2 "descriptor":"public fixture"}','p1of2 {"label":"test",']
        a,x=self.states(self.reference,parts);b,y=self.states(port,parts)
        self.assertEqual(x,y);self.assertEqual([v[0] for v in y],[1,2,3]);self.assertEqual(b.get_wallet_descriptor(),a.get_wallet_descriptor())
    def test_unported_dependency_is_explicit(self):
        with self.assertRaises(FeatureUnavailable):port.DecodeQR().add_data('ur:bytes/abcd')
        with self.assertRaises(FeatureUnavailable):port.DecodeQR().add_data('unknown public text')
    def test_all_classes_retained(self):
        names=[n.name for n in ast.parse(source.read_text()).body if isinstance(n,ast.ClassDef)]
        self.assertEqual(len(names),27)
        for name in names:self.assertTrue(hasattr(port,name),name)
    def test_generated_original_scan_loop_parity_and_cleanup(self):
        from seedsigner_port.scan_screen import NativeScanScreen,CooperativePreview
        class Clock:
            now=0
            def time(self):self.now+=.05;return self.now
        class Input:
            def __init__(self,back=False):self.back=back
            def reset_input(self):pass
            def check_for_low(self,key):return self.back
        class Camera:
            def __init__(self):self.active=False;self.stops=0
            def start_video_stream_mode(self):self.active=True
            def read_video_stream(self):return b'frame'
            def stop_video_stream_mode(self):
                if self.active:self.active=False;self.stops+=1
        # This is a scheduling unit test only; native pixel decoding has its own
        # hardware gate. Both loops receive the same explicit model boundary.
        class Decoder:
            def __init__(self,status):self.status=status
            def add_image(self,frame):return self.status
        for status,back,expected in [(3,False,None),(5,False,None),(4,True,False)]:
            outputs=[]
            for original in (False,True):
                camera=Camera();preview=CooperativePreview(lambda frame:None)
                screen=NativeScanScreen(Decoder(status),camera=camera,preview=preview,buttons=Input(back),clock=Clock())
                if original:
                    tree=ast.parse((source.parent.parent/'gui/screens/scan_screens.py').read_text())
                    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='ScanScreen')
                    method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='_run')
                    # Bind the exact source loop's platform imports to its test
                    # equivalents; no decoder algorithm is replaced here.
                    for node in list(method.body):
                        if isinstance(node,ast.ImportFrom):method.body.remove(node)
                    scope={'DecodeQRStatus':self.reference.DecodeQRStatus,'time':screen.clock,'HardwareButtonsConstants':types.SimpleNamespace(KEY_RIGHT='KEY_RIGHT',KEY_LEFT='KEY_LEFT')}
                    exec(compile(ast.fix_missing_locations(ast.Module(body=[method],type_ignores=[])),'<original ScanScreen._run>','exec'),scope)
                    screen.threads=[preview]
                    screen._run=types.MethodType(scope['_run'],screen)
                outputs.append(screen.run());self.assertFalse(camera.active);self.assertEqual(camera.stops,1)
            self.assertEqual(outputs,[expected,expected])
    def test_invalid_animated_wallet_matches_reference(self):
        parts=['p1of2 {"label":','p2of2 }']
        a,x=self.states(self.reference,parts);b,y=self.states(port,parts)
        self.assertEqual(x,y);self.assertEqual(y[-1][0],5)
        self.assertEqual(a.get_wallet_descriptor(),b.get_wallet_descriptor())
    def test_unavailable_psbt_validation_is_not_misclassification(self):
        with self.assertRaises(FeatureUnavailable):port.DecodeQR().add_data('cHNidP8=')
