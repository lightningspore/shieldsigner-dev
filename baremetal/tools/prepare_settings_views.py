# SPDX-License-Identifier: MIT
"""Original settings View bodies with reviewed native screen/scroll boundaries."""
import ast,hashlib,json,subprocess
from pathlib import Path
from view_source_port import LazyPort
root=Path(__file__).resolve().parents[1];repo=root.parent
source=repo/'dist/firmware/sources/lvgl/application';lock=json.loads((repo/'firmware/lvgl-app/sources.lock.json').read_text())['application']
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip()==lock['commit']
path=source/'src/seedsigner/views/settings_views.py';raw=path.read_bytes()
assert raw==subprocess.check_output(['git','show',lock['commit']+':src/seedsigner/views/settings_views.py'],cwd=source)
tree=ast.parse(raw);classes={n.name:n for n in tree.body if isinstance(n,ast.ClassDef)}
bindings={'Destination':('seedsigner_port.navigation','Destination'),'ButtonListScreen':('seedsigner_port.settings_screens','SettingsButtonListScreen'),'settings_screens':('seedsigner_port.settings_screens',None)}
port=LazyPort(tree,'seedsigner.views.settings_views',classes=classes,bindings=bindings)
nodes=[]
for n in tree.body:
    if not isinstance(n,ast.ClassDef):continue
    if n.name=='SettingsMenuView':
        # Read actual LVGL scroll position captured by the menu facade instead
        # of fabricating the original PIL button-widget list.
        hits=[x for x in ast.walk(n) if isinstance(x,ast.Assign) and ast.unparse(x.value)=='self.screen.buttons[0].scroll_y']
        assert len(hits)==1;hits[0].value=ast.parse('self.screen.scroll_y',mode='eval').body
    n=port.visit(n)
    nodes.append(ast.FunctionDef(name='_make_'+n.name,args=ast.arguments(posonlyargs=[],args=[],kwonlyargs=[],kw_defaults=[],defaults=[]),body=[n,ast.Return(ast.Name(n.name,ast.Load()))],decorator_list=[]))
supported=['SettingsMenuView','LoadBackupFilesSettingsView','LocaleSelectionView','SettingsEntryUpdateSelectionView','SettingsSelectionRequiredWarningView']
header='# Copyright2021 SeedSigner; MIT, see ../LICENSE.SeedSigner\n# Generated original settings Views; unported OS/hardware utilities stay unavailable.\nfrom seedsigner_port.decode_platform import dependency as _dependency,FeatureUnavailable\n'
footer='\n_FACTORIES={'+','.join(repr(name)+':_make_'+name for name in classes)+'}\n_SUPPORTED='+repr(tuple(supported))+'''\n_CACHE={}
def _resolve(name):
    if name not in _FACTORIES:raise AttributeError(name)
    if name not in _SUPPORTED:raise FeatureUnavailable('Native settings feature unavailable: '+name)
    if name not in _CACHE:_CACHE[name]=_FACTORIES[name]()
    return _CACHE[name]
def __getattr__(name):return _resolve(name)
'''
out=root/'app/seedsigner_port/view_settings.py';out.write_text(header+ast.unparse(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])))+'\n'+footer)
(root/'app/settings-views-provenance.json').write_text(json.dumps({'application':lock,'sourceSha256':hashlib.sha256(raw).hexdigest(),'outputSha256':hashlib.sha256(out.read_bytes()).hexdigest(),'classes':list(classes),'supported':supported,'changes':['Original menu/selection/multiselect-required business logic retained.','PIL button scroll metadata replaced by real native scroll snapshot.','Explicit native settings list/selection facades; no OS utility stubs.'],'scope':'Host/source integration candidate; device gates pending.'},indent=2)+'\n')
print('Prepared',len(classes),'original settings classes;',len(supported),'reviewed native entry points')
