import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
def load(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/'firmware/bench-profiles'/name)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

class CensusSafetyTests(unittest.TestCase):
    def test_census_exports_counts_without_object_values(self):
        module=load('python-object-census.py')
        with tempfile.TemporaryDirectory() as directory:
            module.OUT=Path(directory)
            with patch.object(module.Path,'read_text',return_value='MemAvailable: 16000 kB\n'),patch.object(module,'memory',return_value={'Pss':123}),patch.object(module.gc,'get_objects',return_value=[{'wallet':'NEVER_EXPORT_THIS_VALUE'}]):
                module.census('idle')
            text=(module.OUT/'idle.json').read_text();data=json.loads(text)
            self.assertNotIn('NEVER_EXPORT_THIS_VALUE',text)
            self.assertNotIn('wallet',text)
            self.assertEqual(data['types'][0]['count'],1)
            self.assertEqual(data['types'][0]['type'],'builtins.dict')

    def test_low_memory_skips_object_list(self):
        module=load('python-object-census.py')
        with tempfile.TemporaryDirectory() as directory:
            module.OUT=Path(directory)
            with patch.object(module.Path,'read_text',return_value='MemAvailable: 4000 kB\n'),patch.object(module,'memory',return_value={'Pss':123}),patch.object(module.gc,'get_objects') as objects:
                module.census('scan')
            objects.assert_not_called()
            self.assertIn('censusSkipped',json.loads((module.OUT/'scan.json').read_text()))

    def test_full_snapshot_refuses_mini_before_output_or_tracing(self):
        module=load('python-memory-profile.py')
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'absent'
            with patch.object(module.sys,'argv',['profiler','--output',str(output),'--request','/tmp/request']),patch.object(module.Path,'read_text',return_value='MemTotal: 46028 kB\n'),patch.object(module.tracemalloc,'start') as start:
                with self.assertRaises(SystemExit):module.main()
            start.assert_not_called();self.assertFalse(output.exists())

if __name__=='__main__':unittest.main()
