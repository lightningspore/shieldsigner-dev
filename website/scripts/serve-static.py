"""Local preview of the same generated files Caddy serves in production."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path

root=Path(__file__).resolve().parents[1]/'dist'
port=int(os.environ.get('SHIELDSIGNER_PORT','8030'))
print(f'Static preview: http://127.0.0.1:{port}',flush=True)
ThreadingHTTPServer(('127.0.0.1',port),partial(SimpleHTTPRequestHandler,directory=str(root))).serve_forever()
