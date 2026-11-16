# SPDX-License-Identifier: MIT
"""Freeze original QR encoder classes, with lazy unported dependencies."""

import pyformat  # noqa: F401  (formats generated Python on write)
import ast, copy, hashlib, json, subprocess
from pathlib import Path
from view_source_port import LazyPort

root = Path(__file__).resolve().parents[1]
repo = root.parent
source = repo / 'dist/firmware/sources/lvgl/application'
lock = json.loads((repo / 'firmware/lvgl-app/sources.lock.json').read_text())['application']
assert (
    subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=source, text=True).strip()
    == lock['commit']
)
raw = (source / 'src/seedsigner/models/encode_qr.py').read_bytes()
guards = json.loads((repo / 'firmware/lvgl-app/source-guards.json').read_text())
assert hashlib.sha256(raw).hexdigest() == guards['models/encode_qr.py']
tree = ast.parse(raw)
originals = {n.name: copy.deepcopy(n) for n in tree.body if isinstance(n, ast.ClassDef)}


def fields(node):
    out = {}
    for base in node.bases:
        if isinstance(base, ast.Name) and base.id in originals:
            out.update(fields(originals[base.id]))
    out.update({a.target.id: a.value for a in node.body if isinstance(a, ast.AnnAssign)})
    return out


port = LazyPort(tree, 'seedsigner.models.encode_qr', classes=originals)
nodes = []
for node in tree.body:
    if not isinstance(node, ast.ClassDef):
        continue
    if any(ast.unparse(d) == 'dataclass' for d in node.decorator_list):
        f = fields(node)
        args = ','.join(
            name + ('=' + ast.unparse(value) if value is not None else '')
            for name, value in f.items()
        )
        init = (
            'def __init__(self'
            + (',' + args if args else '')
            + '):\n'
            + ''.join('    self.' + name + '=' + name + '\n' for name in f)
            + '    self.__post_init__()\n'
        )
        node.decorator_list = []
        node.body = [x for x in node.body if not isinstance(x, ast.AnnAssign)] + ast.parse(
            init
        ).body
    if node.name == 'StaticXpubQrEncoder':
        # MicroPython resolves a diamond depth-first instead of CPython C3.
        # Materialize the exact BaseStatic methods otherwise shadowed by the
        # BaseXpub -> BaseQr abstract methods. No encoder algorithm changes.
        for method in originals['BaseStaticQrEncoder'].body:
            if isinstance(method, ast.FunctionDef) and method.name in (
                'cur_part',
                'seq_len',
                'is_complete',
            ):
                node.body.append(copy.deepcopy(method))
    if node.name == 'CompactSeedQrEncoder':

        class Strings(ast.NodeTransformer):
            def visit_Call(self, n):
                n = self.generic_visit(n)
                if isinstance(n.func, ast.Attribute) and n.func.attr == 'zfill':
                    return ast.Call(
                        func=ast.Attribute(
                            value=ast.Call(
                                func=ast.Name(id='_dependency', ctx=ast.Load()),
                                args=[
                                    ast.Constant('seedsigner_port.qr_strings'),
                                    ast.Constant(None),
                                ],
                                keywords=[],
                            ),
                            attr='zfill',
                            ctx=ast.Load(),
                        ),
                        args=[n.func.value] + n.args,
                        keywords=n.keywords,
                    )
                return n

        node = Strings().visit(node)
    node = port.visit(node)
    nodes.append(
        ast.FunctionDef(
            name='_make_' + node.name,
            args=ast.arguments(posonlyargs=[], args=[], kwonlyargs=[], kw_defaults=[], defaults=[]),
            body=[node, ast.Return(value=ast.Name(id=node.name, ctx=ast.Load()))],
            decorator_list=[],
        )
    )
text = (
    '# Copyright2021 SeedSigner; MIT, see ../LICENSE.SeedSigner\n# Generated original encoders; optional providers fail on use.\nfrom seedsigner_port.decode_platform import dependency as _dependency,FeatureUnavailable\n'
    + ast.unparse(ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[])))
    + '\n'
)
text += (
    '_FACTORIES={'
    + ','.join(repr(n) + ':_make_' + n for n in originals)
    + '}\n_CACHE={}\ndef _resolve(name):\n    if name not in _CACHE:\n        if name not in _FACTORIES:raise AttributeError(name)\n        _CACHE[name]=_FACTORIES[name]()\n    return _CACHE[name]\ndef __getattr__(name):return _resolve(name)\n'
)
out = root / 'app/seedsigner_port/encode_qr.py'
out.write_text(text)
(root / 'app/encode-qr-provenance.json').write_text(
    json.dumps(
        {
            'application': lock,
            'sourceSha256': hashlib.sha256(raw).hexdigest(),
            'outputSha256': hashlib.sha256(out.read_bytes()).hexdigest(),
            'classes': list(originals),
            'reviewedChanges': [
                'Dataclass constructors are explicit; optional imports resolve lazily.',
                'Compact encoder uses CPython-equivalent zfill helper.',
                'StaticXpub materializes exact BaseStatic cur_part/seq_len/is_complete to preserve CPython C3 resolution on MicroPython diamonds.',
            ],
        },
        indent=2,
    )
    + '\n'
)
print('Prepared', len(originals), 'original QR encoder classes')
