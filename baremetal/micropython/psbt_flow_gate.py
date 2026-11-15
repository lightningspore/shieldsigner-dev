# SPDX-License-Identifier: MIT
# PUBLIC test seed/PSBT only. Generated gate; NOT automatically executed.
import ui,qr,json,hashlib,gc,machine
from embit import psbt,ec
from seedsigner_port.seed import Seed
from seedsigner_port.controller import Controller
from seedsigner_port.renderer import Renderer
from seedsigner_port.navigation import Destination
from seedsigner_port.view_psbt import PSBTOverviewView,PSBTFinalizeView,PSBTSignedQRDisplayView
from seedsigner_port.settings_store import Settings,SettingsConstants as C
from seedsigner_port.psbt_parser import PSBTParser
from seedsigner_port.ur2.ur_decoder import URDecoder
from urtypes.crypto import PSBT as URPSBT
PUBLIC_FIXTURE = {'name': 'NORMAL-1_p2wpkh', 'wireHex': '70736274ff0100710200000001fe00078d8aa9643c7f573f16bf6ba76e6f6df2ab85e0cacb3d47e42bd84113220000000000ffffffff02f8dcfa0200000000160014dd35f1cf4a4f03b9448c88b6bc5e2cccdea581ebf8dcfa02000000001600149c90f934ea51fa0f6504177043e0908da6929983000000000001011f00e1f505000000001600143e34985dca6fddc9fb369940e4c7d8e2873f529c220603025324888e429ab8e3dbaf1f7802648b9cd01e9b418485c5fa4c1b9b5700e1a61873c5da0a5400008000000080000000800100000000000000000101160014dd35f1cf4a4f03b9448c88b6bc5e2cccdea581eb0001011600149c90f934ea51fa0f6504177043e0908da6929983220203e775fd51f0dfb8cd865d9ff1cca2a158cf651fe997fdc9fee9c1d3b5e995ea771873c5da0a540000800000008000000080000000000100000000', 'signedSha256': 'd512673ce02c54f8b054d9f15b0d8c09204d8a198bc26339d14230eb77093852', 'trimmedSha256': 'c86bf4d32a2996d0eaca3ee75b8969a5583d62b0b5d81c3d7a676f10f943882d', 'finalTxSha256': 'a87eac4f9452e56721c3bafde305a573af3e977d32e44657ecfdd2200c1581e2', 'inputs': 1}

def pulse(key):ui.key(key,True);ui.key(key,False)
def decoded_frame():
    raw=ui.framebuffer();pixels=bytearray(240*240)
    for i in range(240*240):
        value=(raw[2*i]<<8)|raw[2*i+1]
        pixels[i]=(((value>>11)*255//31)*77+(((value>>5)&63)*255//63)*150+((value&31)*255//31)*29)>>8
    return qr.decode(pixels,240,240)
class Driver:
    def __init__(self,decline):self.decline=decline;self.builders=[];self.decoder=URDecoder();self.qrframes=0;self.approvals=0
    def __getattr__(self,name):return getattr(ui,name)
    def receive(self,payload):
        # Decode actual pixels after the native renderer displays each UR part.
        assert decoded_frame()==bytes(payload)
        self.decoder.receive_part(bytes(payload).decode())
        self.qrframes+=1
        assert self.qrframes<100
        if self.decoder.is_success():pulse(10)
    def render(self,builder,encoded):
        cfg=json.loads(encoded);ui.render(builder,encoded);self.builders.append(builder)
        if builder=='loading_spinner_screen':return
        if builder=='psbt_overview_screen':
            assert cfg['num_inputs']==1 and len(cfg['destination_addresses'])==1
        elif builder=='psbt_math_screen':
            assert cfg['amounts']['fee']=='10000'
        elif builder=='psbt_change_details_screen':assert cfg['is_verified'] is True
        elif builder=='psbt_address_details_screen':pass
        elif builder=='large_icon_status_screen':
            assert cfg['top_nav']['title']=='Sign Transaction',cfg
            assert self.approvals==0 and PSBTParser.sig_count(c.psbt)==0
            if self.decline:pulse(20);return
            self.approvals+=1
            # Actual native scroll/navigation events expose the button; only the
            # native screen session decides when Select returns an approval.
            for _ in range(12):pulse(18)
        elif builder=='qr_display_screen':
            assert not self.decline and self.approvals==1
            self.receive(bytes.fromhex(cfg['qr_data']));return
        else:raise AssertionError('Unreviewed native PSBT route: '+builder)
        pulse(10)
    def qr_frame(self,payload):ui.qr_frame(payload);self.receive(payload)

ui.init();ui.overlays(0,0);ui.overlays(5);ui.overlays(2)
record=machine.last_reset();print('@@PSBT_FLOW_RESET_BEFORE',record)
assert record is None or record['reason']==2
machine.clear_reset_record();machine.set_reset_marker(0x5053464c)
settings=Settings.get_instance()
keys=(C.SETTING__NETWORK,C.SETTING__QR_BRIGHTNESS,C.SETTING__QR_BRIGHTNESS_TIPS,C.SETTING__QR_DENSITY)
old=[settings.get_value(k) for k in keys]
try:
    for key,value in zip(keys,(C.MAINNET,255,C.OPTION__DISABLED,C.DENSITY__LOW)):settings.set_value(key,value,save=False)
    for decline in (True,False):
        Renderer._instance=None;driver=Driver(decline);Renderer.configure_instance(backend=driver)
        Controller._instance=None;c=Controller.get_instance()
        seed=Seed(['abandon']*11+['about']);c.storage.set_pending_seed(seed);c.storage.finalize_pending_seed()
        wire=bytes.fromhex(PUBLIC_FIXTURE['wireHex']);original=psbt.PSBT.parse(wire)
        c.psbt=psbt.PSBT.parse(wire);c.psbt_seed=seed;c.psbt_parser=None;c.psbt_sign_with_satochip=False
        destination=Destination(PSBTOverviewView);seen=[]
        try:
            for step in range(16):
                name=destination.View_cls.__name__;seen.append(name)
                result=destination.run()
                if name=='PSBTFinalizeView' and decline:
                    assert result.View_cls.__name__=='BackStackView'
                    assert c.psbt.serialize()==wire and PSBTParser.sig_count(c.psbt)==0
                    assert driver.approvals==driver.qrframes==0
                    print('@@PASS native-original-psbt-back-unsigned',seen);break
                if name=='PSBTSignedQRDisplayView':
                    assert result.View_cls.__name__=='MainMenuView' and result.clear_history
                    assert driver.decoder.is_success() and driver.qrframes>0
                    exported=bytes(URPSBT.from_cbor(driver.decoder.result_message().cbor).data)
                    assert exported==c.psbt.serialize()
                    assert hashlib.sha256(exported).hexdigest()==PUBLIC_FIXTURE['trimmedSha256']
                    signed=psbt.PSBT.parse(exported)
                    assert PSBTParser.sig_count(signed)==PUBLIC_FIXTURE['inputs']
                    count=0
                    for index,inp in enumerate(signed.inputs):
                        for pub,sig in inp.partial_sigs.items():
                            assert pub.verify(ec.Signature.parse(sig[:-1]),original.sighash(index,sighash=sig[-1]));count+=1
                    assert count==PUBLIC_FIXTURE['inputs']
                    assert 'PSBTMathView' in seen and 'PSBTAddressDetailsView' in seen and 'PSBTChangeDetailsView' in seen
                    print('@@PASS native-original-psbt-approve-sign-pixel-ur-export',seen,driver.qrframes,count);break
                assert result.View_cls.__name__!='BackStackView'
                destination=result
            else:raise AssertionError('Original PSBT flow did not finish')
        finally:
            c.discard_seed(seed);c.psbt=None;c.psbt_seed=None;c.psbt_parser=None
        assert c.storage.num_seeds()==0 and machine.last_reset() is None
        gc.collect()
finally:
    for key,value in zip(keys,old):settings.set_value(key,value,save=False)
Renderer._instance=None;r=Renderer.get_instance();ui.overlays(0,0)
r.session.show_screen('MainMenuScreen',{'title':'Home','button_data':['Scan','Seeds','Tools','Settings']})
print('@@PSBT_FLOW_GATE_PASS public-only no-clock-no-card')
