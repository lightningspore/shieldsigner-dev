"""Small process-local diagnostic overrides without importing a mock framework."""
from contextlib import contextmanager
@contextmanager
def attribute(target,name,value):
    namespace=vars(target);owned=name in namespace
    original=namespace[name] if owned else getattr(target,name)
    setattr(target,name,value)
    try:yield value
    finally:
        if owned:setattr(target,name,original)
        else:delattr(target,name)
