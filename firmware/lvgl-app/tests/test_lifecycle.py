import sys,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from lifecycle import install,WipeInterrupted
class LifecycleTests(unittest.TestCase):
    def test_original_wipe_then_one_interruption_and_restart(self):
        calls=[]
        class Controller:
            def handle_wipe_timeout(self):calls.append('wipe')
            def handle_exception(self,error):return ('original',error)
        original=Controller.handle_wipe_timeout
        runtime=SimpleNamespace(consume_input_override=lambda:calls.append('consume-override'),screensaver_timeout_ms=120000,configure_screensaver=lambda ms:calls.append(('timeout',ms)),lifecycle_check=None,binary='native',pixel_sink=None,reset_input=lambda:calls.append('reset'),host=SimpleNamespace(close=lambda:calls.append('reap')))
        with patch('lifecycle.install_start_route',return_value=lambda:None):
            restore=install(runtime,Controller)
        try:
            controller=Controller();runtime.lifecycle_check();controller.handle_wipe_timeout()
            with self.assertRaises(WipeInterrupted):runtime.lifecycle_check()
            runtime.lifecycle_check() # Cleanup can poll without repeating interruption.
            error=ValueError('other')
            self.assertEqual(controller.handle_exception(error),('original',error))
            def destination(cls,**kwargs):return (cls,kwargs)
            module=SimpleNamespace(Destination=destination,MainMenuView='home')
            with patch.dict(sys.modules,{'seedsigner.views.view':module}),patch('lifecycle.NativeHost',return_value='new'):
                self.assertEqual(controller.handle_exception(WipeInterrupted()),('home',{'clear_history':True}))
            self.assertEqual(calls,['wipe','reap',('timeout',120000),'consume-override','reset'])
            self.assertEqual(runtime.host,'new');runtime.lifecycle_check()
        finally:restore()
        self.assertIsNone(runtime.lifecycle_check);self.assertIs(Controller.handle_wipe_timeout,original)

    def test_expected_wipe_skips_traceback_but_unexpected_error_keeps_it(self):
        from lifecycle import quiet_wipe_route
        source="""def start(self, error):
    try:
        raise error
    except BaseException as e:
        report(e)
        next_destination = self.handle_exception(e)
    return next_destination
"""
        reports=[]
        run=quiet_wipe_route(source,dict(_LVGLWipeInterrupted=WipeInterrupted,report=reports.append))
        controller=SimpleNamespace(handle_exception=lambda error:type(error).__name__)
        self.assertEqual(run(controller,WipeInterrupted()),'WipeInterrupted');self.assertEqual(reports,[])
        error=ValueError('public fixture')
        self.assertEqual(run(controller,error),'ValueError');self.assertEqual(reports,[error])
        with self.assertRaises(ValueError):quiet_wipe_route('def start(self): pass',{})

    def test_start_route_rejects_unreviewed_controller_without_mutation(self):
        from lifecycle import install_start_route
        class Controller:
            def start(self):return 'unchanged'
        original=Controller.start
        with self.assertRaisesRegex(ValueError,'Unreviewed'):install_start_route(Controller)
        self.assertIs(Controller.start,original)
        self.assertNotIn('_LVGLWipeInterrupted',original.__globals__)
