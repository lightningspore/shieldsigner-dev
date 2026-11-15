# SPDX-License-Identifier: MIT
"""Freeze original Text QR and Password Generator Views/helpers for the native app.

Sources: views/gpg_views.py (Text QR), views/tools_views.py (ToolsTextQRView and
password helpers), views/password_generator_views.py, helpers/password_generation.py,
helpers/diceware.py + resources/diceware (EFF wordlists), embit 0.8.0 bip85.py.
Reviewed native boundaries are listed in app/tools-extra-provenance.json.
"""
import ast,copy,hashlib,io,json,subprocess,tarfile
from pathlib import Path
from view_source_port import LazyPort
root=Path(__file__).resolve().parents[1];repo=root.parent
source=repo/'dist/firmware/sources/lvgl/application';base=source/'src/seedsigner'
lock=json.loads((repo/'firmware/lvgl-app/sources.lock.json').read_text())['application']
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip()==lock['commit']
receipt={'application':lock,'files':{},'scope':'Text QR and Password Generator flows on native screens. Seedkeeper save omitted (smartcard support fixed disabled). System RNG path keeps the original health gate; no RNG monitor exists so it reports unavailable. No entropy/security qualification follows from availability.'}
app=root/'app/seedsigner_port'
def record(out,src,raw,changes):
    receipt['files'][out.name]={'source':src,'sourceSha256':hashlib.sha256(raw).hexdigest(),'outputSha256':hashlib.sha256(out.read_bytes()).hexdigest(),'changes':changes}

# embit bip85 (same pinned sdist as prepare_bip39.py)
tar=root/'.tools/embit-0.8.0/source.tar.gz';data=tar.read_bytes()
assert hashlib.sha256(data).hexdigest()=='8bf4b10073c67400370ce523fb16f035fe759f6fdd987c579bdcc268d75ed770'
with tarfile.open(fileobj=io.BytesIO(data)) as archive:raw=archive.extractfile('embit-0.8.0/src/embit/bip85.py').read()
out=root/'app/embit/bip85.py';out.write_text('# Copyright2020 Stepan Snigirev; MIT, see ../LICENSE.embit\n'+raw.decode());record(out,'embit-0.8.0/src/embit/bip85.py',raw,['Unchanged'])

# EFF diceware wordlists: keys are the ordered dice sequences, store words only.
words={}
for name,rolls in (('eff_short_wordlist_1.txt',4),('eff_large_wordlist.txt',5)):
    raw=(base/'resources/diceware'/name).read_bytes();rows=[l.split('\t',1) for l in raw.decode().splitlines() if l.strip()]
    expected=['']
    for _ in range(rolls):expected=[p+d for p in expected for d in '123456']
    assert [k for k,_ in rows]==expected and all(w==w.strip() and '\n' not in w for _,w in rows)
    words[name]=('\n'.join(w for _,w in rows),rolls,raw)
out=app/'diceware_words.py'
out.write_text('# EFF Diceware wordlists (CC BY 3.0 US, Electronic Frontier Foundation); see ../LICENSE.EFF-diceware\n# Generated: words in ascending dice-sequence order; keys are implied.\n'
    +'EFF_SHORT=%r\nEFF_LARGE=%r\n'%(words['eff_short_wordlist_1.txt'][0],words['eff_large_wordlist.txt'][0]))
(root/'app/LICENSE.EFF-diceware').write_bytes((base/'resources/diceware/LICENSE_EFF.txt').read_bytes())
record(out,'resources/diceware/*.txt',words['eff_short_wordlist_1.txt'][2]+words['eff_large_wordlist.txt'][2],['Words only, ordered by dice key; key order asserted at generation'])

# helpers/password_generation.py
raw=(base/'helpers/password_generation.py').read_bytes();tree=ast.parse(raw)
port=LazyPort(tree,'seedsigner.helpers.password_generation',bindings={'SHAKE256':('seedsigner_port.shake',None),'base64':('seedsigner_port.password_support',None)})
nodes=[port.visit(copy.deepcopy(n)) for n in tree.body if isinstance(n,ast.FunctionDef)]
out=app/'password_generation.py'
out.write_text('# Copyright2021 SeedSigner; MIT, see ../LICENSE.SeedSigner\n# Generated original password generation helpers.\nimport math\nfrom seedsigner_port.decode_platform import dependency as _dependency,FeatureUnavailable\n'+ast.unparse(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])))+'\n')
record(out,'helpers/password_generation.py',raw,['Cryptodome SHAKE256 -> seedsigner_port.shake (FIPS 202, vector-checked)','base64.b85encode -> password_support (CPython algorithm)'])

# Views
def load(file):
    raw=(base/file).read_bytes();return raw,ast.parse(raw)
sources={'views/gpg_views.py':('ToolsTextQRTextEntryView','ToolsTextQRTextEntryExitDialogView','ToolsTextQRReviewTextView','ToolsTextQRTranscribeModePromptView','ToolsTextQRTranscribeModeView','ToolsTextQRFullScreenModeView','ToolsTranscribeTextQRZoomedInView','ToolsTranscribeTextQRConfirmQRPromptView','ToolsTranscribeTextQRConfirmScanView','ToolsTextQRScanQRCodeView','ToolsTextQRReviewTextView2'),
         'views/tools_views.py':('ToolsTextQRView',),
         'views/password_generator_views.py':('ToolsPasswordGeneratorTypeView','ToolsPasswordStrengthView','ToolsPasswordRandomOptionsView','ToolsPasswordEntropySourceView','ToolsPasswordHardwareRngEntropyView','ToolsPasswordWordSeparatorView','ToolsPasswordDiceRollCountView','ToolsPasswordDiceEntryView','ToolsPasswordGenerateView','ToolsPasswordBIP85GenerateView','ToolsPasswordReviewView','ToolsPasswordSaveView')}
functions={'views/gpg_views.py':('_text_qr_done_destination',),
           'views/tools_views.py':('_clear_password_entropy_cache','_cache_password_entropy','_get_password_entropy_cache','_random_charset','_bip85_supported_password_type','_strength_to_length','_dice_rolls_for_strength','_is_diceware_password_type','_diceware_word_count','_format_word_password')}
all_classes=[n for names in sources.values() for n in names]
local=set(all_classes)|{f for fs in functions.values() for f in fs}
S='seedsigner_port.password_support'
bindings={'time':('seedsigner_port.clock',None),'Destination':('seedsigner_port.navigation','Destination'),
          'password_generation':('seedsigner_port.password_generation',None),'diceware':(S,None),
          'mnemonic_generation':('seedsigner_port.camera_entropy_mnemonic',None),
          '_derive_camera_entropy_bytes':('seedsigner_port.camera_entropy','derive_camera_entropy_bytes'),
          '_derive_hardware_rng_entropy_bytes':(S,'hardware_rng_unavailable'),
          'ToolsDiceEntropyEntryScreen':(S,'PasswordDiceEntryScreen'),
          'ToolsMenuView':('seedsigner.views.tools_views','ToolsMenuView'),
          'ToolsImageEntropyLivePreviewView':('seedsigner.views.tools_views','ToolsImageEntropyLivePreviewView')}
for c in ('BIP85_APP_HEX','BIP85_APP_BASE64','BIP85_APP_BASE85','BIP85_APP_DICE'):bindings[c]=('seedsigner_port.view_tools_extra',c)
for screen in ('ToolsTextQRTextEntryScreen','ToolsTextQRReviewTextScreen','ToolsTextQRTranscribeModePromptScreen','ToolsTranscribeTextQRWholeQRScreen','ToolsTranscribeTextQRZoomedInScreen','ToolsTranscribeTextQRConfirmQRPromptScreen'):
    bindings[screen]=('seedsigner.gui.screens',screen)
class Capitalize(ast.NodeTransformer):
    def visit_Call(self,n):
        n=self.generic_visit(n)
        if isinstance(n.func,ast.Attribute) and n.func.attr=='capitalize' and not n.args:
            return ast.Call(func=ast.Name(id='_capitalize',ctx=ast.Load()),args=[n.func.value],keywords=[])
        return n
class Underscore(ast.NodeTransformer):
    # CPython comprehensions have their own scope; `for button, _ in options`
    # must not shadow gettext `_` for the enclosing function after porting.
    def visit_comprehension(self,n):
        for t in ast.walk(n.target):
            if isinstance(t,ast.Name) and t.id=='_':t.id='_unused'
        return self.generic_visit(n)
    def visit_Name(self,n):return n
nodes=[];constants=[];changes=[]
for file in sources:
    raw,tree=load(file)
    port=LazyPort(tree,'seedsigner.'+file[:-3].replace('/','.'),classes=local,bindings=bindings)
    for n in tree.body:
        if isinstance(n,ast.Assign) and all(isinstance(t,ast.Name) and (t.id.startswith('PASSWORD_') or t.id.startswith('BIP85_APP_')) for t in n.targets):
            if ast.unparse(n) not in [ast.unparse(c) for c in constants]:constants.append(copy.deepcopy(n))
        elif isinstance(n,ast.FunctionDef) and n.name in functions.get(file,()):
            nodes.append(port.visit(Capitalize().visit(Underscore().visit(copy.deepcopy(n)))))
        elif isinstance(n,ast.ClassDef) and n.name in sources[file]:
            node=copy.deepcopy(n);run=next(x for x in node.body if isinstance(x,ast.FunctionDef) and x.name=='run')
            if n.name=='ToolsTextQRTextEntryView':
                # CPython raw_unicode_escape/unicode_escape round trip: only \uXXXX
                # escapes are interpreted, invalid ones keep the typed text.
                tries=[x for x in run.body if isinstance(x,ast.Try)];assert len(tries)==1
                run.body[run.body.index(tries[0])]=ast.parse('self.textToEncode=_dependency("%s","text_unescape")(ret_dict["textToEncode"])'%S).body[0]
            if n.name=='ToolsPasswordSaveView':
                assigns=[x for x in run.body if isinstance(x,ast.Assign) and ast.unparse(x)=='button_data = [show_qr, seedkeeper]'];assert len(assigns)==1
                assigns[0].value=ast.parse('[show_qr]',mode='eval').body
                tail=[x for x in run.body if isinstance(x,ast.If) and '_save_password_to_seedkeeper' in ast.unparse(x.test)];assert len(tail)==1
                run.body[run.body.index(tail[0])]=ast.parse('raise RuntimeError("Unexpected password save option")').body[0]
            if n.name=='ToolsPasswordGenerateView':
                clears=[x for x in ast.walk(run) if isinstance(x,ast.If) and ast.unparse(x.test)=='self.entropy_source == PASSWORD_ENTROPY_CAMERA']
                body=clears[0].body;old=[x for x in body if isinstance(x,ast.Assign) and ast.unparse(x.targets[0]).startswith('self.controller.image_entropy_')];assert len(old)==2
                i=body.index(old[0]);body[i:i+2]=ast.parse('_dependency("seedsigner_port.camera_entropy","clear_controller_images")(self.controller)').body
            nodes.append(ast.FunctionDef(name='_make_'+n.name,args=ast.arguments(posonlyargs=[],args=[],kwonlyargs=[],kw_defaults=[],defaults=[]),body=[port.visit(Capitalize().visit(Underscore().visit(node))),ast.Return(value=ast.Name(id=n.name,ctx=ast.Load()))],decorator_list=[]))
    receipt['files'].setdefault('view_tools_extra.py',{'sources':{}})['sources'][file]=hashlib.sha256(raw).hexdigest()
# Module-level helper references to local classes/functions: functions are plain globals.
text='# Copyright2021 SeedSigner; MIT, see ../LICENSE.SeedSigner\n# Generated original Text QR / Password Generator Views; reviewed native boundaries.\nimport math\nfrom seedsigner_port.decode_platform import dependency as _dependency,FeatureUnavailable\nfrom seedsigner_port.password_support import capitalize as _capitalize\n'
text+=ast.unparse(ast.fix_missing_locations(ast.Module(body=constants+nodes,type_ignores=[])))+'\n'
fnames=sorted({f for fs in functions.values() for f in fs})
text+='_FACTORIES={'+','.join(repr(n)+':_make_'+n for n in all_classes)+'}\n_CACHE={}\n_FUNCS={'+','.join(repr(f)+':'+f for f in fnames)+'}\ndef _resolve(name):\n    if name in _FUNCS:return _FUNCS[name]\n    if name not in _CACHE:\n        if name not in _FACTORIES:raise AttributeError(name)\n        _CACHE[name]=_FACTORIES[name]()\n    return _CACHE[name]\ndef __getattr__(name):return _resolve(name)\n'
out=app/'view_tools_extra.py';out.write_text(text)
receipt['files']['view_tools_extra.py'].update(outputSha256=hashlib.sha256(out.read_bytes()).hexdigest(),classes=all_classes,changes=[
 'Text entry unescape: native \\uXXXX equivalent of the CPython raw_unicode_escape/unicode_escape round trip (MicroPython lacks both codecs and regex lookahead).',
 'Password save: Seedkeeper option omitted (smartcard support fixed disabled); Show as QR unchanged.',
 'Camera password entropy: owned native frames wiped via clear_controller_images instead of dropping references.',
 'str.capitalize (absent in MicroPython) -> password_support.capitalize.',
 'Dice entry uses the native keyboard for any source roll count (password counts differ from seed counts).'])
(root/'app/tools-extra-provenance.json').write_text(json.dumps(receipt,indent=2)+'\n')
print('Prepared Text QR / Password Generator Views')
