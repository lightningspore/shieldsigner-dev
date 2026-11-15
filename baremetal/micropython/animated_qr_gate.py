# SPDX-License-Identifier: MIT
# Public original Specter encoder through actual native QR frames/events/LCD.
import ui,qr,json,gc,hashlib,machine
from seedsigner_port.seed import Seed
from seedsigner_port.encode_qr import SpecterLegacyXPubQrEncoder
from seedsigner_port.qr_display import QRDisplayScreen
from seedsigner_port.renderer import Renderer
from seedsigner_port.settings_store import Settings,SettingsConstants as C
words = ['abandon', 'amount', 'liar', 'amount', 'expire', 'adjust', 'cage', 'candy', 'arch', 'gather', 'drum', 'buyer'] # PUBLIC independent oracle.
payload = "[4f4fbd02/84'/0'/0']zpub6s7nZx8HjMQ8mDGtp5XTgbRXhYa9sUBdojXGEEYaKX4xcGGv9QSJNeBSmYyK2vVNsZYTLxvybUffnJpu2naZ9LY33YDUu9qd52D7Rk7owcd" # PUBLIC independent oracle.
derivation = "m/84'/0'/0'" # PUBLIC independent oracle.
parts = ["p1of4 [4f4fbd02/84'/0'/0']zpub6s7nZx8HjMQ8mDGt", 'p2of4 p5XTgbRXhYa9sUBdojXGEEYaKX4xcGGv9QSJNeBS', 'p3of4 mYyK2vVNsZYTLxvybUffnJpu2naZ9LY33YDUu9qd', 'p4of4 52D7Rk7owcd'] # PUBLIC independent oracle.
def pulse(key):ui.key(key,True);ui.key(key,False)
def decoded_frame():
    raw=ui.framebuffer();pixels=bytearray(240*240)
    for i in range(240*240):
        value=(raw[i*2]<<8)|raw[i*2+1]
        pixels[i]=(((value>>11)*255//31)*77+(((value>>5)&63)*255//63)*150+((value&31)*255//31)*29)>>8
    return qr.decode(pixels,240,240)
class Driver:
    def __init__(self,tip=False):self.pushed=[];self.tip=tip;self.initial=None
    def __getattr__(self,name):return getattr(ui,name)
    def render(self,builder,encoded):
        cfg=json.loads(encoded);ui.render(builder,encoded)
        assert builder=='qr_display_screen' and cfg['density_control'] is False
        self.initial=bytes.fromhex(cfg['qr_data'])
        assert self.initial==parts[0].encode()
        if not self.tip:assert decoded_frame()==self.initial
    def qr_frame(self,frame):
        expected=parts[(len(self.pushed)+(0 if self.tip else 1))%len(parts)]
        ui.qr_frame(frame);assert bytes(frame)==expected.encode()
        assert decoded_frame()==bytes(frame)
        self.pushed.append(bytes(frame))
        if len(self.pushed)==4:pulse(20)
ui.init();ui.overlays(0,0);ui.overlays(5);ui.overlays(2)
record=machine.last_reset();print('@@ANIMATED_QR_RESET_BEFORE',record)
assert record is None or record['reason']==2
machine.clear_reset_record();machine.set_reset_marker(0x5152414e)
settings=Settings.get_instance();keys=(C.SETTING__QR_BRIGHTNESS,C.SETTING__QR_BRIGHTNESS_TIPS)
old=[settings.get_value(key) for key in keys]
seed=Seed(words,passphrase='PUBLIC')
try:
    for tip in (False,True):
        settings.set_value(C.SETTING__QR_BRIGHTNESS,255,save=False)
        settings.set_value(C.SETTING__QR_BRIGHTNESS_TIPS,C.OPTION__ENABLED if tip else C.OPTION__DISABLED,save=False)
        Renderer._instance=None;driver=Driver(tip);Renderer.configure_instance(backend=driver)
        encoder=SpecterLegacyXPubQrEncoder(seed=seed,derivation=derivation,network=C.MAINNET,sig_type=C.SINGLE_SIG,qr_density=C.DENSITY__LOW)
        assert encoder.parts==parts and encoder.xpubstring==payload
        result=QRDisplayScreen(encoder,cancel_on_back=True).display()
        assert result==1000 and len(driver.pushed)==4
        assert not any(ui.framebuffer()) and not ui.qr_tip_active()
        print('@@PASS original-specter-native-frames-tip-restart-left-cancel',tip)
    # New API validation and synchronous borrowed input ownership.
    cfg={'qr_data':parts[0].encode().hex(),'data_encoding':'hex','qr_mode':'auto','border':2,'initial_brightness':255,'density_control':False,'show_brightness_tips':False}
    ui.render('qr_display_screen',json.dumps(cfg))
    frame=bytearray(parts[1].encode());ui.qr_frame(frame)
    digest=hashlib.sha256(ui.framebuffer()).hexdigest();frame[:]=b'X'*len(frame);ui.tick()
    assert hashlib.sha256(ui.framebuffer()).hexdigest()==digest and decoded_frame()==parts[1].encode()
    for bad in (b'',b'x'*513):
        try:ui.qr_frame(bad);assert False
        except ValueError:pass
    ui.blank()
    try:ui.qr_frame(b'PUBLIC');assert False
    except RuntimeError:pass
    home={'top_nav':{'title':'Home'},'button_list':['Scan','Seeds','Tools','Settings']}
    def cycle():
        ui.render('qr_display_screen',json.dumps(cfg))
        for part in parts:ui.qr_frame(part.encode())
        ui.render('main_menu_screen',json.dumps(home))
    cycle();cycle();baseline=ui.status()['heap_bytes']
    for _ in range(20):
        cycle();gc.collect();assert ui.status()['heap_bytes']==baseline
    print('@@PASS native-qr-borrowed-frame-guards-20-teardowns-stable',baseline)
    assert machine.last_reset() is None
finally:
    seed.wipe()
    for key,value in zip(keys,old):settings.set_value(key,value,save=False)
Renderer._instance=None;r=Renderer.get_instance();ui.overlays(0,0)
r.session.show_screen('MainMenuScreen',{'title':'Home','button_data':['Scan','Seeds','Tools','Settings']})
