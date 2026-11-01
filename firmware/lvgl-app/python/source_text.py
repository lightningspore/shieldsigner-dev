"""Extract adapter source without retaining an entire real file in linecache."""
import inspect,linecache,os

def getsource(subject):
    filename=inspect.getsourcefile(subject)
    try:return inspect.getsource(subject)
    finally:
        # Generated adapter sources are intentionally registered for later
        # introspection/tracebacks. Only real files can be reread on demand.
        if filename and os.path.isfile(filename):linecache.cache.pop(filename,None)
