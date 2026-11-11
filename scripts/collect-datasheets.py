#!/usr/bin/env python3
"""Collect public supplier PDFs and index coverage of the current factory BOM.

Keep historical originals intact. Never persist or print temporary signed URLs.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import urllib.request
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT/'datasheets'
VARIANT = ROOT/'hardware'
FILES = {
    'C15850':'Samsung-CL21A106KAYNNNE-spec.pdf',
    'C19077498':'C19077498-current.pdf',
    'C2689642':'CK-PTS636.pdf',
    'C2906768':'Keystone-5015.pdf',
    'C51118':'Diodes-AP2112.pdf',
    'C5246813':'GCT-USB4125.pdf',
    'C5417011':'C5417011.pdf',
    'C633309':'SEC1210-DS00001561D.pdf',
}
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--fetch', action='store_true')
args = parser.parse_args()
rows = list(csv.DictReader((VARIANT/'manufacturing/bom-jlcpcb.csv').open()))
codes = {r['LCSC Part #'] for r in rows}
assert len(rows) == len(codes) == 18
assert sum(len(r['Designator'].split(',')) for r in rows) == 44
for code in codes:
    FILES.setdefault(code, code+'.pdf')
manifest_path = DEST/'manifest.json'
manifest = json.loads(manifest_path.read_text())
records = {r['file']:r for r in manifest['files']}
missing = sorted(c for c in codes if not (DEST/FILES[c]).is_file())
if args.fetch and missing:
    # A fresh page is needed: signed links in old snapshots expire in 30 min.
    catalog_path = ROOT/'.tools/electrical-review/datasheet-catalog.json'
    subprocess.run([sys.executable, str(ROOT/'scripts/refresh-jlc.py'), '--only', *missing,
                    '--output', str(catalog_path)], check=True)
    catalog = {p['code']:p for p in json.loads(catalog_path.read_text())['parts']}
    for code in missing:
        row = next(r for r in rows if r['LCSC Part #'] == code)
        mpn = row['Comment'].split('; ')[-1]
        assert catalog[code]['componentModelEn'] == mpn, (code,'BOM/catalog identity mismatch')
        text = (ROOT/'reference/research/catalog-cache'/f'{code}.html').read_text()
        chunks = []
        for match in re.finditer(r'self\.__next_f\.push\((\[.*?\])\)</script>', text, re.S):
            try:
                chunks.extend(s for s in json.loads(match[1]) if isinstance(s,str))
            except json.JSONDecodeError:
                pass
        urls = re.findall(r'https://jlc-prod-smt[^\s"<>]+?x-oss-signature=[0-9a-f]{64}', ''.join(chunks))
        urls = list(dict.fromkeys(u for u in urls if code+'.pdf' in u))
        failures = []
        for url in urls:
            try:
                data = urllib.request.urlopen(url, timeout=30).read()
                assert data.startswith(b'%PDF'), 'Not PDF bytes'
                import io
                count = len(PdfReader(io.BytesIO(data)).pages)
                assert count > 0
                (DEST/FILES[code]).write_bytes(data)
                records[FILES[code]] = {'file':FILES[code], 'source':catalog[code]['url'],
                    'catalogCode':code, 'catalogMpn':mpn, 'pages':count,
                    'sha256':hashlib.sha256(data).hexdigest(),
                    'scope':'Supplier-linked exact-product PDF; document may cover a part family'}
                manifest['files'] = sorted(records.values(), key=lambda r:r['file'])
                manifest_path.write_text(json.dumps(manifest, indent=2)+'\n')
                print(code, 'PDF saved;', count, 'pages')
                break
            except Exception as error:
                # Exception strings may contain the signed URL. Retain type only.
                failures.append(type(error).__name__)
        else:
            raise RuntimeError(f'{code}: no usable fresh PDF ({",".join(failures)})')
    manifest['files'] = sorted(records.values(), key=lambda r:r['file'])
    manifest_path.write_text(json.dumps(manifest, indent=2)+'\n')

coverage = []
for row in rows:
    code = row['LCSC Part #']
    path = DEST/FILES[code]
    assert path.is_file(), f'Missing {code}: run mise run datasheets:fetch'
    assert FILES[code] in records, f'Untracked provenance for {path.name}'
    assert path.read_bytes().startswith(b'%PDF'), f'LFS pointer/unhydrated PDF: {path.name}'
    assert hashlib.sha256(path.read_bytes()).hexdigest() == records[path.name]['sha256'], path.name
    assert len(PdfReader(path).pages) > 0
    coverage.append({'lcsc':code, 'mpn':row['Comment'].split('; ')[-1],
                     'references':row['Designator'].split(','), 'document':path.name})
for name, record in records.items():
    assert hashlib.sha256((DEST/name).read_bytes()).hexdigest() == record['sha256'], name
report = {'bomSha256':hashlib.sha256((VARIANT/'manufacturing/bom-jlcpcb.csv').read_bytes()).hexdigest(),
          'factorySkus':18,'factoryPlacements':44,'coverage':coverage,
          'qualification':'Local document coverage only; not electrical or manufacturer qualification'}
(DEST/'bom-coverage.json').write_text(json.dumps(report,indent=2)+'\n')
lines = ['# Hardware datasheets', '',
         'Local PDF references cover all **18 SKUs / 44 placements** in the current',
         '0.0.12-dev factory BOM, plus the host/LCD modules and historical alternatives.',
         '`manifest.json` records original paths or public source pages and SHA-256;',
         '`bom-coverage.json` binds the table below to the exact BOM bytes.',
         'Some documents cover a component family; coverage is not physical qualification.',
         'The original snapshots in `reference/pdfs/` are preserved. PDFs use Git LFS.', '',
         'Run `mise run datasheets:check` to validate the collection, or',
         '`mise run datasheets:fetch` to obtain missing current-BOM PDFs.', '',
         '## Current factory BOM', '', '| Component | LCSC | References | Local document |',
         '|---|---|---|---|']
for row in coverage:
    name = row['document']
    lines.append(f"| {row['mpn']} | {row['lcsc']} | {', '.join(row['references'])} | [{name}]({name}) |")
lines += ['', '## Modules, supporting data and retained alternatives', '',
          'These are additional references, not automatic substitutes for the selected parts.', '']
used = {r['document'] for r in coverage}
for name in sorted(set(records)-used):
    lines.append(f'- [{name}]({name})')
lines += ['', 'Keystone primary reference: [manufacturer drawing](https://www.keyelco.com/product-pdf.cfm?p=1353).', '']
(DEST/'README.md').write_text('\n'.join(lines))
print(f'Checked {len(records)} PDFs; local references cover all 18 current factory SKUs.')
