# SPDX-License-Identifier: MIT
"""Preserve original ScanScreen._run; move only OS/thread/input boundaries."""
import ast,hashlib,json,subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1];repo=root.parent
source=repo/'dist/firmware/sources/lvgl/application'
lock=json.loads((repo/'firmware/lvgl-app/sources.lock.json').read_text())['application']
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip()==lock['commit']
p=source/'src/seedsigner/gui/screens/scan_screens.py';raw=p.read_bytes();tree=ast.parse(raw)
guards=json.loads((repo/'firmware/lvgl-app/source-guards.json').read_text())
assert hashlib.sha256(raw).hexdigest()==guards['gui/screens/scan_screens.py']
cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='ScanScreen')
method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='_run')
original=ast.get_source_segment(raw.decode(),method)
class Port(ast.NodeTransformer):
    def visit_ImportFrom(self,n):
        if n.module=='seedsigner.hardware.buttons':return None
        if n.module=='seedsigner.models.decode_qr':n.module='seedsigner_port.decode_qr'
        return n
    def visit_Attribute(self,n):
        if isinstance(n.value,ast.Name) and n.value.id=='HardwareButtonsConstants':return ast.copy_location(ast.Constant(n.attr),n)
        if ast.unparse(n)=='self.threads[0].decoder_fps':return ast.copy_location(ast.parse('self.preview.decoder_fps',mode='eval').body,n)
        if ast.unparse(n)=='time.time':return ast.copy_location(ast.parse('self.clock.time',mode='eval').body,n)
        return self.generic_visit(n)
method=Port().visit(method);method.name='run_source'
out=root/'app/seedsigner_port/scan_loop.py'
out.write_text('# SPDX-License-Identifier: MIT\n# Copyright2021 SeedSigner; notice: ../LICENSE.SeedSigner\n# Generated original ScanScreen._run. Do not hand-edit.\n'+ast.unparse(ast.fix_missing_locations(method))+'\n')
(root/'app/scan-loop-provenance.json').write_text(json.dumps({'application':lock,'source':str(p.relative_to(source)),'sourceSha256':hashlib.sha256(raw).hexdigest(),'methodSha256':hashlib.sha256(original.encode()).hexdigest(),'transformations':['Native ButtonInput names replace hardware constant IDs','Cooperative preview owns decoder_fps metadata instead of thread0','Wrap-safe native elapsed clock supplies time.time; source timing arithmetic unchanged','DecodeQRStatus import points at generated original native model'],'outputSha256':hashlib.sha256(out.read_bytes()).hexdigest()},indent=2)+'\n')
