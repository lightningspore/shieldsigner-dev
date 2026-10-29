#!/usr/bin/env python3
"""Compare measured phase wall/CPU maxima and page faults, without captures."""
import json,argparse
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=argparse.ArgumentParser();p.add_argument('input',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
r=json.loads(a.input.read_text());fig,axes=plt.subplots(1,2,figsize=(12,5),layout='constrained')
names=['ae-statistics','awb-statistics','isp-prepare-submit'];width=.23
for n,trial in enumerate(r):
 phases={x['name']:x for x in trial['metrics']['phases']};x=[i+(n-1)*width for i in range(3)]
 axes[0].bar(x,[phases[k]['worstWallUs']/1000 for k in names],width,label=trial['label'])
 axes[1].bar(x,[phases[k]['majorFaults'] for k in names],width,label=trial['label'])
for ax in axes:ax.set_xticks(range(3),['AE','AWB','ISP submission']);ax.grid(axis='y',alpha=.2);ax.legend(fontsize=8)
axes[0].set(title='Longest observed phase duration',ylabel='Wall time (ms)')
axes[1].set(title='Major faults during each phase',ylabel='Fault count (trial lengths differ)')
fig.suptitle('Camera stalls on real hardware • separate diagnostic trials\nThese trials changed logging, then code pinning and startup hashing; no claim of isolated causality')
a.output.parent.mkdir(parents=True,exist_ok=True);fig.savefig(a.output,dpi=160)
