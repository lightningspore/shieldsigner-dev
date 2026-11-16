# SPDX-License-Identifier: MIT
"""Freeze original View bodies behind lazy actual imports, without dummy features."""
import ast,hashlib,json,subprocess,copy
from pathlib import Path
root=Path(__file__).resolve().parents[1];repo=root.parent
source=repo/'dist/firmware/sources/lvgl/application'
lock=json.loads((repo/'firmware/lvgl-app/sources.lock.json').read_text())['application']
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip()==lock['commit']
from view_source_port import LazyPort

def dataclass_constructor(n,classes):
 def fields(n):
  out={}
  for b in n.bases:
   if isinstance(b,ast.Name) and b.id in classes:out.update(fields(classes[b.id]))
  out.update({a.target.id:a.value for a in n.body if isinstance(a,ast.AnnAssign)})
  return out
 f=fields(n)
 args=','.join(name+('='+ast.unparse(value) if value is not None else '') for name,value in f.items())
 body='def __init__(self'+(','+args if args else '')+'):\n'+''.join('    self.'+name+'='+name+'\n' for name in f)+'    self.__post_init__()\n'
 n.decorator_list=[d for d in n.decorator_list if ast.unparse(d)!='dataclass']
 n.body=[a for a in n.body if not isinstance(a,ast.AnnAssign)]+ast.parse(body).body

receipt={'application':lock,'files':{},'reviewedChanges':['SeedWordsView rounds page count up so partial final pages are displayed.','Seed Views random import uses non-secret native quiz_random ordering.','Address verification workers use foreground Counter/Worker, yielding after each original address pair and expanded path precomputation; original matching/routing retained.','RestartView/RebootToLoaderView show the original screen then call native machine.reset (mode 1 sets BOOT_BROM_DOWNLOAD) instead of OS process/syscall threads.']}
for file,outname in [('views/view.py','view_core.py'),('views/scan_views.py','view_scan.py'),('views/seed_views.py','view_seed.py'),('views/screensaver.py','view_splash.py'),('views/developer_os_warning.py','view_development.py')]:
 raw=(source/'src/seedsigner'/file).read_bytes();tree=ast.parse(raw)
 classes={n.name:n for n in tree.body if isinstance(n,ast.ClassDef) and n.name!='Destination' and (outname!='view_splash.py' or n.name=='OpeningSplashView')}
 bindings={'UnicodeDecodeError':('builtins','UnicodeError'),'time':('seedsigner_port.clock',None),'Destination':('seedsigner_port.navigation','Destination'),'OpeningSplashScreen':('seedsigner_port.app_screens','OpeningSplashScreen')}
 if outname=='view_seed.py':bindings['random']=('seedsigner_port.quiz_random',None)
 originals=copy.deepcopy(classes)
 port=LazyPort(tree,'seedsigner.'+file[:-3].replace('/','.'),classes=classes,bindings=bindings)
 nodes=[]
 for n in tree.body:
  if isinstance(n,ast.FunctionDef):nodes.append(port.visit(copy.deepcopy(n)))
  elif isinstance(n,ast.ClassDef) and n.name in classes:
   original=copy.deepcopy(n)
   if n.name=='SeedWordsView':
    # The upstream floor division omits trailing words at15/18/21 lengths.
    matches=[x for x in ast.walk(n) if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='num_pages' for t in x.targets)]
    assert len(matches)==1 and ast.unparse(matches[0].value)=='int(len(mnemonic) / words_per_page)'
    matches[0].value=ast.parse('(len(mnemonic)+words_per_page-1)//words_per_page',mode='eval').body
   if n.name in ('RestartView','RebootToLoaderView'):
    # No OS process/syscall here: show the original screen, let the native
    # renderer flush it, then perform the native global reset. Loader mode
    # sets the Rockchip BOOT_BROM_DOWNLOAD flag so the ROM enters maskrom.
    screen='ResetScreen' if n.name=='RestartView' else 'RebootToLoaderScreen'
    run=next(x for x in n.body if isinstance(x,ast.FunctionDef) and x.name=='run')
    run.body=ast.parse('Settings.get_instance().flush_save()\nself.renderer.session.show_screen(_dependency("seedsigner.gui.screens.screen","'+screen+'"),{})\nfor _ in range(20):self.renderer.session.backend.tick()\n__import__("machine").reset('+('0' if n.name=='RestartView' else '1')+')\n').body
    n.body=[x for x in n.body if not isinstance(x,ast.ClassDef)]
   if any(ast.unparse(d)=='dataclass' for d in n.decorator_list):dataclass_constructor(n,originals)
   selected_port=port
   if n.name=='SeedAddressVerificationView':
    selected_port=LazyPort(tree,'seedsigner.'+file[:-3].replace('/','.'),classes=classes,bindings={**bindings,'BaseThread':('seedsigner_port.address_search','Worker'),'ThreadsafeCounter':('seedsigner_port.address_search','Counter')})
    for worker in [x for x in n.body if isinstance(x,ast.ClassDef)]:
     run=next(x for x in worker.body if isinstance(x,ast.FunctionDef) and x.name=='run')
     if worker.name=='BruteForceAddressVerificationThread':
      loops=[x for x in ast.walk(run) if isinstance(x,ast.While) and ast.unparse(x.test)=='self.keep_running'];assert len(loops)==1
      loops[0].body.append(ast.Expr(value=ast.Yield(value=None)))
     elif worker.name=='ExpandedBruteForceAddressVerificationThread':
      initialization=[x for x in run.body if isinstance(x,ast.For) and ast.unparse(x.target)=='path'];assert len(initialization)==1
      initialization[0].body.append(ast.Expr(value=ast.Yield(value=None)))
      loops=[x for x in ast.walk(run) if isinstance(x,ast.For) and ast.unparse(x.target)=='script_type'];assert len(loops)==1
      loops[0].body.append(ast.Expr(value=ast.Yield(value=None)))
     else:raise AssertionError('Unreviewed address worker')
   n=selected_port.visit(n)
   factory=ast.FunctionDef(name='_make_'+n.name,args=ast.arguments(posonlyargs=[],args=[],kwonlyargs=[],kw_defaults=[],defaults=[]),body=[n,ast.Return(value=ast.Name(id=n.name,ctx=ast.Load()))],decorator_list=[])
   nodes.append(factory)
 header='# Copyright2021 SeedSigner; MIT, see ../LICENSE.SeedSigner\n# Generated from pinned original source; optional class bases resolve only on use.\nfrom seedsigner_port.decode_platform import dependency as _dependency, FeatureUnavailable\nfrom seedsigner_port.navigation import Destination\n'
 footer='\n_FACTORIES={'+','.join(repr(name)+':_make_'+name for name in classes)+'}\n_CACHE={}\ndef _resolve(name):\n    if name not in _CACHE:\n        if name not in _FACTORIES:raise AttributeError(name)\n        _CACHE[name]=_FACTORIES[name]()\n    return _CACHE[name]\ndef __getattr__(name):return _resolve(name)\n'
 out=root/'app/seedsigner_port'/outname
 out.write_text(header+ast.unparse(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])))+'\n'+footer)
 receipt['files'][outname]={'source':file,'sourceSha256':hashlib.sha256(raw).hexdigest(),'outputSha256':hashlib.sha256(out.read_bytes()).hexdigest(),'classes':list(classes)}
(root/'app/views-provenance.json').write_text(json.dumps(receipt,indent=2)+'\n')
