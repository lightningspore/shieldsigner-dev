import csv
import hashlib
import io
import json
from html.parser import HTMLParser
from urllib.parse import urlsplit
from zipfile import ZipFile

from django.conf import settings
from django.test import SimpleTestCase
from .catalog import GUIDES
from . import workflows


class Links(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.hrefs = []
        self.ids = set()
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.add(attrs['id'])
        if tag == 'a' and attrs.get('href'):
            self.hrefs.append(attrs['href'])


class KnowledgeTests(SimpleTestCase):
    def test_enclosure_models_and_print_kit(self):
        response=self.client.get('/guides/enclosure/')
        self.assertContains(response,'data-enclosure-viewer')
        manifest=json.loads((settings.CONTENT_DIR/'enclosure-assets.json').read_text())
        for asset in manifest['assets']:
            self.assertContains(response,f"/files/{asset['name']}?v={asset['sha256'][:12]}")
            path=settings.PUBLIC_DIR/asset['name']
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),asset['sha256'])
        with ZipFile(settings.PUBLIC_DIR/'shieldsigner-enclosure-print.zip') as archive:
            self.assertIn('print/button-fit-coupon.stl',archive.namelist())
            self.assertEqual(len([n for n in archive.namelist() if n.endswith('.stl')]),9)
            self.assertEqual(json.loads(archive.read('checks/hardware-fit.json'))['findings'],[])
            self.assertEqual(json.loads(archive.read('checks/fastener-check.json'))['findings'],[])

    def test_all_guides_and_metadata(self):
        for slug, *_ in GUIDES:
            response = self.client.get(f'/guides/{slug}/')
            self.assertEqual(response.status_code, 200, slug)
            self.assertContains(response, f'https://shieldsigner.dev/guides/{slug}/')
        self.assertEqual(self.client.get('/guides/not-a-guide/').status_code, 404)

    def test_reference_search_and_progressive_enhancement(self):
        response = self.client.get('/guides/?q=SEC1210')
        self.assertContains(response, 'Cards &amp; the Linux reader')
        fragment = self.client.get('/guides/?q=SEC1210', HTTP_HX_REQUEST='true')
        self.assertNotContains(fragment, '<!doctype html>')
        self.assertContains(fragment, 'id="guide-fragment"')
        full = self.client.get('/guides/', HTTP_HX_REQUEST='true', HTTP_HX_BOOSTED='true')
        self.assertContains(full, '<!doctype html>')

    def test_six_actions_from_home_and_sitemap(self):
        home = self.client.get('/')
        self.assertContains(home, 'Build a ShieldSigner.')
        sitemap = self.client.get('/sitemap.xml')
        for slug in ['pcb','parts','compile','flash','use','cards']:
            self.assertContains(home, f'href="/build/{slug}/"')
            self.assertContains(sitemap, f'https://shieldsigner.dev/build/{slug}/')
            response = self.client.get(f'/build/{slug}/')
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, '<h1')
            self.assertContains(response, 'id="step-1"')
        self.assertEqual(self.client.get('/build/not-a-task/').status_code, 404)

    def test_parts_quantity_filter_and_bom_correction(self):
        response = self.client.get('/build/parts/?scope=carrier&q=C603&quantity=5')
        self.assertContains(response, 'C602,C603,C604')
        self.assertContains(response, 'C28323')
        self.assertContains(response, '1 µF')
        self.assertContains(response, '50 V · ±10% · X7R')
        self.assertContains(response, '<strong>15</strong>')
        self.assertNotContains(response, 'C49678')
        fragment = self.client.get('/build/parts/?scope=system&q=camera', HTTP_HX_REQUEST='true')
        self.assertContains(fragment, 'SC3336')
        self.assertContains(fragment, 'id="parts-fragment"')
        self.assertNotContains(fragment, '<!doctype html>')
        invalid = self.client.get('/build/parts/?quantity=-10')
        self.assertContains(invalid, 'Showing quantities for one board.')
        no_match = self.client.get('/build/parts/?q=not-a-real-part')
        self.assertContains(no_match, 'No matching parts in this category.')
        self.assertContains(self.client.get('/build/parts/?scope=system&q=C603'), 'Show 1 matching carrier result')

    def test_passive_values_units_and_revision_are_visible(self):
        page=self.client.get('/build/parts/?scope=carrier')
        for value in ['1 µF', '100 nF', '33 pF', '100 kΩ', '47 Ω', '5.1 kΩ']:
            self.assertContains(page, value)
        self.assertContains(page, '125 mW · ±1%')
        self.assertContains(self.client.get('/guides/bom-table/'), '1 µF')
        self.assertContains(self.client.get('/build/parts/?scope=carrier&q=1uF'), 'C28323')
        self.assertContains(self.client.get('/'), '0.0.5-dev')
        self.assertContains(self.client.get('/'), 'revision')
        self.assertContains(self.client.get('/'), 'site.css?v=')
        self.assertContains(self.client.get('/'), 'site.js?v=')

    def test_card_workflows_are_distinct_and_work_without_javascript(self):
        for card, text in [('seedkeeper','store and load'), ('satochip','initialize and export'), ('diy','install an applet')]:
            response = self.client.get(f'/build/cards/?card={card}')
            self.assertContains(response, text)
            self.assertContains(response, 'id="card-workflow"')
        self.assertContains(self.client.get('/build/cards/?card=unknown'), 'store and load')

    def test_download_boundary(self):
        response = self.client.get('/files/reference/pdfs/C5417011.pdf')
        self.assertEqual(response.status_code, 200)
        response.close()
        for path in ['../manage.py','.env','tools/telegram/shieldsigner.txt','tools/telegram/account.session']:
            self.assertEqual(self.client.get('/files/'+path).status_code, 404)
        for path in settings.PUBLIC_DIR.rglob('*'):
            self.assertNotIn(path.suffix, {'.session','.sqlite3','.env'})

    def test_order_bundle_has_matching_files_and_correct_parts(self):
        bundle = settings.PUBLIC_DIR / 'shieldsigner-jlcpcb-order.zip'
        with ZipFile(bundle) as archive:
            self.assertEqual(set(archive.namelist()), {'shieldsigner-carrier-gerbers.zip','bom-carrier-jlcpcb.csv','cpl-carrier-jlcpcb.csv','README.txt','manifest.json'})
            manifest = json.loads(archive.read('manifest.json'))
            self.assertEqual(manifest['releaseStatus'], 'review_only')
            for file in manifest['files']:
                name = file['name'].split('/')[-1]
                self.assertEqual(hashlib.sha256(archive.read(name)).hexdigest(), file['sha256'])
            bom = list(csv.DictReader(io.StringIO(archive.read('bom-carrier-jlcpcb.csv').decode())))
            refs = {ref for part in bom for ref in part['Designator'].split(',')}
            cpl = list(csv.DictReader(io.StringIO(archive.read('cpl-carrier-jlcpcb.csv').decode())))
            self.assertEqual(len(refs), 43)
            self.assertEqual(len(bom), 21)
            self.assertEqual(refs, {part['Designator'] for part in cpl})
            self.assertFalse(refs & {'R404','R408','J302','U202'})
            caps = next(part for part in bom if part['LCSC Part #']=='C28323')
            self.assertEqual(set(caps['Designator'].split(',')), {'C602','C603','C604'})
            self.assertTrue(caps['Comment'].startswith('1u;'))

    def test_modular_bundle_matches_its_board_and_population(self):
        with ZipFile(settings.PUBLIC_DIR / 'shieldsigner-modular-order.zip') as archive:
            readiness = json.loads(archive.read('readiness.json'))
            board = settings.PUBLIC_DIR / 'variants/lcd-module-2.8/kicad/SeedSigner-Plus-smartcard-pico.kicad_pcb'
            self.assertEqual(readiness['boardSha256'], hashlib.sha256(board.read_bytes()).hexdigest())
            self.assertEqual(readiness['status'], 'prototype_quote_files')
            for name, digest in readiness['files'].items():
                self.assertEqual(hashlib.sha256(archive.read(name)).hexdigest(), digest)
            bom = list(csv.DictReader(io.StringIO(archive.read('bom-jlcpcb.csv').decode())))
            refs = {ref for row in bom for ref in row['Designator'].split(',')}
            cpl = list(csv.DictReader(io.StringIO(archive.read('cpl-jlcpcb.csv').decode())))
            self.assertEqual((len(bom), len(refs)), (17, 35))
            self.assertEqual(refs, {row['Designator'] for row in cpl})
            self.assertFalse(refs & {'J701', 'U202', 'J401', 'J302', 'Q401', 'R403', 'R404', 'R408', 'R409'})
            self.assertTrue(next(row for row in bom if row['LCSC Part #'] == 'C28323')['Comment'].startswith('1 µF;'))
        for slug in ['lcd-module', 'modular-assembly', 'modular-bom']:
            self.assertEqual(self.client.get(f'/guides/{slug}/').status_code, 200)
        image = self.client.get('/files/variants/lcd-module-2.8/assembly-front.png')
        self.assertEqual(image.status_code, 200)
        self.assertTrue(image['Content-Disposition'].startswith('inline;'))
        self.assertEqual(image['Cache-Control'], 'no-cache')
        image.close()

    def test_shopping_defaults_to_pill_and_preserves_standard_reference(self):
        pill = self.client.get('/build/parts/?scope=carrier&q=C701&quantity=5')
        self.assertContains(pill, 'C201,C302,C701,C702')
        self.assertContains(pill, '10 µF')
        self.assertContains(pill, '<strong>20</strong>')
        self.assertContains(pill, '35 fitted pieces / 17 catalog lines')
        self.assertContains(self.client.get('/build/parts/?scope=carrier&q=U701'), 'C51118')
        self.assertContains(self.client.get('/build/parts/?q=lcd'), 'HTM-TFT028A16-SPI')
        standard = self.client.get('/build/parts/?variant=standard&scope=carrier')
        self.assertContains(standard, '43 fitted pieces / 21 catalog lines')
        self.assertNotContains(standard, 'C701,C702')
        self.assertContains(self.client.get('/build/parts/?variant=unknown&scope=carrier'), '35 fitted pieces / 17 catalog lines')
        order = self.client.get('/build/pcb/')
        self.assertContains(order, '/files/shieldsigner-modular-order.zip')
        self.assertContains(order, '160 × 70 mm')

    def test_workflow_internal_links_and_anchors(self):
        cache = {}
        for task in workflows.tasks():
            page = f'/build/{task["slug"]}/'
            html = self.client.get(page).content.decode()
            for href in Links(html).hrefs:
                url = urlsplit(href)
                if url.scheme or url.netloc or not href.startswith(('/', '#')):
                    continue
                path = url.path or page
                destination = path + ('?'+url.query if url.query else '')
                if destination not in cache:
                    response = self.client.get(destination)
                    cache[destination] = (response.status_code, response.content.decode() if not response.streaming else '')
                    response.close()
                status, body = cache[destination]
                self.assertEqual(status, 200, href)
                if url.fragment:
                    self.assertIn(url.fragment, Links(body).ids, href)
