# SPDX-License-Identifier: MIT
"""Original QR format probes without claiming unavailable AES/scrypt providers."""
import ast,hashlib,json,subprocess,importlib.metadata
from pathlib import Path
from Cryptodome.Cipher import AES
from view_source_port import LazyPort
root=Path(__file__).resolve().parents[1];repo=root.parent
source=repo/'dist/firmware/sources/lvgl/application';lock=json.loads((repo/'firmware/lvgl-app/sources.lock.json').read_text())['application']
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip()==lock['commit']
assert importlib.metadata.version('pycryptodomex')=='3.23.0'
constants={name:getattr(AES,name) for name in ('MODE_ECB','MODE_CBC','MODE_CTR','MODE_GCM')}
receipt={'application':lock,'files':{},'aesModeConstants':constants,'compatibilityChanges':['Base43 local prepend buffer is a list because MicroPython bytearray has no insert; returned bytes unchanged.','UnicodeDecodeError uses native UnicodeError where CPython subclass is absent.'],'constantProvider':'pycryptodomex3.23.0, compile-time public format constants only; no native AES module','scope':'Original format detection/envelope parsing; AES/scrypt entry preflights fail explicitly on native runtime.'}
for file,name in [('models/bip38.py','bip38.py'),('models/wif.py','wif.py'),('models/encryption.py','encryption.py'),('helpers/kef.py','kef.py'),('helpers/base43.py','base43.py')]:
    raw=(source/'src/seedsigner'/file).read_bytes()
    assert raw==subprocess.check_output(['git','show',lock['commit']+':src/seedsigner/'+file],cwd=source),file
    tree=ast.parse(raw)
    port=LazyPort(tree,'seedsigner.'+file[:-3].replace('/','.'))
    class Constants(ast.NodeTransformer):
        def visit_Attribute(self,n):
            if isinstance(n.value,ast.Name) and n.value.id=='AES' and n.attr in constants:return ast.copy_location(ast.Constant(constants[n.attr]),n)
            return self.generic_visit(n)
    if name=='base43.py':
        class Buffers(ast.NodeTransformer):
            def visit_Call(self,n):
                if isinstance(n.func,ast.Name) and n.func.id=='bytearray' and not n.args:return ast.copy_location(ast.List(elts=[],ctx=ast.Load()),n)
                return self.generic_visit(n)
        tree=Buffers().visit(tree)
    nodes=[]
    for node in tree.body:
        if isinstance(node,(ast.Import,ast.ImportFrom)):continue
        # Preserve actual numeric mode IDs in original wire-format tables. This
        # supplies no AES object, key handling or cipher implementation.
        if isinstance(node,ast.Assign):node=Constants().visit(node)
        node=port.visit(node)
        if isinstance(node,ast.ClassDef):
            for method in node.body:
                if not isinstance(method,ast.FunctionDef):continue
                checks=[]
                if name=='bip38.py' and method.name=='decrypt':checks=[('hashlib','scrypt'),('Cryptodome.Cipher','AES')]
                if name in ('kef.py','encryption.py') and method.name in ('encrypt','decrypt','create'):checks=[('Cryptodome.Cipher','AES')]
                method.body=[ast.Expr(value=ast.Call(func=ast.Name(id='_dependency',ctx=ast.Load()),args=[ast.Constant(m),ast.Constant(a)],keywords=[])) for m,a in checks]+method.body
        if node is not None:nodes.append(node)
    notice='# Original SeedSigner/Krux source; see LICENSE.SeedSigner and LICENSE.Krux-QR\n'
    text=notice+'# Generated format providers; unavailable crypto remains explicit.\nfrom seedsigner_port.decode_platform import dependency as _dependency,FeatureUnavailable\ntry:\n    UnicodeDecodeError\nexcept NameError:\n    UnicodeDecodeError=UnicodeError\n'+ast.unparse(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])))+'\n'
    out=root/'app/seedsigner_port'/name;out.write_text(text)
    receipt['files'][name]={'source':file,'sourceSha256':hashlib.sha256(raw).hexdigest(),'outputSha256':hashlib.sha256(text.encode()).hexdigest()}
# Retain the actual complete upstream Krux notice from its source header.
raw=(source/'src/seedsigner/helpers/kef.py').read_text();notice=raw.split('from Cryptodome.Cipher import AES',1)[0]
(root/'app/LICENSE.Krux-QR').write_text(notice)
(root/'app/qr-detection-provenance.json').write_text(json.dumps(receipt,indent=2)+'\n')
print('Prepared original QR detection providers:',len(receipt['files']))
