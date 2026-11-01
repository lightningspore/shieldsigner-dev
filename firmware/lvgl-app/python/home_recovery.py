"""Reuse Home's original directional display-recovery callback without PIL setup."""
from types import SimpleNamespace

def monitor(runtime,screen_class,keys,renderer):
    # Render-only fixtures have no configured Renderer. Never initialize legacy
    # display hardware implicitly from a protocol-only screen invocation.
    if renderer is None:return lambda:None
    state=screen_class.__new__(screen_class)
    state.hw_inputs=SimpleNamespace(cur_input=None)
    state.renderer=renderer
    state._hold_key=None;state._hold_start_ms=None
    names={value:name for name,value in keys.items()}
    def poll():
        state.hw_inputs.cur_input=None if runtime.host.screensaver_active else names.get(runtime.current)
        return screen_class._run_callback(state)
    return poll
