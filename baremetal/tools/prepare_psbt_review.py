# SPDX-License-Identifier: MIT
"""Freeze original complete PSBT review policy and actual embit finalizer."""

import pyformat  # noqa: F401  (formats generated Python on write)
import ast, hashlib, io, json, subprocess, tarfile
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
path = source / 'src/seedsigner/models/psbt_parser.py'
raw = path.read_bytes()
assert (
    hashlib.sha256(raw).hexdigest()
    == json.loads((repo / 'firmware/lvgl-app/source-guards.json').read_text())[
        'models/psbt_parser.py'
    ]
)
tree = ast.parse(raw)
port = LazyPort(
    tree, 'seedsigner.models.psbt_parser', bindings={'time': ('seedsigner_port.psbt_clock', None)}
)
nodes = []
for node in tree.body:
    if isinstance(node, (ast.Import, ast.ImportFrom)):
        continue
    if isinstance(node, ast.Assign) and any(
        isinstance(t, ast.Name) and t.id == 'logger' for t in node.targets
    ):
        continue
    # Keep the exact already-frozen error identities shared by the strict loader.
    if isinstance(node, ast.ClassDef) and node.name in ('RejectCode', 'InvalidPSBTError'):
        continue
    nodes.append(port.visit(node))
text = (
    '# Copyright2021 SeedSigner; MIT, see ../LICENSE.SeedSigner\n# Generated original full policy; unported providers fail on use.\nfrom seedsigner_port.decode_platform import dependency as _dependency,FeatureUnavailable\nfrom seedsigner_port.psbt_errors import RejectCode,InvalidPSBTError\n'
    + ast.unparse(ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[])))
    + '\n'
)
out = root / 'app/seedsigner_port/psbt_parser.py'
out.write_text(text)
archive = root / '.tools/embit-0.8.0/source.tar.gz'
data = archive.read_bytes()
assert (
    hashlib.sha256(data).hexdigest()
    == '8bf4b10073c67400370ce523fb16f035fe759f6fdd987c579bdcc268d75ed770'
)
with tarfile.open(fileobj=io.BytesIO(data)) as tar:
    finalizer = tar.extractfile('embit-0.8.0/src/embit/finalizer.py').read()
final_out = root / 'app/embit/finalizer.py'
final_out.write_bytes(b'# Copyright2020 Stepan Snigirev; MIT, see ../LICENSE.embit\n' + finalizer)
receipt = {
    'application': lock,
    'source': 'models/psbt_parser.py',
    'sourceSha256': hashlib.sha256(raw).hexdigest(),
    'outputSha256': hashlib.sha256(out.read_bytes()).hexdigest(),
    'classes': [n.name for n in ast.parse(raw).body if isinstance(n, ast.ClassDef)],
    'reviewedChanges': [
        'Shared original RejectCode/InvalidPSBTError imported from frozen error leaf to preserve strict loader exception identity.',
        'Remove annotations; resolve actual optional imports lazily; preserve function-local bindings and original f-string values through common source port.',
        'Omit logger calls that could format private transaction/key data; unavailable providers propagate before broad fallback handlers.',
    ],
    'finalizer': {
        'provider': 'embit0.8.0 pinned sdist',
        'sourceSha256': hashlib.sha256(finalizer).hexdigest(),
        'outputSha256': hashlib.sha256(final_out.read_bytes()).hexdigest(),
        'changes': 'Original source unchanged apart from attribution header.',
    },
    'limits': [
        'Source availability is not complete signing/UI qualification.',
        'Descriptor provider is not frozen yet; descriptor-specific methods remain unavailable.',
        'Original timestamp comparison delegates to actual standard time through psbt_clock; absent native wall time fails explicitly, never uses uptime.',
        'No board access or production entropy/security claim.',
    ],
}
(root / 'app/psbt-review-provenance.json').write_text(json.dumps(receipt, indent=2) + '\n')
print('Prepared original full PSBTParser and embit finalizer')
