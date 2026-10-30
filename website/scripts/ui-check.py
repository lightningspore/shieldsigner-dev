"""Six static-site journeys, client-side filters, and no-JS content access."""
import json
import csv
import io
import os
from pathlib import Path
from zipfile import ZipFile
from playwright.sync_api import sync_playwright

base = os.environ.get('UI_BASE_URL', 'http://127.0.0.1:8031')
artifacts = Path('artifacts'); artifacts.mkdir(exist_ok=True)
slugs = ['pcb','parts','compile','flash','use','cards']
with sync_playwright() as p:
    browser = p.chromium.launch()
    for width, height in [(1440,1000),(390,844)]:
        context = browser.new_context(viewport={'width':width,'height':height}, permissions=['clipboard-read','clipboard-write'])
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(base)
        page.locator('.board-frame img').wait_for()
        assert page.locator('.board-frame img').evaluate('(img) => img.complete && img.naturalWidth > 0')
        assert page.locator('.task-card').count() == 6
        assert json.loads((Path(__file__).resolve().parents[1]/'version.json').read_text())['version'] in page.locator('footer').inner_text()
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), 'Homepage overflows'
        page.screenshot(path=str(artifacts/f'home-{width}.png'), full_page=True)
        gallery = page.locator('#pcb-views')
        assert gallery.locator('.pcb-face').count() == 2
        for photo in gallery.locator('img').all():
            photo.scroll_into_view_if_needed()
            photo.evaluate('(img) => img.decode()')
            assert photo.evaluate('(img) => img.naturalWidth === 2800')
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), 'PCB views overflow'
        gallery.screenshot(path=str(artifacts/f'pcb-views-{width}.png'))
        with page.expect_popup() as image_window:
            gallery.get_by_role('link', name='Open full-size ↗', exact=True).first.click()
        image_window.value.wait_for_load_state()
        assert '/board-top.png' in image_window.value.url
        image_window.value.close()
        page.locator('.task-card[href="/build/pcb/"]').click()
        page.wait_for_url('**/build/pcb/')
        page.locator('.step-check input').first.check()
        page.reload()
        assert page.locator('.step-check input').first.is_checked(), 'Checklist did not persist'
        with page.expect_download() as download:
            page.locator('.order-launch').get_by_role('link',name='Download JLC order files').click()
        target = artifacts/f'order-{width}.zip'
        download.value.save_as(target)
        with ZipFile(target) as archive:
            bom = list(csv.DictReader(io.StringIO(archive.read('bom-jlcpcb.csv').decode())))
            assert len(bom)==17
        for slug in slugs:
            page.goto(base+f'/build/{slug}/')
            page.locator('h1').wait_for()
            assert page.locator('h1').count()==1
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), f'{slug} overflows'
            if slug in {'pcb','parts','compile','flash','cards'}:
                page.screenshot(path=str(artifacts/f'{slug}-{width}.png'), full_page=True)
        page.goto(base+'/build/parts/?scope=carrier')
        assert page.locator('#parts-results tbody tr').count()==17
        page.locator('#board-variant').select_option('standard')
        page.wait_for_function("document.querySelectorAll('#parts-results tbody tr').length===21")
        assert '43 fitted pieces' in page.locator('#parts-results').inner_text()
        page.locator('#board-variant').select_option('modular')
        page.wait_for_function("document.querySelectorAll('#parts-results tbody tr').length===17")
        page.locator('#part-query').fill('C603')
        page.locator('#board-quantity').fill('5')
        page.locator('#board-quantity').dispatch_event('change')
        page.wait_for_function("document.querySelectorAll('#parts-results tbody tr').length===1 && document.querySelector('#parts-results tbody tr td:nth-child(4)').textContent.trim()==='15' && document.querySelector('#parts-results').innerText.includes('C602,C603,C604')")
        assert page.locator('#parts-results tbody tr').count()==1
        assert 'C28323' in page.locator('#parts-results').inner_text()
        assert '1 µF' in page.locator('#parts-results').inner_text()
        assert '50 V' in page.locator('#parts-results').inner_text()
        page.locator('#part-query').fill('not-a-part')
        page.wait_for_function("document.querySelector('#parts-results').innerText.includes('No matching parts')")
        page.locator('#part-query').fill('')
        page.wait_for_function("document.querySelectorAll('#parts-results tbody tr').length===17")
        page.locator('#part-scope').select_option('system')
        page.wait_for_function("document.querySelectorAll('#parts-results .system-part').length===16")
        page.goto(base+'/build/compile/')
        page.locator('.copy-command').first.click()
        page.wait_for_function("document.querySelector('.copy-feedback').textContent==='Copied'")
        assert 'mise run os:prepare' in page.evaluate('navigator.clipboard.readText()')
        page.goto(base+'/build/cards/')
        page.locator('.card-tabs').get_by_role('link',name='Satochip',exact=True).click()
        page.wait_for_url('**/build/cards/satochip/#card-workflow')
        assert 'initialize and export' in page.locator('#card-workflow h3').inner_text()
        page.locator('.card-tabs').get_by_role('link',name='DIY JavaCard',exact=True).click()
        page.wait_for_url('**/build/cards/diy/#card-workflow')
        assert 'install an applet' in page.locator('#card-workflow h3').inner_text()
        if width==390:
            page.get_by_role('button',name='Toggle navigation').click()
            page.locator('#mobile-nav').get_by_role('link',name='Flash',exact=True).click()
            page.wait_for_url('**/build/flash/')
            assert not page.locator('#mobile-nav').is_visible()
        page.goto(base+'/guides/')
        page.locator('#query').fill('SEC1210')
        page.wait_for_function("document.querySelector('#results').innerText.includes('matching')")
        page.locator('#results').get_by_role('link').filter(has_text='Cards & the Linux reader').click()
        page.wait_for_url('**/guides/smartcards/')
        assert page.locator('h1').inner_text().startswith('Smartcards')
        page.goto(base+'/guides/memory-threads/')
        assert 'Memory and threads' in page.locator('h1').inner_text()
        assert '13.7 MiB' in page.locator('article').inner_text()
        assert '112.5 KiB' in page.locator('article').inner_text()
        for image in page.locator('article img').all():
            image.scroll_into_view_if_needed()
            image.evaluate('(img) => img.decode()')
            assert image.evaluate('(img) => img.naturalWidth > 0')
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), 'Memory guide overflows'
        page.screenshot(path=str(artifacts/f'memory-threads-{width}.png'), full_page=True)
        page.goto(base+'/guides/lcd-module/')
        assert '2.8-inch' in page.locator('h1').inner_text()
        for image in page.locator('main img').all():
            assert image.evaluate('(img) => img.complete && img.naturalWidth > 0')
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), 'Module guide overflows'
        page.screenshot(path=str(artifacts/f'modular-{width}.png'), full_page=True)
        page.goto(base+'/downloads/')
        with page.expect_download() as download:
            page.get_by_role('link', name='Eight-pin pill order kit').click()
        target = artifacts/f'modular-order-{width}.zip'
        download.value.save_as(target)
        with ZipFile(target) as archive:
            bom = list(csv.DictReader(io.StringIO(archive.read('bom-jlcpcb.csv').decode())))
            assert len(bom)==17 and sum(len(row['Designator'].split(',')) for row in bom)==35
        assert not errors, errors
        context.close()
    context = browser.new_context(java_script_enabled=False,viewport={'width':390,'height':844})
    page = context.new_page()
    page.goto(base)
    for slug in slugs:
        assert page.locator(f'.task-card[href="/build/{slug}/"]').count()==1
    page.locator('.task-card[href="/build/parts/"]').click()
    assert page.locator('#parts-results tbody tr').count()==17
    assert page.locator('#parts-results .system-part').count()==16
    assert 'C28323' in page.locator('#parts-results').inner_text()
    assert 'Filtering and quantity calculations need JavaScript' in page.locator('noscript').inner_text()
    page.goto(base+'/build/cards/diy/')
    assert 'install an applet' in page.locator('#card-workflow h3').inner_text()
    assert not page.locator('.copy-command').is_visible() if page.locator('.copy-command').count() else True
    context.close()
    browser.close()
print('Passed six static task journeys, downloads, browser-local BOM quantities/search, copy, checklist persistence, static card routes, mobile navigation, guide search and no-JS content.')
