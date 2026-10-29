#!/usr/bin/env python3
"""Render measured memory only; RSS and CMA are separate to avoid double counting."""
import argparse,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=argparse.ArgumentParser();p.add_argument('input',type=Path);p.add_argument('output',type=Path);p.add_argument('--phase');p.add_argument('--compare',nargs='+');a=p.parse_args()
rows=[json.loads(x) for x in a.input.read_text().splitlines() if x.strip()]
fig,axes=plt.subplots(3,1,figsize=(12,12),layout='constrained')
labels=a.compare or list(dict.fromkeys(r['label'] for r in rows))
if any(not any(r['label']==label for r in rows) for label in labels):raise SystemExit('Unknown comparison phase')
for label in labels:
 group=[r for r in rows if r['label']==label];times=[r['elapsed'] for r in group]
 axes[0].plot(times,[r['memory']['MemAvailable']/1024 for r in group],label=label)
phase=a.phase or labels[-1]
active=[r for r in rows if r['label']==phase]
if not active:raise SystemExit('Unknown phase: '+phase)
t=[r['elapsed'] for r in active]
for name,color in [('python3','#2979b8'),('camera-probe','#d36b23'),('shieldsigner-qr','#8154a0')]:
 axes[1].plot(t,[sum(p.get('Pss',0) for p in r['processes'].values() if p['name']==name)/1024 for r in active],label=name+' PSS',color=color)
 axes[1].plot(t,[sum(p.get('Swap',0) for p in r['processes'].values() if p['name']==name)/1024 for r in active],label=name+' swapped (logical)',color=color,linestyle=':')
 axes[1].plot(t,[sum(p.get('Pss_Anon',0) for p in r['processes'].values() if p['name']==name)/1024 for r in active],label=name+' private anonymous',color=color,linestyle='--')
if any('zram' in r for r in active):
 axes[2].plot(t,[r.get('zram',{}).get('allocatedBytes',0)/1048576 for r in active],label='zram physical RAM',linestyle='--')
if any(r.get('zram',{}).get('originalBytes',0) for r in active):
 axes[2].plot(t,[r.get('zram',{}).get('originalBytes',0)/1048576 for r in active],label='zram logical data',linestyle=':')
for key in ['CmaAllocated','Shmem','SUnreclaim','PageTables','KernelStack']:
 axes[2].plot(t,[r['memory'].get(key,0)/1024 for r in active],label=key)
for ax,title in zip(axes,['Available memory by phase','App and camera process memory — selected trial','Camera DMA and selected OS memory — selected trial']):
 ax.set(title=title,xlabel='Seconds within phase',ylabel='MiB');ax.grid(alpha=.25);ax.legend(fontsize=8,loc='upper center',bbox_to_anchor=(.5,1.0),ncol=3);ax.set_ylim(bottom=0)
fig.suptitle('ShieldSigner • measured on 64 MiB Luckfox Mini\nPSS apportions shared pages; available memory includes reclaimable cache',fontsize=13)
a.output.parent.mkdir(parents=True,exist_ok=True);fig.savefig(a.output,dpi=160)
