"""Original address explorer derivation, paging and QR return with public fixtures."""
import json
import sys
import tempfile
import time
import threading
from pathlib import Path
from types import SimpleNamespace
sys.path[:0]=[str(Path(__file__).resolve().parent),'/usr/lib/shieldsigner-camera/python','/opt/src']
from runtime import Runtime,install_view_dispatch
from seedsigner.models.seed import Seed
from seedsigner.models.seed_storage import SeedStorage
from seedsigner.models.settings import Settings
from seedsigner.models.settings_definition import SettingsConstants as C
from seedsigner.views.view import View
class Buttons:
    def load(self,keys):self.keys=keys;self.start=None;self.capture_qr=False
    def capture(self,expected):
        self.expected=expected;self.start=None;self.capture_qr=True;self.decoded=None;self.last=0

    def __call__(self):
        now=time.monotonic()
        if self.start is None:self.start=now
        if self.capture_qr:
            elapsed=now-self.start
            if self.decoded is not None:return {'KEY_PRESS'}
            if elapsed>20:raise TimeoutError('Signed-message QR pixels did not decode')
            if elapsed<1.5 or now-self.last<.2:return set()
            self.last=now
            with frame_lock:luma=bytes(frame[0::2])
            value=reader.decode_luma(luma,240,240)
            if value is not None:
                assert value==self.expected
                self.decoded=value
            return set()
        t=now-self.start-.5
        if t<0:return set()
        i=int(t/.35)
        if i>=len(self.keys):
            if t>len(self.keys)*.35+5:raise TimeoutError('Explorer navigation did not finish')
            return set()
        return {self.keys[i]} if t%.35<.22 else set()
buttons=Buttons();rectangles=0;hardware=None
frame=bytearray(115200);frame_lock=threading.Lock()
from shieldsigner_lcd import QrWorker
reader=QrWorker('/usr/lib/shieldsigner-camera/shieldsigner-qr-reader',5)
if '--display' in sys.argv:
    from luckfox import LuckfoxHardware
    hardware=LuckfoxHardware()
def pixels(area,data):
    global rectangles
    rectangles+=1
    x1,y1,x2,y2=area;stride=(x2-x1+1)*2
    with frame_lock:
        for row,y in enumerate(range(y1,y2+1)):frame[(y*240+x1)*2:(y*240+x2+1)*2]=data[row*stride:(row+1)*stride]
    if hardware is not None:hardware.pixels(area,data)
runtime=Runtime(sys.argv[1],pixels,buttons)
restore=install_view_dispatch(runtime,'/opt/src',Path(__file__).parent/'source-guards.json')
from seedsigner.controller import Controller
from seedsigner.views.view import BackStackView
from seedsigner.views.seed_views import SeedOptionsView
from seedsigner.views.tools_views import ToolsAddressExplorerAddressTypeView,ToolsAddressExplorerAddressListView,ToolsAddressExplorerAddressView
from embit import bip39,script,networks
from embit.descriptor import Descriptor
original_initialize=View._initialize;original_controller=Controller._instance
seeds=[];checks=[]
with tempfile.TemporaryDirectory(prefix='lvgl-explorer-') as temporary:
    Settings.SETTINGS_FILENAME=str(Path(temporary)/'settings.json');settings=Settings.get_instance()
    settings.set_value(C.SETTING__PERSISTENT_SETTINGS,C.OPTION__DISABLED,save=False)
    controller=SimpleNamespace(address_explorer_data=None,multisig_wallet_descriptor=None,resume_main_flow=None,back_stack=[])
    Controller._instance=controller
    def initialize(view):
        view.controller=controller;view.settings=settings
        view.renderer=SimpleNamespace(canvas_width=240,canvas_height=240)
        view.canvas_width=view.canvas_height=240;view.screen=None;view._redirect=None;view.is_screensaver_allowed=True
    View._initialize=initialize
    try:
        keys=[]
        for i in range(3):
            seed=Seed(bip39.mnemonic_from_bytes(bytes([i])*16).split());seeds.append(seed)
            xpub=seed.get_xpub(wallet_path="m/48h/0h/0h/2h",network=C.MAINNET).to_base58()
            keys.append('['+seed.get_fingerprint()+'/48h/0h/0h/2h]'+xpub+'/{0,1}/*')
        descriptor=Descriptor.from_string('wsh(sortedmulti(2,'+','.join(keys)+'))')
        controller.multisig_wallet_descriptor=descriptor
        for source in ('seed','descriptor'):
            for change in (False,True):
                print(json.dumps(dict(stage='explorer',source=source,change=change)),flush=True)
                view=ToolsAddressExplorerAddressTypeView(seed=seeds[0],script_type=C.NATIVE_SEGWIT) if source=='seed' else ToolsAddressExplorerAddressTypeView()
                buttons.load((['KEY_DOWN'] if change else [])+['KEY_PRESS']);destination=view.run()
                assert destination.View_cls is ToolsAddressExplorerAddressListView and destination.view_args['is_change']==change
                buttons.load(['KEY_DOWN']*20+['KEY_PRESS'])
                destination=destination.View_cls(**destination.view_args).run()
                assert destination.View_cls is ToolsAddressExplorerAddressListView and destination.view_args['start_index']==10
                print(json.dumps(dict(stage='next-page',source=source,change=change)),flush=True)
                args=dict(destination.view_args,selected_button_index=7)
                buttons.load(['KEY_PRESS']);destination=ToolsAddressExplorerAddressListView(**args).run()
                assert destination.View_cls is ToolsAddressExplorerAddressView
                assert destination.view_args['index']==17 and destination.view_args['start_index']==10
                address=destination.view_args['address'];saved_scroll=destination.view_args['parent_initial_scroll']
                if source=='descriptor':expected=descriptor.derive(17,branch_index=int(change)).address()
                else:
                    public=seeds[0].get_root().derive('m/84h/0h/0h/'+str(int(change))+'/17').key.get_public_key()
                    expected=script.p2wpkh(public).address(networks.NETWORKS['main'])
                assert address==expected
                buttons.capture(address.encode());destination=destination.View_cls(**destination.view_args).run()
                assert buttons.decoded==address.encode() and not any(frame)
                assert destination.View_cls is ToolsAddressExplorerAddressListView
                assert destination.view_args==dict(is_change=change,start_index=10,selected_button_index=7,initial_scroll=saved_scroll)
                before=list(controller.address_explorer_data['change_addrs' if change else 'receive_addrs'])
                buttons.load(['KEY_UP']*20+['KEY_PRESS']);destination=destination.View_cls(**destination.view_args).run()
                assert destination.View_cls is BackStackView
                assert controller.address_explorer_data['change_addrs' if change else 'receive_addrs']==before and len(before)==20
                checks.append(dict(source=source,change=change,paging=True,index=17,addressIndependentlyMatched=True,renderedQRBytesExact=True,selectionAndScrollReturned=True,cachedPageUnchanged=True))
        controller.back_stack=[SimpleNamespace(View_cls=SeedOptionsView),SimpleNamespace()]
        controller.resume_main_flow=Controller.FLOW__ADDRESS_EXPLORER
        view=ToolsAddressExplorerAddressTypeView(seed=seeds[0],script_type=C.NATIVE_SEGWIT)
        buttons.load(['KEY_UP']*15+['KEY_PRESS']);destination=view.run()
        assert destination.View_cls is BackStackView and controller.address_explorer_data is None and controller.resume_main_flow is None
        print(json.dumps(dict(passed=True,checks=checks,seedOptionsBackCleanup=True,physicalDisplay=hardware is not None,physicalButtons=False,opticalQualified=False,dependencyInitializationInjected=True,allScriptTypesQualified=False)),flush=True)
    finally:
        controller.address_explorer_data=None;controller.multisig_wallet_descriptor=None
        for seed in seeds:seed.wipe()
        Controller._instance=original_controller;View._initialize=original_initialize;restore();runtime.close();reader.close()
        if hardware is not None:hardware.close()
