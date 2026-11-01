import importlib.util,os,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from bytecode_cache import prepare,current
class BytecodeCacheTests(unittest.TestCase):
    def test_checked_hash_reuses_and_detects_same_size_same_time_edit(self):
        old=sys.pycache_prefix
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder).resolve();source=root/'source';source.mkdir();file=source/'public.py';file.write_text('value=1\n')
            try:
                sys.pycache_prefix=str(root/'cache')
                first=prepare([source]);self.assertEqual(first['compiled'],1)
                self.assertEqual(prepare([source])['reused'],1)
                timestamp=file.stat().st_mtime_ns
                file.write_text('value=2\n');os.utime(file,ns=(timestamp,timestamp))
                cache=importlib.util.cache_from_source(str(file))
                self.assertFalse(current(cache,file.read_bytes()))
                old_write=sys.dont_write_bytecode
                try:
                    sys.dont_write_bytecode=True
                    spec=importlib.util.spec_from_file_location('cache_public',file)
                    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
                    self.assertEqual(module.value,2)
                finally:sys.dont_write_bytecode=old_write
                self.assertEqual(prepare([source])['compiled'],1)
                self.assertTrue(current(cache,file.read_bytes()))
                self.assertFalse((source/'__pycache__').exists())
            finally:sys.pycache_prefix=old
    def test_no_implicit_cache_and_repair_truncated_file(self):
        old=sys.pycache_prefix
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder).resolve();source=root/'source';source.mkdir();file=source/'public.py';file.write_text('value=1\n')
            try:
                sys.pycache_prefix=None
                with self.assertRaises(ValueError):prepare([source])
                sys.pycache_prefix=str(root/'cache');prepare([source])
                cache=Path(importlib.util.cache_from_source(str(file)));cache.write_bytes(cache.read_bytes()[:16])
                self.assertEqual(prepare([source])['compiled'],1)
            finally:sys.pycache_prefix=old


    def test_staging_uses_target_filenames_and_checked_hash_without_execution(self):
        import json,marshal
        from bytecode_cache import stage_sources
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder).resolve();source=root/'input.py';source.write_text('raise RuntimeError("must not execute")\n')
            output=root/'cache';stage_sources([dict(source=str(source),filename='/opt/src/public.py')],output)
            record=json.loads((output/'index.json').read_text());entry=record['entries'][0];data=(output/entry['file']).read_bytes()
            self.assertEqual(int.from_bytes(data[4:8],'little'),3)
            self.assertEqual(marshal.loads(data[16:]).co_filename,'/opt/src/public.py')
            self.assertTrue(current(output/entry['file'],source.read_bytes()))
            self.assertNotIn(str(root),str(record))
            with self.assertRaises(ValueError):stage_sources([dict(source=str(source),filename='../unsafe.py')],root/'bad')
            with self.assertRaisesRegex(ValueError,'Duplicate'):stage_sources([dict(source=str(source),filename='/opt/public.py')]*2,root/'duplicate')

    def test_staged_cache_relocation_and_stale_source_fallback(self):
        import json,shutil
        from bytecode_cache import stage_sources
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder).resolve();source=root/'public.py';source.write_text('value=1\ndef origin(): return 42\n')
            output=root/'cache';stage_sources([dict(source=str(source),filename='/opt/src/public.py')],output)
            entry=json.loads((output/'index.json').read_text())['entries'][0]
            old=sys.pycache_prefix;old_write=sys.dont_write_bytecode
            try:
                sys.pycache_prefix=str(output);sys.dont_write_bytecode=True
                relocated=Path(importlib.util.cache_from_source(str(source)));relocated.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(output/entry['file'],relocated)
                def load():
                    spec=importlib.util.spec_from_file_location('staged_public',source);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
                loaded=load();self.assertEqual(loaded.value,1)
                self.assertEqual(loaded.origin.__code__.co_filename,str(source))
                timestamp=source.stat().st_mtime_ns;source.write_text('value=2\ndef origin(): return 42\n');os.utime(source,ns=(timestamp,timestamp))
                self.assertEqual(load().value,2)
                self.assertFalse(current(relocated,source.read_bytes()))
            finally:sys.pycache_prefix=old;sys.dont_write_bytecode=old_write
