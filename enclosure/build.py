"""Render vendor-neutral case meshes using native OpenSCAD, then check them."""
import os
from pathlib import Path
import shutil
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
out = root / "dist/enclosure"
out.mkdir(parents=True, exist_ok=True)
scad = os.environ.get("OPENSCAD") or shutil.which("openscad")
if not scad:
    candidate = Path("/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD")
    if candidate.exists():
        scad = str(candidate)
if not scad:
    raise SystemExit("Install OpenSCAD or set OPENSCAD to its executable")
for part in ("base", "bezel", "button", "retainer-left", "retainer-right", "camera-tray", "camera-clamp", "service-cover", "button-fit-coupon"):
    subprocess.run([scad, "-o", str(out / f"{part}.stl"), "-D",
                    f'render_part="{part}"', str(root / "enclosure/case.scad")], check=True)
subprocess.run([sys.executable, str(root / "enclosure/check_meshes.py")], check=True)
subprocess.run([sys.executable, str(root / "enclosure/check_assembly.py")], check=True)
subprocess.run([sys.executable, str(root / "enclosure/check_access.py")], check=True)
subprocess.run([scad, "-o", str(out / "assembly-draft.png"),
                "--imgsize=1400,900", "--viewall", "--autocenter", "-D",
                'render_part="assembly"', str(root / "enclosure/case.scad")], check=True)
