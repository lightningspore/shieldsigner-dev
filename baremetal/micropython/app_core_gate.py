# SPDX-License-Identifier: MIT
# Public fixtures only. Actual frozen original storage and native LVGL overlays.
from seedsigner_port.seed_storage import SeedStorage
from seedsigner_port.seed import Seed
from seedsigner_port.encrypted_storage import EncryptedQRStorage
from seedsigner_port.button_options import ButtonOption,ButtonOptionWithoutTranslation
from seedsigner_port.singleton import Singleton,ConfigurableSingleton
from seedsigner_port.session_keys import clear_signing_keys
from seedsigner_port.decode_platform import FeatureUnavailable,dependency
from seedsigner_port.hardware_buttons import HardwareButtons
from seedsigner_port.gui_constants import GUIConstants
from seedsigner_port import clock
import ui,time,gc
ui.init() # Initializes the actual PCB input pins before HardwareButtons reads.
words=('abandon '*11+'about').split()
storage=SeedStorage()
assert storage.num_seeds()==0 and storage.get_pending_seed() is None
assert storage.validate_mnemonic(words) and not storage.validate_mnemonic(['abandon']*12)
storage.init_pending_mnemonic()
assert storage.pending_mnemonic_length==12
for index in range(12):storage.update_pending_mnemonic('abandon',index)
assert storage.get_pending_mnemonic_fingerprint() is None
for index,word in enumerate(words):storage.update_pending_mnemonic(word,index)
copy=storage.pending_mnemonic
copy[0]='invalid'
assert storage.get_pending_mnemonic_word(0)=='abandon'
assert storage.get_pending_mnemonic_fingerprint()=='73c5da0a'
storage.convert_pending_mnemonic_to_pending_seed()
assert storage.pending_mnemonic==[]
assert storage.get_pending_seed().get_fingerprint()=='73c5da0a'
first=storage.finalize_pending_seed()
assert storage.seeds==[first] and storage.get_pending_seed() is None
second=Seed(words)
storage.set_pending_seed(second)
assert storage.finalize_pending_seed() is second
assert storage.num_seeds()==1 and storage.seeds[0] is first
second.wipe()
third=Seed(words,passphrase='public fixture')
alias=third.seed_bytes
storage.set_pending_seed(third)
storage.clear_pending_seed()
assert alias==bytes(64) and storage.get_pending_seed() is None
share='duckling enlarge academic academic agency result length solution fridge kidney coal piece deal husband erode duke ajar critical decision keyboard'
storage.add_slip39_share_mnemonic(share)
assert storage.slip39_shares_entered==1 and storage.slip39_total_needed==1
storage.discard_pending_slip39_shares()
storage.init_pending_slip39_share(20)
assert storage.pending_slip39_share_length==20
storage.update_pending_slip39_share('academic',0)
assert storage.get_pending_slip39_word(0)=='academic'
storage.discard_pending_slip39_shares()
assert storage.slip39_shares_entered==0 and storage.slip39_total_needed is None
first.wipe()
storage.seeds=[]
box=EncryptedQRStorage()
box.set_encryptedqr('public fixture')
assert box.encryptedqr=='public fixture'
box.clear_encryptedqr()
assert box.encryptedqr is None
option=ButtonOption('Done',return_data=7)
assert option==ButtonOption('Done',return_data=7)
assert option!=ButtonOption('Done',return_data=8)
assert option!=ButtonOptionWithoutTranslation('Done',return_data=7)
class S(Singleton):pass
assert S.get_instance() is S.get_instance()
class C(ConfigurableSingleton):pass
raised=False
try:C.get_instance()
except Exception:raised=True
assert raised
class State:pass
state=State();state.luckfox_release_keys={'public':1};state.luckfox_bip85_cache={'public':2}
clear_signing_keys(state)
assert state.luckfox_release_keys is None and state.luckfox_bip85_cache=={}
try:dependency('seedsigner.models.encryptedqr','EncryptedQR');assert False
except FeatureUnavailable:pass
assert GUIConstants.EDGE_PADDING==8
buttons=HardwareButtons.get_instance()
assert buttons is HardwareButtons.get_instance()
before=clock.time();time.sleep_ms(20)
buttons.update_last_input_time()
assert clock.time()>=before and buttons.last_input_time>=int(before*1000)
print('@@PASS original-app-storage-options-singletons')
ui.init()
ui.render('main_menu_screen','{"top_nav":{"title":"Home"},"button_list":["Scan","Seeds","Tools","Settings"]}')
ui.overlays(0,0)
baseline=ui.status()['heap_bytes']
for iteration in range(3):
    ui.overlays(1)
    assert ui.overlays(4)==1
    ui.toast('Public integration test','',0x00ff00,0xffffff,0)
    assert ui.overlays(4)==0 and ui.overlays(6)==1
    ui.overlays(5)
    assert ui.overlays(6)==0
ui.toast('Timed toast','',0x00ff00,0xffffff,80)
time.sleep_ms(200);ui.tick()
assert ui.overlays(6)==0
ui.overlays(3)
ui.overlays(0,80)
time.sleep_ms(250);ui.tick()
assert ui.overlays(4)==1
ui.key(10,True);ui.key(10,False)
assert ui.overlays(4)==0
assert ui.event() is None # Actual saver consumes the wake key.
ui.overlays(0,0)
for args in ((7,),(-1,),(0,-1)):
    try:ui.overlays(*args);assert False
    except ValueError:pass
for text in ('x'*256,'bad\x00text'):
    try:ui.toast(text,'',0,0,1);assert False
    except ValueError:pass
# Font and glyph caches are now warm; repeated construction must be stable.
warm=ui.status()['heap_bytes']
for iteration in range(20):
    ui.overlays(1)
    ui.toast('Public integration test','',0x00ff00,0xffffff,0)
    ui.overlays(5)
    ui.overlays(2)
    gc.collect()
    assert ui.status()['heap_bytes']==warm
print('@@OVERLAY_STABLE_CYCLES',20,warm)
gc.collect()
print('@@OVERLAY_HEAP',baseline,ui.status()['heap_bytes'])
print('@@PASS native-overlays-lifecycle-expiry-wake')
