"""AST inventory of the actual pinned ShieldSigner screens and their call sites."""
import ast
import json
import re
import sys
from pathlib import Path
sys.path.insert(0,str(__import__("pathlib").Path(__file__).resolve().parent/"python"))
from contracts import SUPPORTED
from sources import fetch,DIST,HERE,LOCK
app=fetch('application')
screens=fetch('screens')
base=app/'src/seedsigner'
entries={}
for path in sorted(base.rglob('*.py')):
    tree=ast.parse(path.read_text())
    for node in tree.body:
        if isinstance(node,ast.ClassDef) and node.name.endswith('Screen'):
            annotations={n.target.id:ast.unparse(n.annotation) for n in node.body if isinstance(n,ast.AnnAssign) and isinstance(n.target,ast.Name)}
            entries[node.name]=dict(module=str(path.relative_to(base)),line=node.lineno,bases=[ast.unparse(b) for b in node.bases],fields=annotations,callSites=[])
for path in sorted((base/'views').rglob('*.py')):
    tree=ast.parse(path.read_text())
    for node in ast.walk(tree):
        if not isinstance(node,ast.Call): continue
        target=None
        if isinstance(node.func,ast.Attribute) and node.func.attr=='run_screen':
            if node.args:target=ast.unparse(node.args[0]).split('.')[-1]
            else:
                target=next((ast.unparse(k.value).split('.')[-1] for k in node.keywords if k.arg=='Screen_cls'),None)
        else:target=ast.unparse(node.func).split('.')[-1]
        if target in entries:entries[target]['callSites'].append(dict(module=str(path.relative_to(base)),line=node.lineno,arguments=[k.arg for k in node.keywords]))
corpus=sorted(p.stem for p in (screens/'components/seedsigner/screens').glob('*_screen.cpp'))
for name,row in entries.items():
    snake=re.sub(r'(?<=[a-z0-9])(?=[A-Z])','_',name)
    snake=re.sub(r'(?<=[A-Z])(?=[A-Z][a-z])','_',snake).lower()
    row['candidate']=snake if snake in corpus else None
    row['status']='adapter implemented; flow unverified' if name in SUPPORTED else ('native lifecycle adapter; see scoped validation' if name=='ScreensaverScreen' else 'unmigrated')
# Audited at the pinned sources: these are infrastructure classes, with no
# direct construction/run_screen call resolved in Views. This is not full-flow
# coverage and does not erase their inherited lifecycle requirements.
for name in ('BaseScreen','BaseTopNavScreen','LogoScreen'):
    if entries[name]['callSites']:raise RuntimeError('Infrastructure class gained a direct View call: '+name)
    entries[name]['status']='inherited infrastructure; concrete adapters own rendering/lifecycle; no direct static View call'
entries['LargeButtonScreen']['status']='grid adapter; scoped ARM navigation/tap/hold passed; custom styles incomplete'
entries['MainMenuScreen']['status']='navigation/recovery-hold/battery adapters; scoped ARM/Controller display switching passed with LCD fixtures; physical battery and alternate LCD qualification incomplete'
bip85_evidence=['validation/controller-bip85-'+str(count)+'-arm.json' for count in (12,18,24)]
for evidence in bip85_evidence:
    if not json.loads((HERE/evidence).read_text()).get('passed'):raise ValueError('BIP85 evidence is not a pass')
for name in ('SeedBIP85SelectChildIndexScreen','SeedWordsScreen','SeedWordsBackupTestPromptScreen','SeedFinalizeScreen','SeedOptionsScreen'):
    entries[name]['scopedEvidence']=list(bip85_evidence)
    entries[name]['status']='adapter implemented; BIP85 child-index-0 review/quiz/finalize passed for 12/18/24 words on LCD; other flows not qualified by these checks'
slip39_evidence=['validation/controller-slip39-'+str(count)+'-arm.json' for count in (20,33)]
for evidence in slip39_evidence:
    if not json.loads((HERE/evidence).read_text()).get('passed'):raise ValueError('SLIP39 evidence is not a pass')
for name in ('ScanScreen','SeedWordsScreen','SeedWordsBackupTestPromptScreen','SeedFinalizeScreen','SeedOptionsScreen'):
    entries[name].setdefault('scopedEvidence',[]).extend(slip39_evidence)
    entries[name]['status']=entries[name]['status'].replace('adapter implemented; flow unverified','adapter implemented')+'; SLIP39 2-of-2 QR recovery/review/quiz passed for 20/33-word shares on LCD; synthetic frames, not optical qualification'
encrypted_evidence=['validation/controller-camera-encrypted-cbc-v1-arm.json','validation/controller-encrypted-ecb-v1-arm.json','validation/controller-encrypted-ecb-arm.json']
for evidence in encrypted_evidence:
    if not json.loads((HERE/evidence).read_text()).get('passed'):raise ValueError('Encrypted QR evidence is not a pass')
for name in ('SeedEncryptedQRReviewMnemonicIDScreen','SeedEncryptedQRTranscribeModePromptScreen','QRDisplayScreen'):
    entries[name].setdefault('scopedEvidence',[]).extend(encrypted_evidence)
    entries[name]['status']=entries[name]['status'].replace('adapter implemented; flow unverified','adapter implemented')+'; Controller encrypted export and original-View decrypt passed for strict KEF 0/1/6 fixtures; not optical import qualification'
grid_evidence='validation/grid-color-arm.json'
if not json.loads((HERE/grid_evidence).read_text()).get('passed'):raise ValueError('Grid style evidence is not a pass')
for name in ('LargeButtonScreen','MainMenuScreen'):
    entries[name].setdefault('scopedEvidence',[]).append(grid_evidence)
    entries[name]['status']+='; default/custom selected-color pixels and Right/Select passed on LCD; arbitrary custom fonts remain unqualified'
passphrase_evidence='validation/controller-passphrase-arm.json'
if not json.loads((HERE/passphrase_evidence).read_text()).get('passed'):raise ValueError('Passphrase evidence is not a pass')
for name in ('SeedAddPassphraseScreen','SeedReviewPassphraseScreen','SeedFinalizeScreen','SeedOptionsScreen','ScanScreen'):
    entries[name].setdefault('scopedEvidence',[]).append(passphrase_evidence)
    entries[name]['status']=entries[name]['status'].replace('adapter implemented; flow unverified','adapter implemented')+'; full Controller seed/passphrase scan, edit/review/save and finalize passed with public NUL/Unicode fixture; synthetic QR input'
address_evidence=['validation/controller-address-'+branch+'-arm.json' for branch in ('receive','change')]
for evidence in address_evidence:
    if not json.loads((HERE/evidence).read_text()).get('passed'):raise ValueError('Address evidence is not a pass')
for name in ('SeedSelectSeedScreen','SeedAddressVerificationScreen','SeedAddressVerificationSuccessScreen'):
    entries[name].setdefault('scopedEvidence',[]).extend(address_evidence)
    entries[name]['status']='adapter implemented; full Controller imported-seed address verification passed for native-segwit receive/change index 7; other scripts and expanded search not qualified by these checks'
wallet_evidence='validation/controller-wallet-export-arm.json'
if not json.loads((HERE/wallet_evidence).read_text()).get('passed'):raise ValueError('Wallet export evidence is not a pass')
for name in ('SeedExportXpubDetailsScreen','QRDisplayScreen','LargeIconStatusScreen'):
    entries[name].setdefault('scopedEvidence',[]).append(wallet_evidence)
    entries[name]['status']=entries[name]['status'].replace('adapter implemented; flow unverified','adapter implemented')+'; full Controller static native-segwit xpub export/pixel decode/address handshake passed; other export formats not qualified by this receipt'
report=dict(application=LOCK['application'],screens=LOCK['screens'],screenCount=len(entries),viewCallCount=sum(len(r['callSites']) for r in entries.values()),upstreamScreenCount=len(corpus),upstreamScreens=corpus,screensByClass=entries)
DIST.mkdir(parents=True,exist_ok=True)
(DIST/'inventory.json').write_text(json.dumps(report,indent=2)+'\n')
lines=['# Migration coverage inventory','',f"Pinned app: `{LOCK['application']['commit']}`.",'',f'{len(entries)} screen classes; {report["viewCallCount"]} statically resolved view calls; {len(corpus)} reusable upstream LVGL screen builders.','', 'Candidate matches are names only, not compatibility or migration claims. Top-level Screen classes across the application are included; nested classes and dynamic calls require separate auditing. Scoped validation receipts remain separate from adapter status.','', 'Evidence links below are historical scoped receipts with exact source/binary hashes, not qualification of every flow using a shared screen.','', '| App screen | Upstream candidate | Status | Scoped evidence |','|---|---|---|---|']
for name,row in sorted(entries.items()): lines.append(f'| {name} | {row["candidate"] or "needs explicit mapping"} | {row["status"]} | '+', '.join('['+Path(item).stem+']('+item+')' for item in row.get('scopedEvidence',[]))+' |')
(HERE/'COVERAGE.md').write_text('\n'.join(lines)+'\n')
print(f'{len(entries)} classes, {report["viewCallCount"]} view calls, {len(corpus)} upstream builders')
