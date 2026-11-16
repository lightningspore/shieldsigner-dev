# Generated public fixtures only; actual original Seed class on native runtime.
from seedsigner_port.seed import Seed, InvalidSeedException
from seedsigner_port.decode_platform import FeatureUnavailable
from embit import bip39
import camera
import gc

baseline = camera.settings()['rust_heap_bytes']
words = 'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about'.split()
s = Seed(words, passphrase='TREZOR')
assert (
    s.seed_bytes.hex()
    == 'c55257c360c07c72029aebc1b53c05ed0362ada38ead3e3e9efa3708e53495531f09a6987599d18264c1e1c92f2cf141630c7a3c4ab7c81b2f001698e7463b04'
)
assert (
    s.mnemonic_str
    == 'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about'
)
assert s.mnemonic_display_list == words
assert s.has_passphrase and s.passphrase == 'TREZOR'
assert s.seedqr_supported and s.bip85_supported
alias = s.seed_bytes
s.wipe()
assert alias == bytes(64)
assert (
    s.seed_bytes is None
    and s.master_secret is None
    and s.mnemonic_list == []
    and s.passphrase == ''
)
assert (
    ' '.join(words)
    == 'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about'
)
assert bip39.mnemonic_is_valid(
    'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about'
)
del alias, s, words
gc.collect()
words = 'legal winner thank year wave sausage worth useful legal winner thank yellow'.split()
s = Seed(words, passphrase='TREZOR')
assert (
    s.seed_bytes.hex()
    == '2e8905819b8723fe2c1d161860e5ee1830318dbf49a83bd451cfb8440c28bd6fa457fe1296106559a3c80937a1c1069be3a3a5bd381ee6260e8d9739fce1f607'
)
assert (
    s.mnemonic_str == 'legal winner thank year wave sausage worth useful legal winner thank yellow'
)
assert s.mnemonic_display_list == words
assert s.has_passphrase and s.passphrase == 'TREZOR'
assert s.seedqr_supported and s.bip85_supported
alias = s.seed_bytes
s.wipe()
assert alias == bytes(64)
assert (
    s.seed_bytes is None
    and s.master_secret is None
    and s.mnemonic_list == []
    and s.passphrase == ''
)
assert (
    ' '.join(words) == 'legal winner thank year wave sausage worth useful legal winner thank yellow'
)
assert bip39.mnemonic_is_valid(
    'legal winner thank year wave sausage worth useful legal winner thank yellow'
)
del alias, s, words
gc.collect()
words = 'letter advice cage absurd amount doctor acoustic avoid letter advice cage above'.split()
s = Seed(words, passphrase='TREZOR')
assert (
    s.seed_bytes.hex()
    == 'd71de856f81a8acc65e6fc851a38d4d7ec216fd0796d0a6827a3ad6ed5511a30fa280f12eb2e47ed2ac03b5c462a0358d18d69fe4f985ec81778c1b370b652a8'
)
assert (
    s.mnemonic_str
    == 'letter advice cage absurd amount doctor acoustic avoid letter advice cage above'
)
assert s.mnemonic_display_list == words
assert s.has_passphrase and s.passphrase == 'TREZOR'
assert s.seedqr_supported and s.bip85_supported
alias = s.seed_bytes
s.wipe()
assert alias == bytes(64)
assert (
    s.seed_bytes is None
    and s.master_secret is None
    and s.mnemonic_list == []
    and s.passphrase == ''
)
assert (
    ' '.join(words)
    == 'letter advice cage absurd amount doctor acoustic avoid letter advice cage above'
)
assert bip39.mnemonic_is_valid(
    'letter advice cage absurd amount doctor acoustic avoid letter advice cage above'
)
del alias, s, words
gc.collect()
words = 'zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo wrong'.split()
s = Seed(words, passphrase='TREZOR')
assert (
    s.seed_bytes.hex()
    == 'ac27495480225222079d7be181583751e86f571027b0497b5b5d11218e0a8a13332572917f0f8e5a589620c6f15b11c61dee327651a14c34e18231052e48c069'
)
assert s.mnemonic_str == 'zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo wrong'
assert s.mnemonic_display_list == words
assert s.has_passphrase and s.passphrase == 'TREZOR'
assert s.seedqr_supported and s.bip85_supported
alias = s.seed_bytes
s.wipe()
assert alias == bytes(64)
assert (
    s.seed_bytes is None
    and s.master_secret is None
    and s.mnemonic_list == []
    and s.passphrase == ''
)
assert ' '.join(words) == 'zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo wrong'
assert bip39.mnemonic_is_valid('zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo wrong')
del alias, s, words
gc.collect()
words = 'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon agent'.split()
s = Seed(words, passphrase='TREZOR')
assert (
    s.seed_bytes.hex()
    == '035895f2f481b1b0f01fcf8c289c794660b289981a78f8106447707fdd9666ca06da5a9a565181599b79f53b844d8a71dd9f439c52a3d7b3e8a79c906ac845fa'
)
assert (
    s.mnemonic_str
    == 'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon agent'
)
assert s.mnemonic_display_list == words
assert s.has_passphrase and s.passphrase == 'TREZOR'
assert s.seedqr_supported and s.bip85_supported
alias = s.seed_bytes
s.wipe()
assert alias == bytes(64)
assert (
    s.seed_bytes is None
    and s.master_secret is None
    and s.mnemonic_list == []
    and s.passphrase == ''
)
assert (
    ' '.join(words)
    == 'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon agent'
)
assert bip39.mnemonic_is_valid(
    'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon agent'
)
del alias, s, words
gc.collect()
words = 'legal winner thank year wave sausage worth useful legal winner thank year wave sausage worth useful legal will'.split()
s = Seed(words, passphrase='TREZOR')
assert (
    s.seed_bytes.hex()
    == 'f2b94508732bcbacbcc020faefecfc89feafa6649a5491b8c952cede496c214a0c7b3c392d168748f2d4a612bada0753b52a1c7ac53c1e93abd5c6320b9e95dd'
)
assert (
    s.mnemonic_str
    == 'legal winner thank year wave sausage worth useful legal winner thank year wave sausage worth useful legal will'
)
assert s.mnemonic_display_list == words
assert s.has_passphrase and s.passphrase == 'TREZOR'
assert s.seedqr_supported and s.bip85_supported
alias = s.seed_bytes
s.wipe()
assert alias == bytes(64)
assert (
    s.seed_bytes is None
    and s.master_secret is None
    and s.mnemonic_list == []
    and s.passphrase == ''
)
assert (
    ' '.join(words)
    == 'legal winner thank year wave sausage worth useful legal winner thank year wave sausage worth useful legal will'
)
assert bip39.mnemonic_is_valid(
    'legal winner thank year wave sausage worth useful legal winner thank year wave sausage worth useful legal will'
)
del alias, s, words
gc.collect()
words = 'letter advice cage absurd amount doctor acoustic avoid letter advice cage absurd amount doctor acoustic avoid letter always'.split()
s = Seed(words, passphrase='TREZOR')
assert (
    s.seed_bytes.hex()
    == '107d7c02a5aa6f38c58083ff74f04c607c2d2c0ecc55501dadd72d025b751bc27fe913ffb796f841c49b1d33b610cf0e91d3aa239027f5e99fe4ce9e5088cd65'
)
assert (
    s.mnemonic_str
    == 'letter advice cage absurd amount doctor acoustic avoid letter advice cage absurd amount doctor acoustic avoid letter always'
)
assert s.mnemonic_display_list == words
assert s.has_passphrase and s.passphrase == 'TREZOR'
assert s.seedqr_supported and s.bip85_supported
alias = s.seed_bytes
s.wipe()
assert alias == bytes(64)
assert (
    s.seed_bytes is None
    and s.master_secret is None
    and s.mnemonic_list == []
    and s.passphrase == ''
)
assert (
    ' '.join(words)
    == 'letter advice cage absurd amount doctor acoustic avoid letter advice cage absurd amount doctor acoustic avoid letter always'
)
assert bip39.mnemonic_is_valid(
    'letter advice cage absurd amount doctor acoustic avoid letter advice cage absurd amount doctor acoustic avoid letter always'
)
del alias, s, words
gc.collect()
words = 'zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo when'.split()
s = Seed(words, passphrase='TREZOR')
assert (
    s.seed_bytes.hex()
    == '0cd6e5d827bb62eb8fc1e262254223817fd068a74b5b449cc2f667c3f1f985a76379b43348d952e2265b4cd129090758b3e3c2c49103b5051aac2eaeb890a528'
)
assert s.mnemonic_str == 'zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo when'
assert s.mnemonic_display_list == words
assert s.has_passphrase and s.passphrase == 'TREZOR'
assert s.seedqr_supported and s.bip85_supported
alias = s.seed_bytes
s.wipe()
assert alias == bytes(64)
assert (
    s.seed_bytes is None
    and s.master_secret is None
    and s.mnemonic_list == []
    and s.passphrase == ''
)
assert ' '.join(words) == 'zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo when'
assert bip39.mnemonic_is_valid(
    'zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo when'
)
del alias, s, words
gc.collect()
words = 'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon art'.split()
s = Seed(words, passphrase='TREZOR')
assert (
    s.seed_bytes.hex()
    == 'bda85446c68413707090a52022edd26a1c9462295029f2e60cd7c4f2bbd3097170af7a4d73245cafa9c3cca8d561a7c3de6f5d4a10be8ed2a5e608d68f92fcc8'
)
assert (
    s.mnemonic_str
    == 'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon art'
)
assert s.mnemonic_display_list == words
assert s.has_passphrase and s.passphrase == 'TREZOR'
assert s.seedqr_supported and s.bip85_supported
alias = s.seed_bytes
s.wipe()
assert alias == bytes(64)
assert (
    s.seed_bytes is None
    and s.master_secret is None
    and s.mnemonic_list == []
    and s.passphrase == ''
)
assert (
    ' '.join(words)
    == 'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon art'
)
assert bip39.mnemonic_is_valid(
    'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon art'
)
del alias, s, words
gc.collect()
words = 'legal winner thank year wave sausage worth useful legal winner thank year wave sausage worth useful legal winner thank year wave sausage worth title'.split()
s = Seed(words, passphrase='TREZOR')
assert (
    s.seed_bytes.hex()
    == 'bc09fca1804f7e69da93c2f2028eb238c227f2e9dda30cd63699232578480a4021b146ad717fbb7e451ce9eb835f43620bf5c514db0f8add49f5d121449d3e87'
)
assert (
    s.mnemonic_str
    == 'legal winner thank year wave sausage worth useful legal winner thank year wave sausage worth useful legal winner thank year wave sausage worth title'
)
assert s.mnemonic_display_list == words
assert s.has_passphrase and s.passphrase == 'TREZOR'
assert s.seedqr_supported and s.bip85_supported
alias = s.seed_bytes
s.wipe()
assert alias == bytes(64)
assert (
    s.seed_bytes is None
    and s.master_secret is None
    and s.mnemonic_list == []
    and s.passphrase == ''
)
assert (
    ' '.join(words)
    == 'legal winner thank year wave sausage worth useful legal winner thank year wave sausage worth useful legal winner thank year wave sausage worth title'
)
assert bip39.mnemonic_is_valid(
    'legal winner thank year wave sausage worth useful legal winner thank year wave sausage worth useful legal winner thank year wave sausage worth title'
)
del alias, s, words
gc.collect()
words = 'letter advice cage absurd amount doctor acoustic avoid letter advice cage absurd amount doctor acoustic avoid letter advice cage absurd amount doctor acoustic bless'.split()
s = Seed(words, passphrase='TREZOR')
assert (
    s.seed_bytes.hex()
    == 'c0c519bd0e91a2ed54357d9d1ebef6f5af218a153624cf4f2da911a0ed8f7a09e2ef61af0aca007096df430022f7a2b6fb91661a9589097069720d015e4e982f'
)
assert (
    s.mnemonic_str
    == 'letter advice cage absurd amount doctor acoustic avoid letter advice cage absurd amount doctor acoustic avoid letter advice cage absurd amount doctor acoustic bless'
)
assert s.mnemonic_display_list == words
assert s.has_passphrase and s.passphrase == 'TREZOR'
assert s.seedqr_supported and s.bip85_supported
alias = s.seed_bytes
s.wipe()
assert alias == bytes(64)
assert (
    s.seed_bytes is None
    and s.master_secret is None
    and s.mnemonic_list == []
    and s.passphrase == ''
)
assert (
    ' '.join(words)
    == 'letter advice cage absurd amount doctor acoustic avoid letter advice cage absurd amount doctor acoustic avoid letter advice cage absurd amount doctor acoustic bless'
)
assert bip39.mnemonic_is_valid(
    'letter advice cage absurd amount doctor acoustic avoid letter advice cage absurd amount doctor acoustic avoid letter advice cage absurd amount doctor acoustic bless'
)
del alias, s, words
gc.collect()
words = 'zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo vote'.split()
s = Seed(words, passphrase='TREZOR')
assert (
    s.seed_bytes.hex()
    == 'dd48c104698c30cfe2b6142103248622fb7bb0ff692eebb00089b32d22484e1613912f0a5b694407be899ffd31ed3992c456cdf60f5d4564b8ba3f05a69890ad'
)
assert (
    s.mnemonic_str
    == 'zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo vote'
)
assert s.mnemonic_display_list == words
assert s.has_passphrase and s.passphrase == 'TREZOR'
assert s.seedqr_supported and s.bip85_supported
alias = s.seed_bytes
s.wipe()
assert alias == bytes(64)
assert (
    s.seed_bytes is None
    and s.master_secret is None
    and s.mnemonic_list == []
    and s.passphrase == ''
)
assert (
    ' '.join(words)
    == 'zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo vote'
)
assert bip39.mnemonic_is_valid(
    'zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo vote'
)
del alias, s, words
gc.collect()
words = 'ozone drill grab fiber curtain grace pudding thank cruise elder eight picnic'.split()
s = Seed(words, passphrase='TREZOR')
assert (
    s.seed_bytes.hex()
    == '274ddc525802f7c828d8ef7ddbcdc5304e87ac3535913611fbbfa986d0c9e5476c91689f9c8a54fd55bd38606aa6a8595ad213d4c9c9f9aca3fb217069a41028'
)
assert (
    s.mnemonic_str == 'ozone drill grab fiber curtain grace pudding thank cruise elder eight picnic'
)
assert s.mnemonic_display_list == words
assert s.has_passphrase and s.passphrase == 'TREZOR'
assert s.seedqr_supported and s.bip85_supported
alias = s.seed_bytes
s.wipe()
assert alias == bytes(64)
assert (
    s.seed_bytes is None
    and s.master_secret is None
    and s.mnemonic_list == []
    and s.passphrase == ''
)
assert (
    ' '.join(words)
    == 'ozone drill grab fiber curtain grace pudding thank cruise elder eight picnic'
)
assert bip39.mnemonic_is_valid(
    'ozone drill grab fiber curtain grace pudding thank cruise elder eight picnic'
)
del alias, s, words
gc.collect()
words = 'gravity machine north sort system female filter attitude volume fold club stay feature office ecology stable narrow fog'.split()
s = Seed(words, passphrase='TREZOR')
assert (
    s.seed_bytes.hex()
    == '628c3827a8823298ee685db84f55caa34b5cc195a778e52d45f59bcf75aba68e4d7590e101dc414bc1bbd5737666fbbef35d1f1903953b66624f910feef245ac'
)
assert (
    s.mnemonic_str
    == 'gravity machine north sort system female filter attitude volume fold club stay feature office ecology stable narrow fog'
)
assert s.mnemonic_display_list == words
assert s.has_passphrase and s.passphrase == 'TREZOR'
assert s.seedqr_supported and s.bip85_supported
alias = s.seed_bytes
s.wipe()
assert alias == bytes(64)
assert (
    s.seed_bytes is None
    and s.master_secret is None
    and s.mnemonic_list == []
    and s.passphrase == ''
)
assert (
    ' '.join(words)
    == 'gravity machine north sort system female filter attitude volume fold club stay feature office ecology stable narrow fog'
)
assert bip39.mnemonic_is_valid(
    'gravity machine north sort system female filter attitude volume fold club stay feature office ecology stable narrow fog'
)
del alias, s, words
gc.collect()
words = 'hamster diagram private dutch cause delay private meat slide toddler razor book happy fancy gospel tennis maple dilemma loan word shrug inflict delay length'.split()
s = Seed(words, passphrase='TREZOR')
assert (
    s.seed_bytes.hex()
    == '64c87cde7e12ecf6704ab95bb1408bef047c22db4cc7491c4271d170a1b213d20b385bc1588d9c7b38f1b39d415665b8a9030c9ec653d75e65f847d8fc1fc440'
)
assert (
    s.mnemonic_str
    == 'hamster diagram private dutch cause delay private meat slide toddler razor book happy fancy gospel tennis maple dilemma loan word shrug inflict delay length'
)
assert s.mnemonic_display_list == words
assert s.has_passphrase and s.passphrase == 'TREZOR'
assert s.seedqr_supported and s.bip85_supported
alias = s.seed_bytes
s.wipe()
assert alias == bytes(64)
assert (
    s.seed_bytes is None
    and s.master_secret is None
    and s.mnemonic_list == []
    and s.passphrase == ''
)
assert (
    ' '.join(words)
    == 'hamster diagram private dutch cause delay private meat slide toddler razor book happy fancy gospel tennis maple dilemma loan word shrug inflict delay length'
)
assert bip39.mnemonic_is_valid(
    'hamster diagram private dutch cause delay private meat slide toddler razor book happy fancy gospel tennis maple dilemma loan word shrug inflict delay length'
)
del alias, s, words
gc.collect()
words = 'scheme spot photo card baby mountain device kick cradle pact join borrow'.split()
s = Seed(words, passphrase='TREZOR')
assert (
    s.seed_bytes.hex()
    == 'ea725895aaae8d4c1cf682c1bfd2d358d52ed9f0f0591131b559e2724bb234fca05aa9c02c57407e04ee9dc3b454aa63fbff483a8b11de949624b9f1831a9612'
)
assert s.mnemonic_str == 'scheme spot photo card baby mountain device kick cradle pact join borrow'
assert s.mnemonic_display_list == words
assert s.has_passphrase and s.passphrase == 'TREZOR'
assert s.seedqr_supported and s.bip85_supported
alias = s.seed_bytes
s.wipe()
assert alias == bytes(64)
assert (
    s.seed_bytes is None
    and s.master_secret is None
    and s.mnemonic_list == []
    and s.passphrase == ''
)
assert ' '.join(words) == 'scheme spot photo card baby mountain device kick cradle pact join borrow'
assert bip39.mnemonic_is_valid(
    'scheme spot photo card baby mountain device kick cradle pact join borrow'
)
del alias, s, words
gc.collect()
words = 'horn tenant knee talent sponsor spell gate clip pulse soap slush warm silver nephew swap uncle crack brave'.split()
s = Seed(words, passphrase='TREZOR')
assert (
    s.seed_bytes.hex()
    == 'fd579828af3da1d32544ce4db5c73d53fc8acc4ddb1e3b251a31179cdb71e853c56d2fcb11aed39898ce6c34b10b5382772db8796e52837b54468aeb312cfc3d'
)
assert (
    s.mnemonic_str
    == 'horn tenant knee talent sponsor spell gate clip pulse soap slush warm silver nephew swap uncle crack brave'
)
assert s.mnemonic_display_list == words
assert s.has_passphrase and s.passphrase == 'TREZOR'
assert s.seedqr_supported and s.bip85_supported
alias = s.seed_bytes
s.wipe()
assert alias == bytes(64)
assert (
    s.seed_bytes is None
    and s.master_secret is None
    and s.mnemonic_list == []
    and s.passphrase == ''
)
assert (
    ' '.join(words)
    == 'horn tenant knee talent sponsor spell gate clip pulse soap slush warm silver nephew swap uncle crack brave'
)
assert bip39.mnemonic_is_valid(
    'horn tenant knee talent sponsor spell gate clip pulse soap slush warm silver nephew swap uncle crack brave'
)
del alias, s, words
gc.collect()
words = 'panda eyebrow bullet gorilla call smoke muffin taste mesh discover soft ostrich alcohol speed nation flash devote level hobby quick inner drive ghost inside'.split()
s = Seed(words, passphrase='TREZOR')
assert (
    s.seed_bytes.hex()
    == '72be8e052fc4919d2adf28d5306b5474b0069df35b02303de8c1729c9538dbb6fc2d731d5f832193cd9fb6aeecbc469594a70e3dd50811b5067f3b88b28c3e8d'
)
assert (
    s.mnemonic_str
    == 'panda eyebrow bullet gorilla call smoke muffin taste mesh discover soft ostrich alcohol speed nation flash devote level hobby quick inner drive ghost inside'
)
assert s.mnemonic_display_list == words
assert s.has_passphrase and s.passphrase == 'TREZOR'
assert s.seedqr_supported and s.bip85_supported
alias = s.seed_bytes
s.wipe()
assert alias == bytes(64)
assert (
    s.seed_bytes is None
    and s.master_secret is None
    and s.mnemonic_list == []
    and s.passphrase == ''
)
assert (
    ' '.join(words)
    == 'panda eyebrow bullet gorilla call smoke muffin taste mesh discover soft ostrich alcohol speed nation flash devote level hobby quick inner drive ghost inside'
)
assert bip39.mnemonic_is_valid(
    'panda eyebrow bullet gorilla call smoke muffin taste mesh discover soft ostrich alcohol speed nation flash devote level hobby quick inner drive ghost inside'
)
del alias, s, words
gc.collect()
words = 'cat swing flag economy stadium alone churn speed unique patch report train'.split()
s = Seed(words, passphrase='TREZOR')
assert (
    s.seed_bytes.hex()
    == 'deb5f45449e615feff5640f2e49f933ff51895de3b4381832b3139941c57b59205a42480c52175b6efcffaa58a2503887c1e8b363a707256bdd2b587b46541f5'
)
assert (
    s.mnemonic_str == 'cat swing flag economy stadium alone churn speed unique patch report train'
)
assert s.mnemonic_display_list == words
assert s.has_passphrase and s.passphrase == 'TREZOR'
assert s.seedqr_supported and s.bip85_supported
alias = s.seed_bytes
s.wipe()
assert alias == bytes(64)
assert (
    s.seed_bytes is None
    and s.master_secret is None
    and s.mnemonic_list == []
    and s.passphrase == ''
)
assert (
    ' '.join(words) == 'cat swing flag economy stadium alone churn speed unique patch report train'
)
assert bip39.mnemonic_is_valid(
    'cat swing flag economy stadium alone churn speed unique patch report train'
)
del alias, s, words
gc.collect()
words = 'light rule cinnamon wrap drastic word pride squirrel upgrade then income fatal apart sustain crack supply proud access'.split()
s = Seed(words, passphrase='TREZOR')
assert (
    s.seed_bytes.hex()
    == '4cbdff1ca2db800fd61cae72a57475fdc6bab03e441fd63f96dabd1f183ef5b782925f00105f318309a7e9c3ea6967c7801e46c8a58082674c860a37b93eda02'
)
assert (
    s.mnemonic_str
    == 'light rule cinnamon wrap drastic word pride squirrel upgrade then income fatal apart sustain crack supply proud access'
)
assert s.mnemonic_display_list == words
assert s.has_passphrase and s.passphrase == 'TREZOR'
assert s.seedqr_supported and s.bip85_supported
alias = s.seed_bytes
s.wipe()
assert alias == bytes(64)
assert (
    s.seed_bytes is None
    and s.master_secret is None
    and s.mnemonic_list == []
    and s.passphrase == ''
)
assert (
    ' '.join(words)
    == 'light rule cinnamon wrap drastic word pride squirrel upgrade then income fatal apart sustain crack supply proud access'
)
assert bip39.mnemonic_is_valid(
    'light rule cinnamon wrap drastic word pride squirrel upgrade then income fatal apart sustain crack supply proud access'
)
del alias, s, words
gc.collect()
words = 'all hour make first leader extend hole alien behind guard gospel lava path output census museum junior mass reopen famous sing advance salt reform'.split()
s = Seed(words, passphrase='TREZOR')
assert (
    s.seed_bytes.hex()
    == '26e975ec644423f4a4c4f4215ef09b4bd7ef924e85d1d17c4cf3f136c2863cf6df0a475045652c57eb5fb41513ca2a2d67722b77e954b4b3fc11f7590449191d'
)
assert (
    s.mnemonic_str
    == 'all hour make first leader extend hole alien behind guard gospel lava path output census museum junior mass reopen famous sing advance salt reform'
)
assert s.mnemonic_display_list == words
assert s.has_passphrase and s.passphrase == 'TREZOR'
assert s.seedqr_supported and s.bip85_supported
alias = s.seed_bytes
s.wipe()
assert alias == bytes(64)
assert (
    s.seed_bytes is None
    and s.master_secret is None
    and s.mnemonic_list == []
    and s.passphrase == ''
)
assert (
    ' '.join(words)
    == 'all hour make first leader extend hole alien behind guard gospel lava path output census museum junior mass reopen famous sing advance salt reform'
)
assert bip39.mnemonic_is_valid(
    'all hour make first leader extend hole alien behind guard gospel lava path output census museum junior mass reopen famous sing advance salt reform'
)
del alias, s, words
gc.collect()
words = 'vessel ladder alter error federal sibling chat ability sun glass valve picture'.split()
s = Seed(words, passphrase='TREZOR')
assert (
    s.seed_bytes.hex()
    == '2aaa9242daafcee6aa9d7269f17d4efe271e1b9a529178d7dc139cd18747090bf9d60295d0ce74309a78852a9caadf0af48aae1c6253839624076224374bc63f'
)
assert (
    s.mnemonic_str
    == 'vessel ladder alter error federal sibling chat ability sun glass valve picture'
)
assert s.mnemonic_display_list == words
assert s.has_passphrase and s.passphrase == 'TREZOR'
assert s.seedqr_supported and s.bip85_supported
alias = s.seed_bytes
s.wipe()
assert alias == bytes(64)
assert (
    s.seed_bytes is None
    and s.master_secret is None
    and s.mnemonic_list == []
    and s.passphrase == ''
)
assert (
    ' '.join(words)
    == 'vessel ladder alter error federal sibling chat ability sun glass valve picture'
)
assert bip39.mnemonic_is_valid(
    'vessel ladder alter error federal sibling chat ability sun glass valve picture'
)
del alias, s, words
gc.collect()
words = 'scissors invite lock maple supreme raw rapid void congress muscle digital elegant little brisk hair mango congress clump'.split()
s = Seed(words, passphrase='TREZOR')
assert (
    s.seed_bytes.hex()
    == '7b4a10be9d98e6cba265566db7f136718e1398c71cb581e1b2f464cac1ceedf4f3e274dc270003c670ad8d02c4558b2f8e39edea2775c9e232c7cb798b069e88'
)
assert (
    s.mnemonic_str
    == 'scissors invite lock maple supreme raw rapid void congress muscle digital elegant little brisk hair mango congress clump'
)
assert s.mnemonic_display_list == words
assert s.has_passphrase and s.passphrase == 'TREZOR'
assert s.seedqr_supported and s.bip85_supported
alias = s.seed_bytes
s.wipe()
assert alias == bytes(64)
assert (
    s.seed_bytes is None
    and s.master_secret is None
    and s.mnemonic_list == []
    and s.passphrase == ''
)
assert (
    ' '.join(words)
    == 'scissors invite lock maple supreme raw rapid void congress muscle digital elegant little brisk hair mango congress clump'
)
assert bip39.mnemonic_is_valid(
    'scissors invite lock maple supreme raw rapid void congress muscle digital elegant little brisk hair mango congress clump'
)
del alias, s, words
gc.collect()
words = 'void come effort suffer camp survey warrior heavy shoot primary clutch crush open amazing screen patrol group space point ten exist slush involve unfold'.split()
s = Seed(words, passphrase='TREZOR')
assert (
    s.seed_bytes.hex()
    == '01f5bced59dec48e362f2c45b5de68b9fd6c92c6634f44d6d40aab69056506f0e35524a518034ddc1192e1dacd32c1ed3eaa3c3b131c88ed8e7e54c49a5d0998'
)
assert (
    s.mnemonic_str
    == 'void come effort suffer camp survey warrior heavy shoot primary clutch crush open amazing screen patrol group space point ten exist slush involve unfold'
)
assert s.mnemonic_display_list == words
assert s.has_passphrase and s.passphrase == 'TREZOR'
assert s.seedqr_supported and s.bip85_supported
alias = s.seed_bytes
s.wipe()
assert alias == bytes(64)
assert (
    s.seed_bytes is None
    and s.master_secret is None
    and s.mnemonic_list == []
    and s.passphrase == ''
)
assert (
    ' '.join(words)
    == 'void come effort suffer camp survey warrior heavy shoot primary clutch crush open amazing screen patrol group space point ten exist slush involve unfold'
)
assert bip39.mnemonic_is_valid(
    'void come effort suffer camp survey warrior heavy shoot primary clutch crush open amazing screen patrol group space point ten exist slush involve unfold'
)
del alias, s, words
gc.collect()
s = Seed(
    'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about'.split(),
    passphrase='',
)
assert s.passphrase == ''
assert (
    s.seed_bytes.hex()
    == '5eb00bbddcf069084889a8ab9155568165f5c453ccb85e70811aaed6f6da5fc19a5ac40b389cd370d086206dec8aa6c43daea6690f20ad3d8d48b2d2ce9e38e4'
)
s.wipe()
del s
gc.collect()
s = Seed(
    'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about'.split(),
    passphrase='é',
)
assert s.passphrase == 'é'
assert (
    s.seed_bytes.hex()
    == 'f37f8652bf7004d4bd4ba7702e70e647f54965758656423dde58d64fa725c1e8be1b0416864e10f714c0730e46f9676079b4fd4f72fcf0c09a120ae65589c091'
)
s.wipe()
del s
gc.collect()
s = Seed(
    'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about'.split(),
    passphrase='é',
)
assert s.passphrase == 'é'
assert (
    s.seed_bytes.hex()
    == 'f37f8652bf7004d4bd4ba7702e70e647f54965758656423dde58d64fa725c1e8be1b0416864e10f714c0730e46f9676079b4fd4f72fcf0c09a120ae65589c091'
)
s.wipe()
del s
gc.collect()
s = Seed(
    'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about'.split(),
    passphrase='㍍ガバヴァぱばぐゞちぢ十人十色',
)
assert s.passphrase == 'メートルガバヴァぱばぐゞちぢ十人十色'
assert (
    s.seed_bytes.hex()
    == 'ba553eedefe76e67e2602dc20184c564010859faada929a090dd2c57aacb204ceefd15404ab50ef3e8dbeae5195aeae64b0def4d2eead1cdc728a33ced520ffd'
)
s.wipe()
del s
gc.collect()
s = Seed(
    'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about'.split(),
    passphrase='\x00',
)
assert s.passphrase == '\x00'
assert (
    s.seed_bytes.hex()
    == '4ca62e6b646a1d3548e08b314e11b9215b35a4cbbbdc12c0a482b44aa013cd3f68a8f6a33f561e34dc03a7367110de228e59d3e3700bff1ea561818134fe59eb'
)
s.wipe()
del s
gc.collect()
s = Seed(
    'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about'.split(),
    passphrase='\\u0061',
)
assert s.passphrase == 'a'
assert (
    s.seed_bytes.hex()
    == '87d1b98527bc044ca079026f96de0f4f500311598024b524391919116845af4e664e5cac53ad710e1509955c90b5fe94bb66b6df3fce0634a63fe13b9179f6d3'
)
s.wipe()
del s
gc.collect()
s = Seed(
    'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about'.split(),
    passphrase='\\\\u0061',
)
assert s.passphrase == '\\a'
assert (
    s.seed_bytes.hex()
    == 'c11cb8a82405a3ed8a1e7d1437f7d958aca102f51e23685979620dea077a0b61440bd1858ee498895fcadce282e410d8fd835b0dfa36e1b60094f4170183411a'
)
s.wipe()
del s
gc.collect()
s = Seed(
    'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about'.split(),
    passphrase='\\u005cu0061',
)
assert s.passphrase == '\\u0061'
assert (
    s.seed_bytes.hex()
    == '1b579213681dcc7f62313293fd0d6cdaaa1c74dc4b633c801a3c26885748cabdfdbb718c95af743eb0e6fcee2c9b920a50552833b84c485762478db6fe5e5926'
)
s.wipe()
del s
gc.collect()
s = Seed(
    'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about'.split(),
    passphrase='\\uD800\\uZ',
)
assert s.passphrase == '\\uD800\\uZ'
assert (
    s.seed_bytes.hex()
    == '70b80f74314d166a9a15a5918644e84188a4dadd9b6aab1408b770db6875d4317ad68270fbcb36c1c6ac8bd17ed898b8500f14a9ce06be2476cac9595ebd6e7d'
)
s.wipe()
del s
gc.collect()
s = Seed(
    'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about'.split(),
    passphrase='\\u',
)
assert s.passphrase == '\\u'
assert (
    s.seed_bytes.hex()
    == '4cc32b6368922c251f30bae32d9d85db48f30902d3f236862f30e8bbec2bcd221b844675815d3ad53a3d4bd35641e65a3ee9213adf41974460cb8677ee0ec458'
)
s.wipe()
del s
gc.collect()
s = Seed(
    'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about'.split(),
    passphrase='\\u123',
)
assert s.passphrase == '\\u123'
assert (
    s.seed_bytes.hex()
    == 'a146b0f03f8657276a1cc697af1cd955facb769c8437a55da39711680433a9ef9787d4d7810873d083d53d23080a2cb993944f990b9db41b7c7a3df52586dd4c'
)
s.wipe()
del s
gc.collect()
s = Seed(
    'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about'.split(),
    passphrase='\\U0001f600',
)
assert s.passphrase == '\\U0001f600'
assert (
    s.seed_bytes.hex()
    == 'ae662eeded4fffcf2e50101dc4ccc4ae500b01c3acc95e3c22fb3735d79510753e190dd3c20519d39304d5b7da1a9234d8c8eed85332f2305a0df43220e26444'
)
s.wipe()
del s
gc.collect()
s = Seed(
    'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about'.split(),
    passphrase='\\n',
)
assert s.passphrase == '\\n'
assert (
    s.seed_bytes.hex()
    == 'ebdad9515ba1b64e916813594e5aff4e51d4aa7782f372227154627c4906c6bbfc64d9a9a79a70f452315458192a8e45495f5e40b60a65ba7ccc8ccee413b29d'
)
s.wipe()
del s
gc.collect()
s = Seed(
    'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about'.split(),
    passphrase='abc\\',
)
assert s.passphrase == 'abc\\'
assert (
    s.seed_bytes.hex()
    == '093dcfdb3bb65cf2b698c980ccd094ec6d83147a0525385b343dc1aa8226bd87d38720b64965dda91723c423a81ede1158563013f19981ff36d918484fe95f4d'
)
s.wipe()
del s
gc.collect()
s = Seed(
    'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about'.split(),
    passphrase='\\x41',
)
assert s.passphrase == '\\x41'
assert (
    s.seed_bytes.hex()
    == '1e27d45e9e129b8deeefa2854de4be438f35570874bacbbf8a812d5d923bff281f60b0397b5508d343faf121cabcfed5cb0d89e41fb96ee98e214279f1ef5cf2'
)
s.wipe()
del s
gc.collect()
s = Seed(
    'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about'.split(),
    passphrase='\x00\x00\\uZ\\uDFFF\\uDFFFガ\\u0061\\uD800é\\uD800\x00ﷺ\\u123\\',
)
assert (
    s.passphrase
    == '\x00\x00\\uZ\\uDFFF\\uDFFFガ\\u0061\\uD800é\\uD800\x00صلى الله عليه وسلم\\u123\\'
)
assert (
    s.seed_bytes.hex()
    == '4e858ba34bc118dd02b52861d1f906d152fe14051d51d7d4caab1fc44d1dc9e0cf0e4cb86887de3fe3d965786fdff0289605cd011372be30f0a4a84a25c03214'
)
s.wipe()
del s
gc.collect()
s = Seed(
    'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about'.split(),
    passphrase='\\u00e9\\x20\\u0061ガ\\u123\\u00e9\\u0061\x00\\uZ',
)
assert s.passphrase == '\\u00e9\\x20\\u0061ガ\\u123\\u00e9\\u0061\x00\\uZ'
assert (
    s.seed_bytes.hex()
    == 'dc3f3e1717d01d96bc61056ace01aaf2657fbbb5a3bdcabd93e2cbb2ccf7875a9c09f7f4605e271667285a6f02da335662cefb98d93ba73fe675b197e18a1003'
)
s.wipe()
del s
gc.collect()
s = Seed(
    'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about'.split(),
    passphrase='\\uD800ﷺﷺ\\u0061\\x20ﷺ\\ガ\\uDFFFガé\\uZ\\uD800',
)
assert (
    s.passphrase
    == '\\uD800صلى الله عليه وسلمصلى الله عليه وسلم\\u0061\\x20صلى الله عليه وسلم\\ガ\\uDFFFガé\\uZ\\uD800'
)
assert (
    s.seed_bytes.hex()
    == 'bfcad7050a1f83f46f047dec9166ae2631251f591d3a977afa468e457059094938c45bf636c3772ac8f19a17e20633b8ba99a9f1368476e6da2fa6d105d44e54'
)
s.wipe()
del s
gc.collect()
s = Seed(
    'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about'.split(),
    passphrase='\\uZéé\\u00e9a\\\x00\\u00e9ガ',
)
assert s.passphrase == '\\uZéé\\u00e9a\\\x00\\u00e9ガ'
assert (
    s.seed_bytes.hex()
    == '0612fa7608749a9d5e3f53636bd609287d188e0f05e64441b8d4be990bc8e67d3f9f2aa4700d865526a58e98822ff5685f541f67ad2948474d212e8ba1b237fa'
)
s.wipe()
del s
gc.collect()
s = Seed(
    'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about'.split(),
    passphrase='\\uZ\\uZガUua\\u123é\\',
)
assert s.passphrase == '\\uZ\\uZガUua\\u123é\\'
assert (
    s.seed_bytes.hex()
    == 'ca1f878b188d86fb514c412350aedf1424148c9e508e3e9cd24874b99f798337e381b410f072fd4ae3f4e9cb144efe9ea8445742e03acc95e938a0d444402773'
)
s.wipe()
del s
gc.collect()
s = Seed(
    'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about'.split(),
    passphrase='\\x20\\u0061u\\u0061\\uZu\\ﷺ',
)
assert s.passphrase == '\\x20\\u0061u\\u0061\\uZu\\صلى الله عليه وسلم'
assert (
    s.seed_bytes.hex()
    == 'f1ce39adceeb5cde671379434f471425cea295a0561697f7127aa3f9c476ff27ad1c13a6e0783c8d54e7ea2fc76ae8aeffacc57743e9cc1f063d14fe4ea2e793'
)
s.wipe()
del s
gc.collect()
s = Seed(
    'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about'.split(),
    passphrase='\\u123ﷺ\\u123U😀\\uD800é\\u123',
)
assert s.passphrase == '\\u123صلى الله عليه وسلم\\u123U😀\\uD800é\\u123'
assert (
    s.seed_bytes.hex()
    == 'd81c1fd03caa87c48dea89a358129751b720a9c05daa1bbcc8bfbb5875b6d079816f3a4e86087735ee82e72c0365dbc29ca4bfc16d54f0f068c0e2d20339bc69'
)
s.wipe()
del s
gc.collect()
s = Seed(
    'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about'.split(),
    passphrase='u\\u123a\\uZ\\u123\\u00e9',
)
assert s.passphrase == 'u\\u123a\\uZ\\u123\\u00e9'
assert (
    s.seed_bytes.hex()
    == 'e3fab485c6fd4eaecae7a27465120d4aa6f14dce4338c0cc67bcbebd488b39fc281e45d0dc17b7c7f4421b0df4dcfd552088412d589d48ef2a04a22afb1e8ed6'
)
s.wipe()
del s
gc.collect()
s = Seed(
    'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about'.split(),
    passphrase='\\u00e9\\u00e9\x00\\u00e9\\uZ\\uDFFF\\\x00aa\\uZ\\uD800\\u123',
)
assert s.passphrase == '\\u00e9\\u00e9\x00\\u00e9\\uZ\\uDFFF\\\x00aa\\uZ\\uD800\\u123'
assert (
    s.seed_bytes.hex()
    == '6c4cae9212d860d4d6b5d5e65a805149876439e722107ae2280734f0a58971a3fb4857c99fb1d34a23d71d112e8b6dfe8ed839cd5f6b0e523a719b1b25ed43f9'
)
s.wipe()
del s
gc.collect()
s = Seed(
    'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about'.split(),
    passphrase='\\uZ',
)
assert s.passphrase == '\\uZ'
assert (
    s.seed_bytes.hex()
    == '7cdef1920fa6b1dd5b53b0d45a2be03fe58ed90d79de3dd0f9ba0c80712077fe6c6aadfdcd495992bfe0f344ed53a7ae8e1a960c450c12519f879641177833a3'
)
s.wipe()
del s
gc.collect()
s = Seed(
    'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about'.split(),
    passphrase='😀u\\u00e9ué',
)
assert s.passphrase == '😀uéué'
assert (
    s.seed_bytes.hex()
    == '5387dda91805443e73073be31186d61a1ffbf79a7df710923af720d7f2ed284ecd5ddd7ebeeb2602b0d34ee590603b6731d813476efaeda04da928ccf8a24697'
)
s.wipe()
del s
gc.collect()
s = Seed(
    'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about'.split(),
    passphrase='é😀\\uZ\\u123\\uZ\x00\x00é\\u00e9\\u123ﷺガ\x00\\u00e9',
)
assert s.passphrase == 'é😀\\uZ\\u123\\uZ\x00\x00é\\u00e9\\u123صلى الله عليه وسلمガ\x00\\u00e9'
assert (
    s.seed_bytes.hex()
    == 'fb65b6658198f45228f4a6753c2bba7f3080cdafbb0a27726a73261072a81309bfe3cc9064b21b6fde58a776ee7b145b42b8e3d0e1d6665e40212e02a3ea622d'
)
s.wipe()
del s
gc.collect()
s = Seed(
    'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about'.split(),
    passphrase='ﷺ\\',
)
assert s.passphrase == 'صلى الله عليه وسلم\\'
assert (
    s.seed_bytes.hex()
    == '48012bf0d0cc7acef12db028a6699af293d4032cee8139f012a67a91530edf9f16b1eb38d9e95f6e8eb7affb88c7ed9d54ea337261459bce681e92618c8e1d8b'
)
s.wipe()
del s
gc.collect()
s = Seed(
    'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about'.split(),
    passphrase='\\u123\\\\uZ\\uZ',
)
assert s.passphrase == '\\u123\\\\uZ\\uZ'
assert (
    s.seed_bytes.hex()
    == '51750a69ded6ea054cc29d274ae06a4d4fd40505fd81f0146506fbc60bf9e7276d916960b913fe54033e94210afe4ee9e10538a679527595e2102bd3b88d8957'
)
s.wipe()
del s
gc.collect()
s = Seed(
    'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about'.split(),
    passphrase='\\u00e9\x00U\\ﷺ',
)
assert s.passphrase == 'é\x00U\\صلى الله عليه وسلم'
assert (
    s.seed_bytes.hex()
    == '4882d7b35e0210dbf17626b850980c9ca22f91f013422e143c5cddfef4783ac93f14d6041d1c811b503737111e0f1aa04971e26847c0ae40ffc24e15356fcc4c'
)
s.wipe()
del s
gc.collect()
s = Seed(
    'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about'.split(),
    passphrase='\\a😀\\uZ\\x20Uガé',
)
assert s.passphrase == '\\a😀\\uZ\\x20Uガé'
assert (
    s.seed_bytes.hex()
    == '94410e43720ca23cea79a1cb15f3499073b341f28d90cc7ab6deed745392675bd27883556cac8b05129250bda92c8e4e1ae7317aea441050b13a9efaee322b85'
)
s.wipe()
del s
gc.collect()
s = Seed(
    'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about'.split(),
    passphrase='\x00\\u123ﷺガ\\u0061\\u00e9\\uZa\\uDFFF\\UU',
)
assert s.passphrase == '\x00\\u123صلى الله عليه وسلمガ\\u0061\\u00e9\\uZa\\uDFFF\\UU'
assert (
    s.seed_bytes.hex()
    == 'e0f9b756100c4c4ccdb35eefb2bc37ebaf5985ca4ad99baf6fbe10361c64ef0cafca9f4c8d9b579611dea8b5c02e5067f5b40c65b776372afd8a517a071bcb4b'
)
s.wipe()
del s
gc.collect()
words = 'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about'.split()
a = Seed(words)
b = Seed([word.upper() for word in words])
assert a == b
a.set_passphrase('\u0061')
assert a.passphrase == 'a' and not a == b
a.set_passphrase('', regenerate_seed=False)
assert a.passphrase == '' and not a == b
a.set_passphrase('')
assert a == b
assert a.get_root().is_private
assert (
    a.get_fingerprint() == '73c5da0a'
)  # Public abandon/about, empty passphrase; CPython embit reference
assert a == b
for invalid in (['abandon'] * 12, ['notaword'] * 12):
    try:
        Seed(invalid)
        assert False
    except InvalidSeedException:
        pass
try:
    Seed([])
    assert False
except Exception:
    pass
a.wipe()
b.wipe()
assert len(bip39.WORDLIST) == 2048 and bip39.mnemonic_is_valid('abandon ' * 11 + 'about')
for i in range(3):
    gc.collect()
assert camera.settings()['rust_heap_bytes'] == baseline
print('@@PASS original-seed-public-vectors-passphrase-wipe', 24, 32)
