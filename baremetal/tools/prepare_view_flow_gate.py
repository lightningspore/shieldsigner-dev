# SPDX-License-Identifier: MIT
"""Public numeric SeedQR pixels through actual original Controller/Views/LVGL."""
from pathlib import Path
import qrcode
root=Path(__file__).resolve().parents[1]
q=qrcode.QRCode(border=4,error_correction=qrcode.constants.ERROR_CORRECT_M)
q.add_data('0000'*11+'0003',optimize=0);q.make(fit=True)
rows=tuple(''.join('1' if value else '0' for value in row) for row in q.get_matrix())
code='''# SPDX-License-Identifier: MIT
# Generated public numeric SeedQR. Optical acquisition is not claimed by this gate.
from seedsigner_port.controller import Controller,StopFlowBasedTest
from seedsigner_port.renderer import Renderer
from seedsigner_port.view_core import MainMenuView,BackStackView
from seedsigner_port.view_scan import ScanView
from seedsigner_port.view_seed import SeedFinalizeView,SeedOptionsView
from seedsigner_port.navigation import Destination
import ui,json,hashlib,gc
'''
code+='rows='+repr(rows)+'''\nimage=bytearray(bytes([255])*(640*480*3//2))
width=len(rows)*6
left=(640-width)//2;top=(480-width)//2
for y,row in enumerate(rows):
    line=b''.join(bytes([0 if bit=='1' else 255])*6 for bit in row)
    for j in range(6):
        offset=(top+y*6+j)*640+left
        image[offset:offset+width]=line
class PixelCamera:
    active=False
    starts=0
    stops=0
    frames=0
    def start_video_stream_mode(self):
        assert not self.active
        self.active=True;self.starts+=1
    def read_video_stream(self):
        assert self.active
        self.frames+=1
        return image
    def stop_video_stream_mode(self):
        if self.active:self.stops+=1;self.active=False
source=PixelCamera()
class NativeDriver:
    def __init__(self):self.screens=[];self.frames=[]
    def __getattr__(self,name):return getattr(ui,name)
    def render(self,builder,encoded):
        cfg=json.loads(encoded)
        ui.render(builder,encoded)
        self.screens.append(builder)
        self.frames.append(hashlib.sha256(ui.framebuffer()).hexdigest())
        controller=Controller.get_instance()
        # Inject actual native key pulses, never substitute a selected result.
        if builder=='main_menu_screen':
            assert controller.resume_main_flow is None and controller.psbt is None
            if len(self.screens)>1:
                assert controller.storage.num_seeds()==1
                assert controller.storage.seeds[0].get_fingerprint()=='73c5da0a'
                assert not source.active
                raise StopFlowBasedTest()
            ui.key(10,True);ui.key(10,False)
        elif builder=='seed_finalize_screen':
            assert cfg['fingerprint']=='73c5da0a'
            assert not cfg['top_nav']['show_back_button']
            assert controller.storage.num_seeds()==0
            assert controller.storage.get_pending_seed().get_fingerprint()=='73c5da0a'
            ui.key(10,True);ui.key(10,False)
        elif builder=='button_list_screen':
            assert cfg['top_nav']['title']=='73c5da0a'
            assert controller.storage.num_seeds()==1 and controller.storage.get_pending_seed() is None
            assert len(controller.back_stack)==1 and controller.back_stack[0].View_cls is SeedOptionsView
            ui.key(20,True);ui.key(20,False)
            ui.key(10,True);ui.key(10,False)
        else:
            print('@@FLOW_UNEXPECTED',builder,cfg)
            raise StopFlowBasedTest()
driver=NativeDriver()
Renderer._instance=None
Renderer.configure_instance(backend=driver)
Controller._instance=None
controller=Controller.get_instance();controller._camera=source
controller.start(skip_startup_interstitials=True)
assert driver.screens==['main_menu_screen','seed_finalize_screen','button_list_screen','main_menu_screen']
assert source.starts==1 and source.stops==1 and source.frames==1 and not source.active
assert len(set(driver.frames))==3
assert controller.storage.num_seeds()==1
controller.discard_seed(controller.storage.seeds[0])
assert controller.storage.num_seeds()==0
print('@@FLOW_FRAME_HASHES',driver.frames)
print('@@PASS original-controller-scan-finalize-options-home-real-lvgl')
# Return to interactive Home after the deliberate test-only stop/blank-finally.
Renderer._instance=None
renderer=Renderer.get_instance()
ui.overlays(0,0)
renderer.session.show_screen('MainMenuScreen',{'title':'Home','button_data':['Scan','Seeds','Tools','Settings']})
gc.collect()
'''
(root/'micropython/view_flow_gate.py').write_text(code)
