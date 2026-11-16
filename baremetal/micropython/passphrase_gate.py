# Public fixtures, saved REF oracle; not private passphrases.
from seedsigner_port.passphrase import normalize_passphrase
import camera
import gc

baseline = camera.settings()['rust_heap_bytes']
assert normalize_passphrase('') == ''
assert normalize_passphrase('é') == 'é'
assert normalize_passphrase('é') == 'é'
assert (
    normalize_passphrase('㍍ガバヴァぱばぐゞちぢ十人十色') == 'メートルガバヴァぱばぐゞちぢ十人十色'
)
assert normalize_passphrase('\x00') == '\x00'
assert normalize_passphrase('\\u0061') == 'a'
assert normalize_passphrase('\\\\u0061') == '\\a'
assert normalize_passphrase('\\u005cu0061') == '\\u0061'
assert normalize_passphrase('\\uD800\\uZ') == '\\uD800\\uZ'
assert normalize_passphrase('\\u') == '\\u'
assert normalize_passphrase('\\u123') == '\\u123'
assert normalize_passphrase('\\U0001f600') == '\\U0001f600'
assert normalize_passphrase('\\n') == '\\n'
assert normalize_passphrase('abc\\') == 'abc\\'
assert normalize_passphrase('\\x41') == '\\x41'
try:
    normalize_passphrase('\\uDFFFﷺ')
    assert False
except UnicodeError:
    pass
try:
    normalize_passphrase('\\u0061ﷺaガ\\uDFFF😀\\u0061a😀')
    assert False
except UnicodeError:
    pass
assert (
    normalize_passphrase('\x00\x00\\uZ\\uDFFF\\uDFFFガ\\u0061\\uD800é\\uD800\x00ﷺ\\u123\\')
    == '\x00\x00\\uZ\\uDFFF\\uDFFFガ\\u0061\\uD800é\\uD800\x00صلى الله عليه وسلم\\u123\\'
)
try:
    normalize_passphrase('\\u00e9é\\u00e9ガ😀\\u0061U\\uDFFF\\u00e9\\é')
    assert False
except UnicodeError:
    pass
assert (
    normalize_passphrase('\\u00e9\\x20\\u0061ガ\\u123\\u00e9\\u0061\x00\\uZ')
    == '\\u00e9\\x20\\u0061ガ\\u123\\u00e9\\u0061\x00\\uZ'
)
try:
    normalize_passphrase('\\u0061\\uDFFF\\u00e9u\\u0061😀ﷺ😀é\x00\\u0061\\x20éé')
    assert False
except UnicodeError:
    pass
assert (
    normalize_passphrase('\\uD800ﷺﷺ\\u0061\\x20ﷺ\\ガ\\uDFFFガé\\uZ\\uD800')
    == '\\uD800صلى الله عليه وسلمصلى الله عليه وسلم\\u0061\\x20صلى الله عليه وسلم\\ガ\\uDFFFガé\\uZ\\uD800'
)
try:
    normalize_passphrase('ﷺガ\\uD800a\x00\\x20\\uD800😀😀\\u0061')
    assert False
except UnicodeError:
    pass
assert normalize_passphrase('\\uZéé\\u00e9a\\\x00\\u00e9ガ') == '\\uZéé\\u00e9a\\\x00\\u00e9ガ'
try:
    normalize_passphrase('\\\\\\uDFFFガ\\u0061\\uD800\\u00e9')
    assert False
except UnicodeError:
    pass
assert normalize_passphrase('\\uZ\\uZガUua\\u123é\\') == '\\uZ\\uZガUua\\u123é\\'
assert (
    normalize_passphrase('\\x20\\u0061u\\u0061\\uZu\\ﷺ')
    == '\\x20\\u0061u\\u0061\\uZu\\صلى الله عليه وسلم'
)
assert (
    normalize_passphrase('\\u123ﷺ\\u123U😀\\uD800é\\u123')
    == '\\u123صلى الله عليه وسلم\\u123U😀\\uD800é\\u123'
)
assert normalize_passphrase('u\\u123a\\uZ\\u123\\u00e9') == 'u\\u123a\\uZ\\u123\\u00e9'
assert (
    normalize_passphrase('\\u00e9\\u00e9\x00\\u00e9\\uZ\\uDFFF\\\x00aa\\uZ\\uD800\\u123')
    == '\\u00e9\\u00e9\x00\\u00e9\\uZ\\uDFFF\\\x00aa\\uZ\\uD800\\u123'
)
assert normalize_passphrase('\\uZ') == '\\uZ'
assert normalize_passphrase('😀u\\u00e9ué') == '😀uéué'
assert (
    normalize_passphrase('é😀\\uZ\\u123\\uZ\x00\x00é\\u00e9\\u123ﷺガ\x00\\u00e9')
    == 'é😀\\uZ\\u123\\uZ\x00\x00é\\u00e9\\u123صلى الله عليه وسلمガ\x00\\u00e9'
)
try:
    normalize_passphrase('😀😀\\\\u00e9\\uD800\\u00e9ガ\x00')
    assert False
except UnicodeError:
    pass
try:
    normalize_passphrase('auUガ\\uDFFFガU\\x20\\uD800éa\\uDFFF')
    assert False
except UnicodeError:
    pass
assert normalize_passphrase('ﷺ\\') == 'صلى الله عليه وسلم\\'
assert normalize_passphrase('\\u123\\\\uZ\\uZ') == '\\u123\\\\uZ\\uZ'
assert normalize_passphrase('\\u00e9\x00U\\ﷺ') == 'é\x00U\\صلى الله عليه وسلم'
assert normalize_passphrase('\\a😀\\uZ\\x20Uガé') == '\\a😀\\uZ\\x20Uガé'
assert (
    normalize_passphrase('\x00\\u123ﷺガ\\u0061\\u00e9\\uZa\\uDFFF\\UU')
    == '\x00\\u123صلى الله عليه وسلمガ\\u0061\\u00e9\\uZa\\uDFFF\\UU'
)
try:
    normalize_passphrase('U\x00\\u0061U\\uD800')
    assert False
except UnicodeError:
    pass
assert normalize_passphrase('\\x20U😀\x00\\u123\\u') == '\\x20U😀\x00\\u123\\u'
assert normalize_passphrase('\\u123Uガ\\') == '\\u123Uガ\\'
try:
    normalize_passphrase('\\\x00Uガガé\\x20\\uDFFF')
    assert False
except UnicodeError:
    pass
assert (
    normalize_passphrase('ﷺ\\u0061é\\u00e9\\uDFFF\\x20ガ\\x20ガ\\u123\\u123\\uDFFF\\x20')
    == 'صلى الله عليه وسلم\\u0061é\\u00e9\\uDFFF\\x20ガ\\x20ガ\\u123\\u123\\uDFFF\\x20'
)
try:
    normalize_passphrase('😀\\uDFFF\\\\\\u00e9Ué')
    assert False
except UnicodeError:
    pass
assert normalize_passphrase('\x00\\uDFFFUUu\\uZé\\u123') == '\x00\\uDFFFUUu\\uZé\\u123'
try:
    normalize_passphrase('\\uD800\\x20')
    assert False
except UnicodeError:
    pass
assert (
    normalize_passphrase('😀u\\u00e9a\\u0061\x00\\x20😀\\u123😀ガ\\u00e9uガ')
    == '😀u\\u00e9a\\u0061\x00\\x20😀\\u123😀ガ\\u00e9uガ'
)
try:
    normalize_passphrase('\\\\uD800\\x20')
    assert False
except UnicodeError:
    pass
assert normalize_passphrase('a😀\\u0061\\\\u00e9uUガ') == 'a😀a\\éuUガ'
assert (
    normalize_passphrase('\x00\\uDFFF\\uDFFFガ\x00ué\\uZ\x00\\u00e9\\uZ')
    == '\x00\\uDFFF\\uDFFFガ\x00ué\\uZ\x00\\u00e9\\uZ'
)
assert normalize_passphrase('\\uDFFF\x00\\\x00\\u00e9\\uZ') == '\\uDFFF\x00\\\x00\\u00e9\\uZ'
assert normalize_passphrase('\\u00e9ﷺ\\é\\aa') == 'éصلى الله عليه وسلم\\é\\aa'
assert normalize_passphrase('U\\uZ\x00') == 'U\\uZ\x00'
assert normalize_passphrase('\\u0061\\uD800ﷺ\\u123') == '\\u0061\\uD800صلى الله عليه وسلم\\u123'
assert (
    normalize_passphrase('\\u123\\uZ\\ﷺ\\\\uDFFF\\u123\x00\\uD800\\u0061\\\\uDFFF')
    == '\\u123\\uZ\\صلى الله عليه وسلم\\\\uDFFF\\u123\x00\\uD800\\u0061\\\\uDFFF'
)
try:
    normalize_passphrase('u\\u0061😀éUガéééu\\uD800')
    assert False
except UnicodeError:
    pass
assert normalize_passphrase('\\U\\u123\\u00e9\\u123a\\u0061é') == '\\U\\u123\\u00e9\\u123a\\u0061é'
assert (
    normalize_passphrase('\\uDFFFaU\\u123ﷺ\\u0061ﷺé\\uDFFF\\u00e9éﷺ\x00')
    == '\\uDFFFaU\\u123صلى الله عليه وسلم\\u0061صلى الله عليه وسلمé\\uDFFF\\u00e9éصلى الله عليه وسلم\x00'
)
assert normalize_passphrase('\\u0061\\u00e9é\\uZu\\u123ガ') == '\\u0061\\u00e9é\\uZu\\u123ガ'
assert (
    normalize_passphrase('ガ\\u123\\u123ﷺaガ\\uDFFF\\u123')
    == 'ガ\\u123\\u123صلى الله عليه وسلمaガ\\uDFFF\\u123'
)
assert normalize_passphrase('😀ガ\\u123\\u00e9\\uDFFFガa\\ガ') == '😀ガ\\u123\\u00e9\\uDFFFガa\\ガ'
assert (
    normalize_passphrase('\\uZ\\u00e9ガ😀\x00\\\\\\x20😀😀😀U')
    == '\\uZ\\u00e9ガ😀\x00\\\\\\x20😀😀😀U'
)
assert normalize_passphrase('\\uZガa😀\\uZUé') == '\\uZガa😀\\uZUé'
assert normalize_passphrase('\\x20é\x00ua\\\x00ガ\\u0061') == '\\x20é\x00ua\\\x00ガa'
try:
    normalize_passphrase('ガガ\\\\u0061\x00\\uD800')
    assert False
except UnicodeError:
    pass
assert normalize_passphrase('\\uZﷺ\\x20\\é\\x20u') == '\\uZصلى الله عليه وسلم\\x20\\é\\x20u'
try:
    normalize_passphrase('a\x00é\\uD800\\u00e9ガ')
    assert False
except UnicodeError:
    pass
assert normalize_passphrase('\\u123ﷺUu\\u123') == '\\u123صلى الله عليه وسلمUu\\u123'
assert normalize_passphrase('\\u123\x00\\x20u\\u0061\\uD800') == '\\u123\x00\\x20u\\u0061\\uD800'
assert normalize_passphrase('éu😀') == 'éu😀'
assert normalize_passphrase('ﷺ\\u0061\\uZ\\é') == 'صلى الله عليه وسلم\\u0061\\uZ\\é'
assert normalize_passphrase('\\u00e9ﷺé😀😀Ua\\') == 'éصلى الله عليه وسلمé😀😀Ua\\'
assert normalize_passphrase('ガガﷺ\\u00e9') == 'ガガصلى الله عليه وسلمé'
assert (
    normalize_passphrase('\\u00e9\\x20\\\\u00e9\\\\uZ\\uDFFF\x00ééﷺ')
    == '\\u00e9\\x20\\\\u00e9\\\\uZ\\uDFFF\x00ééصلى الله عليه وسلم'
)
assert normalize_passphrase('\\u123') == '\\u123'
assert (
    normalize_passphrase('U😀\x00\\u123éﷺ\\uDFFFガ\\uDFFF\\\\u0061\\uD800\\uDFFF\\x20')
    == 'U😀\x00\\u123éصلى الله عليه وسلم\\uDFFFガ\\uDFFF\\\\u0061\\uD800\\uDFFF\\x20'
)
assert (
    normalize_passphrase('😀\\uZ\\x20ガ\\uDFFF\\u0061U\\u0061\\x20a')
    == '😀\\uZ\\x20ガ\\uDFFF\\u0061U\\u0061\\x20a'
)
assert normalize_passphrase('\\U\\uZ\\u123\\uD800\x00') == '\\U\\uZ\\u123\\uD800\x00'
assert (
    normalize_passphrase('éé\\uDFFF\\uZ\\u00e9\\uDFFFu\\uZ\\uZ\\')
    == 'éé\\uDFFF\\uZ\\u00e9\\uDFFFu\\uZ\\uZ\\'
)
try:
    normalize_passphrase('\\uDFFFaU\\uDFFF')
    assert False
except UnicodeError:
    pass
try:
    normalize_passphrase('\\uDFFF\\x20a\x00aガ\x00\x00u\x00\\u00e9')
    assert False
except UnicodeError:
    pass
try:
    normalize_passphrase('\\uDFFF')
    assert False
except UnicodeError:
    pass
try:
    normalize_passphrase('\\u0061é\\uD800a\\uDFFFﷺﷺﷺé\\uDFFFガ')
    assert False
except UnicodeError:
    pass
try:
    normalize_passphrase('ﷺ\\uD800\x00\\uDFFFU\\uD800\\u00e9\\uD800é\\u00e9')
    assert False
except UnicodeError:
    pass
try:
    normalize_passphrase('\\uDFFF\\u0061\\u00e9ﷺé\\u00e9é')
    assert False
except UnicodeError:
    pass
assert normalize_passphrase('a😀\\u00e9') == 'a😀é'
assert (
    normalize_passphrase('\\u123ﷺ\\u0061\\x20uﷺ\x00')
    == '\\u123صلى الله عليه وسلم\\u0061\\x20uصلى الله عليه وسلم\x00'
)
assert normalize_passphrase('\\u123UUaガa\\x20\\uD800a') == '\\u123UUaガa\\x20\\uD800a'
assert normalize_passphrase('\\u0061\\u0061\\uZa\\u0061') == '\\u0061\\u0061\\uZa\\u0061'
assert normalize_passphrase('\\u123\\uZガ\\u00e9') == '\\u123\\uZガ\\u00e9'
try:
    normalize_passphrase('😀\\ﷺ\\x20\x00ガU\\u0061\x00\\uDFFFUガ\x00\x00')
    assert False
except UnicodeError:
    pass
assert (
    normalize_passphrase('😀\\uZ😀é\\u0061\\x20\\uDFFF\x00a\\u00e9')
    == '😀\\uZ😀é\\u0061\\x20\\uDFFF\x00a\\u00e9'
)
assert normalize_passphrase('\\\\u0061\\x20aé') == '\\a\\x20aé'
try:
    normalize_passphrase('\\x20\\uD800\\uD800ガ\\u00e9')
    assert False
except UnicodeError:
    pass
assert normalize_passphrase('\\x20ﷺ😀\x00') == '\\x20صلى الله عليه وسلم😀\x00'
assert (
    normalize_passphrase('a\\u00e9\\uD800a\\u123\\😀\\u00e9\\x20')
    == 'a\\u00e9\\uD800a\\u123\\😀\\u00e9\\x20'
)
assert normalize_passphrase('😀\\x20\\u0061u\\u0061') == '😀\\x20aua'
try:
    normalize_passphrase('\\u0061😀u\\uD800\\uDFFFéé')
    assert False
except UnicodeError:
    pass
assert normalize_passphrase('ガ\\uDFFF\\uZaa\\uD800a') == 'ガ\\uDFFF\\uZaa\\uD800a'
assert normalize_passphrase('U\\Ua') == 'U\\Ua'
try:
    normalize_passphrase('U\x00a\\u00e9ﷺ\\uDFFF\\')
    assert False
except UnicodeError:
    pass
assert (
    normalize_passphrase('ガ\\uDFFF\\uZU\\u0061ﷺ\\u123éﷺ\\u123\\x20UaU')
    == 'ガ\\uDFFF\\uZU\\u0061صلى الله عليه وسلم\\u123éصلى الله عليه وسلم\\u123\\x20UaU'
)
try:
    normalize_passphrase('\\u00e9\\uDFFF')
    assert False
except UnicodeError:
    pass
assert (
    normalize_passphrase('\\uDFFF\\u00e9a\\u00e9\\uZU\\u123\\')
    == '\\uDFFF\\u00e9a\\u00e9\\uZU\\u123\\'
)
assert normalize_passphrase('😀éu') == '😀éu'
assert (
    normalize_passphrase('\\u123\\éa\\u00e9ﷺ\\x20\\uDFFF\\uD800aﷺ')
    == '\\u123\\éa\\u00e9صلى الله عليه وسلم\\x20\\uDFFF\\uD800aصلى الله عليه وسلم'
)
assert normalize_passphrase('\\\\u0061\x00ガ\\ガ') == '\\a\x00ガ\\ガ'
assert (
    normalize_passphrase('\\u0061\\u0061\\\\u0061😀ガガ\\uD800éU\\u123\\')
    == '\\u0061\\u0061\\\\u0061😀ガガ\\uD800éU\\u123\\'
)
assert (
    normalize_passphrase('ﷺaa\x00\\uD800ﷺ\\\\u123\\')
    == 'صلى الله عليه وسلمaa\x00\\uD800صلى الله عليه وسلم\\\\u123\\'
)
try:
    normalize_passphrase('\\uD800é\\uD800')
    assert False
except UnicodeError:
    pass
assert (
    normalize_passphrase('\\u123😀\\uDFFF\\\\u00e9ガ\\uD800\x00')
    == '\\u123😀\\uDFFF\\\\u00e9ガ\\uD800\x00'
)
assert normalize_passphrase('\\uZ') == '\\uZ'
try:
    normalize_passphrase('\\uDFFF\\uD800a')
    assert False
except UnicodeError:
    pass
try:
    normalize_passphrase('\\u0061\\x20aガ\\uD800')
    assert False
except UnicodeError:
    pass
try:
    normalize_passphrase('\\x20\\u0061é\\x20\\u00e9\\uD800\\u0061')
    assert False
except UnicodeError:
    pass
assert normalize_passphrase('\\uDFFF\\u00e9U\\uZ\\aU') == '\\uDFFF\\u00e9U\\uZ\\aU'
try:
    normalize_passphrase('ﷺ\\uD800aaé\\x20ガ\\u0061U😀ガ\\a')
    assert False
except UnicodeError:
    pass
assert (
    normalize_passphrase('\\\\u00e9\\u\\x20\\u00e9\\u123\\ガ')
    == '\\\\u00e9\\u\\x20\\u00e9\\u123\\ガ'
)
assert (
    normalize_passphrase('\\u0061U\\x20\\uZ\\x20\\u123\\\\uDFFF\\\\x20\\u123u')
    == '\\u0061U\\x20\\uZ\\x20\\u123\\\\uDFFF\\\\x20\\u123u'
)
assert (
    normalize_passphrase('\\uDFFF😀\\x20u\\x20\\u123\\u123\\u0061')
    == '\\uDFFF😀\\x20u\\x20\\u123\\u123\\u0061'
)
try:
    normalize_passphrase('ﷺ\\u00e9a\\\\uDFFF\x00\\uD800\x00')
    assert False
except UnicodeError:
    pass
assert (
    normalize_passphrase('\\é\\u123\\u123\\uZ\x00U\\uD800\\uZ😀\\x20\\uD800')
    == '\\é\\u123\\u123\\uZ\x00U\\uD800\\uZ😀\\x20\\uD800'
)
assert (
    normalize_passphrase('u😀\x00ﷺéu\\u123ガ\\x20Uﷺ')
    == 'u😀\x00صلى الله عليه وسلمéu\\u123ガ\\x20Uصلى الله عليه وسلم'
)
assert (
    normalize_passphrase('\\u0061é\\uD800\\\\uD800\\u123é\\u0061')
    == '\\u0061é\\uD800\\\\uD800\\u123é\\u0061'
)
try:
    normalize_passphrase('\\x20ﷺ\\u0061\\uDFFFaé😀\\u00e9\\x20ガﷺ😀ガ')
    assert False
except UnicodeError:
    pass
try:
    normalize_passphrase('uU\\uD800\\u0061\x00')
    assert False
except UnicodeError:
    pass
try:
    normalize_passphrase('ガﷺ\\uDFFF')
    assert False
except UnicodeError:
    pass
assert (
    normalize_passphrase('u\\u0061ガ\\u0061ééaa\\\\uD800\\uDFFF\\uZ\\u123')
    == 'u\\u0061ガ\\u0061ééaa\\\\uD800\\uDFFF\\uZ\\u123'
)
assert (
    normalize_passphrase('Uﷺ\\uZ\\u00e9\\x20\\u123\\uD800\\uDFFFガu')
    == 'Uصلى الله عليه وسلم\\uZ\\u00e9\\x20\\u123\\uD800\\uDFFFガu'
)
assert (
    normalize_passphrase('uガ\\x20uaﷺ\\x20\\u0061U\\uZ\\')
    == 'uガ\\x20uaصلى الله عليه وسلم\\x20\\u0061U\\uZ\\'
)
assert normalize_passphrase('ガガ') == 'ガガ'
assert normalize_passphrase('Ué\\x20\\u00e9\\\\uDFFF\\uZガ') == 'Ué\\x20\\u00e9\\\\uDFFF\\uZガ'
assert (
    normalize_passphrase('\\u123éé\\u00e9\\u00e9\x00\\\\u00e9')
    == '\\u123éé\\u00e9\\u00e9\x00\\\\u00e9'
)
assert normalize_passphrase('aﷺ\x00\\u0061') == 'aصلى الله عليه وسلم\x00a'
assert normalize_passphrase('éUé') == 'éUé'
assert normalize_passphrase('\\x20a\\uZ') == '\\x20a\\uZ'
assert normalize_passphrase('u\\x20éé\\u123ﷺé') == 'u\\x20éé\\u123صلى الله عليه وسلمé'
try:
    normalize_passphrase('😀a\\u00e9😀ガ\x00😀\\u0061ガ\\uD800')
    assert False
except UnicodeError:
    pass
assert (
    normalize_passphrase('\\u0061\\uDFFF\\u0061\\u00e9ガ\\u0061\\x20ガU\\uZ\x00')
    == '\\u0061\\uDFFF\\u0061\\u00e9ガ\\u0061\\x20ガU\\uZ\x00'
)
assert normalize_passphrase('\\uZ\\u00e9') == '\\uZ\\u00e9'
assert (
    normalize_passphrase('\\u00e9ﷺau\\uZ\\u123\\u123😀ガ')
    == '\\u00e9صلى الله عليه وسلمau\\uZ\\u123\\u123😀ガ'
)
assert (
    normalize_passphrase('ガaU\\uD800\\uDFFF\\uD800\\uZ\\uDFFFa\\uDFFF')
    == 'ガaU\\uD800\\uDFFF\\uD800\\uZ\\uDFFFa\\uDFFF'
)
assert (
    normalize_passphrase('\\u00e9\\uDFFF\\u123ﷺ\\u123')
    == '\\u00e9\\uDFFF\\u123صلى الله عليه وسلم\\u123'
)
assert normalize_passphrase('\\uDFFF\x00ガ\\u123U') == '\\uDFFF\x00ガ\\u123U'
try:
    normalize_passphrase('\\u00e9\\uD800\\\\ﷺ\\u0061')
    assert False
except UnicodeError:
    pass
assert normalize_passphrase('\\uDFFF\x00\\x20U\\u123\\') == '\\uDFFF\x00\\x20U\\u123\\'
assert (
    normalize_passphrase('éU\\u00e9ﷺ\\x20\\\\x20\\uZaガ\x00\\uZﷺ😀')
    == 'éU\\u00e9صلى الله عليه وسلم\\x20\\\\x20\\uZaガ\x00\\uZصلى الله عليه وسلم😀'
)
assert normalize_passphrase('u😀\x00\\u00e9\\\\uZ\\uZ') == 'u😀\x00\\u00e9\\\\uZ\\uZ'
try:
    normalize_passphrase('U\\uDFFFu')
    assert False
except UnicodeError:
    pass
assert (
    normalize_passphrase('\\x20aU\\x20\\x20u\\u123\\uDFFF\\\\x20u')
    == '\\x20aU\\x20\\x20u\\u123\\uDFFF\\\\x20u'
)
assert (
    normalize_passphrase('u\\\\x20éé\\u0061\x00\\u123\\uD800')
    == 'u\\\\x20éé\\u0061\x00\\u123\\uD800'
)
assert normalize_passphrase('u\x00\\') == 'u\x00\\'
try:
    normalize_passphrase('ﷺ😀éé\\u00e9\\x20\\uDFFF')
    assert False
except UnicodeError:
    pass
assert (
    normalize_passphrase('\\u00e9\\ガ\\uD800\\u123\x00\\uD800a\\u0061Uu\\x20')
    == '\\u00e9\\ガ\\uD800\\u123\x00\\uD800a\\u0061Uu\\x20'
)
try:
    normalize_passphrase('ﷺ\\uDFFFﷺu')
    assert False
except UnicodeError:
    pass
try:
    normalize_passphrase('\\uDFFF\\u00e9')
    assert False
except UnicodeError:
    pass
try:
    normalize_passphrase('\\uDFFF\\x20ﷺ\\uDFFFガ')
    assert False
except UnicodeError:
    pass
try:
    normalize_passphrase('é\\u0061é😀U\\uD800')
    assert False
except UnicodeError:
    pass
assert (
    normalize_passphrase('\\uZuガ\\uZU\\u0061ﷺuu\\u0061')
    == '\\uZuガ\\uZU\\u0061صلى الله عليه وسلمuu\\u0061'
)
assert (
    normalize_passphrase('é\\u0061ﷺ\\u0061ガ\\u00e9\\uZ\\u123\\u0061ﷺ\x00\x00\\uDFFFガ')
    == 'é\\u0061صلى الله عليه وسلم\\u0061ガ\\u00e9\\uZ\\u123\\u0061صلى الله عليه وسلم\x00\x00\\uDFFFガ'
)
assert (
    normalize_passphrase('\\x20\\uD800\\uDFFF\\u123\\x20\\u123\\\\\\uZ\\uDFFFa')
    == '\\x20\\uD800\\uDFFF\\u123\\x20\\u123\\\\\\uZ\\uDFFFa'
)
try:
    normalize_passphrase('\\uD800ﷺa\\uDFFF\\u00e9\\x20\x00\\u0061')
    assert False
except UnicodeError:
    pass
assert normalize_passphrase('\\u0061\\u0061aé') == 'aaaé'
assert normalize_passphrase('😀ガ\\u00e9é😀é\x00a\\u00e9u') == '😀ガéé😀é\x00aéu'
assert normalize_passphrase('\\u0061\\x20a\\u123') == '\\u0061\\x20a\\u123'
assert (
    normalize_passphrase('\\uZ\\uDFFFa\\u0061\\u123ガ\\uD800\x00\\uZ\\uZ')
    == '\\uZ\\uDFFFa\\u0061\\u123ガ\\uD800\x00\\uZ\\uZ'
)
assert (
    normalize_passphrase('ﷺU\\éU😀\\u00e9aガ\\x20\\x20')
    == 'صلى الله عليه وسلمU\\éU😀éaガ\\x20\\x20'
)
assert (
    normalize_passphrase('uU\\u00e9\\uDFFFé\\u123\\uZﷺガ\\uDFFF\\uZ\\uZ\\')
    == 'uU\\u00e9\\uDFFFé\\u123\\uZصلى الله عليه وسلمガ\\uDFFF\\uZ\\uZ\\'
)
assert normalize_passphrase('\\u00e9U\\u123') == '\\u00e9U\\u123'
assert normalize_passphrase('U\x00') == 'U\x00'
assert (
    normalize_passphrase('\\uDFFF\\uZﷺ😀U\\uZ\x00ﷺ\\uDFFF\\u0061\\uZ\\uZ')
    == '\\uDFFF\\uZصلى الله عليه وسلم😀U\\uZ\x00صلى الله عليه وسلم\\uDFFF\\u0061\\uZ\\uZ'
)
assert normalize_passphrase('\x00a😀é\\x20\\x20😀\\') == '\x00a😀é\\x20\\x20😀\\'
assert (
    normalize_passphrase('\\uZUUU\\uZ\\u00e9\\x20ガ😀\\\x00😀')
    == '\\uZUUU\\uZ\\u00e9\\x20ガ😀\\\x00😀'
)
assert normalize_passphrase('é') == 'é'
try:
    normalize_passphrase('\\uDFFFUa\\u00e9')
    assert False
except UnicodeError:
    pass
assert (
    normalize_passphrase('\\u123\\u00e9\\u0061ガガ😀\\x20ガ\\uD800ﷺ\\\\')
    == '\\u123\\u00e9\\u0061ガガ😀\\x20ガ\\uD800صلى الله عليه وسلم\\\\'
)
assert (
    normalize_passphrase('\\uZ\\uDFFF\x00\\u0061\\u0061\\x20\\')
    == '\\uZ\\uDFFF\x00\\u0061\\u0061\\x20\\'
)
assert (
    normalize_passphrase('éuau\\u123\\x20Ué\\uDFFFa\\u123\\\\x20')
    == 'éuau\\u123\\x20Ué\\uDFFFa\\u123\\\\x20'
)
assert (
    normalize_passphrase('u\x00ガ😀\\x20\\u123\\uD800\\\\u0061Ué\\u0061\\u00e9')
    == 'u\x00ガ😀\\x20\\u123\\uD800\\\\u0061Ué\\u0061\\u00e9'
)
assert (
    normalize_passphrase('\\u123\\uZ😀\\uDFFF\\u00e9\\ﷺ\\uD800\\u0061\\\\u123\\')
    == '\\u123\\uZ😀\\uDFFF\\u00e9\\صلى الله عليه وسلم\\uD800\\u0061\\\\u123\\'
)
assert (
    normalize_passphrase('\\uZ\\u0061ﷺ\\uDFFFuﷺU')
    == '\\uZ\\u0061صلى الله عليه وسلم\\uDFFFuصلى الله عليه وسلمU'
)
assert (
    normalize_passphrase('ガ\\u0061\\u0061ガ😀\\uDFFF\\uZéUu')
    == 'ガ\\u0061\\u0061ガ😀\\uDFFF\\uZéUu'
)
assert normalize_passphrase('\\u0061\\u0061\\u00e9') == 'aaé'
try:
    normalize_passphrase('aaéﷺa\\\\uDFFFﷺ\\u00e9ﷺ\\uDFFFガu😀')
    assert False
except UnicodeError:
    pass
assert normalize_passphrase('\\uZ\\') == '\\uZ\\'
assert normalize_passphrase('\\uZ\\u123\\x20😀\\u123U') == '\\uZ\\u123\\x20😀\\u123U'
assert (
    normalize_passphrase('\\uDFFF\\u00e9U\\uD800\\uDFFF\\u123')
    == '\\uDFFF\\u00e9U\\uD800\\uDFFF\\u123'
)
assert (
    normalize_passphrase('\\u123ガ\x00U\\u00e9\\u00e9ガUé\\uZ\\x20')
    == '\\u123ガ\x00U\\u00e9\\u00e9ガUé\\uZ\\x20'
)
assert normalize_passphrase('ガ\\ガU\\u123\\x20\\') == 'ガ\\ガU\\u123\\x20\\'
try:
    normalize_passphrase('a\x00\\x20\\u00e9\\x20ガﷺ\\uDFFF\\uD800\\u00e9\\uD800\x00\\u0061')
    assert False
except UnicodeError:
    pass
try:
    normalize_passphrase('\\uD800u\\😀😀é😀u\\x20')
    assert False
except UnicodeError:
    pass
assert (
    normalize_passphrase('\\\\uZ😀😀ﷺ\\uD800\\x20\\uD800\\\\😀')
    == '\\\\uZ😀😀صلى الله عليه وسلم\\uD800\\x20\\uD800\\\\😀'
)
assert normalize_passphrase('\\uD800😀\\uZ\\u0061\\x20U') == '\\uD800😀\\uZ\\u0061\\x20U'
assert normalize_passphrase('\\uZU\\\\uZ') == '\\uZU\\\\uZ'
assert normalize_passphrase('Uﷺ\\u123U\\uDFFFガ') == 'Uصلى الله عليه وسلم\\u123U\\uDFFFガ'
try:
    normalize_passphrase('U\\uD800\\u123a')
    assert False
except UnicodeError:
    pass
assert normalize_passphrase('\x00\\u0061\x00a😀\\uZaau\\') == '\x00\\u0061\x00a😀\\uZaau\\'
assert normalize_passphrase('\\u00e9\\uD800\\u123') == '\\u00e9\\uD800\\u123'
assert normalize_passphrase('U') == 'U'
try:
    normalize_passphrase('a\\uD800\\u00e9uéガ😀ガ\x00\\uD800\x00')
    assert False
except UnicodeError:
    pass
assert (
    normalize_passphrase('\\uZ\\\\u0061\\uZ\\uDFFFuu\\u00e9ééU')
    == '\\uZ\\\\u0061\\uZ\\uDFFFuu\\u00e9ééU'
)
assert (
    normalize_passphrase('ﷺガ\x00U\\x20\\u0061é\\x20\\x20\\uZﷺ')
    == 'صلى الله عليه وسلمガ\x00U\\x20\\u0061é\\x20\\x20\\uZصلى الله عليه وسلم'
)
assert (
    normalize_passphrase('\\u0061\\uZ\\uDFFFu\\uZ\\u123\\u00e9')
    == '\\u0061\\uZ\\uDFFFu\\uZ\\u123\\u00e9'
)
assert normalize_passphrase('\\uDFFF\\uZ\\x20\\uD800') == '\\uDFFF\\uZ\\x20\\uD800'
assert normalize_passphrase('\x00é') == '\x00é'
assert (
    normalize_passphrase('ガ\\x20a\x00ﷺéU\\x20ﷺ\\')
    == 'ガ\\x20a\x00صلى الله عليه وسلمéU\\x20صلى الله عليه وسلم\\'
)
try:
    normalize_passphrase('u\\uD800\\x20')
    assert False
except UnicodeError:
    pass
try:
    normalize_passphrase('\\\\uD800ﷺ')
    assert False
except UnicodeError:
    pass
try:
    normalize_passphrase('é\\uDFFF\\uDFFF\\u00e9😀\\\\uDFFF\\u00e9😀\\u0061')
    assert False
except UnicodeError:
    pass
assert (
    normalize_passphrase('\\uD800ガ\\x20ﷺ\\uZ\\uD800é\x00😀ﷺ\x00😀\\u0061a')
    == '\\uD800ガ\\x20صلى الله عليه وسلم\\uZ\\uD800é\x00😀صلى الله عليه وسلم\x00😀\\u0061a'
)
assert normalize_passphrase('\x00U\\x20\\u00e9\\uZ😀\\uDFFF') == '\x00U\\x20\\u00e9\\uZ😀\\uDFFF'
assert normalize_passphrase('éé') == 'éé'
assert (
    normalize_passphrase('\\u00e9ガé\\u123a😀a\\uD800\\uDFFF\\uZ\\uD800\\ﷺ')
    == '\\u00e9ガé\\u123a😀a\\uD800\\uDFFF\\uZ\\uD800\\صلى الله عليه وسلم'
)
assert normalize_passphrase('\\u0061') == 'a'
try:
    normalize_passphrase('\\uDFFFU\x00\\x20ガ\\u0061u')
    assert False
except UnicodeError:
    pass
assert normalize_passphrase('é\\u00e9u\\u0061') == 'ééua'
assert (
    normalize_passphrase('\x00\\uZガ\\uDFFF\\uD800aガ\\u0061\\x20\\\\uD800ガ')
    == '\x00\\uZガ\\uDFFF\\uD800aガ\\u0061\\x20\\\\uD800ガ'
)
assert normalize_passphrase('\\u00e9\\uZ\x00\\u00e9ﷺ') == '\\u00e9\\uZ\x00\\u00e9صلى الله عليه وسلم'
assert normalize_passphrase('ﷺ\\uD800\\uZ\\uD800') == 'صلى الله عليه وسلم\\uD800\\uZ\\uD800'
assert (
    normalize_passphrase('Uué\\u00e9uU\\u00e9😀\\u123\\ﷺéé')
    == 'Uué\\u00e9uU\\u00e9😀\\u123\\صلى الله عليه وسلمéé'
)
assert normalize_passphrase('é\\u0061') == 'éa'
try:
    normalize_passphrase('\\uDFFF\\u00e9')
    assert False
except UnicodeError:
    pass
assert (
    normalize_passphrase('\x00\\x20é\\uD800\x00\\uD800\\u123\\uZ\\ガUuaﷺ')
    == '\x00\\x20é\\uD800\x00\\uD800\\u123\\uZ\\ガUuaصلى الله عليه وسلم'
)
assert (
    normalize_passphrase('ﷺéa\\😀\\uD800\\uZ\x00\\u0061😀')
    == 'صلى الله عليه وسلمéa\\😀\\uD800\\uZ\x00\\u0061😀'
)
try:
    normalize_passphrase('😀\\x20é\\uDFFFガ')
    assert False
except UnicodeError:
    pass
assert (
    normalize_passphrase('\\uDFFFﷺ\\u0061\\\\uZﷺ\\uD800\\uDFFFUガU\\u123ガ')
    == '\\uDFFFصلى الله عليه وسلم\\u0061\\\\uZصلى الله عليه وسلم\\uD800\\uDFFFUガU\\u123ガ'
)
assert (
    normalize_passphrase('ガ\\x20ﷺ\x00\\x20U😀ガU\x00')
    == 'ガ\\x20صلى الله عليه وسلم\x00\\x20U😀ガU\x00'
)
try:
    normalize_passphrase('\\x20\\uD800\\u0061😀😀\\u123aガ')
    assert False
except UnicodeError:
    pass
try:
    normalize_passphrase('U😀é\\uD800😀\\u00e9é\x00\\uD800\\\\x20\\x20é😀')
    assert False
except UnicodeError:
    pass
try:
    normalize_passphrase('😀\\uD800ガu\\u00e9\\uDFFFﷺ')
    assert False
except UnicodeError:
    pass
assert (
    normalize_passphrase('ﷺ\\x20ﷺ\x00😀ガ') == 'صلى الله عليه وسلم\\x20صلى الله عليه وسلم\x00😀ガ'
)
try:
    normalize_passphrase('\x00U\x00\\uD800\x00')
    assert False
except UnicodeError:
    pass
assert (
    normalize_passphrase('\\uDFFF\\u123\\uD800\\uD800u\\u123\\uﷺ\\uu\\u123')
    == '\\uDFFF\\u123\\uD800\\uD800u\\u123\\uصلى الله عليه وسلم\\uu\\u123'
)
assert normalize_passphrase('ガUuﷺﷺ') == 'ガUuصلى الله عليه وسلمصلى الله عليه وسلم'
assert normalize_passphrase('ガ\\\\u0061ﷺ\\x20\\') == 'ガ\\aصلى الله عليه وسلم\\x20\\'
assert (
    normalize_passphrase('😀\\\\uZ\\x20éﷺ\\\\u0061') == '😀\\\\uZ\\x20éصلى الله عليه وسلم\\\\u0061'
)
assert normalize_passphrase('uガa\\u0061\\uZ\\u0061\\u123é') == 'uガa\\u0061\\uZ\\u0061\\u123é'
assert (
    normalize_passphrase('\\uZ\\uDFFF😀ua\\x20\\uZ\\uZ\\u00e9ééé\x00\\uD800')
    == '\\uZ\\uDFFF😀ua\\x20\\uZ\\uZ\\u00e9ééé\x00\\uD800'
)
assert (
    normalize_passphrase('\\x20u\\uZ\\uD800\\u00e9\\x20\\u0061\\uZ\\x20\\uD800ガ')
    == '\\x20u\\uZ\\uD800\\u00e9\\x20\\u0061\\uZ\\x20\\uD800ガ'
)
assert normalize_passphrase('\\ﷺ\\uDFFFUé\\x20\\u123') == '\\صلى الله عليه وسلم\\uDFFFUé\\x20\\u123'
assert (
    normalize_passphrase('ﷺ\\aa\\x20\\uZ😀\\u00e9a\\x20ガ\x00\\u0061')
    == 'صلى الله عليه وسلم\\aa\\x20\\uZ😀\\u00e9a\\x20ガ\x00\\u0061'
)
assert normalize_passphrase('\\uZ\\uD800éaU\\u0061\\uZ') == '\\uZ\\uD800éaU\\u0061\\uZ'
try:
    normalize_passphrase('\\u00e9\\uD800UUa')
    assert False
except UnicodeError:
    pass
try:
    normalize_passphrase('\\uDFFFuﷺUé')
    assert False
except UnicodeError:
    pass
assert normalize_passphrase('😀😀\\u0061\\u00e9') == '😀😀aé'
assert (
    normalize_passphrase('😀\\uD800\\u123\\uDFFFau\\uD800\\uZﷺUa')
    == '😀\\uD800\\u123\\uDFFFau\\uD800\\uZصلى الله عليه وسلمUa'
)
assert normalize_passphrase('a') == 'a'
try:
    normalize_passphrase('\\u0061\\uDFFFuガ\\uDFFF\\x20uガ\\')
    assert False
except UnicodeError:
    pass
assert (
    normalize_passphrase('\\uD800\\u0061\\u0061\\u123é\\uZ\\uDFFFUUUガé😀')
    == '\\uD800\\u0061\\u0061\\u123é\\uZ\\uDFFFUUUガé😀'
)
assert normalize_passphrase('Uガ\\u00e9') == 'Uガé'
assert normalize_passphrase('\x00😀a\\uZ\\u00e9\\uZ') == '\x00😀a\\uZ\\u00e9\\uZ'
assert normalize_passphrase('éé\\uDFFFu\x00\\uZ') == 'éé\\uDFFFu\x00\\uZ'
assert normalize_passphrase('aé\x00\\é') == 'aé\x00\\é'
assert normalize_passphrase('\\uZ\\uD800aガ\\\\uDFFF😀') == '\\uZ\\uD800aガ\\\\uDFFF😀'
assert normalize_passphrase('\\uZ\\u123\\') == '\\uZ\\u123\\'
assert normalize_passphrase('\\x20é\\u00e9😀\\uZガ') == '\\x20é\\u00e9😀\\uZガ'
assert (
    normalize_passphrase('\\u00e9\\uZ\\u00e9ガU\\u123😀\\uD800\\uD800ガガ')
    == '\\u00e9\\uZ\\u00e9ガU\\u123😀\\uD800\\uD800ガガ'
)
try:
    normalize_passphrase('ua\x00\\uDFFFﷺ\\uDFFFガaaa\\uDFFF\\')
    assert False
except UnicodeError:
    pass
assert (
    normalize_passphrase('\\uZガガガa\\x20\\uZ\\uDFFFﷺ')
    == '\\uZガガガa\\x20\\uZ\\uDFFFصلى الله عليه وسلم'
)
try:
    normalize_passphrase('\\x20ﷺ\\uDFFF\\x20ガ\\uD800U')
    assert False
except UnicodeError:
    pass
assert (
    normalize_passphrase('ガﷺU\\x20\\uZa\\uZ\\uD800é😀éガﷺ')
    == 'ガصلى الله عليه وسلمU\\x20\\uZa\\uZ\\uD800é😀éガصلى الله عليه وسلم'
)
assert normalize_passphrase('😀\\') == '😀\\'
try:
    normalize_passphrase('\\u00e9\\uDFFF\\u0061ガaé\\x20\\x20ﷺ')
    assert False
except UnicodeError:
    pass
assert normalize_passphrase('😀\\u00e9\x00\\u123') == '😀\\u00e9\x00\\u123'
assert normalize_passphrase('é\\uZ\x00') == 'é\\uZ\x00'
try:
    normalize_passphrase('\\uD800u\x00')
    assert False
except UnicodeError:
    pass
assert (
    normalize_passphrase('u\\uDFFF\\\\uD800\\u0061ﷺﷺ\\u123')
    == 'u\\uDFFF\\\\uD800\\u0061صلى الله عليه وسلمصلى الله عليه وسلم\\u123'
)
assert normalize_passphrase('\\u00e9ﷺu\\') == 'éصلى الله عليه وسلمu\\'
assert normalize_passphrase('U') == 'U'
assert (
    normalize_passphrase('éﷺ\\u0061ﷺ\\uD800uﷺ\x00\\\\uZ\\uD800\\')
    == 'éصلى الله عليه وسلم\\u0061صلى الله عليه وسلم\\uD800uصلى الله عليه وسلم\x00\\\\uZ\\uD800\\'
)
assert normalize_passphrase('\x00ﷺé\\u00e9\\x20') == '\x00صلى الله عليه وسلمéé\\x20'
assert (
    normalize_passphrase('\\u123\\uZ\\uD800\\u00e9\\uZ\\uZ\\é\\uZ\\u00e9😀\\\\uD800a')
    == '\\u123\\uZ\\uD800\\u00e9\\uZ\\uZ\\é\\uZ\\u00e9😀\\\\uD800a'
)
assert normalize_passphrase('U\x00\\uD800\\uZ') == 'U\x00\\uD800\\uZ'
assert normalize_passphrase('ﷺ\\uZué\\uZ\\') == 'صلى الله عليه وسلم\\uZué\\uZ\\'
assert (
    normalize_passphrase('u\\u123\\uZ\\u123U\\uZ😀U\\x20\\u00e9UUaa')
    == 'u\\u123\\uZ\\u123U\\uZ😀U\\x20\\u00e9UUaa'
)
assert normalize_passphrase('\\u123\\uZ\\x20\\') == '\\u123\\uZ\\x20\\'
assert (
    normalize_passphrase('😀\\uZu\\u123\\x20\\uD800\\u00e9\\u00e9\\\\uD800aﷺ')
    == '😀\\uZu\\u123\\x20\\uD800\\u00e9\\u00e9\\\\uD800aصلى الله عليه وسلم'
)
assert (
    normalize_passphrase('\\uZU\\u00e9UU\\\\\\uZ\\uZ\\uD800ﷺ')
    == '\\uZU\\u00e9UU\\\\\\uZ\\uZ\\uD800صلى الله عليه وسلم'
)
assert (
    normalize_passphrase('\x00\\uZ\\uZ\\uDFFFuéu\\x20\\x20\\uD800\x00😀')
    == '\x00\\uZ\\uZ\\uDFFFuéu\\x20\\x20\\uD800\x00😀'
)
assert normalize_passphrase('\x00\\u0061😀ﷺ😀\\é') == '\x00a😀صلى الله عليه وسلم😀\\é'
assert normalize_passphrase('ガﷺ\\uZU\\uZ\\uZ') == 'ガصلى الله عليه وسلم\\uZU\\uZ\\uZ'
try:
    normalize_passphrase('\\x20\\x20\x00😀\\uD800\\x20aﷺﷺU\\uDFFF\\u0061')
    assert False
except UnicodeError:
    pass
assert (
    normalize_passphrase('\\uZU\\u00e9\\uDFFF\\uZa\\u0061\\u0061\\uZ\\ガﷺ')
    == '\\uZU\\u00e9\\uDFFF\\uZa\\u0061\\u0061\\uZ\\ガصلى الله عليه وسلم'
)
assert normalize_passphrase('\\u00e9\\uZ') == '\\u00e9\\uZ'
assert normalize_passphrase('éガ\\u00e9') == 'éガé'
assert normalize_passphrase('U') == 'U'
assert (
    normalize_passphrase('\x00u\\uZu\\uD800\\uZ\\\\u123\\uD800\\uZ😀ガ\\uZ')
    == '\x00u\\uZu\\uD800\\uZ\\\\u123\\uD800\\uZ😀ガ\\uZ'
)
assert (
    normalize_passphrase('\\u00e9ﷺﷺ😀\\u123ガ\\u0061é\\x20U\\u123\\uZ')
    == '\\u00e9صلى الله عليه وسلمصلى الله عليه وسلم😀\\u123ガ\\u0061é\\x20U\\u123\\uZ'
)
assert normalize_passphrase('\\uDFFF😀ガ😀\\uZa') == '\\uDFFF😀ガ😀\\uZa'
try:
    normalize_passphrase('\\\\uDFFF\x00ガ😀u\\u0061😀😀ガ😀u\\uD800')
    assert False
except UnicodeError:
    pass
try:
    normalize_passphrase('\\x20\\\\uD800')
    assert False
except UnicodeError:
    pass
assert normalize_passphrase('\\uZガ\\x20😀😀Uガ') == '\\uZガ\\x20😀😀Uガ'
assert normalize_passphrase('ﷺ') == 'صلى الله عليه وسلم'
assert (
    normalize_passphrase('\\uZガU\\x20ガﷺ\\u0061\\uZ\\u00e9\\uD800\\uZ\\uDFFF')
    == '\\uZガU\\x20ガصلى الله عليه وسلم\\u0061\\uZ\\u00e9\\uD800\\uZ\\uDFFF'
)
assert normalize_passphrase('a') == 'a'
assert normalize_passphrase('u😀éu') == 'u😀éu'
assert normalize_passphrase('éUガ\\u00e9😀éa') == 'éUガé😀éa'
assert (
    normalize_passphrase('U\\😀\\x20a\\u123\\x20\x00éu\\u0061uガ\\uDFFF')
    == 'U\\😀\\x20a\\u123\\x20\x00éu\\u0061uガ\\uDFFF'
)
assert (
    normalize_passphrase('Uauﷺ\\u123éaa\\Uガ\\uDFFFﷺ\\u0061')
    == 'Uauصلى الله عليه وسلم\\u123éaa\\Uガ\\uDFFFصلى الله عليه وسلم\\u0061'
)
try:
    normalize_passphrase('ﷺ\\u0061\x00éU\\uDFFF\x00😀\\x20\\x20')
    assert False
except UnicodeError:
    pass
assert (
    normalize_passphrase('\\u0061\\uDFFF\\u123a\\x20\\uDFFF\\x20aé😀\\u123\\😀😀')
    == '\\u0061\\uDFFF\\u123a\\x20\\uDFFF\\x20aé😀\\u123\\😀😀'
)
assert (
    normalize_passphrase('\x00\x00\\uDFFF\\uZ\x00u\\u00e9\\u123u\x00\x00ééU')
    == '\x00\x00\\uDFFF\\uZ\x00u\\u00e9\\u123u\x00\x00ééU'
)
assert normalize_passphrase('ガua\\uZ\\') == 'ガua\\uZ\\'
assert (
    normalize_passphrase('\\uZ\\😀ガガ\\u00e9\\uZ\\u0061a\\u0061\\u')
    == '\\uZ\\😀ガガ\\u00e9\\uZ\\u0061a\\u0061\\u'
)
assert (
    normalize_passphrase('UU\\u123\\u123\\x20\\u123\\u0061') == 'UU\\u123\\u123\\x20\\u123\\u0061'
)
assert (
    normalize_passphrase('\\u123ﷺ\\uZ\\uD800UU\\uD800')
    == '\\u123صلى الله عليه وسلم\\uZ\\uD800UU\\uD800'
)
assert normalize_passphrase('ガ\\éﷺ\x00') == 'ガ\\éصلى الله عليه وسلم\x00'
try:
    normalize_passphrase('\\uDFFF😀😀\\u0061')
    assert False
except UnicodeError:
    pass
assert (
    normalize_passphrase('\\uD800aa\\u00e9ﷺ\\uZ\\😀\\u123\\u123')
    == '\\uD800aa\\u00e9صلى الله عليه وسلم\\uZ\\😀\\u123\\u123'
)
assert (
    normalize_passphrase('😀\\u123a\\u123ﷺua\\u00e9\\x20U\\uDFFF😀U\\u00e9')
    == '😀\\u123a\\u123صلى الله عليه وسلمua\\u00e9\\x20U\\uDFFF😀U\\u00e9'
)
try:
    normalize_passphrase('\\x20\\x20\\uD800😀u\\u0061\\u0061😀\\u00e9')
    assert False
except UnicodeError:
    pass
assert normalize_passphrase('\\x20ﷺ😀') == '\\x20صلى الله عليه وسلم😀'
assert (
    normalize_passphrase('\\x20\\U\\uZu\\u00e9Ué\\uD800\x00ガ')
    == '\\x20\\U\\uZu\\u00e9Ué\\uD800\x00ガ'
)
assert normalize_passphrase('😀ﷺ\\uZ') == '😀صلى الله عليه وسلم\\uZ'
assert normalize_passphrase('\\uZU\\uDFFF😀\\u0061') == '\\uZU\\uDFFF😀\\u0061'
assert normalize_passphrase('\\ﷺ') == '\\صلى الله عليه وسلم'
assert normalize_passphrase('a\\\\x20') == 'a\\\\x20'
assert normalize_passphrase('\\u\\u00e9\\uDFFFé') == '\\u\\u00e9\\uDFFFé'
assert (
    normalize_passphrase('\\x20ガé\\ガ\\uZ\\uDFFFé\x00ガﷺ\\u00e9')
    == '\\x20ガé\\ガ\\uZ\\uDFFFé\x00ガصلى الله عليه وسلم\\u00e9'
)
assert (
    normalize_passphrase('\\u123\\ﷺU\\uD800\\uDFFFa\\u0061U\x00\\\\x20\\x20')
    == '\\u123\\صلى الله عليه وسلمU\\uD800\\uDFFFa\\u0061U\x00\\\\x20\\x20'
)
assert (
    normalize_passphrase('\\u0061ﷺ\\u00e9😀\\\\uD800\x00\\u0061\\u123\\uZ\\uD800aé')
    == '\\u0061صلى الله عليه وسلم\\u00e9😀\\\\uD800\x00\\u0061\\u123\\uZ\\uD800aé'
)
assert normalize_passphrase('\\u00e9\x00\\u0061a\x00') == 'é\x00aa\x00'
assert (
    normalize_passphrase('\x00😀😀a\\uDFFFU\\uZガ\\uZ\\u123\\uD800a\x00')
    == '\x00😀😀a\\uDFFFU\\uZガ\\uZ\\u123\\uD800a\x00'
)
try:
    normalize_passphrase('\\uDFFFuガガ\x00\\uDFFFaガ😀u\\uDFFF\\uD800\\uD800ﷺ')
    assert False
except UnicodeError:
    pass
assert normalize_passphrase('U\\u0061') == 'Ua'
assert normalize_passphrase('\x00\\') == '\x00\\'
try:
    normalize_passphrase('ﷺ\\uD800\\u0061')
    assert False
except UnicodeError:
    pass
assert normalize_passphrase('a') == 'a'
try:
    normalize_passphrase('\\ﷺ😀ﷺU\\\\uD800')
    assert False
except UnicodeError:
    pass
assert normalize_passphrase('😀') == '😀'
assert (
    normalize_passphrase('aé\\u123uuaガ😀ガ\\uZガ😀\\uD800\\u0061')
    == 'aé\\u123uuaガ😀ガ\\uZガ😀\\uD800\\u0061'
)
assert normalize_passphrase('\\u00e9\x00') == 'é\x00'
assert (
    normalize_passphrase('\x00Uﷺ\\uZ\\uDFFF😀ガ\\u123a\\u0061')
    == '\x00Uصلى الله عليه وسلم\\uZ\\uDFFF😀ガ\\u123a\\u0061'
)
assert normalize_passphrase('\\u00e9\\u123ガé😀\x00\\u00e9') == '\\u00e9\\u123ガé😀\x00\\u00e9'
assert normalize_passphrase('\\uZUaﷺU\\u0061') == '\\uZUaصلى الله عليه وسلمU\\u0061'
assert normalize_passphrase('\\u0061😀a\x00') == 'a😀a\x00'
assert (
    normalize_passphrase('\\u00e9ﷺ\\u0061éガガ\\uDFFF\\u123Uガ😀\\u123\\uD800')
    == '\\u00e9صلى الله عليه وسلم\\u0061éガガ\\uDFFF\\u123Uガ😀\\u123\\uD800'
)
try:
    normalize_passphrase('u\\uD800\\')
    assert False
except UnicodeError:
    pass
try:
    normalize_passphrase('\\x20uﷺ\\uD800\x00\\uD800\\u0061')
    assert False
except UnicodeError:
    pass
assert (
    normalize_passphrase('😀\\u123U\\uZuuﷺ\\u00e9\\u123')
    == '😀\\u123U\\uZuuصلى الله عليه وسلم\\u00e9\\u123'
)
assert (
    normalize_passphrase('ﷺUﷺ😀\x00au\x00u\\u00e9a')
    == 'صلى الله عليه وسلمUصلى الله عليه وسلم😀\x00au\x00uéa'
)
assert (
    normalize_passphrase('\\u0061\\uD800a\\u123ﷺ\\x20')
    == '\\u0061\\uD800a\\u123صلى الله عليه وسلم\\x20'
)
assert (
    normalize_passphrase('\\u123ﷺau\\u00e9a\\u123\\u123😀ﷺ\\u00e9ﷺ😀')
    == '\\u123صلى الله عليه وسلمau\\u00e9a\\u123\\u123😀صلى الله عليه وسلم\\u00e9صلى الله عليه وسلم😀'
)
assert (
    normalize_passphrase('a\\u00e9\x00é\\x20\x00a\\u0061😀\\u0061\\u123\\u00e9')
    == 'a\\u00e9\x00é\\x20\x00a\\u0061😀\\u0061\\u123\\u00e9'
)
try:
    normalize_passphrase('\\😀\\x20\\u00e9\\uD800a')
    assert False
except UnicodeError:
    pass
assert (
    normalize_passphrase('\\u123ガ\x00😀ﷺ\\u123\\uDFFF😀ﷺu')
    == '\\u123ガ\x00😀صلى الله عليه وسلم\\u123\\uDFFF😀صلى الله عليه وسلمu'
)
try:
    normalize_passphrase('😀\\u00e9\\uD800\\uD800')
    assert False
except UnicodeError:
    pass
try:
    normalize_passphrase('\\uD800😀\\x20\\u0061\\u0061')
    assert False
except UnicodeError:
    pass
assert normalize_passphrase('\\ﷺ') == '\\صلى الله عليه وسلم'
try:
    normalize_passphrase('U\\u00e9ﷺ\\uDFFF\x00\\u0061\\u0061ﷺ😀ガ')
    assert False
except UnicodeError:
    pass
try:
    normalize_passphrase('\\u00e9\x00\\uD800U\\u0061')
    assert False
except UnicodeError:
    pass
assert (
    normalize_passphrase('ﷺ😀\\u\\u00e9\\uZ\\uD800\\uD800')
    == 'صلى الله عليه وسلم😀\\u\\u00e9\\uZ\\uD800\\uD800'
)
assert normalize_passphrase('\\u') == '\\u'
assert normalize_passphrase('\\😀\x00\\uZUa\\uZ\x00\\uD800UU') == '\\😀\x00\\uZUa\\uZ\x00\\uD800UU'
assert normalize_passphrase('a😀\\U\\uD800\\uZu') == 'a😀\\U\\uD800\\uZu'
assert (
    normalize_passphrase('U\x00\\u123\\u123Uué\\uDFFF\\x20') == 'U\x00\\u123\\u123Uué\\uDFFF\\x20'
)
try:
    normalize_passphrase('\\uD800\\u00e9\\x20\\u00e9')
    assert False
except UnicodeError:
    pass
assert (
    normalize_passphrase('ガ\\uDFFFﷺガ\\uD800\x00é\\uZﷺ')
    == 'ガ\\uDFFFصلى الله عليه وسلمガ\\uD800\x00é\\uZصلى الله عليه وسلم'
)
assert normalize_passphrase('aa\\x20\\u00e9\\uZ\\uDFFFu') == 'aa\\x20\\u00e9\\uZ\\uDFFFu'
assert normalize_passphrase('u') == 'u'
assert (
    normalize_passphrase('\\u0061U\\uD800\\\\uD800\x00é\\u00e9\\uD800\\\x00\\uZ')
    == '\\u0061U\\uD800\\\\uD800\x00é\\u00e9\\uD800\\\x00\\uZ'
)
try:
    normalize_passphrase('\\u0061u\\x20\\uD800\\u0061😀u')
    assert False
except UnicodeError:
    pass
try:
    normalize_passphrase('\\uD800\x00')
    assert False
except UnicodeError:
    pass
try:
    normalize_passphrase('\\uDFFF\\uD800ﷺ\\x20\\u00e9\x00')
    assert False
except UnicodeError:
    pass
assert (
    normalize_passphrase('😀a\\uZ\\\\u00e9\\u00e9U😀ﷺ')
    == '😀a\\uZ\\\\u00e9\\u00e9U😀صلى الله عليه وسلم'
)
try:
    normalize_passphrase('\x00\\uDFFFé\\u00e9\\u123a\\uD800\\\x00\\uD800😀\\')
    assert False
except UnicodeError:
    pass
try:
    normalize_passphrase('\\uD800ﷺガ\x00uu\\x20ガ')
    assert False
except UnicodeError:
    pass
assert (
    normalize_passphrase('\\u0061\\uD800\\uDFFF\\x20ﷺ\\uD800uガé\\u0061\\u123\\u0061é\\x20')
    == '\\u0061\\uD800\\uDFFF\\x20صلى الله عليه وسلم\\uD800uガé\\u0061\\u123\\u0061é\\x20'
)
assert (
    normalize_passphrase('u\\uZ\\x20u\\\\ﷺ\\uD800\\\\u00e9ガ\\uDFFFU')
    == 'u\\uZ\\x20u\\\\صلى الله عليه وسلم\\uD800\\\\u00e9ガ\\uDFFFU'
)
assert (
    normalize_passphrase('U\\u00e9\\uD800\\uD800\\u0061😀\\uZ\\uZ\\u00e9\\uDFFFガﷺ')
    == 'U\\u00e9\\uD800\\uD800\\u0061😀\\uZ\\uZ\\u00e9\\uDFFFガصلى الله عليه وسلم'
)
try:
    normalize_passphrase('é\\uD800\\uDFFF')
    assert False
except UnicodeError:
    pass
try:
    normalize_passphrase('\\uDFFF\x00U😀')
    assert False
except UnicodeError:
    pass
assert (
    normalize_passphrase('\\uD800\\uD800é😀\\uD800\\u123\\x20')
    == '\\uD800\\uD800é😀\\uD800\\u123\\x20'
)
try:
    normalize_passphrase('ﷺa😀\\u00e9\\uDFFF\x00😀')
    assert False
except UnicodeError:
    pass
assert (
    normalize_passphrase('é\\uD800\\x20é\x00\x00\x00\\u0061\\u123\\\\uDFFF\\u00e9')
    == 'é\\uD800\\x20é\x00\x00\x00\\u0061\\u123\\\\uDFFF\\u00e9'
)
try:
    normalize_passphrase('\\u00e9\\u0061\\uDFFF')
    assert False
except UnicodeError:
    pass
try:
    normalize_passphrase('\\x20é\x00U\\uDFFF')
    assert False
except UnicodeError:
    pass
assert normalize_passphrase('\\u\\uD800\x00\\é\\uZガ😀') == '\\u\\uD800\x00\\é\\uZガ😀'
assert (
    normalize_passphrase('\\\\x20\\u00e9\x00ガ\x00ﷺUé\x00u')
    == '\\\\x20é\x00ガ\x00صلى الله عليه وسلمUé\x00u'
)
assert (
    normalize_passphrase('ガ\\x20\x00ガu\\u00e9ガ\\\\u123\\u00e9U\\uDFFF\\x20')
    == 'ガ\\x20\x00ガu\\u00e9ガ\\\\u123\\u00e9U\\uDFFF\\x20'
)
assert (
    normalize_passphrase('\\x20ガ\\uZé\\u123\\u00e9\\u0061\\u00e9\x00')
    == '\\x20ガ\\uZé\\u123\\u00e9\\u0061\\u00e9\x00'
)
assert (
    normalize_passphrase('é\x00éﷺ\\u00e9\\u0061😀éU\\u123é😀')
    == 'é\x00éصلى الله عليه وسلم\\u00e9\\u0061😀éU\\u123é😀'
)
try:
    normalize_passphrase('\\uDFFFﷺ')
    assert False
except UnicodeError:
    pass
assert normalize_passphrase('ﷺa\\uDFFF\\u123') == 'صلى الله عليه وسلمa\\uDFFF\\u123'
assert normalize_passphrase('\\u123ﷺé\\u0061\\\\uZ') == '\\u123صلى الله عليه وسلمé\\u0061\\\\uZ'
assert normalize_passphrase('é\\uZ\\u00e9u') == 'é\\uZ\\u00e9u'
assert normalize_passphrase('\\u0061ガué') == 'aガué'
assert (
    normalize_passphrase('\\u0061\\uDFFF\\uZ\\u0061u\\uDFFFﷺ\x00😀u')
    == '\\u0061\\uDFFF\\uZ\\u0061u\\uDFFFصلى الله عليه وسلم\x00😀u'
)
assert normalize_passphrase('\\aガuガ') == '\\aガuガ'
assert normalize_passphrase('\\x20u\\uZ\\u123U\x00') == '\\x20u\\uZ\\u123U\x00'
assert (
    normalize_passphrase('\\\x00ガU\\x20\\u123ﷺaé\\uDFFF\\uDFFF')
    == '\\\x00ガU\\x20\\u123صلى الله عليه وسلمaé\\uDFFF\\uDFFF'
)
try:
    normalize_passphrase('\\uD800\\u0061\\x20aﷺ\\uD800\\u0061ﷺUU\x00UU')
    assert False
except UnicodeError:
    pass
assert (
    normalize_passphrase('\x00ガ\\u123\\u123\\x20\\x20\\x20😀u\\uDFFF')
    == '\x00ガ\\u123\\u123\\x20\\x20\\x20😀u\\uDFFF'
)
assert (
    normalize_passphrase('U\\u0061\\u123Uﷺauau\\uD800')
    == 'U\\u0061\\u123Uصلى الله عليه وسلمauau\\uD800'
)
assert normalize_passphrase('\\a') == '\\a'
assert normalize_passphrase('é\\uZガ😀é') == 'é\\uZガ😀é'
assert normalize_passphrase('\\x20') == '\\x20'
assert (
    normalize_passphrase('uU\\uDFFF\\x20\\uZ\\uZ\\u00e9\\ﷺéa\\uZ')
    == 'uU\\uDFFF\\x20\\uZ\\uZ\\u00e9\\صلى الله عليه وسلمéa\\uZ'
)
assert (
    normalize_passphrase('\\u123\\u00e9\\uZガﷺ\\u0061\\uZué\\ﷺ\\u123\\u0061')
    == '\\u123\\u00e9\\uZガصلى الله عليه وسلم\\u0061\\uZué\\صلى الله عليه وسلم\\u123\\u0061'
)
assert (
    normalize_passphrase('\\uDFFF\x00\\x20\\uD800ﷺU😀aﷺ\\u123u\\u123\\')
    == '\\uDFFF\x00\\x20\\uD800صلى الله عليه وسلمU😀aصلى الله عليه وسلم\\u123u\\u123\\'
)
assert normalize_passphrase('uUガ') == 'uUガ'
try:
    normalize_passphrase('\\u0061\\uDFFF\\u0061')
    assert False
except UnicodeError:
    pass
assert normalize_passphrase('\\uZéﷺ') == '\\uZéصلى الله عليه وسلم'
assert normalize_passphrase('Ua\\u00e9\\u0061\\x20\\u0061U\\u0061U') == 'Uaéa\\x20aUaU'
assert normalize_passphrase('\x00\\u00e9U\\u0061\\ガ') == '\x00éUa\\ガ'
assert normalize_passphrase('\\u0061ﷺé') == 'aصلى الله عليه وسلمé'
assert normalize_passphrase('😀ガ😀U\\uDFFFa\\uZ\\uDFFFUa') == '😀ガ😀U\\uDFFFa\\uZ\\uDFFFUa'
assert normalize_passphrase('U') == 'U'
try:
    normalize_passphrase('\\x20\\x20U😀\\uDFFFéガ\\u0061a😀')
    assert False
except UnicodeError:
    pass
assert normalize_passphrase('U\\u0061é') == 'Uaé'
assert normalize_passphrase('ﷺ\\uZ\\u00e9') == 'صلى الله عليه وسلم\\uZ\\u00e9'
assert (
    normalize_passphrase('U\\u00e9😀\\u123\\uD800u\\uDFFF\\\\uDFFF\\u123')
    == 'U\\u00e9😀\\u123\\uD800u\\uDFFF\\\\uDFFF\\u123'
)
try:
    normalize_passphrase('\\😀\\x20😀\\uDFFFガ\\x20')
    assert False
except UnicodeError:
    pass
assert normalize_passphrase('\\uZガa\\u00e9\\u00e9\\x20\x00a') == '\\uZガa\\u00e9\\u00e9\\x20\x00a'
assert normalize_passphrase('u\\x20ガ\\\\u00e9\\u123a😀ガﷺ') == 'u\\x20ガ\\éሺ😀ガصلى الله عليه وسلم'
assert (
    normalize_passphrase('ガガé\\u123\\uDFFF😀ﷺ\x00\\x20\\uD800\\Uガ')
    == 'ガガé\\u123\\uDFFF😀صلى الله عليه وسلم\x00\\x20\\uD800\\Uガ'
)
assert normalize_passphrase('ガU\\u0061\\u123\\x20') == 'ガU\\u0061\\u123\\x20'
assert (
    normalize_passphrase('\\uZガ\\x20\\\\u00e9\\u00e9ガ😀\\u0061\\x20\\uDFFF\\u00e9')
    == '\\uZガ\\x20\\\\u00e9\\u00e9ガ😀\\u0061\\x20\\uDFFF\\u00e9'
)
assert (
    normalize_passphrase('\\u0061\\x20\\u123a\\u00e9\\uZ\\uDFFF\\uD800\\u123ﷺU\\uDFFFa')
    == '\\u0061\\x20\\u123a\\u00e9\\uZ\\uDFFF\\uD800\\u123صلى الله عليه وسلمU\\uDFFFa'
)
assert normalize_passphrase('\\u00e9u\\a\\uﷺ😀') == '\\u00e9u\\a\\uصلى الله عليه وسلم😀'
assert normalize_passphrase('ガé\\u123ガ\\u0061\\uD800Uu\\uZ') == 'ガé\\u123ガ\\u0061\\uD800Uu\\uZ'
assert normalize_passphrase('é') == 'é'
assert normalize_passphrase('U\\u00e9éガ😀ﷺ') == 'Uééガ😀صلى الله عليه وسلم'
try:
    normalize_passphrase('\\uDFFFﷺ\\u00e9ﷺ\\u00e9é\\uDFFF')
    assert False
except UnicodeError:
    pass
try:
    normalize_passphrase('é\\u00e9\\uDFFF\\uD800😀')
    assert False
except UnicodeError:
    pass
try:
    normalize_passphrase('😀\\u0061😀aガ\\uD800ガ\x00ガ\\uD800a\\uD800')
    assert False
except UnicodeError:
    pass
assert (
    normalize_passphrase('\\uZ\x00ガ\\uZ\\x20U\\u00e9u\x00Uﷺ\\u00e9ガ')
    == '\\uZ\x00ガ\\uZ\\x20U\\u00e9u\x00Uصلى الله عليه وسلم\\u00e9ガ'
)
assert (
    normalize_passphrase('\x00é\\u0061a\\x20\\x20\\u123\x00é\\u123\\x20\\u00e9')
    == '\x00é\\u0061a\\x20\\x20\\u123\x00é\\u123\\x20\\u00e9'
)
try:
    normalize_passphrase('\\uDFFF')
    assert False
except UnicodeError:
    pass
try:
    normalize_passphrase('U\\x20\\uD800\\\\u0061ﷺU\\uD800\x00\\u0061\\\\ﷺ😀')
    assert False
except UnicodeError:
    pass
try:
    normalize_passphrase('\\uDFFFガ')
    assert False
except UnicodeError:
    pass
assert normalize_passphrase('\\x20') == '\\x20'
try:
    normalize_passphrase('u\\\\uDFFF\\\\u00e9a😀\\uD800')
    assert False
except UnicodeError:
    pass
try:
    normalize_passphrase('\\ﷺ\\uDFFF')
    assert False
except UnicodeError:
    pass
assert normalize_passphrase('U\\uZa\\uZ\\\\u0061') == 'U\\uZa\\uZ\\\\u0061'
assert normalize_passphrase('\x00\\u123') == '\x00\\u123'
assert (
    normalize_passphrase('U\\uD800ﷺauﷺ\\x20\\uZ\\x20')
    == 'U\\uD800صلى الله عليه وسلمauصلى الله عليه وسلم\\x20\\uZ\\x20'
)
assert (
    normalize_passphrase('\\uZ😀ガ\\ガ\\uZﷺé\x00U😀')
    == '\\uZ😀ガ\\ガ\\uZصلى الله عليه وسلمé\x00U😀'
)
assert normalize_passphrase('\\\\uZ😀ué') == '\\\\uZ😀ué'
try:
    normalize_passphrase('\\uD800u\x00')
    assert False
except UnicodeError:
    pass
assert normalize_passphrase('ガ\\\\u123') == 'ガ\\\\u123'
assert (
    normalize_passphrase('\\u00e9é\\x20\\u123é\\\\\\u00e9\\u123ガ\\uD800')
    == '\\u00e9é\\x20\\u123é\\\\\\u00e9\\u123ガ\\uD800'
)
try:
    normalize_passphrase('\\uDFFFu😀ﷺ\\u00e9ガ\\x20ﷺガUﷺ\\\\u0061')
    assert False
except UnicodeError:
    pass
assert (
    normalize_passphrase('ﷺ\\uZﷺ😀é\\uZ\\') == 'صلى الله عليه وسلم\\uZصلى الله عليه وسلم😀é\\uZ\\'
)
assert normalize_passphrase('u') == 'u'
assert normalize_passphrase('\x00\\x20éu') == '\x00\\x20éu'
assert normalize_passphrase('😀ﷺ\\u00e9a') == '😀صلى الله عليه وسلمéa'
assert (
    normalize_passphrase('\\ﷺ\\u123\\u00e9\\uD800\\u0061\\u0061')
    == '\\صلى الله عليه وسلم\\u123\\u00e9\\uD800\\u0061\\u0061'
)
assert normalize_passphrase('\\u0061\\x20aaﷺ\\u123u') == '\\u0061\\x20aaصلى الله عليه وسلم\\u123u'
assert (
    normalize_passphrase('uﷺ\\uZé\\uZ😀😀\\uZ\x00ガéU')
    == 'uصلى الله عليه وسلم\\uZé\\uZ😀😀\\uZ\x00ガéU'
)
assert normalize_passphrase('aUaa') == 'aUaa'
assert (
    normalize_passphrase('\\aﷺ\x00\\u123\x00U\\uDFFF\\u00e9\\u0061a\\u00e9\\uD800ﷺ')
    == '\\aصلى الله عليه وسلم\x00\\u123\x00U\\uDFFF\\u00e9\\u0061a\\u00e9\\uD800صلى الله عليه وسلم'
)
assert (
    normalize_passphrase('\\x20\\u00e9\\u123\\ﷺ\\u00e9\\u00e9\\uDFFF\\uDFFF')
    == '\\x20\\u00e9\\u123\\صلى الله عليه وسلم\\u00e9\\u00e9\\uDFFF\\uDFFF'
)
assert (
    normalize_passphrase('\\uD800\\uDFFFガ\\uZガaa\x00UUU😀') == '\\uD800\\uDFFFガ\\uZガaa\x00UUU😀'
)
assert (
    normalize_passphrase('\\u123\\u00e9\\uDFFFガ\\x20\\uZ\\u123\\u123aﷺéUé\\u0061')
    == '\\u123\\u00e9\\uDFFFガ\\x20\\uZ\\u123\\u123aصلى الله عليه وسلمéUé\\u0061'
)
assert normalize_passphrase('\\u123U\\\x00uU\\uD800\\u123') == '\\u123U\\\x00uU\\uD800\\u123'
assert normalize_passphrase('é\\uZuガ') == 'é\\uZuガ'
try:
    normalize_passphrase('\\uDFFFau\x00ﷺé')
    assert False
except UnicodeError:
    pass
try:
    normalize_passphrase('éu\\uD800\\uDFFF\\x20ﷺu\\')
    assert False
except UnicodeError:
    pass
try:
    normalize_passphrase('\\\\uD800UuU')
    assert False
except UnicodeError:
    pass
assert normalize_passphrase('aaU😀\\u00e9u') == 'aaU😀éu'
assert normalize_passphrase('\\u00e9\\') == 'é\\'
assert (
    normalize_passphrase('éガ\\x20\\uDFFFガﷺUﷺガ\\\\u123')
    == 'éガ\\x20\\uDFFFガصلى الله عليه وسلمUصلى الله عليه وسلمガ\\\\u123'
)
assert (
    normalize_passphrase('\x00a\\a\\uD800\x00\\u00e9aa😀\\u123\\uD800\\uD800\\u00e9')
    == '\x00a\\a\\uD800\x00\\u00e9aa😀\\u123\\uD800\\uD800\\u00e9'
)
assert (
    normalize_passphrase('U\\uZ\\😀u\\u123U\\uD800\\uD800😀\\uZ')
    == 'U\\uZ\\😀u\\u123U\\uD800\\uD800😀\\uZ'
)
assert normalize_passphrase('\\uZ\\uDFFFガﷺéaガ') == '\\uZ\\uDFFFガصلى الله عليه وسلمéaガ'
assert (
    normalize_passphrase('\\u123u\x00\\\\uD800Uﷺガa\\😀')
    == '\\u123u\x00\\\\uD800Uصلى الله عليه وسلمガa\\😀'
)
assert (
    normalize_passphrase('\\x20\\u00e9a\x00ガ\\ガ😀a\\ガ\\u00e9ﷺU')
    == '\\x20éa\x00ガ\\ガ😀a\\ガéصلى الله عليه وسلمU'
)
try:
    normalize_passphrase('é\\uD800\\u00e9')
    assert False
except UnicodeError:
    pass
try:
    normalize_passphrase('a\\uD800\\x20ﷺ\\x20aﷺUﷺUU')
    assert False
except UnicodeError:
    pass
assert (
    normalize_passphrase('\x00\\uDFFF😀\\u00e9é😀\\u0061\\uZ\\uDFFFu\\uﷺ')
    == '\x00\\uDFFF😀\\u00e9é😀\\u0061\\uZ\\uDFFFu\\uصلى الله عليه وسلم'
)
assert (
    normalize_passphrase('\\u00e9U\\u00e9Uﷺ\\x20uﷺ😀u')
    == 'éUéUصلى الله عليه وسلم\\x20uصلى الله عليه وسلم😀u'
)
assert normalize_passphrase('ガ\x00a\\u0061U') == 'ガ\x00aaU'
assert normalize_passphrase('a\\\\u123\\ﷺ') == 'a\\\\u123\\صلى الله عليه وسلم'
assert normalize_passphrase('\\uZ\x00') == '\\uZ\x00'
assert normalize_passphrase('\x00\x00😀u\\u123😀') == '\x00\x00😀u\\u123😀'
assert (
    normalize_passphrase('\x00UガU\\u00e9\\x20\\\\uD800\\u00e9\\u123\x00\\u00e9\x00')
    == '\x00UガU\\u00e9\\x20\\\\uD800\\u00e9\\u123\x00\\u00e9\x00'
)
assert normalize_passphrase('\\u0061ガU') == 'aガU'
assert (
    normalize_passphrase('\\uD800é\\uD800\\uD800\\uZ\\u00e9\\uZ\\uD800\\u123ﷺ')
    == '\\uD800é\\uD800\\uD800\\uZ\\u00e9\\uZ\\uD800\\u123صلى الله عليه وسلم'
)
assert (
    normalize_passphrase('\\uD800\x00ﷺU\\uD800\\u123😀\\uD800\x00é\\uD800\\u00e9ガ')
    == '\\uD800\x00صلى الله عليه وسلمU\\uD800\\u123😀\\uD800\x00é\\uD800\\u00e9ガ'
)
try:
    normalize_passphrase('a😀\\u0061\\u00e9\\uD800')
    assert False
except UnicodeError:
    pass
assert (
    normalize_passphrase('ガ\\\\x20\\u0061ガ\\u123\\uD800é\\u123ガ\\')
    == 'ガ\\\\x20\\u0061ガ\\u123\\uD800é\\u123ガ\\'
)
assert normalize_passphrase('\\u00e9ﷺ\\é') == 'éصلى الله عليه وسلم\\é'
assert normalize_passphrase('😀\\\\uZ\\') == '😀\\\\uZ\\'
assert (
    normalize_passphrase('é\\u00e9\\u123\\u0061\\uDFFF\x00\x00ﷺ\\uDFFF\\ガ\\u123é')
    == 'é\\u00e9\\u123\\u0061\\uDFFF\x00\x00صلى الله عليه وسلم\\uDFFF\\ガ\\u123é'
)
assert normalize_passphrase('u') == 'u'
assert normalize_passphrase('ﷺU') == 'صلى الله عليه وسلمU'
assert (
    normalize_passphrase('\\uDFFFガ\\uZ😀\\uD800éaﷺﷺ\\uD800a')
    == '\\uDFFFガ\\uZ😀\\uD800éaصلى الله عليه وسلمصلى الله عليه وسلم\\uD800a'
)
assert (
    normalize_passphrase('ﷺ😀U\\x20\\u123\\uD800ガéu\\uD800\\x20')
    == 'صلى الله عليه وسلم😀U\\x20\\u123\\uD800ガéu\\uD800\\x20'
)
assert normalize_passphrase('a\\u123\\x20\\uD800') == 'a\\u123\\x20\\uD800'
assert (
    normalize_passphrase('😀é\\x20\\x20é\\uZガ\x00\\uZ\\uZ\\u123\x00\\u0061a')
    == '😀é\\x20\\x20é\\uZガ\x00\\uZ\\uZ\\u123\x00\\u0061a'
)
assert (
    normalize_passphrase('ﷺ\\u0061\\uZ\\u123\\uZ\\uD800a')
    == 'صلى الله عليه وسلم\\u0061\\uZ\\u123\\uZ\\uD800a'
)
assert (
    normalize_passphrase('\\uZu\\u123\\uD800aé\\u0061ﷺuﷺ')
    == '\\uZu\\u123\\uD800aé\\u0061صلى الله عليه وسلمuصلى الله عليه وسلم'
)
try:
    normalize_passphrase('😀\\ﷺaﷺU\\uDFFF')
    assert False
except UnicodeError:
    pass
assert normalize_passphrase('\\ガ😀') == '\\ガ😀'
assert (
    normalize_passphrase('\\u0061é\\uZ\\u00e9ﷺﷺUa')
    == '\\u0061é\\uZ\\u00e9صلى الله عليه وسلمصلى الله عليه وسلمUa'
)
assert normalize_passphrase('U\\u\\x20ガ') == 'U\\u\\x20ガ'
assert (
    normalize_passphrase('ガ\\u123\\uDFFF\\u123éau\\u123\x00\\u123\\u00e9\\uZ\\uZ')
    == 'ガ\\u123\\uDFFF\\u123éau\\u123\x00\\u123\\u00e9\\uZ\\uZ'
)
assert (
    normalize_passphrase('\\u00e9\\uD800\\uZ\x00\\uZaaauﷺ😀😀')
    == '\\u00e9\\uD800\\uZ\x00\\uZaaauصلى الله عليه وسلم😀😀'
)
assert (
    normalize_passphrase('\x00a\\u123\\uZ\\uZ\\u123ﷺ\\u123\\u00e9\\uDFFF😀')
    == '\x00a\\u123\\uZ\\uZ\\u123صلى الله عليه وسلم\\u123\\u00e9\\uDFFF😀'
)
assert (
    normalize_passphrase('\\uZ\\uZ\\\\u00e9\\uZ\\u0061😀ﷺ')
    == '\\uZ\\uZ\\\\u00e9\\uZ\\u0061😀صلى الله عليه وسلم'
)
assert (
    normalize_passphrase('ガ\\uDFFF\\u00e9\\\\u123é\\u123U\\uZ')
    == 'ガ\\uDFFF\\u00e9\\\\u123é\\u123U\\uZ'
)
assert normalize_passphrase('😀\\u123UU\\uD800\\uDFFF') == '😀\\u123UU\\uD800\\uDFFF'
assert (
    normalize_passphrase('ガU\\uDFFF\\u0061\\uD800\\u00e9\x00ガ\\uZ')
    == 'ガU\\uDFFF\\u0061\\uD800\\u00e9\x00ガ\\uZ'
)
assert (
    normalize_passphrase('\\uZ\\uD800ﷺa\\uDFFF😀\\uDFFF')
    == '\\uZ\\uD800صلى الله عليه وسلمa\\uDFFF😀\\uDFFF'
)
try:
    normalize_passphrase('\\aa\x00a\x00\\u0061a\\u00e9U\x00\\uDFFF\\uDFFF')
    assert False
except UnicodeError:
    pass
assert normalize_passphrase('\\x20\\uZﷺ\\') == '\\x20\\uZصلى الله عليه وسلم\\'
assert normalize_passphrase('\\u0061') == 'a'
assert normalize_passphrase('😀ﷺガéガ') == '😀صلى الله عليه وسلمガéガ'
assert normalize_passphrase('éaUa\\uZ\\x20Ué\\uD800') == 'éaUa\\uZ\\x20Ué\\uD800'
assert normalize_passphrase('😀ua\\u123ﷺ\\u00e9é') == '😀ua\\u123صلى الله عليه وسلم\\u00e9é'
assert normalize_passphrase('\\u00e9aガ\\u123uガ\x00é') == '\\u00e9aガ\\u123uガ\x00é'
assert normalize_passphrase('\\x20é') == '\\x20é'
from embit import bip39

assert (
    bip39.mnemonic_to_seed(
        'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about',
        password=normalize_passphrase(''),
    ).hex()
    == '5eb00bbddcf069084889a8ab9155568165f5c453ccb85e70811aaed6f6da5fc19a5ac40b389cd370d086206dec8aa6c43daea6690f20ad3d8d48b2d2ce9e38e4'
)
assert (
    bip39.mnemonic_to_seed(
        'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about',
        password=normalize_passphrase('é'),
    ).hex()
    == 'f37f8652bf7004d4bd4ba7702e70e647f54965758656423dde58d64fa725c1e8be1b0416864e10f714c0730e46f9676079b4fd4f72fcf0c09a120ae65589c091'
)
assert (
    bip39.mnemonic_to_seed(
        'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about',
        password=normalize_passphrase('é'),
    ).hex()
    == 'f37f8652bf7004d4bd4ba7702e70e647f54965758656423dde58d64fa725c1e8be1b0416864e10f714c0730e46f9676079b4fd4f72fcf0c09a120ae65589c091'
)
assert (
    bip39.mnemonic_to_seed(
        'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about',
        password=normalize_passphrase('㍍ガバヴァぱばぐゞちぢ十人十色'),
    ).hex()
    == 'ba553eedefe76e67e2602dc20184c564010859faada929a090dd2c57aacb204ceefd15404ab50ef3e8dbeae5195aeae64b0def4d2eead1cdc728a33ced520ffd'
)
assert (
    bip39.mnemonic_to_seed(
        'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about',
        password=normalize_passphrase('\x00'),
    ).hex()
    == '4ca62e6b646a1d3548e08b314e11b9215b35a4cbbbdc12c0a482b44aa013cd3f68a8f6a33f561e34dc03a7367110de228e59d3e3700bff1ea561818134fe59eb'
)
assert (
    bip39.mnemonic_to_seed(
        'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about',
        password=normalize_passphrase('\\u0061'),
    ).hex()
    == '87d1b98527bc044ca079026f96de0f4f500311598024b524391919116845af4e664e5cac53ad710e1509955c90b5fe94bb66b6df3fce0634a63fe13b9179f6d3'
)
assert (
    bip39.mnemonic_to_seed(
        'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about',
        password=normalize_passphrase('\\\\u0061'),
    ).hex()
    == 'c11cb8a82405a3ed8a1e7d1437f7d958aca102f51e23685979620dea077a0b61440bd1858ee498895fcadce282e410d8fd835b0dfa36e1b60094f4170183411a'
)
assert (
    bip39.mnemonic_to_seed(
        'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about',
        password=normalize_passphrase('\\u005cu0061'),
    ).hex()
    == '1b579213681dcc7f62313293fd0d6cdaaa1c74dc4b633c801a3c26885748cabdfdbb718c95af743eb0e6fcee2c9b920a50552833b84c485762478db6fe5e5926'
)
assert (
    bip39.mnemonic_to_seed(
        'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about',
        password=normalize_passphrase('\\uD800\\uZ'),
    ).hex()
    == '70b80f74314d166a9a15a5918644e84188a4dadd9b6aab1408b770db6875d4317ad68270fbcb36c1c6ac8bd17ed898b8500f14a9ce06be2476cac9595ebd6e7d'
)
assert (
    bip39.mnemonic_to_seed(
        'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about',
        password=normalize_passphrase('\\u'),
    ).hex()
    == '4cc32b6368922c251f30bae32d9d85db48f30902d3f236862f30e8bbec2bcd221b844675815d3ad53a3d4bd35641e65a3ee9213adf41974460cb8677ee0ec458'
)
assert (
    bip39.mnemonic_to_seed(
        'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about',
        password=normalize_passphrase('\\u123'),
    ).hex()
    == 'a146b0f03f8657276a1cc697af1cd955facb769c8437a55da39711680433a9ef9787d4d7810873d083d53d23080a2cb993944f990b9db41b7c7a3df52586dd4c'
)
assert (
    bip39.mnemonic_to_seed(
        'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about',
        password=normalize_passphrase('\\U0001f600'),
    ).hex()
    == 'ae662eeded4fffcf2e50101dc4ccc4ae500b01c3acc95e3c22fb3735d79510753e190dd3c20519d39304d5b7da1a9234d8c8eed85332f2305a0df43220e26444'
)
assert (
    bip39.mnemonic_to_seed(
        'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about',
        password=normalize_passphrase('\\n'),
    ).hex()
    == 'ebdad9515ba1b64e916813594e5aff4e51d4aa7782f372227154627c4906c6bbfc64d9a9a79a70f452315458192a8e45495f5e40b60a65ba7ccc8ccee413b29d'
)
assert (
    bip39.mnemonic_to_seed(
        'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about',
        password=normalize_passphrase('abc\\'),
    ).hex()
    == '093dcfdb3bb65cf2b698c980ccd094ec6d83147a0525385b343dc1aa8226bd87d38720b64965dda91723c423a81ede1158563013f19981ff36d918484fe95f4d'
)
assert (
    bip39.mnemonic_to_seed(
        'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about',
        password=normalize_passphrase('\\x41'),
    ).hex()
    == '1e27d45e9e129b8deeefa2854de4be438f35570874bacbbf8a812d5d923bff281f60b0397b5508d343faf121cabcfed5cb0d89e41fb96ee98e214279f1ef5cf2'
)
assert (
    bip39.mnemonic_to_seed(
        'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about',
        password=normalize_passphrase(
            '\x00\x00\\uZ\\uDFFF\\uDFFFガ\\u0061\\uD800é\\uD800\x00ﷺ\\u123\\'
        ),
    ).hex()
    == '4e858ba34bc118dd02b52861d1f906d152fe14051d51d7d4caab1fc44d1dc9e0cf0e4cb86887de3fe3d965786fdff0289605cd011372be30f0a4a84a25c03214'
)
assert (
    bip39.mnemonic_to_seed(
        'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about',
        password=normalize_passphrase('\\u00e9\\x20\\u0061ガ\\u123\\u00e9\\u0061\x00\\uZ'),
    ).hex()
    == 'dc3f3e1717d01d96bc61056ace01aaf2657fbbb5a3bdcabd93e2cbb2ccf7875a9c09f7f4605e271667285a6f02da335662cefb98d93ba73fe675b197e18a1003'
)
assert (
    bip39.mnemonic_to_seed(
        'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about',
        password=normalize_passphrase('\\uD800ﷺﷺ\\u0061\\x20ﷺ\\ガ\\uDFFFガé\\uZ\\uD800'),
    ).hex()
    == 'bfcad7050a1f83f46f047dec9166ae2631251f591d3a977afa468e457059094938c45bf636c3772ac8f19a17e20633b8ba99a9f1368476e6da2fa6d105d44e54'
)
assert (
    bip39.mnemonic_to_seed(
        'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about',
        password=normalize_passphrase('\\uZéé\\u00e9a\\\x00\\u00e9ガ'),
    ).hex()
    == '0612fa7608749a9d5e3f53636bd609287d188e0f05e64441b8d4be990bc8e67d3f9f2aa4700d865526a58e98822ff5685f541f67ad2948474d212e8ba1b237fa'
)
assert (
    bip39.mnemonic_to_seed(
        'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about',
        password=normalize_passphrase('\\uZ\\uZガUua\\u123é\\'),
    ).hex()
    == 'ca1f878b188d86fb514c412350aedf1424148c9e508e3e9cd24874b99f798337e381b410f072fd4ae3f4e9cb144efe9ea8445742e03acc95e938a0d444402773'
)
assert (
    bip39.mnemonic_to_seed(
        'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about',
        password=normalize_passphrase('\\x20\\u0061u\\u0061\\uZu\\ﷺ'),
    ).hex()
    == 'f1ce39adceeb5cde671379434f471425cea295a0561697f7127aa3f9c476ff27ad1c13a6e0783c8d54e7ea2fc76ae8aeffacc57743e9cc1f063d14fe4ea2e793'
)
assert (
    bip39.mnemonic_to_seed(
        'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about',
        password=normalize_passphrase('\\u123ﷺ\\u123U😀\\uD800é\\u123'),
    ).hex()
    == 'd81c1fd03caa87c48dea89a358129751b720a9c05daa1bbcc8bfbb5875b6d079816f3a4e86087735ee82e72c0365dbc29ca4bfc16d54f0f068c0e2d20339bc69'
)
assert (
    bip39.mnemonic_to_seed(
        'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about',
        password=normalize_passphrase('u\\u123a\\uZ\\u123\\u00e9'),
    ).hex()
    == 'e3fab485c6fd4eaecae7a27465120d4aa6f14dce4338c0cc67bcbebd488b39fc281e45d0dc17b7c7f4421b0df4dcfd552088412d589d48ef2a04a22afb1e8ed6'
)
assert (
    bip39.mnemonic_to_seed(
        'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about',
        password=normalize_passphrase(
            '\\u00e9\\u00e9\x00\\u00e9\\uZ\\uDFFF\\\x00aa\\uZ\\uD800\\u123'
        ),
    ).hex()
    == '6c4cae9212d860d4d6b5d5e65a805149876439e722107ae2280734f0a58971a3fb4857c99fb1d34a23d71d112e8b6dfe8ed839cd5f6b0e523a719b1b25ed43f9'
)
assert (
    bip39.mnemonic_to_seed(
        'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about',
        password=normalize_passphrase('\\uZ'),
    ).hex()
    == '7cdef1920fa6b1dd5b53b0d45a2be03fe58ed90d79de3dd0f9ba0c80712077fe6c6aadfdcd495992bfe0f344ed53a7ae8e1a960c450c12519f879641177833a3'
)
assert (
    bip39.mnemonic_to_seed(
        'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about',
        password=normalize_passphrase('😀u\\u00e9ué'),
    ).hex()
    == '5387dda91805443e73073be31186d61a1ffbf79a7df710923af720d7f2ed284ecd5ddd7ebeeb2602b0d34ee590603b6731d813476efaeda04da928ccf8a24697'
)
assert (
    bip39.mnemonic_to_seed(
        'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about',
        password=normalize_passphrase('é😀\\uZ\\u123\\uZ\x00\x00é\\u00e9\\u123ﷺガ\x00\\u00e9'),
    ).hex()
    == 'fb65b6658198f45228f4a6753c2bba7f3080cdafbb0a27726a73261072a81309bfe3cc9064b21b6fde58a776ee7b145b42b8e3d0e1d6665e40212e02a3ea622d'
)
assert (
    bip39.mnemonic_to_seed(
        'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about',
        password=normalize_passphrase('ﷺ\\'),
    ).hex()
    == '48012bf0d0cc7acef12db028a6699af293d4032cee8139f012a67a91530edf9f16b1eb38d9e95f6e8eb7affb88c7ed9d54ea337261459bce681e92618c8e1d8b'
)
assert (
    bip39.mnemonic_to_seed(
        'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about',
        password=normalize_passphrase('\\u123\\\\uZ\\uZ'),
    ).hex()
    == '51750a69ded6ea054cc29d274ae06a4d4fd40505fd81f0146506fbc60bf9e7276d916960b913fe54033e94210afe4ee9e10538a679527595e2102bd3b88d8957'
)
assert (
    bip39.mnemonic_to_seed(
        'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about',
        password=normalize_passphrase('\\u00e9\x00U\\ﷺ'),
    ).hex()
    == '4882d7b35e0210dbf17626b850980c9ca22f91f013422e143c5cddfef4783ac93f14d6041d1c811b503737111e0f1aa04971e26847c0ae40ffc24e15356fcc4c'
)
assert (
    bip39.mnemonic_to_seed(
        'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about',
        password=normalize_passphrase('\\a😀\\uZ\\x20Uガé'),
    ).hex()
    == '94410e43720ca23cea79a1cb15f3499073b341f28d90cc7ab6deed745392675bd27883556cac8b05129250bda92c8e4e1ae7317aea441050b13a9efaee322b85'
)
assert (
    bip39.mnemonic_to_seed(
        'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about',
        password=normalize_passphrase('\x00\\u123ﷺガ\\u0061\\u00e9\\uZa\\uDFFF\\UU'),
    ).hex()
    == 'e0f9b756100c4c4ccdb35eefb2bc37ebaf5985ca4ad99baf6fbe10361c64ef0cafca9f4c8d9b579611dea8b5c02e5067f5b40c65b776372afd8a517a071bcb4b'
)
for i in range(3):
    gc.collect()
assert camera.settings()['rust_heap_bytes'] == baseline
print('@@PASSPHRASE_REF_PASS', 515)
