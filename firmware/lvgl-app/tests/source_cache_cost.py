"""Measure source inspection cache retention; no hardware or wallet creation."""
import gc,inspect,json,linecache,os,sys
from pathlib import Path
sys.path[:0]=['/opt/src','/usr/lib/shieldsigner-camera/python']
from dependency_policy import install
from resources import process_snapshot
restore=install('/opt/src',Path(__file__).parent/'source-guards.json')
def memory():
 gc.collect();s=process_snapshot(os.getpid())
 return sum(int(s[key].split()[0]) for key in ('RssAnon','VmSwap'))
read_source=inspect.getsource
if '--evict-on-read' in sys.argv:
 from source_text import getsource as read_source
try:
 from seedsigner.controller import Controller
 from seedsigner.views.seed_views import SeedWordsView
 from seedsigner.views.tools_views import ToolsImageEntropyFinalImageView
 from seedsigner.gui.screens.tools_screens import ToolsImageEntropyLivePreviewScreen
 from seedsigner.hardware.microsd import MicroSD
 methods=[Controller.start,SeedWordsView.run,ToolsImageEntropyFinalImageView.run,ToolsImageEntropyLivePreviewScreen._run,MicroSD.run]
 paths={inspect.getsourcefile(method) for method in methods}
 for path in paths:linecache.cache.pop(path,None)
 before=memory()
 for method in methods:
  text=read_source(method)
  assert text.strip()
 del text
 retained=memory();entries=[]
 for path in sorted(paths):
  entry=linecache.cache.get(path)
  if entry is None:continue
  entries.append(dict(file=str(Path(path).relative_to('/opt/src')),sourceBytes=entry[0],retainedPythonBytes=sys.getsizeof(entry)+sys.getsizeof(entry[2])+sum(sys.getsizeof(line) for line in entry[2])))
 for path in paths:linecache.cache.pop(path,None)
 after=memory()
 print(json.dumps(dict(passed=True,evictOnRead=('--evict-on-read' in sys.argv),scope='Isolated inspection of methods used by existing LVGL adapters; not a running-app total',beforePrivateKiB=before,cachedPrivateKiB=retained,evictedPrivateKiB=after,cacheEntries=entries,retainedPythonBytes=sum(e['retainedPythonBytes'] for e in entries),hardwareOpened=False,walletCreated=False)),flush=True)
finally:restore()
