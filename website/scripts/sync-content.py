"""Package explicit public docs/assets; never copy private ingestion or research data."""
import urllib.request
import csv
from zipfile import ZipFile, ZIP_DEFLATED
import runpy
import subprocess
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "website"
sys.path.insert(0, str(SITE))
from knowledge.catalog import GUIDES
content = SITE / "content"
public = SITE / "public"
for directory in [content, public]:
    if directory.exists(): shutil.rmtree(directory)
    directory.mkdir()
url_map = {str((ROOT / source).resolve()): f"/guides/{slug}/" for slug, source, *_ in GUIDES}
files = [*(f"reference/pdfs/{p.name}" for p in sorted((ROOT / "reference/pdfs").glob("*.pdf"))),
"docs/workflows.json", "docs/system-parts.json", "docs/card-workflows.json", "docs/os-build-benchmark.json", "docs/pdf-references.json", "docs/drc-assembly-exceptions.json",
"manufacturing/jlcpcb/bom-carrier-jlcpcb.csv", "manufacturing/jlcpcb/cpl-carrier-jlcpcb.csv"]
# Hardware-only review bundle produced by review:build; no firmware/private archives.
for name in ["shieldsigner-luckfox-kicad.zip", "shieldsigner-carrier-gerbers.zip", "pcb-top.svg", "pcb-bottom.svg", "schematic.pdf"]:
    source = ROOT / "dist/kicad" / name
    if not source.exists() and name in {'shieldsigner-carrier-gerbers.zip','shieldsigner-luckfox-kicad.zip','schematic.pdf'}:
        artifact = next(a for a in json.loads((ROOT/'assets/downloads.json').read_text())['assets'] if a['name']==name)
        cache = ROOT/'.tools/website-downloads'/artifact['sha256']/name
        if not cache.exists():
            cache.parent.mkdir(parents=True,exist_ok=True)
            request=urllib.request.Request(artifact['url'],headers={'User-Agent':'ShieldSigner-content-builder'})
            with urllib.request.urlopen(request,timeout=60) as response: payload=response.read()
            if hashlib.sha256(payload).hexdigest()!=artifact['sha256']: raise ValueError('Release asset checksum mismatch: '+name)
            cache.write_bytes(payload)
        if hashlib.sha256(cache.read_bytes()).hexdigest()!=artifact['sha256']: raise ValueError('Cached release asset changed: '+name)
        source=cache
    if not source.exists() and name.endswith(".svg"):
        source = ROOT / "assets" / name
    if source.exists():
        shutil.copyfile(source, public / name)
        url_map[str(source.resolve())] = f"/files/{name}"
for name in files:
    source = ROOT / name
    if not source.is_file(): raise RuntimeError(f"Missing public asset: {name}")
    target = public / name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    url_map[str(source.resolve())] = f"/files/{name}"
# Native files are downloadable individually, preserving hierarchy/library assets.
for source in (ROOT / "kicad").rglob("*"):
    if source.is_file() and source.suffix in {".kicad_pcb", ".kicad_sch", ".kicad_pro", ".kicad_sym", ".kicad_mod"} or source.is_file() and source.name in {"fp-lib-table", "sym-lib-table"}:
        name = str(source.relative_to(ROOT))
        target = public / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        url_map[str(source.resolve())] = f"/files/{name}"
# Explicit separate-variant allowlist; never mix its BOM/files into the standard order kit.
variant = ROOT / "variants/lcd-module-2.8"
for source in variant.rglob("*"):
    if source.is_file() and (source.suffix in {".kicad_pcb", ".kicad_sch", ".kicad_pro", ".kicad_sym", ".kicad_mod", ".svg", ".json", ".csv", ".md", ".png", ".step"} or source.name in {"fp-lib-table", "sym-lib-table"}):
        name = str(source.relative_to(ROOT))
        target = public / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        url_map[str(source.resolve())] = f"/files/{name}" + (f"?v={hashlib.sha256(source.read_bytes()).hexdigest()[:12]}" if source.suffix == '.png' else '')
# Release-pinned modular outputs remain reproducible in a fresh public checkout.
modular_manifest = json.loads((ROOT / "assets/modular-downloads.json").read_text())
board = ROOT / "variants/lcd-module-2.8/kicad/SeedSigner-Plus-smartcard-pico.kicad_pcb"
if hashlib.sha256(board.read_bytes()).hexdigest() != modular_manifest["boardSha256"]:
    raise RuntimeError("Modular hardware changed; rebuild and publish matching quote/review assets first")
for artifact in modular_manifest["assets"]:
    source = ROOT / "dist/lcd-module-2.8" / artifact["name"]
    if not source.exists():
        source = ROOT / ".tools/website-downloads" / artifact["sha256"] / artifact["name"]
        if not source.exists():
            source.parent.mkdir(parents=True, exist_ok=True)
            request = urllib.request.Request(artifact["url"], headers={"User-Agent":"ShieldSigner-content-builder"})
            with urllib.request.urlopen(request, timeout=60) as response: payload=response.read()
            if hashlib.sha256(payload).hexdigest()!=artifact["sha256"]: raise ValueError("Modular asset checksum mismatch")
            source.write_bytes(payload)
    if hashlib.sha256(source.read_bytes()).hexdigest()!=artifact["sha256"]: raise ValueError("Modular asset changed: "+artifact["name"])
    shutil.copyfile(source, public / artifact["name"])
repo_url = "https://github.com/lightningspore/shieldsigner-dev/tree/main/"
for slug, name, *_ in GUIDES:
    source = ROOT / name
    def link(match):
        label, dest = match.groups()
        if re.match(r"^(?:https?://|mailto:|#|/)", dest): return match.group(0)
        dest_path, sep, anchor = dest.partition("#")
        resolved = str((source.parent / dest_path).resolve())
        url = url_map.get(resolved)
        if url is None:
            try: relative = str(Path(resolved).relative_to(ROOT))
            except ValueError: return f"[{label}](https://github.com/lightningspore/shieldsigner-dev)"
            url = repo_url + relative
        return f"[{label}]({url}{'#' + anchor if sep else ''})"
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", link, source.read_text())
    # Local operator/server details do not belong on the public project site.
    text = re.sub(r"(?:192\.168\.\d+\.\d+|100\.(?:\d+\.){2}\d+)", "private-host", text)
    text = re.sub(r"[a-zA-Z0-9-]+\.tail[a-zA-Z0-9]+\.ts\.net", "private-tailnet-host", text)
    text = re.sub(r"http://(?:localhost|127\.0\.0\.1):\d+[^\s)]*", "/downloads/", text)
    (content / f"{slug}.md").write_text(text)
version=json.loads((SITE/'version.json').read_text())
version['revision']=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip()
version['dirty']=bool(subprocess.check_output(['git','-C',str(ROOT),'status','--porcelain'],text=True).strip())
(content/'site-version.json').write_text(json.dumps(version,indent=2)+'\n')
# The task interface consumes authoritative data packaged into the same release.
for name in ['workflows', 'system-parts', 'card-workflows']:
    shutil.copyfile(ROOT / 'docs' / f'{name}.json', content / f'{name}.json')
values=runpy.run_path(str(ROOT/'scripts/part-values.py'))
rows = []
with (ROOT / 'manufacturing/jlcpcb/bom-carrier-jlcpcb.csv').open() as file:
    bom = list(csv.DictReader(file))
catalog = {p['code']: p for p in json.loads((ROOT/'docs/jlc-catalog.json').read_text())['parts']}
for row in bom:
    code = row['LCSC Part #']; part = catalog[code]
    rows.append({'refs': row['Designator'], 'qty': len(row['Designator'].split(',')), 'code': code,
                 'value': values['nominal'](row['Comment'].split(';')[0],row['Designator'].split(',')),
                 'ratings': values['ratings'](part,row['Designator'].split(',')), 'mpn': part['componentModelEn'],
                 'manufacturer': part['componentBrandEn'], 'package': row['Footprint'],
                 'source': part['url'], 'checkedAt': part['checkedAt'][:10],
                 'library': 'Basic' if part['componentLibraryType']=='base' else 'Extended'})
assert len(rows)==21 and sum(r['qty'] for r in rows)==43
caps = next(r for r in rows if r['code']=='C28323')
assert {'C602','C603','C604'}==set(caps['refs'].split(',')), '1 uF BOM correction missing'
(content/'carrier-parts.json').write_text(json.dumps(rows,indent=2)+'\n')
modular_catalog = {p['code']: p for p in json.loads((variant/'jlc-catalog.json').read_text())['parts']}
modular_rows = []
with (variant/'manufacturing/bom-jlcpcb.csv').open() as file:
    for row in csv.DictReader(file):
        code = row['LCSC Part #']; part = modular_catalog[code]; refs = row['Designator'].split(',')
        modular_rows.append({'refs':row['Designator'], 'qty':len(refs), 'code':code,
            'value':row['Comment'].split(';')[0], 'ratings':values['ratings'](part,refs),
            'mpn':part['componentModelEn'], 'manufacturer':part['componentBrandEn'],
            'package':row['Footprint'], 'source':part['url'], 'checkedAt':part['checkedAt'][:10],
            'library':'Basic' if part['componentLibraryType']=='base' else 'Extended'})
assert len(modular_rows)==17 and sum(p['qty'] for p in modular_rows)==35
(content/'modular-carrier-parts.json').write_text(json.dumps(modular_rows,indent=2)+'\n')
shutil.copyfile(variant/'system-parts.json', content/'modular-system-parts.json')
mechanics = json.loads((variant/'mechanical.json').read_text())
(content/'modular-pcb-spec.json').write_text(json.dumps({'width':mechanics['board']['width'],
    'height':mechanics['board']['height'], 'thickness':1.6, 'layers':2,
    'boardSha256':modular_manifest['boardSha256']},indent=2)+'\n')
readiness = json.loads((ROOT/'manufacturing/jlcpcb/readiness.json').read_text())
board_sha = hashlib.sha256((ROOT/'kicad/SeedSigner-Plus-smartcard-pico.kicad_pcb').read_bytes()).hexdigest()
assert readiness['boardSha256']==board_sha, 'BOM/CPL readiness belongs to another board revision'
geometry=json.loads((ROOT/'src/generated/reference-board.json').read_text())
assert geometry['source']['sha256']==board_sha, 'Regenerate geometry before publishing'
(content/'pcb-spec.json').write_text(json.dumps({'width':round(geometry['width'],2),'height':round(geometry['height'],2),'thickness':1.6,'layers':2,'boardSha256':board_sha},indent=2)+'\n')
order_files = ['shieldsigner-carrier-gerbers.zip', 'manufacturing/jlcpcb/bom-carrier-jlcpcb.csv', 'manufacturing/jlcpcb/cpl-carrier-jlcpcb.csv']
if all((public/name).is_file() for name in order_files):
    with ZipFile(public/'shieldsigner-jlcpcb-order.zip','w',ZIP_DEFLATED) as bundle:
        for name in order_files: bundle.write(public/name,arcname=Path(name).name)
        bundle.writestr('README.txt','ShieldSigner carrier WITHOUT Luckfox: upload Gerber ZIP, then BOM/CPL for PCBA.\n43 fitted pieces / 21 catalog lines. J302, R404 and R408 DNP.\nC603/C604 are 1 uF C28323. UR2 reader config required.\nReview only: paste/rotation/LCD/enclosure/bench qualification pending.\n')
        bundle.writestr('manifest.json',json.dumps({'boardSha256':board_sha,'releaseStatus':'review_only','files':[{'name':name,'sha256':hashlib.sha256((public/name).read_bytes()).hexdigest()} for name in order_files]},indent=2))
manifest = [{"name": str(p.relative_to(public)), "size": p.stat().st_size, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(public.rglob("*")) if p.is_file()]
(public / "manifest.json").write_text(json.dumps(manifest, indent=2)+"\n")
print(f"Published allowlist: {len(GUIDES)} guides, {len(manifest)} public files; no private Telegram/session data.")
