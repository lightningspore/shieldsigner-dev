# SPDX-License-Identifier: MIT
"""Keep original Settings data algorithms; replace Linux boundaries explicitly."""

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
p = source / 'src/seedsigner/models/settings.py'
raw = p.read_bytes()
tree = ast.parse(raw)
original = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'Settings')
methods = {n.name: n for n in original.body if isinstance(n, ast.FunctionDef)}


class Port(ast.NodeTransformer):
    def visit_FunctionDef(self, node):
        node.returns = None
        for arg in [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]:
            arg.annotation = None
        return self.generic_visit(node)

    def visit_Expr(self, node):
        if (
            isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Attribute)
            and isinstance(node.value.func.value, ast.Name)
            and node.value.func.value.id == 'logger'
        ):
            return ast.copy_location(ast.Pass(), node)
        return self.generic_visit(node)

    def visit_Attribute(self, node):
        # Original update's default backfill now honors explicit native defaults.
        if (
            isinstance(node.value, ast.Name)
            and node.value.id == 'entry'
            and node.attr == 'default_value'
        ):
            return ast.copy_location(
                ast.Call(
                    func=ast.Attribute(
                        value=ast.Name(id='self', ctx=ast.Load()),
                        attr='_default_value',
                        ctx=ast.Load(),
                    ),
                    args=[
                        ast.Attribute(
                            value=ast.Name(id='entry', ctx=ast.Load()),
                            attr='attr_name',
                            ctx=ast.Load(),
                        )
                    ],
                    keywords=[],
                ),
                node,
            )
        return self.generic_visit(node)


selected = [
    'update',
    'get_value',
    'get_value_display_name',
    'get_multiselect_value_display_names',
    'get_platform_default_display_config',
    'get_platform_default_camera_rotation',
]
node = ast.parse('class Settings(SettingsQR):\n pass').body[0]
node.body = []
source_hashes = {}
for name in selected:
    method = methods[name]
    source_hashes[name] = hashlib.sha256(
        ast.get_source_segment(raw.decode(), method).encode()
    ).hexdigest()
    if name == 'update':
        # Reject unavailable platform actions before a bulk update can partially apply.
        preflight = ast.parse(
            'for key,value in new_settings.items():\n self._platform.check(key,value)'
        ).body[0]
        method.body.insert(1, preflight)
    if name == 'get_value':
        for n in ast.walk(method):
            if (
                isinstance(n, ast.Return)
                and n.value is not None
                and ast.unparse(n.value)
                == 'SettingsDefinition.get_settings_entry(attr_name).default_value'
            ):
                n.value = ast.parse('self._default_value(attr_name)', mode='eval').body
    node.body.append(Port().visit(method))
setter = methods['set_value']
source_hashes['set_value'] = hashlib.sha256(
    ast.get_source_segment(raw.decode(), setter).encode()
).hexdigest()
cut = next(
    i
    for i, n in enumerate(setter.body)
    if isinstance(n, ast.If) and 'SETTING__PERSISTENT_SETTINGS' in ast.unparse(n.test)
)
assert any('numeric_value' in ast.unparse(n) for n in setter.body[:cut])
assert any('TYPE__MULTISELECT' in ast.unparse(n) for n in setter.body[:cut])
setter.body = (
    setter.body[:cut]
    + ast.parse(
        'self._platform.check(attr_name,value)\nself._data[attr_name]=value\nif save:self.save()\nif attr_name==SettingsConstants.SETTING__LOCALE:self.load_locale()'
    ).body
)
node.body.append(Port().visit(setter))
# Native initialization and save/locale boundaries are separate reviewed policy.
policy = '''
_instance=None
RUNTIME_PROFILE='luckfox_22'
OS_ENVIRONMENT='baremetal'
HOSTNAME='rv1103-baremetal'
SETTINGS_FILENAME=None
SU_COMMAND_PREFIX=None
def __init__(self):
    raise Exception('Cannot directly instantiate a Singleton. Access via get_instance()')
@classmethod
def get_instance(cls):
    if cls._instance is None:
        instance=object.__new__(cls)
        instance._platform=NativeSettingsPlatform()
        instance._data=SettingsDefinition.get_defaults()
        instance._data.update(instance._platform.defaults())
        cls._instance=instance
    return cls._instance
@classmethod
def is_seedsigner_os(cls):return False
@classmethod
def is_dev_board(cls):return False
@classmethod
def is_desktop(cls):return False
@classmethod
def get_platform_default_hardware_config(cls):return 'mini-pcb240'
@classmethod
def get_default_settings_filename(cls):raise UnsupportedSettingsAction('No native settings file is mounted')
def _default_value(self,key):return self._platform.default_value(key)
def save(self):return self._platform.save(self._data)
def flush_save(self):return self._platform.save(self._data)
def load_locale(self):return self._platform.load_locale(self._data)
'''
node.body = ast.parse(policy).body + node.body
module = ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[]))
header = '# SPDX-License-Identifier: MIT\n# Copyright 2021 SeedSigner; upstream notice: ../LICENSE.SeedSigner\n# Generated by tools/prepare_settings_store.py. Do not hand-edit.\nfrom seedsigner_port.settings_schema import SettingsConstants,SettingsDefinition,SettingsQR\nfrom seedsigner_port.settings_platform import NativeSettingsPlatform,UnsupportedSettingsAction\n'
out = root / 'app/seedsigner_port/settings_store.py'
out.write_text(
    header + '\n'.join(line.rstrip() for line in ast.unparse(module).splitlines()) + '\n'
)
(root / 'app/settings-store-provenance.json').write_text(
    json.dumps(
        {
            'application': lock,
            'source': str(p.relative_to(source)),
            'fileSha256': hashlib.sha256(raw).hexdigest(),
            'originalMethodSha256': source_hashes,
            'transformations': [
                'Strip annotations and logging only in data algorithms',
                'Keep complete set_value validation/equality prefix; replace Linux side effects with native policy',
                'update preflights native actions and uses native defaults in missing/empty backfill',
                'Native singleton uses object.__new__(cls): inherited __new__ is not exposed by MicroPython; no file reads/timers, explicit RAM-only save and locale capability',
            ],
            'outputSha256': hashlib.sha256(out.read_bytes()).hexdigest(),
        },
        indent=2,
    )
    + '\n'
)
print(out)
