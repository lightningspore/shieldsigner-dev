# SPDX-License-Identifier: MIT
"""Freeze original PSBT Views and existing native renderer contracts lazily."""

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
path = source / 'src/seedsigner/views/psbt_views.py'
raw = path.read_bytes()
assert raw == subprocess.check_output(
    ['git', 'show', lock['commit'] + ':src/seedsigner/views/psbt_views.py'], cwd=source
)
tree = ast.parse(raw)
classes = {n.name: copy.deepcopy(n) for n in tree.body if isinstance(n, ast.ClassDef)}


class Port(LazyPort):
    def visit_Name(self, n):
        if isinstance(n.ctx, ast.Load) and n.id in ('REJECT_PRESENTATION', 'REFUSAL_VIEWS'):
            return ast.copy_location(
                ast.Call(
                    func=ast.Name(
                        id='_presentations' if n.id == 'REJECT_PRESENTATION' else '_refusal_views',
                        ctx=ast.Load(),
                    ),
                    args=[],
                    keywords=[],
                ),
                n,
            )
        return super().visit_Name(n)

    def visit_Subscript(self, n):
        if ast.unparse(n) == 'globals()[p.destination_name]':
            return ast.copy_location(
                ast.Call(
                    func=ast.Name(id='_destination_view', ctx=ast.Load()),
                    args=[self.visit(n.slice)],
                    keywords=[],
                ),
                n,
            )
        return self.generic_visit(n)


port = Port(
    tree,
    'seedsigner.views.psbt_views',
    classes=classes,
    bindings={
        'Destination': ('seedsigner_port.navigation', 'Destination'),
        'time': ('seedsigner_port.psbt_clock', None),
    },
)
nodes = []
for n in tree.body:
    if isinstance(n, (ast.Import, ast.ImportFrom)):
        continue
    if isinstance(n, ast.Assign) and any(
        isinstance(t, ast.Name) and t.id in ('logger', 'REFUSAL_VIEWS') for t in n.targets
    ):
        continue
    if isinstance(n, ast.Assign) and any(
        isinstance(t, ast.Name) and t.id == 'REJECT_PRESENTATION' for t in n.targets
    ):
        value = port.visit(n.value)
        nodes.append(
            ast.FunctionDef(
                name='_build_presentations',
                args=ast.arguments(
                    posonlyargs=[], args=[], kwonlyargs=[], kw_defaults=[], defaults=[]
                ),
                body=[ast.Return(value=value)],
                decorator_list=[],
            )
        )
        continue
    if isinstance(n, ast.ClassDef):
        if any(ast.unparse(d) == 'dataclass' for d in n.decorator_list):
            fields = {a.target.id: a.value for a in n.body if isinstance(a, ast.AnnAssign)}
            assert n.name == 'RejectPresentation'
            init = (
                'def __init__(self,'
                + ','.join(k + '=' + ast.unparse(v) for k, v in fields.items())
                + '):\n'
                + ''.join(' self.' + k + '=' + k + '\n' for k in fields)
            )
            n.decorator_list = []
            n.body = [a for a in n.body if not isinstance(a, ast.AnnAssign)] + ast.parse(init).body
        n = port.visit(n)
        nodes.append(
            ast.FunctionDef(
                name='_make_' + n.name,
                args=ast.arguments(
                    posonlyargs=[], args=[], kwonlyargs=[], kw_defaults=[], defaults=[]
                ),
                body=[n, ast.Return(value=ast.Name(id=n.name, ctx=ast.Load()))],
                decorator_list=[],
            )
        )
    else:
        nodes.append(port.visit(n))
refusals = [
    name
    for name, node in classes.items()
    if any(isinstance(b, ast.Name) and b.id == 'PSBTRefusalView' for b in node.bases)
]
header = '# Copyright2021 SeedSigner; MIT, see ../LICENSE.SeedSigner\n# Generated original Views; optional providers remain explicit.\nfrom seedsigner_port.decode_platform import dependency as _dependency,FeatureUnavailable\n'
footer = (
    '\n_FACTORIES={'
    + ','.join(repr(n) + ':_make_' + n for n in classes)
    + '}\n_CACHE={}\n_PRESENTATIONS=None\n_REFUSALS=None\n'
)
footer += '''def _resolve(name):
 if name not in _CACHE:
  if name not in _FACTORIES:raise AttributeError(name)
  _CACHE[name]=_FACTORIES[name]()
 return _CACHE[name]
def _destination_view(name):
 return _resolve(name) if name in _FACTORIES else _dependency('seedsigner.views.view',name)
def _presentations():
 global _PRESENTATIONS
 if _PRESENTATIONS is None:_PRESENTATIONS=_build_presentations()
 return _PRESENTATIONS
def _refusal_views():
 global _REFUSALS
 if _REFUSALS is None:
  classes=[_resolve(name) for name in REFUSAL_NAMES]
  _REFUSALS={cls.code:cls for cls in classes}
 return _REFUSALS
def __getattr__(name):
 if name=='REJECT_PRESENTATION':return _presentations()
 if name=='REFUSAL_VIEWS':return _refusal_views()
 return _resolve(name)
'''.replace('REFUSAL_NAMES', repr(refusals))
out = root / 'app/seedsigner_port/view_psbt.py'
out.write_text(
    header
    + ast.unparse(ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[])))
    + '\n'
    + footer
)
receipt = {
    'application': lock,
    'sourceSha256': hashlib.sha256(raw).hexdigest(),
    'outputSha256': hashlib.sha256(out.read_bytes()).hexdigest(),
    'classes': list(classes),
    'refusalSubclasses': refusals,
    'changes': [
        'Lazy original class factories and import/annotation/formatting boundaries through common source port.',
        'RejectPresentation gets explicit original-field constructor, without fictitious post_init.',
        'Original presentation table and refusal subclasses resolved lazily; frozen source subclass list replaces unavailable subclass introspection.',
        'Original named refusal destination globals lookup resolves the same original lazy class.',
        'Date calls use explicit actual-time boundary; no uptime/calendar substitute.',
        'Payload logger calls omitted; actual missing providers propagate explicitly.',
    ],
}
# Reuse existing reviewed Linux native contracts/formatting source, adapting imports only.
for source_name, target in [
    ('formatting.py', 'psbt_formatting.py'),
    ('psbt_contracts.py', 'psbt_contracts.py'),
]:
    path = repo / 'firmware/lvgl-app/python' / source_name
    data = path.read_bytes()
    t = ast.parse(data)
    bindings = {}
    if source_name == 'psbt_contracts.py':
        bindings = {
            name: ('seedsigner_port.psbt_formatting', name)
            for name in ('btc_amount_from_sats', 'format_btc', 'format_sats')
        }
        bindings['ngettext'] = ('seedsigner_port.psbt_screens', 'ngettext')
    adapter = LazyPort(t, 'native.' + source_name[:-3], bindings=bindings)
    adapted = []
    for n in t.body:
        if isinstance(n, (ast.Import, ast.ImportFrom)):
            continue
        n = adapter.visit(n)
        if n is not None:
            adapted.append(n)
    text = (
        '# SPDX-License-Identifier: MIT\n# Copyright (c) 2021 SeedSigner; MIT, see ../LICENSE.SeedSigner.\n# Formatting adapted from kdmukAI-bot/seedsigner fd9ba8fc766f715668bc37fbb5485499def9e52f.\n# Source-backed native contract; upstream source/notice pinned in provenance.\nfrom seedsigner_port.decode_platform import dependency as _dependency,FeatureUnavailable\n'
        + ast.unparse(ast.fix_missing_locations(ast.Module(body=adapted, type_ignores=[])))
        + '\n'
    )
    if source_name == 'psbt_contracts.py':
        text = text.replace("data.decode('utf-8', errors='strict')", "data.decode('utf-8')")
    p = root / 'app/seedsigner_port' / target
    p.write_text(text)
    receipt[target] = {
        'source': str(path.relative_to(repo)),
        'sourceSha256': hashlib.sha256(data).hexdigest(),
        'outputSha256': hashlib.sha256(p.read_bytes()).hexdigest(),
        'changes': ['Actual lazy native settings/localization/formatter imports.']
        + (
            [
                'Strict UTF8 decode uses default strict native spelling; native Unicode checks enabled.'
            ]
            if source_name == 'psbt_contracts.py'
            else []
        ),
    }
# Original fields required by the PSBT-specific native screen config layer.
fields = {}
path = source / 'src/seedsigner/gui/screens/psbt_screens.py'
raw_screens = path.read_bytes()
for node in ast.parse(raw_screens).body:
    if isinstance(node, ast.ClassDef):
        values = {}
        for a in node.body:
            if isinstance(a, ast.AnnAssign) and a.value is not None:
                values[a.target.id] = ast.literal_eval(a.value)
        fields[node.name] = values
p = root / 'app/seedsigner_port/psbt_screen_defaults.py'
p.write_text(
    '# Copyright2021 SeedSigner; MIT, see ../LICENSE.SeedSigner\n# Generated original PSBT field defaults.\nDEFAULTS='
    + repr(fields)
    + '\n'
)
receipt['screens'] = {
    'sourceSha256': hashlib.sha256(raw_screens).hexdigest(),
    'outputSha256': hashlib.sha256(p.read_bytes()).hexdigest(),
    'classes': list(fields),
}
(root / 'app/psbt-views-provenance.json').write_text(json.dumps(receipt, indent=2) + '\n')
print('Prepared', len(classes), 'original PSBT Views and', len(fields), 'native screen contracts')
