# SPDX-License-Identifier: MIT
# PUBLIC synthetic inputs only. Preparation does not run or access hardware.
import ui,json,machine,gc
from seedsigner_port.controller import Controller,StopFlowBasedTest
from seedsigner_port.renderer import Renderer
from seedsigner_port.navigation import Destination
from seedsigner_port.camera_entropy_views import ToolsMenuView
from seedsigner_port.hardware_buttons import HardwareButtons
from seedsigner_port.settings_store import Settings,SettingsConstants as C
# BEGIN PUBLIC ORACLE
fixtures=[(1, 12, ['invest', 'spring', 'manage', 'emotion', 'blanket', 'sauce', 'walnut', 'various', 'cool', 'parent', 'excuse', 'average'], 'ccf4527d'), (1, 24, ['invest', 'spring', 'manage', 'emotion', 'blanket', 'sauce', 'walnut', 'various', 'cool', 'parent', 'excuse', 'average', 'trash', 'silver', 'loyal', 'solid', 'fork', 'canal', 'destroy', 'velvet', 'scissors', 'absent', 'theory', 'price'], 'ec5f0162'), (2, 12, ['spot', 'ride', 'plug', 'barrel', 'butter', 'napkin', 'goddess', 'energy', 'senior', 'unknown', 'onion', 'silk'], '3b623043'), (2, 24, ['spot', 'ride', 'plug', 'barrel', 'butter', 'napkin', 'goddess', 'energy', 'senior', 'unknown', 'onion', 'silly', 'awful', 'nuclear', 'tag', 'alter', 'supreme', 'run', 'mammal', 'catch', 'alter', 'camp', 'jacket', 'call'], '8069a4a7')]
dice_fixtures=[(12, '12345612345612345612345612345612345612345612345612', ['unveil', 'nice', 'picture', 'region', 'tragic', 'fault', 'cream', 'strike', 'tourist', 'control', 'recipe', 'tourist'], '85480bc5'), (24, '123456123456123456123456123456123456123456123456123456123456123456123456123456123456123456123456123', ['few', 'educate', 'sugar', 'bless', 'boring', 'random', 'strategy', 'waste', 'mutual', 'cargo', 'type', 'hawk', 'prefer', 'denial', 'scan', 'abstract', 'filter', 'extend', 'dignity', 'balcony', 'dust', 'unusual', 'correct', 'bubble'], '5545de0e')]
# END PUBLIC ORACLE

def pulse(key):ui.key(key,True);ui.key(key,False)
def choose(cfg,label):
    labels=[x if isinstance(x,str) else x['label'] for x in cfg['button_list']]
    for _ in range(labels.index(label)):pulse(18)
    pulse(10)
def back():pulse(20);pulse(10)
class Broker:
    def __init__(self):self.mask=0;self.now=0
    def read(self):return self.mask
    def clock(self):return self.now
    def step(self):self.now+=20
class Pixels:
    def __init__(self,broker,mode):
        self.broker=broker;self.mode=mode;self.cycle=0;self.buffer=bytearray(460800);self.running=False
    def start_video_stream_mode(self,*args,**kwargs):
        self.cycle+=1;self.reads=0;self.running=True
    def stop_video_stream_mode(self):self.running=False
    def read_video_stream(self):
        assert self.running
        self.reads+=1;self.broker.step();assert self.reads<30
        n=self.reads
        self.broker.mask=16 if n<6 or n>=8 else 0
        if self.mode=='cancel':self.broker.mask=4 if n>=2 else 0
        phase=self.cycle*16+n
        self.buffer[:307200]=bytes((i+phase)%256 for i in range(256))*1200
        self.buffer[307200:]=bytes([128])*153600
        if self.mode=='poor' and self.cycle==1 and n==10:self.buffer[:]=bytes(460800)
        return memoryview(self.buffer) # One borrowed buffer, overwritten on EVERY fetch.
class Driver:
    def __init__(self,broker,pixels,mode,count,words,fingerprint):
        self.broker=broker;self.pixels=pixels;self.mode=mode;self.count=count
        self.words=words;self.fingerprint=fingerprint;self.phase=None
        self.reviews=0;self.lengths=0;self.pages=[];self.failure=None;self.old=[];self.warnings=0
    def __getattr__(self,name):return getattr(ui,name)
    def scan_begin(self,caption):
        ui.scan_begin(caption);self.phase='review' if 'reshoot' in caption else 'live'
        self.broker.mask=16;self.review_ticks=0
        c=Controller.get_instance()
        if self.phase=='review':
            self.reviews+=1
            self.old.append((c.image_entropy_preview_frames,c.image_entropy_final_image))
            assert self.pixels.reads==10 # Held entry key cannot trigger capture.
        elif self.old:
            for samples,final in self.old:
                assert final.closed and not any(final.data)
                assert all(sample.closed and not any(sample.data) for sample in samples)
    def scan_frame(self,frame):ui.scan_frame(frame)
    def scan_end(self):ui.scan_end();self.phase=None
    def tick(self):
        self.broker.step()
        if self.phase=='review':
            self.review_ticks+=1;assert self.review_ticks<30
            if self.review_ticks<3:self.broker.mask=16
            elif self.review_ticks<5:self.broker.mask=0
            else:self.broker.mask=4 if self.mode=='reshoot' and self.reviews==1 else 8
        return ui.tick()
    def render(self,builder,encoded):
        try:self.checked_render(builder,encoded)
        except StopFlowBasedTest:raise
        except Exception as error:
            self.failure=(builder,type(error).__name__);raise StopFlowBasedTest()
    def checked_render(self,builder,encoded):
        self.broker.mask=0
        cfg=json.loads(encoded);ui.render(builder,encoded)
        if builder=='loading_spinner_screen':return # Original transient progress screen; no decision.
        title=cfg['top_nav']['title'];c=Controller.get_instance()
        if builder=='seed_words_screen':
            page=cfg['page_index'];assert cfg['words']==self.words[page*4:(page+1)*4]
            self.pages.append(page);pulse(10)
        elif builder=='seed_finalize_screen':
            assert cfg['fingerprint']==self.fingerprint;pulse(10)
        elif title=='Tools':
            if self.mode=='cancel' and self.pixels.cycle:back()
            else:choose(cfg,' New seed')
        elif title=='Mnemonic Length':
            self.lengths+=1
            if self.mode=='length-back' and self.lengths==1:back()
            else:choose(cfg,str(self.count)+' words')
        elif title=='Poor Entropy':
            assert self.mode=='poor';self.warnings+=1;pulse(10)
        elif title=='Verify Backup?':choose(cfg,'Skip')
        elif builder=='large_icon_status_screen':
            assert c.storage.get_pending_seed().mnemonic_list==self.words
            for samples,final in self.old:
                assert final.closed and not any(final.data)
                assert all(sample.closed and not any(sample.data) for sample in samples)
            assert c.image_entropy_preview_frames is None and c.image_entropy_final_image is None
            pulse(10)
        elif title==self.fingerprint:
            assert c.storage.num_seeds()==1 and c.storage.get_pending_seed() is None
            back()
        elif builder=='main_menu_screen':raise StopFlowBasedTest()
        else:raise ValueError('Unexpected public gate screen')

class DiceDriver(Driver):
    def checked_render(self,builder,encoded):
        cfg=json.loads(encoded)
        if builder=='loading_spinner_screen':ui.render(builder,encoded);return
        title=cfg['top_nav']['title']
        if title=='Tools':
            ui.render(builder,encoded)
            if self.lengths and self.mode in ('dice-back','dice-poor'):back()
            else:choose(cfg,'New seed')
        elif title=='Mnemonic Length' and self.lengths and self.mode in ('dice-back','dice-poor'):
            ui.render(builder,encoded);back()
        elif builder=='keyboard_screen':
            ui.render(builder,encoded)
            assert cfg['return_after_n_chars']==len(self.rolls) and cfg['cols']==3
            if self.mode=='dice-back':pulse(17);pulse(10);return
            current=0
            rolls='1'*len(self.rolls) if self.mode=='dice-poor' else self.rolls
            for char in rolls:
                target=int(char)-1
                if current//3!=target//3:
                    pulse(18 if target//3 else 17);current=(target//3)*3+current%3
                while current%3!=target%3:
                    pulse(19);current=(current//3)*3+(current+1)%3
                pulse(10)
        elif title=='Poor Entropy':
            assert self.mode=='dice-poor';ui.render(builder,encoded);self.warnings+=1;pulse(10)
        else:super().checked_render(builder,encoded)

settings=Settings.get_instance();old_warning=settings.get_value(C.SETTING__DIRE_WARNINGS)
settings.set_value(C.SETTING__DIRE_WARNINGS,C.OPTION__ENABLED,save=False)
try:
    for mode,count in (('normal',12),('normal',24),('reshoot',12),('length-back',12),('poor',12),('cancel',12)):
        cycle=2 if mode in ('reshoot','poor') else 1
        _,_,words,fingerprint=next(item for item in fixtures if item[:2]==(cycle,count))
        broker=Broker();pixels=Pixels(broker,mode)
        buttons=HardwareButtons(read_mask=broker.read,clock=broker.clock)
        HardwareButtons._instance=buttons
        Renderer._instance=None;driver=Driver(broker,pixels,mode,count,words,fingerprint)
        Renderer.configure_instance(backend=driver,buttons=buttons)
        Controller._instance=None;c=Controller.get_instance();c._camera=pixels
        machine.clear_reset_record();machine.set_reset_marker(0x43414d46)
        destination=Destination(ToolsMenuView);c.back_stack.append(destination)
        c.start(initial_destination=destination,skip_startup_interstitials=True)
        assert driver.failure is None,driver.failure
        assert not pixels.running and machine.last_reset() is None
        if mode=='cancel':
            assert c.storage.num_seeds()==0 and c.storage.get_pending_seed() is None
            assert not driver.pages
        else:
            assert driver.pages==list(range((count+3)//4)) and c.storage.num_seeds()==1
            seed=c.storage.seeds[0];assert seed.mnemonic_list==words;c.discard_seed(seed)
            assert driver.warnings==(1 if mode=='poor' else 0)
            if mode=='length-back':assert driver.reviews==2 and pixels.cycle==1
            if mode in ('reshoot','poor'):assert pixels.cycle==2
        print('@@PASS public-camera-source-native-ui',mode,count)
        gc.collect()
    for mode,count in (('dice',12),('dice',24),('dice-back',12),('dice-poor',12)):
        _,rolls,words,fingerprint=next(item for item in dice_fixtures if item[0]==count)
        broker=Broker();pixels=Pixels(broker,mode)
        buttons=HardwareButtons(read_mask=broker.read,clock=broker.clock)
        HardwareButtons._instance=buttons
        Renderer._instance=None;driver=DiceDriver(broker,pixels,mode,count,words,fingerprint);driver.rolls=rolls
        Renderer.configure_instance(backend=driver,buttons=buttons)
        Controller._instance=None;c=Controller.get_instance();c._camera=pixels
        machine.clear_reset_record();machine.set_reset_marker(0x44494345)
        destination=Destination(ToolsMenuView);c.back_stack.append(destination)
        c.start(initial_destination=destination,skip_startup_interstitials=True)
        assert driver.failure is None,driver.failure
        assert pixels.cycle==0 and machine.last_reset() is None
        if mode=='dice':
            assert driver.pages==list(range((count+3)//4)) and c.storage.num_seeds()==1
            seed=c.storage.seeds[0];assert seed.mnemonic_list==words;c.discard_seed(seed)
        else:
            assert not driver.pages and c.storage.num_seeds()==0 and c.storage.get_pending_seed() is None
            assert driver.warnings==(1 if mode=='dice-poor' else 0)
        print('@@PASS public-dice-source-native-ui',mode,count)
        gc.collect()

finally:
    settings.set_value(C.SETTING__DIRE_WARNINGS,old_warning,save=False)
    Renderer._instance=None;HardwareButtons._instance=None
print('@@PASS public-camera-flow-no-real-sensor-or-private-payloads')
