# SPDX-License-Identifier: MIT
"""Freeze original camera mnemonic/View logic with explicit native boundaries."""
import ast,copy,hashlib,json,subprocess
from pathlib import Path
from view_source_port import LazyPort
root=Path(__file__).resolve().parents[1];repo=root.parent
source=repo/'dist/firmware/sources/lvgl/application';base=source/'src/seedsigner'
lock=json.loads((repo/'firmware/lvgl-app/sources.lock.json').read_text())['application']
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip()==lock['commit']
guards=json.loads((repo/'firmware/lvgl-app/source-guards.json').read_text())
receipt={'application':lock,'files':{},'scope':'Camera-only native flow; no fabricated RNG health or OS/TRNG prerequisite. No entropy/security qualification follows from function availability.'}
raw=(base/'helpers/mnemonic_generation.py').read_bytes();assert hashlib.sha256(raw).hexdigest()==guards['helpers/mnemonic_generation.py']
tree=ast.parse(raw)
class Counts(ast.NodeTransformer):
    def visit_Call(self,n):
        n=self.generic_visit(n)
        if isinstance(n.func,ast.Name) and n.func.id=='Counter':n.func=ast.Name(id='_counts',ctx=ast.Load())
        return n
port=LazyPort(tree,'seedsigner.helpers.mnemonic_generation')
selected={'calculate_checksum','generate_mnemonic_from_bytes','_shannon_entropy','byte_entropy_is_sufficient','_hash_dice_rolls','generate_mnemonic_from_dice','generate_bytes_from_dice','dice_entropy_is_sufficient'}
nodes=[]
for n in tree.body:
    if isinstance(n,ast.FunctionDef) and n.name in selected:nodes.append(port.visit(Counts().visit(copy.deepcopy(n))))
    elif isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ('SUPPORTED_WORD_LENGTHS','ENTROPY_BYTES_REQUIRED','DICE_ROLLS_REQUIRED','ROLL_COUNT_TO_LENGTH') for t in n.targets):nodes.append(copy.deepcopy(n))
header='''# Copyright2021 SeedSigner; MIT, see ../LICENSE.SeedSigner
# Generated original selected mnemonic/quality helpers; no RNG substitute.
from seedsigner_port.decode_platform import dependency as _dependency,FeatureUnavailable
def _counts(data):
    counts={}
    for value in data:counts[value]=counts.get(value,0)+1
    return counts
'''
text=header+ast.unparse(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])))+'\n'
out=root/'app/seedsigner_port/camera_entropy_mnemonic.py';out.write_text(text)
receipt['files']['camera_entropy_mnemonic.py']={'source':'helpers/mnemonic_generation.py','sourceSha256':hashlib.sha256(raw).hexdigest(),'outputSha256':hashlib.sha256(out.read_bytes()).hexdigest(),'functions':sorted(selected),'changes':['Original Counter(data) frequency histogram uses equivalent native dict counts; annotations/import boundaries use common source port.']}
raw=(base/'views/tools_views.py').read_bytes();assert hashlib.sha256(raw).hexdigest()==guards['views/tools_views.py']
tree=ast.parse(raw);names=('ToolsMenuView','ToolsImageEntropyLivePreviewView','ToolsImageEntropyFinalImageView','ToolsImageEntropyMnemonicLengthView','ToolsDiceEntropyMnemonicLengthView','ToolsDiceEntropyEntryView','ToolsCalcFinalWordNumWordsView','ToolsCalcFinalWordFinalizePromptView','ToolsCalcFinalWordCoinFlipsView','ToolsCalcFinalWordShowFinalWordView','ToolsCalcFinalWordDoneView','ToolsAddressExplorerSelectSourceView','ToolsAddressExplorerAddressTypeView','ToolsAddressExplorerAddressListView','ToolsAddressExplorerAddressView')
classes={n.name:copy.deepcopy(n) for n in tree.body if isinstance(n,ast.ClassDef) and n.name in names}
bindings={'_derive_camera_entropy_bytes':('seedsigner_port.camera_entropy','derive_camera_entropy_bytes'),'mnemonic_generation':('seedsigner_port.camera_entropy_mnemonic',None),'ToolsDiceEntropyMnemonicLengthView':('seedsigner.views.tools_views','ToolsDiceEntropyMnemonicLengthView'),'time':('seedsigner_port.clock',None),'Destination':('seedsigner_port.navigation','Destination'),'format':('seedsigner_port.final_word','builtin_format')}
port=LazyPort(tree,'seedsigner.views.tools_views',classes=classes,bindings=bindings)
nodes=[]
for name in names:
    node=classes[name];method=next(n for n in node.body if isinstance(n,ast.FunctionDef) and n.name=='run')
    if name=='ToolsMenuView':
        # Source menu options/title/destinations for entries ported to this
        # runtime. Linux battery/network/build/GPG/microSD/smartcard probes are
        # not constructed. Text QR / Password Generator Views live in view_tools_extra.
        # SLIP39 seed creation is omitted: shamir share generation needs random
        # bytes (secrets.token_bytes) and this device has no RNG source.
        method.body=ast.parse('button_data=[self.IMAGE,self.DICE]\nif getattr(self,"include_password_generator",True):button_data.append(self.PASSWORD_GENERATOR)\nbutton_data.extend([self.KEYBOARD,self.ADDRESS_EXPLORER,self.VERIFY_ADDRESS,self.TEXTQRCODE])\nselected_menu_num=self.run_screen(ButtonListScreen,title=_("Tools"),is_button_text_centered=False,button_data=button_data)\nif selected_menu_num==RET_CODE__BACK_BUTTON:return Destination(BackStackView)\nif button_data[selected_menu_num]==self.IMAGE:return Destination(ToolsImageEntropyLivePreviewView)\nif button_data[selected_menu_num]==self.KEYBOARD:return Destination(ToolsCalcFinalWordNumWordsView)\nif button_data[selected_menu_num]==self.ADDRESS_EXPLORER:return Destination(ToolsAddressExplorerSelectSourceView)\nif button_data[selected_menu_num]==self.VERIFY_ADDRESS:return Destination(_dependency("seedsigner.views.scan_views","ScanAddressView"))\nif button_data[selected_menu_num]==self.SLIP39_IMAGE:\n    self.controller.create_slip39=True\n    return Destination(ToolsImageEntropyLivePreviewView)\nif button_data[selected_menu_num]==self.SLIP39_DICE:\n    self.controller.create_slip39=True\n    return Destination(ToolsDiceEntropyMnemonicLengthView)\nif button_data[selected_menu_num]==self.TEXTQRCODE:return Destination(_dependency("seedsigner_port.view_tools_extra","ToolsTextQRView"))\nif button_data[selected_menu_num]==self.PASSWORD_GENERATOR:return Destination(_dependency("seedsigner_port.view_tools_extra","ToolsPasswordGeneratorTypeView"))\nreturn Destination(ToolsDiceEntropyMnemonicLengthView)\n').body
    elif name=='ToolsImageEntropyLivePreviewView':
        gates=[n for n in method.body if isinstance(n,ast.If) and ast.unparse(n.test)=='not self.controller.hardware_rng_is_healthy'];assert len(gates)==1
        method.body.remove(gates[0])
        for n in ast.walk(method):
            if isinstance(n,ast.ImportFrom) and n.module=='seedsigner.gui.screens.tools_screens':n.module='seedsigner_port.camera_entropy_screens'
    elif name=='ToolsImageEntropyFinalImageView':
        # The native live screen always returns one owned final NV12 capture.
        # PIL autocontrast/resize was presentation-only; display native copy.
        method.body=ast.parse('''from seedsigner_port.camera_entropy_screens import ToolsImageEntropyFinalImageScreen
if self.controller.image_entropy_final_image is None:
    raise RuntimeError('Camera did not return a final capture')
ret=self.run_screen(ToolsImageEntropyFinalImageScreen,final_image=self.controller.image_entropy_final_image)
if ret==RET_CODE__BACK_BUTTON:
    from seedsigner_port.camera_entropy import clear_controller_images
    clear_controller_images(self.controller)
    return Destination(BackStackView)
next_view=self.next_view or ToolsImageEntropyMnemonicLengthView
return Destination(next_view,view_args=self.next_view_args)
''').body
    elif name=='ToolsImageEntropyMnemonicLengthView':
        poor=[x for x in method.body if isinstance(x,ast.If) and ast.unparse(x.test)=='final_hash is None'];assert len(poor)==1
        returns=[x for x in poor[0].body if isinstance(x,ast.Return)];assert len(returns)==1
        # Source intends a retry after clearing all images. Native review cannot
        # fabricate/recover a missing pool, so retry fresh camera acquisition.
        returns[0].value=ast.Call(func=ast.Name(id='Destination',ctx=ast.Load()),args=[ast.Name(id='ToolsImageEntropyLivePreviewView',ctx=ast.Load())],keywords=[ast.keyword(arg='skip_current_view',value=ast.Constant(True))])
        # Source Back goes to final-image review and MUST retain owned inputs.
        # Every other return/error/unwind releases them.
        back=[x for x in method.body if isinstance(x,ast.If) and ast.unparse(x.test)=='selected_menu_num == RET_CODE__BACK_BUTTON'];assert len(back)==1
        back[0].body.insert(0,ast.Assign(targets=[ast.Name(id='release_inputs',ctx=ast.Store())],value=ast.Constant(False)))
        keep=ast.parse('owned_previews=self.controller.image_entropy_preview_frames\nowned_final=self.controller.image_entropy_final_image\nrelease_inputs=True').body
        cleanup=ast.parse('if release_inputs:\n from seedsigner_port.camera_entropy import clear_images,clear_controller_images\n clear_images(owned_previews,owned_final)\n clear_controller_images(self.controller)').body
        method.body=keep+[ast.Try(body=method.body,handlers=[],orelse=[],finalbody=cleanup)]
    elif name=='ToolsDiceEntropyEntryView':
        for n in ast.walk(method):
            if isinstance(n,ast.ImportFrom) and n.module=='seedsigner.gui.screens.tools_screens':n.module='seedsigner_port.camera_entropy_screens'
    node=port.visit(node)
    nodes.append(ast.FunctionDef(name='_make_'+name,args=ast.arguments(posonlyargs=[],args=[],kwonlyargs=[],kw_defaults=[],defaults=[]),body=[node,ast.Return(value=ast.Name(id=name,ctx=ast.Load()))],decorator_list=[]))
text='# Copyright2021 SeedSigner; MIT, see ../LICENSE.SeedSigner\n# Generated original camera Views; reviewed native-only platform boundaries.\nfrom seedsigner_port.decode_platform import dependency as _dependency,FeatureUnavailable\n'+ast.unparse(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])))+'\n'
text+='_FACTORIES={'+','.join(repr(n)+':_make_'+n for n in names)+'}\n_CACHE={}\ndef _resolve(name):\n    if name not in _CACHE:\n        if name not in _FACTORIES:raise AttributeError(name)\n        _CACHE[name]=_FACTORIES[name]()\n    return _CACHE[name]\ndef __getattr__(name):return _resolve(name)\n'
out=root/'app/seedsigner_port/camera_entropy_views.py';out.write_text(text)
receipt['files']['camera_entropy_views.py']={'source':'views/tools_views.py','sourceSha256':hashlib.sha256(raw).hexdigest(),'outputSha256':hashlib.sha256(out.read_bytes()).hexdigest(),'classes':list(names),'changes':['Camera is configured entropy source; remove Linux fork RNG-health entry prerequisite.','Native capture always returns final owned NV12; no PIL/procfs/fallback camera boundary.','Mnemonic length, entropy truncation/BIP39/pending-seed routing remain original; image buffers cleared in finally.','Poor Entropy clears images and retries fresh acquisition; length Back retains images for review.']}
(root/'app/camera-entropy-provenance.json').write_text(json.dumps(receipt,indent=2)+'\n')
print('Prepared original camera/dice helpers and Views')
