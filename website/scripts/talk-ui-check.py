"""Exercise progressive talk presentation controls against an existing preview."""
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = os.environ.get('UI_BASE_URL', 'http://127.0.0.1:8034').rstrip('/')
IDS = ['intro', 'trust', 'incidents', 'multisig', 'workflow', 'pcb', 'assembly',
       'case', 'camera', 'lvgl', 'demo', 'verification', 'cost', 'next']
OUT = Path('artifacts')
OUT.mkdir(exist_ok=True)


def no_overflow(page):
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), 'Talk overflows horizontally'


def capture(page, path):
    assert page.locator('img').evaluate_all('''async (images) => {
        const visible = images.filter(image => {
            const box = image.getBoundingClientRect();
            return box.width > 0 && box.height > 0 && box.top < innerHeight && box.bottom > 0;
        });
        await Promise.all(visible.map(image => image.decode()));
        return visible.every(image => image.complete && image.naturalWidth > 0);
    }'''), 'Visible talk image failed to decode'
    no_overflow(page)
    page.screenshot(path=str(path))


def current(page, slide):
    assert page.locator('body').evaluate('(body) => body.classList.contains("talk-presenting")')
    assert page.locator('.talk-slide:visible').count() == 1
    assert page.locator('.talk-slide:visible').get_attribute('id') == slide
    assert page.locator('.talk-slide:visible').evaluate('''(section) =>
        section.scrollHeight <= section.clientHeight + 1 ||
        ['auto', 'scroll'].includes(getComputedStyle(section).overflowY)'''), 'Tall presentation content cannot scroll'
    assert page.evaluate('location.hash') == '#' + slide
    position = page.locator('#talk-position').inner_text()
    assert str(IDS.index(slide) + 1) in position and '14' in position, position
    no_overflow(page)


def reading(page):
    assert not page.locator('body').evaluate('(body) => body.classList.contains("talk-presenting")')
    assert page.locator('#talk .talk-slide').evaluate_all('(slides) => slides.map(s => s.id)') == IDS
    assert page.locator('.talk-slide:visible').count() == 14
    for slide in page.locator('.talk-slide').all():
        assert slide.locator('h1,h2,h3').count(), 'Slide needs a readable heading'
    no_overflow(page)


with sync_playwright() as playwright:
    browser = playwright.chromium.launch(args=['--enable-unsafe-swiftshader'])
    for width, height in [(1440, 900), (390, 844)]:
        context = browser.new_context(viewport={'width': width, 'height': height})
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        # Stub only the optional browser Fullscreen API so the control is
        # deterministic in headless Chromium and on platforms without support.
        page.add_init_script('''window.__talkFullscreenRequests = 0;
            Element.prototype.requestFullscreen = function () {
                window.__talkFullscreenRequests += 1; return Promise.resolve();
            };''')
        response = page.goto(BASE + '/talk/')
        assert response.ok
        reading(page)
        assert page.locator('.talk-notes').count() > 0
        assert page.locator('.talk-notes[open]').count() == 0
        for control in ['start', 'exit', 'prev', 'next', 'notes', 'fullscreen']:
            assert page.locator('#talk-' + control).evaluate(
                '(button) => Boolean(button.innerText.trim() || button.getAttribute("aria-label"))'), 'Unnamed talk control'
        assert page.locator('#talk-index').evaluate(
            '(select) => Boolean(select.labels.length || select.getAttribute("aria-label"))'), 'Unlabelled slide selector'
        page.keyboard.press('ArrowRight')
        reading(page)
        assert page.evaluate('location.hash') == '', 'Reading mode captured navigation keys'
        capture(page, OUT / f'talk-reading-{width}.png')

        page.locator('#talk-start').click()
        current(page, 'intro')
        assert page.locator('#talk-prev').is_disabled()
        assert not page.locator('#talk-next').is_disabled()
        assert page.evaluate('document.activeElement.closest("#talk") !== null'), 'Presentation focus escaped the talk'
        page.locator('#talk-next').click()
        current(page, 'trust')
        # Move focus away from controls before exercising document navigation.
        page.locator('.talk-slide:visible').evaluate('(slide) => {slide.tabIndex = -1; slide.focus();}')
        page.keyboard.press('PageDown')
        current(page, 'incidents')
        page.keyboard.press('ArrowLeft')
        current(page, 'trust')
        page.keyboard.press('PageUp')
        current(page, 'intro')
        page.keyboard.press('End')
        current(page, 'next')
        assert page.locator('#talk-next').is_disabled()
        page.keyboard.press('Home')
        current(page, 'intro')

        page.locator('#talk-index').select_option('multisig')
        current(page, 'multisig')
        threshold = page.locator('[data-threshold-demo]')
        signers = threshold.locator('[data-cosigner]')
        assert signers.count() == 3
        signers.nth(0).click()
        assert threshold.locator('[data-threshold-count]').inner_text() == '1 / 3'
        assert threshold.get_attribute('data-met') == 'false'
        signers.nth(2).click()
        assert threshold.locator('[data-threshold-count]').inner_text() == '2 / 3'
        assert threshold.get_attribute('data-met') == 'true'
        signers.nth(0).click()
        assert threshold.get_attribute('data-met') == 'false'

        page.locator('#talk-index').select_option('assembly')
        current(page, 'assembly')
        viewer = page.locator('#assembly [data-enclosure-viewer]')
        page.wait_for_function('document.querySelector("#assembly [data-enclosure-viewer]").dataset.loaded === "assembled"', timeout=60000)
        canvas = viewer.locator('canvas')
        assert canvas.is_visible()
        for mode in ['pcb', 'fit']:
            viewer.locator(f'[data-mode="{mode}"]').click()
            page.wait_for_function('(mode) => document.querySelector("#assembly [data-enclosure-viewer]").dataset.loaded === mode', arg=mode, timeout=60000)
            for layer in ['display_module', 'luckfox_module']:
                checkbox = viewer.locator(f'[data-layer="{layer}"]')
                assert checkbox.is_visible()
                checkbox.uncheck()
                assert not checkbox.is_checked()
            canvas.screenshot(path=str(OUT / f'talk-model-{mode}-headers-{width}.png'))
            for layer in ['display_module', 'luckfox_module']:
                viewer.locator(f'[data-layer="{layer}"]').check()
        canvas.focus()
        page.keyboard.press('ArrowRight')
        current(page, 'assembly')
        capture(page, OUT / f'talk-assembly-{width}.png')
        page.locator('#talk-index').select_option('camera')
        current(page, 'camera')

        # Arrows belong to editable fields and interactive canvases, even when
        # those controls are added by a demo after initial page load.
        for tag in ['input', 'canvas']:
            page.locator('#camera').evaluate('''(slide, tag) => {
                const node = document.createElement(tag); node.id = 'talk-test-input';
                node.tabIndex = 0; slide.append(node); node.focus();
            }''', tag)
            page.keyboard.press('ArrowRight')
            current(page, 'camera')
            page.locator('#talk-test-input').evaluate('(node) => node.remove()')

        notes = page.locator('#camera .talk-notes')
        assert notes.count(), 'Camera slide needs speaker notes'
        page.locator('#talk-notes').click()
        assert notes.evaluate('(node) => node.open'), 'Notes control did not open current notes'
        page.locator('#talk-notes').click()
        assert not notes.evaluate('(node) => node.open')
        page.locator('#talk-fullscreen').click()
        assert page.evaluate('window.__talkFullscreenRequests') == 1
        for slide in ['pcb', 'camera', 'demo']:
            page.locator('#talk-index').select_option(slide)
            current(page, slide)
            capture(page, OUT / f'talk-present-{slide}-{width}.png')

        page.locator('#talk-exit').click()
        reading(page)
        assert page.locator('#talk-start').is_visible()
        assert page.evaluate('''document.activeElement === document.body ||
            document.activeElement.getClientRects().length > 0'''), 'Exit left focus on a hidden control'
        page.locator('#talk a[href="#camera"]:visible').first.click()
        assert page.evaluate('location.hash') == '#camera'
        reading(page)
        page.goto(BASE + '/talk/#camera')
        reading(page)
        page.locator('#talk-start').click()
        current(page, 'camera')
        # Hash updates while presenting also select the matching slide.
        page.evaluate('location.hash = "#cost"')
        page.wait_for_function('document.querySelector("#cost").getBoundingClientRect().height > 0')
        current(page, 'cost')
        assert not errors, errors
        context.close()

    for width, height in [(1440, 900), (390, 844)]:
        context = browser.new_context(java_script_enabled=False, viewport={'width': width, 'height': height})
        page = context.new_page()
        page.goto(BASE + '/talk/')
        reading(page)
        assert not page.locator('#talk-start').is_visible(), 'Presentation controls require JavaScript'
        for control in ['talk-prev', 'talk-next', 'talk-exit', 'talk-index', 'talk-notes', 'talk-fullscreen']:
            assert not page.locator('#' + control).is_visible(), f'No-JS control visible: {control}'
        assert page.locator('.talk-notes[open]').count() == 0
        page.locator('#camera .talk-notes summary').click()
        assert page.locator('#camera .talk-notes').evaluate('(node) => node.open')
        page.locator('#talk a[href="#verification"]:visible').first.click()
        assert page.evaluate('location.hash') == '#verification'
        no_overflow(page)
        capture(page, OUT / f'talk-nojs-{width}.png')
        context.close()
    browser.close()

print(json.dumps(dict(passed=True, slides=14, viewports=['1440x900', '390x844'],
    checks=['reading', 'presentation', 'boundaries', 'keyboard', 'input/canvas ownership',
            'hash/deep links', 'notes', 'fullscreen request', '2-of-3 threshold',
            'lazy 3D / PCB / case fit / layer visibility', 'visible image decoding',
            'no-JS', 'horizontal overflow']), indent=2))
