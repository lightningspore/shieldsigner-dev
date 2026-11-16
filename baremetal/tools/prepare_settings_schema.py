# SPDX-License-Identifier: MIT
"""Prepare actual app settings schema without Linux/file discovery dependencies."""

import pyformat  # noqa: F401  (formats generated Python on write)
import ast
import hashlib
import json
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parents[1]
repo = root.parent
source = repo / 'dist/firmware/sources/lvgl/application'
lock = json.loads((repo / 'firmware/lvgl-app/sources.lock.json').read_text())['application']
assert (
    subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=source, text=True).strip()
    == lock['commit']
)
p = source / 'src/seedsigner/models/settings_definition.py'
raw = p.read_bytes()
tree = ast.parse(raw)
l10n = source / 'src/seedsigner/helpers/l10n.py'
mark = ast.parse(l10n.read_text()).body[0]
mark.name = '_mft'


class Types(ast.NodeTransformer):
    def visit_FunctionDef(self, node):
        node.returns = None
        for arg in [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]:
            arg.annotation = None
        return self.generic_visit(node)

    def visit_AnnAssign(self, node):
        return (
            ast.copy_location(ast.Assign(targets=[node.target], value=node.value), node)
            if node.value is not None
            else None
        )


nodes = [mark, ast.parse('USING_MOCK_GPIO = False').body[0]]
classes = {}
for name in ('SettingsConstants', 'SettingsEntry', 'SettingsDefinition'):
    node = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == name)
    classes[name] = hashlib.sha256(ast.get_source_segment(raw.decode(), node).encode()).hexdigest()
    if name == 'SettingsConstants':
        old = next(
            n
            for n in node.body
            if isinstance(n, ast.FunctionDef) and n.name == 'get_detected_languages'
        )
        # Only English assets are frozen. No os/pathlib probing or invented files.
        replacement = ast.parse(
            '@classmethod\ndef get_detected_languages(cls):\n return [(cls.LOCALE__ENGLISH,cls.ALL_LOCALES[cls.LOCALE__ENGLISH])]'
        ).body[0]
        node.body[node.body.index(old)] = replacement
    if name == 'SettingsEntry':
        fields = [n for n in node.body if isinstance(n, ast.AnnAssign)]
        args = ['self'] + [
            n.target.id + ('=' + ast.unparse(n.value) if n.value is not None else '')
            for n in fields
        ]
        constructor = (
            'def __init__('
            + ','.join(args)
            + '):\n'
            + ''.join(' self.' + n.target.id + '=' + n.target.id + '\n' for n in fields)
            + ' self.__post_init__()'
        )
        equal = (
            'def __eq__(self,other):\n if type(self) is not type(other):return NotImplemented\n return '
            + ' and '.join('self.' + n.target.id + '==other.' + n.target.id for n in fields)
        )
        representation = (
            'def __repr__(self):\n return "SettingsEntry("+'
            + '+", "+'.join('"' + n.target.id + '="+repr(self.' + n.target.id + ')' for n in fields)
            + '+")"'
        )
        node.body = [n for n in node.body if n not in fields]
        node.body[1:1] = ast.parse(constructor + '\n' + equal + '\n' + representation).body
        node.decorator_list = []
    nodes.append(Types().visit(node))
settings_path = source / 'src/seedsigner/models/settings.py'
settings_raw = settings_path.read_bytes()
settings_tree = ast.parse(settings_raw)
invalid = next(
    n
    for n in settings_tree.body
    if isinstance(n, ast.ClassDef) and n.name == 'InvalidSettingsQRData'
)
settings = next(
    n for n in settings_tree.body if isinstance(n, ast.ClassDef) and n.name == 'Settings'
)
parser = next(
    n for n in settings.body if isinstance(n, ast.FunctionDef) and n.name == 'parse_settingsqr'
)


class Quiet(ast.NodeTransformer):
    def visit_Expr(self, node):
        if (
            isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Attribute)
            and isinstance(node.value.func.value, ast.Name)
            and node.value.func.value.id == 'logger'
        ):
            return ast.copy_location(ast.Pass(), node)
        return self.generic_visit(node)


float_helper = ast.parse(
    'def _settings_float(value):\n try:\n  convert=float\n except NameError:\n  raise NotImplementedError("Decimal settings require the native-ui double runtime")\n return convert(value)'
).body[0]


class FloatCalls(ast.NodeTransformer):
    def visit_Name(self, node):
        return (
            ast.copy_location(ast.Name(id='_settings_float', ctx=node.ctx), node)
            if node.id == 'float'
            else node
        )


parser = FloatCalls().visit(parser)
nodes.extend(
    [
        float_helper,
        invalid,
        ast.ClassDef(
            name='SettingsQR',
            bases=[],
            keywords=[],
            body=[Types().visit(Quiet().visit(parser))],
            decorator_list=[],
        ),
    ]
)
module = ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[]))
out = root / 'app/seedsigner_port/settings_schema.py'
out.write_text(
    '# SPDX-License-Identifier: MIT\n# Copyright 2021 SeedSigner; upstream notice: ../LICENSE.SeedSigner\n# Generated by tools/prepare_settings_schema.py. Do not hand-edit.\n'
    + '\n'.join(line.rstrip() for line in ast.unparse(module).splitlines())
    + '\n'
)
(root / 'app/settings-schema-provenance.json').write_text(
    json.dumps(
        {
            'application': lock,
            'source': str(p.relative_to(source)),
            'fileSha256': hashlib.sha256(raw).hexdigest(),
            'classSha256': classes,
            'settingsSourceSha256': hashlib.sha256(settings_raw).hexdigest(),
            'parser': 'Original Settings.parse_settingsqr extracted as SettingsQR.parse_settingsqr; logging removed, float conversion uses real doubles or explicit unsupported error',
            'l10nSourceSha256': hashlib.sha256(l10n.read_bytes()).hexdigest(),
            'transformations': [
                'Original mark_for_translation helper, renamed _mft',
                'No periphery probe: actual hardware profile, USING_MOCK_GPIO=False',
                'Frozen English-only detected languages, no filesystem emulation',
                'Strip annotations and replace SettingsEntry dataclass init/eq/repr explicitly',
            ],
            'outputSha256': hashlib.sha256(out.read_bytes()).hexdigest(),
        },
        indent=2,
    )
    + '\n'
)
print(out)
