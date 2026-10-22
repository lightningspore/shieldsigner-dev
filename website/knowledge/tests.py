"""Validate the published static tree, links, hardware boundaries and downloads."""
import csv
import hashlib
from html.parser import HTMLParser
import io
import json
from pathlib import Path
import unittest
from urllib.parse import unquote, urljoin, urlsplit
from zipfile import ZipFile

from .catalog import GUIDES
from . import workflows

ROOT=Path(__file__).resolve().parents[1]
DIST=ROOT/'dist'

class Links(HTMLParser):
    def __init__(self, html):
        super().__init__(); self.urls=[]; self.ids=set(); self.feed(html)
    def handle_starttag(self, tag, attrs):
        attrs=dict(attrs)
        if attrs.get('id'): self.ids.add(attrs['id'])
        for attribute in ['href','src']:
            if attrs.get(attribute): self.urls.append(attrs[attribute])

def page(url):
    return (DIST/url.lstrip('/')/'index.html').read_text()

class StaticSiteTests(unittest.TestCase):
    def test_all_guides_tasks_and_card_pages_exist(self):
        paths=['/','/guides/','/downloads/',*[f'/guides/{g[0]}/' for g in GUIDES],
               *[f"/build/{t['slug']}/" for t in workflows.tasks()],
               *[f'/build/cards/{c}/' for c in ['seedkeeper','satochip','diy']]]
        for url in paths:
            html=page(url)
            self.assertIn(f'https://shieldsigner.dev{url}',html)
            self.assertIn('<main id="main">',html)
            self.assertNotIn('hx-',html)
        self.assertIn('initialize and export',page('/build/cards/satochip/'))
        self.assertIn('install an applet',page('/build/cards/diy/'))
        self.assertIn('Build a ShieldSigner.',page('/'))

    def test_static_links_and_workflow_anchors(self):
        for source in DIST.rglob('index.html'):
            url='/'+str(source.parent.relative_to(DIST))+'/' if source.parent!=DIST else '/'
            links=Links(source.read_text())
            for href in links.urls:
                dest=urlsplit(urljoin(url,href))
                if dest.scheme or dest.netloc: continue
                path=unquote(dest.path)
                target=DIST/path.lstrip('/')
                if path.endswith('/'): target=target/'index.html'
                self.assertTrue(target.is_file(),f'{url} → {href}')
                if dest.fragment and url.startswith('/build/') and target.suffix=='.html':
                    self.assertIn(unquote(dest.fragment),Links(target.read_text()).ids,f'{url} → {href}')

    def test_download_manifest_and_private_boundary(self):
        manifest=json.loads((DIST/'files/manifest.json').read_text())
        expected={p['name'] for p in manifest}|{'manifest.json'}
        actual={str(p.relative_to(DIST/'files')) for p in (DIST/'files').rglob('*') if p.is_file()}
        self.assertEqual(actual,expected)
        for item in manifest:
            path=DIST/'files'/item['name']
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),item['sha256'])
        for path in DIST.rglob('*'):
            self.assertNotIn(path.suffix,{'.session','.sqlite3','.env','.py','.toml','.lock'})
            self.assertNotIn('private',path.parts)
        self.assertFalse((DIST/'manage.py').exists())

    def test_both_order_bundles_match_native_populations(self):
        for name, count, lines, bom_name, cpl_name in [
            ('shieldsigner-jlcpcb-order.zip',43,21,'bom-carrier-jlcpcb.csv','cpl-carrier-jlcpcb.csv'),
            ('shieldsigner-modular-order.zip',35,17,'bom-jlcpcb.csv','cpl-jlcpcb.csv')]:
            with ZipFile(DIST/'files'/name) as archive:
                bom=list(csv.DictReader(io.StringIO(archive.read(bom_name).decode())))
                cpl=list(csv.DictReader(io.StringIO(archive.read(cpl_name).decode())))
                refs={ref for part in bom for ref in part['Designator'].split(',')}
                self.assertEqual((len(refs),len(bom)),(count,lines))
                self.assertEqual(refs,{p['Designator'] for p in cpl})
                self.assertFalse(refs & {'U202','J701','J302','R404','R408'})
                caps=next(p for p in bom if p['LCSC Part #']=='C28323')
                self.assertEqual(set(caps['Designator'].split(',')),{'C602','C603','C604'})
                if count==35:
                    readiness=json.loads(archive.read('readiness.json'))
                    board=DIST/'files/variants/lcd-module-2.8/kicad/SeedSigner-Plus-smartcard-pico.kicad_pcb'
                    self.assertEqual(readiness['boardSha256'],hashlib.sha256(board.read_bytes()).hexdigest())
                    for file,digest in readiness['files'].items():
                        self.assertEqual(hashlib.sha256(archive.read(file)).hexdigest(),digest)

    def test_complete_parts_and_search_fallbacks(self):
        html=page('/build/parts/')
        for value in ['1 µF','100 nF','33 pF','100 kΩ','47 Ω','5.1 kΩ','50 V','125 mW']:
            self.assertIn(value,html)
        self.assertIn('data-parts-variant="standard"',html)
        self.assertIn('data-parts-variant="modular"',html)
        self.assertIn('Filtering and quantity calculations need JavaScript',html)
        search=json.loads((DIST/'static/guide-search.json').read_text())
        self.assertEqual(set(search),{g[0] for g in GUIDES})
        self.assertIn('sec1210',search['smartcards'])

    def test_enclosure_assets_and_print_kit(self):
        html=page('/guides/enclosure/')
        for asset in workflows.load('enclosure-assets')['assets']:
            self.assertIn(asset['name'],html)
            self.assertEqual(hashlib.sha256((DIST/'files'/asset['name']).read_bytes()).hexdigest(),asset['sha256'])
        with ZipFile(DIST/'files/shieldsigner-enclosure-print.zip') as archive:
            self.assertIn('print/button-fit-coupon.stl',archive.namelist())
            self.assertEqual(len([n for n in archive.namelist() if n.endswith('.stl')]),9)
            self.assertEqual(json.loads(archive.read('checks/hardware-fit.json'))['findings'],[])

    def test_runtime_and_health_are_static(self):
        health=json.loads((DIST/'healthz').read_text())
        self.assertEqual(health['hosting'],'static')
        self.assertEqual((health['guides'],health['tasks']),(len(GUIDES),6))
        dockerfile=(ROOT/'Dockerfile').read_text()
        self.assertIn('FROM caddy:',dockerfile)
        self.assertNotIn('python',dockerfile)
        for name in ['django','gunicorn','whitenoise']:
            self.assertNotIn(name,(ROOT/'uv.lock').read_text())
