"""Wipe interruption boundary around the original Controller's wipe policy.

Install only alongside native toasts and Renderer. Wiping remains original code;
this adapter unwinds an active View and restarts the native process, removing
all old widget/QR text before the Controller returns to Home.
"""
from source_text import getsource as adapter_source
import threading
from transport import NativeHost
class WipeInterrupted(Exception):pass


def quiet_wipe_route(source,namespace):
    """Add only an expected-wipe catch before the original broad error handler."""
    import ast,copy,textwrap
    tree=ast.parse(textwrap.dedent(source));matches=0
    for node in ast.walk(tree):
        if not isinstance(node,ast.Try):continue
        for index,handler in enumerate(node.handlers):
            if isinstance(handler.type,ast.Name) and handler.type.id=='BaseException':
                if handler.name!='e' or not handler.body or ast.unparse(handler.body[-1])!='next_destination = self.handle_exception(e)':raise ValueError('Unexpected Controller exception route')
                route=ast.ExceptHandler(type=ast.Name(id='_LVGLWipeInterrupted',ctx=ast.Load()),name='e',body=[copy.deepcopy(handler.body[-1])])
                node.handlers.insert(index,route);matches+=1;break
    if matches!=1 or len(tree.body)!=1 or not isinstance(tree.body[0],ast.FunctionDef) or tree.body[0].name!='start':raise ValueError('Unexpected Controller.start shape')
    tree.body[0].decorator_list=[];ast.fix_missing_locations(tree)
    local={};exec(compile(tree,'<guarded LVGL wipe route>','exec'),namespace,local)
    return local['start']

def install_start_route(controller_class):
    import hashlib,inspect,json
    from pathlib import Path
    path=Path(inspect.getfile(controller_class)).resolve()
    manifest=Path(__file__).parent/'source-guards.json'
    if not manifest.exists():manifest=Path(__file__).parent.parent/'source-guards.json'
    guards=json.loads(manifest.read_text())
    if hashlib.sha256(path.read_bytes()).hexdigest()!=guards['controller.py']:raise ValueError('Unreviewed Controller wipe route')
    original_start=controller_class.start
    namespace=original_start.__globals__
    if '_LVGLWipeInterrupted' in namespace:raise ValueError('LVGL wipe route already installed')
    namespace['_LVGLWipeInterrupted']=WipeInterrupted
    try:replacement=quiet_wipe_route(adapter_source(original_start),namespace)
    except BaseException:
        del namespace['_LVGLWipeInterrupted'];raise
    controller_class.start=replacement
    def restore():
        controller_class.start=original_start
        del namespace['_LVGLWipeInterrupted']
    return restore

def install(runtime,controller_class):
    restore_start=install_start_route(controller_class)
    original_wipe=controller_class.handle_wipe_timeout
    original_error=controller_class.handle_exception
    event=threading.Event();delivered=[False]
    previous=runtime.lifecycle_check
    def wipe(controller):
        original_wipe(controller)
        event.set()
    def check():
        if previous is not None:previous()
        if event.is_set() and not delivered[0]:
            delivered[0]=True
            raise WipeInterrupted('Inactivity wipe interrupted active LVGL flow')
    def handle(controller,error):
        if not isinstance(error,WipeInterrupted):return original_error(controller,error)
        # Camera/QR finally blocks have run before Controller catches this.
        old=runtime.host
        old.close()
        runtime.host=NativeHost(runtime.binary,runtime.pixel_sink,**({'width':runtime.width,'height':runtime.height} if hasattr(runtime,'width') else {}))
        if hasattr(runtime,"configure_screensaver"):runtime.configure_screensaver(runtime.screensaver_timeout_ms)
        consume=getattr(runtime,'consume_input_override',None)
        if consume is not None:consume()
        runtime.reset_input();event.clear();delivered[0]=False
        from seedsigner.views.view import Destination,MainMenuView
        return Destination(MainMenuView,clear_history=True)
    runtime.lifecycle_check=check
    controller_class.handle_wipe_timeout=wipe;controller_class.handle_exception=handle
    def restore():
        restore_start()
        runtime.lifecycle_check=previous
        controller_class.handle_wipe_timeout=original_wipe;controller_class.handle_exception=original_error
    return restore
