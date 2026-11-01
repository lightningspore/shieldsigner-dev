import ast,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from calibration import compile_loop,configure
class CalibrationTests(unittest.TestCase):
    def test_only_drawing_block_changes(self):
        source='def _run(self):\n self.events.append("log")\n with self.renderer.lock:\n  self.renderer.show_image()\n self.events.append("stop")\n'
        fn=compile_loop(source,{})
        from types import SimpleNamespace
        events=[];screen=SimpleNamespace(events=events,_lvgl_status=lambda *args:events.append(args))
        fn.__globals__.update(elapsed_text='01',voltage_text='3.7',current_text='-250',status_text='Discharging')
        fn(screen);self.assertEqual(events,['log',('01','3.7','-250','Discharging'),'stop'])
        with self.assertRaises(ValueError):compile_loop(source.replace('self.renderer.lock','self.other.lock'),{})
    def test_intro_start_preserve_actions_and_messages(self):
        for name,label in [('ToolsBatteryCalibrationIntroScreen','Next'),('ToolsBatteryCalibrationStartScreen','Start')]:
            builder,cfg=configure(name,{'top_nav':{}})
            self.assertEqual(builder,'button_list_screen');self.assertEqual(cfg['button_list'],[label]);self.assertEqual(cfg['top_nav']['title'],'Battery Calibration');self.assertTrue(cfg['is_button_text_centered'])
    def test_original_control_logging_and_camera_cleanup_are_unchanged(self):
        import io
        from contextlib import nullcontext
        from types import SimpleNamespace
        source=(Path(__file__).resolve().parents[3]/'dist/firmware/sources/lvgl/application/src/seedsigner/gui/screens/tools_screens.py').read_text()
        cls=next(node for node in ast.parse(source).body if isinstance(node,ast.ClassDef) and node.name=='ToolsBatteryCalibrationRunningScreen')
        methods={node.name:node for node in cls.body if isinstance(node,ast.FunctionDef)}
        def execute(adapted,charging,start_failed,cancel_after=3):
            class Clock:
                now=0
                def monotonic(self):return self.now
                def time(self):return 1700000000+self.now
                def sleep(self,duration):self.now+=1
            class Handle(io.StringIO):
                def __exit__(self,*args):return False
            handle=Handle();clock=Clock();events=[];drawn=[]
            class Log:
                parent=SimpleNamespace(mkdir=lambda **kwargs:None)
                deleted=False
                def open(self,*args,**kwargs):return handle
                def exists(self):return not self.deleted
                def unlink(self):self.deleted=True
            log=Log()
            def start(**kwargs):
                events.append(('start',kwargs))
                if start_failed:raise RuntimeError('public startup failure')
            def input_active():
                if clock.now>100:raise AssertionError('Loop failed to exit')
                return not charging and clock.now>=cancel_after
            screen=SimpleNamespace(log_path=log,camera=SimpleNamespace(start_video_stream_mode=start,stop_video_stream_mode=lambda:events.append('stop')),battery_hat=SimpleNamespace(get_voltage=lambda:3.7,get_current=lambda:100 if charging else -100),hw_inputs=SimpleNamespace(has_any_input=input_active,override_ind=False),status_font=SimpleNamespace(size=16))
            namespace=dict(time=clock,RET_CODE__BACK_BUTTON=1000,_=lambda value:value,GUIConstants=SimpleNamespace(BACKGROUND_COLOR=0,EDGE_PADDING=8,COMPONENT_PADDING=4,BODY_FONT_COLOR=1))
            for name in ('_format_elapsed','_write_log_line'):
                local={};exec(compile(ast.Module(body=[methods[name]],type_ignores=[]),'<original helper>','exec'),namespace,local);setattr(screen,name,local[name].__get__(screen))
            screen._lvgl_status=lambda elapsed,voltage,current,status:drawn.extend(['Elapsed: '+elapsed,'Voltage: '+voltage,'Current: '+current,'Status: '+status])
            screen.renderer=SimpleNamespace(lock=nullcontext(),canvas_width=240,canvas_height=240,draw=SimpleNamespace(rectangle=lambda *args,**kwargs:None,text=lambda xy,text,**kwargs:drawn.append(text)),show_image=lambda:None)
            if adapted:run=compile_loop(ast.get_source_segment(source,methods['_run']),namespace)
            else:
                local={};exec(compile(ast.Module(body=[methods['_run']],type_ignores=[]),'<original loop>','exec'),namespace,local);run=local['_run']
            result=run(screen)
            return result,events,drawn,handle.getvalue(),log.deleted,clock.now
        for charging,start_failed,cancel_after in ((False,False,3),(True,False,3),(False,True,3),(False,False,63)):
            original=execute(False,charging,start_failed,cancel_after);adapted=execute(True,charging,start_failed,cancel_after)
            self.assertEqual(adapted,original)
            self.assertTrue(adapted[4]);self.assertEqual(adapted[0],1000)
            if cancel_after==63:self.assertEqual(adapted[3].splitlines(),['1700000000,3.7000','1700000060,3.7000'])
