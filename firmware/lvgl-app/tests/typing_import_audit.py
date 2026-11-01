"""Trace typing imports in the idle/scan module graph; no devices or wallet."""
import builtins,gc,json,os,sys
from pathlib import Path
sys.path[:0]=['/opt/src','/usr/lib/shieldsigner-camera/python']
from resources import process_snapshot
from dependency_policy import install
initially_loaded='typing' in sys.modules
edges=[];original_import=builtins.__import__
def traced(name,globals=None,locals=None,fromlist=(),level=0):
 if name=='typing':
  caller=sys._getframe(1)
  edges.append(dict(module=caller.f_globals.get('__name__'),file=caller.f_code.co_filename,line=caller.f_lineno,names=list(fromlist or ())))
 return original_import(name,globals,locals,fromlist,level)
builtins.__import__=traced;restore=None
try:
 restore=install('/opt/src',Path(__file__).parent/'source-guards.json')
 from runtime import Runtime
 from startup_policy import install as startup
 startup('/opt/src','/usr/lib/shieldsigner-camera/python')
 from seedsigner.gui.screens import seed_screens,scan_screens
 from seedsigner.views import scan_views
 gc.collect()
 print(json.dumps(dict(passed=True,initiallyLoaded=initially_loaded,typingLoaded='typing' in sys.modules,importEdges=edges,process=process_snapshot(os.getpid()),scope='Import-only Controller/Runtime/seed-screen/scan graph; no hardware opened or wallet created')),flush=True)
finally:
 builtins.__import__=original_import
 if restore is not None:restore()
