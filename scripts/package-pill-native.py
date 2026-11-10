#!/usr/bin/env python3
"""Bundle the independently compilable tscircuit source and review outputs."""
import json,zipfile
from pathlib import Path
root=Path(__file__).resolve().parents[1]
dest=root/'dist/pill-native/ShieldSigner-pill-tscircuit-source.zip'
files=[root/'src/PillCarrier.tsx',root/'package.json',root/'bun.lock',root/'tsconfig.json',root/'LICENSE']
files += [p for p in (root/'src/pill').rglob('*') if p.is_file()]
files += [root/'scripts'/p for p in ['build-pill.tsx','pill-schema.ts','render-pill-native.mjs','dev-pill.ts']]
with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED)as z:
 for p in files:z.write(p,p.relative_to(root))
 z.writestr('mise.toml','''[tools]
bun="1.2.21"
[tasks.setup]
run="bun install --frozen-lockfile"
[tasks.build]
run=["bun scripts/build-pill.tsx", "bun scripts/render-pill-native.mjs"]
[tasks.dev]
run="bun scripts/dev-pill.ts"
''')
 z.writestr('PORT.json',json.dumps({'entry':'src/PillCarrier.tsx','build':'mise run setup && mise run build','preview':'mise run dev','architecture':'Native tscircuit source, ordinary component/footprint primitives, local GLB assets; no KiCad files or generated geometry snapshots needed.','qualification':'Experimental software-validated port; hardware not qualified.'},indent=2))
print(dest.relative_to(root))
