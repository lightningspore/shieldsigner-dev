# SPDX-License-Identifier: MIT
"""Host-only AST inventory of a read-only REF source snapshot; never run the app."""
import ast
import hashlib
import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('source', type=Path)
root = parser.parse_args().source
if not (root / 'seedsigner/version.json').is_file():
    raise SystemExit('Expected a snapshot of REF /opt/src')
files = []
imports = set()
features = {'annotations': 0, 'asyncFunctions': 0, 'dataclassDecorators': 0}
for path in sorted(root.rglob('*.py')):
    if '__pycache__' in path.parts:
        continue
    source = path.read_bytes()
    tree = ast.parse(source, filename=str(path))
    modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(name.name for name in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add('.' * node.level + node.module)
        elif isinstance(node, ast.AnnAssign):
            features['annotations'] += 1
        elif isinstance(node, ast.AsyncFunctionDef):
            features['asyncFunctions'] += 1
        elif isinstance(node, ast.ClassDef):
            features['dataclassDecorators'] += sum(isinstance(d, ast.Name) and d.id == 'dataclass' for d in node.decorator_list)
    imports.update(modules)
    files.append({'path': str(path.relative_to(root)), 'bytes': len(source),
                  'sha256': hashlib.sha256(source).hexdigest(), 'imports': sorted(modules)})
print('@@APP_INVENTORY ' + json.dumps({'scope': 'Read-only AST inventory, no app imports, user settings or seed files read',
    'version': json.loads((root/'seedsigner/version.json').read_text()),
    'sourceFiles': files, 'allImports': sorted(imports), 'syntaxCounts': features}))
