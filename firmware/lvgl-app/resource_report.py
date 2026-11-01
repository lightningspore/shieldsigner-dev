"""Summarize verified hardware receipts without adding shared RSS as total RAM.

One receipt reports observations; two require matching code and workload before
comparison. No device access, deployment, payloads or pixel data.
"""
import argparse,json,statistics
from pathlib import Path

def number(value):return int(value.split()[0])

def summarize(receipt):
    result=receipt.get('result')
    if not receipt.get('passed') or not isinstance(result,dict) or not result.get('passed'):
        raise ValueError('A successful hardware receipt is required')
    if receipt.get('worktreeChangedDuringCheck') or receipt.get('remainingOwnerPids') or not receipt.get('remoteBundleVerified'):
        raise ValueError('Unverified bundle, source mutation or remaining diagnostic owner')
    phases={}
    for phase,start,end in [('home-idle',1,8),('camera-live',5,15)]:
        rows=[row for row in result['samples'] if row['phase']==phase and start<=row['elapsed']<end]
        if not rows:continue
        if len(rows)<2:raise ValueError('Insufficient samples for '+phase)
        processes={};owners={}
        for row in rows:
            groups={key:row[key] for key in ('python','native') if row.get(key) is not None}
            for owner in row.get('pipelineOwners',[]):
                name=owner['executable']
                owners.setdefault(name,set()).add(owner['pid'])
                if len(owners[name])!=1 or name in groups:raise ValueError('Owner changed or duplicated inside measurement window')
                groups[name]=owner['process']
            for name,process in groups.items():processes.setdefault(name,[]).append((row['wall'],process))
        summaries={}
        for name,samples in processes.items():
            first,last=samples[0],samples[-1]
            if len(samples)!=len(rows):raise ValueError('Process absent during part of measurement window: '+name)
            seconds=last[0]-first[0]
            ticks=lambda p:p['user_ticks']+p['system_ticks']
            delta=ticks(last[1])-ticks(first[1])
            if seconds<=0 or delta<0:raise ValueError('Invalid process counter interval')
            summaries[name]={key:statistics.median(number(sample[key]) for _,sample in samples) for key in ('VmRSS','RssAnon','VmSwap','Threads')}
            summaries[name]['cpuPercentOneCore']=round(100*delta/result['clockTicks']/seconds,3)
        phases[phase]=dict(sampleCount=len(rows),windowSeconds=round(rows[-1]['wall']-rows[0]['wall'],4),medianUnits='KiB except Threads',processes=summaries,medianSystemMemAvailableKiB=statistics.median(number(row['system']['MemAvailable']) for row in rows),dmaObservations=sorted({row['dma'] for row in rows if row.get('dma') is not None}))
    if 'home-idle' not in phases or (result.get('cameraStarted') and 'camera-live' not in phases):raise ValueError('Missing required workload window')
    return dict(frontend=result['frontend'],phases=phases,cameraStats=result.get('cameraStats'))

def report(receipts):
    if not 1<=len(receipts)<=2:raise ValueError('Supply one observation or two matched receipts')
    summaries=[summarize(receipt) for receipt in receipts]
    if len(receipts)==2:
        if {summary['frontend'] for summary in summaries}!={'lvgl','pil'}:raise ValueError('Comparison needs LVGL and original PIL')
        a,b=receipts
        if not a.get('bundleSha256') or a['bundleSha256']!=b.get('bundleSha256') or a.get('binarySha256')!=b.get('binarySha256'):
            raise ValueError('Comparison code/binary differs; rerun both with the same bundle')
        for key in ('cameraStarted','cameraSeconds','idleSeconds','sameSmallRamPolicy','sameGPIOScript','cameraCompletionSuppressed'):
            if a['result'].get(key)!=b['result'].get(key):raise ValueError('Comparison workload differs: '+key)
    return dict(kind='frontend-resource-observations',paired=len(receipts)==2,results=summaries,limitations=['Warm-device measurements with benchmark overhead; no cold-start or repeat-order qualification.','RSS and swap are separate; shared pages and DMA prevent summing RSS as total physical RAM.','Process CPU excludes unmeasured kernel work; no FPS or response-latency claim.'])

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('receipts',nargs='+',type=Path)
    args=parser.parse_args()
    print(json.dumps(report([json.loads(path.read_text()) for path in args.receipts]),indent=2))

if __name__=='__main__':main()
