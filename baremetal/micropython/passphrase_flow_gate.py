# SPDX-License-Identifier: MIT
# Generated PUBLIC fixtures. Native key pulses, original Views and real roots.
from seedsigner_port.controller import Controller,StopFlowBasedTest
from seedsigner_port.renderer import Renderer
from seedsigner_port.view_seed import SeedAddPassphraseView
from seedsigner_port.seed import Seed
from seedsigner_port.navigation import Destination
from seedsigner_port.native_ui import ScreenSession
import ui,json,hashlib,gc
expected={'': '73c5da0a', 'k': '52e15a41', 'kl': 'e6a78bb8'}
ui.init()
session=ScreenSession()
def pulse(key):ui.key(key,True);ui.key(key,False)
for text in ('', ' public  ', 'é🙂', 'a\0b\\c', 'x'*255, 'é'*127):
    session.show_screen('SeedAddPassphraseScreen',{'title':'Public passphrase test','passphrase':text})
    pulse(51)
    assert session.screen_result(ui.event())=={'passphrase':text}
    assert ui.event() is None
    session.show_screen('SeedAddPassphraseScreen',{'title':'Public passphrase test','passphrase':text})
    for _index in range(6):pulse(17)
    pulse(10)
    assert session.screen_result(ui.event())=={'passphrase':text,'is_back_button':True}
print('@@PASS native-passphrase-confirm-back-exact-text')
session.show_screen('SeedAddPassphraseScreen',{'title':'Public modes','passphrase':''})
pulse(49)
assert ui.event() is None
pulse(10);pulse(50)
assert ui.event() is None
pulse(10);pulse(51)
assert session.screen_result(ui.event())=={'passphrase':'K6'}
print('@@PASS native-passphrase-case-digits-controls')
class Driver:
    def __init__(self,mode):
        self.mode=mode;self.screens=[];self.hashes=[];self.failure=None;self.entries=0;self.reviews=0
    def __getattr__(self,name):return getattr(ui,name)
    def render(self,builder,encoded):
        cfg=json.loads(encoded);ui.render(builder,encoded)
        self.screens.append(builder);self.hashes.append(hashlib.sha256(ui.framebuffer()).hexdigest())
        controller=Controller.get_instance()
        if builder=='seed_add_passphrase_screen':
            self.entries+=1
            if self.mode=='edit' and self.entries==2:
                assert cfg['initial_text']=='k'
                pulse(19);pulse(10);pulse(51) # Last typed k -> next key l -> commit kl.
            else:
                assert cfg['initial_text']==''
                if self.mode=='skip':pulse(51) # Empty commit invokes original skip dialog.
                else:
                    pulse(10) # Actual central default key inserts k.
                    if self.mode=='discard':
                        pulse(19);pulse(10) # Actual next key inserts l.
                        for _index in range(6):pulse(17)
                        pulse(10) # Actual Back snapshots kl.
                    else:pulse(51)
        elif builder=='seed_review_passphrase_screen':
            self.reviews+=1
            assert self.mode in ('accept','edit')
            value='kl' if self.mode=='edit' and self.reviews==2 else 'k'
            assert cfg['passphrase']==value
            assert cfg['fingerprint_without']==expected[''] and cfg['fingerprint_with']==expected[value]
            assert controller.storage.get_pending_seed().passphrase==value
            if self.mode=='edit' and self.reviews==1:pulse(18) # Original Edit action.
            pulse(10)
        elif builder=='large_icon_status_screen':
            want='Skip passphrase?' if self.mode=='skip' else 'Discard passphrase?'
            if cfg['top_nav']['title']!=want:
                self.failure=cfg;raise StopFlowBasedTest()
            assert self.mode in ('discard','skip')
            value='kl' if self.mode=='discard' else ''
            assert controller.storage.get_pending_seed().passphrase==value
            assert controller.storage.get_pending_seed().get_fingerprint()==expected[value]
            pulse(18);pulse(10)
        elif builder=='seed_finalize_screen':
            assert self.mode in ('discard','skip') and cfg['fingerprint']==expected['']
            assert controller.storage.get_pending_seed().passphrase==''
            pulse(10)
        elif builder=='button_list_screen':
            value='k' if self.mode=='accept' else 'kl' if self.mode=='edit' else ''
            assert cfg['top_nav']['title']==expected[value]
            assert controller.storage.num_seeds()==1 and controller.storage.get_pending_seed() is None
            assert len(controller.back_stack)==1
            pulse(20);pulse(10)
        elif builder=='main_menu_screen':raise StopFlowBasedTest()
        else:self.failure=cfg;raise StopFlowBasedTest()
for mode in ('accept','edit','discard','skip'):
    Renderer._instance=None;driver=Driver(mode);Renderer.configure_instance(backend=driver)
    Controller._instance=None;controller=Controller.get_instance()
    controller.storage.set_pending_seed(Seed(('abandon '*11+'about').split()))
    controller.start(initial_destination=Destination(SeedAddPassphraseView),skip_startup_interstitials=True)
    assert driver.failure is None
    middle=['seed_review_passphrase_screen'] if mode=='accept' else ['seed_review_passphrase_screen','seed_add_passphrase_screen','seed_review_passphrase_screen'] if mode=='edit' else ['large_icon_status_screen','seed_finalize_screen']
    assert driver.screens==['seed_add_passphrase_screen']+middle+['button_list_screen','main_menu_screen']
    assert controller.storage.num_seeds()==1
    seed=controller.storage.seeds[0]
    assert seed.passphrase==('k' if mode=='accept' else 'kl' if mode=='edit' else '')
    assert seed.get_fingerprint()==expected[seed.passphrase]
    controller.discard_seed(seed)
    assert controller.storage.num_seeds()==0
    print('@@PASS original-passphrase-'+mode+'-flow-real-lvgl',driver.hashes)
Renderer._instance=None;renderer=Renderer.get_instance();ui.overlays(0,0)
renderer.session.show_screen('MainMenuScreen',{'title':'Home','button_data':['Scan','Seeds','Tools','Settings']})
gc.collect()
