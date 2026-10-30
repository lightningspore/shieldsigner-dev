#!/usr/bin/env python3
"""Separate import allocation and shallow-object views; no invented heap pie."""
import argparse,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=argparse.ArgumentParser();p.add_argument('input',type=Path);p.add_argument('output',type=Path);a=p.parse_args();data=json.loads(a.input.read_text())
fig,axes=plt.subplots(1,2,figsize=(13,6),layout='constrained')
rows=data['startupImportSequence'];labels=['Entry imports','Startup routes','Scan imports','Seed views','Tools views','Settings views','Smartcard views']
values=[r['tracedLiveBytes']/1048576 for r in rows]
axes[0].barh(labels,values,color=['#477b9d','#c97932','#477b9d','#477b9d','#477b9d','#477b9d','#477b9d']);axes[0].invert_yaxis();axes[0].set_title('ARM Python live traced import allocations\nQEMU import sequence; no live GUI or target RSS')
scan=next(r for r in data['objectCensus'] if r['phase']=='scan');bytype={r['type']:r for r in scan['types']}
names=['Function code objects','Class objects','Dictionaries','Function objects','Tuples','Lists']
sizes=[scan['functionCodeShallowBytes']]+[bytype[x]['shallowBytes'] for x in ['builtins.type','builtins.dict','builtins.function','builtins.tuple','builtins.list']]
axes[1].barh(names,[x/1048576 for x in sizes],color='#627b5c');axes[1].invert_yaxis();axes[1].set_title('Shallow sizes during Scan on the real board\nExcludes contents/native buffers; selected categories only')
for ax in axes:
 ax.set_xlabel('MiB');ax.grid(axis='x',alpha=.2);ax.set_axisbelow(True)
 for bar in ax.patches:
  width=bar.get_width();ax.text(width+.04,bar.get_y()+bar.get_height()/2,f'{width:.2f}',va='center',fontsize=9)
 ax.set_xlim(0,ax.get_xlim()[1]*1.13)
for ax in axes: ax.title.set_fontsize(11)
fig.suptitle('ShieldSigner Python memory — separate measurement views, not additive',fontsize=14)
a.output.parent.mkdir(parents=True,exist_ok=True);fig.savefig(a.output,dpi=150)
