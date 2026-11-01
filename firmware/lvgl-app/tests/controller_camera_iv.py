"""Original Controller camera-IV capture/review with physical camera and LCD.

Public test seed/key only; no image, IV bytes or key material is printed/saved.
Stop at the original mnemonic-ID prompt after checking its incoming IV, or at
Home after cancellation. Hash observation adds overhead; not a memory benchmark.
"""
import argparse,hashlib,json,sys,tempfile,time,threading
from contextlib import ExitStack
from pathlib import Path
sys.path[:0]=['/opt/src','/usr/lib/shieldsigner-camera/python']
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('binary');parser.add_argument('--mode',default='AES-CBC',choices=['AES-CBC','AES-CBC v1','AES-ECB','AES-ECB v1','AES-CTR','AES-GCM'])
parser.add_argument('--cancel',choices=['preview','review'])
parser.add_argument('--roundtrip',action='store_true')
args=parser.parse_args()
is_ecb=args.mode.startswith('AES-ECB')
if is_ecb and (args.cancel or not args.roundtrip):parser.error('ECB fixture requires --roundtrip without camera cancellation')
from dependency_policy import install as dependencies
from diagnostic_scope import attribute
from app import stop_workers
guards=Path(__file__).parent/'source-guards.json'
with tempfile.TemporaryDirectory(prefix='lvgl-camera-iv-') as temporary,ExitStack() as scope:
    scope.callback(dependencies('/opt/src',guards))
    from startup_policy import install as startup
    startup('/opt/src','/usr/lib/shieldsigner-camera/python')
    from seedsigner.models.settings import Settings
    from seedsigner.models.settings_definition import SettingsConstants as C
    Settings.SETTINGS_FILENAME=str(Path(temporary)/'settings.json');settings=Settings.get_instance()
    settings.set_value(C.SETTING__PERSISTENT_SETTINGS,C.OPTION__DISABLED,save=False)
    settings.set_value(C.SETTING__WIPE_TIMER,C.WIPE_TIMER__DISABLED,save=False)
    settings.set_value(C.SETTING__ENCRYPTION_MODE,args.mode,save=False)
    from luckfox import LuckfoxHardware
    from runtime import Runtime,install_view_dispatch
    from renderer_bridge import install as renderer
    from seedsigner.gui.renderer import Renderer
    hardware=LuckfoxHardware();scope.callback(hardware.close)
    state=dict(screen=None,since=0,ready=None,keys=[],qr=None,lastDecode=0,exportIsText=False);seen=[];streams=[];expected=[];verified=[];decryption_test=[False]
    frame=bytearray(240*240*2);frame_lock=threading.Lock();export_expected=[None]
    from shieldsigner_lcd import QrWorker
    reader=QrWorker('/usr/lib/shieldsigner-camera/shieldsigner-qr-reader',5);scope.callback(reader.close)
    def pixels(area,data):
        if args.roundtrip:
            x1,y1,x2,y2=area;stride=(x2-x1+1)*2
            with frame_lock:
                for row,y in enumerate(range(y1,y2+1)):frame[(y*240+x1)*2:(y*240+x2+1)*2]=data[row*stride:(row+1)*stride]
        hardware.pixels(area,data)
    def buttons():
        name=state['screen'];elapsed=time.monotonic()-state['since']
        if elapsed>35:raise TimeoutError('Camera IV diagnostic stalled')
        if name=='ToolsImageEntropyLivePreviewScreen':
            stats=getattr(runtime,'entropy_stats',{})
            if args.cancel=='preview':return {'KEY_LEFT'} if stats.get('previewFrames',0)>=3 else set()
            if stats.get('poolFrames')==5:
                if state['ready'] is None:state['ready']=stats['previewFrames']
                if stats['previewFrames']>state['ready']:return {'KEY_PRESS'}
            return set()
        if elapsed<.5:return set()
        if name=='QRDisplayScreen':
            if state['qr'] is not None:return {'KEY_PRESS'}
            if elapsed>1 and time.monotonic()-state['lastDecode']>.2:
                state['lastDecode']=time.monotonic()
                with frame_lock:luma=bytes(frame[0::2])
                payload=reader.decode_luma(luma,240,240)
                if payload is not None:
                    assert payload==export_expected[0];state['qr']=payload
            return set()
        offset=elapsed-.5;index=int(offset/.35)
        return {state['keys'][index]} if index<len(state['keys']) and offset%.35<.22 else set()
    runtime=Runtime(args.binary,pixels,buttons,hardware.buttons.update_last_input_time);scope.callback(runtime.close)
    scope.callback(install_view_dispatch(runtime,'/opt/src',guards));scope.callback(renderer(runtime,hardware,Renderer))
    from seedsigner.hardware.microsd import MicroSD
    from microsd_lifecycle import install as microsd
    scope.callback(microsd(MicroSD,'/opt/src',guards))
    import entropy_camera
    original_start=entropy_camera.start;original_read=entropy_camera._FallbackInstance.read_video_stream
    def start(camera,**kwargs):
        result=original_start(camera,**kwargs);streams.append(camera._video_stream);return result
    def read(camera,**kwargs):
        image=original_read(camera,**kwargs)
        if image is not None:expected.append(hashlib.sha256(image.tobytes()).digest())
        return image
    scope.enter_context(attribute(entropy_camera,'start',start));scope.enter_context(attribute(entropy_camera._FallbackInstance,'read_video_stream',read))
    from seedsigner.controller import Controller,StopFlowBasedTest,FlowBasedTestException
    from seedsigner.views.view import View,Destination
    from seedsigner.views.seed_views import SeedEncryptedQRnonECBModeView,SeedEncryptedQRMnemonicIDPromptView
    from seedsigner.models.seed import Seed
    from seedsigner.helpers import kef
    controller=Controller.get_instance();controller.boot_failover_cleared=True
    scope.callback(stop_workers,controller)
    original_initialize=View._initialize;original_screen=View.run_screen;original_run=runtime.run
    def screen_run(cls,kwargs):
        name=cls.__name__;seen.append(name);state.update(screen=name,since=time.monotonic(),ready=None)
        state['keys']=['KEY_LEFT' if name=='ToolsImageEntropyFinalImageScreen' and args.cancel=='review' else 'KEY_PRESS']
        if name=='SeedEncryptedQRReviewMnemonicIDScreen':state['keys']=['KEY_DOWN']*12+['KEY_UP','KEY_PRESS']
        if name=='SeedEncryptedQRTranscribeModePromptScreen' or decryption_test[0]:state['keys']=['KEY_DOWN']*12+['KEY_PRESS']
        if name=='SeedOptionsScreen' and args.roundtrip:
            assert state['qr'] is not None;raise StopFlowBasedTest()
        if name=='QRDisplayScreen':
            payload=kwargs['qr_encoder'].data;state['exportIsText']=isinstance(payload,str);export_expected[0]=payload.encode() if isinstance(payload,str) else payload
        if name=='MainMenuScreen':
            assert args.cancel;raise StopFlowBasedTest()
        allowed=('ButtonListScreen','ToolsImageEntropyLivePreviewScreen','ToolsImageEntropyFinalImageScreen','SeedEncryptedQRReviewMnemonicIDScreen','SeedEncryptedQRTranscribeModePromptScreen','QRDisplayScreen')
        if name not in allowed and not (decryption_test[0] and name=='WarningScreen'):
            raise FlowBasedTestException('Unexpected camera IV screen '+name)
        return original_run(cls,kwargs)
    def screen(view,cls,**kwargs):
        if isinstance(view,SeedEncryptedQRMnemonicIDPromptView):
            if is_ecb:
                assert view.i_vector is None;verified.append(0)
            else:
                assert not args.cancel and expected
                length=kef.MODE_IVS[kef.MODE_NUMBERS[args.mode]]
                assert view.i_vector==expected[-1][:length]
                verified.append(length)
            if not args.roundtrip:raise StopFlowBasedTest()
        return original_screen(view,cls,**kwargs)
    scope.enter_context(attribute(runtime,'run',screen_run))
    scope.enter_context(attribute(View,'run_screen',screen))
    if args.mode.endswith(' v1'):
        from embit import bip39
        seed=Seed(bip39.mnemonic_from_bytes(bytes(range(16))).split())
    else:seed=Seed(['abandon']*11+['about'])
    exported_version=None
    destination=Destination(SeedEncryptedQRMnemonicIDPromptView,view_args=dict(seed=seed,encryption_key='public diagnostic key',i_vector=None)) if is_ecb else Destination(SeedEncryptedQRnonECBModeView,view_args=dict(seed=seed,encryption_key='public diagnostic key',mode_name=args.mode))
    controller.start(initial_destination=destination,skip_startup_interstitials=True)
    assert View._initialize is original_initialize
    assert bool(verified)==(not args.cancel)
    if args.roundtrip:
        assert state['qr'] is not None and not any(frame)
        raw=state['qr']
        if state['exportIsText']:
            from seedsigner.helpers.base43 import base43_decode
            raw=base43_decode(raw.decode('ascii'))
        exported_version=kef.unwrap(raw)[1]
        assert kef.VERSIONS[exported_version]['mode']==kef.MODE_NUMBERS[args.mode]
        if args.mode.endswith(' v1'):assert exported_version==({'AES-CBC v1':1,'AES-ECB v1':0}[args.mode])

        from seedsigner.views.scan_views import ScanDecryptEncryptedQRView
        from seedsigner.views.seed_views import SeedFinalizeView
        from seedsigner.views.view import BackStackView
        decryption_test[0]=True
        destination=ScanDecryptEncryptedQRView(encryption_key='wrong public key',encrypted_data=state['qr']).run()
        assert destination.View_cls is BackStackView and controller.storage.get_pending_seed() is None
        controller.storage2.clear_encryptedqr()
        destination=ScanDecryptEncryptedQRView(encryption_key='public diagnostic key',encrypted_data=state['qr']).run()
        assert destination.View_cls is SeedFinalizeView
        pending=controller.storage.get_pending_seed();assert pending.mnemonic_list==seed.mnemonic_list
        controller.storage.clear_pending_seed();controller.storage2.clear_encryptedqr()
        assert not any(name==prefix or name.startswith(prefix+'.') for name in sys.modules for prefix in ('pyzbar','cv2','numpy','qrcode.image.styledpil'))
    assert all(stream.is_stopped and stream.owner_exit_code==0 for stream in streams)
    assert len(streams)==(0 if is_ecb else 1 if args.cancel=='preview' else 2)
    assert Path('/sys/kernel/debug/dma_buf/bufinfo').read_text().splitlines()[-1]=='Total 0 objects, 0 bytes'
    assert not Path(Settings.SETTINGS_FILENAME).exists()
    print(json.dumps(dict(passed=True,mode=args.mode,exportedKefVersion=exported_version,cancelStage=args.cancel,originalController=True,originalViewInitialization=True,ivMatchesOriginalFullImageHash=bool(verified) and not is_ecb,ivLengths=verified,screenSequence=seen,streamsStopped=len(streams),physicalCamera=not is_ecb,physicalDisplay=True,physicalButtons=False,hashObservationOverheadIncluded=not is_ecb,imagesOrIVBytesSaved=False,completeEncryptionRoundTrip=args.roundtrip,pixelsDecodedByNativeZXing=args.roundtrip,wrongKeyRejected=args.roundtrip,originalMnemonicRecovered=args.roundtrip)),flush=True)
