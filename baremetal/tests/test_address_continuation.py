# SPDX-License-Identifier: MIT
"""Original continuation destinations and gate navigation assumptions."""
import ast,copy,sys,types,unittest
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.append(str(root/'app'))
from seedsigner_port.navigation import Destination
from seedsigner_port.button_options import ButtonOption
class Harness:
 reply=0
 def __init__(self):pass
 def run_screen(self,*args,**kwargs):self.arguments=kwargs;return self.reply
class MainMenuView:pass
class SeedAddressVerificationView:pass
class WarningScreen:pass
class ContinuationSourceTests(unittest.TestCase):
 def setUp(self):
    names=('SeedAddressVerificationSimpleNotFoundView','SeedAddressVerificationNotFoundView')
    original=ast.parse((root.parent/'dist/firmware/sources/lvgl/application/src/seedsigner/views/seed_views.py').read_text())
    generated=ast.parse((root/'app/seedsigner_port/view_seed.py').read_text())
    self.scopes=[]
    for tree,native in ((original,False),(generated,True)):
        classes=[copy.deepcopy(n.body[0] if native else n) for n in tree.body if (isinstance(n,ast.FunctionDef) and n.name in tuple('_make_'+x for x in names)) or (not native and isinstance(n,ast.ClassDef) and n.name in names)]
        for node in classes:
            node.bases=[ast.Name('View',ast.Load())]
            for method in node.body:
                if isinstance(method,ast.FunctionDef):method.body=[x for x in method.body if not isinstance(x,(ast.Import,ast.ImportFrom))]
        scope={'View':Harness,'Seed':object,'ButtonOption':ButtonOption,'Destination':Destination,'MainMenuView':MainMenuView,'SeedAddressVerificationView':SeedAddressVerificationView,'WarningScreen':WarningScreen,'RET_CODE__BACK_BUTTON':1000,'_':lambda x:x}
        scope['gettext']=lambda x:x
        scope['_dependency']=lambda module,attr=None,scope=scope:scope[attr]
        scope['_resolve']=lambda name,scope=scope:scope[name]
        exec(compile(ast.fix_missing_locations(ast.Module(body=classes,type_ignores=[])),'source','exec'),scope)
        self.scopes.append(scope)
 def test_original_and_generated_all_continuation_choices(self):
    for name,kwargs,replies in [('SeedAddressVerificationSimpleNotFoundView',{'seed':'PUBLIC','addrs_checked':100,'next_start_index':100},(0,1,2,1000)),('SeedAddressVerificationNotFoundView',{'seed':'PUBLIC','addrs_per_path_checked':10,'next_start_index':10},(0,1,1000))]:
        for reply in replies:
            results=[]
            for scope in self.scopes:
                view=scope[name](**kwargs);view.reply=reply;d=view.run()
                results.append((d.View_cls.__name__,d.view_args))
            self.assertEqual(*results)
            if reply==0:self.assertEqual(results[0][1].get('simple_start_index',results[0][1].get('expanded_start_index')),kwargs['next_start_index'])

class GateChoiceTests(unittest.TestCase):
 def test_read_first_navigation_reaches_requested_row_without_prefocus(self):
    tree=ast.parse((root/'micropython/address_search_gate.py').read_text())
    choose=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='choose')
    for initial in (None,0,1,2):
        state={'position':initial,'scroll':0,'selected':None}
        def pulse(key):
            if key==18:
                if state['position'] is None:
                    state['scroll']+=1
                    if state['scroll']==4:state['position']=0
                else:state['position']=min(2,state['position']+1)
            elif key==17:state['position']=max(0,state['position']-1)
            elif key==10:state['selected']=state['position']
        scope={'pulse':pulse};exec(compile(ast.Module(body=[choose],type_ignores=[]),'gate','exec'),scope)
        self.assertEqual(scope['choose']({'button_list':['Next 100','Expanded Search','Cancel']},'Next 100'),0)
        self.assertEqual(state['selected'],0)
