"""Route reviewed direct Screen(...).display() calls without PIL construction."""
from types import SimpleNamespace

def install(runtime,classes):
    """Patch only this process; preserve class identity, dataclass init and fields.

    Unknown subclasses retain their original constructors. The View dispatch
    still rejects unreviewed classes before constructing them.
    """
    classes=set(classes)
    snapshots=[]
    for cls in classes:
        snapshots.append((cls,cls.__dict__.get('__post_init__'),cls.__dict__.get('display'),getattr(cls,'__post_init__'),getattr(cls,'display')))
    for cls,own_post,own_display,original_post,original_display in snapshots:
        def post(screen,_original=original_post):
            if type(screen) not in classes:_original(screen)
            elif type(screen).__name__=="SeedSignMessageConfirmMessageScreen":
                from message_contracts import prepare
                prepare(screen)
        def display(screen,_original=original_display):
            if type(screen) not in classes:return _original(screen)
            value=runtime.run(type(screen),dict(vars(screen)))
            screen.buttons=[SimpleNamespace(scroll_y=runtime.last_scroll_y)]
            screen.selected_button=value
            return value
        cls.__post_init__=post
        cls.display=display
    def uninstall():
        for cls,own_post,own_display,_,_ in snapshots:
            for name,original in [('__post_init__',own_post),('display',own_display)]:
                if original is None:delattr(cls,name)
                else:setattr(cls,name,original)
    return uninstall


def install_modules(runtime,supported,module_specs):
    """Patch reviewed screen modules when imported, without loading every screen.

    Preserve original import loaders, module/class identities and constructors.
    Exact-path/hash checks are repeated at execution for modules loaded later.
    """
    import hashlib,sys
    from importlib.machinery import PathFinder
    from pathlib import Path
    restorers=[];seen=set()
    def prepare(module):
        if module.__name__ in seen:return
        path,digest=module_specs[module.__name__]
        if Path(module.__file__).resolve()!=Path(path).resolve() or hashlib.sha256(Path(path).read_bytes()).hexdigest()!=digest:
            raise ValueError('Unreviewed lazy screen module '+module.__name__)
        classes={value for name,value in vars(module).items() if name in supported and isinstance(value,type) and value.__module__==module.__name__}
        restorers.append(install(runtime,classes));seen.add(module.__name__)
    class Loader:
        def __init__(self,original):self.original=original
        def create_module(self,spec):
            create=getattr(self.original,'create_module',None)
            return create(spec) if create else None
        def exec_module(self,module):
            path,digest=module_specs[module.__name__]
            if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=digest:raise ValueError('Changed lazy screen source')
            self.original.exec_module(module);prepare(module)
        def __getattr__(self,name):return getattr(self.original,name)
    class Finder:
        def find_spec(self,fullname,path=None,target=None):
            if fullname not in module_specs:return None
            spec=PathFinder.find_spec(fullname,path,target)
            if spec is None or spec.loader is None or Path(spec.origin).resolve()!=Path(module_specs[fullname][0]).resolve():raise ValueError('Unexpected lazy screen origin')
            for finder in sys.meta_path:
                dependency_spec=getattr(finder,'lvgl_dependency_spec',None)
                if dependency_spec is not None:
                    spec=dependency_spec(fullname,spec);break
            spec.loader=Loader(spec.loader);return spec
    finder=Finder();sys.meta_path.insert(0,finder)
    try:
        for name in module_specs:
            if name in sys.modules:prepare(sys.modules[name])
    except BaseException:
        sys.meta_path.remove(finder)
        for restore in reversed(restorers):restore()
        raise
    def restore():
        if finder in sys.meta_path:sys.meta_path.remove(finder)
        for undo in reversed(restorers):undo()
    return restore
