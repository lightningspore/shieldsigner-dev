"""Exercise the static site's WebGL viewer and portable downloads."""
import os
from pathlib import Path
from zipfile import ZipFile
import io
from playwright.sync_api import sync_playwright

base=os.environ.get('UI_BASE_URL','http://127.0.0.1:8031')
artifacts=Path('artifacts');artifacts.mkdir(exist_ok=True)
with sync_playwright() as p:
    browser=p.chromium.launch(args=['--enable-unsafe-swiftshader'])
    for width,height in [(1440,1000),(390,844)]:
        context=browser.new_context(viewport={'width':width,'height':height})
        page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(base)
        page.get_by_role('link',name='View 3D model').click()
        page.wait_for_function("document.querySelector('[data-enclosure-viewer]')?.dataset.loaded==='assembled'",timeout=60000)
        home_viewer=page.locator('[data-enclosure-viewer]')
        home_viewer.get_by_role('button',name='Exploded',exact=True).click()
        page.wait_for_function("document.querySelector('[data-enclosure-viewer]').dataset.loaded==='exploded'",timeout=60000)
        home_viewer.locator('canvas').screenshot(path=str(artifacts/f'home-3d-{width}.png'))
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),'Homepage 3D model overflows'
        page.get_by_role('link',name='Print the case & inspect it in 3D').click()
        page.wait_for_url('**/guides/enclosure/')
        viewer=page.locator('[data-enclosure-viewer]')
        page.wait_for_function("document.querySelector('[data-enclosure-viewer]')?.dataset.loaded==='assembled'",timeout=60000)
        canvas=viewer.locator('canvas');canvas.scroll_into_view_if_needed()
        page.wait_for_timeout(500)
        canvas.screenshot(path=str(artifacts/f'enclosure-assembled-{width}.png'))
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),'Enclosure guide overflows'
        viewer.get_by_role('button',name='Exploded',exact=True).click()
        page.wait_for_function("document.querySelector('[data-enclosure-viewer]').dataset.loaded==='exploded'",timeout=60000)
        page.wait_for_timeout(500)
        canvas.screenshot(path=str(artifacts/f'enclosure-exploded-{width}.png'))
        assert viewer.get_by_role('button',name='Exploded',exact=True).get_attribute('aria-pressed')=='true'
        bounds=canvas.bounding_box();page.mouse.move(bounds['x']+bounds['width']/2,bounds['y']+bounds['height']/2)
        page.mouse.down();page.mouse.move(bounds['x']+bounds['width']/2+60,bounds['y']+bounds['height']/2+20,steps=8);page.mouse.up()
        viewer.get_by_role('button',name='Reset view').click()
        response=page.request.get(base+'/files/shieldsigner-enclosure-print.zip')
        assert response.ok
        with ZipFile(io.BytesIO(response.body())) as archive:
            assert 'print/button-fit-coupon.stl' in archive.namelist()
            assert len([n for n in archive.namelist() if n.endswith('.stl')])==9
        # Navigate away and back through ordinary static pages.
        page.locator('.article-meta a').click();page.wait_for_url('**/guides/')
        page.get_by_role('link',name='Print and assemble the enclosure').click()
        page.wait_for_function("document.querySelector('[data-enclosure-viewer]')?.dataset.loaded==='assembled'",timeout=60000)
        assert not errors,errors
        context.close()
    context=browser.new_context(java_script_enabled=False)
    page=context.new_page();page.goto(base+'/guides/enclosure/')
    assert page.get_by_role('link',name='shieldsigner-enclosure-print.zip').is_visible()
    assert page.locator('.enclosure-fallback img').is_visible()
    assert page.locator('.enclosure-fallback img').evaluate('(img)=>img.complete && img.naturalWidth>0')
    assert not page.locator('[data-enclosure-viewer] canvas').is_visible()
    context.close();browser.close()
print('Static enclosure viewer passed: desktop/mobile, both models, controls, page return, print ZIP and no-JS downloads')
