"""Fetch exact public source revisions into ignored dist; never modify checkouts."""
import json
from pathlib import Path
import subprocess
HERE=Path(__file__).resolve().parent
from artifact_paths import ROOT,DIST,LVGL_SOURCES
LOCK=json.loads((HERE/'sources.lock.json').read_text())
def fetch(name):
    spec=LOCK[name]; path=LVGL_SOURCES/name
    if not path.exists():
        subprocess.run(['git','init',str(path)],check=True,stdout=subprocess.DEVNULL)
        subprocess.run(['git','-C',str(path),'remote','add','origin',spec['url']],check=True)
        subprocess.run(['git','-C',str(path),'fetch','--depth','1','origin',spec['commit']],check=True)
        subprocess.run(['git','-C',str(path),'checkout','--detach','FETCH_HEAD'],check=True)
    actual=subprocess.check_output(['git','-C',str(path),'rev-parse','HEAD'],text=True).strip()
    if actual!=spec['commit']: raise RuntimeError(f'{name}: unexpected revision {actual}')
    if subprocess.check_output(['git','-C',str(path),'status','--porcelain'],text=True).strip():
        raise RuntimeError(f'{name}: source checkout is dirty')
    return path
if __name__=='__main__':
    for name in LOCK: print(name,fetch(name))
