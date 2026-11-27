#!/usr/bin/env python3
"""Record or verify the alternate ILI9341 socket edit (J702, JP701, JP702).

  uv run python scripts/audit-ili9341-socket.py --record   # after the edit scripts
  uv run python scripts/audit-ili9341-socket.py            # verify (hardware:check)

The record (docs/pcb-ili9341-edits.json) pins the 0.0.13 baseline board and
lists every item the edit added, removed or modified, with fingerprints.
Verification fails on any other difference: unrecorded routing, footprint or
net changes, non-45-degree or zero-length new tracks, or changes to existing
schematic circuitry beyond the added J702/JP701/JP702 connections.
"""

import argparse
import hashlib
import json
import math
import runpy
import subprocess
import xml.etree.ElementTree as E
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
K = ROOT / 'kicad'
V = ROOT / 'hardware'
PCB = K / 'SeedSigner-Plus-smartcard-pico.kicad_pcb'
RECORD = ROOT / 'docs/pcb-ili9341-edits.json'
BASELINE = '86d702b'  # last 0.0.13 board commit
ADDED_REFS = {'J702', 'JP701', 'JP702'}
SLOTTED = {'H702', 'H704'}
SILK_TRIMMED = {'U202'}

sx = runpy.run_path(str(ROOT / 'scripts/kicad-sexpr.py'))
c, o, parse = sx['children'], sx['one'], sx['parse']


def norm(n):
    if isinstance(n, list):
        return [norm(x) for x in n]
    try:
        return float(n)
    except ValueError:
        return n


def strip_uuid(n):
    if isinstance(n, list):
        return [strip_uuid(x) for x in n if not (isinstance(x, list) and x and x[0] == 'uuid')]
    return n


def fingerprint(n):
    return hashlib.sha256(json.dumps(norm(n), separators=(',', ':')).encode()).hexdigest()


def nodes(tree, kind):
    return {o(n, 'uuid')[1]: n for n in c(tree, kind)}


def fps(tree):
    return {next(p[2] for p in c(n, 'property') if p[1] == 'Reference'): n
            for n in c(tree, 'footprint')}


def texts(tree):
    return {o(n, 'uuid')[1]: n for n in c(tree, 'gr_text')}


def without(node, keys):
    return [x for x in node if not (isinstance(x, list) and x and x[0] in keys)]


def git(path):
    return subprocess.check_output(['git', 'show', BASELINE + ':' + path], cwd=ROOT)


def diff(before, after):
    a, b = parse(before.decode()), parse(after)
    out = {}
    for kind in ('segment', 'via'):
        old, new = nodes(a, kind), nodes(b, kind)
        out[kind] = {'removed': sorted(set(old) - set(new)), 'added': sorted(set(new) - set(old)),
                     'changed': sorted(k for k in set(old) & set(new) if norm(old[k]) != norm(new[k]))}
    oldt, newt = texts(a), texts(b)
    out['text'] = {'added': sorted(set(newt) - set(oldt)),
                   'changed': sorted(k for k in set(oldt) & set(newt) if norm(oldt[k]) != norm(newt[k])),
                   'removed': sorted(set(oldt) - set(newt))}
    oldf, newf = fps(a), fps(b)
    out['footprints'] = {'added': sorted(set(newf) - set(oldf)), 'removed': sorted(set(oldf) - set(newf)),
                         'changed': sorted(r for r in set(oldf) & set(newf)
                                           if norm(oldf[r]) != norm(newf[r]))}
    return a, b, out


def record():
    before = git('kicad/' + PCB.name)
    a, b, d = diff(before, PCB.read_text())
    segs, vias, newt, newf = nodes(b, 'segment'), nodes(b, 'via'), texts(b), fps(b)
    oldsegs = nodes(a, 'segment')
    data = {
        'revision': '0.0.13-dev + alternate ILI9341 socket',
        'baselineCommit': BASELINE,
        'baselineBoardSha256': hashlib.sha256(before).hexdigest(),
        'scripts': ['scripts/add-ili9341-schematic.py', 'scripts/add-ili9341-pcb.py',
                    'scripts/route-ili9341.py'],
        'removedSegments': {k: o(oldsegs[k], 'net')[-1] for k in d['segment']['removed']},
        'addedSegments': {k: fingerprint(segs[k]) for k in d['segment']['added']},
        'addedVias': {k: fingerprint(vias[k]) for k in d['via']['added']},
        'addedTexts': {k: fingerprint(newt[k]) for k in d['text']['added']},
        'movedTexts': {k: fingerprint(newt[k]) for k in d['text']['changed']},
        'addedFootprints': {r: fingerprint(strip_uuid(newf[r])) for r in d['footprints']['added']},
        'modifiedFootprints': {r: fingerprint(strip_uuid(newf[r])) for r in d['footprints']['changed']},
        'filledZones': {k: fingerprint(z) for k, z in nodes(b, 'zone').items()},
    }
    RECORD.write_text(json.dumps(data, indent=2) + '\n')
    print('Recorded', RECORD.relative_to(ROOT), {k: len(v) for k, v in data.items()
                                                  if isinstance(v, (dict, list))})


def netlist(folder, out):
    cli = runpy.run_path(str(ROOT / 'scripts/kicad.py'))['cli']()
    subprocess.run([str(cli), 'sch', 'export', 'netlist', '--format', 'kicadxml', '--output',
                    str(out), str(folder / PCB.with_suffix('.kicad_sch').name)],
                   check=True, stdout=subprocess.DEVNULL)
    t = E.parse(out)
    parts = {n.attrib['ref']: (n.findtext('value'), n.findtext('footprint'))
             for n in t.findall('./components/comp') if n.attrib['ref'] not in ADDED_REFS}
    nets = sorted(sorted((n.attrib['ref'], n.attrib['pin']) for n in net.findall('node')
                         if n.attrib['ref'] not in ADDED_REFS) for net in t.findall('./nets/net'))
    return parts, [n for n in nets if n]


def verify():
    rec = json.loads(RECORD.read_text())
    before = git('kicad/' + PCB.name)
    assert hashlib.sha256(before).hexdigest() == rec['baselineBoardSha256'], 'Baseline moved'
    a, b, d = diff(before, PCB.read_text())
    segs, vias, newt, newf, oldf = nodes(b, 'segment'), nodes(b, 'via'), texts(b), fps(b), fps(a)
    # Everything outside the recorded item families must remain identical,
    # including stackup, design rules, board outline, keepouts and ground fills.
    assert norm(without(a, {'footprint', 'segment', 'via', 'gr_text', 'zone'})) == norm(
        without(b, {'footprint', 'segment', 'via', 'gr_text', 'zone'})), 'Unrecorded board change'
    oldzones, newzones = nodes(a, 'zone'), nodes(b, 'zone')
    assert set(oldzones) == set(newzones), 'Zone added or removed'
    for key in oldzones:
        assert norm(without(oldzones[key], {'filled_polygon'})) == norm(
            without(newzones[key], {'filled_polygon'})), 'Zone rules or boundary changed'
    assert {k: fingerprint(z) for k, z in newzones.items()} == rec['filledZones'], 'Unrecorded zone fill'
    assert git('kicad/' + PCB.with_suffix('.kicad_pro').name) == PCB.with_suffix('.kicad_pro').read_bytes(), 'Project rules changed'


    assert d['segment']['changed'] == [] and d['via']['changed'] == [], 'Unrecorded route change'
    assert d['via']['removed'] == [], 'Unrecorded via removal'
    assert d['segment']['removed'] == sorted(rec['removedSegments']), 'Unrecorded track removal'
    assert {k: fingerprint(segs[k]) for k in d['segment']['added']} == rec['addedSegments']
    assert {k: fingerprint(vias[k]) for k in d['via']['added']} == rec['addedVias']
    assert d['text']['removed'] == []
    assert {k: fingerprint(newt[k]) for k in d['text']['added']} == rec['addedTexts']
    assert {k: fingerprint(newt[k]) for k in d['text']['changed']} == rec['movedTexts']
    for k in d['text']['changed']:  # J701 legends and the TP803 marker: position only
        assert norm(without(texts(a)[k], {'at'})) == norm(without(newt[k], {'at'}))
    assert d['footprints']['removed'] == []
    assert set(d['footprints']['added']) == ADDED_REFS
    assert set(d['footprints']['changed']) <= SLOTTED | SILK_TRIMMED, d['footprints']['changed']
    for r in d['footprints']['added']:
        assert fingerprint(strip_uuid(newf[r])) == rec['addedFootprints'][r]
    for r in d['footprints']['changed']:
        assert fingerprint(strip_uuid(newf[r])) == rec['modifiedFootprints'][r]
        old, new = oldf[r], newf[r]
        if r in SLOTTED:  # only the hole's shape, size and offset change
            assert norm(without(old, {'pad'})) == norm(without(new, {'pad'}))
            assert [o(p, 'net') for p in c(old, 'pad')] == [o(p, 'net') for p in c(new, 'pad')]
        else:  # silkscreen-only trims
            keep = lambda f: [x for x in f if not (isinstance(x, list) and x and x[0] in
                                                   ('fp_line', 'fp_rect', 'fp_poly', 'fp_text', 'property'))]
            assert norm(keep(old)) == norm(keep(new)), r
            shapes = lambda f: [x for k in ('fp_line', 'fp_rect', 'fp_poly') for x in c(f, k)]
            old_shapes = [norm(strip_uuid(y)) for y in shapes(old)]
            assert all('Silk' in o(x, 'layer')[1] for x in shapes(new)
                       if norm(strip_uuid(x)) not in old_shapes), r
            new_shapes = [norm(strip_uuid(y)) for y in shapes(new)]
            assert all('Silk' in o(x, 'layer')[1] for x in shapes(old)
                       if norm(strip_uuid(x)) not in new_shapes), r
    j702 = newf['J702']
    assert 'dnp' in o(j702, 'attr'), 'J702 must stay DNP in the default HOTHMI build'
    pins = {p[1]: o(p, 'net')[-1] for p in c(j702, 'pad')}
    assert [pins[str(i)] for i in range(1, 9)] == [
        'LCD_ALT_VCC', 'GND', 'RPI_SPI_CS', 'LCD_RST', 'LCD_DC', 'LCD_MOSI', 'LCD_SCLK',
        'RPI_BACKLIGHT'], pins
    assert all(pins[str(i)].startswith('unconnected-') for i in range(9, 15))
    jp = {r: {p[1]: o(p, 'net')[-1] for p in c(newf[r], 'pad')} for r in ('JP701', 'JP702')}
    assert jp == {'JP701': {'1': 'LCD_3V3', '2': 'LCD_ALT_VCC'},
                  'JP702': {'1': '+5V', '2': 'LCD_ALT_VCC'}}, jp
    assert 'Bridged' in newf['JP701'][1] and 'Open' in newf['JP702'][1]
    for k in d['segment']['added']:
        n = segs[k]
        s, e = list(map(float, o(n, 'start')[1:])), list(map(float, o(n, 'end')[1:]))
        dx, dy = abs(s[0] - e[0]), abs(s[1] - e[1])
        assert math.hypot(dx, dy) > 0.000002, 'Zero-length track: ' + k
        assert min(dx, dy, abs(dx - dy)) <= 0.00000201, 'Non-45-degree track: ' + k
        assert o(n, 'layer')[1] != 'In1.Cu', 'In1.Cu stays an unbroken GND plane'

    out = ROOT / 'dist/lcd-module-2.8/ili9341-review'
    base = out / 'baseline'
    base.mkdir(parents=True, exist_ok=True)
    for path in K.glob('*.kicad_sch'):
        (base / path.name).write_bytes(git('kicad/' + path.name))
    before_nl, after_nl = netlist(base, out / 'before.xml'), netlist(K, out / 'after.xml')
    assert before_nl == after_nl, 'Existing schematic circuitry changed'

    report = {
        'passed': True, 'revision': rec['revision'],
        'boardSha256': hashlib.sha256(PCB.read_bytes()).hexdigest(),
        'baselineCommit': BASELINE, 'addedFootprints': sorted(ADDED_REFS),
        'modifiedFootprints': d['footprints']['changed'],
        'removedSegments': len(rec['removedSegments']), 'addedSegments': len(rec['addedSegments']),
        'addedVias': len(rec['addedVias']), 'innerLayerUse': 'In2.Cu only; In1.Cu untouched',
        'qualification': 'Source geometry, netlist and recorded-edit checks; run native '
                         'ERC/DRC separately. ILI9341 module fit and powered operation are '
                         'not qualified.',
    }
    (V / 'ili9341-socket-audit.json').write_text(json.dumps(report, indent=2) + '\n')
    config = V / 'jlc-placement-corrections.json'
    cfg = json.loads(config.read_text())
    cfg['boardSha256'] = report['boardSha256']
    cfg['ili9341Socket'] = {'audit': 'ili9341-socket-audit.json', 'auditSha256': hashlib.sha256(
        (V / 'ili9341-socket-audit.json').read_bytes()).hexdigest()}
    config.write_text(json.dumps(cfg, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--record', action='store_true')
    record() if ap.parse_args().record else verify()
