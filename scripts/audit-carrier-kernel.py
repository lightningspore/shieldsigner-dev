#!/usr/bin/env python3
"""Review a retained compiled kernel snapshot, without relabeling image proof."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import runpy
from carrier_pinmux import audit_carrier_pinmux,audit_carrier_uart

ROOT = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--dtb',type=Path,required=True)
p.add_argument('--config',type=Path,required=True)
p.add_argument('--report',type=Path,required=True)
a = p.parse_args()
parser = runpy.run_path(str(ROOT/'reverse-engineering/rkaiq/scripts/check-image-kernel-abi.py'))
config_text = a.config.read_text()
config = dict(re.findall(r'^(CONFIG_\w+)=(.+)$',config_text,re.M))
config.update({key:'n' for key in re.findall(r'^# (CONFIG_\w+) is not set$',config_text,re.M)})
nodes = parser['fdt_properties'](a.dtb.read_bytes())
report = {'scope':'Retained compiled snapshot audit, not the installed or selected carrier image',
          'installedImageVerified':False,
          'dtb':{'path':str(a.dtb),'sha256':hashlib.sha256(a.dtb.read_bytes()).hexdigest()},
          'kernelConfig':{'path':str(a.config),'sha256':hashlib.sha256(a.config.read_bytes()).hexdigest()},
          'compiledCarrierPinmux':audit_carrier_pinmux(nodes,config),
          'compiledCarrierUart':audit_carrier_uart(nodes,config)}
a.report.parent.mkdir(parents=True,exist_ok=True)
a.report.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
