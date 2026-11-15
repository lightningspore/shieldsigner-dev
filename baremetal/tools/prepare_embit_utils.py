# SPDX-License-Identifier: MIT
"""Freeze original embit helpers behind actual lazy native dependencies."""
import ast,hashlib,json,subprocess
from pathlib import Path
from view_source_port import LazyPort
root=Path(__file__).resolve().parents[1];repo=root.parent
source=repo/'dist/firmware/sources/lvgl/application'
lock=json.loads((repo/'firmware/lvgl-app/sources.lock.json').read_text())['application']
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip()==lock['commit']
raw=(source/'src/seedsigner/helpers/embit_utils.py').read_bytes()
assert hashlib.sha256(raw).hexdigest()==json.loads((repo/'firmware/lvgl-app/source-guards.json').read_text())['helpers/embit_utils.py']
tree=ast.parse(raw);port=LazyPort(tree,'seedsigner.helpers.embit_utils')
functions=[n for n in tree.body if isinstance(n,ast.FunctionDef)]
nodes=[port.visit(n) for n in functions]
text='# Copyright2021 SeedSigner; MIT, see ../LICENSE.SeedSigner\n# Generated original helpers; unported providers fail on use.\nfrom seedsigner_port.decode_platform import dependency as _dependency,FeatureUnavailable\n'+ast.unparse(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])))+'\n'
out=root/'app/seedsigner_port/embit_utils.py';out.write_text(text)
(root/'app/embit-utils-provenance.json').write_text(json.dumps({'application':lock,'sourceSha256':hashlib.sha256(raw).hexdigest(),'outputSha256':hashlib.sha256(out.read_bytes()).hexdigest(),'functions':[n.name for n in functions],'changes':['Remove annotations, lazy real imports, original f-string conversions through common source port.'],'scope':'Function presence is not qualification; descriptor/message-signing providers remain separately gated.'},indent=2)+'\n')
