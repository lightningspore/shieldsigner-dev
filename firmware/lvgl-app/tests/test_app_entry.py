import os,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from app import options,check_owners,stop_workers,termination_signals,check_settings_destination,verify_native_artifact
class AppEntryTests(unittest.TestCase):
    def test_original_cli_arguments_forward_unchanged(self):
        args=options(['--settings','/tmp/public-lvgl-settings.json','--','--iotest','--loglevel','WARNING'])
        self.assertEqual(args.upstream,['--iotest','--loglevel','WARNING'])
    def test_competing_owner_rejected_without_signals(self):
        with tempfile.TemporaryDirectory() as temporary:
            proc=Path(temporary);other=proc/str(os.getpid()+1);other.mkdir()
            for command in (b'python3\0/opt/main.py\0',b'/tmp/shieldsigner-lvgl-host\0',b'/usr/bin/probe\0stream-sc3336\0'):
                (other/'cmdline').write_bytes(command)
                with self.assertRaises(RuntimeError):check_owners(proc)
            (other/'cmdline').write_bytes(b'');check_owners(proc)
            (other/'cmdline').write_bytes(b'/usr/bin/sshd\0');check_owners(proc)
    def test_current_process_is_not_a_competing_owner(self):
        with tempfile.TemporaryDirectory() as temporary:
            proc=Path(temporary);own=proc/str(os.getpid());own.mkdir()
            (own/'cmdline').write_bytes(b'python3\0app.py\0');check_owners(proc)

    def test_shutdown_stops_all_before_join_and_skips_unstarted_workers(self):
        from types import SimpleNamespace
        calls=[]
        class Worker:
            def __init__(self,name,live=True):self.name=name;self.live=live
            def is_alive(self):return self.live
            def stop(self):calls.append(('stop',self.name))
            def join(self,timeout):calls.append(('join',self.name));self.live=False
        one=Worker('one');two=Worker('two');dead=Worker('dead',False)
        stop_workers(SimpleNamespace(toast_notification_thread=one,battery_hat=dead,wipe_timer_thread=two,rng_monitor_thread=one))
        self.assertEqual(calls,[('stop','one'),('stop','two'),('join','one'),('join','two')])
    def test_shutdown_attempts_siblings_after_stop_failure(self):
        from types import SimpleNamespace
        calls=[]
        class Bad:
            def is_alive(self):return True
            def stop(self):calls.append('bad-stop');raise ValueError('test')
            def join(self,timeout):calls.append('bad-join')
        class Good:
            live=True
            def is_alive(self):return self.live
            def stop(self):calls.append('good-stop')
            def join(self,timeout):calls.append('good-join');self.live=False
        with self.assertRaisesRegex(RuntimeError,'shutdown incomplete'):
            stop_workers(SimpleNamespace(wipe_timer_thread=Bad(),rng_monitor_thread=Good()))
        self.assertEqual(calls,['bad-stop','good-stop','bad-join','good-join'])

    def test_term_unwinds_once_and_restores_previous_handler(self):
        import signal
        previous=signal.getsignal(signal.SIGTERM)
        with termination_signals():
            handler=signal.getsignal(signal.SIGTERM)
            with self.assertRaises(KeyboardInterrupt):handler(signal.SIGTERM,None)
            self.assertIsNone(handler(signal.SIGTERM,None))
        self.assertIs(signal.getsignal(signal.SIGTERM),previous)

    def test_settings_reject_original_symlink_and_hardlink_without_writes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);original=root/'original.json';original.write_text('public marker')
            symbolic=root/'symbolic.json';symbolic.symlink_to(original)
            hard=root/'hard.json';os.link(original,hard)
            for path in (original,symbolic,hard,root):
                with self.assertRaises(ValueError):check_settings_destination(path,original)
            self.assertEqual(original.read_text(),'public marker')
    def test_settings_accept_separate_regular_or_new_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);original=root/'original.json';original.write_text('public marker')
            separate=root/'lvgl.json';check_settings_destination(separate,original)
            self.assertFalse(separate.exists())
            separate.write_text('separate marker');check_settings_destination(separate,original)
            self.assertEqual(separate.read_text(),'separate marker')

    def test_native_artifact_requires_matching_build_metadata(self):
        import json,hashlib
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);binary=root/'native';binary.write_bytes(b'public build fixture')
            manifest=root/'manifest.json';metadata=dict(target='arm-linux-musleabihf',binarySha256=hashlib.sha256(binary.read_bytes()).hexdigest(),inputs={'native/host.cpp':'public source digest'})
            manifest.write_text(json.dumps(metadata));self.assertEqual(verify_native_artifact(binary,manifest),metadata)
            binary.write_bytes(b'changed public fixture')
            with self.assertRaisesRegex(ValueError,'hash mismatch'):verify_native_artifact(binary,manifest)
            for invalid in ({},[],dict(metadata,target='x86_64-linux'),dict(metadata,inputs={})):
                manifest.write_text(json.dumps(invalid))
                with self.assertRaises(ValueError):verify_native_artifact(binary,manifest)
