# SPDX-License-Identifier: MIT
"""Static route/dependency audit of the frozen native app Views.

For every generated View factory, resolve each literal ``_dependency(module, attr)``
through the real ``decode_platform`` alias table and classify it against the
frozen manifest and the native C modules of the UI build. A dependency outside
both raises FeatureUnavailable on device when that code path runs. This is a
static inventory only; it does not prove any route works on hardware.

Usage: uv run --python 3.13 python baremetal/tools/audit_routes.py [--json]
"""

import ast, builtins, json, re, sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
app = root / 'app'
VIEW_FILES = (
    'view_core.py',
    'view_scan.py',
    'view_seed.py',
    'view_psbt.py',
    'view_settings.py',
    'view_splash.py',
    'view_development.py',
    'camera_entropy_views.py',
)


def frozen_modules():
    text = (root / 'micropython/manifest.py').read_text()
    files = {a or b for a, b in re.findall(r'"([\w/]+\.py)"|\'([\w/]+\.py)\'', text)}
    return {f[:-3].replace('/', '.').removesuffix('.__init__'): app / f for f in files}


def native_modules():
    # Source of truth: registered C modules plus enabled MicroPython builtins.
    path = root / 'build/micropython-ui/genhdr/moduledefs.h'
    if path.exists():
        return set(re.findall(r'MP_QSTR_(\w+)', path.read_text()))
    names = set()
    for c in (root / 'micropython').glob('*.c'):
        names |= set(re.findall(r'MP_REGISTER_MODULE\(MP_QSTR_(\w+)', c.read_text()))
    return names | {
        'array',
        'binascii',
        'builtins',
        'collections',
        'gc',
        'io',
        'json',
        'math',
        'micropython',
        'random',
        'struct',
        'sys',
    }


def resolver():
    sys.path.insert(0, str(app))
    from seedsigner_port import decode_platform

    def resolve(module, attr):
        seen = []
        real = builtins.__import__

        def capture(name, *a, **k):
            if not seen:
                seen.append(name)
                raise ImportError(name)
            return real(name, *a, **k)

        builtins.__import__ = capture
        try:
            try:
                decode_platform.dependency(module, attr)
            except Exception:
                pass
        finally:
            builtins.__import__ = real
        return seen[0] if seen else module

    # attribute remaps are part of the table; recover them by source inspection
    special = ast.literal_eval(
        re.search(
            r'special=(\{.*?\})\n', (app / 'seedsigner_port/decode_platform.py').read_text(), re.S
        ).group(1)
    )

    def full(module, attr):
        if (module, attr) in special:
            module, attr = special[(module, attr)]
            return module, attr
        return resolve(module, attr), attr

    return full


_names_cache = {}


def module_names(path):
    if path not in _names_cache:
        tree = ast.parse(path.read_text())
        names = set()
        dynamic = False
        factories = set()
        for n in tree.body:
            if isinstance(n, (ast.FunctionDef, ast.ClassDef)):
                names.add(n.name)
                dynamic |= n.name == '__getattr__'
            elif isinstance(n, ast.Assign):
                for t in n.targets:
                    for x in ast.walk(t):
                        if isinstance(x, ast.Name):
                            names.add(x.id)
                if any(
                    isinstance(t, ast.Name) and t.id == '_FACTORIES' for t in n.targets
                ) and isinstance(n.value, ast.Dict):
                    factories = {k.value for k in n.value.keys}
            elif isinstance(n, (ast.Import, ast.ImportFrom)):
                names |= {(a.asname or a.name).split('.')[0] for a in n.names}
            elif isinstance(n, (ast.If, ast.Try)):
                for x in ast.walk(n):
                    if isinstance(x, (ast.FunctionDef, ast.ClassDef)):
                        names.add(x.name)
                    elif isinstance(x, ast.Name) and isinstance(x.ctx, ast.Store):
                        names.add(x.id)
                    elif isinstance(x, (ast.Import, ast.ImportFrom)):
                        names |= {(a.asname or a.name).split('.')[0] for a in x.names}
        _names_cache[path] = (names, dynamic, factories)
    return _names_cache[path]


def classify(module, attr, frozen, native, full):
    target, tattr = full(module, attr)
    if target in frozen:
        if tattr is None:
            return 'ok', target
        names, dynamic, factories = module_names(frozen[target])
        if tattr in names or target + '.' + tattr in frozen:
            return 'ok', target
        if dynamic and (not factories or tattr in factories):
            return 'ok', target
        return 'missing-attr', target + '.' + tattr
    if target.split('.')[0] in native and target.split('.')[0] not in frozen:
        return 'native', target
    return 'unavailable', target + ('.' + tattr if tattr else '')


def audit():
    frozen = frozen_modules()
    native = native_modules()
    full = resolver()
    views = {}
    for fname in VIEW_FILES:
        path = app / 'seedsigner_port' / fname
        tree = ast.parse(path.read_text())
        _, _, factories = module_names(path)
        supported = None
        for n in tree.body:
            if isinstance(n, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == '_SUPPORTED' for t in n.targets
            ):
                supported = set(ast.literal_eval(n.value))
        for fn in tree.body:
            if not (isinstance(fn, ast.FunctionDef) and fn.name.startswith('_make_')):
                continue
            view = fn.name[6:]
            deps = {'unavailable': set(), 'missing-attr': set(), 'bad-route': set()}
            routes = set()
            for c in ast.walk(fn):
                if not isinstance(c, ast.Call):
                    continue
                name = getattr(c.func, 'id', '')
                lits = [a.value if isinstance(a, ast.Constant) else ... for a in c.args]
                if name == '_dependency' and lits and isinstance(lits[0], str):
                    attr = lits[1] if len(lits) > 1 and isinstance(lits[1], str) else None
                    if len(lits) > 1 and lits[1] is ...:
                        continue
                    kind, what = classify(lits[0], attr, frozen, native, full)
                    if kind in deps:
                        deps[kind].add(what)
                elif name == '_resolve' and lits and isinstance(lits[0], str):
                    routes.add(lits[0])
                    if lits[0] not in factories:
                        deps['bad-route'].add(lits[0])
            excluded = supported is not None and view not in supported
            views[f'{fname}:{view}'] = {
                'routes': sorted(routes),
                'excluded': excluded,
                **{k: sorted(v) for k, v in deps.items()},
            }
    return views


def status(v):
    if v['excluded']:
        return 'deliberately excluded (refused explicitly)'
    if v['bad-route'] or v['missing-attr']:
        return 'FAILING (static)'
    if v['unavailable']:
        return 'partial: some paths raise FeatureUnavailable'
    return 'dependencies resolve; device-untested'


if __name__ == '__main__':
    views = audit()
    if '--json' in sys.argv:
        print(json.dumps(views, indent=1))
        sys.exit()
    counts = {}
    for k, v in views.items():
        s = status(v)
        counts[s] = counts.get(s, 0) + 1
        extra = '; '.join(
            f'{kk}: ' + ', '.join(v[kk])
            for kk in ('bad-route', 'missing-attr', 'unavailable')
            if v[kk]
        )
        print(f'| `{k}` | {s} | {extra} |')
    print(counts, file=sys.stderr)
