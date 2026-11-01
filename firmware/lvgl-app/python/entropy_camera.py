"""Private copy of the existing guarded Rust Camera adapter; no app-file edits."""
import hashlib,importlib,sys,types
from pathlib import Path
from startup_policy import INTEGRATION_SHA256

def create(app_root='/opt/src',camera_root='/usr/lib/shieldsigner-camera/python'):
    root=Path(camera_root).resolve();path=root/'shieldsigner_integration.py'
    if hashlib.sha256(path.read_bytes()).hexdigest()!=INTEGRATION_SHA256:raise ValueError('Unreviewed camera integration')
    sys.path.insert(0,str(root));integration=importlib.import_module('shieldsigner_integration')
    if Path(integration.__file__).resolve()!=path:raise ValueError('Unexpected camera integration path')
    path,original,patched=integration.camera_source(app_root)
    # Same guarded source transform as the installed camera integration, isolated
    # from the original application's Camera singleton and module registry.
    module=types.ModuleType('shieldsigner_lvgl_entropy_camera');module.__file__=str(path)
    exec(compile(patched,str(path)+' [private Rust entropy camera]','exec'),module.__dict__)
    return module.Camera.get_instance()

def start(camera,**kwargs):
    """Use the same default owner config as scan; restore caller environment."""
    import os
    values={'SHIELDSIGNER_FRONTEND_BACKEND':'rust','SHIELDSIGNER_CAMERA_CONFIG':os.environ.get('SHIELDSIGNER_CAMERA_CONFIG','/usr/lib/shieldsigner-camera/owner.json')}
    if not Path(values['SHIELDSIGNER_CAMERA_CONFIG']).is_file():raise ValueError('Missing managed camera owner config')
    previous={key:os.environ.get(key) for key in values}
    try:
        os.environ.update(values)
        result=camera.start_video_stream_mode(**kwargs)
        return result
    finally:
        for key,value in previous.items():
            if value is None:os.environ.pop(key,None)
            else:os.environ[key]=value


class FallbackCamera:
    """Only the original final-image fallback's three-method camera contract."""
    @staticmethod
    def get_instance():return _FallbackInstance(create())

class _FallbackInstance:
    def __init__(self,camera):self.camera=camera
    def start_video_stream_mode(self):return start(self.camera)
    def read_video_stream(self,**kwargs):return self.camera.read_video_stream(**kwargs)
    def stop_video_stream_mode(self):return self.camera.stop_video_stream_mode()
