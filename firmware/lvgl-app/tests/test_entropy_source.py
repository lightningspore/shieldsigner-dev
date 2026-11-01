import ast,hashlib,sys,time,unittest
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from entropy_source import acquisition_loop,acquisition_method
SOURCE=Path(__file__).resolve().parents[3]/'dist/firmware/sources/lvgl/application/src/seedsigner/gui/screens/tools_screens.py'
class Sample:
    def __init__(self,index,flat=False):self.index=index;self.flat=flat
    def getextrema(self):return ((0,0),)*3 if self.flat else ((0,255),)*3
    def convert(self,mode):assert mode=='L';return self
    def resize(self,size,resampling):assert size==(96,96);return self
    def tobytes(self):return bytes([self.index])*96*96
class Camera:
    def __init__(self,repeat=False,flat=False):self.n=0;self.repeat=repeat;self.flat=flat;self.stopped=False
    def read_video_stream(self,as_image,preview=False):
        if preview:self.n+=1
        return Sample(1 if self.repeat else self.n,self.flat)
    def stop_video_stream_mode(self):self.stopped=True
class EntropySourceTests(unittest.TestCase):
    def run_loop(self,repeat=False,flat=False,held=False,original=False,method_only=False):
        if not SOURCE.exists():self.skipTest('Pinned checkout not materialized; run inventory/build first')
        source=SOURCE.read_text();camera=Camera(repeat,flat);paint=[]
        def low(keys):
            if keys==20:return camera.n>=10
            return camera.n>=7 or (held and camera.n<6)
        screen=SimpleNamespace(camera=camera,PREVIEW_POOL_SIZE=5,hw_inputs=SimpleNamespace(check_for_low=low,update_last_input_time=lambda:None),_lvgl_preview=lambda frame,entropy,count:paint.append((camera.n,count)))
        namespace=dict(hashlib=hashlib,time=time,Image=SimpleNamespace(Resampling=SimpleNamespace(BILINEAR=1,NEAREST=0)),HardwareButtonsConstants=SimpleNamespace(KEY_LEFT=20,KEYS__ANYCLICK=[10,49,50,51]),RET_CODE__BACK_BUTTON=1000)
        if original:
            screen.canvas_width=screen.canvas_height=240
            noop=lambda *args,**kwargs:None
            screen.renderer=SimpleNamespace(lock=nullcontext(),canvas=SimpleNamespace(paste=noop),draw=SimpleNamespace(text=noop,ellipse=noop),show_image=noop,canvas_width=240,canvas_height=240)
            namespace.update(Fonts=SimpleNamespace(get_font=lambda *args:SimpleNamespace(getlength=lambda value:0)),GUIConstants=SimpleNamespace(get_body_font_name=lambda:None,get_button_font_size=lambda:None,EDGE_PADDING=8,COMPONENT_PADDING=8,ERROR_COLOR=0,WARNING_COLOR=0,GREEN_INDICATOR_COLOR=0,BODY_FONT_COLOR=0,BACKGROUND_COLOR=0,ACCENT_COLOR=0),mnemonic_generation=SimpleNamespace(_shannon_entropy=lambda value:0),resize_image_to_fit=lambda image,*args,**kwargs:image,_=lambda value:value)
            cls=next(node for node in ast.parse(source).body if isinstance(node,ast.ClassDef) and node.name=='ToolsImageEntropyLivePreviewScreen')
            method=next(node for node in cls.body if isinstance(node,ast.FunctionDef) and node.name=='_run')
            local={};exec(compile(ast.fix_missing_locations(ast.Module(body=[method],type_ignores=[])),'<original loop>','exec'),namespace,local)
            loop=local['_run']
        elif method_only:
            cls=next(node for node in ast.parse(source).body if isinstance(node,ast.ClassDef) and node.name=='ToolsImageEntropyLivePreviewScreen')
            method=next(node for node in cls.body if isinstance(node,ast.FunctionDef) and node.name=='_run')
            import textwrap
            loop=acquisition_method(textwrap.dedent(ast.get_source_segment(source,method)),namespace)
        else:loop=acquisition_loop(source,namespace)
        result=loop(screen)
        return result,camera,paint
    def test_distinct_full_pool_release_gate_and_exact_capture(self):
        for held in (False,True):
            (pool,final),camera,paint=self.run_loop(held=held)
            self.assertEqual([sample.index for sample in pool],[2,3,4,5,6])
            self.assertEqual(final.index,7);self.assertTrue(camera.stopped)
            self.assertEqual(len(pool),5);self.assertEqual(paint[-1],(7,5))
    def test_flat_and_frozen_sources_never_capture(self):
        for options in (dict(repeat=True),dict(flat=True)):
            result,camera,paint=self.run_loop(**options)
            self.assertEqual(result,1000);self.assertTrue(camera.stopped)
            self.assertTrue(all(count<5 for _,count in paint))
    def test_unexpected_presentation_boundaries_rejected(self):
        if not SOURCE.exists():self.skipTest('Pinned checkout not materialized')
        source=SOURCE.read_text();prefix,body=source.split('class ToolsImageEntropyLivePreviewScreen',1)
        source=prefix+'class ToolsImageEntropyLivePreviewScreen'+body.replace('with self.renderer.lock:','with self.other.lock:',1)
        with self.assertRaises(ValueError):acquisition_loop(source,{})

    def test_matches_unmodified_original_acquisition_results(self):
        for options in ({},{'held':True},{'repeat':True},{'flat':True}):
            adapted,adapted_camera,_=self.run_loop(**options)
            original,original_camera,_=self.run_loop(original=True,**options)
            def signature(result):
                if isinstance(result,int):return result
                pool,final=result
                return [sample.tobytes() for sample in pool],final.tobytes()
            self.assertEqual(signature(adapted),signature(original))
            self.assertEqual(adapted_camera.n,original_camera.n)
            self.assertEqual(adapted_camera.stopped,original_camera.stopped)

    def test_method_only_matches_whole_module_adapter(self):
        for options in ({},{'held':True},{'repeat':True},{'flat':True}):
            first,camera,_=self.run_loop(**options)
            second,other,_=self.run_loop(method_only=True,**options)
            def signature(result):
                if isinstance(result,int):return result
                pool,final=result
                return [sample.tobytes() for sample in pool],final.tobytes()
            self.assertEqual(signature(first),signature(second));self.assertEqual(camera.n,other.n)
        with self.assertRaises(ValueError):acquisition_method('def other(self): pass',{})

