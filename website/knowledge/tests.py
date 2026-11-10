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
    def test_talk_has_all_readable_slides_notes_and_local_presentation_assets(self):
        expected=['intro', 'signer', 'lineage', 'trust', 'incidents', 'multisig', 'software', 'libraries', 'hardware', 'swaps', 'workflow', 'pcb', 'tscircuit', 'case', 'assembly', 'camera', 'qr-decoder', 'lvgl', 'demo', 'verification', 'cost', 'next']
        content=json.loads((ROOT/'knowledge/talk.json').read_text())
        self.assertEqual([slide['id'] for slide in content['slides']],expected)
        self.assertTrue(all(slide['notes'] and slide['sources'] for slide in content['slides']))
        by_id={slide['id']:slide for slide in content['slides']}
        for id in ['software','hardware']:
            diagram=by_id[id]
            blocks=diagram.get('blocks') or [block for lane in diagram['lanes'] for block in lane['blocks']]
            self.assertEqual(len(blocks),6)
            self.assertTrue(all(all(block.get(key) for key in ['title','interface','role','connection']) for block in blocks))
            self.assertTrue(diagram['hubRole'] and diagram['hubConnection'])
        self.assertEqual({lib['name'] for lib in by_id['libraries']['libraries']},{'embit','rust-bitcoin','libwally'})
        self.assertTrue(20*60 <= sum(slide['seconds'] for slide in content['slides']) <= 25*60)
        html=page('/talk/')
        class TalkElements(HTMLParser):
            def __init__(self):
                super().__init__(); self.elements=[]; self.feed(html)
            def handle_starttag(self,tag,attrs):
                self.elements.append((tag,dict(attrs)))
        elements=TalkElements().elements
        slides=[attrs for tag,attrs in elements if tag=='section' and 'talk-slide' in attrs.get('class','').split()]
        self.assertEqual([slide.get('id') for slide in slides],expected)
        self.assertTrue(all('hidden' not in slide and slide.get('aria-hidden')!='true' for slide in slides),
                        'Slides must be readable before JavaScript runs')
        links=Links(html)
        self.assertIn('talk',links.ids)
        controls={attrs['id']:(tag,attrs) for tag,attrs in elements if attrs.get('id','').startswith('talk-')}
        for name in ['start','exit','prev','next','notes','fullscreen']:
            self.assertEqual(controls['talk-'+name][0],'button')
        self.assertEqual(controls['talk-index'][0],'select')
        self.assertEqual(controls['talk-position'][0],'output')
        notes=[attrs for tag,attrs in elements if tag=='details' and 'talk-notes' in attrs.get('class','').split()]
        self.assertEqual(len(notes),len(expected))
        self.assertTrue(all('open' not in note for note in notes),'Reading notes should start closed')
        for slide in expected:
            self.assertIn('#'+slide,links.urls,'Ordinary anchors must work without JavaScript')
        assets=[attrs['src'] for tag,attrs in elements if tag=='script' and attrs.get('src')]
        self.assertIn('/static/js/talk.js',[urlsplit(url).path for url in assets])
        self.assertTrue(all(url.startswith('/static/') for url in assets),'Talk scripts must be served locally')
        self.assertTrue(any('github.com/' in url and 'seedsigner' in url.lower() for url in links.urls),
                        'Upstream source attribution should be linked, not implied')
        for private_marker in ['/Users/', 'tools/telegram/private/', '.session', 'api_hash', 'bot_token']:
            self.assertNotIn(private_marker,html,'Private integration material must not be published in the talk')

    def test_firmware_status_separates_bench_hardware_and_evidence(self):
        status=page('/guides/firmware-status/')
        for text in ['lvgl-dev.cb6170a37a5a', '240×240', '2.8-inch',
                     '11,012 KiB', '13,576 KiB', 'logical swap', 'pending',
                     'ZXing-C++', 'Python', 'local build artifact']:
            self.assertIn(text,status)
        self.assertIn('/guides/firmware-status/',page('/'))
        for task in ['compile','flash','use']:
            self.assertIn('/guides/firmware-status/',page(f'/build/{task}/'))
        legacy=page('/guides/memory-threads/')
        self.assertIn('earlier Python/Pillow renderer',legacy)
        # A documented local image must never become a broken public download.
        for path in DIST.rglob('index.html'):
            for url in Links(path.read_text()).urls:
                target=urlsplit(url)
                self.assertFalse((not target.netloc or target.netloc=='shieldsigner.dev')
                                 and target.path.endswith(('.img','.img.xz')),
                                 f'Unpublished firmware download in {path}')

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
            ('shieldsigner-modular-order.zip',43,18,'bom-jlcpcb.csv','cpl-jlcpcb.csv')]:
            with ZipFile(DIST/'files'/name) as archive:
                bom=list(csv.DictReader(io.StringIO(archive.read(bom_name).decode())))
                cpl=list(csv.DictReader(io.StringIO(archive.read(cpl_name).decode())))
                refs={ref for part in bom for ref in part['Designator'].split(',')}
                self.assertEqual((len(refs),len(bom)),(count,lines))
                self.assertEqual(refs,{p['Designator'] for p in cpl})
                self.assertFalse(refs & {'U202','J701','J302','R404','R408'})
                caps=next(p for p in bom if p['LCSC Part #']=='C28323')
                self.assertEqual(set(caps['Designator'].split(',')),{'C602','C603','C604'})
                if name=='shieldsigner-modular-order.zip':
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
