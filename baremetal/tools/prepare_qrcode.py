# SPDX-License-Identifier: MIT
"""Freeze pinned original python-qrcode matrix algorithms without image backends."""
import ast,hashlib,importlib.metadata,json
from pathlib import Path
import qrcode
from view_source_port import LazyPort
root=Path(__file__).resolve().parents[1]
assert importlib.metadata.version('qrcode')=='7.3.1'
source=Path(qrcode.__file__).parent;out=root/'app/qrcode';out.mkdir(exist_ok=True)
expected={'main.py':'37cec6e9d8bb239edf005ec46c2a2040b3b2c29604432a1d10e541dcff4ef7d2','base.py':'f894e62848eb28b3b0f3875f352ede18d8bd07086f20d3155742d6d1de5b4002','util.py':'12bc06e5c94ddb9375644770d67c54b7d8c6b666c92fe0fd0b0451eafe913a1d','constants.py':'d02b1af1861d790f0d685ad19ade3799a560d763bcf5dfa82a088a01520edace','exceptions.py':'2f67d9b9838ab1cbdd9fbdab6bec05f06c2caf6641f5e4595aba757f4203c781','LUT.py':'01e7dd7f10fe106794b5daff56cd927da138c3576e9826b3e5ad62bb44c1efa9'}
class Port(ast.NodeTransformer):
 visit_JoinedStr=LazyPort.visit_JoinedStr
 def visit_Import(self,n):
    for item in n.names:
        if item.name=='re':item.name='seedsigner_port.qr_regex';item.asname='re'
    return n
 def visit_ImportFrom(self,n):
    if n.module=='qrcode.image.base':return None
    if n.module=='bisect':n.module='seedsigner_port.qr_bisect'
    return n
 def visit_Call(self,n):
    n=self.generic_visit(n)
    if isinstance(n.func,ast.Attribute) and ast.unparse(n.func.value)=='ALPHA_NUM' and n.func.attr=='find' and isinstance(n.args[0],ast.Subscript):
        n.args[0]=ast.Call(func=ast.Name(id='bytes',ctx=ast.Load()),args=[ast.Tuple(elts=[n.args[0]],ctx=ast.Load())],keywords=[])
    return n
 def visit_Assert(self,n):
    if ast.unparse(n.test)=='issubclass(image_factory, BaseImage)':return ast.Raise(exc=ast.Call(func=ast.Name(id='FeatureUnavailable',ctx=ast.Load()),args=[ast.Constant('PIL/image QR backends are unavailable')],keywords=[]))
    return self.generic_visit(n)
 def visit_FunctionDef(self,n):
    if n.name in ('make_image','print_tty','print_ascii'):
        n.body=ast.parse("raise FeatureUnavailable('QR matrix API only; no image/terminal backend')").body
    return self.generic_visit(n)
receipt={'package':'qrcode','version':'7.3.1','files':{},'scope':'Original segmentation, RS, mask and matrix algorithms; image/terminal methods explicitly unavailable; native PCRE2/bisect adapters; indexed bytes.find values become one-byte bytes for MicroPython.'}
for name,digest in expected.items():
    raw=(source/name).read_bytes();assert hashlib.sha256(raw).hexdigest()==digest,name
    tree=Port().visit(ast.parse(raw));text='# Copyright python-qrcode contributors; BSD, see ../LICENSE.qrcode\n# Generated pinned matrix implementation; no image backend.\nfrom seedsigner_port.decode_platform import FeatureUnavailable\n'+ast.unparse(ast.fix_missing_locations(tree))+'\n'
    (out/name).write_text(text);receipt['files'][name]={'sourceSha256':digest,'outputSha256':hashlib.sha256(text.encode()).hexdigest()}
(out/'__init__.py').write_text('# python-qrcode7.3.1; BSD, see ../LICENSE.qrcode\nfrom qrcode.main import QRCode\nfrom qrcode import constants\n')
d=importlib.metadata.distribution('qrcode');license_path=next(p for p in d.files if str(p).endswith('/LICENSE'))
(root/'app/LICENSE.qrcode').write_text(d.locate_file(license_path).read_text())
(root/'app/qrcode-provenance.json').write_text(json.dumps(receipt,indent=2)+'\n')
print('Prepared pinned qrcode matrix modules')
