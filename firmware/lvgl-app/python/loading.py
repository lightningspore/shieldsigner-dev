"""Replace only LoadingScreenThread's rendering lifecycle with native LVGL timers."""
import threading

def install(runtime,cls):
    names=('start','stop','is_alive','join')
    own={name:cls.__dict__.get(name) for name in names}
    def start(loader):
        if getattr(loader,'_lvgl_started',False):raise RuntimeError('Loading indicator already started')
        loader._lvgl_started=True;loader._lvgl_stopped=threading.Event()
        loader.keep_running=True
        try:loader._lvgl_token=runtime.show_loading(loader.text)
        except BaseException:
            loader.keep_running=False;loader._lvgl_stopped.set();raise
    def stop(loader):
        if not getattr(loader,'_lvgl_started',False):return
        if not loader._lvgl_stopped.is_set():
            try:runtime.hide_loading(loader._lvgl_token)
            finally:loader.keep_running=False;loader._lvgl_stopped.set()
    def is_alive(loader):return bool(getattr(loader,'_lvgl_started',False) and not loader._lvgl_stopped.is_set())
    def join(loader,timeout=None):
        if not getattr(loader,'_lvgl_started',False):raise RuntimeError('Cannot join before start')
        loader._lvgl_stopped.wait(timeout)
    for name,method in zip(names,(start,stop,is_alive,join)):setattr(cls,name,method)
    def uninstall():
        for name,method in own.items():
            if method is None:delattr(cls,name)
            else:setattr(cls,name,method)
    return uninstall
