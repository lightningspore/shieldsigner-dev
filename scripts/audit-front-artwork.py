#!/usr/bin/env python3
"""Verify the exact front-artwork delta and return its protected predecessor.

This adds a new link to the historical audit chain. It never widens or rewrites
the older routing/socket records. All pre-existing board objects, including
front pin labels and rear attribution, must be identical to the predecessor.
"""
import hashlib
import json
import runpy
import subprocess
import uuid
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PCB=ROOT/'kicad/SeedSigner-Plus-smartcard-pico.kicad_pcb'
RECORD=ROOT/'docs/pcb-front-artwork.json'
sx=runpy.run_path(str(ROOT/'scripts/kicad-sexpr.py'))
art=runpy.run_path(str(ROOT/'scripts/audit-pcb-artwork.py'))


def verify():
    rec=json.loads(RECORD.read_text())
    baseline=subprocess.check_output(['git','show',rec['baselineCommit']+':kicad/'+PCB.name],cwd=ROOT)
    assert hashlib.sha256(baseline).hexdigest()==rec['baselineBoardSha256']
    current=PCB.read_text()
    assert hashlib.sha256(current.encode()).hexdigest()==rec['boardSha256'],'Unrecorded change after front artwork'
    before=sx['parse'](baseline.decode());after=sx['parse'](current)
    identity=lambda n:sx['one'](n,'uuid')[1]
    before_map={identity(n):n for n in before if isinstance(n,list) and sx['one'](n,'uuid')}
    after_map={identity(n):n for n in after if isinstance(n,list) and sx['one'](n,'uuid')}
    assert len(after_map)==sum(isinstance(n,list) and bool(sx['one'](n,'uuid')) for n in after),'Repeated top-level UUID'
    for key,value in before_map.items():
        assert after_map.get(key)==value,'Existing object changed: '+key
    expected={str(uuid.uuid5(uuid.NAMESPACE_URL,'shieldsigner-front-orbital:'+str(i))) for i in range(rec['graphics'])}
    assert set(after_map)-set(before_map)==expected|{rec['groupUuid']},'Unexpected added object'
    assert all(art['silk'](after_map[key]) and sx['one'](after_map[key],'layer')[1]=='F.SilkS' for key in expected)
    group=after_map[rec['groupUuid']]
    assert group[0]=='group' and group[1]==rec['groupName']
    assert len(group)==4 and set(sx['one'](group,'members')[1:])==expected
    assert len(sx['one'](group,'members')[1:])==len(expected),'Repeated or missing group member'
    protected_before=art['protected'](before)
    protected_after=art['protected']([n for n in after if n!=group])
    assert protected_before==protected_after,'Protected hardware changed'
    assert art['digest'](protected_after)==rec['protectedTreeSha256']
    # Rear artwork and original front texts/shapes also match exactly via the
    # UUID comparison above; original object ordering is not a design change.
    out=ROOT/'hardware/front-artwork-audit.json'
    report=dict(schema=1,passed=True,boardSha256=rec['boardSha256'],baselineCommit=rec['baselineCommit'],
                baselineBoardSha256=rec['baselineBoardSha256'],protectedTreeSha256=rec['protectedTreeSha256'],
                addedFrontGraphics=rec['graphics'],group=rec['groupName'],
                scope=rec['scope'],minimumStrokeMm=rec['minimumStrokeMm'],maskClearanceMm=rec['maskClearanceMm'],
                qualification='Exact artwork-only source comparison and recorded clearance constraints; native DRC, print-process review and physical hardware qualification remain separate.')
    out.write_text(json.dumps(report,indent=2)+'\n')
    print('Front artwork audit: all original objects unchanged; only grouped F.SilkS graphics added.')
    return baseline


if __name__=='__main__':
    verify()
