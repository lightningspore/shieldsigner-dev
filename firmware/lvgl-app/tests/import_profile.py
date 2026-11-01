"""Metadata-only pinned import profile; no LCD, wallet or camera startup."""
import importlib,json,os,sys,time
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parent),'/opt/src']
from guards import verify
from resources import process_snapshot,system_snapshot
verify('/opt/src',Path(__file__).parent/'source-guards.json')
started=time.monotonic();snapshots=[];previous=set(sys.modules)
def capture(stage):
    global previous
    current=set(sys.modules)
    item=dict(stage=stage,seconds=round(time.monotonic()-started,3),python=process_snapshot(os.getpid()),system=system_snapshot(),addedModules=sorted(current-previous),moduleCount=len(current))
    snapshots.append(item);previous=current;print(json.dumps(item),flush=True)
capture('baseline')
for name in ('seedsigner.models.settings','seedsigner.gui.screens.seed_screens','seedsigner.views.seed_views','seedsigner.views.tools_views'):
    importlib.import_module(name);capture(name)
exports={}
for name in ('seedsigner.views.tools_views','seedsigner.views.gpg_views','seedsigner.views.smartcard_views','seedsigner.views.password_generator_views','seedsigner.views.microsd_views'):
    module=sys.modules.get(name)
    if module is not None:
        exports[name]={key:dict(kind=type(value).__name__,origin=getattr(value,'__module__',None),qualname=getattr(value,'__qualname__',None)) for key,value in vars(module).items() if not key.startswith('__')}
print(json.dumps(dict(passed=True,importOnly=True,physicalDisplay=False,physicalCamera=False,snapshots=snapshots,exportBindings=exports)),flush=True)
