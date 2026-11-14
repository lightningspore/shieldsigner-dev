# Public synthetic data; actual original checker + native embit, not signing.
import binascii
from seedsigner_port.psbt_framing import parse_psbt
from seedsigner_port.psbt_errors import InvalidPSBTError
from seedsigner_port.decode_platform import FeatureUnavailable
from seedsigner_port.decode_qr import DecodeQR,DecodeQRStatus
from embit import ec
import camera
import gc
baseline=camera.settings()['rust_heap_bytes']
raw=binascii.unhexlify('70736274ff01003d020000000111111111111111111111111111111111111111111111111111111111111111110000000000ffffffff01e803000000000000015100000000000000')
result='unexpected'
try:
    parsed=parse_psbt(raw)
    result='ok'
    assert parsed.serialize().hex()=='70736274ff01003d020000000111111111111111111111111111111111111111111111111111111111111111110000000000ffffffff01e803000000000000015100000000000000'
except FeatureUnavailable:raise
except InvalidPSBTError as e:result='reject:'+e.code
except Exception as e:result='error:'+type(e).__name__
assert result=='ok',('valid-v0',result)
gc.collect()
raw=binascii.unhexlify('70736274ff01fb040200000001020402000000010401010105010100010e201111111111111111111111111111111111111111111111111111111111111111010f040000000000010308e8030000000000000104015100')
result='unexpected'
try:
    parsed=parse_psbt(raw)
    result='ok'
    assert parsed.serialize().hex()=='70736274ff01020402000000010401010105010101fb040200000000010e201111111111111111111111111111111111111111111111111111111111111111010f0400000000011004ffffffff00010308e8030000000000000104015100'
except FeatureUnavailable:raise
except InvalidPSBTError as e:result='reject:'+e.code
except Exception as e:result='error:'+type(e).__name__
assert result=='ok',('valid-v2',result)
gc.collect()
raw=binascii.unhexlify('70736274ff01fb040200000001fb040200000000')
result='unexpected'
try:
    parsed=parse_psbt(raw)
    result='ok'
except FeatureUnavailable:raise
except InvalidPSBTError as e:result='reject:'+e.code
except Exception as e:result='error:'+type(e).__name__
assert result=='reject:MALFORMED_ENCODING',('duplicate',result)
gc.collect()
raw=binascii.unhexlify('70736274fffd0100fb040000000000')
result='unexpected'
try:
    parsed=parse_psbt(raw)
    result='ok'
except FeatureUnavailable:raise
except InvalidPSBTError as e:result='reject:'+e.code
except Exception as e:result='error:'+type(e).__name__
assert result=='reject:MALFORMED_ENCODING',('nonminimal-key-length',result)
gc.collect()
raw=binascii.unhexlify('70736274ff03fd01000000')
result='unexpected'
try:
    parsed=parse_psbt(raw)
    result='ok'
except FeatureUnavailable:raise
except InvalidPSBTError as e:result='reject:'+e.code
except Exception as e:result='error:'+type(e).__name__
assert result=='reject:MALFORMED_ENCODING',('nonminimal-type',result)
gc.collect()
raw=binascii.unhexlify('70736274ff01fbfd04000000000000')
result='unexpected'
try:
    parsed=parse_psbt(raw)
    result='ok'
except FeatureUnavailable:raise
except InvalidPSBTError as e:result='reject:'+e.code
except Exception as e:result='error:'+type(e).__name__
assert result=='reject:MALFORMED_ENCODING',('nonminimal-value',result)
gc.collect()
raw=binascii.unhexlify('70736274ff01003d020000000111111111111111111111111111111111111111111111111111111111111111110000000000ffffffff01e80300000000000001510000000001020400000000000000')
result='unexpected'
try:
    parsed=parse_psbt(raw)
    result='ok'
except FeatureUnavailable:raise
except InvalidPSBTError as e:result='reject:'+e.code
except Exception as e:result='error:'+type(e).__name__
assert result=='reject:WRONG_VERSION_FIELD',('v0-global-v2-field',result)
gc.collect()
raw=binascii.unhexlify('70736274ff01003d020000000111111111111111111111111111111111111111111111111111111111111111110000000000ffffffff01e80300000000000001510000000000010e2011111111111111111111111111111111111111111111111111111111111111110000')
result='unexpected'
try:
    parsed=parse_psbt(raw)
    result='ok'
except FeatureUnavailable:raise
except InvalidPSBTError as e:result='reject:'+e.code
except Exception as e:result='error:'+type(e).__name__
assert result=='reject:WRONG_VERSION_FIELD',('v0-input-v2-field',result)
gc.collect()
raw=binascii.unhexlify('70736274ff01003d020000000111111111111111111111111111111111111111111111111111111111111111110000000000ffffffff01e8030000000000000151000000000000010308000000000000000000')
result='unexpected'
try:
    parsed=parse_psbt(raw)
    result='ok'
except FeatureUnavailable:raise
except InvalidPSBTError as e:result='reject:'+e.code
except Exception as e:result='error:'+type(e).__name__
assert result=='reject:WRONG_VERSION_FIELD',('v0-output-v2-field',result)
gc.collect()
raw=binascii.unhexlify('70736274ff01fb040200000001020402000000010401010105010101003d020000000111111111111111111111111111111111111111111111111111111111111111110000000000ffffffff01e80300000000000001510000000000010e201111111111111111111111111111111111111111111111111111111111111111010f040000000000010308e8030000000000000104015100')
result='unexpected'
try:
    parsed=parse_psbt(raw)
    result='ok'
except FeatureUnavailable:raise
except InvalidPSBTError as e:result='reject:'+e.code
except Exception as e:result='error:'+type(e).__name__
assert result=='reject:WRONG_VERSION_FIELD',('v2-global-tx',result)
gc.collect()
raw=binascii.unhexlify('70736274ff01fb0402000000010405feffffffff0105010100')
result='unexpected'
try:
    parsed=parse_psbt(raw)
    result='ok'
except FeatureUnavailable:raise
except InvalidPSBTError as e:result='reject:'+e.code
except Exception as e:result='error:'+type(e).__name__
assert result=='reject:MALFORMED_ENCODING',('v2-impossible-count',result)
gc.collect()
raw=binascii.unhexlify('70736274ff01fb040200000001040201000105010100')
result='unexpected'
try:
    parsed=parse_psbt(raw)
    result='ok'
except FeatureUnavailable:raise
except InvalidPSBTError as e:result='reject:'+e.code
except Exception as e:result='error:'+type(e).__name__
assert result=='reject:MALFORMED_ENCODING',('count-extra',result)
gc.collect()
raw=binascii.unhexlify('70736274ff01003d020000000111111111111111111111111111111111111111111111111111111111111111110000000000ffffffff01e80300000000000001510000000000000000')
result='unexpected'
try:
    parsed=parse_psbt(raw)
    result='ok'
except FeatureUnavailable:raise
except InvalidPSBTError as e:result='reject:'+e.code
except Exception as e:result='error:'+type(e).__name__
assert result=='reject:MALFORMED_ENCODING',('trailing',result)
gc.collect()
raw=binascii.unhexlify('70736274ff01003d020000000111111111111111111111111111111111111111111111111111111111111111110000000000ffffffff01e803000000000000015100000000')
result='unexpected'
try:
    parsed=parse_psbt(raw)
    result='ok'
except FeatureUnavailable:raise
except InvalidPSBTError as e:result='reject:'+e.code
except Exception as e:result='error:'+type(e).__name__
assert result=='error:RuntimeError',('truncated',result)
gc.collect()
raw=binascii.unhexlify('7075626c69632d6e6f742d70736274')
result='unexpected'
try:
    parsed=parse_psbt(raw)
    result='ok'
except FeatureUnavailable:raise
except InvalidPSBTError as e:result='reject:'+e.code
except Exception as e:result='error:'+type(e).__name__
assert result=='error:PSBTError',('wrong-magic',result)
gc.collect()
try:
    ec.PublicKey.parse(binascii.unhexlify('0279be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798'))
    assert False
except FeatureUnavailable:pass
try:
    ec.NUMS_PUBKEY
    assert False
except FeatureUnavailable:pass
d=DecodeQR()
status=d.add_data('0000'*11+'0003')
assert status==DecodeQRStatus.COMPLETE and d.is_complete
assert d.get_seed_phrase()==['abandon']*11+['about']
assert camera.settings()['rust_heap_bytes']==baseline
print('@@PASS original-psbt-framing-and-numeric-seedqr',15)
