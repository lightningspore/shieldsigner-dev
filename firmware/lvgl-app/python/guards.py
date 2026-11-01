"""Reject application versions whose screen contracts have not been reviewed."""
import hashlib
import json
from pathlib import Path

def verify(app_root,manifest):
    base=Path(app_root).resolve()/'seedsigner'
    guards=json.loads(Path(manifest).read_text())
    for relative,expected in guards.items():
        path=base/relative
        digest=hashlib.sha256()
        with path.open('rb') as source:
            for chunk in iter(lambda:source.read(65536),b''):digest.update(chunk)
        if digest.hexdigest()!=expected:raise ValueError('Unreviewed LVGL app source: '+relative)
    return len(guards)
