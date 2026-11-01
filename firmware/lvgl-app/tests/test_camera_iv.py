import ast,hashlib,sys,unittest
from pathlib import Path
from types import ModuleType,SimpleNamespace
from unittest.mock import patch
from PIL import Image
from PIL.ImageOps import autocontrast
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from entropy_fallback import compile_run
BASE=Path(__file__).resolve().parents[3]/'dist/firmware/sources/lvgl/application/src/seedsigner'

class CameraIVTests(unittest.TestCase):
    def execute(self,adapted,mode,action):
        source=(BASE/'views/seed_views.py').read_text()
        cls=next(n for n in ast.parse(source).body if isinstance(n,ast.ClassDef) and n.name=='SeedEncryptedQRnonECBModeView')
        method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='run')
        table=dict(MODE_ECB='ecb',MODE_CBC='cbc',MODE_CTR='ctr',MODE_GCM='gcm')
        statements=[n for n in ast.parse((BASE/'helpers/kef.py').read_text()).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ('MODE_NUMBERS','MODE_IVS') for t in n.targets)]
        exec(compile(ast.Module(body=statements,type_ignores=[]),'<pinned IV tables>','exec'),table)
        events=[];controller=SimpleNamespace(image_entropy_preview_frames=['old']);image=Image.new('RGB',(640,480),(31,52,89))
        def preview():events.append('preview');return 1000 if action=='preview-back' else 0
        def review(**kwargs):
            self.assertEqual(kwargs['final_image'].size,(240,240));kwargs['final_image'].close()
            return SimpleNamespace(display=lambda:(events.append('review') or (1000 if action=='review-back' else 0)))
        screens=ModuleType('seedsigner.gui.screens.tools_screens')
        screens.ToolsImageEntropyLivePreviewScreen=lambda:SimpleNamespace(display=preview)
        screens.ToolsImageEntropyFinalImageScreen=review
        def start():
            events.append('start')
            if action=='start-error':raise RuntimeError('fixture start')
        def read(**kwargs):
            self.assertEqual(kwargs,{'as_image':True});events.append('read')
            if action=='read-error':raise RuntimeError('fixture read')
            return None if action=='empty' or events.count('read')<3 else image
        camera=SimpleNamespace(start_video_stream_mode=start,read_video_stream=read,stop_video_stream_mode=lambda:events.append('stop'))
        camera_module=ModuleType('seedsigner.hardware.camera');camera_module.Camera=SimpleNamespace(get_instance=lambda:camera)
        helpers=ModuleType('seedsigner.helpers');helpers.kef=SimpleNamespace(**{k:table[k] for k in ('MODE_NUMBERS','MODE_IVS')})
        class ButtonOption:
            def __init__(self,label):self.button_label=label
        namespace=dict(ButtonOption=ButtonOption,RET_CODE__BACK_BUTTON=1000,BackStackView='Back',SeedEncryptedQRMnemonicIDPromptView='MnemonicID',Destination=lambda target,view_args=None:SimpleNamespace(target=target,args=view_args),time=SimpleNamespace(sleep=lambda seconds:events.append(('sleep',seconds))),Image=Image,autocontrast=autocontrast,hashlib=hashlib)
        namespace['ButtonListScreen']=object()
        if adapted:run=compile_run(ast.get_source_segment(source,method),namespace,'<adapted camera IV>')
        else:
            local={};exec(compile(ast.Module(body=[method],type_ignores=[]),'<original camera IV>','exec'),namespace,local);run=local['run']
        view=SimpleNamespace(controller=controller,seed='public fixture seed',encryption_key='public fixture key',mode_name=mode,canvas_width=240,canvas_height=240,run_screen=lambda *a,**k:1 if action=='cancel' else 1000 if action=='menu-back' else 0)
        try:
            with patch.dict(sys.modules,{screens.__name__:screens,camera_module.__name__:camera_module,helpers.__name__:helpers}),patch('entropy_camera.FallbackCamera.get_instance',return_value=camera):
                try:
                    result=run(view);outcome=(result.target,result.args)
                except Exception as error:outcome=(type(error).__name__,str(error))
            if action=='accept':
                expected=hashlib.sha256(image.tobytes()).digest()[:table['MODE_IVS'][table['MODE_NUMBERS'][mode]]]
                self.assertEqual(outcome,('MnemonicID',dict(encryption_key='public fixture key',i_vector=expected,seed='public fixture seed')))
            elif action in ('cancel','menu-back','preview-back','review-back'):self.assertEqual(outcome,('Back',None))
            elif action=='empty':
                self.assertEqual(outcome,('Exception','Failed to capture additional entropy image'))
                self.assertEqual(events.count('read'),10)
            else:self.assertEqual(outcome,('RuntimeError','fixture '+('start' if action=='start-error' else 'read')))
            if 'start' in events:self.assertEqual(events.count('stop'),1)
            return outcome,events,controller.image_entropy_preview_frames
        finally:image.close()

    def test_original_camera_iv_sampling_hash_selection_and_cleanup_preserved(self):
        for mode in ('AES-CBC','AES-CTR','AES-GCM','AES-CBC v1'):
            for action in ('accept','cancel','menu-back','preview-back','review-back','empty','start-error','read-error'):
                with self.subTest(mode=mode,action=action):
                    self.assertEqual(self.execute(False,mode,action),self.execute(True,mode,action))
