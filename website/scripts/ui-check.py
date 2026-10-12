"""Focused desktop/mobile, HTMX and no-JavaScript verification."""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
base = os.environ.get('UI_BASE_URL', 'http://127.0.0.1:8030')
artifacts = Path('artifacts'); artifacts.mkdir(exist_ok=True)
with sync_playwright() as p:
    browser = p.chromium.launch()
    for width, height in [(1440, 1000), (390, 844)]:
        page = browser.new_page(viewport={'width':width,'height':height})
        page.goto(base)
        page.locator('.board-frame img').wait_for()
        assert page.locator('.board-frame img').evaluate('(img) => img.complete && img.naturalWidth > 0')
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), 'Homepage overflows'
        page.screenshot(path=str(artifacts/f'home-{width}.png'), full_page=True)
        if width == 390:
            page.get_by_role('button',name='Toggle navigation').click()
            page.locator('#mobile-nav').get_by_role('link',name='Guides', exact=True).click()
        else:
            page.locator('header').get_by_role('link',name='Guides', exact=True).click()
        page.wait_for_url('**/guides/')
        page.locator('#query').fill('SEC1210')
        page.wait_for_function("document.querySelector('#results').innerText.includes('matching')")
        page.locator('#results').get_by_role('link').filter(has_text='Cards & the Linux reader').click()
        page.wait_for_url('**/guides/smartcards/')
        assert page.locator('h1').inner_text().startswith('Smartcards')
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), 'Guide overflows'
        page.screenshot(path=str(artifacts/f'smartcards-{width}.png'), full_page=True)
        page.close()
    page = browser.new_page(java_script_enabled=False,viewport={'width':390,'height':844})
    page.goto(base+'/guides/')
    page.locator('#query').fill('SeedKeeper')
    page.get_by_role('button',name='Search', exact=True).click()
    assert 'matching' in page.locator('#results').inner_text()
    page.locator('#results').get_by_role('link').filter(has_text='Cards & the Linux reader').click()
    assert page.locator('h1').inner_text().startswith('Smartcards')
    browser.close()
print('Passed desktop/mobile navigation, HTMX search, no-JS search, imagery and overflow checks.')
