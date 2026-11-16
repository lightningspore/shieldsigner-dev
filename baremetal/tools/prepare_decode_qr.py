# SPDX-License-Identifier: MIT
"""Freeze all original QR model classes, changing platform boundaries explicitly."""
import ast,hashlib,json,subprocess
from pathlib import Path
from source_port import Bound
root=Path(__file__).resolve().parents[1];repo=root.parent
source=repo/'dist/firmware/sources/lvgl/application'
lock=json.loads((repo/'firmware/lvgl-app/sources.lock.json').read_text())['application']
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip()==lock['commit']
path=source/'src/seedsigner/models/decode_qr.py';raw=path.read_bytes();tree=ast.parse(raw)
guards=json.loads((repo/'firmware/lvgl-app/source-guards.json').read_text())
assert hashlib.sha256(raw).hexdigest()==guards['models/decode_qr.py']
bindings={}
for n in tree.body:
    if isinstance(n,ast.Import):
        for a in n.names:bindings[a.asname or a.name]=(a.name,None)
    elif isinstance(n,ast.ImportFrom):
        for a in n.names:bindings[a.asname or a.name]=(n.module,a.name)
for name in ('json','re','logging','dataclass','IntEnum','QRType','SettingsConstants'):bindings.pop(name,None)
class Port(ast.NodeTransformer):
    def __init__(self):self.locals=[]
    def visit_FunctionDef(self,n):
        if n.name=='base43_decode':
            # MicroPython lacks stepped bytes slicing and bytearray.reverse().
            # Keep the original reverse traversal and byte assembly via iter/list.
            for node in ast.walk(n):
                if isinstance(node,ast.For) and isinstance(node.iter,ast.Subscript) and ast.unparse(node.iter)=='v[::-1]':
                    node.iter=ast.Call(func=ast.Name(id='reversed',ctx=ast.Load()),args=[ast.Name(id='v',ctx=ast.Load())],keywords=[])
                if isinstance(node,ast.Assign) and isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Name) and node.value.func.id=='bytearray' and not node.value.args:
                    node.value=ast.List(elts=[],ctx=ast.Load())
        n.returns=None
        for a in [*n.args.posonlyargs,*n.args.args,*n.args.kwonlyargs,*([n.args.vararg] if n.args.vararg else []),*([n.args.kwarg] if n.args.kwarg else [])]:a.annotation=None
        n.decorator_list=[self.visit(d) for d in n.decorator_list]
        n.args.defaults=[self.visit(d) for d in n.args.defaults]
        n.args.kw_defaults=[self.visit(d) if d is not None else None for d in n.args.kw_defaults]
        bound=Bound()
        for item in n.body:bound.visit(item)
        bound.names.update(a.arg for a in [*n.args.posonlyargs,*n.args.args,*n.args.kwonlyargs,*([n.args.vararg] if n.args.vararg else []),*([n.args.kwarg] if n.args.kwarg else [])])
        self.locals.append(bound.names)
        body=[]
        for item in n.body:
            value=self.visit(item)
            if isinstance(value,list):body.extend(value)
            elif value is not None:body.append(value)
        n.body=body or [ast.Pass()];self.locals.pop()
        return n
    def visit_AnnAssign(self,n):
        return ast.copy_location(ast.Assign(targets=[n.target],value=self.visit(n.value)),n) if n.value is not None else None
    def visit_Name(self,n):
        if isinstance(n.ctx,ast.Load) and n.id in bindings and not any(n.id in scope for scope in self.locals):
            module,attr=bindings[n.id]
            return ast.copy_location(ast.Call(func=ast.Name(id='_dependency',ctx=ast.Load()),args=[ast.Constant(module),ast.Constant(attr)],keywords=[]),n)
        return n
    def visit_ImportFrom(self,n):
        if n.module=='seedsigner.models.settings':
            n.module='seedsigner_port.settings_store';return n
        return [ast.copy_location(ast.Assign(targets=[ast.Name(id=a.asname or a.name,ctx=ast.Store())],value=ast.Call(func=ast.Name(id='_dependency',ctx=ast.Load()),args=[ast.Constant(n.module),ast.Constant(a.name)],keywords=[])),n) for a in n.names]
    def visit_Import(self,n):
        return [ast.copy_location(ast.Assign(targets=[ast.Name(id=a.asname or a.name,ctx=ast.Store())],value=ast.Call(func=ast.Name(id='_dependency',ctx=ast.Load()),args=[ast.Constant(a.name),ast.Constant(None)],keywords=[])),n) for a in n.names]
    def visit_Try(self,n):
        n=self.generic_visit(n)
        if any(h.type is None or (isinstance(h.type,ast.Name) and h.type.id in ('Exception','BaseException')) for h in n.handlers):
            n.handlers.insert(0,ast.ExceptHandler(type=ast.Name(id='FeatureUnavailable',ctx=ast.Load()),name=None,body=[ast.Raise()]))
        return n
    def visit_ExceptHandler(self,n):
        if n.type is not None and ast.unparse(n.type)=='json.decoder.JSONDecodeError':n.type=ast.Name(id='ValueError',ctx=ast.Load())
        return self.generic_visit(n)
    def visit_Expr(self,n):
        if isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Attribute) and isinstance(n.value.func.value,ast.Name) and n.value.func.value.id in ('logger','logging'):return ast.copy_location(ast.Pass(),n)
        return self.generic_visit(n)
classes=[n for n in tree.body if isinstance(n,ast.ClassDef)];provenance={}
for cls in classes:
    provenance[cls.name]=hashlib.sha256(ast.get_source_segment(raw.decode(),cls).encode()).hexdigest()
    cls.decorator_list=[]
    if cls.name=='DecodeQRStatus':cls.bases=[]
    if cls.name=='PayloadAnalysis':
        cls.body=ast.parse('''def __init__(self,segment,candidate_types,public_data=None,encrypted_qr=None):
 self.segment=segment
 self.candidate_types=candidate_types
 self.public_data=public_data
 self.encrypted_qr=encrypted_qr
''').body
    Port().visit(cls)
    if cls.name=='DecodeQR':
        policy={'is_qr_scanner_available':'return _available()',
                'get_qr_scanner_error':"return '' if _available() else 'Native QR decoder unavailable'",
                '_opencv_available_desktop':'return False',
                '_extract_qr_data_opencv':"raise FeatureUnavailable('OpenCV is replaced by native ZXing')",
                'extract_qr_data':'return _extract(image,is_binary)'}
        for method in cls.body:
            if isinstance(method,ast.FunctionDef) and method.name in policy:method.body=ast.parse(policy[method.name]).body
header='''# SPDX-License-Identifier: MIT
# Copyright2021 SeedSigner; upstream notice: ../LICENSE.SeedSigner
# Generated from all original model classes by tools/prepare_decode_qr.py.
# Native dependencies remain explicit; class availability is not workflow qualification.
import json
import re
from seedsigner_port.qr_type import QRType
from seedsigner_port.settings_schema import SettingsConstants
from seedsigner_port.decode_platform import dependency as _dependency, FeatureUnavailable, available as _available, extract as _extract
try:
    UnicodeDecodeError
except NameError:
    UnicodeDecodeError=UnicodeError
'''
out=root/'app/seedsigner_port/decode_qr.py';out.write_text(header+ast.unparse(ast.fix_missing_locations(ast.Module(body=classes,type_ignores=[])))+'\n')
qr_path=source/'src/seedsigner/models/qr_type.py'
(root/'app/seedsigner_port/qr_type.py').write_text('# SPDX-License-Identifier: MIT\n# Copyright2021 SeedSigner; upstream notice: ../LICENSE.SeedSigner\n'+qr_path.read_text())
# Original MicroPython library base64; normalize its exception spelling to the
# real MicroPython binascii API, which raises ValueError for malformed input.
base=root/'.tools/micropython/lib/micropython-lib/python-stdlib/base64/base64.py'
(root/'app/LICENSE.micropython-lib').write_bytes((root/'.tools/micropython/lib/micropython-lib/LICENSE').read_bytes())
assert hashlib.sha256(base.read_bytes()).hexdigest()=='7db45610392bf27d506b2159279c40d3fd5e5f04b6b3bcced7acaf2f9edd3852'
text=base.read_text();(root/'app/base64.py').write_text('# Derived from pinned micropython-lib base64; original notices retained.\n'+text.replace('raise binascii.Error(', 'raise ValueError('))
receipt={'application':lock,'source':str(path.relative_to(source)),'sourceSha256':hashlib.sha256(raw).hexdigest(),'classes':provenance,'transformations':['Remove annotations; explicit PayloadAnalysis constructor; integer status constants','Defer actual feature imports to native dependency boundary; preserve function-local bindings and arguments','Propagate unavailable dependencies before broad parse handlers','Remove logger payload calls; JSON decode exception spelling normalized','Base43 uses reversed(v) and a list reverse buffer; original byte algorithm unchanged','Replace legacy image probes/extraction with existing native ZXing API'],'outputSha256':hashlib.sha256(out.read_bytes()).hexdigest(),'base64':{'source':'micropython-lib/python-stdlib/base64/base64.py','sourceSha256':hashlib.sha256(base.read_bytes()).hexdigest(),'outputSha256':hashlib.sha256((root/'app/base64.py').read_bytes()).hexdigest(),'change':'binascii.Error raises become ValueError, matching actual MicroPython binascii errors'}}
(root/'app/decode-qr-provenance.json').write_text(json.dumps(receipt,indent=2)+'\n')
