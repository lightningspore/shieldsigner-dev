#!/usr/bin/env python3
"""Host-side ADB sampling; no Python interpreter or capture data on target."""
import argparse,json,subprocess,time,shlex
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--serial',default='0a523b8b23110ffc');p.add_argument('--label',required=True);p.add_argument('--seconds',type=float,default=30);p.add_argument('--output',type=Path,required=True);p.add_argument('--telemetry-file',type=Path);a=p.parse_args()
command='''echo SECTION:meminfo
cat /proc/meminfo
for p in /proc/[0-9]*; do
 read name < "$p/comm" || continue
 case "$name" in python3|camera-probe|shieldsigner-qr*)
 echo SECTION:process:${p##*/}:$name
 cat "$p/smaps_rollup" 2>/dev/null
 read proc_stat < "$p/stat" && echo "STAT:${p##*/}:$proc_stat"
 ;; esac
done
echo SECTION:zram
cat /sys/block/zram0/mm_stat 2>/dev/null || true
'''
if a.telemetry_file:
 command += 'echo SECTION:telemetry\ncat '+shlex.quote(str(a.telemetry_file))+' 2>/dev/null || true\n'
a.output.parent.mkdir(parents=True,exist_ok=True)
start=time.monotonic()
with a.output.open('a') as f:
 while True:
  raw=subprocess.check_output(['adb','-s',a.serial,'shell',command],text=True)
  record={'label':a.label,'unix':time.time(),'elapsed':time.monotonic()-start,'processes':{}}
  section=None
  for line in raw.splitlines():
   if line.startswith('SECTION:'):
    parts=line.split(':')
    if parts[1]=='meminfo':section=record.setdefault('memory',{})
    elif parts[1]=='zram':section='zram'
    elif parts[1]=='telemetry':section='telemetry'
    else:section=record['processes'].setdefault(parts[2],{'name':parts[3]})
   elif section=='telemetry':
    try:record['telemetry']=json.loads(line)
    except ValueError:pass
   elif line.startswith('STAT:'):
    _,pid,raw_stat=line.split(':',2)
    # comm is enclosed in parentheses and may contain spaces.
    fields=raw_stat.rsplit(')',1)[1].split()
    record['processes'][pid].update(userCpuTicks=int(fields[11]),systemCpuTicks=int(fields[12]),threads=int(fields[17]),startTicks=int(fields[19]))
   elif section=='zram':
    values=line.split()
    if len(values)>=3 and all(v.isdigit() for v in values):record['zram']={'originalBytes':int(values[0]),'compressedBytes':int(values[1]),'allocatedBytes':int(values[2])}
   elif section is not None and ':' in line:
    key,value=line.split(':',1)
    if value.strip().endswith('kB'):section[key]=int(value.split()[0])
  f.write(json.dumps(record)+'\n');f.flush()
  if time.monotonic()-start>=a.seconds:break
  time.sleep(1)
