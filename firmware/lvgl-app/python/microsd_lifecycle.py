"""Cancellable FIFO wait around pinned original microSD event callbacks."""
from source_text import getsource as adapter_source
import ast,hashlib,inspect,json,os,select,time,textwrap
from pathlib import Path

def read_event(worker):
    descriptor=os.open(worker.FIFO_PATH,os.O_RDONLY|os.O_NONBLOCK)
    data=bytearray()
    try:
        while worker.keep_running:
            ready,_,_=select.select([descriptor],[],[],.1)
            if not ready:continue
            chunk=os.read(descriptor,4096)
            if chunk:
                data.extend(chunk)
                if len(data)>4096:raise ValueError('microSD event exceeds bound')
            elif data:return data.decode()
            else:time.sleep(.02) # A writer has not connected yet.
        return None
    finally:os.close(descriptor)

def compile_run(source,namespace):
    tree=ast.parse(textwrap.dedent(source));matches=0
    for node in ast.walk(tree):
        if not isinstance(node,ast.While):continue
        for index,statement in enumerate(node.body):
            if not isinstance(statement,ast.With):continue
            if ast.unparse(statement.items[0].context_expr)!='open(self.FIFO_PATH)':continue
            if len(statement.items)!=1 or ast.unparse(statement.items[0].optional_vars)!='fifo' or ast.unparse(statement.body[0])!='action = fifo.read()':raise ValueError('Unexpected microSD FIFO block')
            replacement=ast.parse('action = _lvgl_read_microsd_event(self)\nif action is None:\n    break').body
            node.body[index:index+1]=replacement+statement.body[1:];matches+=1
    if matches!=1 or len(tree.body)!=1 or tree.body[0].name!='run':raise ValueError('Unexpected microSD run structure')
    ast.fix_missing_locations(tree);local={}
    exec(compile(tree,'<guarded cancellable microSD wait>','exec'),namespace,local)
    return local['run']

def install(cls,app_root,manifest):
    path=Path(app_root).resolve()/'seedsigner/hardware/microsd.py'
    guards=json.loads(Path(manifest).read_text())
    if Path(inspect.getfile(cls)).resolve()!=path or hashlib.sha256(path.read_bytes()).hexdigest()!=guards['hardware/microsd.py']:raise ValueError('Unreviewed microSD lifecycle source')
    original=cls.run;namespace=dict(original.__globals__);namespace['_lvgl_read_microsd_event']=read_event
    cls.run=compile_run(adapter_source(original),namespace)
    def restore():cls.run=original
    return restore
