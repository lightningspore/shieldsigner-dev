import sys,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from live_info import configure,monitor,lines,state
class LiveInfoTests(unittest.TestCase):
    def test_original_formatter_and_refresh_deadline_are_preserved(self):
        samples=[];sent=[];now=[0]
        class Screen:
            ROWS=[('total','Total')];REFRESH_INTERVAL=2.0
            def _build_lines(self):samples.append(self.row_labels);return ['Total: '+str(len(samples))]
        with patch('live_info.time.monotonic',side_effect=lambda:now[0]):
            builder,cfg=configure(Screen,{'top_nav':{}})
            runtime=SimpleNamespace(host=SimpleNamespace(send=lambda *args,**kwargs:sent.append((args,kwargs))))
            poll=monitor(runtime,Screen,cfg)
            poll();self.assertEqual(len(samples),1)
            now[0]=2;poll();self.assertEqual(sent,[(('info_text',),{'text':'Total: 2'})])
            self.assertEqual(runtime.memory_info_stats,dict(samples=2,updates=1,refreshInterval=2.0,extraThreads=0))
            self.assertEqual(builder,'button_list_screen');self.assertTrue(cfg['live_info'])
    def test_unchanged_lines_do_not_send_redundant_updates(self):
        class Screen:
            ROWS=[('total','Total')];REFRESH_INTERVAL=2
            def _build_lines(self):return ['Total: 1']
        runtime=SimpleNamespace(host=SimpleNamespace(send=lambda *args,**kwargs:self.fail('redundant update')))
        with patch('live_info.time.monotonic',side_effect=[0,2]):
            poll=monitor(runtime,Screen,{'text':'Total: 1'});poll()
        self.assertEqual(runtime.memory_info_stats['samples'],2)
    def test_bad_row_count_is_rejected(self):
        class Screen:
            ROWS=[('total','Total')]
            def _build_lines(self):return []
        with self.assertRaises(ValueError):lines(Screen,state(Screen))
