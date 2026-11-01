"""Fresh-process guarded wallet import footprint; no wallets or hardware opened."""
import importlib,json,os,sys,gc
from pathlib import Path
sys.path[:0]=['/opt/src','/usr/lib/shieldsigner-camera/python']
from dependency_policy import install
from resources import process_snapshot
restore=install('/opt/src',Path(__file__).parent/'source-guards.json')
def snapshot():
 gc.collect();status=process_snapshot(os.getpid())
 return dict(privateKiB=sum(int(status[key].split()[0]) for key in ('RssAnon','VmSwap')),rssKiB=int(status['VmRSS'].split()[0]),packages={root:sum(n==root or n.startswith(root+'.') for n in sys.modules) for root in ('PIL','Cryptodome','cryptography','pysatochip','smartcard','ecdsa','urtypes')})
try:
 target=sys.argv[2] if len(sys.argv)>2 else 'seedsigner.views.seed_views'
 before=snapshot();importlib.import_module(target);after=snapshot()
 print(json.dumps(dict(passed=True,module=target,before=before,after=after,importDeltaPrivateKiB=after['privateKiB']-before['privateKiB'],scope='Import-only wallet View graph; no hardware, seed, key or wallet created')),flush=True)
finally:restore()
