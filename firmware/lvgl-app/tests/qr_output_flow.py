"""Original encoders -> LVGL -> transmitted LCD pixels -> actual ZXing decoder.

Public fixtures only; no captured pixels or payloads written to the receipt.
This is a rendered-pixel check, not a photograph/optical camera qualification.
"""
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import time
sys.path[:0]=[str(Path(__file__).resolve().parent),'/usr/lib/shieldsigner-camera/python','/opt/src']
restore_policy=None
if '--dependencies' in sys.argv:
    from dependency_policy import install as dependencies
    restore_policy=dependencies('/opt/src',Path(__file__).parent/'source-guards.json')
from resources import process_snapshot
from shieldsigner_lcd import QrWorker
from runtime import Runtime,install_view_dispatch
from qr_output import part_bytes
from seedsigner.gui.screens.screen import QRDisplayScreen
from seedsigner.models.encode_qr import CompactSeedQrEncoder,SeedQrEncoder,GenericStaticQrEncoder,UrPsbtQrEncoder
from seedsigner.models.decode_qr import DecodeQR
from seedsigner.models.settings import Settings
from seedsigner.models.settings_definition import SettingsConstants as C
from embit import psbt,transaction,script
frame=bytearray(115200);lock=threading.Lock();hardware=None
if '--display' in sys.argv:
    from luckfox import LuckfoxHardware
    hardware=LuckfoxHardware()
def pixels(area,data):
    x1,y1,x2,y2=area;stride=(x2-x1+1)*2
    with lock:
        for row,y in enumerate(range(y1,y2+1)):frame[(y*240+x1)*2:(y*240+x2+1)*2]=data[row*stride:(row+1)*stride]
    if hardware is not None:hardware.pixels(area,data)
class Observed:
    def __init__(self,encoder):self.encoder=encoder;self.parts=[];self.times=[];self.restarts=0
    def next_part(self):
        part=self.encoder.next_part();self.parts.append(part_bytes(part));self.times.append(time.monotonic());return part
    def seq_len(self):return self.encoder.seq_len()
    def restart(self):self.restarts+=1;self.encoder.restart()
class Buttons:
    def capture(self,encoder,decoder=None):
        self.start=None;self.encoder=encoder;self.decoder=decoder;self.captured=[];self.complete=False;self.timed=None;self.last=0
    def plan(self,keys):self.start=None;self.timed=keys
    def __call__(self):
        now=time.monotonic()
        if self.start is None:self.start=now
        elapsed=now-self.start
        if self.timed is not None:
            t=elapsed-.2
            if t<0:return set()
            i=int(t/.2)
            if i>=len(self.timed):
                if t>len(self.timed)*.2+5:raise TimeoutError('QR key plan stalled')
                return set()
            return {self.timed[i]} if t%.2<.1 else set()
        if self.complete:return {'KEY_PRESS'}
        if elapsed>20:raise TimeoutError('Rendered QR did not decode')
        if elapsed<1.5 or now-self.last<.12:return set()
        self.last=now
        # QR pixels are grayscale. The high RGB565 byte is a monotonic luma
        # approximation; slice in C rather than allocating per-pixel Python objects.
        with lock:luma=bytes(frame[0::2])
        data=reader.decode_luma(luma,240,240)
        if data is None:return set()
        assert data in self.encoder.parts,'Rendered QR bytes differ from original encoder'
        self.captured.append(data)
        if self.decoder is not None:
            self.decoder.add_data(data);self.complete=bool(self.decoder.is_complete)
        else:self.complete=True
        return set()
buttons=Buttons();reader=QrWorker('/usr/lib/shieldsigner-camera/shieldsigner-qr-reader',5)
runtime=Runtime(sys.argv[1],pixels,buttons)
restore=install_view_dispatch(runtime,'/opt/src',Path(__file__).parent/'source-guards.json')
checks=[];memory=[]
def sample(stage):
    if '--memory-cycles' not in sys.argv:return
    import gc
    before=process_snapshot(os.getpid());collected=gc.collect()
    memory.append(dict(stage=stage,python=before,afterCollection=process_snapshot(os.getpid()),native=process_snapshot(runtime.host.child.pid),collectedObjects=collected))
with tempfile.TemporaryDirectory(prefix='lvgl-qr-output-test-') as temporary:
    Settings.SETTINGS_FILENAME=str(Path(temporary)/'settings.json')
    settings=Settings.get_instance();settings.set_value(C.SETTING__PERSISTENT_SETTINGS,C.OPTION__DISABLED,save=False)
    settings.set_value(C.SETTING__QR_BRIGHTNESS,62,save=False)
    settings.set_value(C.SETTING__QR_BRIGHTNESS_TIPS,C.OPTION__ENABLED,save=False)
    try:
        words=['abandon']*11+['about']
        for name,encoder in [('compact-binary',CompactSeedQrEncoder(mnemonic=words)),('numeric-seed',SeedQrEncoder(mnemonic=words)),('address-text',GenericStaticQrEncoder(data='1BoatSLRHtKNngkdXEeobR76b53LETtpyT'))]:
            observed=Observed(encoder);buttons.capture(observed)
            assert QRDisplayScreen(qr_encoder=observed).display() is None
            assert len(buttons.captured)>0 and not any(frame)
            checks.append(dict(name=name,renderedBytesExact=True,capturedFrames=len(buttons.captured),blackOnExit=True))
        tx=transaction.Transaction(vin=[transaction.TransactionInput(bytes(32),0)],vout=[transaction.TransactionOutput(0,script.Script(b'\x6a\x4c\xc8'+bytes(range(200))))])
        unsigned=psbt.PSBT(tx);observed=Observed(UrPsbtQrEncoder(psbt=unsigned));decoder=DecodeQR();buttons.capture(observed,decoder)
        assert observed.seq_len()>1
        assert QRDisplayScreen(qr_encoder=observed).display() is None
        assert decoder.get_data_psbt()==unsigned.serialize()
        assert observed.restarts>=1 and observed.times[1]-observed.times[0]>=1.0
        checks.append(dict(name='animated-public-psbt',renderedBytesExact=True,assembledOriginalPSBT=True,capturedFrames=len(buttons.captured),tipHoldAndRestart=True,generatedFrames=len(observed.parts)))
        sample('after-initial-exports')
        saved=[];original_set=settings.set_value
        def save(attr_name,value,**kwargs):
            if attr_name==C.SETTING__QR_BRIGHTNESS:saved.append(value)
            return original_set(attr_name,value,**kwargs)
        settings.set_value=save
        buttons.plan(['KEY_DOWN','KEY_UP','KEY_PRESS'])
        assert QRDisplayScreen(qr_encoder=GenericStaticQrEncoder(data='public')).display() is None
        assert saved==[62] and settings.get_value(C.SETTING__QR_BRIGHTNESS)==62
        checks.append(dict(name='brightness-save-on-exit',savedOnce=True,finalBrightness=62))
        buttons.plan(['KEY_LEFT'])
        assert QRDisplayScreen(qr_encoder=GenericStaticQrEncoder(data='public'),cancel_on_back=True).display()==1000
        buttons.plan(['KEY_RIGHT'])
        assert QRDisplayScreen(qr_encoder=GenericStaticQrEncoder(data='public'),cancel_on_back=True).display() is None
        checks.append(dict(name='cancel-left-only',leftReturnsBack=True,rightReturnsNone=True))
        if '--memory-cycles' in sys.argv:
            settings.set_value(C.SETTING__QR_BRIGHTNESS_TIPS,C.OPTION__DISABLED,save=False)
            for cycle in range(5):
                observed=Observed(CompactSeedQrEncoder(mnemonic=words));buttons.capture(observed)
                assert QRDisplayScreen(qr_encoder=observed).display() is None
                assert buttons.captured and not any(frame)
                sample('repeat-export-'+str(cycle+1))
        assert not Path(Settings.SETTINGS_FILENAME).exists()
        print(json.dumps(dict(passed=True,checks=checks,memorySnapshots=memory,productionDependencyPolicy=restore_policy is not None,repeatedExports=5 if memory else 0,physicalDisplay=hardware is not None,physicalButtons=False,pixelsDecodedByNativeZXing=True,opticalQualified=False,persistentSettingsWritten=False)))
    finally:
        restore();runtime.close();reader.close()
        if hardware is not None:hardware.close()
        if restore_policy is not None:restore_policy()
