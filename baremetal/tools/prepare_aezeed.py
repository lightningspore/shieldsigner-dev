# SPDX-License-Identifier: MIT
"""Retain complete locked Aezeed module; real unsupported crypto stays explicit."""

import pyformat  # noqa: F401  (formats generated Python on write)
import ast, hashlib, json, subprocess
from pathlib import Path
from source_records import Records

root = Path(__file__).resolve().parents[1]
repo = root.parent
source = repo / 'dist/firmware/sources/lvgl/application'
lock = json.loads((repo / 'firmware/lvgl-app/sources.lock.json').read_text())['application']
assert (
    subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=source, text=True).strip()
    == lock['commit']
)
p = source / 'src/seedsigner/models/aezeed.py'
raw = p.read_bytes()
sha = hashlib.sha256(raw).hexdigest()
# Additional source boundary not in the older central guards.
assert sha == '895f7b283216114cdf7e8cd8b08df8f87b2df0532e3b687a87985f7966165eef'


class Port(ast.NodeTransformer):
    def visit_ImportFrom(self, n):
        return None if n.module in ('__future__', 'typing', 'dataclasses') else n

    def visit_FunctionDef(self, n):
        n.returns = None
        for a in n.args.args + n.args.kwonlyargs + n.args.posonlyargs:
            a.annotation = None
        return self.generic_visit(n)

    def visit_AnnAssign(self, n):
        return (
            ast.copy_location(ast.Assign(targets=[n.target], value=self.visit(n.value)), n)
            if n.value is not None
            else None
        )

    def visit_Call(self, n):
        n = self.generic_visit(n)
        if (
            isinstance(n.func, ast.Attribute)
            and isinstance(n.func.value, ast.Name)
            and n.func.value.id == 'hashlib'
            and n.func.attr in ('scrypt', 'blake2b')
        ):
            n.func = ast.Call(
                func=ast.Name(id='_dependency', ctx=ast.Load()),
                args=[ast.Constant('hashlib'), ast.Constant(n.func.attr)],
                keywords=[],
            )
        return n

    def visit_Try(self, n):
        n = self.generic_visit(n)
        if any(
            h.type is None
            or (isinstance(h.type, ast.Name) and h.type.id in ('Exception', 'BaseException'))
            for h in n.handlers
        ):
            n.handlers.insert(
                0,
                ast.ExceptHandler(
                    type=ast.Name(id='FeatureUnavailable', ctx=ast.Load()),
                    name=None,
                    body=[ast.Raise()],
                ),
            )
        return n


header = '# Copyright2021 SeedSigner; MIT, see ../LICENSE.SeedSigner\nfrom collections import namedtuple as _namedtuple\nfrom seedsigner_port.decode_platform import dependency as _dependency, FeatureUnavailable\n'
tree = Port().visit(Records().visit(ast.parse(raw)))
out = root / 'app/seedsigner_port/aezeed.py'
out.write_text(header + ast.unparse(ast.fix_missing_locations(tree)) + '\n')
(root / 'app/aezeed-provenance.json').write_text(
    json.dumps(
        {
            'application': lock,
            'sourceSha256': sha,
            'outputSha256': hashlib.sha256(out.read_bytes()).hexdigest(),
            'scope': 'Whole original module; checksum supported, actual Blake2B/scrypt providers required for decryption',
            'transformations': [
                'Remove annotations',
                'Immutable tuple-backed frozen record representation',
                'Unavailable Blake2B/scrypt functions resolve explicitly; no substitute crypto',
            ],
        },
        indent=2,
    )
    + '\n'
)
