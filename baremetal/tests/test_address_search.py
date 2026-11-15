# SPDX-License-Identifier: MIT
import sys,unittest
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]/'app'))
from seedsigner_port.address_search import Counter,Worker
class CountingWorker(Worker):
 def __init__(self,counter,events):super().__init__();self.threadsafe_counter=counter;self.events=events
 def run(self):
    try:
        while self.keep_running:
            self.events.append(self.threadsafe_counter.cur_count)
            self.threadsafe_counter.increment()
            yield
    finally:self.events.append('closed')
class WorkerTest(unittest.TestCase):
 def test_foreground_steps_and_skip_use_shared_current_index(self):
    counter=Counter();events=[];worker=CountingWorker(counter,events);worker.start()
    self.assertEqual(events,[]);self.assertIs(counter.worker,worker)
    worker.step();counter.increment(10);worker.step()
    self.assertEqual(events,[0,11]);worker.stop()
    self.assertEqual(events,[0,11,'closed']);self.assertFalse(worker.is_alive());self.assertIsNone(counter.worker)
 def test_duplicate_owner_and_idempotent_stop(self):
    counter=Counter();events=[];a=CountingWorker(counter,events);b=CountingWorker(counter,events);a.start()
    with self.assertRaisesRegex(RuntimeError,'already active'):a.start()
    with self.assertRaisesRegex(RuntimeError,'already owned'):b.start()
    a.stop();a.stop();self.assertFalse(a.step());self.assertIsNone(counter.worker)
 def test_error_and_interrupt_release_generator_and_counter(self):
    for error in (ValueError('public'),KeyboardInterrupt()):
        class Broken(CountingWorker):
            def run(self):
                try:raise error
                finally:self.events.append('closed')
                yield
        counter=Counter();events=[];worker=Broken(counter,events);worker.start()
        with self.assertRaises(type(error)):worker.step()
        self.assertFalse(worker.is_alive());self.assertIsNone(counter.worker);self.assertEqual(events,['closed'])
 def test_normal_generator_exhaustion_releases_owner(self):
    class Once(CountingWorker):
        def run(self):yield
    counter=Counter();worker=Once(counter,[]);worker.start()
    self.assertTrue(worker.step());self.assertFalse(worker.step());self.assertIsNone(counter.worker)

class SourceWorkerFidelityTest(unittest.TestCase):
 def test_search_bodies_match_original_after_only_yield_removal(self):
    import ast,copy
    root=Path(__file__).resolve().parents[1]
    sys.path.append(str(root/'tools'))
    from view_source_port import LazyPort
    source=ast.parse((root.parent/'dist/firmware/sources/lvgl/application/src/seedsigner/views/seed_views.py').read_text())
    classes={n.name:n for n in source.body if isinstance(n,ast.ClassDef)}
    original=classes['SeedAddressVerificationView']
    actual_tree=ast.parse((root/'app/seedsigner_port/view_seed.py').read_text())
    actual=next(n.body[0] for n in actual_tree.body if isinstance(n,ast.FunctionDef) and n.name=='_make_SeedAddressVerificationView')
    class RemoveYield(ast.NodeTransformer):
        def visit_Expr(self,node):
            if isinstance(node.value,ast.Yield):return None
            return self.generic_visit(node)
    for name in ('BruteForceAddressVerificationThread','ExpandedBruteForceAddressVerificationThread'):
        expected_class=next(n for n in original.body if isinstance(n,ast.ClassDef) and n.name==name)
        actual_class=next(n for n in actual.body if isinstance(n,ast.ClassDef) and n.name==name)
        expected=next(n for n in expected_class.body if isinstance(n,ast.FunctionDef) and n.name=='run')
        current=next(n for n in actual_class.body if isinstance(n,ast.FunctionDef) and n.name=='run')
        port=LazyPort(source,'seedsigner.views.seed_views',classes=classes,bindings={'time':('seedsigner_port.clock',None)})
        expected=port.visit(copy.deepcopy(expected));current=RemoveYield().visit(copy.deepcopy(current))
        self.assertEqual(ast.dump(expected,include_attributes=False),ast.dump(current,include_attributes=False),name)
