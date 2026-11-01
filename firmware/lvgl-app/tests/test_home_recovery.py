import sys,unittest
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from home_recovery import monitor

class HomeRecoveryTests(unittest.TestCase):
    def test_original_callback_identity_input_and_return(self):
        calls=[];renderer=object()
        class Home:
            def __init__(self):raise AssertionError('PIL constructor invoked')
            def _run_callback(self):
                calls.append((self.hw_inputs.cur_input,self.renderer,self._hold_key,self._hold_start_ms))
                self._hold_key='tracked'
                return 1002
        runtime=SimpleNamespace(current=17,host=SimpleNamespace(screensaver_active=False))
        poll=monitor(runtime,Home,{'KEY_UP':17},renderer)
        self.assertEqual(poll(),1002)
        self.assertEqual(calls[-1],('KEY_UP',renderer,None,None))
        runtime.host.screensaver_active=True
        poll()
        self.assertEqual(calls[-1],(None,renderer,'tracked',None))
        runtime.host.screensaver_active=False;runtime.current=None
        poll();self.assertIsNone(calls[-1][0])

    def test_render_only_fixture_does_not_initialize_hardware(self):
        self.assertIsNone(monitor(None,None,None,None)())

    def test_pinned_callback_five_second_switch_release_and_same_config(self):
        import ast,types
        from unittest.mock import patch
        source=(Path(__file__).resolve().parents[3]/'dist/firmware/sources/lvgl/application/src/seedsigner/gui/screens/screen.py').read_text()
        cls=next(n for n in ast.parse(source).body if isinstance(n,ast.ClassDef) and n.name=='MainMenuScreen')
        callback=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='_run_callback')
        constants=SimpleNamespace(DISPLAY_CONFIGURATION__ST7789__240x240='square',DISPLAY_CONFIGURATION__ST7789__320x240='wide',DISPLAY_CONFIGURATION__ST7735__128x128='small',SETTING__DISPLAY_CONFIGURATION='display')
        clock=[0];writes=[];active=['square'];initialized=[]
        settings=SimpleNamespace(get_value=lambda key:active[0],set_value=lambda key,value:(active.__setitem__(0,value),writes.append(value)))
        module=types.ModuleType('seedsigner.models.settings');module.Settings=SimpleNamespace(get_instance=lambda:settings)
        class Home: _DIRECTION_TO_DISPLAY=None;VERY_LONG_PRESS_MS=5000
        ns=dict(MainMenuScreen=Home,HardwareButtonsConstants=SimpleNamespace(KEY_UP='KEY_UP',KEY_RIGHT='KEY_RIGHT',KEY_DOWN='KEY_DOWN'),SettingsConstants=constants,time=SimpleNamespace(time=lambda:clock[0]),logger=SimpleNamespace(info=lambda *a:None),RET_CODE__DISPLAY_TOGGLE=1002)
        exec(compile(ast.Module(body=[callback],type_ignores=[]),'<pinned Home callback>','exec'),ns)
        Home._run_callback=ns['_run_callback']
        runtime=SimpleNamespace(current=19,host=SimpleNamespace(screensaver_active=False))
        poll=monitor(runtime,Home,{'KEY_UP':17,'KEY_RIGHT':19,'KEY_DOWN':18},SimpleNamespace(initialize_display=lambda:initialized.append(active[0])))
        with patch.dict(sys.modules,{'seedsigner.models.settings':module}):
            self.assertIsNone(poll());clock[0]=4.999;self.assertIsNone(poll())
            clock[0]=5;self.assertEqual(poll(),1002)
            clock[0]=10;self.assertIsNone(poll());self.assertEqual(writes,['wide'])
            runtime.current=18;clock[0]=11;poll()
            runtime.current=None;clock[0]=15;poll()
            runtime.current=18;clock[0]=16;poll()
            clock[0]=20.999;self.assertIsNone(poll())
            clock[0]=21;self.assertEqual(poll(),1002)
            runtime.current=17;clock[0]=22;poll()
            runtime.host.screensaver_active=True;clock[0]=27;self.assertIsNone(poll())
            runtime.host.screensaver_active=False;clock[0]=28;poll()
            clock[0]=33;self.assertEqual(poll(),1002)
        self.assertEqual(initialized,['wide','small','square'])
