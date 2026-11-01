"""Verify public fixture before using it for LVGL transaction acceptance."""
import json,sys
sys.path.insert(0,'/opt/src')
from multisig_fixture import build
from seedsigner.models.psbt_parser import PSBTParser
from seedsigner.models.settings_definition import SettingsConstants as C
from embit.finalizer import finalize_psbt
seeds,roots,descriptor,psbt=build()
try:
 parser=PSBTParser(psbt,seeds[0],network=C.REGTEST,multisig_descriptor=descriptor)
 assert parser.is_multisig and len(psbt.inputs)==1 and len(psbt.outputs)==2
 assert PSBTParser.sig_count(psbt)==0
 added=psbt.sign_with(roots[0]);assert added==1 and PSBTParser.sig_count(psbt)==1
 assert finalize_psbt(psbt) is None
 added=psbt.sign_with(roots[1]);assert added==1 and PSBTParser.sig_count(psbt)==2
 tx=finalize_psbt(psbt);assert tx is not None
 assert [output.serialize() for output in tx.vout]==[output.serialize() for output in psbt.tx.vout]
 print(json.dumps(dict(passed=True,publicRegtestFixture=True,multisig=True,threshold=2,cosigners=3,inputCount=1,outputCount=2,oneSignatureInsufficient=True,twoSignaturesFinalizable=True,outputsUnchanged=True,physicalDisplay=False,uiQualified=False)),flush=True)
finally:
 for seed in seeds:seed.wipe()
