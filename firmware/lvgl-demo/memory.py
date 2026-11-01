"""Read-only PSS/thread/system memory sample for the isolated hardware demo."""
import json
from pathlib import Path
import subprocess
import sys
import time
from artifact_paths import DEMO_WORK

def shell(command):
    return subprocess.check_output(['adb','shell',command],text=True).replace('\r','')
processes=[]
for line in shell('ps -o pid,ppid,args').splitlines()[1:]:
    fields=line.split(None,2)
    if len(fields)<3: continue
    pid,parent,args=fields
    if args=='/tmp/lvgl-demo': name='lvgl'
    elif args=='python3 -u /tmp/lvgl-demo-run.py': name='python-adapter'
    elif args.startswith('/usr/lib/shieldsigner-camera/camera-probe stream-sc3336 '): name='rust-camera'
    else: continue
    values={}
    for item in shell(f'cat /proc/{pid}/smaps_rollup; cat /proc/{pid}/status').splitlines():
        key,sep,value=item.partition(':')
        if sep and key in ('Rss','Pss','Pss_Anon','Pss_File','Pss_Shmem','SwapPss','Threads'):
            values[key]=int(value.strip().split()[0])
    processes.append(dict(name=name,pid=int(pid),memoryKiB=values))
mem={}
for item in shell('cat /proc/meminfo').splitlines():
    key,_,value=item.partition(':')
    if key in ('MemTotal','MemAvailable','MemFree','Cached','Shmem','SwapTotal','SwapFree'):mem[key]=int(value.split()[0])
result=dict(timestamp=time.time(),label=sys.argv[1],processes=processes,systemKiB=mem,zramMmStat=shell('cat /sys/block/zram0/mm_stat').strip(),dma=shell('cat /sys/kernel/debug/dma_buf/bufinfo').splitlines()[-1],page=shell('cat /tmp/lvgl-demo-page').strip())
out=DEMO_WORK/('memory-'+sys.argv[1]+'.json')
out.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
