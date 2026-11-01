"""Guarded display-only correction: include the final partial mnemonic page."""
from source_text import getsource as adapter_source
import ast,functools,hashlib,inspect,json,linecache,textwrap
from pathlib import Path

def compile_run(source,namespace,filename):
    tree=ast.parse(textwrap.dedent(source));matches=[]
    for node in ast.walk(tree):
        if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id=='num_pages':matches.append(node)
    if len(matches)!=1 or ast.unparse(matches[0].value)!='int(len(mnemonic) / words_per_page)':raise ValueError('Unexpected mnemonic page calculation')
    matches[0].value=ast.parse('(len(mnemonic) + words_per_page - 1) // words_per_page',mode='eval').body
    if len(tree.body)!=1 or not isinstance(tree.body[0],ast.FunctionDef) or tree.body[0].name!='run':raise ValueError('Unexpected mnemonic review method')
    ast.fix_missing_locations(tree);local={};exec(compile(tree,filename,'exec'),namespace,local)
    return local['run']

def install(view_class,app_root,manifest):
    original_init=view_class.__init__;patched={}
    path=Path(app_root).resolve()/'seedsigner/views/seed_views.py'
    expected=json.loads(Path(manifest).read_text())['views/seed_views.py']
    @functools.wraps(original_init)
    def initialize(view,*args,**kwargs):
        original_init(view,*args,**kwargs)
        cls=type(view)
        if (cls.__module__,cls.__name__)!=('seedsigner.views.seed_views','SeedWordsView') or cls in patched:return
        if Path(inspect.getfile(cls)).resolve()!=path or hashlib.sha256(path.read_bytes()).hexdigest()!=expected:raise ValueError('Unreviewed mnemonic review View')
        method=cls.run;source=adapter_source(method);filename=str(path)+' [LVGL partial word page]'
        linecache.cache[filename]=(len(source),None,textwrap.dedent(source).splitlines(True),filename)
        replacement=compile_run(source,method.__globals__,filename);replacement.__qualname__=method.__qualname__
        patched[cls]=method;cls.run=replacement
    view_class.__init__=initialize
    def restore():
        view_class.__init__=original_init
        for cls,method in patched.items():cls.run=method
    return restore
