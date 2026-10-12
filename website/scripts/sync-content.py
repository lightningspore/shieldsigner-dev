"""Package explicit public docs/assets; never copy private ingestion or research data."""
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
"docs/os-build-benchmark.json", "docs/pdf-references.json", "docs/drc-assembly-exceptions.json",
"manufacturing/jlcpcb/bom-carrier-jlcpcb.csv", "manufacturing/jlcpcb/cpl-carrier-jlcpcb.csv"]
# Hardware-only review bundle produced by review:build; no firmware/private archives.
for name in ["shieldsigner-luckfox-kicad.zip", "shieldsigner-carrier-gerbers.zip", "pcb-top.svg", "pcb-bottom.svg"]:
    source = ROOT / "dist/kicad" / name
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
manifest = [{"name": str(p.relative_to(public)), "size": p.stat().st_size, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(public.rglob("*")) if p.is_file()]
(public / "manifest.json").write_text(json.dumps(manifest, indent=2)+"\n")
print(f"Published allowlist: {len(GUIDES)} guides, {len(manifest)} public files; no private Telegram/session data.")
