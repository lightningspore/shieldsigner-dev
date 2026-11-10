#!/usr/bin/env python3
"""Exercise exact pinned display startup methods without hardware or real sleeps."""
import ast
import hashlib
import json
import re
import types
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sources = json.loads((ROOT/'reference/research/firmware/carrier-runtime-sources.json').read_text())
cache = ROOT/'.tools/electrical-review/upstream'
cache.mkdir(parents=True, exist_ok=True)
texts = {}
for name, spec in sources.items():
    path = cache/name
    if not path.exists():
        path.write_bytes(urllib.request.urlopen(spec['url'], timeout=30).read())
    assert hashlib.sha256(path.read_bytes()).hexdigest() == spec['sha256'], name
    texts[name] = path.read_text()

driver = next(n for n in ast.parse(texts['ST7789.py']).body if isinstance(n, ast.ClassDef) and n.name == 'ST7789')
methods = [n for n in driver.body if isinstance(n, ast.FunctionDef) and n.name in ('init', 'reset')]
assert len(methods) == 2
clock = [0.0]
events = []
def sleep(seconds):
    assert seconds >= 0
    clock[0] += seconds
def emit(kind, value):
    events.append((clock[0], kind, value))
namespace = {'time': types.SimpleNamespace(sleep=sleep)}
exec(compile(ast.Module(body=methods, type_ignores=[]), '<pinned ST7789 startup methods>', 'exec'), namespace)
display = types.SimpleNamespace(_rst=types.SimpleNamespace(write=lambda v: emit('reset', v)),
                                command=lambda v: emit('command', v), data=lambda v: emit('data', v))
display.reset = types.MethodType(namespace['reset'], display)
namespace['init'](display)
resets = [(t,v) for t,k,v in events if k == 'reset']
assert [v for t,v in resets] == [True, False, True]
release = resets[-1][0]
commands = [(t,v) for t,k,v in events if k == 'command']
first = commands[0][0]
wake = next(t for t,v in commands if v == 0x11)
on = next(t for t,v in commands if v == 0x29)
assert first-release >= .120 and wake-release >= .120 and on-wake >= .120
assert not any(wake < t < wake+.120 for t,v in commands)

gpio = texts['configure-gpio.sh']
body = re.search(r'configure_fox_22\(\)\s*\{(.*?)\n\}', gpio, re.S).group(1)
expected = ['GPIO1_D0','GPIO1_D1','GPIO1_C6','GPIO1_C7','GPIO0_A4','GPIO4_C0','GPIO4_C1','GPIO1_C5']
for pin in expected:
    assert re.search(r'\bconfigure_'+pin+r'\b', body), pin
    fn = re.search(r'configure_'+pin+r'\(\)\s*\{(.*?)\n\}', gpio, re.S).group(1)
    assert 'pull-up' in fn and 'input' in fn and 'enable' in fn, pin
buttons = texts['buttons.py']
assert 'GPIO(*gpio_selector, "in", bias=pin_bias)' in buttons
assert 'retrying without bias' in buttons  # Preserve this limitation explicitly.
startup=texts['start-seedsigner.sh']
assert '/usr/bin/configure-gpio.sh 2>&1' in startup
assert 'ensure_gpiochip_symlinks()' in startup
assert 'ln -sf /dev/gpiochip3 /dev/gpiochip4' in startup
reader = texts['ccid_serial.c']
assert 'SEC1210UR2' in reader and 'SEC1210URT' in reader
board = ROOT/'variants/lcd-module-2.8/kicad/SeedSigner-Plus-smartcard-pico.kicad_pcb'
report = {'boardSha256':hashlib.sha256(board.read_bytes()).hexdigest(),
          'scope':'Pinned source and virtual-time startup checks only; no installed-image or physical timing claim',
          'sources':sources,
          'display':{'resetSequence':[True,False,True], 'firstCommandAfterResetMs':round((first-release)*1000),
                     'sleepOutAfterResetMs':round((wake-release)*1000), 'displayOnAfterSleepOutMs':round((on-wake)*1000)},
          'buttons':{'osSetupFunctionsChecked':expected,'applicationRequestsBias':True,
                     'biasFallbackExists':True,'upstreamNumericAliasWorkaroundExists':True,
                     'pullUpSetupInvokedBeforeApp':startup.index('/usr/bin/configure-gpio.sh 2>&1')<startup.index('    python -u main.py'),'requiredPhysicalCheck':'All eight released inputs stable high, pressed low; verify 1.8 V domain for Key1/Key2'},
          'reader':{'ur2AndUrtHaveDistinctSourceIdentities':True,'physicalOperationVerified':False}}
# Independently compare the selected pill initializer to the manufacturer PDF
# fixture, using the original pinned reset implementation and virtual time.
import sys
from unittest.mock import patch
sys.path.insert(0,str(ROOT/'firmware/lvgl-app/python'))
import hothmi
fixture=json.loads((ROOT/'reference/research/firmware/hothmi-init.json').read_text())
assert hashlib.sha256((ROOT/fixture['source']).read_bytes()).hexdigest()==fixture['sha256']
clock[0]=0;events.clear()
display.width=320;display.height=240;display._display_initialized=False
with patch.object(hothmi.time,'sleep',side_effect=sleep):
    hothmi.install(display);display.init()
transactions=[]
for t,kind,value in events:
    if kind=='command':transactions.append({'command':value,'data':[],'time':t})
    elif kind=='data':transactions[-1]['data'].append(value)
assert [{k:r[k] for k in ('command','data')} for r in transactions]==[{k:r[k] for k in ('command','data')} for r in fixture['commands']]
for i,row in enumerate(fixture['commands']):
    end=transactions[i+1]['time'] if i+1<len(transactions) else clock[0]
    assert round((end-transactions[i]['time'])*1000,5)>=row['minimumDelayMs']
report['selectedPillPanelProfile']=hothmi.PROFILE
report['hothmi']={'manufacturerCommandDataMatches':True,'commandsChecked':len(transactions),
                 'dataBytesChecked':sum(len(r['data']) for r in transactions),
                 'source':fixture['source'],'sourceSha256':fixture['sha256'],'sourcePages':fixture['pages'],
                 'implementationSha256':hashlib.sha256((ROOT/'firmware/lvgl-app/python/hothmi.py').read_bytes()).hexdigest(),
                 'physicalOperationVerified':False}
# Check the actual generated carrier profile and independently pinned kernel ABI.
import importlib.util
import tempfile
spec=importlib.util.spec_from_file_location('carrier_io',ROOT/'scripts/configure-image-io-profile.py')
io=importlib.util.module_from_spec(spec);spec.loader.exec_module(io)
gpio_sources=json.loads((ROOT/'reference/research/firmware/gpio-cdev-sources.json').read_text())
for name,row in gpio_sources['sources'].items():
    path=ROOT/'.tools/electrical-review'/name
    if not path.exists():path.write_bytes(urllib.request.urlopen(row['url'],timeout=30).read())
    assert hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256'],name
kernel_gpio=(ROOT/'.tools/electrical-review/gpio.h').read_text()
assert '#define GPIO_MAX_NAME_SIZE 32' in kernel_gpio
assert '#define GPIO_GET_CHIPINFO_IOCTL _IOR(0xB4, 0x01, struct gpiochip_info)' in kernel_gpio
with tempfile.TemporaryDirectory() as tmp:
    path=Path(tmp)/'io_config.json'
    raw=(ROOT/'reference/research/firmware/io-config-efdd1cfd.json').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==io.UPSTREAM_SHA256
    path.write_bytes(raw);receipt=io.configure(path,'carrier')
    profile=io.selected(json.loads(path.read_text()))
    assert profile['display']['dc']==['/dev/gpiochip-bank1',20]
    assert profile['display']['rst']==['/dev/gpiochip-bank1',19]
    assert profile['display']['spi_hz']==10_000_000
    assert profile['buttons']['KEY1']==['/dev/gpiochip-bank4',16,'pull_up']
    assert profile['buttons']['KEY2']==['/dev/gpiochip-bank4',17,'pull_up']
report['gpioBankSelection']={'policy':'kernel-label-aliases','ioConfigSha256':receipt['outputSha256'],
    'requiredLabels':['gpio0','gpio1','gpio4'],'deviceIndicesAssumed':False,
    'metadataIoctl':'GPIO_GET_CHIPINFO_IOCTL','metadataBytes':68,
    'sourceEvidence':'reference/research/firmware/gpio-cdev-sources.json',
    'physicalOperationVerified':False}
(ROOT/'variants/lcd-module-2.8/carrier-runtime-audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k != 'sources'}, indent=2))
