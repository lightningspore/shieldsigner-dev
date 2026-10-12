#!/usr/bin/env python3
# /// script
# dependencies = ["markdown>=3.7,<4"]
# ///
"""Build the local review page and a hardware-only source/review bundle."""
import html,json,re
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import markdown
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'dist/kicad';OUT.mkdir(parents=True,exist_ok=True)
for source in (ROOT/'reference/pdfs').glob('*.pdf'):
 target=OUT/source.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True)
 target.write_bytes(source.read_bytes())
STYLE='body{margin:0;background:#eef2f6;color:#172334;font:16px system-ui}main{max-width:1200px;margin:auto;padding:28px;line-height:1.6}a{color:#1457a5}table{border-collapse:collapse;width:100%;display:block;overflow:auto}td,th{padding:8px;border:1px solid #cad4df;text-align:left;vertical-align:top}pre{padding:16px;background:#172334;color:white;overflow:auto}code{overflow-wrap:anywhere}img{max-width:100%}.status{padding:18px;background:#fff2d1;border-radius:10px}nav{display:flex;gap:16px;flex-wrap:wrap;margin:24px 0}'
for source in [ROOT/'README.md',ROOT/'KICAD.md',*(ROOT/'docs').glob('*.md')]:
 relative=source.relative_to(ROOT);target=OUT/relative.with_suffix('.html');target.parent.mkdir(parents=True,exist_ok=True)
 text=source.read_text()
 for match in re.finditer(r'\]\(([^)]+\.md)(#[^)]*)?\)',text):
  url=match[1]
  if not url.startswith(('http:','https:')):assert (source.parent/url).exists(),f'Broken documentation link: {source}: {url}'
 text=re.sub(r'(\]\()([^)]*?)\.md(?=[#)])',r'\1\2.html',text)
 body=markdown.markdown(text,extensions=['tables','fenced_code','toc'])
 target.write_text(f'<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(source.stem)}</title><style>{STYLE}</style><main><a href="'+('../' if relative.parts[0]=='docs' else '')+f'board.html">Board review</a>{body}</main></html>')
for name in ['bom-carrier-jlcpcb.csv','cpl-carrier-jlcpcb.csv','population-audit.csv','readiness.json']:
 (OUT/name).write_bytes((ROOT/'manufacturing/jlcpcb'/name).read_bytes())
status=json.loads((OUT/'checks-summary.json').read_text())
board=f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ShieldSigner native KiCad review</title><style>{STYLE}</style><main><h1>ShieldSigner Luckfox Plus — native KiCad</h1><p>43 fitted carrier pieces · 21 catalog part lines · optional Luckfox host. Exact catalog identities and dated public availability are documented.</p><p class="status">Review package: {status['erc']['bySeverity'].get('error',0)} ERC errors; {status['drc']['unconnectedItems']} unconnected PCB items; {status['drc']['schematicParityIssues']} parity issues. <strong>{status['drc']['bySeverity'].get('error',0)} active layout DRC errors; {status['drc'].get('excluded',0)} documented DNP strap exceptions.</strong> Stock is not reserved; footprints/placement and bench tests remain unqualified.</p><nav><a href="docs/ELECTRICAL-REVIEW.html">1. Electrical review</a><a href="docs/BOM.html">2. BOM / JLCPCB plan</a><a href="docs/BRINGUP.html">3. Bring-up guide</a><a href="docs/SMARTCARDS.html">4. Smartcard choices</a></nav><nav><a href="docs/BOM-TABLE.html">Sourcing table</a><a href="docs/COMPONENTS.html">All component explanations</a><a href="schematic.pdf">Schematic PDF</a><a href="docs/OS-BUILD.html">OS build guide</a><a href="docs/PDF-REFERENCES.html">Datasheets</a><a href="shieldsigner-carrier-gerbers.zip">Gerbers and drills</a><a href="shieldsigner-luckfox-kicad.zip">Download review bundle</a></nav><nav><a href="bom-carrier-jlcpcb.csv">Carrier BOM CSV</a><a href="cpl-carrier-jlcpcb.csv">Carrier placement CSV</a><a href="population-audit.csv">Population audit</a><a href="readiness.json">Release status</a><a href="drc.json">DRC report</a></nav><h2>Top copper and silkscreen</h2><img src="pcb-top.svg" alt="Native top PCB"><h2>Bottom copper and silkscreen</h2><img src="pcb-bottom.svg" alt="Native bottom PCB"></main></html>'''
(OUT/'board.html').write_text(board)
with ZipFile(OUT/'shieldsigner-luckfox-kicad.zip','w',ZIP_DEFLATED) as archive:
 for folder in ['kicad','docs','scripts','manufacturing','reference','src']:
  for path in (ROOT/folder).rglob('*'):
   rel=path.relative_to(ROOT)
   if not path.is_file() or '__pycache__' in rel.parts or path.suffix in ['.lck','.kicad_prl'] or ('reference' in rel.parts and 'research' in rel.parts):continue
   archive.write(path,rel)
 for name in ['README.md','KICAD.md','LICENSE','TELEGRAM.md','mise.toml','package.json','bun.lock','tsconfig.json']:
  path=ROOT/name
  if path.exists():archive.write(path,path.relative_to(ROOT))
 for path in OUT.rglob('*'):
  if path.is_file() and path.suffix in ['.pdf','.svg','.json','.xml','.html','.csv']:archive.write(path,path.relative_to(ROOT))
 assert not any('tools/telegram/' in name or '.tools/' in name for name in archive.namelist())
print('Checked local Markdown links and refreshed readable review pages/BOM/CPL/bundle; private Telegram data excluded.')
