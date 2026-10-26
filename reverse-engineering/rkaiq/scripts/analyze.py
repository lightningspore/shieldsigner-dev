#!/usr/bin/env python3
"""Run pinned Ghidra headless, reusing projects while keeping decompiles ignored."""
from pathlib import Path
import json,subprocess
ROOT=Path(__file__).resolve().parents[3]
info=json.loads((ROOT/'reverse-engineering/rkaiq/artifacts.json').read_text())
subprocess.run(['mise','exec','--','uv','run','python',str(Path(__file__).with_name('prepare.py')),'--ghidra'],cwd=ROOT,check=True)
cache=ROOT/'.tools/reverse-engineering';projects=ROOT/'dist/reverse-engineering/ghidra-projects';projects.mkdir(parents=True,exist_ok=True)
for name,project,folder in [('rkaiq_3A_server','RkaiqServer','server'),('librkaiq.so','RkaiqLibrary','library')]:
 out=cache/'decompiled'/folder;out.mkdir(parents=True,exist_ok=True)
 action=['-process',name] if (projects/(project+'.gpr')).exists() else ['-import',str(cache/'rkaiq-original'/name)]
 command=['mise','exec','java@'+info['tools']['java'],'--',str(cache/info['ghidra']['directory']/'support/analyzeHeadless'),str(projects),project,*action,'-max-cpu','4','-analysisTimeoutPerFile','600','-scriptPath',str(ROOT/'reverse-engineering/rkaiq/ghidra'),'-postScript','ExportRkaiq.java',str(out)]
 log=ROOT/'dist/reverse-engineering'/('ghidra-'+folder+'.log')
 inventory=out/'functions.json';before=inventory.stat().st_mtime_ns if inventory.exists() else 0
 with log.open('w') as f:subprocess.run(command,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,check=True)
 assert inventory.stat().st_mtime_ns>before,'Ghidra export did not refresh the inventory'
 functions=json.loads(inventory.read_text());selected=[f for f in functions if 'decompileCompleted' in f]
 assert selected and all(f['decompileCompleted'] for f in selected),'Selected decompiles failed; inspect '+str(log)
 print(name,len(functions),'analyzed functions;',len(selected),'selected decompiled')
