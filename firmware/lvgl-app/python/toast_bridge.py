"""Original toast content/conditions, native top-layer rendering and dismissal."""
import itertools,time
from contracts import color
_tokens=itertools.count(1)

def install(runtime,module):
    overlay=module.ToastOverlay;manager=module.BaseToastOverlayManagerThread
    original_post=overlay.__post_init__;original_run=manager.run
    def post(toast):pass # Content dataclass stays intact; no PIL widgets/canvas.
    def run(loader):
        token=next(_tokens);shown=False;start=time.monotonic()
        try:
            while time.monotonic()-start<loader.activation_delay:
                if not loader.keep_running or loader.hw_inputs.has_any_input():return
                time.sleep(.1)
            while loader.keep_running and loader.should_keep_running():
                if loader.hw_inputs.has_any_input():break
                if not shown:
                    toast=loader.toast
                    runtime.host.send('toast',token=token,text=toast.label_text or '',icon=toast.icon_name or '',outline=color(toast.color),font=color(toast.font_color),duration_ms=max(0,int(loader.duration*1000)))
                    shown=True
                if time.monotonic()-start>loader.activation_delay+loader.duration:break
                time.sleep(.1)
        finally:
            if shown:runtime.host.send('toast_stop',token=token)
    overlay.__post_init__=post;manager.run=run
    def restore():overlay.__post_init__=original_post;manager.run=original_run
    return restore
