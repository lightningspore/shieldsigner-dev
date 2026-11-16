# SPDX-License-Identifier: MIT
# Public REF CPython15.0 oracle cases; no wallet secrets.
import unicodedata as u
import camera
import gc

assert u.unidata_version == '15.0.0'
baseline = camera.settings()['rust_heap_bytes']
assert u.normalize('NFC', '') == ''
assert u.is_normalized('NFC', '') == True
assert u.normalize('NFC', 'é') == 'é'
assert u.is_normalized('NFC', 'é') == True
assert u.normalize('NFC', 'é') == 'é'
assert u.is_normalized('NFC', 'é') == False
assert u.normalize('NFC', 'Å') == 'Å'
assert u.is_normalized('NFC', 'Å') == False
assert u.normalize('NFC', 'ﬁ') == 'ﬁ'
assert u.is_normalized('NFC', 'ﬁ') == True
assert u.normalize('NFC', 'Ａ') == 'Ａ'
assert u.is_normalized('NFC', 'Ａ') == True
assert u.normalize('NFC', 'ﷺ') == 'ﷺ'
assert u.is_normalized('NFC', 'ﷺ') == True
assert u.normalize('NFC', '각') == '각'
assert u.is_normalized('NFC', '각') == True
assert u.normalize('NFC', '각') == '각'
assert u.is_normalized('NFC', '각') == False
assert u.normalize('NFC', 'à̕') == 'à̕'
assert u.is_normalized('NFC', 'à̕') == False
assert u.normalize('NFC', '𞀰') == '𞀰'
assert u.is_normalized('NFC', '𞀰') == True
assert u.normalize('NFC', '𜳖') == '𜳖'
assert u.is_normalized('NFC', '𜳖') == True
assert u.normalize('NFC', '㍍ガバヴァぱばぐゞちぢ十人十色') == '㍍ガバヴァぱばぐゞちぢ十人十色'
assert u.is_normalized('NFC', '㍍ガバヴァぱばぐゞちぢ十人十色') == True
assert u.normalize('NFC', 'public\x00text') == 'public\x00text'
assert u.is_normalized('NFC', 'public\x00text') == True
assert u.normalize('NFC', '🙂') == '🙂'
assert u.is_normalized('NFC', '🙂') == True
assert u.normalize('NFD', '') == ''
assert u.is_normalized('NFD', '') == True
assert u.normalize('NFD', 'é') == 'é'
assert u.is_normalized('NFD', 'é') == False
assert u.normalize('NFD', 'é') == 'é'
assert u.is_normalized('NFD', 'é') == True
assert u.normalize('NFD', 'Å') == 'Å'
assert u.is_normalized('NFD', 'Å') == False
assert u.normalize('NFD', 'ﬁ') == 'ﬁ'
assert u.is_normalized('NFD', 'ﬁ') == True
assert u.normalize('NFD', 'Ａ') == 'Ａ'
assert u.is_normalized('NFD', 'Ａ') == True
assert u.normalize('NFD', 'ﷺ') == 'ﷺ'
assert u.is_normalized('NFD', 'ﷺ') == True
assert u.normalize('NFD', '각') == '각'
assert u.is_normalized('NFD', '각') == False
assert u.normalize('NFD', '각') == '각'
assert u.is_normalized('NFD', '각') == True
assert u.normalize('NFD', 'à̕') == 'à̕'
assert u.is_normalized('NFD', 'à̕') == False
assert u.normalize('NFD', '𞀰') == '𞀰'
assert u.is_normalized('NFD', '𞀰') == True
assert u.normalize('NFD', '𜳖') == '𜳖'
assert u.is_normalized('NFD', '𜳖') == True
assert u.normalize('NFD', '㍍ガバヴァぱばぐゞちぢ十人十色') == '㍍ガバヴァぱばぐゞちぢ十人十色'
assert u.is_normalized('NFD', '㍍ガバヴァぱばぐゞちぢ十人十色') == False
assert u.normalize('NFD', 'public\x00text') == 'public\x00text'
assert u.is_normalized('NFD', 'public\x00text') == True
assert u.normalize('NFD', '🙂') == '🙂'
assert u.is_normalized('NFD', '🙂') == True
assert u.normalize('NFKC', '') == ''
assert u.is_normalized('NFKC', '') == True
assert u.normalize('NFKC', 'é') == 'é'
assert u.is_normalized('NFKC', 'é') == True
assert u.normalize('NFKC', 'é') == 'é'
assert u.is_normalized('NFKC', 'é') == False
assert u.normalize('NFKC', 'Å') == 'Å'
assert u.is_normalized('NFKC', 'Å') == False
assert u.normalize('NFKC', 'ﬁ') == 'fi'
assert u.is_normalized('NFKC', 'ﬁ') == False
assert u.normalize('NFKC', 'Ａ') == 'A'
assert u.is_normalized('NFKC', 'Ａ') == False
assert u.normalize('NFKC', 'ﷺ') == 'صلى الله عليه وسلم'
assert u.is_normalized('NFKC', 'ﷺ') == False
assert u.normalize('NFKC', '각') == '각'
assert u.is_normalized('NFKC', '각') == True
assert u.normalize('NFKC', '각') == '각'
assert u.is_normalized('NFKC', '각') == False
assert u.normalize('NFKC', 'à̕') == 'à̕'
assert u.is_normalized('NFKC', 'à̕') == False
assert u.normalize('NFKC', '𞀰') == 'а'
assert u.is_normalized('NFKC', '𞀰') == False
assert u.normalize('NFKC', '𜳖') == '𜳖'
assert u.is_normalized('NFKC', '𜳖') == True
assert (
    u.normalize('NFKC', '㍍ガバヴァぱばぐゞちぢ十人十色') == 'メートルガバヴァぱばぐゞちぢ十人十色'
)
assert u.is_normalized('NFKC', '㍍ガバヴァぱばぐゞちぢ十人十色') == False
assert u.normalize('NFKC', 'public\x00text') == 'public\x00text'
assert u.is_normalized('NFKC', 'public\x00text') == True
assert u.normalize('NFKC', '🙂') == '🙂'
assert u.is_normalized('NFKC', '🙂') == True
assert u.normalize('NFKD', '') == ''
assert u.is_normalized('NFKD', '') == True
assert u.normalize('NFKD', 'é') == 'é'
assert u.is_normalized('NFKD', 'é') == False
assert u.normalize('NFKD', 'é') == 'é'
assert u.is_normalized('NFKD', 'é') == True
assert u.normalize('NFKD', 'Å') == 'Å'
assert u.is_normalized('NFKD', 'Å') == False
assert u.normalize('NFKD', 'ﬁ') == 'fi'
assert u.is_normalized('NFKD', 'ﬁ') == False
assert u.normalize('NFKD', 'Ａ') == 'A'
assert u.is_normalized('NFKD', 'Ａ') == False
assert u.normalize('NFKD', 'ﷺ') == 'صلى الله عليه وسلم'
assert u.is_normalized('NFKD', 'ﷺ') == False
assert u.normalize('NFKD', '각') == '각'
assert u.is_normalized('NFKD', '각') == False
assert u.normalize('NFKD', '각') == '각'
assert u.is_normalized('NFKD', '각') == True
assert u.normalize('NFKD', 'à̕') == 'à̕'
assert u.is_normalized('NFKD', 'à̕') == False
assert u.normalize('NFKD', '𞀰') == 'а'
assert u.is_normalized('NFKD', '𞀰') == False
assert u.normalize('NFKD', '𜳖') == '𜳖'
assert u.is_normalized('NFKD', '𜳖') == True
assert (
    u.normalize('NFKD', '㍍ガバヴァぱばぐゞちぢ十人十色') == 'メートルガバヴァぱばぐゞちぢ十人十色'
)
assert u.is_normalized('NFKD', '㍍ガバヴァぱばぐゞちぢ十人十色') == False
assert u.normalize('NFKD', 'public\x00text') == 'public\x00text'
assert u.is_normalized('NFKD', 'public\x00text') == True
assert u.normalize('NFKD', '🙂') == '🙂'
assert u.is_normalized('NFKD', '🙂') == True
assert u.normalize('bad', '') == ''
for form, text, error in [
    ('bad', 'x', ValueError),
    ('NFC' + chr(0) + 'x', 'x', ValueError),
    (b'NFC', '', TypeError),
    ('NFKD', b'x', TypeError),
    ('NFKD', 'x' * 65537, ValueError),
]:
    try:
        u.normalize(form, text)
    except error:
        pass
    else:
        raise AssertionError('invalid normalization input accepted')
for i in range(100):
    text = 'a' + chr(0x315) * 100 + chr(0x300) * 100
    result = u.normalize('NFD', text)
    assert result == 'a' + chr(0x300) * 100 + chr(0x315) * 100
    gc.collect()
    assert camera.settings()['rust_heap_bytes'] == baseline
print('@@PASS native-unicode15-normalization')
