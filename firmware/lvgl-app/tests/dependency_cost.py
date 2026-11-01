"""Fresh-process import deltas; public module metadata, no hardware or wallets."""
import json,subprocess,sys
CHILD=r'''
import gc,importlib,json,sys
from pathlib import Path
sys.path[:0]=['/opt/src','/usr/lib/shieldsigner-camera/python']
def memory():
 out={}
 for line in Path('/proc/self/status').read_text().splitlines():
  key,_,value=line.partition(':')
  if key in ('VmRSS','RssAnon','RssFile','VmSwap'):out[key]=int(value.split()[0])
 out['privateAnonPlusSwap']=out['RssAnon']+out['VmSwap'];return out
gc.collect();before=memory();modules=set(sys.modules)
for name in json.loads(sys.argv[1]):importlib.import_module(name)
gc.collect();after=memory()
print(json.dumps(dict(beforeKiB=before,afterKiB=after,deltaKiB={key:after[key]-before[key] for key in before},addedModuleCount=len(set(sys.modules)-modules))))
'''
cases=[('Pillow core',['PIL.Image']),('Pillow GUI helpers',['PIL.Image','PIL.ImageDraw','PIL.ImageFont','PIL.ImageFilter','PIL.ImageColor']),('Seed model',['seedsigner.models.seed']),('Legacy GUI components',['seedsigner.gui.components']),('Legacy seed screens',['seedsigner.gui.screens.seed_screens'])]
results=[]
for label,modules in cases:
 result=json.loads(subprocess.check_output([sys.executable,'-B','-c',CHILD,json.dumps(modules)],text=True,timeout=45))
 results.append(dict(label=label,modules=modules,**result));print(json.dumps(dict(event='import-cost',label=label,**result)),flush=True)
print(json.dumps(dict(passed=True,results=results,units='KiB',freshProcessPerCase=True,scope='Import-only marginal costs versus a stdlib diagnostic baseline; overlapping cases must not be added; not complete running-app attribution',physicalDisplay=False)),flush=True)
