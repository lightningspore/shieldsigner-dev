# SPDX-License-Identifier: MIT
# Public generated mnemonic fixtures; real native events and original View logic.
import ui,json,gc,machine
from seedsigner_port.controller import Controller,StopFlowBasedTest
from seedsigner_port.renderer import Renderer
from seedsigner_port.navigation import Destination
from seedsigner_port.view_seed import SeedBackupView,SeedWordsWarningView
from seedsigner_port.seed import Seed
from seedsigner_port.settings_store import Settings,SettingsConstants as C
from seedsigner_port import quiz_random
fixtures = [(['abandon', 'amount', 'liar', 'amount', 'expire', 'adjust', 'cage', 'candy', 'arch', 'gather', 'drum', 'buyer'], '05d027a5'), (['abandon', 'amount', 'liar', 'amount', 'expire', 'adjust', 'cage', 'candy', 'arch', 'gather', 'drum', 'bullet', 'absurd', 'math', 'exhibit'], '45db4809'), (['abandon', 'amount', 'liar', 'amount', 'expire', 'adjust', 'cage', 'candy', 'arch', 'gather', 'drum', 'bullet', 'absurd', 'math', 'era', 'live', 'bid', 'rib'], '28c3d664'), (['abandon', 'amount', 'liar', 'amount', 'expire', 'adjust', 'cage', 'candy', 'arch', 'gather', 'drum', 'bullet', 'absurd', 'math', 'era', 'live', 'bid', 'rhythm', 'alien', 'crouch', 'saddle'], 'a8ae0bd3'), (['abandon', 'amount', 'liar', 'amount', 'expire', 'adjust', 'cage', 'candy', 'arch', 'gather', 'drum', 'bullet', 'absurd', 'math', 'era', 'live', 'bid', 'rhythm', 'alien', 'crouch', 'range', 'attend', 'journey', 'unaware'], '3e1f3ae0')] # PUBLIC CPython embit0.8.0 oracle.
def pulse(key):ui.key(key,True);ui.key(key,False)
def choose(cfg,label):
    labels=[x if isinstance(x,str) else x['label'] for x in cfg['button_list']]
    index=labels.index(label)
    for _ in range(index):pulse(18)
    pulse(10)
# Standard pseudorandom behavior only; never entropy qualification.
for size in (0,1,2,3,12,24):
    quiz_random.seed(723)
    a=list(range(size));quiz_random.shuffle(a)
    quiz_random.seed(723)
    b=list(range(size));quiz_random.shuffle(b)
    assert a==b and sorted(a)==list(range(size))
for _ in range(100):assert 0<=quiz_random.random()<1
print('@@PASS native-quiz-prng-permutations-and-repeatability-not-entropy')
class Driver:
    def __init__(self,mode,words,fingerprint,pending):
        self.mode=mode;self.words=words;self.fingerprint=fingerprint;self.pending=pending
        self.pages=[];self.confirmed=[];self.failed_once=False;self.mistakes=0
        self.prompts=0;self.warnings=0;self.success=False;self.finalized=False;self.failure=None
    def __getattr__(self,name):return getattr(ui,name)
    def render(self,builder,encoded):
        try:self.checked_render(builder,encoded)
        except StopFlowBasedTest:raise
        except Exception as error:
            self.failure=(builder,type(error).__name__);raise StopFlowBasedTest()
    def checked_render(self,builder,encoded):
        cfg=json.loads(encoded);ui.render(builder,encoded)
        c=Controller.get_instance();title=cfg['top_nav']['title']
        if builder=='seed_words_screen':
            page=cfg['page_index'];total=(len(self.words)+3)//4
            assert cfg['words']==self.words[page*4:(page+1)*4]
            assert cfg['start_number']==page*4+1 and title=='Seed Words: %d/%d'%(page+1,total)
            assert 0<=page<total and 1<=len(cfg['words'])<=4
            self.pages.append(page)
            assert c.storage.num_seeds()==(0 if self.pending else 1)
            if self.mode=='back' and self.pages==[0,1]:pulse(20);pulse(10)
            else:pulse(10)
        elif builder=='seed_finalize_screen':
            assert self.pending and cfg['fingerprint']==self.fingerprint
            assert c.storage.get_pending_seed() is not None and c.storage.num_seeds()==0
            self.finalized=True;pulse(10)
        elif builder=='large_icon_status_screen':
            if title=='Backup Verified':
                assert self.mode=='verify' and sorted(self.confirmed)==list(range(len(self.words)))
                self.success=True;pulse(10)
            elif title=='Verification Error':
                assert self.failed_once and not self.mistakes
                self.mistakes+=1;choose(cfg,'Try again')
            else:
                assert 'private' in cfg.get('text','')
                self.warnings+=1;pulse(10)
        elif builder=='button_list_screen':
            if title=='Backup Seed':choose(cfg,'View seed words')
            elif title=='Verify Backup?':
                self.prompts+=1
                assert not cfg['top_nav']['show_back_button'] and cfg['text']
                if self.mode=='review' and self.prompts==1:choose(cfg,'Review')
                else:choose(cfg,'Verify' if self.mode=='verify' else 'Skip')
            elif title.startswith('Verify Word #'):
                assert self.mode=='verify'
                index=int(title.split('#')[1])-1;assert 0<=index<len(self.words)
                labels=[x if isinstance(x,str) else x['label'] for x in cfg['button_list']]
                assert not cfg['top_nav']['show_back_button'] and len(labels)==4
                if not self.failed_once:
                    wrong=next(word for word in labels if word!=self.words[index])
                    self.failed_once=True;choose(cfg,wrong)
                else:
                    assert index not in self.confirmed
                    self.confirmed.append(index);choose(cfg,self.words[index])
            else:
                assert title==self.fingerprint and c.storage.num_seeds()==1
                assert c.storage.get_pending_seed() is None
                if self.pending:assert self.finalized
                if self.mode=='verify':
                    assert self.success and self.mistakes==1
                    if not self.pending:assert len(c.back_stack)==1
                pulse(20);pulse(10)
        elif builder=='main_menu_screen':raise StopFlowBasedTest()
        else:raise ValueError('Unexpected builder')
settings=Settings.get_instance();old=settings.get_value(C.SETTING__DIRE_WARNINGS)
settings.set_value(C.SETTING__DIRE_WARNINGS,C.OPTION__ENABLED,save=False)
cases=[('skip',fixture,False) for fixture in fixtures]+[(mode,fixtures[0],pending) for mode,pending in (('back',False),('review',False),('skip',True),('verify',False),('verify',True))]
try:
    for mode,fixture,pending in cases:
        words,fingerprint=fixture
        Renderer._instance=None;driver=Driver(mode,words,fingerprint,pending);Renderer.configure_instance(backend=driver)
        Controller._instance=None;c=Controller.get_instance()
        seed=Seed(list(words));assert seed.get_fingerprint()==fingerprint
        c.storage.set_pending_seed(seed)
        if not pending:c.storage.finalize_pending_seed()
        machine.clear_reset_record();machine.set_reset_marker(0x4241434b)
        destination=Destination(SeedWordsWarningView,view_args={'seed':None}) if pending else Destination(SeedBackupView,view_args={'seed':seed})
        c.back_stack.append(destination) # A running non-Home View has its history entry.
        c.start(initial_destination=destination,skip_startup_interstitials=True)
        assert driver.failure is None,driver.failure
        total=(len(words)+3)//4
        expected=list(range(total))
        if mode=='back':expected=[0,1]+expected
        if mode=='review':expected*=2
        assert driver.pages==expected
        assert driver.warnings==(2 if mode=='review' else 1)
        assert c.storage.num_seeds()==1 and c.storage.get_pending_seed() is None
        assert machine.last_reset() is None
        c.discard_seed(seed);assert c.storage.num_seeds()==0
        print('@@PASS original-backup-'+mode+'-real-lvgl',len(words),pending,len(driver.pages),len(driver.confirmed))
finally:settings.set_value(C.SETTING__DIRE_WARNINGS,old,save=False)
# Force the existing inactivity policy while private words are actually shown.
from seedsigner_port.hardware_buttons import HardwareButtons
from seedsigner_port import clock
class IdleDriver(Driver):
    def checked_render(self,builder,encoded):
        if builder!='seed_words_screen':return super().checked_render(builder,encoded)
        cfg=json.loads(encoded);ui.render(builder,encoded)
        assert cfg['words']==self.words[:4]
        self.pages.append(0)
        HardwareButtons.get_instance().last_input_time=int(clock.time()*1000)-60001
for pending in (False,True):
    words,fingerprint=fixtures[0]
    Renderer._instance=None;driver=IdleDriver('idle',words,fingerprint,pending);Renderer.configure_instance(backend=driver)
    Controller._instance=None;c=Controller.get_instance()
    seed=Seed(list(words));alias=seed.seed_bytes;c.storage.set_pending_seed(seed)
    if not pending:c.storage.finalize_pending_seed()
    old_timer=settings.get_value(C.SETTING__WIPE_TIMER)
    HardwareButtons.get_instance().last_input_time=int(clock.time()*1000)
    settings.set_value(C.SETTING__WIPE_TIMER,1,save=False)
    machine.clear_reset_record();machine.set_reset_marker(0x4241434b)
    destination=Destination(SeedWordsWarningView,view_args={'seed':None if pending else seed})
    c.back_stack.append(destination)
    try:c.start(initial_destination=destination,skip_startup_interstitials=True)
    finally:settings.set_value(C.SETTING__WIPE_TIMER,old_timer,save=False)
    assert driver.failure is None,driver.failure
    assert driver.pages==[0] and alias==bytes(64)
    assert c.storage.num_seeds()==0 and c.storage.get_pending_seed() is None
    assert machine.last_reset() is None
    print('@@PASS original-backup-word-idle-wipe-home',pending)
Renderer._instance=None;r=Renderer.get_instance();ui.overlays(0,0)
r.session.show_screen('MainMenuScreen',{'title':'Home','button_data':['Scan','Seeds','Tools','Settings']})
gc.collect()
