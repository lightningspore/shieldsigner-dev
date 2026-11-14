# SPDX-License-Identifier: MIT
"""Compare the complete PUBLIC default schema exported by DUT with port source."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'app'))
from seedsigner_port.settings_schema import SettingsDefinition
p=argparse.ArgumentParser(description=__doc__);p.add_argument('serial',type=Path);p.add_argument('report',type=Path);a=p.parse_args()
raw=a.serial.read_bytes()
lines=[line[len(b'@@SETTINGS_PUBLIC_SCHEMA '):] for line in raw.splitlines() if line.startswith(b'@@SETTINGS_PUBLIC_SCHEMA ')]
if len(lines)!=1:raise SystemExit('Need one complete public default schema')
actual=json.loads(lines[0]);expected=json.loads(json.dumps(SettingsDefinition.to_dict()))
if actual!=expected:raise SystemExit('Device schema differs from generated original schema')
canonical=json.dumps(actual,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
report={'passed':True,'entries':len(actual['settings_entries']),'schemaSha256':hashlib.sha256(canonical).hexdigest(),'serialSha256':hashlib.sha256(raw).hexdigest(),'portSourceSha256':hashlib.sha256((root/'app/seedsigner_port/settings_schema.py').read_bytes()).hexdigest(),'scope':'Public default schema, no applied/persisted/user settings'}
a.report.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
