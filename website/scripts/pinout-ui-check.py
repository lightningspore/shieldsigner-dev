"""Exercise pin selection, mux filters, revision differences and no-JS fallback."""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
base=os.environ.get('UI_BASE_URL','http://127.0.0.1:8030')
out=Path('artifacts');out.mkdir(exist_ok=True)
with sync_playwright() as p:
 browser=p.chromium.launch()
 for width,height in [(1440,1000),(768,1024),(390,844)]:
  context=browser.new_context(viewport={'width':width,'height':height})
  page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.goto(base+'/guides/luckfox-pinout/')
  root=page.locator('[data-pinout-tool]')
  page.wait_for_function("document.querySelector('[data-pinout-tool]').dataset.selectedPin==='14'")
  assert root.locator('svg [data-pin]').count()==22
  assert root.locator('.pinout-table tbody tr').count()==22
  assert 'Unused on 0.0.7' in root.locator('[data-selected-use]').inner_text()
  root.get_by_role('button',name='PWM',exact=True).click()
  assert 'dimmed' in root.locator('[data-pin="19"]').get_attribute('class')
  assert 'dimmed' not in root.locator('[data-pin="20"]').get_attribute('class')
  root.get_by_role('button',name='All pins',exact=True).click()
  root.locator('[data-pinout-revision]').select_option('candidate')
  assert 'LCD_PWM' in root.locator('[data-selected-net]').inner_text()
  assert 'always-on remains default' in root.locator('[data-selected-use]').inner_text().lower()
  assert root.locator('[data-table-net="14"]').inner_text()=='LCD_PWM'
  assert '0.0.8' in root.locator('svg title').text_content()
  root.locator('[data-pin="19"]').focus();page.keyboard.press('Enter')
  assert root.get_attribute('data-selected-pin')=='19'
  assert '1.8 V' in root.locator('[data-selected-title]').inner_text()
  assert 'internal pull-up' in root.locator('[data-selected-use]').inner_text()
  root.locator('[data-pinout-pick]').select_option('22')
  assert 'no GPIO address' in root.locator('[data-selected-gpio]').inner_text()
  root.locator('[data-pinout-revision]').select_option('released')
  root.locator('[data-pinout-pick]').select_option('14')
  assert root.locator('[data-table-net="14"]').inner_text()=='I2C-SDA'
  # Long labels and number badges must remain inside the SVG bounds.
  assert page.locator('svg text').evaluate_all('(texts)=>texts.every(t=>{let b=t.getBBox();return b.x>=0&&b.x+b.width<=1600})')
  assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),'Pinout page overflows viewport'
  root.locator('.pinout-frame').screenshot(path=str(out/f'pinout-diagram-{width}.png'))
  root.locator('.pinout-selection').screenshot(path=str(out/f'pinout-detail-{width}.png'))
  page.screenshot(path=str(out/f'pinout-page-{width}.png'))
  for revision in ['released','candidate']:
   response=page.request.get(base+f'/static/pinouts/luckfox-mini-{revision}.svg')
   assert response.ok and '<svg' in response.text()
  assert not errors,errors
  context.close()
 context=browser.new_context(java_script_enabled=False,viewport={'width':390,'height':844})
 page=context.new_page();page.goto(base+'/guides/luckfox-pinout/')
 assert page.locator('.pinout-table tbody tr').count()==22
 assert page.locator('[data-pinout-revision]').is_disabled()
 assert '1.8 V only' in page.locator('#pin-19').inner_text()
 assert 'PWM candidate' in page.locator('#pin-14').inner_text() or '0.0.8 candidate' in page.locator('#pin-14').inner_text()
 assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
 context.close();browser.close()
print('Pinout UI passed: desktop/tablet/mobile, 22 pins, keyboard, filters, revisions, SVG downloads and no-JS fallback')
