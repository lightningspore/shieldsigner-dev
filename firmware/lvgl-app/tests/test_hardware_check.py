import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from hardware_check import assess,owners,remote_digests,owner_events,diagnostic_pids,remote_command
class HardwareCheckTests(unittest.TestCase):
    def test_remote_shell_preserves_spaced_and_literal_arguments(self):
        import shlex
        arguments=['python3','/public/check.py','--mode','AES-CBC v1',"public ' quote $(literal)"]
        command=remote_command(['adb','-s','public-device'],arguments)
        self.assertEqual(command[:4],['adb','-s','public-device','shell'])
        self.assertEqual(shlex.split(' '.join(command[4:])),arguments)

    def test_adb_zero_is_insufficient_without_one_clean_receipt(self):
        good='{"passed": true}\n'
        self.assertTrue(assess(good,0)[0])
        for output,code,timeout in [('Traceback (most recent call last):\nfailed',0,False),(good+'Traceback (most recent call last):\ncleanup failed',0,False),(good,1,False),(good+good,0,False),(good,0,True),('{"passed": false}',0,False)]:
            self.assertFalse(assess(output,code,timeout)[0])
    def test_owner_check_recognizes_absolute_python_and_camera_processes(self):
        output='PID PPID COMMAND\n1 0 init\n2 1 [python3]\n3 1 /usr/bin/python3 /opt/src/main.py\n4 1 /usr/lib/probe stream-sc3336 plan\n5 1 /tmp/shieldsigner-lvgl-host\n6 1 /bin/sh -c ps\n'
        self.assertEqual([owner['pid'] for owner in owners(output)],[3,4,5])

    def test_hash_verification_batches_all_paths_under_adb_limit(self):
        paths=[Path('public_'+str(n)+'.py') for n in range(88)];calls=[]
        def call(*args):
            self.assertEqual(args[:2],('shell','sha256sum'));self.assertLessEqual(len(args[2:]),16)
            calls.append(args)
            return '\n'.join('a'*64+'  '+name for name in args[2:])
        hashes=remote_digests(call,'/tmp/public',paths)
        self.assertEqual(len(hashes),88);self.assertEqual(len(calls),6)

    def test_owner_metadata_ignores_scalars_and_pixel_fields(self):
        data='"scalar"\n'+ '{"event":"finished","error":"public failure","pixels":"must not export","cleanupErrors":[]}\n'
        self.assertEqual(owner_events(data),[dict(event='finished',error='public failure',cleanupErrors=[])])

    def test_timeout_identity_uses_full_argv_and_exact_script_argument(self):
        script='/userdata/shieldsigner-lvgl-app/public.py'
        def call(*args):
            if args[1]=='ps':return 'PID PPID COMMAND\n10 1 python3 -B -X truncated\n11 1 python3 unrelated\n12 1 python3 gone\n'
            pid=args[2].split('/')[2]
            if pid=='12':
                import subprocess
                raise subprocess.CalledProcessError(1,args)
            return 'python3\0-B\0-X\0cache=long\0'+(script if pid=='10' else script+'.other')+'\0'
        self.assertEqual(diagnostic_pids(call,script),[10])


class RuntimeCacheBundleTests(unittest.TestCase):
    def fixture(self,temporary):
        import json,package
        root=Path(temporary);source=root/'source';staged=root/'staged'
        (source/'python').mkdir(parents=True)
        deployed=staged/package.PREFIX/'python';deployed.mkdir(parents=True)
        (source/'python/public.py').write_text('value=42\n');(deployed/'public.py').write_text('value=42\n')
        (source/'source-guards.json').write_text('{}');(deployed/'source-guards.json').write_text('{}')
        (staged/'runtime-manifest.json').write_text(json.dumps(dict(nativeBuild=dict(binarySha256='a'*64))))
        return source,staged,deployed

    def test_frozen_cache_must_match_binary_sources_and_guards(self):
        import tempfile,package
        from unittest.mock import patch
        from hardware_check import runtime_cache_files
        with tempfile.TemporaryDirectory() as temporary:
            source,staged,deployed=self.fixture(temporary)
            with patch('hardware_check.HERE',source),patch.object(package,'verify') as verify:
                cache,info=runtime_cache_files(staged,'a'*64)
                verify.assert_called_once_with(staged)
                self.assertEqual(cache,deployed/'import-cache')
                self.assertIsNone(info['normalBytecodePrefix'])
                with self.assertRaisesRegex(ValueError,'native binary differs'):runtime_cache_files(staged,'b'*64)
                (deployed/'public.py').write_text('value=43\n')
                with self.assertRaisesRegex(ValueError,'Python differs'):runtime_cache_files(staged,'a'*64)
                (deployed/'public.py').write_text('value=42\n');(deployed/'source-guards.json').write_text('{"different":true}')
                with self.assertRaisesRegex(ValueError,'source guards differ'):runtime_cache_files(staged,'a'*64)


    def test_cold_source_mode_requires_a_frozen_runtime_before_any_adb_call(self):
        import io
        from contextlib import redirect_stderr
        from unittest.mock import patch
        from hardware_check import main
        with patch('sys.argv',['hardware_check','app-entry-flow','--fresh-normal-cache']),patch('hardware_check.subprocess.check_output') as call,redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as error:main()
            self.assertEqual(error.exception.code,2)
            call.assert_not_called()
