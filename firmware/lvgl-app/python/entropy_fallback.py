"""Bind original final-image/IV retry branches to the guarded Rust Camera."""
from source_text import getsource as adapter_source
import ast,functools,hashlib,inspect,json,linecache,textwrap
from pathlib import Path

def compile_run(source,namespace,filename):
    tree=ast.parse(textwrap.dedent(source));count=0
    for node in ast.walk(tree):
        if isinstance(node,ast.ImportFrom) and node.module=='seedsigner.hardware.camera':
            if len(node.names)!=1 or node.names[0].name!='Camera' or node.names[0].asname is not None:raise ValueError('Unexpected fallback Camera import')
            node.module='entropy_camera';node.names=[ast.alias(name='FallbackCamera',asname='Camera')];count+=1
    if count!=1 or len(tree.body)!=1 or not isinstance(tree.body[0],ast.FunctionDef) or tree.body[0].name!='run':raise ValueError('Unexpected final-image fallback method')
    from dependency_policy import bind_original_pillow
    tree=bind_original_pillow(tree,namespace)
    ast.fix_missing_locations(tree);local={};exec(compile(tree,filename,'exec'),namespace,local)
    return local['run']

def install(view_class,app_root,manifest):
    original_init=view_class.__init__;patched={}
    base=Path(app_root).resolve()/'seedsigner';guards=json.loads(Path(manifest).read_text())
    targets={('seedsigner.views.tools_views','ToolsImageEntropyFinalImageView'):'views/tools_views.py',('seedsigner.views.seed_views','SeedEncryptedQRnonECBModeView'):'views/seed_views.py'}
    @functools.wraps(original_init)
    def initialize(view,*args,**kwargs):
        original_init(view,*args,**kwargs)
        cls=type(view)
        relative=targets.get((cls.__module__,cls.__name__))
        if relative is None or cls in patched:return
        path=base/relative;expected=guards[relative]
        if Path(inspect.getfile(cls)).resolve()!=path or hashlib.sha256(path.read_bytes()).hexdigest()!=expected:raise ValueError('Unreviewed entropy fallback View')
        method=cls.run;source=adapter_source(method)
        filename=str(path)+' [LVGL entropy fallback]'
        lines=textwrap.dedent(source).splitlines(True)
        linecache.cache[filename]=(len(source),None,lines,filename)
        replacement=compile_run(source,method.__globals__,filename)
        replacement.__qualname__=method.__qualname__;patched[cls]=method;cls.run=replacement
    view_class.__init__=initialize
    def restore():
        view_class.__init__=original_init
        for cls,method in patched.items():cls.run=method
    return restore
