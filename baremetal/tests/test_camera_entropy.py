# SPDX-License-Identifier: MIT
"""Public camera fixtures: owned inputs, source chaining/quality, capture lifecycle."""
import ast,collections,hashlib,json,math,sys,types,unittest
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.append(str(root/'app'))
from seedsigner_port.camera_entropy import CameraFrame,CameraSample,CameraPool,FRAME_BYTES,WIDTH,HEIGHT,SAMPLE_SIDE,SAMPLE_BYTES,derive_camera_entropy_bytes,clear_images
from seedsigner_port.camera_entropy_screens import ToolsImageEntropyLivePreviewScreen,ToolsImageEntropyFinalImageScreen
from seedsigner_port.camera_entropy_mnemonic import _shannon_entropy,byte_entropy_is_sufficient

def public_frame(phase=0):
    y=bytes((i+phase)%256 for i in range(256))*(WIDTH*HEIGHT//256)
    return bytearray(y+bytes([128])*(WIDTH*HEIGHT//2))

class BorrowedCamera:
    def __init__(self,error=None):self.data=public_frame();self.reads=0;self.starts=0;self.stops=0;self.active=False;self.error=error
    def start_video_stream_mode(self):self.starts+=1;self.active=True
    def read_video_stream(self):
        if self.error:raise self.error
        self.reads+=1;self.data[:]=public_frame(self.reads)
        return memoryview(self.data)
    def stop_video_stream_mode(self):
        if self.active:self.stops+=1;self.active=False
class Backend:
    def __init__(self):self.active=False;self.begins=[];self.frames=0
    def scan_begin(self,text):self.active=True;self.begins.append(text)
    def scan_frame(self,frame):assert self.active;self.frames+=1
    def scan_end(self):self.active=False
    def tick(self):pass
class CaptureButtons:
    def __init__(self,camera,cancel=False):self.camera=camera;self.cancel=cancel
    def reset_input(self):pass
    def check_for_low(self,key=None,keys=None):
        if key=='KEY_LEFT':return self.cancel
        # Capture key is held before the pool fills and then released. Only a
        # subsequent press after that release may capture the final image.
        return self.camera.reads<6 or self.camera.reads>=7

class CameraEntropyTest(unittest.TestCase):
 def test_public_core_gate_oracle_matches_exact_center_sampling(self):
    # Pillow resize floating-point tie rounding differs from our explicit integer
    # center contract. Keep the independent generated public oracle honest.
    tree=ast.parse((root/'micropython/camera_entropy_core_gate.py').read_text())
    expected=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='expected')
    pool=CameraPool()
    for phase in range(1,6):self.assertTrue(pool.add(public_frame(phase)))
    samples=pool.transfer();final=CameraFrame(public_frame(8))
    try:self.assertEqual(derive_camera_entropy_bytes(samples,final),expected)
    finally:clear_images(samples,final)
 def test_source_helper_provenance_and_functions(self):
    receipt=json.loads((root/'app/camera-entropy-provenance.json').read_text())
    for output,entry in receipt['files'].items():
        raw=(root.parent/'dist/firmware/sources/lvgl/application/src/seedsigner'/entry['source']).read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),entry['sourceSha256'])
        self.assertEqual(hashlib.sha256((root/'app/seedsigner_port'/output).read_bytes()).hexdigest(),entry['outputSha256'])
 def test_quality_check_matches_original_counter_shannon(self):
    for data in (b'',bytes(1000),bytes(range(256)),bytes(range(16))*50,b'public camera bytes'*90,'public unicode café'):
        raw=data.encode() if isinstance(data,str) else data
        n=len(raw);expected=-sum((count/n)*math.log2(count/n) for count in collections.Counter(raw).values())
        self.assertAlmostEqual(_shannon_entropy(data),expected)
        self.assertEqual(byte_entropy_is_sufficient(data),expected>=3.5)
 def test_pool_rejects_flat_and_repeated_borrowed_frames(self):
    pool=CameraPool();flat=bytearray(bytes([16])*(WIDTH*HEIGHT)+bytes([128])*(WIDTH*HEIGHT//2))
    self.assertFalse(pool.add(flat));frame=public_frame(1)
    self.assertTrue(pool.add(frame));before=bytes(pool.samples[0].data)
    self.assertFalse(pool.add(frame));frame[:]=public_frame(2)
    self.assertEqual(pool.samples[0].data,before)
    for phase in range(2,7):self.assertTrue(pool.add(public_frame(phase)))
    self.assertTrue(pool.ready);self.assertEqual(len(pool.samples),5)
    self.assertFalse(pool.add(public_frame(1))) # previously counted, outside window
    refs=list(pool.samples);pool.clear()
    self.assertTrue(all(not any(s.data) and s.closed for s in refs))
 def test_camera_only_chain_preserves_ordered_source_hash_tail(self):
    pool=CameraPool()
    for phase in range(1,6):pool.add(public_frame(phase))
    samples=pool.transfer();final=CameraFrame(public_frame(8));expected=b''
    for sample in samples:expected=hashlib.sha256(expected+sample.data).digest()
    expected=hashlib.sha256(expected+final.data).digest()
    self.assertEqual(derive_camera_entropy_bytes(samples,final),expected)
    self.assertNotEqual(derive_camera_entropy_bytes(list(reversed(samples)),final),expected)
    self.assertIsNone(derive_camera_entropy_bytes(samples[:-1],final))
    self.assertIsNone(derive_camera_entropy_bytes([samples[0]]*5,final))
    self.assertIsNone(derive_camera_entropy_bytes(samples,CameraFrame(bytes(FRAME_BYTES))))
    clear_images(samples,final);self.assertFalse(any(final.data))
 def test_capture_owns_pool_and_final_with_source_release_gate(self):
    camera=BorrowedCamera();backend=Backend();buttons=CaptureButtons(camera)
    screen=ToolsImageEntropyLivePreviewScreen(camera,buttons,backend,lambda:None,lambda ms:None)
    samples,final=screen.display()
    self.assertEqual((camera.starts,camera.stops,camera.reads),(1,1,8))
    self.assertFalse(camera.active);self.assertFalse(backend.active)
    saved=bytes(final.data);camera.read_video_stream();self.assertEqual(final.data,saved)
    self.assertEqual(derive_camera_entropy_bytes(samples,final),derive_camera_entropy_bytes(samples,CameraFrame(saved)))
    clear_images(samples,final)
 def test_capture_cancel_error_and_interrupt_close_camera_and_surface(self):
    for error,cancel in ((None,True),(RuntimeError('public source error'),False),(KeyboardInterrupt(),False)):
        camera=BorrowedCamera(error);backend=Backend();buttons=CaptureButtons(camera,cancel)
        screen=ToolsImageEntropyLivePreviewScreen(camera,buttons,backend,lambda:None,lambda ms:None)
        if error:
            with self.assertRaises(type(error)):screen.display()
        else:self.assertEqual(screen.display(),1000)
        self.assertFalse(camera.active);self.assertFalse(backend.active);self.assertEqual(camera.stops,1)
 def test_review_does_not_accept_held_capture_key(self):
    class Buttons:
        checks=0
        def reset_input(self):pass
        def check_for_low(self,keys):self.checks+=1;return self.checks<3
        def poll(self,keys):
            self.assert_released=self.checks>=3
            return 'KEY_RIGHT'
    buttons=Buttons();backend=Backend();image=CameraFrame(public_frame())
    screen=ToolsImageEntropyFinalImageScreen(image,buttons,backend,lambda:None,lambda ms:None)
    self.assertIsNone(screen.display());self.assertTrue(buttons.assert_released);self.assertFalse(backend.active)
    image.clear()

 def test_source_length_back_retains_image_for_original_review_route(self):
    from seedsigner_port.settings_schema import SettingsConstants as C
    from seedsigner_port.button_options import ButtonOption
    from seedsigner_port.navigation import Destination
    tree=ast.parse((root/'app/seedsigner_port/camera_entropy_views.py').read_text())
    factory=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_make_ToolsImageEntropyMnemonicLengthView')
    run=next(n for n in factory.body[0].body if isinstance(n,ast.FunctionDef) and n.name=='run')
    class Back:pass
    def dependency(module,name):
        if name=='SettingsConstants':return C
        if name=='ButtonListScreen':return object
        if name=='gettext':return lambda value:value
        if name=='RET_CODE__BACK_BUTTON':return 1000
        if name=='Destination':return Destination
        if name=='BackStackView':return Back
        raise AssertionError('Back must not generate entropy or touch native loading')
    namespace={'_dependency':dependency};exec(compile(ast.Module(body=[run],type_ignores=[]),'<original camera length/back>','exec'),namespace)
    pool=CameraPool()
    for phase in range(1,6):pool.add(public_frame(phase))
    samples=pool.transfer();final=CameraFrame(public_frame(8))
    controller=types.SimpleNamespace(image_entropy_preview_frames=samples,image_entropy_final_image=final)
    view=types.SimpleNamespace(controller=controller,settings=types.SimpleNamespace(get_value=lambda key:[12]),run_screen=lambda *a,**kw:1000)
    for count,label in ((12,'TWELVE_WORDS'),(15,'FIFTEEN_WORDS'),(18,'EIGHTEEN_WORDS'),(21,'TWENTYONE_WORDS'),(24,'TWENTYFOUR_WORDS')):setattr(view,label,ButtonOption(str(count),return_data=count))
    result=namespace['run'](view)
    self.assertIs(result.View_cls,Back);self.assertIs(controller.image_entropy_final_image,final)
    self.assertFalse(final.closed);self.assertTrue(any(final.tobytes()))
    self.assertTrue(all(not sample.closed for sample in samples));clear_images(samples,final)

 def test_source_poor_entropy_retries_fresh_pool_and_clears_owned_aliases(self):
    from seedsigner_port.settings_schema import SettingsConstants as C
    from seedsigner_port.button_options import ButtonOption
    from seedsigner_port.navigation import Destination
    from seedsigner_port.camera_entropy import clear_controller_images
    tree=ast.parse((root/'app/seedsigner_port/camera_entropy_views.py').read_text())
    factory=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_make_ToolsImageEntropyMnemonicLengthView')
    run=next(n for n in factory.body[0].body if isinstance(n,ast.FunctionDef) and n.name=='run')
    class Live:pass
    class Loader:
        def __init__(self,**kw):pass
        def start(self):pass
        def stop(self):pass
    def dependency(module,name):
        if name=='SettingsConstants':return C
        if name=='gettext':return lambda value:value
        if name in ('ButtonListScreen','ErrorScreen'):return type(name,(),{})
        if name=='RET_CODE__BACK_BUTTON':return 1000
        if name=='Destination':return Destination
        if name=='LoadingScreenThread':return Loader
        if name=='derive_camera_entropy_bytes':return derive_camera_entropy_bytes
        if name=='clear_images':return clear_images
        if name=='clear_controller_images':return clear_controller_images
        raise AssertionError('Poor camera input must not produce a seed')
    namespace={'_dependency':dependency,'_resolve':lambda name:Live};exec(compile(ast.Module(body=[run],type_ignores=[]),'<original camera poor-entropy retry>','exec'),namespace)
    pool=CameraPool()
    for phase in range(1,6):pool.add(public_frame(phase))
    samples=pool.transfer();final=CameraFrame(bytes(FRAME_BYTES));screens=[]
    controller=types.SimpleNamespace(image_entropy_preview_frames=samples,image_entropy_final_image=final)
    view=types.SimpleNamespace(controller=controller,settings=types.SimpleNamespace(get_value=lambda key:[12]),run_screen=lambda screen,**kw:screens.append(screen.__name__) or 0)
    for count,label in ((12,'TWELVE_WORDS'),(15,'FIFTEEN_WORDS'),(18,'EIGHTEEN_WORDS'),(21,'TWENTYONE_WORDS'),(24,'TWENTYFOUR_WORDS')):setattr(view,label,ButtonOption(str(count),return_data=count))
    result=namespace['run'](view)
    self.assertIs(result.View_cls,Live);self.assertTrue(result.skip_current_view)
    self.assertEqual(screens,['ButtonListScreen','ErrorScreen'])
    self.assertIsNone(controller.image_entropy_preview_frames);self.assertIsNone(controller.image_entropy_final_image)
    self.assertTrue(final.closed);self.assertTrue(all(sample.closed and not any(sample.data) for sample in samples))
