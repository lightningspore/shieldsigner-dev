import os,sys,tempfile,threading,time,unittest
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from microsd_lifecycle import read_event,compile_run
class MicroSDLifecycleTests(unittest.TestCase):
    def test_stop_unblocks_fifo_without_fake_event(self):
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)/'events';os.mkfifo(path)
            worker=SimpleNamespace(FIFO_PATH=path,keep_running=True);result=[]
            thread=threading.Thread(target=lambda:result.append(read_event(worker)))
            thread.start();time.sleep(.05);worker.keep_running=False;thread.join(1)
            self.assertFalse(thread.is_alive());self.assertEqual(result,[None])
    def test_writer_chunks_preserve_complete_event_on_close(self):
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)/'events';os.mkfifo(path)
            worker=SimpleNamespace(FIFO_PATH=path,keep_running=True);result=[]
            thread=threading.Thread(target=lambda:result.append(read_event(worker)))
            thread.start()
            with path.open('wb',buffering=0) as output:
                output.write(b'add');time.sleep(.02);output.write(b'\n')
            thread.join(1);worker.keep_running=False
            self.assertFalse(thread.is_alive());self.assertEqual(result,['add\n'])
    def test_changed_original_block_rejected(self):
        with self.assertRaises(ValueError):compile_run('def run(self):\n    pass',{})
    def test_pinned_original_event_callbacks_and_setup_failure_match(self):
        import ast,logging,types
        from unittest.mock import patch
        from contextlib import nullcontext
        source=(Path(__file__).resolve().parents[3]/'dist/firmware/sources/lvgl/application/src/seedsigner/hardware/microsd.py').read_text()
        cls=next(n for n in ast.parse(source).body if isinstance(n,ast.ClassDef) and n.name=='MicroSD')
        method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='run')
        text=ast.get_source_segment(source,method)
        def execute(adapted,inserted,setup_failure=False,cancel=False):
            events=[];messages=['add','remove\n'];worker=SimpleNamespace(FIFO_PATH='/public/events',FIFO_MODE=0o600,is_inserted=inserted,keep_running=True)
            def read():return messages.pop(0)
            def settings_event(action):events.append(('settings',action))
            def toast_event(toast):
                events.append(('toast',toast))
                if not messages:worker.keep_running=False
            settings=types.ModuleType('seedsigner.models.settings')
            settings.Settings=SimpleNamespace(is_seedsigner_os=lambda:True,handle_microsd_state_change=settings_event)
            controller=types.ModuleType('seedsigner.controller')
            controller.Controller=SimpleNamespace(get_instance=lambda:SimpleNamespace(activate_toast=toast_event))
            toast=types.ModuleType('seedsigner.gui.toast')
            toast.SDCardStateChangeToastManagerThread=lambda **kwargs:kwargs['action']
            def mkfifo(path,mode):
                events.append(('mkfifo',path,mode))
                if setup_failure:raise OSError('public fixture')
            fake_os=SimpleNamespace(path=SimpleNamespace(exists=lambda path:True),remove=lambda path:events.append(('remove',path)),mkfifo=mkfifo)
            namespace=dict(os=fake_os,time=SimpleNamespace(sleep=lambda value:events.append(('sleep',value))),logger=logging.getLogger('microsd-test'),MicroSD=SimpleNamespace(ACTION__INSERTED='add',ACTION__REMOVED='remove'),open=lambda path:nullcontext(SimpleNamespace(read=read)),_lvgl_read_microsd_event=lambda worker:None if cancel else read())
            if adapted:run=compile_run(text,namespace)
            else:
                local={};exec(compile(ast.Module(body=[method],type_ignores=[]),'<original microSD>','exec'),namespace,local);run=local['run']
            with patch.dict(sys.modules,{'seedsigner.models.settings':settings,'seedsigner.controller':controller,'seedsigner.gui.toast':toast}):run(worker)
            return events
        for inserted in (False,True):
            self.assertEqual(execute(False,inserted),execute(True,inserted))
            self.assertEqual(execute(False,inserted,True),execute(True,inserted,True))
        events=execute(True,True,cancel=True)
        self.assertEqual([e for e in events if e[0]=='settings'],[('settings','add')])
        self.assertFalse(any(e[0]=='toast' for e in events))
