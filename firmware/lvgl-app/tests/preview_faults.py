"""Malformed and truncated preview input must fail boundedly and be reaped."""
import json
from pathlib import Path
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parent))
from transport import NativeHost
results=[]
for name,header,expected,code in [
    ('invalid-size',dict(width=240,height=180,bytes=1),'invalid_preview_size',5),
    ('truncated-pixels',dict(width=240,height=180,bytes=129600),'preview_timeout',4),
]:
    host=NativeHost(sys.argv[1],lambda *args:None)
    started=time.monotonic()
    try:
        host.send('preview',**header)
        event=host.events.get(timeout=5)
        assert event==dict(event='error',kind=expected),event
        assert host.child.wait(timeout=2)==code
        results.append(dict(name=name,boundedFailure=True,seconds=time.monotonic()-started,exitCode=code))
    finally:host.close()
    assert not host.reader.is_alive()
print(json.dumps(dict(passed=True,cases=results,childrenReaped=True,readerThreadsJoined=True)))
