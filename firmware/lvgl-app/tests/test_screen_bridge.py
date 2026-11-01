import sys
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from screen_bridge import install
class ScreenBridgeTests(unittest.TestCase):
    def test_direct_construction_keeps_fields_and_class_without_original_rendering(self):
        calls=[]
        @dataclass
        class Screen:
            initial_value:str=''
            def __post_init__(self):calls.append('PIL constructor')
            def display(self):return 'PIL display'
        class Backend:
            last_scroll_y=123
            def run(self,cls,args):
                self.arguments=args;return 'native result'
        backend=Backend();original_post=Screen.__post_init__;original_display=Screen.display
        uninstall=install(backend,[Screen])
        try:
            screen=Screen(initial_value='42')
            self.assertIs(type(screen),Screen);self.assertEqual(calls,[])
            self.assertEqual(screen.display(),'native result')
            self.assertEqual(backend.arguments,dict(initial_value='42'))
            self.assertEqual(screen.buttons[0].scroll_y,123)
        finally:uninstall()
        self.assertIs(Screen.__post_init__,original_post);self.assertIs(Screen.display,original_display)
    def test_unknown_subclass_keeps_original_constructor(self):
        calls=[]
        @dataclass
        class Parent:
            def __post_init__(self):calls.append('parent')
            def display(self):return 'old'
        class Child(Parent):pass
        uninstall=install(SimpleNamespace(),[Parent])
        try:
            child=Child();self.assertEqual(calls,['parent']);self.assertEqual(child.display(),'old')
        finally:uninstall()
    def test_patched_inheritance_restores_inherited_methods(self):
        @dataclass
        class Parent:
            value:int=1
            def __post_init__(self):raise AssertionError('PIL')
            def display(self):return 'old'
        @dataclass
        class Child(Parent):pass
        class Backend:
            last_scroll_y=0
            def run(self,cls,args):return args['value']
        uninstall=install(Backend(),[Parent,Child])
        try:self.assertEqual(Child(7).display(),7)
        finally:uninstall()
        self.assertNotIn('__post_init__',Child.__dict__);self.assertNotIn('display',Child.__dict__)
if __name__=='__main__':unittest.main()
