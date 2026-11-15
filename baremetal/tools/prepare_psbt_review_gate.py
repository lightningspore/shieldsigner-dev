# SPDX-License-Identifier: MIT
"""Compare full original review policy with port on the PUBLIC adversarial corpus.

Uses actual CPython embit0.8.0 before adding the native app directory. Native
firmware gate output is generated, never run by this host-only preparation tool.
"""
import ast,base64,dataclasses,hashlib,importlib.metadata,io,json,logging,os,sys,time,types,typing
from pathlib import Path
from embit import bip32,bip39,psbt,script,ec,hashes
from embit.base import EmbitError
from embit.psbt import PSBT,DerivationPath,InputScope,OutputScope
from embit.ec import PublicKey
from embit.finalizer import finalize_psbt
assert importlib.metadata.version('embit')=='0.8.0'
root=Path(__file__).resolve().parents[1];repo=root.parent
appsrc=repo/'dist/firmware/sources/lvgl/application'
sys.path.insert(0,str(root/'app'))
from seedsigner_port import psbt_parser as port
from seedsigner_port.psbt_framing import parse_psbt
from seedsigner_port.settings_schema import SettingsConstants as C
PUBLIC_TIME=1787616000
clock=types.SimpleNamespace(time=lambda:PUBLIC_TIME)
real_dependency=port._dependency
port._dependency=lambda module,name=None:clock if module=='seedsigner_port.psbt_clock' else real_dependency(module,name)
raw=(appsrc/'src/seedsigner/models/psbt_parser.py').read_bytes()
tree=ast.parse(raw)
namespace=dict(logging=logging,time=clock,hexlify=__import__('binascii').hexlify,psbt=psbt,script=script,ec=ec,bip32=bip32,hashes=hashes,EmbitError=EmbitError,NETWORKS=__import__('embit.networks',fromlist=['NETWORKS']).NETWORKS,PSBT=PSBT,DerivationPath=DerivationPath,InputScope=InputScope,OutputScope=OutputScope,PublicKey=PublicKey,BytesIO=io.BytesIO,List=typing.List,SettingsConstants=C)
original_nodes=[n for n in tree.body if not isinstance(n,(ast.Import,ast.ImportFrom)) or isinstance(n,ast.ImportFrom) and n.module=='__future__']
exec(compile(ast.Module(body=original_nodes,type_ignores=[]),'<unmodified original PSBTParser>','exec'),namespace)
Original=namespace['PSBTParser']
# Read the original public expectation table without importing the app's OS stack.
util=appsrc/'tests/psbt_suite_util.py';util_tree=ast.parse(util.read_bytes())
util_scope={'__file__':str(util),'os':os,'dataclass':dataclasses.dataclass,'field':dataclasses.field,'Optional':typing.Optional,'SettingsConstants':C}
selected=[]
for n in util_tree.body:
    if isinstance(n,ast.ClassDef):selected.append(n)
    elif isinstance(n,ast.Assign):
        selected.append(n)
        if any(isinstance(t,ast.Name) and t.id=='VECTORS' for t in n.targets):break
exec(compile(ast.Module(body=selected,type_ignores=[]),'<original public corpus table>','exec'),util_scope)
seed=bip39.mnemonic_to_seed('abandon '*11+'about')

def snapshot(model):
    return {'input_amount':model.input_amount,'fee_amount':model.fee_amount,'spend_amount':model.spend_amount,'change_amount':model.change_amount,'num_inputs':model.num_inputs,'policy':model.policy,'destination_addresses':model.destination_addresses,'destination_amounts':model.destination_amounts,'change_data':model.change_data,'op_return_amount':model.op_return_amount,'op_return_payloads':[b.hex() for b in model.op_return_payloads],'risk_warnings':sorted(model.risk_warnings),'locktime':model.locktime,'locktime_is_enforced':model.locktime_is_enforced,'is_high_fee':model.is_high_fee,'verified_input_prefixes':sorted(list(p) for p in model.verified_input_prefixes),'verified_max_input_index':model.verified_max_input_index,'fee_rate':model.fee_rate}

def evaluate(Parser,wire):
    try:
        p=parse_psbt(wire)
        model=Parser(p,root=bip32.HDKey.from_seed(seed),network=C.MAINNET,change_index_lookahead=100,max_fee_rate=120,reference_time=PUBLIC_TIME,block_anchor=(963408,PUBLIC_TIME))
        return {'status':'parsed','review':snapshot(model)}
    except Exception as e:
        if hasattr(e,'code'):return {'status':'reject','code':e.code}
        if isinstance(e,EmbitError):return {'status':'embit-reject'}
        raise

cases=[];signing=[]
for vector in util_scope['VECTORS']:
    data=Path(vector.path).read_bytes();wire=data if data.startswith(b'psbt\xff') else base64.b64decode(data.strip())
    expected=evaluate(Original,wire);actual=evaluate(port.PSBTParser,wire)
    assert actual==expected,(vector.name,expected,actual)
    if vector.expect in ('reject_parser','reject_framing'):assert actual=={'status':'reject','code':vector.reject_code},(vector.name,actual,vector.expect)
    elif vector.expect=='reject_embit':assert actual['status'] in ('embit-reject','reject'),(vector.name,actual)
    else:
        assert actual['status']=='parsed',(vector.name,actual)
        s=actual['review']
        if vector.input_amount is not None:assert s['input_amount']==vector.input_amount
        if vector.output_amount is not None:assert s['spend_amount']+s['change_amount']+s['op_return_amount']==vector.output_amount
        if vector.owned_outputs is not None:assert len(s['change_data'])==vector.owned_outputs
        assert set(vector.advisories)<=set(s['risk_warnings']),(vector.name,s['risk_warnings'],vector.advisories)
    needs_wall_clock=False
    if actual['status']=='parsed':
        p=parse_psbt(wire)
        needs_wall_clock=p.tx.locktime>=500000000 and any(v.sequence!=0xffffffff for v in p.tx.vin)
    cases.append({'name':vector.name,'wireHex':wire.hex(),'expected':actual,'needsWallClock':needs_wall_clock})
    if vector.category=='normal':
        p=parse_psbt(wire);before=p.serialize();key=bip32.HDKey.from_seed(seed)
        model=port.PSBTParser(p,root=key,network=C.MAINNET,change_index_lookahead=100,max_fee_rate=120)
        assert p.serialize()==before
        added=p.sign_with(key);assert added==len(p.inputs)
        for index,inp in enumerate(p.inputs):
            for pub,sig in inp.partial_sigs.items():assert pub.verify(ec.Signature.parse(sig[:-1]),p.sighash(index,sighash=sig[-1]))
        assert port.PSBTParser.sig_count(p)==len(p.inputs)
        final=finalize_psbt(p);assert final is not None
        trimmed=port.PSBTParser.trim(p)
        assert port.PSBTParser.sig_count(trimmed)==len(p.inputs)
        signing.append({'name':vector.name,'wireHex':wire.hex(),'signedSha256':hashlib.sha256(p.serialize()).hexdigest(),'trimmedSha256':hashlib.sha256(trimmed.serialize()).hexdigest(),'finalTxSha256':hashlib.sha256(final.serialize()).hexdigest(),'inputs':len(p.inputs)})
# Capture exact provenance for the independent host environment/results.
report={'sourceSha256':hashlib.sha256(raw).hexdigest(),'corpusTableSha256':hashlib.sha256(util.read_bytes()).hexdigest(),'cases':len(cases),'parsed':sum(c['expected']['status']=='parsed' for c in cases),'rejected':sum(c['expected']['status']!='parsed' for c in cases),'publicClock':PUBLIC_TIME,'provider':'Unmodified original PSBTParser and CPython embit0.8.0; original corpus target table','signingCases':len(signing),'scope':'Original review fields/refusal policy parity, deterministic public signatures independently verified, final full transaction and original trim. No UI/hardware/production-security qualification.','casesData':cases,'signingData':signing}
(root/'app/psbt-review-public-oracle.json').write_text(json.dumps(report,indent=2)+'\n')
code='''# SPDX-License-Identifier: MIT
# Generated PUBLIC transaction fixtures and original-source review/signing oracle.
from seedsigner_port.psbt_parser import PSBTParser,InvalidPSBTError
from seedsigner_port.decode_platform import FeatureUnavailable
from seedsigner_port.psbt_framing import parse_psbt
from seedsigner_port.settings_schema import SettingsConstants as C
from embit import bip32,bip39,ec
from embit.finalizer import finalize_psbt
from embit.base import EmbitError
import hashlib,gc,machine,time
cases='''+repr(cases)+'''
signing='''+repr(signing)+'''
seed=bip39.mnemonic_to_seed('abandon '*11+'about')
root=bip32.HDKey.from_seed(seed)
record=machine.last_reset();print('@@PSBT_REVIEW_RESET_BEFORE',record)
assert record is None or record['reason']==2
machine.clear_reset_record();machine.set_reset_marker(0x50534254)
def snapshot(model):
    return {'input_amount':model.input_amount,'fee_amount':model.fee_amount,'spend_amount':model.spend_amount,'change_amount':model.change_amount,'num_inputs':model.num_inputs,'policy':model.policy,'destination_addresses':model.destination_addresses,'destination_amounts':model.destination_amounts,'change_data':model.change_data,'op_return_amount':model.op_return_amount,'op_return_payloads':[b.hex() for b in model.op_return_payloads],'risk_warnings':sorted(model.risk_warnings),'locktime':model.locktime,'locktime_is_enforced':model.locktime_is_enforced,'is_high_fee':model.is_high_fee,'verified_input_prefixes':sorted(list(p) for p in model.verified_input_prefixes),'verified_max_input_index':model.verified_max_input_index,'fee_rate':model.fee_rate}
for number,case in enumerate(cases):
    if case['needsWallClock']:
        try:
            p=parse_psbt(bytes.fromhex(case['wireHex']))
            PSBTParser(p,root=root,network=C.MAINNET,change_index_lookahead=100,max_fee_rate=120,reference_time=1787616000,block_anchor=(963408,1787616000))
            assert False
        except FeatureUnavailable as error:assert 'wall-clock/date provider unavailable' in str(error)
        print('@@PASS original-psbt-clock-explicit-unavailable',number,case['name']);continue
    try:
        p=parse_psbt(bytes.fromhex(case['wireHex']))
        model=PSBTParser(p,root=root,network=C.MAINNET,change_index_lookahead=100,max_fee_rate=120,reference_time=1787616000,block_anchor=(963408,1787616000))
        result={'status':'parsed','review':snapshot(model)}
    except InvalidPSBTError as error:result={'status':'reject','code':error.code}
    except EmbitError:result={'status':'embit-reject'}
    assert result==case['expected'],(case['name'],result.get('status'),result.get('code'))
    gc.collect();print('@@PASS original-psbt-review-corpus',number,case['name'])
for number,case in enumerate(signing):
    p=parse_psbt(bytes.fromhex(case['wireHex']));before=p.serialize()
    model=PSBTParser(p,root=root,network=C.MAINNET,change_index_lookahead=100,max_fee_rate=120)
    assert p.serialize()==before
    assert p.sign_with(root)==case['inputs']
    for index,inp in enumerate(p.inputs):
        for pub,sig in inp.partial_sigs.items():assert pub.verify(ec.Signature.parse(sig[:-1]),p.sighash(index,sighash=sig[-1]))
    assert PSBTParser.sig_count(p)==case['inputs']
    assert hashlib.sha256(p.serialize()).hexdigest()==case['signedSha256']
    final=finalize_psbt(p);assert final is not None
    assert hashlib.sha256(final.serialize()).hexdigest()==case['finalTxSha256']
    trimmed=PSBTParser.trim(p);assert PSBTParser.sig_count(trimmed)==case['inputs']
    assert hashlib.sha256(trimmed.serialize()).hexdigest()==case['trimmedSha256']
    gc.collect();print('@@PASS original-psbt-normal-sign-verify-trim',number,case['name'])
assert machine.last_reset() is None
print('@@PASS original-psbt-review-signing-gate')
'''
(root/'micropython/psbt_review_gate.py').write_text(code)
report['nativeGateSha256']=hashlib.sha256(code.encode()).hexdigest()
report['nativeCases']=len(cases)
report['nativeReviewCases']=sum(not c['needsWallClock'] for c in cases)
report['nativeExplicitUnavailableClockCases']=[c['name'] for c in cases if c['needsWallClock']]
report['referenceLibrarySha256']={name:hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest() for name,module in [('bip32',bip32),('psbt',psbt),('script',script),('ec',ec),('secp256k1',ec.secp256k1)]}
(root/'app/psbt-review-public-oracle.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ('casesData','signingData')},indent=2))
