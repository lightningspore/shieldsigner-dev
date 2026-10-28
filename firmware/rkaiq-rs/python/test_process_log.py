"""Exercise pipe draining, bounded disk use and conservative session retention."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from shieldsigner_process_log import ProcessLog, record_finished_session, MARKER, OWNER


class ProcessLogTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def test_large_child_cannot_block_and_keeps_start_and_shutdown(self):
        log = ProcessLog(self.root / 'owner.log', head_bytes=256, tail_bytes=768)
        command = "import os; os.write(1,b'START\\n'); [os.write(1,b'x'*8192+b'\\n') for _ in range(256)]; os.write(1,b'FINAL-SHUTDOWN\\n')"
        child = subprocess.Popen([sys.executable, '-c', command], stdout=subprocess.PIPE)
        log.start(child.stdout)
        self.assertEqual(child.wait(timeout=5), 0)
        info = log.finish()
        output = (self.root / 'owner.log').read_bytes()
        self.assertTrue(output.startswith(b'START\n'))
        self.assertTrue(output.endswith(b'FINAL-SHUTDOWN\n'))
        self.assertIn(b'bytes omitted', output)
        self.assertLessEqual(len(output), 1024 + 100)
        self.assertGreater(info['bytesReceived'], 2_000_000)
        self.assertIsNone(info['errorType'])
        self.assertEqual(log.finish(), info)

    def test_untruncated_stream_is_byte_exact(self):
        for payload in [b'a'*100, b'a'*300, b'a'*1024]:
            with self.subTest(length=len(payload)):
                path = self.root / str(len(payload))
                log = ProcessLog(path, head_bytes=256, tail_bytes=768)
                for offset in range(0, len(payload), 37):
                    log._append(payload[offset:offset+37])
                log.finish()
                self.assertEqual(path.read_bytes(), payload)

    def test_disk_failure_still_drains_producer(self):
        log = ProcessLog(self.root / 'owner.log', head_bytes=256, tail_bytes=768)
        def fail(_):
            raise OSError('simulated full filesystem')
        log._write = fail
        child = subprocess.Popen([sys.executable, '-c', "import os; [os.write(1,b'a'*8192) for _ in range(256)]"], stdout=subprocess.PIPE)
        log.start(child.stdout)
        self.assertEqual(child.wait(timeout=5), 0)
        info = log.finish()
        self.assertEqual(info['errorType'], 'OSError')
        self.assertEqual(info['bytesReceived'], 256*8192)

    def test_full_diagnostic_mode_preserves_all_bytes(self):
        payload = bytes(range(256))*100
        log = ProcessLog(self.root / 'owner.log', full=True, head_bytes=256, tail_bytes=768)
        log._append(payload)
        info = log.finish()
        self.assertEqual((self.root / 'owner.log').read_bytes(), payload)
        self.assertTrue(info['fullLog'])
        self.assertIsNone(info['maxRetainedPayloadBytes'])

    def test_retention_only_prunes_owned_finished_bounded_sessions(self):
        info = {'fullLog': False, 'bytesReceived': 0, 'errorType': None}
        unknown = self.root / 'camera-unknown'; unknown.mkdir()
        active = self.root / 'camera-active'; active.mkdir()
        (active / 'owner.log').write_text('active')
        diagnostic = self.root / 'camera-diagnostic'; diagnostic.mkdir()
        record_finished_session(diagnostic, 0, {**info, 'fullLog': True})
        linked = self.root / 'camera-symlink'; linked.symlink_to(unknown, target_is_directory=True)
        for i in range(6):
            directory = self.root / ('camera-' + str(i)); directory.mkdir()
            record_finished_session(directory, 0, info)
        bounded = [path for path in self.root.glob('camera-*') if (path / MARKER).exists()
                   and not json.loads((path / MARKER).read_text())['fullLog']]
        self.assertEqual(len(bounded), 3)
        self.assertTrue((self.root / 'camera-5').exists())
        for path in [unknown, active, diagnostic, linked]:
            self.assertTrue(path.exists())


if __name__ == '__main__':
    unittest.main()
