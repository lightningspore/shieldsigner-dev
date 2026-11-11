"""Trace the official monochrome logo into native PCB silkscreen polygons.

Run with mise's pcb:denver task. Artwork only: no footprints, copper, nets,
mask, paste, board edges or schematic fields are modified.
"""
from pathlib import Path
import hashlib
import json
import runpy
import subprocess
import uuid

import cv2
import mapbox_earcut
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
VARIANT = ROOT / 'hardware'
BOARD = VARIANT / 'kicad/SeedSigner-Plus-smartcard-pico.kicad_pcb'
ASSETS = ROOT / 'assets/branding'
BASE_SHA = 'b4eb7a7cef3f026bfc332a19980727a165de9ea826e4eb25dcc68e2c458004b7'
BASE_COMMIT = 'd290b7032629723223d8cab7984255b089a9657f'
SOURCE_SHA = '32f6dd6ce4ad7032ae67440e622f2c078db1dad4bd4621566663dda040a13b63'
SOURCE_URL = 'https://denver.space/assets/branding/Logos/TheSpace_Logos_Full_3.webp'
WIDTH_MM = 30
CENTER = (184.5, 106.5)


def uid(value):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'shieldsigner-denver-space:' + value))


def main():
    source = ASSETS / 'denver-space-source.webp'
    assert hashlib.sha256(source.read_bytes()).hexdigest() == SOURCE_SHA, 'Official source artwork differs'
    image = np.asarray(Image.open(source).convert('RGB'))
    mask = np.where(image.max(axis=2) < 100, 255, 0).astype(np.uint8)
    x, y, width, height = cv2.boundingRect(cv2.findNonZero(mask))
    mask = mask[y:y + height, x:x + width]
    crop = [x, y, width, height]
    mask = cv2.resize(mask, (1500, round(height * 1500 / width)), interpolation=cv2.INTER_AREA)
    mask = np.where(mask > 127, 255, 0).astype(np.uint8)
    height, width = mask.shape
    # Drop sub-printable orbit hairlines. Preserve the main lettering/ring.
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN,
                            cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))
    contours, hierarchy = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    triangles = []
    outlines = []
    for index, contour in enumerate(contours):
        if hierarchy[0][index][3] != -1 or cv2.contourArea(contour) < 30:
            continue
        rings = [cv2.approxPolyDP(contour, .6, True).reshape(-1, 2)]
        child = hierarchy[0][index][2]
        while child != -1:
            rings.append(cv2.approxPolyDP(contours[child], .6, True).reshape(-1, 2))
            child = hierarchy[0][child][0]
        vertices = np.concatenate(rings).astype(np.float64)
        ends = np.cumsum([len(ring) for ring in rings]).astype(np.uint32)
        indices = mapbox_earcut.triangulate_float64(vertices, ends)
        triangles.extend(vertices[indices].reshape(-1, 3, 2).tolist())
        outlines.append(rings)
    scale = WIDTH_MM / width
    height_mm = height * scale
    # SVG is a normal-reading reference; back-side PCB geometry is X-mirrored.
    paths = []
    for rings in outlines:
        paths.append(' '.join('M ' + ' L '.join(f'{a * scale:.5f},{b * scale:.5f}' for a, b in ring) + ' Z' for ring in rings))
    (ASSETS / 'denver-space-silkscreen.svg').write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH_MM} {height_mm:.5f}">\n'
        + '\n'.join(f'<path fill="black" fill-rule="evenodd" d="{path}"/>' for path in paths) + '\n</svg>\n')
    current = BOARD.read_text()
    baseline = ROOT / '.tools/pcb-branding/baseline.kicad_pcb'
    if not baseline.exists():
        text = subprocess.check_output(['git', 'show', f'{BASE_COMMIT}:{BOARD.relative_to(ROOT)}'],
                                       cwd=ROOT, text=True)
        assert hashlib.sha256(text.encode()).hexdigest() == BASE_SHA, 'Wrong Git artwork baseline'
        baseline.parent.mkdir(parents=True, exist_ok=True)
        baseline.write_text(text)
    else:
        text = baseline.read_text()
    assert hashlib.sha256(text.encode()).hexdigest() == BASE_SHA, 'Wrong artwork baseline'
    sx = runpy.run_path(str(ROOT / 'scripts/kicad-sexpr.py'))
    revision = next(raw for _, _, raw in sx['expressions'](text)
                    if raw.startswith('(gr_text "2.8 SPI  /  0.0.7-dev"'))
    text = text.replace(revision, revision.replace('0.0.7-dev', '0.0.9-dev'), 1)
    graphics = []
    for index, triangle in enumerate(triangles):
        points = ' '.join(f'(xy {CENTER[0] - (a - width / 2) * scale:.6f} '
                          f'{CENTER[1] + (b - height / 2) * scale:.6f})' for a, b in triangle)
        graphics.append(f'(gr_poly (pts {points}) (stroke (width 0) (type solid)) '
                        f'(fill solid) (layer "B.SilkS") (uuid "{uid(str(index))}"))')
    graphics.append(f'(gr_text "denver.space" (at 186 114.2 0) (layer "B.SilkS") '
                    f'(uuid "{uid("name")}") (effects (font (size 1.25 1.25) (thickness 0.2)) '
                    '(justify mirror)))')
    # Repeatable updates may replace only the exact baseline or our prior output.
    if hashlib.sha256(current.encode()).hexdigest() != BASE_SHA:
        assert uid('name') in current, 'Board changed independently; review before applying'
        prior = json.loads((VARIANT / 'branding.json').read_text())
        assert hashlib.sha256(current.encode()).hexdigest() == prior['boardSha256'], 'Board changed since branding; refusing overwrite'
        old = sx['parse'](current)
        base = sx['parse'](text)
        protected = lambda tree: [n for n in tree if not (isinstance(n, list) and n[0].startswith('gr_')
                               and sx['one'](n, 'layer')[1:] in [['F.SilkS'], ['B.SilkS']])]
        assert protected(old) == protected(base), 'Independent non-silkscreen edit; refusing overwrite'
    BOARD.write_text(text.rstrip()[:-1] + '\n' + '\n'.join(graphics) + '\n)\n')
    report = dict(schema=1, revision='0.0.9-dev', sourceUrl=SOURCE_URL,
                  sourceSha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                  sourceCropPixels=crop, traceWidthPixels=1500, widthMm=WIDTH_MM,
                  heightMm=height_mm, centerMm=list(CENTER), side='B.SilkS',
                  polygons=len(triangles), name='denver.space', nameHeightMm=1.25,
                  nameStrokeMm=.2, baselineBoardSha256=BASE_SHA,
                  boardSha256=hashlib.sha256(BOARD.read_bytes()).hexdigest(),
                  conversion='Monochrome threshold; trace at1500px width; 9px(0.18mm) morphology removes sub-printable hairlines; '
                             '0.6px contour tolerance; native filled triangles preserve holes; '
                             'X-mirrored geometry reads normally from board bottom',
                  rights='Logo belongs to The Space; source retained with attribution; no relicensing claim')
    (VARIANT / 'branding.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
