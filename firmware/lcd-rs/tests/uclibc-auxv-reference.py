"""Run under packed ARM Python: script.py /absolute/extension.so."""
import ctypes,errno,json,os,struct,sys
from pathlib import Path
lib=ctypes.CDLL(sys.argv[1],use_errno=True)
f=lib.__wrap_getauxval;f.argtypes=[ctypes.c_ulong];f.restype=ctypes.c_ulong
raw=Path('/proc/self/auxv').read_bytes()
size=struct.calcsize('@LL')
entries=dict(struct.unpack('@LL',raw[i:i+size]) for i in range(0,len(raw),size))
for kind in [6,16,51]:
 ctypes.set_errno(123)
 assert f(kind)==entries.get(kind,0),(kind,f(kind),entries.get(kind,0))
 assert ctypes.get_errno()==(123 if kind in entries else errno.ENOENT)
ctypes.set_errno(0);assert f(0xffffffff)==0 and ctypes.get_errno()==errno.ENOENT
assert f(6)==os.sysconf('SC_PAGE_SIZE')
print(json.dumps({'passed':True,'auxvKeysCompared':[6,16,51],'pageSizeMatchesSysconf':True,'unknownKeyEnoent':True,'successPreservesErrno':True}))
