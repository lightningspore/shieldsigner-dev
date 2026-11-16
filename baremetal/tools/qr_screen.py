# SPDX-License-Identifier: MIT
"""Host-controlled QR target display for demos and optical scan tests (PUBLIC data only).

  qr_screen.py serve [--display-x -1440 --display-w 1440 --display-h 900] [--no-window]
  qr_screen.py preset seed|address|psbt [--fps 6 --fragment 60]
  qr_screen.py text 'bc1q...'                      static QR
  qr_screen.py ur-psbt --hex 70736274ff... [--fragment 60 --fps 6]
  qr_screen.py frames a b c --fps 4                arbitrary animated frames
  qr_screen.py blank | status

`serve` opens the page in Safari on the second display and runs an HTTP control
server on 127.0.0.1:8766. The page (ShieldSigner website styling) selects the
demo presets itself: testnet SeedQR, testnet address and an animated testnet
PSBT (tools/demo_fixtures.py), with fps/fragment/size controls and a clean
presentation mode for filming. Keys: 1/2/3 presets, H hide controls, Space
pause, Left/Right step parts, +/- size, B blank. Tests import set_text /
set_frames / set_ur_psbt / set_preset / blank. UR parts use the upstream
SeedSigner ur2 encoder (dist sources), upper-cased like SeedSigner so the QR uses
alphanumeric mode. Never put private keys or seeds of value here.
"""

import argparse, io, json, subprocess, sys, threading, time, urllib.request
from pathlib import Path
import http.server

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
URL = 'http://127.0.0.1:8766'
STATE = {
    'version': 0,
    'frames': [],
    'fps': 0,
    'label': 'blank',
    'png': {},
    'size': 75,
    'y': 0,
    'preset': None,
    'meta': {},
}
LOCK = threading.Lock()
PAGE = Path(__file__).resolve().parent / 'qr_screen.html'


def _png(text):
    import segno

    # Black on white with the card supplying the quiet zone; scale up, CSS fits it.
    out = io.BytesIO()
    segno.make(text, error='l', boost_error=False).save(out, kind='png', scale=10, border=0)
    return out.getvalue()


def _short(text, n=18):
    return text if len(text) <= 2 * n + 1 else text[:n] + '…' + text[-n:]


def build_preset(name, fps=6, fragment=60):
    import demo_fixtures as F

    if name == 'seed':
        q = F.seedqr()
        return (
            [q],
            0,
            {
                'title': 'Testnet seed',
                'kind': 'SeedQR · static',
                'lines': [
                    ('Mnemonic', 'abandon ×11 · about'),
                    ('Fingerprint', F.summary()['fingerprint']),
                    ('Payload', _short(q)),
                ],
                'note': 'Public BIP39 test vector. Never fund it.',
            },
        )
    if name == 'address':
        a = F.address()
        return (
            [a],
            0,
            {
                'title': 'Testnet address',
                'kind': 'Native SegWit · static',
                'lines': [('Address', a), ('Path', "m/84'/1'/0'/0/0"), ('Seed', '73c5da0a')],
                'note': 'Scan to verify it belongs to the loaded seed.',
            },
        )
    if name == 'psbt':
        from urtypes.crypto import PSBT

        raw = F.psbt()
        s = F.summary()
        parts = ur_parts('crypto-psbt', PSBT(raw).to_cbor(), fragment)
        return (
            parts,
            fps,
            {
                'title': 'Testnet PSBT',
                'kind': 'Animated UR · %d parts' % len(parts),
                'lines': [
                    ('Send', '%s sats' % format(s['send_sats'], ',')),
                    ('To', _short(s['send_to'], 10)),
                    ('Change', '%s sats' % format(s['change_sats'], ',')),
                    ('Fee', '%s sats' % format(s['fee_sats'], ',')),
                ],
                'note': 'Set Network to Testnet on the device before scanning.',
                'animated': True,
            },
        )
    raise ValueError('unknown preset ' + name)


def _apply(frames, fps, label, size=None, y=None, preset=None, meta=None):
    frames = [str(f) for f in frames]
    pngs = {i: _png(f) for i, f in enumerate(frames)}  # pre-render: page timing is exact
    with LOCK:
        v = STATE['version'] + 1
        STATE.update(
            frames=frames,
            fps=float(fps),
            label=label,
            png={(v, i): p for i, p in pngs.items()},
            version=v,
            preset=preset,
            meta=meta or {},
        )
        if size is not None:
            STATE['size'] = float(size)
        if y is not None:
            STATE['y'] = float(y)
        return {'version': v, 'count': len(frames)}


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, body, ctype, code=200):
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj, code=200):
        self._send(json.dumps(obj).encode(), 'application/json', code)

    def do_GET(self):
        if self.path == '/state':
            with LOCK:
                self._json(
                    {
                        k: STATE[k]
                        for k in ('version', 'fps', 'label', 'size', 'y', 'preset', 'meta')
                    }
                    | {'count': len(STATE['frames'])}
                )
        elif self.path.startswith('/f/'):
            _, _, ver, name = self.path.split('/')
            i = int(name.split('.')[0])
            with LOCK:
                png = STATE['png'].get((int(ver), i))
            if png is None:
                self.send_error(404)
                return
            self._send(png, 'image/png')
        elif self.path.split('?')[0] in ('/', '/index.html'):
            self._send(PAGE.read_bytes(), 'text/html; charset=utf-8')
        else:
            self.send_error(404)

    def do_POST(self):
        req = json.loads(self.rfile.read(int(self.headers['Content-Length'])) or b'{}')
        try:
            if self.path == '/preset':
                name = req['name']
                fps = float(req.get('fps', 6))
                fragment = int(req.get('fragment', 60))
                if not 1 <= fps <= 30 or not 10 <= fragment <= 400:
                    raise ValueError('fps 1-30, fragment 10-400')
                frames, fps, meta = build_preset(name, fps, fragment)
                self._json(
                    _apply(
                        frames,
                        fps,
                        meta['title'],
                        req.get('size'),
                        req.get('y'),
                        name,
                        meta | {'fragment': fragment},
                    )
                )
            elif self.path == '/view':  # size/position only, no re-render
                with LOCK:
                    for k in ('size', 'y'):
                        if k in req:
                            STATE[k] = float(req[k])
                self._json({'ok': True})
            else:  # /set: arbitrary frames (optical tests)
                self._json(
                    _apply(
                        req.get('frames', []),
                        req.get('fps', 0),
                        str(req.get('label', '')),
                        req.get('size'),
                        req.get('y'),
                        None,
                        {'title': str(req.get('label', '')) or 'Custom', 'kind': 'Test pattern'},
                    )
                )
        except (KeyError, ValueError) as e:
            self._json({'error': str(e)}, 400)


def serve(a):
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 8766), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    if not a.no_window:
        subprocess.run(
            [
                'osascript',
                '-e',
                'tell application "Safari" to make new document with properties {URL:"%s/"}' % URL,
                '-e',
                'tell application "Safari" to set bounds of front window to {%d, 0, %d, %d}'
                % (a.display_x, a.display_x + a.display_w, a.display_h),
            ],
            check=False,
        )
    print('qr screen serving', URL, flush=True)
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        pass


SIZE = None
Y = None


def _req(path, obj):
    data = json.dumps(obj).encode()
    with urllib.request.urlopen(
        urllib.request.Request(URL + path, data=data, headers={'Content-Type': 'application/json'}),
        timeout=60,
    ) as r:
        return json.loads(r.read())


def _post(frames, fps=0, label=''):
    req = {'frames': frames, 'fps': fps, 'label': label}
    if SIZE is not None:
        req['size'] = SIZE
    if Y is not None:
        req['y'] = Y
    return _req('/set', req)


def set_text(text, label=None):
    return _post([text], 0, label or text[:60])


def set_frames(frames, fps=4, label='animated'):
    return _post(list(frames), fps, label)


def set_preset(name, fps=6, fragment=60):
    req = {'name': name, 'fps': fps, 'fragment': fragment}
    if SIZE is not None:
        req['size'] = SIZE
    return _req('/preset', req)


def blank():
    return _post([], 0, 'blank')


def ur_parts(ur_type, cbor, fragment=60, extra=0):
    sys.path.insert(0, str(ROOT / 'dist/firmware/sources/lvgl/application/src'))
    from seedsigner.helpers.ur2.ur_encoder import UREncoder
    from seedsigner.helpers.ur2.ur import UR

    enc = UREncoder(UR(ur_type, cbor), fragment, 0)
    count = enc.fountain_encoder.seq_len() + extra
    return [enc.next_part().upper() for _ in range(count)]


def set_ur_psbt(psbt_bytes, fragment=60, fps=6, extra=0):
    from urtypes.crypto import PSBT

    parts = ur_parts('crypto-psbt', PSBT(psbt_bytes).to_cbor(), fragment, extra)
    return set_frames(
        parts, fps, 'ur:crypto-psbt %d bytes fragment %d @%sfps' % (len(psbt_bytes), fragment, fps)
    ), parts


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    s = sub.add_parser('serve')
    s.add_argument('--display-x', type=int, default=-1440)
    s.add_argument('--display-w', type=int, default=1440)
    s.add_argument('--display-h', type=int, default=900)
    s.add_argument('--no-window', action='store_true')
    p = sub.add_parser('preset')
    p.add_argument('name', choices=['seed', 'address', 'psbt'])
    p.add_argument('--fps', type=float, default=6)
    p.add_argument('--fragment', type=int, default=60)
    t = sub.add_parser('text')
    t.add_argument('text')
    f = sub.add_parser('frames')
    f.add_argument('frames', nargs='+')
    f.add_argument('--fps', type=float, default=4)
    u = sub.add_parser('ur-psbt')
    u.add_argument('--hex', required=True)
    u.add_argument('--fragment', type=int, default=60)
    u.add_argument('--fps', type=float, default=6)
    u.add_argument('--extra', type=int, default=0)
    sub.add_parser('blank')
    sub.add_parser('status')
    ap.add_argument(
        '--y', type=float, help='vertical offset in %% of screen height (negative = up)'
    )
    ap.add_argument(
        '--size', type=float, help='QR height in %% of screen height (default keeps current)'
    )
    a = ap.parse_args()
    global SIZE, Y
    SIZE = a.size
    Y = a.y
    if a.cmd == 'serve':
        serve(a)
    elif a.cmd == 'preset':
        print(set_preset(a.name, a.fps, a.fragment))
    elif a.cmd == 'text':
        print(set_text(a.text))
    elif a.cmd == 'frames':
        print(set_frames(a.frames, a.fps))
    elif a.cmd == 'ur-psbt':
        r, parts = set_ur_psbt(bytes.fromhex(a.hex), a.fragment, a.fps, a.extra)
        print(r, len(parts), parts[0][:50])
    elif a.cmd == 'blank':
        print(blank())
    else:
        print(urllib.request.urlopen(URL + '/state').read().decode())


if __name__ == '__main__':
    main()
