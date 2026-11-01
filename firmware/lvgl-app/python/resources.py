"""Metadata-only /proc snapshots for temporary hardware qualification."""
from pathlib import Path
import re

def smaps_snapshot(source):
    """Aggregate accounting only; omit addresses and arbitrary mapped filenames."""
    groups={};current=None
    fields=('Rss','Pss','Private_Dirty','Private_Clean','Swap','SwapPss')
    for line in source.splitlines():
        if re.match(r'^[0-9a-f]+-[0-9a-f]+ ',line):
            parts=line.split(None,5);path=parts[5].strip() if len(parts)>5 else ''
            name=path.rsplit('/',1)[-1]
            if not path:name='[anonymous]'
            elif path.startswith('['):name=path if path in ('[heap]','[stack]','[vdso]','[vectors]','[sigpage]') else '[kernel mapping]'
            elif not re.search(r'\.so(?:\.[0-9]+)*$',name) and not re.fullmatch(r'python[0-9.]*',name):name='[mapped file]'
            current=groups.setdefault(name,{field:0 for field in fields})
        elif current is not None and ':' in line:
            key,_,value=line.partition(':')
            if key in fields:
                count,unit=value.split()
                if unit!='kB' or not count.isdigit():raise ValueError('Unexpected smaps accounting')
                current[key]+=int(count)
    if not groups:raise ValueError('No smaps mappings available')
    rows=[dict(mapping=name,**values) for name,values in groups.items()]
    rows.sort(key=lambda row:row['Rss']+row['Swap'],reverse=True)
    return dict(units='KiB',mappings=rows,processTotals={field:sum(row[field] for row in rows) for field in fields})

def process_snapshot(pid):
    status={}
    for line in (Path('/proc')/str(pid)/'status').read_text().splitlines():
        name,_,value=line.partition(':')
        if name in {'VmRSS','VmHWM','VmSize','RssAnon','RssFile','RssShmem','Threads','VmSwap','VmData'}:status[name]=value.strip()
    # stat's parenthesized comm can contain spaces; fields after it start at 3.
    stat=(Path('/proc')/str(pid)/'stat').read_text().rsplit(')',1)[1].split()
    status['minor_faults']=int(stat[7]);status['major_faults']=int(stat[9])
    status['user_ticks']=int(stat[11]);status['system_ticks']=int(stat[12])
    return status


def system_snapshot():
    result={}
    wanted={'MemTotal','MemAvailable','MemFree','SwapTotal','SwapFree','Shmem'}
    for line in Path('/proc/meminfo').read_text().splitlines():
        name,_,value=line.partition(':')
        if name in wanted:result[name]=value.strip()
    return result
