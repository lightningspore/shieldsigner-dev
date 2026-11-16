# SPDX-License-Identifier: MIT
"""Public native paged-review flows; independent CPython BIP39 fingerprints."""

import pyformat  # noqa: F401  (formats generated Python on write)
import hashlib, unicodedata
from pathlib import Path
from embit import bip32

root = Path(__file__).resolve().parents[1]
words = 'abandon ' * 11 + 'about'
values = ['0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ' * 5, '  Café🙂\0\\finish\n  ', '🙂' * 63]
fixtures = []
for value in values:
    normalized = unicodedata.normalize('NFKD', value)
    seed = hashlib.pbkdf2_hmac('sha512', words.encode(), ('mnemonic' + normalized).encode(), 2048)
    fixtures.append(
        (
            value,
            unicodedata.normalize('NFC', normalized),
            bip32.HDKey.from_seed(seed).my_fingerprint.hex(),
        )
    )
code = '''# SPDX-License-Identifier: MIT
# PUBLIC fixtures. Real original View, native pages/buttons, actual seed roots.
from seedsigner_port.controller import Controller,StopFlowBasedTest
from seedsigner_port.renderer import Renderer
from seedsigner_port.view_seed import SeedReviewPassphraseView
from seedsigner_port.seed import Seed
from seedsigner_port.navigation import Destination
from seedsigner_port.hardware_buttons import HardwareButtons
from seedsigner_port.settings_store import Settings,SettingsConstants as C
from seedsigner_port import clock
import ui,json,hashlib,gc
'''
code += (
    'fixtures='
    + repr(fixtures)
    + '''\ndef pulse(key):ui.key(key,True);ui.key(key,False)
def forward():
    for i in range(18):pulse(18)
    pulse(10)
def back():
    for i in range(18):pulse(17)
    pulse(10)
class Driver:
    def __init__(self,display,fp,mode):
        self.display=display;self.fp=fp;self.mode=mode;self.summaries=0;self.seen={};self.visits={};self.failure=None;self.started=False;self.alias=None
    def __getattr__(self,name):return getattr(ui,name)
    def render(self,builder,encoded):
        cfg=json.loads(encoded);ui.render(builder,encoded)
        controller=Controller.get_instance();title=cfg['top_nav']['title']
        if builder=='button_list_screen' and title=='Exact Characters':
            assert controller.storage.get_pending_seed().passphrase_display==self.display
            if self.mode=='exit':back()
            else:forward()
        elif builder=='button_list_screen' and title.startswith('Passphrase '):
            page=int(title.split()[1].split('/')[0]);total=int(title.split('/')[1])
            self.seen[page]=cfg['text'];self.visits[page]=self.visits.get(page,0)+1
            assert cfg['text'].startswith('Chars ') and cfg['text_monospace'] and cfg['read_first']
            assert controller.storage.get_pending_seed().passphrase_display==self.display
            assert controller.storage.get_pending_seed().get_fingerprint()==self.fp
            if self.mode=='wipe':
                self.alias=controller.storage.get_pending_seed().seed_bytes
                HardwareButtons.get_instance().last_input_time=int(clock.time()*1000)-60001
            elif self.mode=='revisit' and self.summaries==1 and page==total and self.visits[page]==2:back()
            else:forward()
        elif builder=='seed_review_passphrase_screen':
            self.summaries+=1
            assert cfg['passphrase']=='%d chars read'%len(self.display)
            assert cfg['fingerprint_without']=='73c5da0a' and cfg['fingerprint_with']==self.fp
            assert len(self.seen)>0
            if self.mode=='revisit' and self.summaries==1:back()
            else:pulse(10)
        elif builder=='seed_finalize_screen':
            assert self.mode=='exit' and controller.storage.get_pending_seed().passphrase==''
            pulse(10)
        elif builder=='button_list_screen' and len(title)==8:
            assert title==('73c5da0a' if self.mode=='exit' else self.fp)
            back()
        elif builder=='main_menu_screen':
            if self.mode=='wipe':
                assert controller.storage.get_pending_seed() is None and controller.storage.num_seeds()==0
                assert self.alias==bytes(64)
            raise StopFlowBasedTest()
        else:
            self.failure=(builder,cfg);raise StopFlowBasedTest()
for number,(raw,display,fp) in enumerate(fixtures):
    for mode in (('revisit','exit','wipe') if number==0 else ('accept',)):
        Renderer._instance=None;driver=Driver(display,fp,mode);Renderer.configure_instance(backend=driver)
        Controller._instance=None;controller=Controller.get_instance()
        candidate=Seed(('abandon '*11+'about').split(),passphrase=raw)
        assert candidate.passphrase_display==display and candidate.get_fingerprint()==fp
        controller.storage.set_pending_seed(candidate)
        settings=Settings.get_instance();previous=settings.get_value(C.SETTING__WIPE_TIMER)
        if mode=='wipe':
            HardwareButtons.get_instance().update_last_input_time()
            settings.set_value(C.SETTING__WIPE_TIMER,1)
        try:controller.start(initial_destination=Destination(SeedReviewPassphraseView),skip_startup_interstitials=True)
        finally:settings.set_value(C.SETTING__WIPE_TIMER,previous)
        assert driver.failure is None
        if mode not in ('wipe','exit'):
            assert controller.storage.num_seeds()==1
            assert controller.storage.seeds[0].passphrase_display==display
            assert controller.storage.seeds[0].get_fingerprint()==fp
            assert sorted(driver.seen)==list(range(1,len(driver.seen)+1))
            print('@@PUBLIC_REVIEW_PAGES',number,mode,json.dumps([driver.seen[i] for i in sorted(driver.seen)]))
        elif mode=='exit':assert driver.summaries==0
        for stored in list(controller.storage.seeds):controller.discard_seed(stored)
        assert controller.storage.num_seeds()==0
        print('@@PASS original-paged-review',number,mode,len(driver.seen),driver.summaries)
from seedsigner_port.review_text import pages,page_config
public=''.join(chr(cp) for cp in range(33,127))
content=pages(public)
home={'top_nav':{'title':'Home'},'button_list':['Scan','Seeds','Tools','Settings']}
steady=None
for iteration in range(21):
    for index,page in enumerate(content):ui.render('button_list_screen',json.dumps(page_config(public,page,index,len(content))))
    ui.render('main_menu_screen',json.dumps(home));gc.collect()
    if steady is None:steady=ui.status()['heap_bytes']
    else:assert ui.status()['heap_bytes']==steady
print('@@PASS paged-review-warm-heap-stable',20,steady)
Renderer._instance=None;renderer=Renderer.get_instance();ui.overlays(0,0)
renderer.session.show_screen('MainMenuScreen',{'title':'Home','button_data':['Scan','Seeds','Tools','Settings']})
gc.collect()
'''
)
(root / 'micropython/review_pages_gate.py').write_text(code)
