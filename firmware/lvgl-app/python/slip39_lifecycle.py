"""Initialize parent wipe fields missing from the pinned Slip39Seed constructor.

No derivation, passphrase normalization, share parsing or wipe routine is replaced.
Keep model loading lazy and preserve original class identity.
"""
import functools,hashlib,json,sys
from importlib.machinery import PathFinder
from pathlib import Path

def initialize_fields(original):
    @functools.wraps(original)
    def initialize(seed,*args,**kwargs):
        seed._mnemonic=[]
        seed._passphrase=''
        original(seed,*args,**kwargs)
    return initialize

def install(app_root,manifest):
    name='seedsigner.models.seed';path=Path(app_root).resolve()/'seedsigner/models/seed.py'
    expected=json.loads(Path(manifest).read_text())['models/seed.py'];patched=[]
    def verify():
        if hashlib.sha256(path.read_bytes()).hexdigest()!=expected:raise ValueError('Unreviewed SLIP39 lifecycle source')
    def prepare(module):
        verify()
        if Path(module.__file__).resolve()!=path:raise ValueError('Unexpected SLIP39 model origin')
        cls=module.Slip39Seed
        if cls.__module__!=name:raise ValueError('Unexpected SLIP39 class origin')
        original=cls.__init__;cls.__init__=initialize_fields(original);patched.append((cls,original))
    class Loader:
        def __init__(self,original):self.original=original
        def create_module(self,spec):
            create=getattr(self.original,'create_module',None)
            return create(spec) if create else None
        def exec_module(self,module):verify();self.original.exec_module(module);prepare(module)
        def __getattr__(self,key):return getattr(self.original,key)
    class Finder:
        def find_spec(self,fullname,search_path=None,target=None):
            if fullname!=name:return None
            spec=PathFinder.find_spec(fullname,search_path,target)
            if spec is None or spec.loader is None or Path(spec.origin).resolve()!=path:raise ValueError('Unexpected SLIP39 model source')
            for dependency_finder in sys.meta_path:
                dependency_spec=getattr(dependency_finder,'lvgl_dependency_spec',None)
                if dependency_spec is not None:
                    spec=dependency_spec(fullname,spec);break
            spec.loader=Loader(spec.loader);return spec
    finder=Finder();sys.meta_path.insert(0,finder)
    try:
        if name in sys.modules:prepare(sys.modules[name])
    except BaseException:
        sys.meta_path.remove(finder);raise
    def restore():
        if finder in sys.meta_path:sys.meta_path.remove(finder)
        for cls,original in reversed(patched):cls.__init__=original
    return restore
