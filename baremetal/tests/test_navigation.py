# SPDX-License-Identifier: MIT
"""Compare ported navigation with the actual pinned CPython/dataclass classes."""
import ast
from dataclasses import dataclass
import importlib.util
from pathlib import Path
import unittest
from typing import Type
root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('ported_navigation',root/'app/seedsigner_port/navigation.py')
port=importlib.util.module_from_spec(spec);spec.loader.exec_module(port)
source=root.parent/'dist/firmware/sources/lvgl/application/src/seedsigner'

class ReferenceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # No app imports, settings or model execution. Extract exact original classes.
        if not source.is_dir():raise unittest.SkipTest('Pinned app cache required for differential check')
        scope={'dataclass':dataclass,'Type':Type,'View':object}
        nodes=[]
        for file,name in [('views/view.py','Destination'),('controller.py','BackStack')]:
            tree=ast.parse((source/file).read_text())
            nodes.append(next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==name))
        exec(compile(ast.Module(body=nodes,type_ignores=[]),'<original navigation>','exec'),scope)
        cls.reference=scope
    def test_constructor_equality_and_backstack(self):
        for name,cls in [('original',self.reference['Destination']),('port',port.Destination)]:
            with self.subTest(name=name):
                a=cls(None);b=cls(None,{},True,True)
                self.assertEqual(a,b);self.assertFalse(a!=b)
                self.assertEqual(a.skip_current_view,False)
                self.assertEqual(b.clear_history,True)
                self.assertNotEqual(a,object())
        original=self.reference['BackStack']([self.reference['Destination'](None)])
        actual=port.BackStack([port.Destination(None)])
        self.assertEqual(repr(actual),repr(original))
    def test_run_and_redirect_match_reference(self):
        class View:
            has_redirect=False
            def __init__(self,number=9):self.number=number
            def run(self):return self.number+1
        class Redirect(View):
            has_redirect=True
            def get_redirect(self):return 'redirect-result'
        for view in (View,Redirect):
            for cls in (self.reference['Destination'],port.Destination):
                route=cls(view,{'number':41})
                self.assertEqual(route.run(),'redirect-result' if view is Redirect else 42)
                self.assertEqual(route,cls(view,{'number':41},True,True))
                noargs=cls(view);noargs.run();self.assertEqual(noargs.view_args,{})
    def test_sensitive_repr_parity(self):
        values={'passphrase':'unit-test-secret','items':[{'PIN':'unit-test-pin','public':'visible'}],'entropy_bytes':b'unit-test-entropy'}
        expected=repr(self.reference['Destination'](None,values,clear_history=True))
        actual=repr(port.Destination(None,values,clear_history=True))
        self.assertEqual(actual,expected)
        for value in ('unit-test-secret','unit-test-pin','unit-test-entropy'):self.assertNotIn(value,actual)
        self.assertIn('visible',actual)
