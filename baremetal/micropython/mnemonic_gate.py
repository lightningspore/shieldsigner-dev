# Public fixtures only. Actual source algorithms, frozen storage and native KDF.
import shamir_mnemonic as sm
from shamir_mnemonic import wordlist,recovery,shamir
from seedsigner_port import aezeed
from seedsigner_port.seed import Seed,AezeedSeed
from seedsigner_port.decode_qr import DecodeQR,DecodeQRStatus
from seedsigner_port.decode_platform import FeatureUnavailable
from seedsigner_port.qr_type import QRType
from seedsigner_port.settings_schema import SettingsConstants
import importlib
import hashlib
import camera
import gc
assert importlib.import_module('shamir_mnemonic.wordlist') is wordlist
assert importlib.import_module('.wordlist','shamir_mnemonic') is wordlist
assert importlib.import_module('..wordlist','shamir_mnemonic.share') is wordlist
assert len(wordlist.WORDLIST)==1024
assert hashlib.sha256(('\n'.join(wordlist.WORDLIST)+'\n').encode()).hexdigest()=='bcc4555340332d169718aed8bf31dd9d5248cb7da6e5d355140ef4f1e601eec3'
baseline=camera.settings()['rust_heap_bytes']
phrases=['duckling enlarge academic academic agency result length solution fridge kidney coal piece deal husband erode duke ajar critical decision keyboard']
expected='bb54aac4b89dc868ba37d9cc21b2cece'
if expected:
    result=sm.combine_mnemonics(phrases,b'TREZOR')
    assert result.hex()==expected
    state=recovery.RecoveryState()
    for phrase in phrases:
        share=sm.Share.from_mnemonic(phrase)
        assert share.mnemonic()==phrase
        scanned=DecodeQR()
        assert scanned.add_data(phrase)==DecodeQRStatus.COMPLETE
        assert scanned.is_slip39_share and scanned.get_slip39_share()==phrase
        assert hash(share)==hash(sm.Share.from_mnemonic(phrase))
        assert len({share,sm.Share.from_mnemonic(phrase)})==1
        assert share!=tuple(share)
        parameters=share.common_parameters()
        assert parameters==tuple(parameters) and hash(parameters)==hash(tuple(parameters))
        for field in ('identifier','new_field'):
            try:setattr(parameters,field,99);assert False
            except AttributeError:pass
        for field in ('identifier','new_field'):
            try:setattr(share,field,1);assert False
            except AttributeError:pass
        state.add_share(share)
    assert state.is_complete() and state.recover(b'TREZOR').hex()==expected
    assert len(state.group_prefix(share.group_index).split())==3
else:
    try:
        sm.combine_mnemonics(phrases,b'TREZOR')
        assert False
    except sm.MnemonicError:pass
for i in range(2):gc.collect()
phrases=['duckling enlarge academic academic agency result length solution fridge kidney coal piece deal husband erode duke ajar critical decision kidney']
expected=''
if expected:
    result=sm.combine_mnemonics(phrases,b'TREZOR')
    assert result.hex()==expected
    state=recovery.RecoveryState()
    for phrase in phrases:
        share=sm.Share.from_mnemonic(phrase)
        assert share.mnemonic()==phrase
        scanned=DecodeQR()
        assert scanned.add_data(phrase)==DecodeQRStatus.COMPLETE
        assert scanned.is_slip39_share and scanned.get_slip39_share()==phrase
        assert hash(share)==hash(sm.Share.from_mnemonic(phrase))
        assert len({share,sm.Share.from_mnemonic(phrase)})==1
        assert share!=tuple(share)
        parameters=share.common_parameters()
        assert parameters==tuple(parameters) and hash(parameters)==hash(tuple(parameters))
        for field in ('identifier','new_field'):
            try:setattr(parameters,field,99);assert False
            except AttributeError:pass
        for field in ('identifier','new_field'):
            try:setattr(share,field,1);assert False
            except AttributeError:pass
        state.add_share(share)
    assert state.is_complete() and state.recover(b'TREZOR').hex()==expected
    assert len(state.group_prefix(share.group_index).split())==3
else:
    try:
        sm.combine_mnemonics(phrases,b'TREZOR')
        assert False
    except sm.MnemonicError:pass
for i in range(2):gc.collect()
phrases=['duckling enlarge academic academic email result length solution fridge kidney coal piece deal husband erode duke ajar music cargo fitness']
expected=''
if expected:
    result=sm.combine_mnemonics(phrases,b'TREZOR')
    assert result.hex()==expected
    state=recovery.RecoveryState()
    for phrase in phrases:
        share=sm.Share.from_mnemonic(phrase)
        assert share.mnemonic()==phrase
        scanned=DecodeQR()
        assert scanned.add_data(phrase)==DecodeQRStatus.COMPLETE
        assert scanned.is_slip39_share and scanned.get_slip39_share()==phrase
        assert hash(share)==hash(sm.Share.from_mnemonic(phrase))
        assert len({share,sm.Share.from_mnemonic(phrase)})==1
        assert share!=tuple(share)
        parameters=share.common_parameters()
        assert parameters==tuple(parameters) and hash(parameters)==hash(tuple(parameters))
        for field in ('identifier','new_field'):
            try:setattr(parameters,field,99);assert False
            except AttributeError:pass
        for field in ('identifier','new_field'):
            try:setattr(share,field,1);assert False
            except AttributeError:pass
        state.add_share(share)
    assert state.is_complete() and state.recover(b'TREZOR').hex()==expected
    assert len(state.group_prefix(share.group_index).split())==3
else:
    try:
        sm.combine_mnemonics(phrases,b'TREZOR')
        assert False
    except sm.MnemonicError:pass
for i in range(2):gc.collect()
phrases=['shadow pistol academic always adequate wildlife fancy gross oasis cylinder mustang wrist rescue view short owner flip making coding armed', 'shadow pistol academic acid actress prayer class unknown daughter sweater depict flip twice unkind craft early superior advocate guest smoking']
expected='b43ceb7e57a0ea8766221624d01b0864'
if expected:
    result=sm.combine_mnemonics(phrases,b'TREZOR')
    assert result.hex()==expected
    state=recovery.RecoveryState()
    for phrase in phrases:
        share=sm.Share.from_mnemonic(phrase)
        assert share.mnemonic()==phrase
        scanned=DecodeQR()
        assert scanned.add_data(phrase)==DecodeQRStatus.COMPLETE
        assert scanned.is_slip39_share and scanned.get_slip39_share()==phrase
        assert hash(share)==hash(sm.Share.from_mnemonic(phrase))
        assert len({share,sm.Share.from_mnemonic(phrase)})==1
        assert share!=tuple(share)
        parameters=share.common_parameters()
        assert parameters==tuple(parameters) and hash(parameters)==hash(tuple(parameters))
        for field in ('identifier','new_field'):
            try:setattr(parameters,field,99);assert False
            except AttributeError:pass
        for field in ('identifier','new_field'):
            try:setattr(share,field,1);assert False
            except AttributeError:pass
        state.add_share(share)
    assert state.is_complete() and state.recover(b'TREZOR').hex()==expected
    assert len(state.group_prefix(share.group_index).split())==3
else:
    try:
        sm.combine_mnemonics(phrases,b'TREZOR')
        assert False
    except sm.MnemonicError:pass
for i in range(2):gc.collect()
phrases=['shadow pistol academic always adequate wildlife fancy gross oasis cylinder mustang wrist rescue view short owner flip making coding armed']
expected=''
if expected:
    result=sm.combine_mnemonics(phrases,b'TREZOR')
    assert result.hex()==expected
    state=recovery.RecoveryState()
    for phrase in phrases:
        share=sm.Share.from_mnemonic(phrase)
        assert share.mnemonic()==phrase
        scanned=DecodeQR()
        assert scanned.add_data(phrase)==DecodeQRStatus.COMPLETE
        assert scanned.is_slip39_share and scanned.get_slip39_share()==phrase
        assert hash(share)==hash(sm.Share.from_mnemonic(phrase))
        assert len({share,sm.Share.from_mnemonic(phrase)})==1
        assert share!=tuple(share)
        parameters=share.common_parameters()
        assert parameters==tuple(parameters) and hash(parameters)==hash(tuple(parameters))
        for field in ('identifier','new_field'):
            try:setattr(parameters,field,99);assert False
            except AttributeError:pass
        for field in ('identifier','new_field'):
            try:setattr(share,field,1);assert False
            except AttributeError:pass
        state.add_share(share)
    assert state.is_complete() and state.recover(b'TREZOR').hex()==expected
    assert len(state.group_prefix(share.group_index).split())==3
else:
    try:
        sm.combine_mnemonics(phrases,b'TREZOR')
        assert False
    except sm.MnemonicError:pass
for i in range(2):gc.collect()
phrases=['adequate smoking academic acid debut wine petition glen cluster slow rhyme slow simple epidemic rumor junk tracks treat olympic tolerate', 'adequate stay academic agency agency formal party ting frequent learn upstairs remember smear leaf damage anatomy ladle market hush corner']
expected=''
if expected:
    result=sm.combine_mnemonics(phrases,b'TREZOR')
    assert result.hex()==expected
    state=recovery.RecoveryState()
    for phrase in phrases:
        share=sm.Share.from_mnemonic(phrase)
        assert share.mnemonic()==phrase
        scanned=DecodeQR()
        assert scanned.add_data(phrase)==DecodeQRStatus.COMPLETE
        assert scanned.is_slip39_share and scanned.get_slip39_share()==phrase
        assert hash(share)==hash(sm.Share.from_mnemonic(phrase))
        assert len({share,sm.Share.from_mnemonic(phrase)})==1
        assert share!=tuple(share)
        parameters=share.common_parameters()
        assert parameters==tuple(parameters) and hash(parameters)==hash(tuple(parameters))
        for field in ('identifier','new_field'):
            try:setattr(parameters,field,99);assert False
            except AttributeError:pass
        for field in ('identifier','new_field'):
            try:setattr(share,field,1);assert False
            except AttributeError:pass
        state.add_share(share)
    assert state.is_complete() and state.recover(b'TREZOR').hex()==expected
    assert len(state.group_prefix(share.group_index).split())==3
else:
    try:
        sm.combine_mnemonics(phrases,b'TREZOR')
        assert False
    except sm.MnemonicError:pass
for i in range(2):gc.collect()
phrases=['peasant leaves academic acid desert exact olympic math alive axle trial tackle drug deny decent smear dominant desert bucket remind', 'peasant leader academic agency cultural blessing percent network envelope medal junk primary human pumps jacket fragment payroll ticket evoke voice']
expected=''
if expected:
    result=sm.combine_mnemonics(phrases,b'TREZOR')
    assert result.hex()==expected
    state=recovery.RecoveryState()
    for phrase in phrases:
        share=sm.Share.from_mnemonic(phrase)
        assert share.mnemonic()==phrase
        scanned=DecodeQR()
        assert scanned.add_data(phrase)==DecodeQRStatus.COMPLETE
        assert scanned.is_slip39_share and scanned.get_slip39_share()==phrase
        assert hash(share)==hash(sm.Share.from_mnemonic(phrase))
        assert len({share,sm.Share.from_mnemonic(phrase)})==1
        assert share!=tuple(share)
        parameters=share.common_parameters()
        assert parameters==tuple(parameters) and hash(parameters)==hash(tuple(parameters))
        for field in ('identifier','new_field'):
            try:setattr(parameters,field,99);assert False
            except AttributeError:pass
        for field in ('identifier','new_field'):
            try:setattr(share,field,1);assert False
            except AttributeError:pass
        state.add_share(share)
    assert state.is_complete() and state.recover(b'TREZOR').hex()==expected
    assert len(state.group_prefix(share.group_index).split())==3
else:
    try:
        sm.combine_mnemonics(phrases,b'TREZOR')
        assert False
    except sm.MnemonicError:pass
for i in range(2):gc.collect()
phrases=['liberty category beard echo animal fawn temple briefing math username various wolf aviation fancy visual holy thunder yelp helpful payment', 'liberty category beard email beyond should fancy romp founder easel pink holy hairy romp loyalty material victim owner toxic custody', 'liberty category academic easy being hazard crush diminish oral lizard reaction cluster force dilemma deploy force club veteran expect photo']
expected=''
if expected:
    result=sm.combine_mnemonics(phrases,b'TREZOR')
    assert result.hex()==expected
    state=recovery.RecoveryState()
    for phrase in phrases:
        share=sm.Share.from_mnemonic(phrase)
        assert share.mnemonic()==phrase
        scanned=DecodeQR()
        assert scanned.add_data(phrase)==DecodeQRStatus.COMPLETE
        assert scanned.is_slip39_share and scanned.get_slip39_share()==phrase
        assert hash(share)==hash(sm.Share.from_mnemonic(phrase))
        assert len({share,sm.Share.from_mnemonic(phrase)})==1
        assert share!=tuple(share)
        parameters=share.common_parameters()
        assert parameters==tuple(parameters) and hash(parameters)==hash(tuple(parameters))
        for field in ('identifier','new_field'):
            try:setattr(parameters,field,99);assert False
            except AttributeError:pass
        for field in ('identifier','new_field'):
            try:setattr(share,field,1);assert False
            except AttributeError:pass
        state.add_share(share)
    assert state.is_complete() and state.recover(b'TREZOR').hex()==expected
    assert len(state.group_prefix(share.group_index).split())==3
else:
    try:
        sm.combine_mnemonics(phrases,b'TREZOR')
        assert False
    except sm.MnemonicError:pass
for i in range(2):gc.collect()
phrases=['average senior academic leaf broken teacher expect surface hour capture obesity desire negative dynamic dominant pistol mineral mailman iris aide', 'average senior academic agency curious pants blimp spew clothes slice script dress wrap firm shaft regular slavery negative theater roster']
expected=''
if expected:
    result=sm.combine_mnemonics(phrases,b'TREZOR')
    assert result.hex()==expected
    state=recovery.RecoveryState()
    for phrase in phrases:
        share=sm.Share.from_mnemonic(phrase)
        assert share.mnemonic()==phrase
        scanned=DecodeQR()
        assert scanned.add_data(phrase)==DecodeQRStatus.COMPLETE
        assert scanned.is_slip39_share and scanned.get_slip39_share()==phrase
        assert hash(share)==hash(sm.Share.from_mnemonic(phrase))
        assert len({share,sm.Share.from_mnemonic(phrase)})==1
        assert share!=tuple(share)
        parameters=share.common_parameters()
        assert parameters==tuple(parameters) and hash(parameters)==hash(tuple(parameters))
        for field in ('identifier','new_field'):
            try:setattr(parameters,field,99);assert False
            except AttributeError:pass
        for field in ('identifier','new_field'):
            try:setattr(share,field,1);assert False
            except AttributeError:pass
        state.add_share(share)
    assert state.is_complete() and state.recover(b'TREZOR').hex()==expected
    assert len(state.group_prefix(share.group_index).split())==3
else:
    try:
        sm.combine_mnemonics(phrases,b'TREZOR')
        assert False
    except sm.MnemonicError:pass
for i in range(2):gc.collect()
phrases=['music husband acrobat acid artist finance center either graduate swimming object bike medical clothes station aspect spider maiden bulb welcome', 'music husband acrobat agency advance hunting bike corner density careful material civil evil tactics remind hawk discuss hobo voice rainbow', 'music husband beard academic black tricycle clock mayor estimate level photo episode exclude ecology papa source amazing salt verify divorce']
expected=''
if expected:
    result=sm.combine_mnemonics(phrases,b'TREZOR')
    assert result.hex()==expected
    state=recovery.RecoveryState()
    for phrase in phrases:
        share=sm.Share.from_mnemonic(phrase)
        assert share.mnemonic()==phrase
        scanned=DecodeQR()
        assert scanned.add_data(phrase)==DecodeQRStatus.COMPLETE
        assert scanned.is_slip39_share and scanned.get_slip39_share()==phrase
        assert hash(share)==hash(sm.Share.from_mnemonic(phrase))
        assert len({share,sm.Share.from_mnemonic(phrase)})==1
        assert share!=tuple(share)
        parameters=share.common_parameters()
        assert parameters==tuple(parameters) and hash(parameters)==hash(tuple(parameters))
        for field in ('identifier','new_field'):
            try:setattr(parameters,field,99);assert False
            except AttributeError:pass
        for field in ('identifier','new_field'):
            try:setattr(share,field,1);assert False
            except AttributeError:pass
        state.add_share(share)
    assert state.is_complete() and state.recover(b'TREZOR').hex()==expected
    assert len(state.group_prefix(share.group_index).split())==3
else:
    try:
        sm.combine_mnemonics(phrases,b'TREZOR')
        assert False
    except sm.MnemonicError:pass
for i in range(2):gc.collect()
phrases=['device stay academic always dive coal antenna adult black exceed stadium herald advance soldier busy dryer daughter evaluate minister laser', 'device stay academic always dwarf afraid robin gravity crunch adjust soul branch walnut coastal dream costume scholar mortgage mountain pumps']
expected=''
if expected:
    result=sm.combine_mnemonics(phrases,b'TREZOR')
    assert result.hex()==expected
    state=recovery.RecoveryState()
    for phrase in phrases:
        share=sm.Share.from_mnemonic(phrase)
        assert share.mnemonic()==phrase
        scanned=DecodeQR()
        assert scanned.add_data(phrase)==DecodeQRStatus.COMPLETE
        assert scanned.is_slip39_share and scanned.get_slip39_share()==phrase
        assert hash(share)==hash(sm.Share.from_mnemonic(phrase))
        assert len({share,sm.Share.from_mnemonic(phrase)})==1
        assert share!=tuple(share)
        parameters=share.common_parameters()
        assert parameters==tuple(parameters) and hash(parameters)==hash(tuple(parameters))
        for field in ('identifier','new_field'):
            try:setattr(parameters,field,99);assert False
            except AttributeError:pass
        for field in ('identifier','new_field'):
            try:setattr(share,field,1);assert False
            except AttributeError:pass
        state.add_share(share)
    assert state.is_complete() and state.recover(b'TREZOR').hex()==expected
    assert len(state.group_prefix(share.group_index).split())==3
else:
    try:
        sm.combine_mnemonics(phrases,b'TREZOR')
        assert False
    except sm.MnemonicError:pass
for i in range(2):gc.collect()
phrases=['hour painting academic academic device formal evoke guitar random modern justice filter withdraw trouble identify mailman insect general cover oven', 'hour painting academic agency artist again daisy capital beaver fiber much enjoy suitable symbolic identify photo editor romp float echo']
expected=''
if expected:
    result=sm.combine_mnemonics(phrases,b'TREZOR')
    assert result.hex()==expected
    state=recovery.RecoveryState()
    for phrase in phrases:
        share=sm.Share.from_mnemonic(phrase)
        assert share.mnemonic()==phrase
        scanned=DecodeQR()
        assert scanned.add_data(phrase)==DecodeQRStatus.COMPLETE
        assert scanned.is_slip39_share and scanned.get_slip39_share()==phrase
        assert hash(share)==hash(sm.Share.from_mnemonic(phrase))
        assert len({share,sm.Share.from_mnemonic(phrase)})==1
        assert share!=tuple(share)
        parameters=share.common_parameters()
        assert parameters==tuple(parameters) and hash(parameters)==hash(tuple(parameters))
        for field in ('identifier','new_field'):
            try:setattr(parameters,field,99);assert False
            except AttributeError:pass
        for field in ('identifier','new_field'):
            try:setattr(share,field,1);assert False
            except AttributeError:pass
        state.add_share(share)
    assert state.is_complete() and state.recover(b'TREZOR').hex()==expected
    assert len(state.group_prefix(share.group_index).split())==3
else:
    try:
        sm.combine_mnemonics(phrases,b'TREZOR')
        assert False
    except sm.MnemonicError:pass
for i in range(2):gc.collect()
phrases=['guilt walnut academic acid deliver remove equip listen vampire tactics nylon rhythm failure husband fatigue alive blind enemy teaspoon rebound', 'guilt walnut academic agency brave hamster hobo declare herd taste alpha slim criminal mild arcade formal romp branch pink ambition']
expected=''
if expected:
    result=sm.combine_mnemonics(phrases,b'TREZOR')
    assert result.hex()==expected
    state=recovery.RecoveryState()
    for phrase in phrases:
        share=sm.Share.from_mnemonic(phrase)
        assert share.mnemonic()==phrase
        scanned=DecodeQR()
        assert scanned.add_data(phrase)==DecodeQRStatus.COMPLETE
        assert scanned.is_slip39_share and scanned.get_slip39_share()==phrase
        assert hash(share)==hash(sm.Share.from_mnemonic(phrase))
        assert len({share,sm.Share.from_mnemonic(phrase)})==1
        assert share!=tuple(share)
        parameters=share.common_parameters()
        assert parameters==tuple(parameters) and hash(parameters)==hash(tuple(parameters))
        for field in ('identifier','new_field'):
            try:setattr(parameters,field,99);assert False
            except AttributeError:pass
        for field in ('identifier','new_field'):
            try:setattr(share,field,1);assert False
            except AttributeError:pass
        state.add_share(share)
    assert state.is_complete() and state.recover(b'TREZOR').hex()==expected
    assert len(state.group_prefix(share.group_index).split())==3
else:
    try:
        sm.combine_mnemonics(phrases,b'TREZOR')
        assert False
    except sm.MnemonicError:pass
for i in range(2):gc.collect()
phrases=['eraser senior beard romp adorn nuclear spill corner cradle style ancient family general leader ambition exchange unusual garlic promise voice']
expected=''
if expected:
    result=sm.combine_mnemonics(phrases,b'TREZOR')
    assert result.hex()==expected
    state=recovery.RecoveryState()
    for phrase in phrases:
        share=sm.Share.from_mnemonic(phrase)
        assert share.mnemonic()==phrase
        scanned=DecodeQR()
        assert scanned.add_data(phrase)==DecodeQRStatus.COMPLETE
        assert scanned.is_slip39_share and scanned.get_slip39_share()==phrase
        assert hash(share)==hash(sm.Share.from_mnemonic(phrase))
        assert len({share,sm.Share.from_mnemonic(phrase)})==1
        assert share!=tuple(share)
        parameters=share.common_parameters()
        assert parameters==tuple(parameters) and hash(parameters)==hash(tuple(parameters))
        for field in ('identifier','new_field'):
            try:setattr(parameters,field,99);assert False
            except AttributeError:pass
        for field in ('identifier','new_field'):
            try:setattr(share,field,1);assert False
            except AttributeError:pass
        state.add_share(share)
    assert state.is_complete() and state.recover(b'TREZOR').hex()==expected
    assert len(state.group_prefix(share.group_index).split())==3
else:
    try:
        sm.combine_mnemonics(phrases,b'TREZOR')
        assert False
    except sm.MnemonicError:pass
for i in range(2):gc.collect()
phrases=['eraser senior decision scared cargo theory device idea deliver modify curly include pancake both news skin realize vitamins away join', 'eraser senior decision roster beard treat identify grumpy salt index fake aviation theater cubic bike cause research dragon emphasis counter']
expected=''
if expected:
    result=sm.combine_mnemonics(phrases,b'TREZOR')
    assert result.hex()==expected
    state=recovery.RecoveryState()
    for phrase in phrases:
        share=sm.Share.from_mnemonic(phrase)
        assert share.mnemonic()==phrase
        scanned=DecodeQR()
        assert scanned.add_data(phrase)==DecodeQRStatus.COMPLETE
        assert scanned.is_slip39_share and scanned.get_slip39_share()==phrase
        assert hash(share)==hash(sm.Share.from_mnemonic(phrase))
        assert len({share,sm.Share.from_mnemonic(phrase)})==1
        assert share!=tuple(share)
        parameters=share.common_parameters()
        assert parameters==tuple(parameters) and hash(parameters)==hash(tuple(parameters))
        for field in ('identifier','new_field'):
            try:setattr(parameters,field,99);assert False
            except AttributeError:pass
        for field in ('identifier','new_field'):
            try:setattr(share,field,1);assert False
            except AttributeError:pass
        state.add_share(share)
    assert state.is_complete() and state.recover(b'TREZOR').hex()==expected
    assert len(state.group_prefix(share.group_index).split())==3
else:
    try:
        sm.combine_mnemonics(phrases,b'TREZOR')
        assert False
    except sm.MnemonicError:pass
for i in range(2):gc.collect()
phrases=['eraser senior decision shadow artist work morning estate greatest pipeline plan ting petition forget hormone flexible general goat admit surface', 'eraser senior beard romp adorn nuclear spill corner cradle style ancient family general leader ambition exchange unusual garlic promise voice']
expected=''
if expected:
    result=sm.combine_mnemonics(phrases,b'TREZOR')
    assert result.hex()==expected
    state=recovery.RecoveryState()
    for phrase in phrases:
        share=sm.Share.from_mnemonic(phrase)
        assert share.mnemonic()==phrase
        scanned=DecodeQR()
        assert scanned.add_data(phrase)==DecodeQRStatus.COMPLETE
        assert scanned.is_slip39_share and scanned.get_slip39_share()==phrase
        assert hash(share)==hash(sm.Share.from_mnemonic(phrase))
        assert len({share,sm.Share.from_mnemonic(phrase)})==1
        assert share!=tuple(share)
        parameters=share.common_parameters()
        assert parameters==tuple(parameters) and hash(parameters)==hash(tuple(parameters))
        for field in ('identifier','new_field'):
            try:setattr(parameters,field,99);assert False
            except AttributeError:pass
        for field in ('identifier','new_field'):
            try:setattr(share,field,1);assert False
            except AttributeError:pass
        state.add_share(share)
    assert state.is_complete() and state.recover(b'TREZOR').hex()==expected
    assert len(state.group_prefix(share.group_index).split())==3
else:
    try:
        sm.combine_mnemonics(phrases,b'TREZOR')
        assert False
    except sm.MnemonicError:pass
for i in range(2):gc.collect()
phrases=['eraser senior decision roster beard treat identify grumpy salt index fake aviation theater cubic bike cause research dragon emphasis counter', 'eraser senior ceramic snake clay various huge numb argue hesitate auction category timber browser greatest hanger petition script leaf pickup', 'eraser senior ceramic shaft dynamic become junior wrist silver peasant force math alto coal amazing segment yelp velvet image paces', 'eraser senior ceramic round column hawk trust auction smug shame alive greatest sheriff living perfect corner chest sled fumes adequate', 'eraser senior decision smug corner ruin rescue cubic angel tackle skin skunk program roster trash rumor slush angel flea amazing']
expected='7c3397a292a5941682d7a4ae2d898d11'
if expected:
    result=sm.combine_mnemonics(phrases,b'TREZOR')
    assert result.hex()==expected
    state=recovery.RecoveryState()
    for phrase in phrases:
        share=sm.Share.from_mnemonic(phrase)
        assert share.mnemonic()==phrase
        scanned=DecodeQR()
        assert scanned.add_data(phrase)==DecodeQRStatus.COMPLETE
        assert scanned.is_slip39_share and scanned.get_slip39_share()==phrase
        assert hash(share)==hash(sm.Share.from_mnemonic(phrase))
        assert len({share,sm.Share.from_mnemonic(phrase)})==1
        assert share!=tuple(share)
        parameters=share.common_parameters()
        assert parameters==tuple(parameters) and hash(parameters)==hash(tuple(parameters))
        for field in ('identifier','new_field'):
            try:setattr(parameters,field,99);assert False
            except AttributeError:pass
        for field in ('identifier','new_field'):
            try:setattr(share,field,1);assert False
            except AttributeError:pass
        state.add_share(share)
    assert state.is_complete() and state.recover(b'TREZOR').hex()==expected
    assert len(state.group_prefix(share.group_index).split())==3
else:
    try:
        sm.combine_mnemonics(phrases,b'TREZOR')
        assert False
    except sm.MnemonicError:pass
for i in range(2):gc.collect()
phrases=['eraser senior decision smug corner ruin rescue cubic angel tackle skin skunk program roster trash rumor slush angel flea amazing', 'eraser senior beard romp adorn nuclear spill corner cradle style ancient family general leader ambition exchange unusual garlic promise voice', 'eraser senior decision scared cargo theory device idea deliver modify curly include pancake both news skin realize vitamins away join']
expected='7c3397a292a5941682d7a4ae2d898d11'
if expected:
    result=sm.combine_mnemonics(phrases,b'TREZOR')
    assert result.hex()==expected
    state=recovery.RecoveryState()
    for phrase in phrases:
        share=sm.Share.from_mnemonic(phrase)
        assert share.mnemonic()==phrase
        scanned=DecodeQR()
        assert scanned.add_data(phrase)==DecodeQRStatus.COMPLETE
        assert scanned.is_slip39_share and scanned.get_slip39_share()==phrase
        assert hash(share)==hash(sm.Share.from_mnemonic(phrase))
        assert len({share,sm.Share.from_mnemonic(phrase)})==1
        assert share!=tuple(share)
        parameters=share.common_parameters()
        assert parameters==tuple(parameters) and hash(parameters)==hash(tuple(parameters))
        for field in ('identifier','new_field'):
            try:setattr(parameters,field,99);assert False
            except AttributeError:pass
        for field in ('identifier','new_field'):
            try:setattr(share,field,1);assert False
            except AttributeError:pass
        state.add_share(share)
    assert state.is_complete() and state.recover(b'TREZOR').hex()==expected
    assert len(state.group_prefix(share.group_index).split())==3
else:
    try:
        sm.combine_mnemonics(phrases,b'TREZOR')
        assert False
    except sm.MnemonicError:pass
for i in range(2):gc.collect()
phrases=['eraser senior beard romp adorn nuclear spill corner cradle style ancient family general leader ambition exchange unusual garlic promise voice', 'eraser senior acrobat romp bishop medical gesture pumps secret alive ultimate quarter priest subject class dictate spew material endless market']
expected='7c3397a292a5941682d7a4ae2d898d11'
if expected:
    result=sm.combine_mnemonics(phrases,b'TREZOR')
    assert result.hex()==expected
    state=recovery.RecoveryState()
    for phrase in phrases:
        share=sm.Share.from_mnemonic(phrase)
        assert share.mnemonic()==phrase
        scanned=DecodeQR()
        assert scanned.add_data(phrase)==DecodeQRStatus.COMPLETE
        assert scanned.is_slip39_share and scanned.get_slip39_share()==phrase
        assert hash(share)==hash(sm.Share.from_mnemonic(phrase))
        assert len({share,sm.Share.from_mnemonic(phrase)})==1
        assert share!=tuple(share)
        parameters=share.common_parameters()
        assert parameters==tuple(parameters) and hash(parameters)==hash(tuple(parameters))
        for field in ('identifier','new_field'):
            try:setattr(parameters,field,99);assert False
            except AttributeError:pass
        for field in ('identifier','new_field'):
            try:setattr(share,field,1);assert False
            except AttributeError:pass
        state.add_share(share)
    assert state.is_complete() and state.recover(b'TREZOR').hex()==expected
    assert len(state.group_prefix(share.group_index).split())==3
else:
    try:
        sm.combine_mnemonics(phrases,b'TREZOR')
        assert False
    except sm.MnemonicError:pass
for i in range(2):gc.collect()
phrases=['theory painting academic academic armed sweater year military elder discuss acne wildlife boring employer fused large satoshi bundle carbon diagnose anatomy hamster leaves tracks paces beyond phantom capital marvel lips brave detect luck']
expected='989baf9dcaad5b10ca33dfd8cc75e42477025dce88ae83e75a230086a0e00e92'
if expected:
    result=sm.combine_mnemonics(phrases,b'TREZOR')
    assert result.hex()==expected
    state=recovery.RecoveryState()
    for phrase in phrases:
        share=sm.Share.from_mnemonic(phrase)
        assert share.mnemonic()==phrase
        scanned=DecodeQR()
        assert scanned.add_data(phrase)==DecodeQRStatus.COMPLETE
        assert scanned.is_slip39_share and scanned.get_slip39_share()==phrase
        assert hash(share)==hash(sm.Share.from_mnemonic(phrase))
        assert len({share,sm.Share.from_mnemonic(phrase)})==1
        assert share!=tuple(share)
        parameters=share.common_parameters()
        assert parameters==tuple(parameters) and hash(parameters)==hash(tuple(parameters))
        for field in ('identifier','new_field'):
            try:setattr(parameters,field,99);assert False
            except AttributeError:pass
        for field in ('identifier','new_field'):
            try:setattr(share,field,1);assert False
            except AttributeError:pass
        state.add_share(share)
    assert state.is_complete() and state.recover(b'TREZOR').hex()==expected
    assert len(state.group_prefix(share.group_index).split())==3
else:
    try:
        sm.combine_mnemonics(phrases,b'TREZOR')
        assert False
    except sm.MnemonicError:pass
for i in range(2):gc.collect()
phrases=['theory painting academic academic armed sweater year military elder discuss acne wildlife boring employer fused large satoshi bundle carbon diagnose anatomy hamster leaves tracks paces beyond phantom capital marvel lips brave detect lunar']
expected=''
if expected:
    result=sm.combine_mnemonics(phrases,b'TREZOR')
    assert result.hex()==expected
    state=recovery.RecoveryState()
    for phrase in phrases:
        share=sm.Share.from_mnemonic(phrase)
        assert share.mnemonic()==phrase
        scanned=DecodeQR()
        assert scanned.add_data(phrase)==DecodeQRStatus.COMPLETE
        assert scanned.is_slip39_share and scanned.get_slip39_share()==phrase
        assert hash(share)==hash(sm.Share.from_mnemonic(phrase))
        assert len({share,sm.Share.from_mnemonic(phrase)})==1
        assert share!=tuple(share)
        parameters=share.common_parameters()
        assert parameters==tuple(parameters) and hash(parameters)==hash(tuple(parameters))
        for field in ('identifier','new_field'):
            try:setattr(parameters,field,99);assert False
            except AttributeError:pass
        for field in ('identifier','new_field'):
            try:setattr(share,field,1);assert False
            except AttributeError:pass
        state.add_share(share)
    assert state.is_complete() and state.recover(b'TREZOR').hex()==expected
    assert len(state.group_prefix(share.group_index).split())==3
else:
    try:
        sm.combine_mnemonics(phrases,b'TREZOR')
        assert False
    except sm.MnemonicError:pass
for i in range(2):gc.collect()
phrases=['theory painting academic academic campus sweater year military elder discuss acne wildlife boring employer fused large satoshi bundle carbon diagnose anatomy hamster leaves tracks paces beyond phantom capital marvel lips facility obtain sister']
expected=''
if expected:
    result=sm.combine_mnemonics(phrases,b'TREZOR')
    assert result.hex()==expected
    state=recovery.RecoveryState()
    for phrase in phrases:
        share=sm.Share.from_mnemonic(phrase)
        assert share.mnemonic()==phrase
        scanned=DecodeQR()
        assert scanned.add_data(phrase)==DecodeQRStatus.COMPLETE
        assert scanned.is_slip39_share and scanned.get_slip39_share()==phrase
        assert hash(share)==hash(sm.Share.from_mnemonic(phrase))
        assert len({share,sm.Share.from_mnemonic(phrase)})==1
        assert share!=tuple(share)
        parameters=share.common_parameters()
        assert parameters==tuple(parameters) and hash(parameters)==hash(tuple(parameters))
        for field in ('identifier','new_field'):
            try:setattr(parameters,field,99);assert False
            except AttributeError:pass
        for field in ('identifier','new_field'):
            try:setattr(share,field,1);assert False
            except AttributeError:pass
        state.add_share(share)
    assert state.is_complete() and state.recover(b'TREZOR').hex()==expected
    assert len(state.group_prefix(share.group_index).split())==3
else:
    try:
        sm.combine_mnemonics(phrases,b'TREZOR')
        assert False
    except sm.MnemonicError:pass
for i in range(2):gc.collect()
phrases=['humidity disease academic always aluminum jewelry energy woman receiver strategy amuse duckling lying evidence network walnut tactics forget hairy rebound impulse brother survive clothes stadium mailman rival ocean reward venture always armed unwrap', 'humidity disease academic agency actress jacket gross physics cylinder solution fake mortgage benefit public busy prepare sharp friar change work slow purchase ruler again tricycle involve viral wireless mixture anatomy desert cargo upgrade']
expected='c938b319067687e990e05e0da0ecce1278f75ff58d9853f19dcaeed5de104aae'
if expected:
    result=sm.combine_mnemonics(phrases,b'TREZOR')
    assert result.hex()==expected
    state=recovery.RecoveryState()
    for phrase in phrases:
        share=sm.Share.from_mnemonic(phrase)
        assert share.mnemonic()==phrase
        scanned=DecodeQR()
        assert scanned.add_data(phrase)==DecodeQRStatus.COMPLETE
        assert scanned.is_slip39_share and scanned.get_slip39_share()==phrase
        assert hash(share)==hash(sm.Share.from_mnemonic(phrase))
        assert len({share,sm.Share.from_mnemonic(phrase)})==1
        assert share!=tuple(share)
        parameters=share.common_parameters()
        assert parameters==tuple(parameters) and hash(parameters)==hash(tuple(parameters))
        for field in ('identifier','new_field'):
            try:setattr(parameters,field,99);assert False
            except AttributeError:pass
        for field in ('identifier','new_field'):
            try:setattr(share,field,1);assert False
            except AttributeError:pass
        state.add_share(share)
    assert state.is_complete() and state.recover(b'TREZOR').hex()==expected
    assert len(state.group_prefix(share.group_index).split())==3
else:
    try:
        sm.combine_mnemonics(phrases,b'TREZOR')
        assert False
    except sm.MnemonicError:pass
for i in range(2):gc.collect()
phrases=['humidity disease academic always aluminum jewelry energy woman receiver strategy amuse duckling lying evidence network walnut tactics forget hairy rebound impulse brother survive clothes stadium mailman rival ocean reward venture always armed unwrap']
expected=''
if expected:
    result=sm.combine_mnemonics(phrases,b'TREZOR')
    assert result.hex()==expected
    state=recovery.RecoveryState()
    for phrase in phrases:
        share=sm.Share.from_mnemonic(phrase)
        assert share.mnemonic()==phrase
        scanned=DecodeQR()
        assert scanned.add_data(phrase)==DecodeQRStatus.COMPLETE
        assert scanned.is_slip39_share and scanned.get_slip39_share()==phrase
        assert hash(share)==hash(sm.Share.from_mnemonic(phrase))
        assert len({share,sm.Share.from_mnemonic(phrase)})==1
        assert share!=tuple(share)
        parameters=share.common_parameters()
        assert parameters==tuple(parameters) and hash(parameters)==hash(tuple(parameters))
        for field in ('identifier','new_field'):
            try:setattr(parameters,field,99);assert False
            except AttributeError:pass
        for field in ('identifier','new_field'):
            try:setattr(share,field,1);assert False
            except AttributeError:pass
        state.add_share(share)
    assert state.is_complete() and state.recover(b'TREZOR').hex()==expected
    assert len(state.group_prefix(share.group_index).split())==3
else:
    try:
        sm.combine_mnemonics(phrases,b'TREZOR')
        assert False
    except sm.MnemonicError:pass
for i in range(2):gc.collect()
phrases=['smear husband academic acid deadline scene venture distance dive overall parking bracelet elevator justice echo burning oven chest duke nylon', 'smear isolate academic agency alpha mandate decorate burden recover guard exercise fatal force syndrome fumes thank guest drift dramatic mule']
expected=''
if expected:
    result=sm.combine_mnemonics(phrases,b'TREZOR')
    assert result.hex()==expected
    state=recovery.RecoveryState()
    for phrase in phrases:
        share=sm.Share.from_mnemonic(phrase)
        assert share.mnemonic()==phrase
        scanned=DecodeQR()
        assert scanned.add_data(phrase)==DecodeQRStatus.COMPLETE
        assert scanned.is_slip39_share and scanned.get_slip39_share()==phrase
        assert hash(share)==hash(sm.Share.from_mnemonic(phrase))
        assert len({share,sm.Share.from_mnemonic(phrase)})==1
        assert share!=tuple(share)
        parameters=share.common_parameters()
        assert parameters==tuple(parameters) and hash(parameters)==hash(tuple(parameters))
        for field in ('identifier','new_field'):
            try:setattr(parameters,field,99);assert False
            except AttributeError:pass
        for field in ('identifier','new_field'):
            try:setattr(share,field,1);assert False
            except AttributeError:pass
        state.add_share(share)
    assert state.is_complete() and state.recover(b'TREZOR').hex()==expected
    assert len(state.group_prefix(share.group_index).split())==3
else:
    try:
        sm.combine_mnemonics(phrases,b'TREZOR')
        assert False
    except sm.MnemonicError:pass
for i in range(2):gc.collect()
phrases=['finger trash academic acid average priority dish revenue academic hospital spirit western ocean fact calcium syndrome greatest plan losing dictate', 'finger traffic academic agency building lilac deny paces subject threaten diploma eclipse window unknown health slim piece dragon focus smirk']
expected=''
if expected:
    result=sm.combine_mnemonics(phrases,b'TREZOR')
    assert result.hex()==expected
    state=recovery.RecoveryState()
    for phrase in phrases:
        share=sm.Share.from_mnemonic(phrase)
        assert share.mnemonic()==phrase
        scanned=DecodeQR()
        assert scanned.add_data(phrase)==DecodeQRStatus.COMPLETE
        assert scanned.is_slip39_share and scanned.get_slip39_share()==phrase
        assert hash(share)==hash(sm.Share.from_mnemonic(phrase))
        assert len({share,sm.Share.from_mnemonic(phrase)})==1
        assert share!=tuple(share)
        parameters=share.common_parameters()
        assert parameters==tuple(parameters) and hash(parameters)==hash(tuple(parameters))
        for field in ('identifier','new_field'):
            try:setattr(parameters,field,99);assert False
            except AttributeError:pass
        for field in ('identifier','new_field'):
            try:setattr(share,field,1);assert False
            except AttributeError:pass
        state.add_share(share)
    assert state.is_complete() and state.recover(b'TREZOR').hex()==expected
    assert len(state.group_prefix(share.group_index).split())==3
else:
    try:
        sm.combine_mnemonics(phrases,b'TREZOR')
        assert False
    except sm.MnemonicError:pass
for i in range(2):gc.collect()
phrases=['flavor pink beard echo depart forbid retreat become frost helpful juice unwrap reunion credit math burning spine black capital lair', 'flavor pink beard email diet teaspoon freshman identify document rebound cricket prune headset loyalty smell emission skin often square rebound', 'flavor pink academic easy credit cage raisin crazy closet lobe mobile become drink human tactics valuable hand capture sympathy finger']
expected=''
if expected:
    result=sm.combine_mnemonics(phrases,b'TREZOR')
    assert result.hex()==expected
    state=recovery.RecoveryState()
    for phrase in phrases:
        share=sm.Share.from_mnemonic(phrase)
        assert share.mnemonic()==phrase
        scanned=DecodeQR()
        assert scanned.add_data(phrase)==DecodeQRStatus.COMPLETE
        assert scanned.is_slip39_share and scanned.get_slip39_share()==phrase
        assert hash(share)==hash(sm.Share.from_mnemonic(phrase))
        assert len({share,sm.Share.from_mnemonic(phrase)})==1
        assert share!=tuple(share)
        parameters=share.common_parameters()
        assert parameters==tuple(parameters) and hash(parameters)==hash(tuple(parameters))
        for field in ('identifier','new_field'):
            try:setattr(parameters,field,99);assert False
            except AttributeError:pass
        for field in ('identifier','new_field'):
            try:setattr(share,field,1);assert False
            except AttributeError:pass
        state.add_share(share)
    assert state.is_complete() and state.recover(b'TREZOR').hex()==expected
    assert len(state.group_prefix(share.group_index).split())==3
else:
    try:
        sm.combine_mnemonics(phrases,b'TREZOR')
        assert False
    except sm.MnemonicError:pass
for i in range(2):gc.collect()
phrases=['column flea academic leaf debut extra surface slow timber husky lawsuit game behavior husky swimming already paper episode tricycle scroll', 'column flea academic agency blessing garbage party software stadium verify silent umbrella therapy decorate chemical erode dramatic eclipse replace apart']
expected=''
if expected:
    result=sm.combine_mnemonics(phrases,b'TREZOR')
    assert result.hex()==expected
    state=recovery.RecoveryState()
    for phrase in phrases:
        share=sm.Share.from_mnemonic(phrase)
        assert share.mnemonic()==phrase
        scanned=DecodeQR()
        assert scanned.add_data(phrase)==DecodeQRStatus.COMPLETE
        assert scanned.is_slip39_share and scanned.get_slip39_share()==phrase
        assert hash(share)==hash(sm.Share.from_mnemonic(phrase))
        assert len({share,sm.Share.from_mnemonic(phrase)})==1
        assert share!=tuple(share)
        parameters=share.common_parameters()
        assert parameters==tuple(parameters) and hash(parameters)==hash(tuple(parameters))
        for field in ('identifier','new_field'):
            try:setattr(parameters,field,99);assert False
            except AttributeError:pass
        for field in ('identifier','new_field'):
            try:setattr(share,field,1);assert False
            except AttributeError:pass
        state.add_share(share)
    assert state.is_complete() and state.recover(b'TREZOR').hex()==expected
    assert len(state.group_prefix(share.group_index).split())==3
else:
    try:
        sm.combine_mnemonics(phrases,b'TREZOR')
        assert False
    except sm.MnemonicError:pass
for i in range(2):gc.collect()
phrases=['smirk pink acrobat acid auction wireless impulse spine sprinkle fortune clogs elbow guest hush loyalty crush dictate tracks airport talent', 'smirk pink acrobat agency dwarf emperor ajar organize legs slice harvest plastic dynamic style mobile float bulb health coding credit', 'smirk pink beard academic alto strategy carve shame language rapids ruin smart location spray training acquire eraser endorse submit peaceful']
expected=''
if expected:
    result=sm.combine_mnemonics(phrases,b'TREZOR')
    assert result.hex()==expected
    state=recovery.RecoveryState()
    for phrase in phrases:
        share=sm.Share.from_mnemonic(phrase)
        assert share.mnemonic()==phrase
        scanned=DecodeQR()
        assert scanned.add_data(phrase)==DecodeQRStatus.COMPLETE
        assert scanned.is_slip39_share and scanned.get_slip39_share()==phrase
        assert hash(share)==hash(sm.Share.from_mnemonic(phrase))
        assert len({share,sm.Share.from_mnemonic(phrase)})==1
        assert share!=tuple(share)
        parameters=share.common_parameters()
        assert parameters==tuple(parameters) and hash(parameters)==hash(tuple(parameters))
        for field in ('identifier','new_field'):
            try:setattr(parameters,field,99);assert False
            except AttributeError:pass
        for field in ('identifier','new_field'):
            try:setattr(share,field,1);assert False
            except AttributeError:pass
        state.add_share(share)
    assert state.is_complete() and state.recover(b'TREZOR').hex()==expected
    assert len(state.group_prefix(share.group_index).split())==3
else:
    try:
        sm.combine_mnemonics(phrases,b'TREZOR')
        assert False
    except sm.MnemonicError:pass
for i in range(2):gc.collect()
phrases=['fishing recover academic always device craft trend snapshot gums skin downtown watch device sniff hour clock public maximum garlic born', 'fishing recover academic always aircraft view software cradle fangs amazing package plastic evaluate intend penalty epidemic anatomy quarter cage apart']
expected=''
if expected:
    result=sm.combine_mnemonics(phrases,b'TREZOR')
    assert result.hex()==expected
    state=recovery.RecoveryState()
    for phrase in phrases:
        share=sm.Share.from_mnemonic(phrase)
        assert share.mnemonic()==phrase
        scanned=DecodeQR()
        assert scanned.add_data(phrase)==DecodeQRStatus.COMPLETE
        assert scanned.is_slip39_share and scanned.get_slip39_share()==phrase
        assert hash(share)==hash(sm.Share.from_mnemonic(phrase))
        assert len({share,sm.Share.from_mnemonic(phrase)})==1
        assert share!=tuple(share)
        parameters=share.common_parameters()
        assert parameters==tuple(parameters) and hash(parameters)==hash(tuple(parameters))
        for field in ('identifier','new_field'):
            try:setattr(parameters,field,99);assert False
            except AttributeError:pass
        for field in ('identifier','new_field'):
            try:setattr(share,field,1);assert False
            except AttributeError:pass
        state.add_share(share)
    assert state.is_complete() and state.recover(b'TREZOR').hex()==expected
    assert len(state.group_prefix(share.group_index).split())==3
else:
    try:
        sm.combine_mnemonics(phrases,b'TREZOR')
        assert False
    except sm.MnemonicError:pass
for i in range(2):gc.collect()
phrases=['evoke garden academic academic answer wolf scandal modern warmth station devote emerald market physics surface formal amazing aquatic gesture medical', 'evoke garden academic agency deal revenue knit reunion decrease magazine flexible company goat repair alarm military facility clogs aide mandate']
expected=''
if expected:
    result=sm.combine_mnemonics(phrases,b'TREZOR')
    assert result.hex()==expected
    state=recovery.RecoveryState()
    for phrase in phrases:
        share=sm.Share.from_mnemonic(phrase)
        assert share.mnemonic()==phrase
        scanned=DecodeQR()
        assert scanned.add_data(phrase)==DecodeQRStatus.COMPLETE
        assert scanned.is_slip39_share and scanned.get_slip39_share()==phrase
        assert hash(share)==hash(sm.Share.from_mnemonic(phrase))
        assert len({share,sm.Share.from_mnemonic(phrase)})==1
        assert share!=tuple(share)
        parameters=share.common_parameters()
        assert parameters==tuple(parameters) and hash(parameters)==hash(tuple(parameters))
        for field in ('identifier','new_field'):
            try:setattr(parameters,field,99);assert False
            except AttributeError:pass
        for field in ('identifier','new_field'):
            try:setattr(share,field,1);assert False
            except AttributeError:pass
        state.add_share(share)
    assert state.is_complete() and state.recover(b'TREZOR').hex()==expected
    assert len(state.group_prefix(share.group_index).split())==3
else:
    try:
        sm.combine_mnemonics(phrases,b'TREZOR')
        assert False
    except sm.MnemonicError:pass
for i in range(2):gc.collect()
phrases=['river deal academic acid average forbid pistol peanut custody bike class aunt hairy merit valid flexible learn ajar very easel', 'river deal academic agency camera amuse lungs numb isolate display smear piece traffic worthy year patrol crush fact fancy emission']
expected=''
if expected:
    result=sm.combine_mnemonics(phrases,b'TREZOR')
    assert result.hex()==expected
    state=recovery.RecoveryState()
    for phrase in phrases:
        share=sm.Share.from_mnemonic(phrase)
        assert share.mnemonic()==phrase
        scanned=DecodeQR()
        assert scanned.add_data(phrase)==DecodeQRStatus.COMPLETE
        assert scanned.is_slip39_share and scanned.get_slip39_share()==phrase
        assert hash(share)==hash(sm.Share.from_mnemonic(phrase))
        assert len({share,sm.Share.from_mnemonic(phrase)})==1
        assert share!=tuple(share)
        parameters=share.common_parameters()
        assert parameters==tuple(parameters) and hash(parameters)==hash(tuple(parameters))
        for field in ('identifier','new_field'):
            try:setattr(parameters,field,99);assert False
            except AttributeError:pass
        for field in ('identifier','new_field'):
            try:setattr(share,field,1);assert False
            except AttributeError:pass
        state.add_share(share)
    assert state.is_complete() and state.recover(b'TREZOR').hex()==expected
    assert len(state.group_prefix(share.group_index).split())==3
else:
    try:
        sm.combine_mnemonics(phrases,b'TREZOR')
        assert False
    except sm.MnemonicError:pass
for i in range(2):gc.collect()
phrases=['wildlife deal beard romp alcohol space mild usual clothes union nuclear testify course research heat listen task location thank hospital slice smell failure fawn helpful priest ambition average recover lecture process dough stadium']
expected=''
if expected:
    result=sm.combine_mnemonics(phrases,b'TREZOR')
    assert result.hex()==expected
    state=recovery.RecoveryState()
    for phrase in phrases:
        share=sm.Share.from_mnemonic(phrase)
        assert share.mnemonic()==phrase
        scanned=DecodeQR()
        assert scanned.add_data(phrase)==DecodeQRStatus.COMPLETE
        assert scanned.is_slip39_share and scanned.get_slip39_share()==phrase
        assert hash(share)==hash(sm.Share.from_mnemonic(phrase))
        assert len({share,sm.Share.from_mnemonic(phrase)})==1
        assert share!=tuple(share)
        parameters=share.common_parameters()
        assert parameters==tuple(parameters) and hash(parameters)==hash(tuple(parameters))
        for field in ('identifier','new_field'):
            try:setattr(parameters,field,99);assert False
            except AttributeError:pass
        for field in ('identifier','new_field'):
            try:setattr(share,field,1);assert False
            except AttributeError:pass
        state.add_share(share)
    assert state.is_complete() and state.recover(b'TREZOR').hex()==expected
    assert len(state.group_prefix(share.group_index).split())==3
else:
    try:
        sm.combine_mnemonics(phrases,b'TREZOR')
        assert False
    except sm.MnemonicError:pass
for i in range(2):gc.collect()
phrases=['wildlife deal decision scared acne fatal snake paces obtain election dryer dominant romp tactics railroad marvel trust helpful flip peanut theory theater photo luck install entrance taxi step oven network dictate intimate listen', 'wildlife deal decision smug ancestor genuine move huge cubic strategy smell game costume extend swimming false desire fake traffic vegan senior twice timber submit leader payroll fraction apart exact forward pulse tidy install']
expected=''
if expected:
    result=sm.combine_mnemonics(phrases,b'TREZOR')
    assert result.hex()==expected
    state=recovery.RecoveryState()
    for phrase in phrases:
        share=sm.Share.from_mnemonic(phrase)
        assert share.mnemonic()==phrase
        scanned=DecodeQR()
        assert scanned.add_data(phrase)==DecodeQRStatus.COMPLETE
        assert scanned.is_slip39_share and scanned.get_slip39_share()==phrase
        assert hash(share)==hash(sm.Share.from_mnemonic(phrase))
        assert len({share,sm.Share.from_mnemonic(phrase)})==1
        assert share!=tuple(share)
        parameters=share.common_parameters()
        assert parameters==tuple(parameters) and hash(parameters)==hash(tuple(parameters))
        for field in ('identifier','new_field'):
            try:setattr(parameters,field,99);assert False
            except AttributeError:pass
        for field in ('identifier','new_field'):
            try:setattr(share,field,1);assert False
            except AttributeError:pass
        state.add_share(share)
    assert state.is_complete() and state.recover(b'TREZOR').hex()==expected
    assert len(state.group_prefix(share.group_index).split())==3
else:
    try:
        sm.combine_mnemonics(phrases,b'TREZOR')
        assert False
    except sm.MnemonicError:pass
for i in range(2):gc.collect()
phrases=['wildlife deal decision shadow analysis adjust bulb skunk muscle mandate obesity total guitar coal gravity carve slim jacket ruin rebuild ancestor numerous hour mortgage require herd maiden public ceiling pecan pickup shadow club', 'wildlife deal beard romp alcohol space mild usual clothes union nuclear testify course research heat listen task location thank hospital slice smell failure fawn helpful priest ambition average recover lecture process dough stadium']
expected=''
if expected:
    result=sm.combine_mnemonics(phrases,b'TREZOR')
    assert result.hex()==expected
    state=recovery.RecoveryState()
    for phrase in phrases:
        share=sm.Share.from_mnemonic(phrase)
        assert share.mnemonic()==phrase
        scanned=DecodeQR()
        assert scanned.add_data(phrase)==DecodeQRStatus.COMPLETE
        assert scanned.is_slip39_share and scanned.get_slip39_share()==phrase
        assert hash(share)==hash(sm.Share.from_mnemonic(phrase))
        assert len({share,sm.Share.from_mnemonic(phrase)})==1
        assert share!=tuple(share)
        parameters=share.common_parameters()
        assert parameters==tuple(parameters) and hash(parameters)==hash(tuple(parameters))
        for field in ('identifier','new_field'):
            try:setattr(parameters,field,99);assert False
            except AttributeError:pass
        for field in ('identifier','new_field'):
            try:setattr(share,field,1);assert False
            except AttributeError:pass
        state.add_share(share)
    assert state.is_complete() and state.recover(b'TREZOR').hex()==expected
    assert len(state.group_prefix(share.group_index).split())==3
else:
    try:
        sm.combine_mnemonics(phrases,b'TREZOR')
        assert False
    except sm.MnemonicError:pass
for i in range(2):gc.collect()
phrases=['wildlife deal ceramic round aluminum pitch goat racism employer miracle percent math decision episode dramatic editor lily prospect program scene rebuild display sympathy have single mustang junction relate often chemical society wits estate', 'wildlife deal decision scared acne fatal snake paces obtain election dryer dominant romp tactics railroad marvel trust helpful flip peanut theory theater photo luck install entrance taxi step oven network dictate intimate listen', 'wildlife deal ceramic scatter argue equip vampire together ruin reject literary rival distance aquatic agency teammate rebound false argue miracle stay again blessing peaceful unknown cover beard acid island language debris industry idle', 'wildlife deal ceramic snake agree voter main lecture axis kitchen physics arcade velvet spine idea scroll promise platform firm sharp patrol divorce ancestor fantasy forbid goat ajar believe swimming cowboy symbolic plastic spelling', 'wildlife deal decision shadow analysis adjust bulb skunk muscle mandate obesity total guitar coal gravity carve slim jacket ruin rebuild ancestor numerous hour mortgage require herd maiden public ceiling pecan pickup shadow club']
expected='5385577c8cfc6c1a8aa0f7f10ecde0a3318493262591e78b8c14c6686167123b'
if expected:
    result=sm.combine_mnemonics(phrases,b'TREZOR')
    assert result.hex()==expected
    state=recovery.RecoveryState()
    for phrase in phrases:
        share=sm.Share.from_mnemonic(phrase)
        assert share.mnemonic()==phrase
        scanned=DecodeQR()
        assert scanned.add_data(phrase)==DecodeQRStatus.COMPLETE
        assert scanned.is_slip39_share and scanned.get_slip39_share()==phrase
        assert hash(share)==hash(sm.Share.from_mnemonic(phrase))
        assert len({share,sm.Share.from_mnemonic(phrase)})==1
        assert share!=tuple(share)
        parameters=share.common_parameters()
        assert parameters==tuple(parameters) and hash(parameters)==hash(tuple(parameters))
        for field in ('identifier','new_field'):
            try:setattr(parameters,field,99);assert False
            except AttributeError:pass
        for field in ('identifier','new_field'):
            try:setattr(share,field,1);assert False
            except AttributeError:pass
        state.add_share(share)
    assert state.is_complete() and state.recover(b'TREZOR').hex()==expected
    assert len(state.group_prefix(share.group_index).split())==3
else:
    try:
        sm.combine_mnemonics(phrases,b'TREZOR')
        assert False
    except sm.MnemonicError:pass
for i in range(2):gc.collect()
phrases=['wildlife deal decision scared acne fatal snake paces obtain election dryer dominant romp tactics railroad marvel trust helpful flip peanut theory theater photo luck install entrance taxi step oven network dictate intimate listen', 'wildlife deal beard romp alcohol space mild usual clothes union nuclear testify course research heat listen task location thank hospital slice smell failure fawn helpful priest ambition average recover lecture process dough stadium', 'wildlife deal decision smug ancestor genuine move huge cubic strategy smell game costume extend swimming false desire fake traffic vegan senior twice timber submit leader payroll fraction apart exact forward pulse tidy install']
expected='5385577c8cfc6c1a8aa0f7f10ecde0a3318493262591e78b8c14c6686167123b'
if expected:
    result=sm.combine_mnemonics(phrases,b'TREZOR')
    assert result.hex()==expected
    state=recovery.RecoveryState()
    for phrase in phrases:
        share=sm.Share.from_mnemonic(phrase)
        assert share.mnemonic()==phrase
        scanned=DecodeQR()
        assert scanned.add_data(phrase)==DecodeQRStatus.COMPLETE
        assert scanned.is_slip39_share and scanned.get_slip39_share()==phrase
        assert hash(share)==hash(sm.Share.from_mnemonic(phrase))
        assert len({share,sm.Share.from_mnemonic(phrase)})==1
        assert share!=tuple(share)
        parameters=share.common_parameters()
        assert parameters==tuple(parameters) and hash(parameters)==hash(tuple(parameters))
        for field in ('identifier','new_field'):
            try:setattr(parameters,field,99);assert False
            except AttributeError:pass
        for field in ('identifier','new_field'):
            try:setattr(share,field,1);assert False
            except AttributeError:pass
        state.add_share(share)
    assert state.is_complete() and state.recover(b'TREZOR').hex()==expected
    assert len(state.group_prefix(share.group_index).split())==3
else:
    try:
        sm.combine_mnemonics(phrases,b'TREZOR')
        assert False
    except sm.MnemonicError:pass
for i in range(2):gc.collect()
phrases=['wildlife deal beard romp alcohol space mild usual clothes union nuclear testify course research heat listen task location thank hospital slice smell failure fawn helpful priest ambition average recover lecture process dough stadium', 'wildlife deal acrobat romp anxiety axis starting require metric flexible geology game drove editor edge screw helpful have huge holy making pitch unknown carve holiday numb glasses survive already tenant adapt goat fangs']
expected='5385577c8cfc6c1a8aa0f7f10ecde0a3318493262591e78b8c14c6686167123b'
if expected:
    result=sm.combine_mnemonics(phrases,b'TREZOR')
    assert result.hex()==expected
    state=recovery.RecoveryState()
    for phrase in phrases:
        share=sm.Share.from_mnemonic(phrase)
        assert share.mnemonic()==phrase
        scanned=DecodeQR()
        assert scanned.add_data(phrase)==DecodeQRStatus.COMPLETE
        assert scanned.is_slip39_share and scanned.get_slip39_share()==phrase
        assert hash(share)==hash(sm.Share.from_mnemonic(phrase))
        assert len({share,sm.Share.from_mnemonic(phrase)})==1
        assert share!=tuple(share)
        parameters=share.common_parameters()
        assert parameters==tuple(parameters) and hash(parameters)==hash(tuple(parameters))
        for field in ('identifier','new_field'):
            try:setattr(parameters,field,99);assert False
            except AttributeError:pass
        for field in ('identifier','new_field'):
            try:setattr(share,field,1);assert False
            except AttributeError:pass
        state.add_share(share)
    assert state.is_complete() and state.recover(b'TREZOR').hex()==expected
    assert len(state.group_prefix(share.group_index).split())==3
else:
    try:
        sm.combine_mnemonics(phrases,b'TREZOR')
        assert False
    except sm.MnemonicError:pass
for i in range(2):gc.collect()
phrases=['junk necklace academic academic acne isolate join hesitate lunar roster dough calcium chemical ladybug amount mobile glasses verify cylinder']
expected=''
if expected:
    result=sm.combine_mnemonics(phrases,b'TREZOR')
    assert result.hex()==expected
    state=recovery.RecoveryState()
    for phrase in phrases:
        share=sm.Share.from_mnemonic(phrase)
        assert share.mnemonic()==phrase
        scanned=DecodeQR()
        assert scanned.add_data(phrase)==DecodeQRStatus.COMPLETE
        assert scanned.is_slip39_share and scanned.get_slip39_share()==phrase
        assert hash(share)==hash(sm.Share.from_mnemonic(phrase))
        assert len({share,sm.Share.from_mnemonic(phrase)})==1
        assert share!=tuple(share)
        parameters=share.common_parameters()
        assert parameters==tuple(parameters) and hash(parameters)==hash(tuple(parameters))
        for field in ('identifier','new_field'):
            try:setattr(parameters,field,99);assert False
            except AttributeError:pass
        for field in ('identifier','new_field'):
            try:setattr(share,field,1);assert False
            except AttributeError:pass
        state.add_share(share)
    assert state.is_complete() and state.recover(b'TREZOR').hex()==expected
    assert len(state.group_prefix(share.group_index).split())==3
else:
    try:
        sm.combine_mnemonics(phrases,b'TREZOR')
        assert False
    except sm.MnemonicError:pass
for i in range(2):gc.collect()
phrases=['fraction necklace academic academic award teammate mouse regular testify coding building member verdict purchase blind camera duration email prepare spirit quarter']
expected=''
if expected:
    result=sm.combine_mnemonics(phrases,b'TREZOR')
    assert result.hex()==expected
    state=recovery.RecoveryState()
    for phrase in phrases:
        share=sm.Share.from_mnemonic(phrase)
        assert share.mnemonic()==phrase
        scanned=DecodeQR()
        assert scanned.add_data(phrase)==DecodeQRStatus.COMPLETE
        assert scanned.is_slip39_share and scanned.get_slip39_share()==phrase
        assert hash(share)==hash(sm.Share.from_mnemonic(phrase))
        assert len({share,sm.Share.from_mnemonic(phrase)})==1
        assert share!=tuple(share)
        parameters=share.common_parameters()
        assert parameters==tuple(parameters) and hash(parameters)==hash(tuple(parameters))
        for field in ('identifier','new_field'):
            try:setattr(parameters,field,99);assert False
            except AttributeError:pass
        for field in ('identifier','new_field'):
            try:setattr(share,field,1);assert False
            except AttributeError:pass
        state.add_share(share)
    assert state.is_complete() and state.recover(b'TREZOR').hex()==expected
    assert len(state.group_prefix(share.group_index).split())==3
else:
    try:
        sm.combine_mnemonics(phrases,b'TREZOR')
        assert False
    except sm.MnemonicError:pass
for i in range(2):gc.collect()
phrases=['herald flea academic cage avoid space trend estate dryer hairy evoke eyebrow improve airline artwork garlic premium duration prevent oven', 'herald flea academic client blue skunk class goat luxury deny presence impulse graduate clay join blanket bulge survive dish necklace', 'herald flea academic acne advance fused brother frozen broken game ranked ajar already believe check install theory angry exercise adult']
expected='ad6f2ad8b59bbbaa01369b9006208d9a'
if expected:
    result=sm.combine_mnemonics(phrases,b'TREZOR')
    assert result.hex()==expected
    state=recovery.RecoveryState()
    for phrase in phrases:
        share=sm.Share.from_mnemonic(phrase)
        assert share.mnemonic()==phrase
        scanned=DecodeQR()
        assert scanned.add_data(phrase)==DecodeQRStatus.COMPLETE
        assert scanned.is_slip39_share and scanned.get_slip39_share()==phrase
        assert hash(share)==hash(sm.Share.from_mnemonic(phrase))
        assert len({share,sm.Share.from_mnemonic(phrase)})==1
        assert share!=tuple(share)
        parameters=share.common_parameters()
        assert parameters==tuple(parameters) and hash(parameters)==hash(tuple(parameters))
        for field in ('identifier','new_field'):
            try:setattr(parameters,field,99);assert False
            except AttributeError:pass
        for field in ('identifier','new_field'):
            try:setattr(share,field,1);assert False
            except AttributeError:pass
        state.add_share(share)
    assert state.is_complete() and state.recover(b'TREZOR').hex()==expected
    assert len(state.group_prefix(share.group_index).split())==3
else:
    try:
        sm.combine_mnemonics(phrases,b'TREZOR')
        assert False
    except sm.MnemonicError:pass
for i in range(2):gc.collect()
phrases=['testify swimming academic academic column loyalty smear include exotic bedroom exotic wrist lobe cover grief golden smart junior estimate learn']
expected='1679b4516e0ee5954351d288a838f45e'
if expected:
    result=sm.combine_mnemonics(phrases,b'TREZOR')
    assert result.hex()==expected
    state=recovery.RecoveryState()
    for phrase in phrases:
        share=sm.Share.from_mnemonic(phrase)
        assert share.mnemonic()==phrase
        scanned=DecodeQR()
        assert scanned.add_data(phrase)==DecodeQRStatus.COMPLETE
        assert scanned.is_slip39_share and scanned.get_slip39_share()==phrase
        assert hash(share)==hash(sm.Share.from_mnemonic(phrase))
        assert len({share,sm.Share.from_mnemonic(phrase)})==1
        assert share!=tuple(share)
        parameters=share.common_parameters()
        assert parameters==tuple(parameters) and hash(parameters)==hash(tuple(parameters))
        for field in ('identifier','new_field'):
            try:setattr(parameters,field,99);assert False
            except AttributeError:pass
        for field in ('identifier','new_field'):
            try:setattr(share,field,1);assert False
            except AttributeError:pass
        state.add_share(share)
    assert state.is_complete() and state.recover(b'TREZOR').hex()==expected
    assert len(state.group_prefix(share.group_index).split())==3
else:
    try:
        sm.combine_mnemonics(phrases,b'TREZOR')
        assert False
    except sm.MnemonicError:pass
for i in range(2):gc.collect()
phrases=['enemy favorite academic acid cowboy phrase havoc level response walnut budget painting inside trash adjust froth kitchen learn tidy punish', 'enemy favorite academic always academic sniff script carpet romp kind promise scatter center unfair training emphasis evening belong fake enforce']
expected='48b1a4b80b8c209ad42c33672bdaa428'
if expected:
    result=sm.combine_mnemonics(phrases,b'TREZOR')
    assert result.hex()==expected
    state=recovery.RecoveryState()
    for phrase in phrases:
        share=sm.Share.from_mnemonic(phrase)
        assert share.mnemonic()==phrase
        scanned=DecodeQR()
        assert scanned.add_data(phrase)==DecodeQRStatus.COMPLETE
        assert scanned.is_slip39_share and scanned.get_slip39_share()==phrase
        assert hash(share)==hash(sm.Share.from_mnemonic(phrase))
        assert len({share,sm.Share.from_mnemonic(phrase)})==1
        assert share!=tuple(share)
        parameters=share.common_parameters()
        assert parameters==tuple(parameters) and hash(parameters)==hash(tuple(parameters))
        for field in ('identifier','new_field'):
            try:setattr(parameters,field,99);assert False
            except AttributeError:pass
        for field in ('identifier','new_field'):
            try:setattr(share,field,1);assert False
            except AttributeError:pass
        state.add_share(share)
    assert state.is_complete() and state.recover(b'TREZOR').hex()==expected
    assert len(state.group_prefix(share.group_index).split())==3
else:
    try:
        sm.combine_mnemonics(phrases,b'TREZOR')
        assert False
    except sm.MnemonicError:pass
for i in range(2):gc.collect()
phrases=['impulse calcium academic academic alcohol sugar lyrics pajamas column facility finance tension extend space birthday rainbow swimming purple syndrome facility trial warn duration snapshot shadow hormone rhyme public spine counter easy hawk album']
expected='8340611602fe91af634a5f4608377b5235fa2d757c51d720c0c7656249a3035f'
if expected:
    result=sm.combine_mnemonics(phrases,b'TREZOR')
    assert result.hex()==expected
    state=recovery.RecoveryState()
    for phrase in phrases:
        share=sm.Share.from_mnemonic(phrase)
        assert share.mnemonic()==phrase
        scanned=DecodeQR()
        assert scanned.add_data(phrase)==DecodeQRStatus.COMPLETE
        assert scanned.is_slip39_share and scanned.get_slip39_share()==phrase
        assert hash(share)==hash(sm.Share.from_mnemonic(phrase))
        assert len({share,sm.Share.from_mnemonic(phrase)})==1
        assert share!=tuple(share)
        parameters=share.common_parameters()
        assert parameters==tuple(parameters) and hash(parameters)==hash(tuple(parameters))
        for field in ('identifier','new_field'):
            try:setattr(parameters,field,99);assert False
            except AttributeError:pass
        for field in ('identifier','new_field'):
            try:setattr(share,field,1);assert False
            except AttributeError:pass
        state.add_share(share)
    assert state.is_complete() and state.recover(b'TREZOR').hex()==expected
    assert len(state.group_prefix(share.group_index).split())==3
else:
    try:
        sm.combine_mnemonics(phrases,b'TREZOR')
        assert False
    except sm.MnemonicError:pass
for i in range(2):gc.collect()
phrases=['western apart academic always artist resident briefing sugar woman oven coding club ajar merit pecan answer prisoner artist fraction amount desktop mild false necklace muscle photo wealthy alpha category unwrap spew losing making', 'western apart academic acid answer ancient auction flip image penalty oasis beaver multiple thunder problem switch alive heat inherit superior teaspoon explain blanket pencil numb lend punish endless aunt garlic humidity kidney observe']
expected='8dc652d6d6cd370d8c963141f6d79ba440300f25c467302c1d966bff8f62300d'
if expected:
    result=sm.combine_mnemonics(phrases,b'TREZOR')
    assert result.hex()==expected
    state=recovery.RecoveryState()
    for phrase in phrases:
        share=sm.Share.from_mnemonic(phrase)
        assert share.mnemonic()==phrase
        scanned=DecodeQR()
        assert scanned.add_data(phrase)==DecodeQRStatus.COMPLETE
        assert scanned.is_slip39_share and scanned.get_slip39_share()==phrase
        assert hash(share)==hash(sm.Share.from_mnemonic(phrase))
        assert len({share,sm.Share.from_mnemonic(phrase)})==1
        assert share!=tuple(share)
        parameters=share.common_parameters()
        assert parameters==tuple(parameters) and hash(parameters)==hash(tuple(parameters))
        for field in ('identifier','new_field'):
            try:setattr(parameters,field,99);assert False
            except AttributeError:pass
        for field in ('identifier','new_field'):
            try:setattr(share,field,1);assert False
            except AttributeError:pass
        state.add_share(share)
    assert state.is_complete() and state.recover(b'TREZOR').hex()==expected
    assert len(state.group_prefix(share.group_index).split())==3
else:
    try:
        sm.combine_mnemonics(phrases,b'TREZOR')
        assert False
    except sm.MnemonicError:pass
for i in range(2):gc.collect()
try:shamir.RANDOM_BYTES(16);assert False
except FeatureUnavailable:pass
assert aezeed._crc32c(b'')==0
assert aezeed._crc32c(b'123456789')==3808858755
assert aezeed._crc32c(b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f !"#$%&\'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~\x7f\x80\x81\x82\x83\x84\x85\x86\x87\x88\x89\x8a\x8b\x8c\x8d\x8e\x8f\x90\x91\x92\x93\x94\x95\x96\x97\x98\x99\x9a\x9b\x9c\x9d\x9e\x9f\xa0\xa1\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xab\xac\xad\xae\xaf\xb0\xb1\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xbb\xbc\xbd\xbe\xbf\xc0\xc1\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xcb\xcc\xcd\xce\xcf\xd0\xd1\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xdb\xdc\xdd\xde\xdf\xe0\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xeb\xec\xed\xee\xef\xf0\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xfb\xfc\xfd\xfe\xff')==2621708363
assert aezeed._crc32c(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')==2606653433
assert aezeed._crc32c(b'\x88')==1515335910
assert aezeed._crc32c(b'\xe3\x18')==610180884
assert aezeed._crc32c(b'\x02\x871')==1814890617
assert aezeed._crc32c(b'\x89?\xdf\xe0')==3554277391
assert aezeed._crc32c(b'\xebS\x88O\t')==2033712805
assert aezeed._crc32c(b'B6\x1f\xc9) ')==2159883757
assert aezeed._crc32c(b'\x9a\x9e\xa2\x9eK\xca\x94')==3944439478
assert aezeed._crc32c(b'\xf6\x8fi#%l\x99\xe2')==3499517367
assert aezeed._crc32c(b'5\xbb\xff\xc6{|\xd7\xdbJ')==3925944110
assert aezeed._crc32c(b'g\n\x08Y\xf7\x8e:\xd7\x9e\x98')==2448731974
assert aezeed._crc32c(b'\xd1\x9f\x07\x9a\xf9\x1e\x06W\xa7$p')==3451328720
assert aezeed._crc32c(b'\xd2!S\xae\xade\xdc\x19EJ\xdb^')==3346776523
assert aezeed._crc32c(b'H\xa2\xfe\xd3\xa81)\x87\x1f^.\xbdo')==4028214898
assert aezeed._crc32c(b'\xce\xe8_\xdd\xfb\x81\x81\x8c(z\xd1B"5')==3072392829
assert aezeed._crc32c(b'\xf8_\x002\xad\x9f>\x12\\q\xb3\xa6\xe1\xba;')==638163534
assert aezeed._crc32c(b'\xed\x86|\xbb\xca\xe6\xf8S\x905\xf0!ms\x03M')==4865011
assert aezeed._crc32c(b',\xc05\xaf\xa2J\xf4T\xdc6d\xc6K\x98\x8ck\x05')==1280697624
assert aezeed._crc32c(b'\xbe\x9f^\xcfI\x08\xc1\xc3\xd9\xd6\x02}.\x88\xe3\x80\x96b')==1911084682
assert aezeed._crc32c(b'\x06\xc5y\x18\xe2\xe7\xc6v\x04\xe3\xd2\x1ewka\xfd3-K')==2835540958
assert aezeed._crc32c(b'0\xc35@\xf5jL\x1f\n\xd9>\xfd\xd4\xfa+<d\x17\xd5\x0c')==3158695771
assert aezeed._crc32c(b'\xb7\x97\x10\x1e\x03\xeb\xd4\xe8\x8a\xe5\xd2kD;^\xcb\xce%\xfd\x83z')==2778644652
assert aezeed._crc32c(b'\xd2\xe4\x98\nA\xcbR\x9f\xe3\xbf\xd1\xcdQ\xae\x82*\x04\xf4$FnG')==127728431
assert aezeed._crc32c(b'\xd1\x02\xc2^\xfdM\xbd\xea\xea~\x95#\xe0\xd2\x9bhM\x1fj?\xc2\xa8\x1d')==2394168906
assert aezeed._crc32c(b"\xf5e\xceaL\xd5\x99 \x8a\x16\x1e\xfdQ\x92\xf2'\xf7\xdb\xce\x02\x11\xc1\x17X")==992436861
assert aezeed._crc32c(b'\x0b\xb0@g\r\x9f\xf6\xa3\x9d\xf1\x0c\x14^\x0b\x98\x9a\xdb\xf4X\xfd\xdd\nY\xc5\xb6')==3598957521
assert aezeed._crc32c(b'\xad\xc5\x0cM\xdcE\x91Q\xa52\xd8\xa2Sn\x05\x9f\xe8\xcd\xd1\xfe\x9ap\xd3\xfc\x16f')==1372250245
assert aezeed._crc32c(b'\xdeV`o\x88c\xdb\xa1MF*0\xfc.R\xfb}\xc5@H\xfc\xd9\xe0\x86_\xcaa')==1147805834
assert aezeed._crc32c(b'%E\xef\xfc\xde4\x13^\x81ie78\x153\xd8\xc6\x85#\x0f\x8b\xc3m! \xc3\x08\xd1')==136920505
assert aezeed._crc32c(b'7"c\x89\x11/\xc3\x96\x99\'\x1d\xb8~\xacpkQ\xa1Z\xe4s\xf9\xe6e\xcd\xb3\x85\xf1\xd9')==2567035617
assert aezeed._crc32c(b'\x05\x0f\xaaS\x80~\x18\t\x15H%a8a\xc5\xb5Sk6\xce\x8b\xc4I\x12\xacmD\xde\x11&')==1758343556
assert aezeed._crc32c(b'b\xcd\xafye\xfb\xa9[\xc7\xd4\x02\x81:QS,\xd3\xf6\xc9y\xbf]\x99\x0bg=\xc4c\xde0\xf8')==2781820724
aezeed_words=['ability', 'adult', 'worry', 'magnet', 'this', 'ice', 'trash', 'mean', 'assist', 'safe', 'real', 'belt', 'amateur', 'input', 'coyote', 'nurse', 'glare', 'fish', 'pipe', 'leaf', 'twin', 'beyond', 'foster', 'combine']
ambiguous_words=['able', 'crop', 'pole', 'battle', 'jar', 'squeeze', 'cycle', 'open', 'now', 'replace', 'resist', 'light', 'always', 'earth', 'about', 'media', 'only', 'taxi', 'corn', 'inflict', 'dream', 'drill', 'sugar', 'essay']
mapping={word:i for i,word in enumerate(Seed.get_wordlist())}
assert aezeed.has_valid_checksum(aezeed_words,mapping)
assert aezeed.has_valid_checksum(ambiguous_words,mapping)
invalid=list(aezeed_words)
invalid[-1]=Seed.get_wordlist()[(mapping[invalid[-1]]+1)%2048]
assert not aezeed.has_valid_checksum(invalid,mapping)
assert not aezeed.has_valid_checksum(['abandon']*12,mapping)
try:AezeedSeed(aezeed_words);assert False
except FeatureUnavailable:pass
try:aezeed._extract_key(bytes(32));assert False
except FeatureUnavailable:pass
for words,kind in ((aezeed_words,'aezeed'),(ambiguous_words,'ambiguous')):
    d=DecodeQR()
    assert d.add_data(' '.join(words))==DecodeQRStatus.COMPLETE
    assert d.decoder.seed_type==kind
d=DecodeQR()
assert d.add_data('abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'about']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('aban aban aban aban aban aban aban aban aban aban aban abou')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'about']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('000000000000000000000000000000000000000000000003')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'about']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('legal winner thank year wave sausage worth useful legal winner thank yellow')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['legal', 'winner', 'thank', 'year', 'wave', 'sausage', 'worth', 'useful', 'legal', 'winner', 'thank', 'yellow']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('lega winn than year wave saus wort usef lega winn than yell')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['legal', 'winner', 'thank', 'year', 'wave', 'sausage', 'worth', 'useful', 'legal', 'winner', 'thank', 'yellow']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('101920151790203919831533203119191019201517902040')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['legal', 'winner', 'thank', 'year', 'wave', 'sausage', 'worth', 'useful', 'legal', 'winner', 'thank', 'yellow']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('letter advice cage absurd amount doctor acoustic avoid letter advice cage above')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['letter', 'advice', 'cage', 'absurd', 'amount', 'doctor', 'acoustic', 'avoid', 'letter', 'advice', 'cage', 'above']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('lett advi cage absu amou doct acou avoi lett advi cage abov')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['letter', 'advice', 'cage', 'absurd', 'amount', 'doctor', 'acoustic', 'avoid', 'letter', 'advice', 'cage', 'above']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('102800320257000800640514001601281028003202570004')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['letter', 'advice', 'cage', 'absurd', 'amount', 'doctor', 'acoustic', 'avoid', 'letter', 'advice', 'cage', 'above']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo wrong')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'wrong']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo wron')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'wrong']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('204720472047204720472047204720472047204720472037')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'wrong']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon agent')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'agent']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('aban aban aban aban aban aban aban aban aban aban aban aban aban aban aban aban aban agen')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'agent']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('000000000000000000000000000000000000000000000000000000000000000000000039')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'agent']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('legal winner thank year wave sausage worth useful legal winner thank year wave sausage worth useful legal will')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['legal', 'winner', 'thank', 'year', 'wave', 'sausage', 'worth', 'useful', 'legal', 'winner', 'thank', 'year', 'wave', 'sausage', 'worth', 'useful', 'legal', 'will']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('lega winn than year wave saus wort usef lega winn than year wave saus wort usef lega will')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['legal', 'winner', 'thank', 'year', 'wave', 'sausage', 'worth', 'useful', 'legal', 'winner', 'thank', 'year', 'wave', 'sausage', 'worth', 'useful', 'legal', 'will']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('101920151790203919831533203119191019201517902039198315332031191910192009')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['legal', 'winner', 'thank', 'year', 'wave', 'sausage', 'worth', 'useful', 'legal', 'winner', 'thank', 'year', 'wave', 'sausage', 'worth', 'useful', 'legal', 'will']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('letter advice cage absurd amount doctor acoustic avoid letter advice cage absurd amount doctor acoustic avoid letter always')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['letter', 'advice', 'cage', 'absurd', 'amount', 'doctor', 'acoustic', 'avoid', 'letter', 'advice', 'cage', 'absurd', 'amount', 'doctor', 'acoustic', 'avoid', 'letter', 'always']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('lett advi cage absu amou doct acou avoi lett advi cage absu amou doct acou avoi lett alwa')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['letter', 'advice', 'cage', 'absurd', 'amount', 'doctor', 'acoustic', 'avoid', 'letter', 'advice', 'cage', 'absurd', 'amount', 'doctor', 'acoustic', 'avoid', 'letter', 'always']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('102800320257000800640514001601281028003202570008006405140016012810280060')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['letter', 'advice', 'cage', 'absurd', 'amount', 'doctor', 'acoustic', 'avoid', 'letter', 'advice', 'cage', 'absurd', 'amount', 'doctor', 'acoustic', 'avoid', 'letter', 'always']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo when')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'when']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo when')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'when']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('204720472047204720472047204720472047204720472047204720472047204720472001')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'when']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon art')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'art']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('aban aban aban aban aban aban aban aban aban aban aban aban aban aban aban aban aban aban aban aban aban aban aban art')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'art']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000102')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'abandon', 'art']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('legal winner thank year wave sausage worth useful legal winner thank year wave sausage worth useful legal winner thank year wave sausage worth title')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['legal', 'winner', 'thank', 'year', 'wave', 'sausage', 'worth', 'useful', 'legal', 'winner', 'thank', 'year', 'wave', 'sausage', 'worth', 'useful', 'legal', 'winner', 'thank', 'year', 'wave', 'sausage', 'worth', 'title']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('lega winn than year wave saus wort usef lega winn than year wave saus wort usef lega winn than year wave saus wort titl')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['legal', 'winner', 'thank', 'year', 'wave', 'sausage', 'worth', 'useful', 'legal', 'winner', 'thank', 'year', 'wave', 'sausage', 'worth', 'useful', 'legal', 'winner', 'thank', 'year', 'wave', 'sausage', 'worth', 'title']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('101920151790203919831533203119191019201517902039198315332031191910192015179020391983153320311815')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['legal', 'winner', 'thank', 'year', 'wave', 'sausage', 'worth', 'useful', 'legal', 'winner', 'thank', 'year', 'wave', 'sausage', 'worth', 'useful', 'legal', 'winner', 'thank', 'year', 'wave', 'sausage', 'worth', 'title']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('letter advice cage absurd amount doctor acoustic avoid letter advice cage absurd amount doctor acoustic avoid letter advice cage absurd amount doctor acoustic bless')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['letter', 'advice', 'cage', 'absurd', 'amount', 'doctor', 'acoustic', 'avoid', 'letter', 'advice', 'cage', 'absurd', 'amount', 'doctor', 'acoustic', 'avoid', 'letter', 'advice', 'cage', 'absurd', 'amount', 'doctor', 'acoustic', 'bless']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('lett advi cage absu amou doct acou avoi lett advi cage absu amou doct acou avoi lett advi cage absu amou doct acou bles')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['letter', 'advice', 'cage', 'absurd', 'amount', 'doctor', 'acoustic', 'avoid', 'letter', 'advice', 'cage', 'absurd', 'amount', 'doctor', 'acoustic', 'avoid', 'letter', 'advice', 'cage', 'absurd', 'amount', 'doctor', 'acoustic', 'bless']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('102800320257000800640514001601281028003202570008006405140016012810280032025700080064051400160189')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['letter', 'advice', 'cage', 'absurd', 'amount', 'doctor', 'acoustic', 'avoid', 'letter', 'advice', 'cage', 'absurd', 'amount', 'doctor', 'acoustic', 'avoid', 'letter', 'advice', 'cage', 'absurd', 'amount', 'doctor', 'acoustic', 'bless']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo vote')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'vote']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo vote')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'vote']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('204720472047204720472047204720472047204720472047204720472047204720472047204720472047204720471967')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'zoo', 'vote']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('ozone drill grab fiber curtain grace pudding thank cruise elder eight picnic')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['ozone', 'drill', 'grab', 'fiber', 'curtain', 'grace', 'pudding', 'thank', 'cruise', 'elder', 'eight', 'picnic']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('ozon dril grab fibe curt grac pudd than crui elde eigh picn')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['ozone', 'drill', 'grab', 'fiber', 'curtain', 'grace', 'pudding', 'thank', 'cruise', 'elder', 'eight', 'picnic']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('126805350810068504330811138517900421057005671313')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['ozone', 'drill', 'grab', 'fiber', 'curtain', 'grace', 'pudding', 'thank', 'cruise', 'elder', 'eight', 'picnic']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('gravity machine north sort system female filter attitude volume fold club stay feature office ecology stable narrow fog')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['gravity', 'machine', 'north', 'sort', 'system', 'female', 'filter', 'attitude', 'volume', 'fold', 'club', 'stay', 'feature', 'office', 'ecology', 'stable', 'narrow', 'fog']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('grav mach nort sort syst fema filt atti volu fold club stay feat offi ecol stab narr fog')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['gravity', 'machine', 'north', 'sort', 'system', 'female', 'filter', 'attitude', 'volume', 'fold', 'club', 'stay', 'feature', 'office', 'ecology', 'stable', 'narrow', 'fog']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('081610681202166017660679069101171966072403531703067312280560169411760722')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['gravity', 'machine', 'north', 'sort', 'system', 'female', 'filter', 'attitude', 'volume', 'fold', 'club', 'stay', 'feature', 'office', 'ecology', 'stable', 'narrow', 'fog']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('hamster diagram private dutch cause delay private meat slide toddler razor book happy fancy gospel tennis maple dilemma loan word shrug inflict delay length')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['hamster', 'diagram', 'private', 'dutch', 'cause', 'delay', 'private', 'meat', 'slide', 'toddler', 'razor', 'book', 'happy', 'fancy', 'gospel', 'tennis', 'maple', 'dilemma', 'loan', 'word', 'shrug', 'inflict', 'delay', 'length']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('hams diag priv dutc caus dela priv meat slid todd razo book happ fanc gosp tenn mapl dile loan word shru infl dela leng')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['hamster', 'diagram', 'private', 'dutch', 'cause', 'delay', 'private', 'meat', 'slide', 'toddler', 'razor', 'book', 'happy', 'fancy', 'gospel', 'tennis', 'maple', 'dilemma', 'loan', 'word', 'shrug', 'inflict', 'delay', 'length']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('083704871369054702920463136911041628181914290204083906630806178510840497104820271594092304631024')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['hamster', 'diagram', 'private', 'dutch', 'cause', 'delay', 'private', 'meat', 'slide', 'toddler', 'razor', 'book', 'happy', 'fancy', 'gospel', 'tennis', 'maple', 'dilemma', 'loan', 'word', 'shrug', 'inflict', 'delay', 'length']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('scheme spot photo card baby mountain device kick cradle pact join borrow')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['scheme', 'spot', 'photo', 'card', 'baby', 'mountain', 'device', 'kick', 'cradle', 'pact', 'join', 'borrow']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('sche spot phot card baby moun devi kick crad pact join borr')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['scheme', 'spot', 'photo', 'card', 'baby', 'mountain', 'device', 'kick', 'cradle', 'pact', 'join', 'borrow']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('154116861309027601361156048509770399126909610208')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['scheme', 'spot', 'photo', 'card', 'baby', 'mountain', 'device', 'kick', 'cradle', 'pact', 'join', 'borrow']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('horn tenant knee talent sponsor spell gate clip pulse soap slush warm silver nephew swap uncle crack brave')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['horn', 'tenant', 'knee', 'talent', 'sponsor', 'spell', 'gate', 'clip', 'pulse', 'soap', 'slush', 'warm', 'silver', 'nephew', 'swap', 'uncle', 'crack', 'brave']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('horn tena knee tale spon spel gate clip puls soap slus warm silv neph swap uncl crac brav')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['horn', 'tenant', 'knee', 'talent', 'sponsor', 'spell', 'gate', 'clip', 'pulse', 'soap', 'slush', 'warm', 'silver', 'nephew', 'swap', 'uncle', 'crack', 'brave']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('087617840988177116831673077003461388164516341977160611861754189203980218')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['horn', 'tenant', 'knee', 'talent', 'sponsor', 'spell', 'gate', 'clip', 'pulse', 'soap', 'slush', 'warm', 'silver', 'nephew', 'swap', 'uncle', 'crack', 'brave']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('panda eyebrow bullet gorilla call smoke muffin taste mesh discover soft ostrich alcohol speed nation flash devote level hobby quick inner drive ghost inside')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['panda', 'eyebrow', 'bullet', 'gorilla', 'call', 'smoke', 'muffin', 'taste', 'mesh', 'discover', 'soft', 'ostrich', 'alcohol', 'speed', 'nation', 'flash', 'devote', 'level', 'hobby', 'quick', 'inner', 'drive', 'ghost', 'inside']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('pand eyeb bull gori call smok muff tast mesh disc soft ostr alco spee nati flas devo leve hobb quic inne driv ghos insi')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['panda', 'eyebrow', 'bullet', 'gorilla', 'call', 'smoke', 'muffin', 'taste', 'mesh', 'discover', 'soft', 'ostrich', 'alcohol', 'speed', 'nation', 'flash', 'devote', 'level', 'hobby', 'quick', 'inner', 'drive', 'ghost', 'inside']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('127506500241080502591638116117771118050316501255004816721178070704861029086614050931053807800937')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['panda', 'eyebrow', 'bullet', 'gorilla', 'call', 'smoke', 'muffin', 'taste', 'mesh', 'discover', 'soft', 'ostrich', 'alcohol', 'speed', 'nation', 'flash', 'devote', 'level', 'hobby', 'quick', 'inner', 'drive', 'ghost', 'inside']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('cat swing flag economy stadium alone churn speed unique patch report train')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['cat', 'swing', 'flag', 'economy', 'stadium', 'alone', 'churn', 'speed', 'unique', 'patch', 'report', 'train']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('cat swin flag econ stad alon chur spee uniq patc repo trai')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['cat', 'swing', 'flag', 'economy', 'stadium', 'alone', 'churn', 'speed', 'unique', 'patch', 'report', 'train']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('028617600705056116950055032616721900128614631848')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['cat', 'swing', 'flag', 'economy', 'stadium', 'alone', 'churn', 'speed', 'unique', 'patch', 'report', 'train']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('light rule cinnamon wrap drastic word pride squirrel upgrade then income fatal apart sustain crack supply proud access')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['light', 'rule', 'cinnamon', 'wrap', 'drastic', 'word', 'pride', 'squirrel', 'upgrade', 'then', 'income', 'fatal', 'apart', 'sustain', 'crack', 'supply', 'proud', 'access']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('ligh rule cinn wrap dras word prid squi upgr then inco fata apar sust crac supp prou acce')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['light', 'rule', 'cinnamon', 'wrap', 'drastic', 'word', 'pride', 'squirrel', 'upgrade', 'then', 'income', 'fatal', 'apart', 'sustain', 'crack', 'supply', 'proud', 'access']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('103615130328203205302027136416931909179309160668008217510398174213820010')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['light', 'rule', 'cinnamon', 'wrap', 'drastic', 'word', 'pride', 'squirrel', 'upgrade', 'then', 'income', 'fatal', 'apart', 'sustain', 'crack', 'supply', 'proud', 'access']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('all hour make first leader extend hole alien behind guard gospel lava path output census museum junior mass reopen famous sing advance salt reform')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['all', 'hour', 'make', 'first', 'leader', 'extend', 'hole', 'alien', 'behind', 'guard', 'gospel', 'lava', 'path', 'output', 'census', 'museum', 'junior', 'mass', 'reopen', 'famous', 'sing', 'advance', 'salt', 'reform']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('all hour make firs lead exte hole alie behi guar gosp lava path outp cens muse juni mass reop famo sing adva salt refo')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['all', 'hour', 'make', 'first', 'leader', 'extend', 'hole', 'alien', 'behind', 'guard', 'gospel', 'lava', 'path', 'output', 'census', 'museum', 'junior', 'mass', 'reopen', 'famous', 'sing', 'advance', 'salt', 'reform']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('005108821076069910120647086900500164082608061006128712590298116509691092145906611610003115251442')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['all', 'hour', 'make', 'first', 'leader', 'extend', 'hole', 'alien', 'behind', 'guard', 'gospel', 'lava', 'path', 'output', 'census', 'museum', 'junior', 'mass', 'reopen', 'famous', 'sing', 'advance', 'salt', 'reform']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('vessel ladder alter error federal sibling chat ability sun glass valve picture')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['vessel', 'ladder', 'alter', 'error', 'federal', 'sibling', 'chat', 'ability', 'sun', 'glass', 'valve', 'picture']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('vess ladd alte erro fede sibl chat abil sun glas valv pict')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['vessel', 'ladder', 'alter', 'error', 'federal', 'sibling', 'chat', 'ability', 'sun', 'glass', 'valve', 'picture']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('194409950059061406751597031000011738079119281314')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['vessel', 'ladder', 'alter', 'error', 'federal', 'sibling', 'chat', 'ability', 'sun', 'glass', 'valve', 'picture']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('scissors invite lock maple supreme raw rapid void congress muscle digital elegant little brisk hair mango congress clump')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['scissors', 'invite', 'lock', 'maple', 'supreme', 'raw', 'rapid', 'void', 'congress', 'muscle', 'digital', 'elegant', 'little', 'brisk', 'hair', 'mango', 'congress', 'clump']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('scis invi lock mapl supr raw rapi void cong musc digi eleg litt bris hair mang cong clum')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['scissors', 'invite', 'lock', 'maple', 'supreme', 'raw', 'rapid', 'void', 'congress', 'muscle', 'digital', 'elegant', 'little', 'brisk', 'hair', 'mango', 'congress', 'clump']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('154409441051108417431428142319640376116404950572104402260834108103760354')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['scissors', 'invite', 'lock', 'maple', 'supreme', 'raw', 'rapid', 'void', 'congress', 'muscle', 'digital', 'elegant', 'little', 'brisk', 'hair', 'mango', 'congress', 'clump']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('void come effort suffer camp survey warrior heavy shoot primary clutch crush open amazing screen patrol group space point ten exist slush involve unfold')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['void', 'come', 'effort', 'suffer', 'camp', 'survey', 'warrior', 'heavy', 'shoot', 'primary', 'clutch', 'crush', 'open', 'amazing', 'screen', 'patrol', 'group', 'space', 'point', 'ten', 'exist', 'slush', 'involve', 'unfold']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('void come effo suff camp surv warr heav shoo prim clut crus open amaz scre patr grou spac poin ten exis slus invo unfo')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['void', 'come', 'effort', 'suffer', 'camp', 'survey', 'warrior', 'heavy', 'shoot', 'primary', 'clutch', 'crush', 'open', 'amazing', 'screen', 'patrol', 'group', 'space', 'point', 'ten', 'exist', 'slush', 'involve', 'unfold']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('196403680565173302621749197808511588136503560424124100621548128908231666133817830638163409451897')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['void', 'come', 'effort', 'suffer', 'camp', 'survey', 'warrior', 'heavy', 'shoot', 'primary', 'clutch', 'crush', 'open', 'amazing', 'screen', 'patrol', 'group', 'space', 'point', 'ten', 'exist', 'slush', 'involve', 'unfold']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('abandon amount liar amount expire adjust cage candy arch gather drum bullet absurd math exhibit')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['abandon', 'amount', 'liar', 'amount', 'expire', 'adjust', 'cage', 'candy', 'arch', 'gather', 'drum', 'bullet', 'absurd', 'math', 'exhibit']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('aban amou liar amou expi adju cage cand arch gath drum bull absu math exhi')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['abandon', 'amount', 'liar', 'amount', 'expire', 'adjust', 'cage', 'candy', 'arch', 'gather', 'drum', 'bullet', 'absurd', 'math', 'exhibit']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('000000641030006406430028025702660088077105400241000810960636')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['abandon', 'amount', 'liar', 'amount', 'expire', 'adjust', 'cage', 'candy', 'arch', 'gather', 'drum', 'bullet', 'absurd', 'math', 'exhibit']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('abandon amount liar amount expire adjust cage candy arch gather drum bullet absurd math era live bid rhythm alien crouch saddle')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['abandon', 'amount', 'liar', 'amount', 'expire', 'adjust', 'cage', 'candy', 'arch', 'gather', 'drum', 'bullet', 'absurd', 'math', 'era', 'live', 'bid', 'rhythm', 'alien', 'crouch', 'saddle']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('aban amou liar amou expi adju cage cand arch gath drum bull absu math era live bid rhyt alie crou sadd')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['abandon', 'amount', 'liar', 'amount', 'expire', 'adjust', 'cage', 'candy', 'arch', 'gather', 'drum', 'bullet', 'absurd', 'math', 'era', 'live', 'bid', 'rhythm', 'alien', 'crouch', 'saddle']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
d=DecodeQR()
assert d.add_data('000000641030006406430028025702660088077105400241000810960610104501761478005004171518')==DecodeQRStatus.COMPLETE
assert d.get_seed_phrase()==['abandon', 'amount', 'liar', 'amount', 'expire', 'adjust', 'cage', 'candy', 'arch', 'gather', 'drum', 'bullet', 'absurd', 'math', 'era', 'live', 'bid', 'rhythm', 'alien', 'crouch', 'saddle']
assert d.decoder.seed_type=='bip39'
del d
gc.collect()
assert camera.settings()['rust_heap_bytes']==baseline
print('@@PASS original-mnemonic-recognition-shamir-recovery',45,26,35)
