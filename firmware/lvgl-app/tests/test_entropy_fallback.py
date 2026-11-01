import ast,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from entropy_fallback import compile_run
class EntropyFallbackTests(unittest.TestCase):
    def test_only_import_dependency_changes(self):
        source='def run(self):\n from seedsigner.hardware.camera import Camera\n try:\n  value=Camera.get_instance()\n  return value\n finally:\n  self.stopped=True\n'
        fn=compile_run(source,{},'<public fixture>')
        self.assertEqual(fn.__name__,'run')
        self.assertIn('entropy_camera',fn.__code__.co_names)
        self.assertNotIn('seedsigner.hardware.camera',fn.__code__.co_names)
        with self.assertRaises(ValueError):compile_run('def run(self): return None',{},'<public>')
    def test_facade_routes_start_read_stop_without_changing_values(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        from entropy_camera import _FallbackInstance
        events=[];image=object()
        camera=SimpleNamespace(read_video_stream=lambda **kwargs:(events.append(kwargs) or image),stop_video_stream_mode=lambda:events.append('stop'))
        facade=_FallbackInstance(camera)
        with patch('entropy_camera.start',lambda value:events.append(('start',value))):facade.start_video_stream_mode()
        self.assertIs(facade.read_video_stream(as_image=True),image);facade.stop_video_stream_mode()
        self.assertEqual(events,[('start',camera),{'as_image':True},'stop'])

    def check_lazy_hook(self,module_name,class_name):
        import hashlib,importlib.util,json,tempfile
        from entropy_fallback import install
        from unittest.mock import patch
        class Base:
            def __init__(self):self.initialized=True
        original_init=Base.__init__
        name='seedsigner.views.'+module_name
        source=f'class {class_name}(Base):\n def run(self):\n  from seedsigner.hardware.camera import Camera\n  return Camera.get_instance()\n'
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);path=root/f'seedsigner/views/{module_name}.py'
            path.parent.mkdir(parents=True);path.write_text(source)
            manifest=root/'guards.json';manifest.write_text(json.dumps({f'views/{module_name}.py':hashlib.sha256(path.read_bytes()).hexdigest()}))
            spec=importlib.util.spec_from_file_location(name,path)
            module=importlib.util.module_from_spec(spec);module.Base=Base
            with patch.dict(sys.modules,{name:module}):
                spec.loader.exec_module(module);cls=getattr(module,class_name);original_run=cls.run
                restore=install(Base,root,manifest)
                try:
                    self.assertIs(cls.run,original_run) # No eager app imports/patching.
                    instance=cls();self.assertTrue(instance.initialized)
                    self.assertIsNot(cls.run,original_run)
                    replacement=cls.run;cls();self.assertIs(cls.run,replacement)
                    sentinel=object()
                    with patch('entropy_camera.FallbackCamera.get_instance',return_value=sentinel):self.assertIs(instance.run(),sentinel)
                finally:restore()
                self.assertIs(Base.__init__,original_init);self.assertIs(cls.run,original_run)
                path.write_text(source+'# unexpected edit\n')
                restore=install(Base,root,manifest)
                try:
                    with self.assertRaisesRegex(ValueError,'Unreviewed'):cls()
                    self.assertIs(cls.run,original_run)
                finally:restore()

    def test_lazy_hook_is_guarded_and_restores_original_class(self):
        self.check_lazy_hook('tools_views','ToolsImageEntropyFinalImageView')
        self.check_lazy_hook('seed_views','SeedEncryptedQRnonECBModeView')

    def test_pinned_original_retry_limit_and_failure_cleanup(self):
        from types import SimpleNamespace,ModuleType
        from unittest.mock import patch
        path=Path(__file__).resolve().parents[3]/'dist/firmware/sources/lvgl/application/src/seedsigner/views/tools_views.py'
        self.assertTrue(path.is_file(),'Fetch pinned application with mise run lvgl:app:fetch')
        source=path.read_text();tree=ast.parse(source)
        cls=next(node for node in tree.body if isinstance(node,ast.ClassDef) and node.name=='ToolsImageEntropyFinalImageView')
        method=next(node for node in cls.body if isinstance(node,ast.FunctionDef) and node.name=='run')
        screen_module=ModuleType('seedsigner.gui.screens.tools_screens');screen_module.ToolsImageEntropyFinalImageScreen=object
        pil=ModuleType('PIL');pil.Image=object
        ops=ModuleType('PIL.ImageOps');ops.autocontrast=lambda *args,**kwargs:self.fail('Image processing reached after failed capture')
        for failure in ('empty','start','read'):
            events=[]
            def start():
                events.append('start')
                if failure=='start':raise RuntimeError('fixture start failure')
            def read(**kwargs):
                self.assertEqual(kwargs,{'as_image':True});events.append('read')
                if failure=='read':raise RuntimeError('fixture read failure')
                return None
            camera=SimpleNamespace(start_video_stream_mode=start,read_video_stream=read,stop_video_stream_mode=lambda:events.append('stop'))
            namespace={'time':SimpleNamespace(sleep=lambda value:events.append(('sleep',value))),'logger':SimpleNamespace(info=lambda value:None)}
            run=compile_run(ast.get_source_segment(source,method),namespace,'<pinned original retry>')
            view=SimpleNamespace(controller=SimpleNamespace(image_entropy_final_image=None))
            with patch.dict(sys.modules,{'seedsigner.gui.screens.tools_screens':screen_module,'PIL':pil,'PIL.ImageOps':ops}),patch('entropy_camera.FallbackCamera.get_instance',return_value=camera):
                with self.assertRaisesRegex(Exception,'Failed to capture' if failure=='empty' else 'fixture'):run(view)
            self.assertEqual(events[-1],'stop');self.assertEqual(events.count('stop'),1)
            self.assertEqual(events.count('read'),10 if failure=='empty' else (1 if failure=='read' else 0))
            self.assertIsNone(view.controller.image_entropy_final_image)
