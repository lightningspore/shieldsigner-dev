"""Defer the legacy stream's Pillow import; native frame transport is unchanged."""
import hashlib,sys
from importlib.machinery import PathFinder
from pathlib import Path
SOURCE_SHA256='db700586037edd9a3dd198bce64ece52dc999f92d92ffd07c33e08c83c194c75'
NAME='shieldsigner_video_stream'
def deferred(source):
    if hashlib.sha256(source).hexdigest()!=SOURCE_SHA256:raise ValueError('Unreviewed managed stream source')
    text=source.decode();line='from PIL import Image\n';method='    def _frame_from_payload(self, width, height, payload):\n'
    if text.count(line)!=1 or text.count(method)!=1:raise ValueError('Changed legacy stream image import')
    # Reuse the first comment line for the local import, preserving source line
    # positions for every original method and traceback.
    if text.count(method+'        #')!=1:raise ValueError('Changed legacy stream conversion header')
    return text.replace(line,'\n',1).replace(method+'        #',method+'        from PIL import Image  #',1)
def install():
    if NAME in sys.modules:raise RuntimeError('Install stream imports before camera modules load')
    class Loader:
        def create_module(self,spec):return None
        def exec_module(self,module):
            path=Path(module.__spec__.origin)
            source=path.read_bytes()
            if hashlib.sha256(source).hexdigest()!=SOURCE_SHA256:raise ValueError('Unreviewed managed stream source')
            from import_cache import load
            code=load(NAME,source,filename=str(path))
            if code is None:code=compile(deferred(source),str(path),'exec')
            exec(code,module.__dict__)
    class Finder:
        def find_spec(self,fullname,path=None,target=None):
            if fullname!=NAME:return None
            spec=PathFinder.find_spec(fullname,path,target)
            if spec is None or not spec.origin:raise ValueError('Managed stream module unavailable')
            spec.loader=Loader();return spec
    finder=Finder();sys.meta_path.insert(0,finder)
    def restore():
        if finder in sys.meta_path:sys.meta_path.remove(finder)
    return restore
