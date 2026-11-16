# SPDX-License-Identifier: MIT
"""Prepare actual original storage/constants/options and shared View prerequisites."""

import pyformat  # noqa: F401  (formats generated Python on write)
import ast, hashlib, json, subprocess
from pathlib import Path
from source_port import Port

root = Path(__file__).resolve().parents[1]
repo = root.parent
source = repo / 'dist/firmware/sources/lvgl/application'
lock = json.loads((repo / 'firmware/lvgl-app/sources.lock.json').read_text())['application']
assert (
    subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=source, text=True).strip()
    == lock['commit']
)
receipt = {'application': lock, 'files': {}}


def emit(path, outname, names):
    raw = (source / 'src/seedsigner' / path).read_bytes()
    tree = ast.parse(raw)
    nodes = [
        n for n in tree.body if isinstance(n, (ast.ClassDef, ast.FunctionDef)) and n.name in names
    ]
    port = Port(tree, 'seedsigner.' + path[:-3].replace('/', '.'))
    nodes = [port.visit(n) for n in nodes]
    header = '# Copyright2021 SeedSigner; MIT, see ../LICENSE.SeedSigner\nfrom seedsigner_port.decode_platform import dependency as _dependency, FeatureUnavailable\n'
    out = root / 'app/seedsigner_port' / outname
    out.write_text(
        header
        + ast.unparse(ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[])))
        + '\n'
    )
    receipt['files'][outname] = {
        'source': path,
        'sourceSha256': hashlib.sha256(raw).hexdigest(),
        'outputSha256': hashlib.sha256(out.read_bytes()).hexdigest(),
        'names': names,
    }


emit('models/seed_storage.py', 'seed_storage.py', ['SeedStorage'])
emit('models/encryptedqr.py', 'encrypted_storage.py', ['EncryptedQRStorage'])
emit('models/singleton.py', 'singleton.py', ['Singleton', 'ConfigurableSingleton'])
p = root / 'app/seedsigner_port/singleton.py'
p.write_text(p.read_text().replace('cls.__new__(cls)', 'object.__new__(cls)'))
receipt['files']['singleton.py']['outputSha256'] = hashlib.sha256(p.read_bytes()).hexdigest()
emit(
    'gui/components.py',
    'gui_constants.py',
    ['GUIConstants', 'SeedSignerIconConstants', 'FontAwesomeIconConstants'],
)
# Options are exact original fields, with dataclass-generated methods made explicit.
p = source / 'src/seedsigner/gui/screens/screen.py'
raw = p.read_bytes()
tree = ast.parse(raw)
n = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'ButtonOption')
fields = [a for a in n.body if isinstance(a, ast.AnnAssign)]
names = [a.target.id for a in fields]
params = [
    name + ('=' + ast.unparse(a.value) if a.value is not None else '')
    for name, a in zip(names, fields)
]
body = (
    'def __init__(self,'
    + ','.join(params)
    + '):\n'
    + ''.join('    self.' + name + '=' + name + '\n' for name in names)
)
body += (
    'def __eq__(self,other):\n    return type(self) is type(other) and '
    + ' and '.join('self.' + f + '==other.' + f for f in names)
    + '\n'
)
n.decorator_list = []
n.body = [a for a in n.body if not isinstance(a, ast.AnnAssign)] + ast.parse(body).body
n2 = next(
    n
    for n in tree.body
    if isinstance(n, ast.ClassDef) and n.name == 'ButtonOptionWithoutTranslation'
)
n2.decorator_list = []
port = Port(tree, 'seedsigner.gui.screens.screen')
out = root / 'app/seedsigner_port/button_options.py'
out.write_text(
    '# Copyright2021 SeedSigner; MIT, see ../LICENSE.SeedSigner\n'
    + ast.unparse(
        ast.fix_missing_locations(ast.Module(body=[port.visit(n), port.visit(n2)], type_ignores=[]))
    )
    + '\n'
)
receipt['files']['button_options.py'] = {
    'source': 'gui/screens/screen.py',
    'sourceSha256': hashlib.sha256(raw).hexdigest(),
    'fields': names,
    'outputSha256': hashlib.sha256(out.read_bytes()).hexdigest(),
}
# Actual release-signing key-clear helpers; no signing/OS feature is implied.
p = source / 'src/seedsigner/views/resign_views.py'
raw = p.read_bytes()
tree = ast.parse(raw)
nodes = [
    n
    for n in tree.body
    if (
        isinstance(n, ast.FunctionDef)
        and n.name in ('clear_rekey_keys', 'clear_bip85_cache', 'clear_signing_keys')
    )
    or (
        isinstance(n, ast.Assign)
        and any(
            isinstance(t, ast.Name) and t.id in ('_SEEDKEEPER_KEYS_ATTR', '_BIP85_CACHE_ATTR')
            for t in n.targets
        )
    )
]
out = root / 'app/seedsigner_port/session_keys.py'
out.write_text(
    '# Copyright2021 SeedSigner; MIT, see ../LICENSE.SeedSigner\n'
    + ast.unparse(ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[])))
    + '\n'
)
receipt['files']['session_keys.py'] = {
    'source': 'views/resign_views.py',
    'sourceSha256': hashlib.sha256(raw).hexdigest(),
    'outputSha256': hashlib.sha256(out.read_bytes()).hexdigest(),
}
(root / 'app/app-core-provenance.json').write_text(json.dumps(receipt, indent=2) + '\n')
