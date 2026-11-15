# Generated PUBLIC vectors only; no private wallet data.
import secp256k1 as c
from embit import bip32,bip39,ec
from seedsigner_port.seed import Seed
from seedsigner_port.decode_platform import FeatureUnavailable
import binascii
import camera
import gc
import time
baseline=camera.settings()['rust_heap_bytes']
start=time.ticks_ms()
c.context_randomize(bytes(range(32)))
assert c.context_status()['randomized']
root=bip32.HDKey.from_seed(binascii.unhexlify('000102030405060708090a0b0c0d0e0f'))
key=root.derive('m')
assert key.to_base58()=='xprv9s21ZrQH143K3QTDL4LXw2F7HEK3wJUD2nW2nRk4stbPy6cq3jPPqjiChkVvvNKmPGJxWUtg6LnF5kejMRNNU3TGtRBeJgk33yuGBxrMPHi'
assert key.to_public().to_base58()=='xpub661MyMwAqRbcFtXgS5sYJABqqG9YLmC4Q1Rdap9gSE8NqtwybGhePY2gZ29ESFjqJoCu1Rupje8YtGqsefD265TMg7usUDFdp6W1EGMcet8'
assert bip32.HDKey.from_string('xprv9s21ZrQH143K3QTDL4LXw2F7HEK3wJUD2nW2nRk4stbPy6cq3jPPqjiChkVvvNKmPGJxWUtg6LnF5kejMRNNU3TGtRBeJgk33yuGBxrMPHi').serialize()==key.serialize()
assert bip32.HDKey.from_string('xpub661MyMwAqRbcFtXgS5sYJABqqG9YLmC4Q1Rdap9gSE8NqtwybGhePY2gZ29ESFjqJoCu1Rupje8YtGqsefD265TMg7usUDFdp6W1EGMcet8').serialize()==key.to_public().serialize()
gc.collect()
root=bip32.HDKey.from_seed(binascii.unhexlify('000102030405060708090a0b0c0d0e0f'))
key=root.derive("m/0'")
assert key.to_base58()=='xprv9uHRZZhk6KAJC1avXpDAp4MDc3sQKNxDiPvvkX8Br5ngLNv1TxvUxt4cV1rGL5hj6KCesnDYUhd7oWgT11eZG7XnxHrnYeSvkzY7d2bhkJ7'
assert key.to_public().to_base58()=='xpub68Gmy5EdvgibQVfPdqkBBCHxA5htiqg55crXYuXoQRKfDBFA1WEjWgP6LHhwBZeNK1VTsfTFUHCdrfp1bgwQ9xv5ski8PX9rL2dZXvgGDnw'
assert bip32.HDKey.from_string('xprv9uHRZZhk6KAJC1avXpDAp4MDc3sQKNxDiPvvkX8Br5ngLNv1TxvUxt4cV1rGL5hj6KCesnDYUhd7oWgT11eZG7XnxHrnYeSvkzY7d2bhkJ7').serialize()==key.serialize()
assert bip32.HDKey.from_string('xpub68Gmy5EdvgibQVfPdqkBBCHxA5htiqg55crXYuXoQRKfDBFA1WEjWgP6LHhwBZeNK1VTsfTFUHCdrfp1bgwQ9xv5ski8PX9rL2dZXvgGDnw').serialize()==key.to_public().serialize()
gc.collect()
root=bip32.HDKey.from_seed(binascii.unhexlify('000102030405060708090a0b0c0d0e0f'))
key=root.derive("m/0'/1")
assert key.to_base58()=='xprv9wTYmMFdV23N2TdNG573QoEsfRrWKQgWeibmLntzniatZvR9BmLnvSxqu53Kw1UmYPxLgboyZQaXwTCg8MSY3H2EU4pWcQDnRnrVA1xe8fs'
assert key.to_public().to_base58()=='xpub6ASuArnXKPbfEwhqN6e3mwBcDTgzisQN1wXN9BJcM47sSikHjJf3UFHKkNAWbWMiGj7Wf5uMash7SyYq527Hqck2AxYysAA7xmALppuCkwQ'
assert bip32.HDKey.from_string('xprv9wTYmMFdV23N2TdNG573QoEsfRrWKQgWeibmLntzniatZvR9BmLnvSxqu53Kw1UmYPxLgboyZQaXwTCg8MSY3H2EU4pWcQDnRnrVA1xe8fs').serialize()==key.serialize()
assert bip32.HDKey.from_string('xpub6ASuArnXKPbfEwhqN6e3mwBcDTgzisQN1wXN9BJcM47sSikHjJf3UFHKkNAWbWMiGj7Wf5uMash7SyYq527Hqck2AxYysAA7xmALppuCkwQ').serialize()==key.to_public().serialize()
assert root.derive("m/0'").to_public().child(1).to_base58()=='xpub6ASuArnXKPbfEwhqN6e3mwBcDTgzisQN1wXN9BJcM47sSikHjJf3UFHKkNAWbWMiGj7Wf5uMash7SyYq527Hqck2AxYysAA7xmALppuCkwQ'
gc.collect()
root=bip32.HDKey.from_seed(binascii.unhexlify('000102030405060708090a0b0c0d0e0f'))
key=root.derive("m/0'/1/2'")
assert key.to_base58()=='xprv9z4pot5VBttmtdRTWfWQmoH1taj2axGVzFqSb8C9xaxKymcFzXBDptWmT7FwuEzG3ryjH4ktypQSAewRiNMjANTtpgP4mLTj34bhnZX7UiM'
assert key.to_public().to_base58()=='xpub6D4BDPcP2GT577Vvch3R8wDkScZWzQzMMUm3PWbmWvVJrZwQY4VUNgqFJPMM3No2dFDFGTsxxpG5uJh7n7epu4trkrX7x7DogT5Uv6fcLW5'
assert bip32.HDKey.from_string('xprv9z4pot5VBttmtdRTWfWQmoH1taj2axGVzFqSb8C9xaxKymcFzXBDptWmT7FwuEzG3ryjH4ktypQSAewRiNMjANTtpgP4mLTj34bhnZX7UiM').serialize()==key.serialize()
assert bip32.HDKey.from_string('xpub6D4BDPcP2GT577Vvch3R8wDkScZWzQzMMUm3PWbmWvVJrZwQY4VUNgqFJPMM3No2dFDFGTsxxpG5uJh7n7epu4trkrX7x7DogT5Uv6fcLW5').serialize()==key.to_public().serialize()
gc.collect()
root=bip32.HDKey.from_seed(binascii.unhexlify('000102030405060708090a0b0c0d0e0f'))
key=root.derive("m/0'/1/2'/2")
assert key.to_base58()=='xprvA2JDeKCSNNZky6uBCviVfJSKyQ1mDYahRjijr5idH2WwLsEd4Hsb2Tyh8RfQMuPh7f7RtyzTtdrbdqqsunu5Mm3wDvUAKRHSC34sJ7in334'
assert key.to_public().to_base58()=='xpub6FHa3pjLCk84BayeJxFW2SP4XRrFd1JYnxeLeU8EqN3vDfZmbqBqaGJAyiLjTAwm6ZLRQUMv1ZACTj37sR62cfN7fe5JnJ7dh8zL4fiyLHV'
assert bip32.HDKey.from_string('xprvA2JDeKCSNNZky6uBCviVfJSKyQ1mDYahRjijr5idH2WwLsEd4Hsb2Tyh8RfQMuPh7f7RtyzTtdrbdqqsunu5Mm3wDvUAKRHSC34sJ7in334').serialize()==key.serialize()
assert bip32.HDKey.from_string('xpub6FHa3pjLCk84BayeJxFW2SP4XRrFd1JYnxeLeU8EqN3vDfZmbqBqaGJAyiLjTAwm6ZLRQUMv1ZACTj37sR62cfN7fe5JnJ7dh8zL4fiyLHV').serialize()==key.to_public().serialize()
assert root.derive("m/0'/1/2'").to_public().child(2).to_base58()=='xpub6FHa3pjLCk84BayeJxFW2SP4XRrFd1JYnxeLeU8EqN3vDfZmbqBqaGJAyiLjTAwm6ZLRQUMv1ZACTj37sR62cfN7fe5JnJ7dh8zL4fiyLHV'
gc.collect()
root=bip32.HDKey.from_seed(binascii.unhexlify('000102030405060708090a0b0c0d0e0f'))
key=root.derive("m/0'/1/2'/2/1000000000")
assert key.to_base58()=='xprvA41z7zogVVwxVSgdKUHDy1SKmdb533PjDz7J6N6mV6uS3ze1ai8FHa8kmHScGpWmj4WggLyQjgPie1rFSruoUihUZREPSL39UNdE3BBDu76'
assert key.to_public().to_base58()=='xpub6H1LXWLaKsWFhvm6RVpEL9P4KfRZSW7abD2ttkWP3SSQvnyA8FSVqNTEcYFgJS2UaFcxupHiYkro49S8yGasTvXEYBVPamhGW6cFJodrTHy'
assert bip32.HDKey.from_string('xprvA41z7zogVVwxVSgdKUHDy1SKmdb533PjDz7J6N6mV6uS3ze1ai8FHa8kmHScGpWmj4WggLyQjgPie1rFSruoUihUZREPSL39UNdE3BBDu76').serialize()==key.serialize()
assert bip32.HDKey.from_string('xpub6H1LXWLaKsWFhvm6RVpEL9P4KfRZSW7abD2ttkWP3SSQvnyA8FSVqNTEcYFgJS2UaFcxupHiYkro49S8yGasTvXEYBVPamhGW6cFJodrTHy').serialize()==key.to_public().serialize()
assert root.derive("m/0'/1/2'/2").to_public().child(1000000000).to_base58()=='xpub6H1LXWLaKsWFhvm6RVpEL9P4KfRZSW7abD2ttkWP3SSQvnyA8FSVqNTEcYFgJS2UaFcxupHiYkro49S8yGasTvXEYBVPamhGW6cFJodrTHy'
gc.collect()
root=bip32.HDKey.from_seed(binascii.unhexlify('fffcf9f6f3f0edeae7e4e1dedbd8d5d2cfccc9c6c3c0bdbab7b4b1aeaba8a5a29f9c999693908d8a8784817e7b7875726f6c696663605d5a5754514e4b484542'))
key=root.derive('m')
assert key.to_base58()=='xprv9s21ZrQH143K31xYSDQpPDxsXRTUcvj2iNHm5NUtrGiGG5e2DtALGdso3pGz6ssrdK4PFmM8NSpSBHNqPqm55Qn3LqFtT2emdEXVYsCzC2U'
assert key.to_public().to_base58()=='xpub661MyMwAqRbcFW31YEwpkMuc5THy2PSt5bDMsktWQcFF8syAmRUapSCGu8ED9W6oDMSgv6Zz8idoc4a6mr8BDzTJY47LJhkJ8UB7WEGuduB'
assert bip32.HDKey.from_string('xprv9s21ZrQH143K31xYSDQpPDxsXRTUcvj2iNHm5NUtrGiGG5e2DtALGdso3pGz6ssrdK4PFmM8NSpSBHNqPqm55Qn3LqFtT2emdEXVYsCzC2U').serialize()==key.serialize()
assert bip32.HDKey.from_string('xpub661MyMwAqRbcFW31YEwpkMuc5THy2PSt5bDMsktWQcFF8syAmRUapSCGu8ED9W6oDMSgv6Zz8idoc4a6mr8BDzTJY47LJhkJ8UB7WEGuduB').serialize()==key.to_public().serialize()
gc.collect()
root=bip32.HDKey.from_seed(binascii.unhexlify('fffcf9f6f3f0edeae7e4e1dedbd8d5d2cfccc9c6c3c0bdbab7b4b1aeaba8a5a29f9c999693908d8a8784817e7b7875726f6c696663605d5a5754514e4b484542'))
key=root.derive('m/0')
assert key.to_base58()=='xprv9vHkqa6EV4sPZHYqZznhT2NPtPCjKuDKGY38FBWLvgaDx45zo9WQRUT3dKYnjwih2yJD9mkrocEZXo1ex8G81dwSM1fwqWpWkeS3v86pgKt'
assert key.to_public().to_base58()=='xpub69H7F5d8KSRgmmdJg2KhpAK8SR3DjMwAdkxj3ZuxV27CprR9LgpeyGmXUbC6wb7ERfvrnKZjXoUmmDznezpbZb7ap6r1D3tgFxHmwMkQTPH'
assert bip32.HDKey.from_string('xprv9vHkqa6EV4sPZHYqZznhT2NPtPCjKuDKGY38FBWLvgaDx45zo9WQRUT3dKYnjwih2yJD9mkrocEZXo1ex8G81dwSM1fwqWpWkeS3v86pgKt').serialize()==key.serialize()
assert bip32.HDKey.from_string('xpub69H7F5d8KSRgmmdJg2KhpAK8SR3DjMwAdkxj3ZuxV27CprR9LgpeyGmXUbC6wb7ERfvrnKZjXoUmmDznezpbZb7ap6r1D3tgFxHmwMkQTPH').serialize()==key.to_public().serialize()
assert root.derive('m').to_public().child(0).to_base58()=='xpub69H7F5d8KSRgmmdJg2KhpAK8SR3DjMwAdkxj3ZuxV27CprR9LgpeyGmXUbC6wb7ERfvrnKZjXoUmmDznezpbZb7ap6r1D3tgFxHmwMkQTPH'
gc.collect()
root=bip32.HDKey.from_seed(binascii.unhexlify('fffcf9f6f3f0edeae7e4e1dedbd8d5d2cfccc9c6c3c0bdbab7b4b1aeaba8a5a29f9c999693908d8a8784817e7b7875726f6c696663605d5a5754514e4b484542'))
key=root.derive("m/0/2147483647'")
assert key.to_base58()=='xprv9wSp6B7kry3Vj9m1zSnLvN3xH8RdsPP1Mh7fAaR7aRLcQMKTR2vidYEeEg2mUCTAwCd6vnxVrcjfy2kRgVsFawNzmjuHc2YmYRmagcEPdU9'
assert key.to_public().to_base58()=='xpub6ASAVgeehLbnwdqV6UKMHVzgqAG8Gr6riv3Fxxpj8ksbH9ebxaEyBLZ85ySDhKiLDBrQSARLq1uNRts8RuJiHjaDMBU4Zn9h8LZNnBC5y4a'
assert bip32.HDKey.from_string('xprv9wSp6B7kry3Vj9m1zSnLvN3xH8RdsPP1Mh7fAaR7aRLcQMKTR2vidYEeEg2mUCTAwCd6vnxVrcjfy2kRgVsFawNzmjuHc2YmYRmagcEPdU9').serialize()==key.serialize()
assert bip32.HDKey.from_string('xpub6ASAVgeehLbnwdqV6UKMHVzgqAG8Gr6riv3Fxxpj8ksbH9ebxaEyBLZ85ySDhKiLDBrQSARLq1uNRts8RuJiHjaDMBU4Zn9h8LZNnBC5y4a').serialize()==key.to_public().serialize()
gc.collect()
root=bip32.HDKey.from_seed(binascii.unhexlify('fffcf9f6f3f0edeae7e4e1dedbd8d5d2cfccc9c6c3c0bdbab7b4b1aeaba8a5a29f9c999693908d8a8784817e7b7875726f6c696663605d5a5754514e4b484542'))
key=root.derive("m/0/2147483647'/1")
assert key.to_base58()=='xprv9zFnWC6h2cLgpmSA46vutJzBcfJ8yaJGg8cX1e5StJh45BBciYTRXSd25UEPVuesF9yog62tGAQtHjXajPPdbRCHuWS6T8XA2ECKADdw4Ef'
assert key.to_public().to_base58()=='xpub6DF8uhdarytz3FWdA8TvFSvvAh8dP3283MY7p2V4SeE2wyWmG5mg5EwVvmdMVCQcoNJxGoWaU9DCWh89LojfZ537wTfunKau47EL2dhHKon'
assert bip32.HDKey.from_string('xprv9zFnWC6h2cLgpmSA46vutJzBcfJ8yaJGg8cX1e5StJh45BBciYTRXSd25UEPVuesF9yog62tGAQtHjXajPPdbRCHuWS6T8XA2ECKADdw4Ef').serialize()==key.serialize()
assert bip32.HDKey.from_string('xpub6DF8uhdarytz3FWdA8TvFSvvAh8dP3283MY7p2V4SeE2wyWmG5mg5EwVvmdMVCQcoNJxGoWaU9DCWh89LojfZ537wTfunKau47EL2dhHKon').serialize()==key.to_public().serialize()
assert root.derive("m/0/2147483647'").to_public().child(1).to_base58()=='xpub6DF8uhdarytz3FWdA8TvFSvvAh8dP3283MY7p2V4SeE2wyWmG5mg5EwVvmdMVCQcoNJxGoWaU9DCWh89LojfZ537wTfunKau47EL2dhHKon'
gc.collect()
root=bip32.HDKey.from_seed(binascii.unhexlify('fffcf9f6f3f0edeae7e4e1dedbd8d5d2cfccc9c6c3c0bdbab7b4b1aeaba8a5a29f9c999693908d8a8784817e7b7875726f6c696663605d5a5754514e4b484542'))
key=root.derive("m/0/2147483647'/1/2147483646'")
assert key.to_base58()=='xprvA1RpRA33e1JQ7ifknakTFpgNXPmW2YvmhqLQYMmrj4xJXXWYpDPS3xz7iAxn8L39njGVyuoseXzU6rcxFLJ8HFsTjSyQbLYnMpCqE2VbFWc'
assert key.to_public().to_base58()=='xpub6ERApfZwUNrhLCkDtcHTcxd75RbzS1ed54G1LkBUHQVHQKqhMkhgbmJbZRkrgZw4koxb5JaHWkY4ALHY2grBGRjaDMzQLcgJvLJuZZvRcEL'
assert bip32.HDKey.from_string('xprvA1RpRA33e1JQ7ifknakTFpgNXPmW2YvmhqLQYMmrj4xJXXWYpDPS3xz7iAxn8L39njGVyuoseXzU6rcxFLJ8HFsTjSyQbLYnMpCqE2VbFWc').serialize()==key.serialize()
assert bip32.HDKey.from_string('xpub6ERApfZwUNrhLCkDtcHTcxd75RbzS1ed54G1LkBUHQVHQKqhMkhgbmJbZRkrgZw4koxb5JaHWkY4ALHY2grBGRjaDMzQLcgJvLJuZZvRcEL').serialize()==key.to_public().serialize()
gc.collect()
root=bip32.HDKey.from_seed(binascii.unhexlify('fffcf9f6f3f0edeae7e4e1dedbd8d5d2cfccc9c6c3c0bdbab7b4b1aeaba8a5a29f9c999693908d8a8784817e7b7875726f6c696663605d5a5754514e4b484542'))
key=root.derive("m/0/2147483647'/1/2147483646'/2")
assert key.to_base58()=='xprvA2nrNbFZABcdryreWet9Ea4LvTJcGsqrMzxHx98MMrotbir7yrKCEXw7nadnHM8Dq38EGfSh6dqA9QWTyefMLEcBYJUuekgW4BYPJcr9E7j'
assert key.to_public().to_base58()=='xpub6FnCn6nSzZAw5Tw7cgR9bi15UV96gLZhjDstkXXxvCLsUXBGXPdSnLFbdpq8p9HmGsApME5hQTZ3emM2rnY5agb9rXpVGyy3bdW6EEgAtqt'
assert bip32.HDKey.from_string('xprvA2nrNbFZABcdryreWet9Ea4LvTJcGsqrMzxHx98MMrotbir7yrKCEXw7nadnHM8Dq38EGfSh6dqA9QWTyefMLEcBYJUuekgW4BYPJcr9E7j').serialize()==key.serialize()
assert bip32.HDKey.from_string('xpub6FnCn6nSzZAw5Tw7cgR9bi15UV96gLZhjDstkXXxvCLsUXBGXPdSnLFbdpq8p9HmGsApME5hQTZ3emM2rnY5agb9rXpVGyy3bdW6EEgAtqt').serialize()==key.to_public().serialize()
assert root.derive("m/0/2147483647'/1/2147483646'").to_public().child(2).to_base58()=='xpub6FnCn6nSzZAw5Tw7cgR9bi15UV96gLZhjDstkXXxvCLsUXBGXPdSnLFbdpq8p9HmGsApME5hQTZ3emM2rnY5agb9rXpVGyy3bdW6EEgAtqt'
gc.collect()
root=bip32.HDKey.from_seed(binascii.unhexlify('4b381541583be4423346c643850da4b320e46a87ae3d2a4e6da11eba819cd4acba45d239319ac14f863b8d5ab5a0d0c64d2e8a1e7d1457df2e5a3c51c73235be'))
key=root.derive('m')
assert key.to_base58()=='xprv9s21ZrQH143K25QhxbucbDDuQ4naNntJRi4KUfWT7xo4EKsHt2QJDu7KXp1A3u7Bi1j8ph3EGsZ9Xvz9dGuVrtHHs7pXeTzjuxBrCmmhgC6'
assert key.to_public().to_base58()=='xpub661MyMwAqRbcEZVB4dScxMAdx6d4nFc9nvyvH3v4gJL378CSRZiYmhRoP7mBy6gSPSCYk6SzXPTf3ND1cZAceL7SfJ1Z3GC8vBgp2epUt13'
assert bip32.HDKey.from_string('xprv9s21ZrQH143K25QhxbucbDDuQ4naNntJRi4KUfWT7xo4EKsHt2QJDu7KXp1A3u7Bi1j8ph3EGsZ9Xvz9dGuVrtHHs7pXeTzjuxBrCmmhgC6').serialize()==key.serialize()
assert bip32.HDKey.from_string('xpub661MyMwAqRbcEZVB4dScxMAdx6d4nFc9nvyvH3v4gJL378CSRZiYmhRoP7mBy6gSPSCYk6SzXPTf3ND1cZAceL7SfJ1Z3GC8vBgp2epUt13').serialize()==key.to_public().serialize()
gc.collect()
root=bip32.HDKey.from_seed(binascii.unhexlify('4b381541583be4423346c643850da4b320e46a87ae3d2a4e6da11eba819cd4acba45d239319ac14f863b8d5ab5a0d0c64d2e8a1e7d1457df2e5a3c51c73235be'))
key=root.derive("m/0'")
assert key.to_base58()=='xprv9uPDJpEQgRQfDcW7BkF7eTya6RPxXeJCqCJGHuCJ4GiRVLzkTXBAJMu2qaMWPrS7AANYqdq6vcBcBUdJCVVFceUvJFjaPdGZ2y9WACViL4L'
assert key.to_public().to_base58()=='xpub68NZiKmJWnxxS6aaHmn81bvJeTESw724CRDs6HbuccFQN9Ku14VQrADWgqbhhTHBaohPX4CjNLf9fq9MYo6oDaPPLPxSb7gwQN3ih19Zm4Y'
assert bip32.HDKey.from_string('xprv9uPDJpEQgRQfDcW7BkF7eTya6RPxXeJCqCJGHuCJ4GiRVLzkTXBAJMu2qaMWPrS7AANYqdq6vcBcBUdJCVVFceUvJFjaPdGZ2y9WACViL4L').serialize()==key.serialize()
assert bip32.HDKey.from_string('xpub68NZiKmJWnxxS6aaHmn81bvJeTESw724CRDs6HbuccFQN9Ku14VQrADWgqbhhTHBaohPX4CjNLf9fq9MYo6oDaPPLPxSb7gwQN3ih19Zm4Y').serialize()==key.to_public().serialize()
gc.collect()
root=bip32.HDKey.from_seed(binascii.unhexlify('3ddd5602285899a946114506157c7997e5444528f3003f6134712147db19b678'))
key=root.derive('m')
assert key.to_base58()=='xprv9s21ZrQH143K48vGoLGRPxgo2JNkJ3J3fqkirQC2zVdk5Dgd5w14S7fRDyHH4dWNHUgkvsvNDCkvAwcSHNAQwhwgNMgZhLtQC63zxwhQmRv'
assert key.to_public().to_base58()=='xpub661MyMwAqRbcGczjuMoRm6dXaLDEhW1u34gKenbeYqAix21mdUKJyuyu5F1rzYGVxyL6tmgBUAEPrEz92mBXjByMRiJdba9wpnN37RLLAXa'
assert bip32.HDKey.from_string('xprv9s21ZrQH143K48vGoLGRPxgo2JNkJ3J3fqkirQC2zVdk5Dgd5w14S7fRDyHH4dWNHUgkvsvNDCkvAwcSHNAQwhwgNMgZhLtQC63zxwhQmRv').serialize()==key.serialize()
assert bip32.HDKey.from_string('xpub661MyMwAqRbcGczjuMoRm6dXaLDEhW1u34gKenbeYqAix21mdUKJyuyu5F1rzYGVxyL6tmgBUAEPrEz92mBXjByMRiJdba9wpnN37RLLAXa').serialize()==key.to_public().serialize()
gc.collect()
root=bip32.HDKey.from_seed(binascii.unhexlify('3ddd5602285899a946114506157c7997e5444528f3003f6134712147db19b678'))
key=root.derive("m/0'")
assert key.to_base58()=='xprv9vB7xEWwNp9kh1wQRfCCQMnZUEG21LpbR9NPCNN1dwhiZkjjeGRnaALmPXCX7SgjFTiCTT6bXes17boXtjq3xLpcDjzEuGLQBM5ohqkao9G'
assert key.to_public().to_base58()=='xpub69AUMk3qDBi3uW1sXgjCmVjJ2G6WQoYSnNHyzkmdCHEhSZ4tBok37xfFEqHd2AddP56Tqp4o56AePAgCjYdvpW2PU2jbUPFKsav5ut6Ch1m'
assert bip32.HDKey.from_string('xprv9vB7xEWwNp9kh1wQRfCCQMnZUEG21LpbR9NPCNN1dwhiZkjjeGRnaALmPXCX7SgjFTiCTT6bXes17boXtjq3xLpcDjzEuGLQBM5ohqkao9G').serialize()==key.serialize()
assert bip32.HDKey.from_string('xpub69AUMk3qDBi3uW1sXgjCmVjJ2G6WQoYSnNHyzkmdCHEhSZ4tBok37xfFEqHd2AddP56Tqp4o56AePAgCjYdvpW2PU2jbUPFKsav5ut6Ch1m').serialize()==key.to_public().serialize()
gc.collect()
root=bip32.HDKey.from_seed(binascii.unhexlify('3ddd5602285899a946114506157c7997e5444528f3003f6134712147db19b678'))
key=root.derive("m/0'/1'")
assert key.to_base58()=='xprv9xJocDuwtYCMNAo3Zw76WENQeAS6WGXQ55RCy7tDJ8oALr4FWkuVoHJeHVAcAqiZLE7Je3vZJHxspZdFHfnBEjHqU5hG1Jaj32dVoS6XLT1'
assert key.to_public().to_base58()=='xpub6BJA1jSqiukeaesWfxe6sNK9CCGaujFFSJLomWHprUL9DePQ4JDkM5d88n49sMGJxrhpjazuXYWdMf17C9T5XnxkopaeS7jGk1GyyVziaMt'
assert bip32.HDKey.from_string('xprv9xJocDuwtYCMNAo3Zw76WENQeAS6WGXQ55RCy7tDJ8oALr4FWkuVoHJeHVAcAqiZLE7Je3vZJHxspZdFHfnBEjHqU5hG1Jaj32dVoS6XLT1').serialize()==key.serialize()
assert bip32.HDKey.from_string('xpub6BJA1jSqiukeaesWfxe6sNK9CCGaujFFSJLomWHprUL9DePQ4JDkM5d88n49sMGJxrhpjazuXYWdMf17C9T5XnxkopaeS7jGk1GyyVziaMt').serialize()==key.to_public().serialize()
gc.collect()
try:
    bip32.HDKey.from_string('xpub661MyMwAqRbcEYS8w7XLSVeEsBXy79zSzH1J8vCdxAZningWLdN3zgtU6LBpB85b3D2yc8sfvZU521AAwdZafEz7mnzBBsz4wKY5fTtTQBm')
    assert False
except (ValueError,ec.ECError,bip32.HDError):pass
try:
    bip32.HDKey.from_string('xprv9s21ZrQH143K24Mfq5zL5MhWK9hUhhGbd45hLXo2Pq2oqzMMo63oStZzFGTQQD3dC4H2D5GBj7vWvSQaaBv5cxi9gafk7NF3pnBju6dwKvH')
    assert False
except (ValueError,ec.ECError,bip32.HDError):pass
try:
    bip32.HDKey.from_string('xpub661MyMwAqRbcEYS8w7XLSVeEsBXy79zSzH1J8vCdxAZningWLdN3zgtU6Txnt3siSujt9RCVYsx4qHZGc62TG4McvMGcAUjeuwZdduYEvFn')
    assert False
except (ValueError,ec.ECError,bip32.HDError):pass
try:
    bip32.HDKey.from_string('xprv9s21ZrQH143K24Mfq5zL5MhWK9hUhhGbd45hLXo2Pq2oqzMMo63oStZzFGpWnsj83BHtEy5Zt8CcDr1UiRXuWCmTQLxEK9vbz5gPstX92JQ')
    assert False
except (ValueError,ec.ECError,bip32.HDError):pass
try:
    bip32.HDKey.from_string('xpub661MyMwAqRbcEYS8w7XLSVeEsBXy79zSzH1J8vCdxAZningWLdN3zgtU6N8ZMMXctdiCjxTNq964yKkwrkBJJwpzZS4HS2fxvyYUA4q2Xe4')
    assert False
except (ValueError,ec.ECError,bip32.HDError):pass
try:
    bip32.HDKey.from_string('xprv9s21ZrQH143K24Mfq5zL5MhWK9hUhhGbd45hLXo2Pq2oqzMMo63oStZzFAzHGBP2UuGCqWLTAPLcMtD9y5gkZ6Eq3Rjuahrv17fEQ3Qen6J')
    assert False
except (ValueError,ec.ECError,bip32.HDError):pass
try:
    bip32.HDKey.from_string('xprv9s2SPatNQ9Vc6GTbVMFPFo7jsaZySyzk7L8n2uqKXJen3KUmvQNTuLh3fhZMBoG3G4ZW1N2kZuHEPY53qmbZzCHshoQnNf4GvELZfqTUrcv')
    assert False
except (ValueError,ec.ECError,bip32.HDError):pass
try:
    bip32.HDKey.from_string('xpub661no6RGEX3uJkY4bNnPcw4URcQTrSibUZ4NqJEw5eBkv7ovTwgiT91XX27VbEXGENhYRCf7hyEbWrR3FewATdCEebj6znwMfQkhRYHRLpJ')
    assert False
except (ValueError,ec.ECError,bip32.HDError):pass
try:
    bip32.HDKey.from_string('xprv9s21ZrQH4r4TsiLvyLXqM9P7k1K3EYhA1kkD6xuquB5i39AU8KF42acDyL3qsDbU9NmZn6MsGSUYZEsuoePmjzsB3eFKSUEh3Gu1N3cqVUN')
    assert False
except (ValueError,ec.ECError,bip32.HDError):pass
try:
    bip32.HDKey.from_string('xpub661MyMwAuDcm6CRQ5N4qiHKrJ39Xe1R1NyfouMKTTWcguwVcfrZJaNvhpebzGerh7gucBvzEQWRugZDuDXjNDRmXzSZe4c7mnTK97pTvGS8')
    assert False
except (ValueError,ec.ECError,bip32.HDError):pass
try:
    bip32.HDKey.from_string('DMwo58pR1QLEFihHiXPVykYB6fJmsTeHvyTp7hRThAtCX8CvYzgPcn8XnmdfHGMQzT7ayAmfo4z3gY5KfbrZWZ6St24UVf2Qgo6oujFktLHdHY4')
    assert False
except (ValueError,ec.ECError,bip32.HDError):pass
try:
    bip32.HDKey.from_string('DMwo58pR1QLEFihHiXPVykYB6fJmsTeHvyTp7hRThAtCX8CvYzgPcn8XnmdfHPmHJiEDXkTiJTVV9rHEBUem2mwVbbNfvT2MTcAqj3nesx8uBf9')
    assert False
except (ValueError,ec.ECError,bip32.HDError):pass
try:
    bip32.HDKey.from_string('xprv9s21ZrQH143K24Mfq5zL5MhWK9hUhhGbd45hLXo2Pq2oqzMMo63oStZzF93Y5wvzdUayhgkkFoicQZcP3y52uPPxFnfoLZB21Teqt1VvEHx')
    assert False
except (ValueError,ec.ECError,bip32.HDError):pass
try:
    bip32.HDKey.from_string('xprv9s21ZrQH143K24Mfq5zL5MhWK9hUhhGbd45hLXo2Pq2oqzMMo63oStZzFAzHGBP2UuGCqWLTAPLcMtD5SDKr24z3aiUvKr9bJpdrcLg1y3G')
    assert False
except (ValueError,ec.ECError,bip32.HDError):pass
try:
    bip32.HDKey.from_string('xpub661MyMwAqRbcEYS8w7XLSVeEsBXy79zSzH1J8vCdxAZningWLdN3zgtU6Q5JXayek4PRsn35jii4veMimro1xefsM58PgBMrvdYre8QyULY')
    assert False
except (ValueError,ec.ECError,bip32.HDError):pass
try:
    bip32.HDKey.from_string('xprv9s21ZrQH143K3QTDL4LXw2F7HEK3wJUD2nW2nRk4stbPy6cq3jPPqjiChkVvvNKmPGJxWUtg6LnF5kejMRNNU3TGtRBeJgk33yuGBxrMPHL')
    assert False
except (ValueError,ec.ECError,bip32.HDError):pass
print('@@BIP32_PASS',17,16)
signature=binascii.unhexlify('e907831f80848d1069a5371b402410364bdf1c5f8307b0084c55f1ce2dca821525f66a4a85ea8b71e482a74f382d2ce5ebeee8fdb2172f477df4900d310536c0')
message=binascii.unhexlify('0000000000000000000000000000000000000000000000000000000000000000')
result=False
try:
    point=c.xonly_pubkey_parse(binascii.unhexlify('f9308a019258c31049344f85f89d5229b531c845836f99b08601f113bce036f9'))
    result=c.schnorrsig_verify(signature,message,point)
except ValueError:pass
assert result is True
secret=binascii.unhexlify('0000000000000000000000000000000000000000000000000000000000000003')
assert c.xonly_pubkey_serialize(c.ec_pubkey_create(secret))==binascii.unhexlify('f9308a019258c31049344f85f89d5229b531c845836f99b08601f113bce036f9')
assert c.schnorrsig_sign(message,secret,extra_data=binascii.unhexlify('0000000000000000000000000000000000000000000000000000000000000000'))==signature
gc.collect()
signature=binascii.unhexlify('6896bd60eeae296db48a229ff71dfe071bde413e6d43f917dc8dcf8c78de33418906d11ac976abccb20b091292bff4ea897efcb639ea871cfa95f6de339e4b0a')
message=binascii.unhexlify('243f6a8885a308d313198a2e03707344a4093822299f31d0082efa98ec4e6c89')
result=False
try:
    point=c.xonly_pubkey_parse(binascii.unhexlify('dff1d77f2a671c5f36183726db2341be58feae1da2deced843240f7b502ba659'))
    result=c.schnorrsig_verify(signature,message,point)
except ValueError:pass
assert result is True
secret=binascii.unhexlify('b7e151628aed2a6abf7158809cf4f3c762e7160f38b4da56a784d9045190cfef')
assert c.xonly_pubkey_serialize(c.ec_pubkey_create(secret))==binascii.unhexlify('dff1d77f2a671c5f36183726db2341be58feae1da2deced843240f7b502ba659')
assert c.schnorrsig_sign(message,secret,extra_data=binascii.unhexlify('0000000000000000000000000000000000000000000000000000000000000001'))==signature
gc.collect()
signature=binascii.unhexlify('5831aaeed7b44bb74e5eab94ba9d4294c49bcf2a60728d8b4c200f50dd313c1bab745879a5ad954a72c45a91c3a51d3c7adea98d82f8481e0e1e03674a6f3fb7')
message=binascii.unhexlify('7e2d58d8b3bcdf1abadec7829054f90dda9805aab56c77333024b9d0a508b75c')
result=False
try:
    point=c.xonly_pubkey_parse(binascii.unhexlify('dd308afec5777e13121fa72b9cc1b7cc0139715309b086c960e18fd969774eb8'))
    result=c.schnorrsig_verify(signature,message,point)
except ValueError:pass
assert result is True
secret=binascii.unhexlify('c90fdaa22168c234c4c6628b80dc1cd129024e088a67cc74020bbea63b14e5c9')
assert c.xonly_pubkey_serialize(c.ec_pubkey_create(secret))==binascii.unhexlify('dd308afec5777e13121fa72b9cc1b7cc0139715309b086c960e18fd969774eb8')
assert c.schnorrsig_sign(message,secret,extra_data=binascii.unhexlify('c87aa53824b4d7ae2eb035a2b5bbbccc080e76cdc6d1692c4b0b62d798e6d906'))==signature
gc.collect()
signature=binascii.unhexlify('7eb0509757e246f19449885651611cb965ecc1a187dd51b64fda1edc9637d5ec97582b9cb13db3933705b32ba982af5af25fd78881ebb32771fc5922efc66ea3')
message=binascii.unhexlify('ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff')
result=False
try:
    point=c.xonly_pubkey_parse(binascii.unhexlify('25d1dff95105f5253c4022f628a996ad3a0d95fbf21d468a1b33f8c160d8f517'))
    result=c.schnorrsig_verify(signature,message,point)
except ValueError:pass
assert result is True
secret=binascii.unhexlify('0b432b2677937381aef05bb02a66ecd012773062cf3fa2549e44f58ed2401710')
assert c.xonly_pubkey_serialize(c.ec_pubkey_create(secret))==binascii.unhexlify('25d1dff95105f5253c4022f628a996ad3a0d95fbf21d468a1b33f8c160d8f517')
assert c.schnorrsig_sign(message,secret,extra_data=binascii.unhexlify('ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff'))==signature
gc.collect()
signature=binascii.unhexlify('00000000000000000000003b78ce563f89a0ed9414f5aa28ad0d96d6795f9c6376afb1548af603b3eb45c9f8207dee1060cb71c04e80f593060b07d28308d7f4')
message=binascii.unhexlify('4df3c3f68fcc83b27e9d42c90431a72499f17875c81a599b566c9889b9696703')
result=False
try:
    point=c.xonly_pubkey_parse(binascii.unhexlify('d69c3509bb99e412e68b0fe8544e72837dfa30746d8be2aa65975f29d22dc7b9'))
    result=c.schnorrsig_verify(signature,message,point)
except ValueError:pass
assert result is True
gc.collect()
signature=binascii.unhexlify('6cff5c3ba86c69ea4b7376f31a9bcb4f74c1976089b2d9963da2e5543e17776969e89b4c5564d00349106b8497785dd7d1d713a8ae82b32fa79d5f7fc407d39b')
message=binascii.unhexlify('243f6a8885a308d313198a2e03707344a4093822299f31d0082efa98ec4e6c89')
result=False
try:
    point=c.xonly_pubkey_parse(binascii.unhexlify('eefdea4cdb677750a420fee807eacf21eb9898ae79b9768766e4faa04a2d4a34'))
    result=c.schnorrsig_verify(signature,message,point)
except ValueError:pass
assert result is False
gc.collect()
signature=binascii.unhexlify('fff97bd5755eeea420453a14355235d382f6472f8568a18b2f057a14602975563cc27944640ac607cd107ae10923d9ef7a73c643e166be5ebeafa34b1ac553e2')
message=binascii.unhexlify('243f6a8885a308d313198a2e03707344a4093822299f31d0082efa98ec4e6c89')
result=False
try:
    point=c.xonly_pubkey_parse(binascii.unhexlify('dff1d77f2a671c5f36183726db2341be58feae1da2deced843240f7b502ba659'))
    result=c.schnorrsig_verify(signature,message,point)
except ValueError:pass
assert result is False
gc.collect()
signature=binascii.unhexlify('1fa62e331edbc21c394792d2ab1100a7b432b013df3f6ff4f99fcb33e0e1515f28890b3edb6e7189b630448b515ce4f8622a954cfe545735aaea5134fccdb2bd')
message=binascii.unhexlify('243f6a8885a308d313198a2e03707344a4093822299f31d0082efa98ec4e6c89')
result=False
try:
    point=c.xonly_pubkey_parse(binascii.unhexlify('dff1d77f2a671c5f36183726db2341be58feae1da2deced843240f7b502ba659'))
    result=c.schnorrsig_verify(signature,message,point)
except ValueError:pass
assert result is False
gc.collect()
signature=binascii.unhexlify('6cff5c3ba86c69ea4b7376f31a9bcb4f74c1976089b2d9963da2e5543e177769961764b3aa9b2ffcb6ef947b6887a226e8d7c93e00c5ed0c1834ff0d0c2e6da6')
message=binascii.unhexlify('243f6a8885a308d313198a2e03707344a4093822299f31d0082efa98ec4e6c89')
result=False
try:
    point=c.xonly_pubkey_parse(binascii.unhexlify('dff1d77f2a671c5f36183726db2341be58feae1da2deced843240f7b502ba659'))
    result=c.schnorrsig_verify(signature,message,point)
except ValueError:pass
assert result is False
gc.collect()
signature=binascii.unhexlify('0000000000000000000000000000000000000000000000000000000000000000123dda8328af9c23a94c1feecfd123ba4fb73476f0d594dcb65c6425bd186051')
message=binascii.unhexlify('243f6a8885a308d313198a2e03707344a4093822299f31d0082efa98ec4e6c89')
result=False
try:
    point=c.xonly_pubkey_parse(binascii.unhexlify('dff1d77f2a671c5f36183726db2341be58feae1da2deced843240f7b502ba659'))
    result=c.schnorrsig_verify(signature,message,point)
except ValueError:pass
assert result is False
gc.collect()
signature=binascii.unhexlify('00000000000000000000000000000000000000000000000000000000000000017615fbaf5ae28864013c099742deadb4dba87f11ac6754f93780d5a1837cf197')
message=binascii.unhexlify('243f6a8885a308d313198a2e03707344a4093822299f31d0082efa98ec4e6c89')
result=False
try:
    point=c.xonly_pubkey_parse(binascii.unhexlify('dff1d77f2a671c5f36183726db2341be58feae1da2deced843240f7b502ba659'))
    result=c.schnorrsig_verify(signature,message,point)
except ValueError:pass
assert result is False
gc.collect()
signature=binascii.unhexlify('4a298dacae57395a15d0795ddbfd1dcb564da82b0f269bc70a74f8220429ba1d69e89b4c5564d00349106b8497785dd7d1d713a8ae82b32fa79d5f7fc407d39b')
message=binascii.unhexlify('243f6a8885a308d313198a2e03707344a4093822299f31d0082efa98ec4e6c89')
result=False
try:
    point=c.xonly_pubkey_parse(binascii.unhexlify('dff1d77f2a671c5f36183726db2341be58feae1da2deced843240f7b502ba659'))
    result=c.schnorrsig_verify(signature,message,point)
except ValueError:pass
assert result is False
gc.collect()
signature=binascii.unhexlify('fffffffffffffffffffffffffffffffffffffffffffffffffffffffefffffc2f69e89b4c5564d00349106b8497785dd7d1d713a8ae82b32fa79d5f7fc407d39b')
message=binascii.unhexlify('243f6a8885a308d313198a2e03707344a4093822299f31d0082efa98ec4e6c89')
result=False
try:
    point=c.xonly_pubkey_parse(binascii.unhexlify('dff1d77f2a671c5f36183726db2341be58feae1da2deced843240f7b502ba659'))
    result=c.schnorrsig_verify(signature,message,point)
except ValueError:pass
assert result is False
gc.collect()
signature=binascii.unhexlify('6cff5c3ba86c69ea4b7376f31a9bcb4f74c1976089b2d9963da2e5543e177769fffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364141')
message=binascii.unhexlify('243f6a8885a308d313198a2e03707344a4093822299f31d0082efa98ec4e6c89')
result=False
try:
    point=c.xonly_pubkey_parse(binascii.unhexlify('dff1d77f2a671c5f36183726db2341be58feae1da2deced843240f7b502ba659'))
    result=c.schnorrsig_verify(signature,message,point)
except ValueError:pass
assert result is False
gc.collect()
signature=binascii.unhexlify('6cff5c3ba86c69ea4b7376f31a9bcb4f74c1976089b2d9963da2e5543e17776969e89b4c5564d00349106b8497785dd7d1d713a8ae82b32fa79d5f7fc407d39b')
message=binascii.unhexlify('243f6a8885a308d313198a2e03707344a4093822299f31d0082efa98ec4e6c89')
result=False
try:
    point=c.xonly_pubkey_parse(binascii.unhexlify('fffffffffffffffffffffffffffffffffffffffffffffffffffffffefffffc30'))
    result=c.schnorrsig_verify(signature,message,point)
except ValueError:pass
assert result is False
gc.collect()
signature=binascii.unhexlify('71535db165ecd9fbbc046e5ffaea61186bb6ad436732fccc25291a55895464cf6069ce26bf03466228f19a3a62db8a649f2d560fac652827d1af0574e427ab63')
message=binascii.unhexlify('')
result=False
try:
    point=c.xonly_pubkey_parse(binascii.unhexlify('778caa53b4393ac467774d09497a87224bf9fab6f6e68b23086497324d6fd117'))
    result=c.schnorrsig_verify(signature,message,point)
except ValueError:pass
assert result is True
secret=binascii.unhexlify('0340034003400340034003400340034003400340034003400340034003400340')
assert c.xonly_pubkey_serialize(c.ec_pubkey_create(secret))==binascii.unhexlify('778caa53b4393ac467774d09497a87224bf9fab6f6e68b23086497324d6fd117')
assert c.schnorrsig_sign(message,secret,extra_data=binascii.unhexlify('0000000000000000000000000000000000000000000000000000000000000000'))==signature
gc.collect()
signature=binascii.unhexlify('08a20a0afef64124649232e0693c583ab1b9934ae63b4c3511f3ae1134c6a303ea3173bfea6683bd101fa5aa5dbc1996fe7cacfc5a577d33ec14564cec2bacbf')
message=binascii.unhexlify('11')
result=False
try:
    point=c.xonly_pubkey_parse(binascii.unhexlify('778caa53b4393ac467774d09497a87224bf9fab6f6e68b23086497324d6fd117'))
    result=c.schnorrsig_verify(signature,message,point)
except ValueError:pass
assert result is True
secret=binascii.unhexlify('0340034003400340034003400340034003400340034003400340034003400340')
assert c.xonly_pubkey_serialize(c.ec_pubkey_create(secret))==binascii.unhexlify('778caa53b4393ac467774d09497a87224bf9fab6f6e68b23086497324d6fd117')
assert c.schnorrsig_sign(message,secret,extra_data=binascii.unhexlify('0000000000000000000000000000000000000000000000000000000000000000'))==signature
gc.collect()
signature=binascii.unhexlify('5130f39a4059b43bc7cac09a19ece52b5d8699d1a71e3c52da9afdb6b50ac370c4a482b77bf960f8681540e25b6771ece1e5a37fd80e5a51897c5566a97ea5a5')
message=binascii.unhexlify('0102030405060708090a0b0c0d0e0f1011')
result=False
try:
    point=c.xonly_pubkey_parse(binascii.unhexlify('778caa53b4393ac467774d09497a87224bf9fab6f6e68b23086497324d6fd117'))
    result=c.schnorrsig_verify(signature,message,point)
except ValueError:pass
assert result is True
secret=binascii.unhexlify('0340034003400340034003400340034003400340034003400340034003400340')
assert c.xonly_pubkey_serialize(c.ec_pubkey_create(secret))==binascii.unhexlify('778caa53b4393ac467774d09497a87224bf9fab6f6e68b23086497324d6fd117')
assert c.schnorrsig_sign(message,secret,extra_data=binascii.unhexlify('0000000000000000000000000000000000000000000000000000000000000000'))==signature
gc.collect()
signature=binascii.unhexlify('403b12b0d8555a344175ea7ec746566303321e5dbfa8be6f091635163eca79a8585ed3e3170807e7c03b720fc54c7b23897fcba0e9d0b4a06894cfd249f22367')
message=binascii.unhexlify('99999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999')
result=False
try:
    point=c.xonly_pubkey_parse(binascii.unhexlify('778caa53b4393ac467774d09497a87224bf9fab6f6e68b23086497324d6fd117'))
    result=c.schnorrsig_verify(signature,message,point)
except ValueError:pass
assert result is True
secret=binascii.unhexlify('0340034003400340034003400340034003400340034003400340034003400340')
assert c.xonly_pubkey_serialize(c.ec_pubkey_create(secret))==binascii.unhexlify('778caa53b4393ac467774d09497a87224bf9fab6f6e68b23086497324d6fd117')
assert c.schnorrsig_sign(message,secret,extra_data=binascii.unhexlify('0000000000000000000000000000000000000000000000000000000000000000'))==signature
gc.collect()
print('@@BIP340_PASS',19)
s=Seed('abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about'.split(),passphrase='TREZOR')
assert s.get_root().to_base58()=='xprv9s21ZrQH143K3h3fDYiay8mocZ3afhfULfb5GX8kCBdno77K4HiA15Tg23wpbeF1pLfs1c5SPmYHrEpTuuRhxMwvKDwqdKiGJS9XFKzUsAF'
assert s.get_fingerprint()=='b4e3f5ed'
s.wipe()
gc.collect()
s=Seed('legal winner thank year wave sausage worth useful legal winner thank yellow'.split(),passphrase='TREZOR')
assert s.get_root().to_base58()=='xprv9s21ZrQH143K2gA81bYFHqU68xz1cX2APaSq5tt6MFSLeXnCKV1RVUJt9FWNTbrrryem4ZckN8k4Ls1H6nwdvDTvnV7zEXs2HgPezuVccsq'
assert s.get_fingerprint()=='1ddb040f'
s.wipe()
gc.collect()
s=Seed('letter advice cage absurd amount doctor acoustic avoid letter advice cage above'.split(),passphrase='TREZOR')
assert s.get_root().to_base58()=='xprv9s21ZrQH143K2shfP28KM3nr5Ap1SXjz8gc2rAqqMEynmjt6o1qboCDpxckqXavCwdnYds6yBHZGKHv7ef2eTXy461PXUjBFQg6PrwY4Gzq'
assert s.get_fingerprint()=='53452836'
s.wipe()
gc.collect()
s=Seed('zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo wrong'.split(),passphrase='TREZOR')
assert s.get_root().to_base58()=='xprv9s21ZrQH143K2V4oox4M8Zmhi2Fjx5XK4Lf7GKRvPSgydU3mjZuKGCTg7UPiBUD7ydVPvSLtg9hjp7MQTYsW67rZHAXeccqYqrsx8LcXnyd'
assert s.get_fingerprint()=='128d6f17'
s.wipe()
gc.collect()
s=Seed('abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon agent'.split(),passphrase='TREZOR')
assert s.get_root().to_base58()=='xprv9s21ZrQH143K3mEDrypcZ2usWqFgzKB6jBBx9B6GfC7fu26X6hPRzVjzkqkPvDqp6g5eypdk6cyhGnBngbjeHTe4LsuLG1cCmKJka5SMkmU'
assert s.get_fingerprint()=='edc43bbe'
s.wipe()
gc.collect()
s=Seed('legal winner thank year wave sausage worth useful legal winner thank year wave sausage worth useful legal will'.split(),passphrase='TREZOR')
assert s.get_root().to_base58()=='xprv9s21ZrQH143K3Lv9MZLj16np5GzLe7tDKQfVusBni7toqJGcnKRtHSxUwbKUyUWiwpK55g1DUSsw76TF1T93VT4gz4wt5RM23pkaQLnvBh7'
assert s.get_fingerprint()=='15e8639c'
s.wipe()
gc.collect()
s=Seed('letter advice cage absurd amount doctor acoustic avoid letter advice cage absurd amount doctor acoustic avoid letter always'.split(),passphrase='TREZOR')
assert s.get_root().to_base58()=='xprv9s21ZrQH143K3VPCbxbUtpkh9pRG371UCLDz3BjceqP1jz7XZsQ5EnNkYAEkfeZp62cDNj13ZTEVG1TEro9sZ9grfRmcYWLBhCocViKEJae'
assert s.get_fingerprint()=='b7c11d9d'
s.wipe()
gc.collect()
s=Seed('zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo when'.split(),passphrase='TREZOR')
assert s.get_root().to_base58()=='xprv9s21ZrQH143K36Ao5jHRVhFGDbLP6FCx8BEEmpru77ef3bmA928BxsqvVM27WnvvyfWywiFN8K6yToqMaGYfzS6Db1EHAXT5TuyCLBXUfdm'
assert s.get_fingerprint()=='465649fd'
s.wipe()
gc.collect()
s=Seed('abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon art'.split(),passphrase='TREZOR')
assert s.get_root().to_base58()=='xprv9s21ZrQH143K32qBagUJAMU2LsHg3ka7jqMcV98Y7gVeVyNStwYS3U7yVVoDZ4btbRNf4h6ibWpY22iRmXq35qgLs79f312g2kj5539ebPM'
assert s.get_fingerprint()=='88bca92b'
s.wipe()
gc.collect()
s=Seed('legal winner thank year wave sausage worth useful legal winner thank year wave sausage worth useful legal winner thank year wave sausage worth title'.split(),passphrase='TREZOR')
assert s.get_root().to_base58()=='xprv9s21ZrQH143K3Y1sd2XVu9wtqxJRvybCfAetjUrMMco6r3v9qZTBeXiBZkS8JxWbcGJZyio8TrZtm6pkbzG8SYt1sxwNLh3Wx7to5pgiVFU'
assert s.get_fingerprint()=='e5ddd654'
s.wipe()
gc.collect()
s=Seed('letter advice cage absurd amount doctor acoustic avoid letter advice cage absurd amount doctor acoustic avoid letter advice cage absurd amount doctor acoustic bless'.split(),passphrase='TREZOR')
assert s.get_root().to_base58()=='xprv9s21ZrQH143K3CSnQNYC3MqAAqHwxeTLhDbhF43A4ss4ciWNmCY9zQGvAKUSqVUf2vPHBTSE1rB2pg4avopqSiLVzXEU8KziNnVPauTqLRo'
assert s.get_fingerprint()=='eb2bfaaf'
s.wipe()
gc.collect()
s=Seed('zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo zoo vote'.split(),passphrase='TREZOR')
assert s.get_root().to_base58()=='xprv9s21ZrQH143K2WFF16X85T2QCpndrGwx6GueB72Zf3AHwHJaknRXNF37ZmDrtHrrLSHvbuRejXcnYxoZKvRquTPyp2JiNG3XcjQyzSEgqCB'
assert s.get_fingerprint()=='b18c73ee'
s.wipe()
gc.collect()
s=Seed('ozone drill grab fiber curtain grace pudding thank cruise elder eight picnic'.split(),passphrase='TREZOR')
assert s.get_root().to_base58()=='xprv9s21ZrQH143K2oZ9stBYpoaZ2ktHj7jLz7iMqpgg1En8kKFTXJHsjxry1JbKH19YrDTicVwKPehFKTbmaxgVEc5TpHdS1aYhB2s9aFJBeJH'
assert s.get_fingerprint()=='806969a0'
s.wipe()
gc.collect()
s=Seed('gravity machine north sort system female filter attitude volume fold club stay feature office ecology stable narrow fog'.split(),passphrase='TREZOR')
assert s.get_root().to_base58()=='xprv9s21ZrQH143K3uT8eQowUjsxrmsA9YUuQQK1RLqFufzybxD6DH6gPY7NjJ5G3EPHjsWDrs9iivSbmvjc9DQJbJGatfa9pv4MZ3wjr8qWPAK'
assert s.get_fingerprint()=='005af296'
s.wipe()
gc.collect()
s=Seed('hamster diagram private dutch cause delay private meat slide toddler razor book happy fancy gospel tennis maple dilemma loan word shrug inflict delay length'.split(),passphrase='TREZOR')
assert s.get_root().to_base58()=='xprv9s21ZrQH143K2XTAhys3pMNcGn261Fi5Ta2Pw8PwaVPhg3D8DWkzWQwjTJfskj8ofb81i9NP2cUNKxwjueJHHMQAnxtivTA75uUFqPFeWzk'
assert s.get_fingerprint()=='1f989357'
s.wipe()
gc.collect()
s=Seed('scheme spot photo card baby mountain device kick cradle pact join borrow'.split(),passphrase='TREZOR')
assert s.get_root().to_base58()=='xprv9s21ZrQH143K3FperxDp8vFsFycKCRcJGAFmcV7umQmcnMZaLtZRt13QJDsoS5F6oYT6BB4sS6zmTmyQAEkJKxJ7yByDNtRe5asP2jFGhT6'
assert s.get_fingerprint()=='c66a100e'
s.wipe()
gc.collect()
s=Seed('horn tenant knee talent sponsor spell gate clip pulse soap slush warm silver nephew swap uncle crack brave'.split(),passphrase='TREZOR')
assert s.get_root().to_base58()=='xprv9s21ZrQH143K3R1SfVZZLtVbXEB9ryVxmVtVMsMwmEyEvgXN6Q84LKkLRmf4ST6QrLeBm3jQsb9gx1uo23TS7vo3vAkZGZz71uuLCcywUkt'
assert s.get_fingerprint()=='3e95301d'
s.wipe()
gc.collect()
s=Seed('panda eyebrow bullet gorilla call smoke muffin taste mesh discover soft ostrich alcohol speed nation flash devote level hobby quick inner drive ghost inside'.split(),passphrase='TREZOR')
assert s.get_root().to_base58()=='xprv9s21ZrQH143K2WNnKmssvZYM96VAr47iHUQUTUyUXH3sAGNjhJANddnhw3i3y3pBbRAVk5M5qUGFr4rHbEWwXgX4qrvrceifCYQJbbFDems'
assert s.get_fingerprint()=='d3539b0d'
s.wipe()
gc.collect()
s=Seed('cat swing flag economy stadium alone churn speed unique patch report train'.split(),passphrase='TREZOR')
assert s.get_root().to_base58()=='xprv9s21ZrQH143K4G28omGMogEoYgDQuigBo8AFHAGDaJdqQ99QKMQ5J6fYTMfANTJy6xBmhvsNZ1CJzRZ64PWbnTFUn6CDV2FxoMDLXdk95DQ'
assert s.get_fingerprint()=='31d13b25'
s.wipe()
gc.collect()
s=Seed('light rule cinnamon wrap drastic word pride squirrel upgrade then income fatal apart sustain crack supply proud access'.split(),passphrase='TREZOR')
assert s.get_root().to_base58()=='xprv9s21ZrQH143K3wtsvY8L2aZyxkiWULZH4vyQE5XkHTXkmx8gHo6RUEfH3Jyr6NwkJhvano7Xb2o6UqFKWHVo5scE31SGDCAUsgVhiUuUDyh'
assert s.get_fingerprint()=='365fc42f'
s.wipe()
gc.collect()
s=Seed('all hour make first leader extend hole alien behind guard gospel lava path output census museum junior mass reopen famous sing advance salt reform'.split(),passphrase='TREZOR')
assert s.get_root().to_base58()=='xprv9s21ZrQH143K3rEfqSM4QZRVmiMuSWY9wugscmaCjYja3SbUD3KPEB1a7QXJoajyR2T1SiXU7rFVRXMV9XdYVSZe7JoUXdP4SRHTxsT1nzm'
assert s.get_fingerprint()=='328434ac'
s.wipe()
gc.collect()
s=Seed('vessel ladder alter error federal sibling chat ability sun glass valve picture'.split(),passphrase='TREZOR')
assert s.get_root().to_base58()=='xprv9s21ZrQH143K2QWV9Wn8Vvs6jbqfF1YbTCdURQW9dLFKDovpKaKrqS3SEWsXCu6ZNky9PSAENg6c9AQYHcg4PjopRGGKmdD313ZHszymnps'
assert s.get_fingerprint()=='8264ddd1'
s.wipe()
gc.collect()
s=Seed('scissors invite lock maple supreme raw rapid void congress muscle digital elegant little brisk hair mango congress clump'.split(),passphrase='TREZOR')
assert s.get_root().to_base58()=='xprv9s21ZrQH143K4aERa2bq7559eMCCEs2QmmqVjUuzfy5eAeDX4mqZffkYwpzGQRE2YEEeLVRoH4CSHxianrFaVnMN2RYaPUZJhJx8S5j6puX'
assert s.get_fingerprint()=='3f070a56'
s.wipe()
gc.collect()
s=Seed('void come effort suffer camp survey warrior heavy shoot primary clutch crush open amazing screen patrol group space point ten exist slush involve unfold'.split(),passphrase='TREZOR')
assert s.get_root().to_base58()=='xprv9s21ZrQH143K39rnQJknpH1WEPFJrzmAqqasiDcVrNuk926oizzJDDQkdiTvNPr2FYDYzWgiMiC63YmfPAa2oPyNB23r2g7d1yiK6WpqaQS'
assert s.get_fingerprint()=='9c0becda'
s.wipe()
gc.collect()
key=ec.PrivateKey(binascii.unhexlify('0000000000000000000000000000000000000000000000000000000000000001'))
message=binascii.unhexlify('0a19b677e9c9a3f67f5527d43dc0f33fe26d7d6c608ecb94ba1e6d32f21ff4f1')
sig=key.sign(message,grind=False)
assert sig.serialize()==binascii.unhexlify('3045022100da28256497c36caa1e416da74022ec464f364ceeca00535e425781183bb52291022022a89de41920a6fe4485213ef26eec05db3f9856e0276db3dddfdc4a1a104f45')
assert key.verify(sig,message)
assert not key.verify(sig,bytes(32))
assert ec.Signature.parse(sig.serialize()).serialize()==sig.serialize()
key=ec.PrivateKey(binascii.unhexlify('0000000000000000000000000000000000000000000000000000000000000001'))
message=binascii.unhexlify('0a19b677e9c9a3f67f5527d43dc0f33fe26d7d6c608ecb94ba1e6d32f21ff4f1')
sig=key.sign(message,grind=True)
assert sig.serialize()==binascii.unhexlify('304402206625902137c0eb8f5bbcbaff299804cb2cfb09cfc5d5302b71ec29e6995abf9f022025021cec3fa0ba9915071b7e57efe0ae85b1e0760d31bff54e620836a0b96390')
assert key.verify(sig,message)
assert not key.verify(sig,bytes(32))
assert ec.Signature.parse(sig.serialize()).serialize()==sig.serialize()
peer=ec.PrivateKey(binascii.unhexlify('0000000000000000000000000000000000000000000000000000000000000002'))
assert key.ecdh(peer.to_public())==binascii.unhexlify('b1c9938f01121e159887ac2c8d393a22e4476ff8212de13fe1939de2a236f0a7')
assert key.ecdh(peer.to_public())==peer.ecdh(key.to_public())
recovered=c.ecdsa_sign_recoverable(message,key.secret)
assert c.ecdsa_recover(recovered,message)==c.ec_pubkey_create(key.secret)
compact,recid=c.ecdsa_recoverable_signature_serialize_compact(recovered)
assert c.ecdsa_recoverable_signature_parse_compact(compact,recid)==recovered
key=ec.PrivateKey(binascii.unhexlify('0000000000000000000000000000000000000000000000000000000000000002'))
message=binascii.unhexlify('a0a89b8424f6de8ec49de9fba31ec4ae6528ae4b5814d659124271992e66e936')
sig=key.sign(message,grind=False)
assert sig.serialize()==binascii.unhexlify('3044022038cadc9cbf7117d7f9bdfed778ed0e6d0912d1a552892cbc1b02fda84cfafd3102206dacd0b91dc3b08482892107278af7b5271d08670dd64a8788ccbca53f2e3891')
assert key.verify(sig,message)
assert not key.verify(sig,bytes(32))
assert ec.Signature.parse(sig.serialize()).serialize()==sig.serialize()
key=ec.PrivateKey(binascii.unhexlify('0000000000000000000000000000000000000000000000000000000000000002'))
message=binascii.unhexlify('a0a89b8424f6de8ec49de9fba31ec4ae6528ae4b5814d659124271992e66e936')
sig=key.sign(message,grind=True)
assert sig.serialize()==binascii.unhexlify('3044022038cadc9cbf7117d7f9bdfed778ed0e6d0912d1a552892cbc1b02fda84cfafd3102206dacd0b91dc3b08482892107278af7b5271d08670dd64a8788ccbca53f2e3891')
assert key.verify(sig,message)
assert not key.verify(sig,bytes(32))
assert ec.Signature.parse(sig.serialize()).serialize()==sig.serialize()
peer=ec.PrivateKey(binascii.unhexlify('0000000000000000000000000000000000000000000000000000000000000003'))
assert key.ecdh(peer.to_public())==binascii.unhexlify('c7d9ba2fa1496c81be20038e5c608f2fd5d0246d8643783730df6c2bbb855cb2')
assert key.ecdh(peer.to_public())==peer.ecdh(key.to_public())
recovered=c.ecdsa_sign_recoverable(message,key.secret)
assert c.ecdsa_recover(recovered,message)==c.ec_pubkey_create(key.secret)
compact,recid=c.ecdsa_recoverable_signature_serialize_compact(recovered)
assert c.ecdsa_recoverable_signature_parse_compact(compact,recid)==recovered
key=ec.PrivateKey(binascii.unhexlify('0000000000000000000000000000000000000000000000000000000000000003'))
message=binascii.unhexlify('407611eddc7b09afa18f42365c1fbc0e68ac3b665414f3e2bcec5063c2058473')
sig=key.sign(message,grind=False)
assert sig.serialize()==binascii.unhexlify('30450221008b2a5618e3d18cbe732afbf1fef3169dc72cc521c8d532bd2637dfb2e2adf59702200e46e90064e28c652f4ae31592699b7e487b53403e7d0aec688e0b79e962a2ec')
assert key.verify(sig,message)
assert not key.verify(sig,bytes(32))
assert ec.Signature.parse(sig.serialize()).serialize()==sig.serialize()
key=ec.PrivateKey(binascii.unhexlify('0000000000000000000000000000000000000000000000000000000000000003'))
message=binascii.unhexlify('407611eddc7b09afa18f42365c1fbc0e68ac3b665414f3e2bcec5063c2058473')
sig=key.sign(message,grind=True)
assert sig.serialize()==binascii.unhexlify('304402207c96bc747f028d9e1145e397a31bb1669328708f09282adbeea61abf5c0069280220182e856ecdb567e4a4b12136ca9d96dc0f0aca76b5715444e3bbfe3cb6eae9bf')
assert key.verify(sig,message)
assert not key.verify(sig,bytes(32))
assert ec.Signature.parse(sig.serialize()).serialize()==sig.serialize()
peer=ec.PrivateKey(binascii.unhexlify('0000000000000000000000000000000000000000000000000000000000000004'))
assert key.ecdh(peer.to_public())==binascii.unhexlify('7793f54cf24463535ec6738f7afe1984c128398182a5046cb006f4b6e89af817')
assert key.ecdh(peer.to_public())==peer.ecdh(key.to_public())
recovered=c.ecdsa_sign_recoverable(message,key.secret)
assert c.ecdsa_recover(recovered,message)==c.ec_pubkey_create(key.secret)
compact,recid=c.ecdsa_recoverable_signature_serialize_compact(recovered)
assert c.ecdsa_recoverable_signature_parse_compact(compact,recid)==recovered
key=ec.PrivateKey(binascii.unhexlify('0000000000000000000000000000000000000000000000000000000000000011'))
message=binascii.unhexlify('57b071b7bffc4bf63e2e26c72e21906d46de3f266545726c95f9e7b4e2ba40aa')
sig=key.sign(message,grind=False)
assert sig.serialize()==binascii.unhexlify('3045022100fae9a42d4733ac5ca3c03b6a2ddb115ac180863152398d26da276fb89dda955002207607ac5e0ec271728d8bda4a100fd513f0b290716de55055606d9be6748f9535')
assert key.verify(sig,message)
assert not key.verify(sig,bytes(32))
assert ec.Signature.parse(sig.serialize()).serialize()==sig.serialize()
key=ec.PrivateKey(binascii.unhexlify('0000000000000000000000000000000000000000000000000000000000000011'))
message=binascii.unhexlify('57b071b7bffc4bf63e2e26c72e21906d46de3f266545726c95f9e7b4e2ba40aa')
sig=key.sign(message,grind=True)
assert sig.serialize()==binascii.unhexlify('30440220572c57af1e30ea6506ef4beb37e6328fe8245e22d86f29d1588022f6cec7324602200091ba15712f41a8a39996e5a8bf6a28f1882643e8de49c3317a75174ecab635')
assert key.verify(sig,message)
assert not key.verify(sig,bytes(32))
assert ec.Signature.parse(sig.serialize()).serialize()==sig.serialize()
peer=ec.PrivateKey(binascii.unhexlify('0000000000000000000000000000000000000000000000000000000000000012'))
assert key.ecdh(peer.to_public())==binascii.unhexlify('1a67d27b5371c866dfc02df00de72bdb55e4f1d371b585dbfe85e9587edecd89')
assert key.ecdh(peer.to_public())==peer.ecdh(key.to_public())
recovered=c.ecdsa_sign_recoverable(message,key.secret)
assert c.ecdsa_recover(recovered,message)==c.ec_pubkey_create(key.secret)
compact,recid=c.ecdsa_recoverable_signature_serialize_compact(recovered)
assert c.ecdsa_recoverable_signature_parse_compact(compact,recid)==recovered
key=ec.PrivateKey(binascii.unhexlify('0000000000000000000000000000000000000000000000000000000000000100'))
message=binascii.unhexlify('06a77c33e5baf620758421e5aaf817104745cfe9e61921a280d65c7a16bb7232')
sig=key.sign(message,grind=False)
assert sig.serialize()==binascii.unhexlify('3045022100b5c4101c990f20e8a72c2b9b76636f5bb81add9a0957c7cee38f54d957ad7ca90220591a40fa88932d802b936d4a8cbe2993281228aa3cda243b571272fb8ca74952')
assert key.verify(sig,message)
assert not key.verify(sig,bytes(32))
assert ec.Signature.parse(sig.serialize()).serialize()==sig.serialize()
key=ec.PrivateKey(binascii.unhexlify('0000000000000000000000000000000000000000000000000000000000000100'))
message=binascii.unhexlify('06a77c33e5baf620758421e5aaf817104745cfe9e61921a280d65c7a16bb7232')
sig=key.sign(message,grind=True)
assert sig.serialize()==binascii.unhexlify('3044022073326883acec186b1385aea918eaa0beafcdb20ac52df8d45f5e3be187aa0647022056c04c302843c5013dec7929a0e3435d3af9da0f14b81b49828811d81d201eb4')
assert key.verify(sig,message)
assert not key.verify(sig,bytes(32))
assert ec.Signature.parse(sig.serialize()).serialize()==sig.serialize()
peer=ec.PrivateKey(binascii.unhexlify('0000000000000000000000000000000000000000000000000000000000000101'))
assert key.ecdh(peer.to_public())==binascii.unhexlify('0ce05f15339f8e96f7c11551cd2ece1c0b3a363687fb0d627f59d008c08bc286')
assert key.ecdh(peer.to_public())==peer.ecdh(key.to_public())
recovered=c.ecdsa_sign_recoverable(message,key.secret)
assert c.ecdsa_recover(recovered,message)==c.ec_pubkey_create(key.secret)
compact,recid=c.ecdsa_recoverable_signature_serialize_compact(recovered)
assert c.ecdsa_recoverable_signature_parse_compact(compact,recid)==recovered
key=ec.PrivateKey(binascii.unhexlify('0000000000000000000000000000000000000000000000000000000000010001'))
message=binascii.unhexlify('24eef549aeb4a5990d0d098ab7d9a9cbab6b9c246af5975cfbd3002c97ec89b3')
sig=key.sign(message,grind=False)
assert sig.serialize()==binascii.unhexlify('3045022100f10090949c2d70ed270e2b38ca7e5626a5273d320486bd9b67edc987b167208702203dd05192250865f73f8abcc32625945505358c5fdd0017a96e52fb0e92b225d6')
assert key.verify(sig,message)
assert not key.verify(sig,bytes(32))
assert ec.Signature.parse(sig.serialize()).serialize()==sig.serialize()
key=ec.PrivateKey(binascii.unhexlify('0000000000000000000000000000000000000000000000000000000000010001'))
message=binascii.unhexlify('24eef549aeb4a5990d0d098ab7d9a9cbab6b9c246af5975cfbd3002c97ec89b3')
sig=key.sign(message,grind=True)
assert sig.serialize()==binascii.unhexlify('3044022040d825381275699bf781fcf41fc1da88b796123ab863d1d096af04424f45b8ab022010123a82ea9454004eb951b3232785fd6e5d876510b96cf026bc18dcbc111c9a')
assert key.verify(sig,message)
assert not key.verify(sig,bytes(32))
assert ec.Signature.parse(sig.serialize()).serialize()==sig.serialize()
peer=ec.PrivateKey(binascii.unhexlify('0000000000000000000000000000000000000000000000000000000000010002'))
assert key.ecdh(peer.to_public())==binascii.unhexlify('a5559628c59e7dbacc22a135dc1a140ed91949febae292f6ef2f3fc3f1d5df2f')
assert key.ecdh(peer.to_public())==peer.ecdh(key.to_public())
recovered=c.ecdsa_sign_recoverable(message,key.secret)
assert c.ecdsa_recover(recovered,message)==c.ec_pubkey_create(key.secret)
compact,recid=c.ecdsa_recoverable_signature_serialize_compact(recovered)
assert c.ecdsa_recoverable_signature_parse_compact(compact,recid)==recovered
one=bytes(31)+bytes((1,))
two=bytes(31)+bytes((2,))
p=c.ec_pubkey_create(one)
assert c.ec_privkey_add(one,one)==two
assert c.ec_privkey_mul(two,two)==bytes(31)+bytes((4,))
assert c.ec_pubkey_mul(p,two)==c.ec_pubkey_create(two)
assert c.ec_pubkey_add(p,one)==c.ec_pubkey_create(two)
assert c.ec_pubkey_create(c.ec_privkey_negate(one))==c.ec_pubkey_negate(p)
for length in (0,1,31,33,63,65,96):
    invalid=bytes(length)
    for function in (c.ec_seckey_verify,c.ec_pubkey_create):
        try:function(invalid);assert False
        except ValueError:pass
for invalid in (bytes(32),b'\xff'*32):assert not c.ec_seckey_verify(invalid)
for invalid in (bytes(64),b'\xff'*64):
    try:c.ec_pubkey_serialize(invalid);assert False
    except ValueError:pass
for i in range(100):
    for invalid in (b'',b'0',bytes(71)):
        try:c.ecdsa_signature_parse_der(invalid);assert False
        except ValueError:pass
    assert c.ec_pubkey_serialize(c.ec_pubkey_create(one))==c.ec_pubkey_serialize(p)
try:c.ecdsa_sign(bytes(32),one,nonce_function=lambda:None);assert False
except FeatureUnavailable:pass
point=c.ec_pubkey_create(one)
message=bytes(32)
sig=c.ecdsa_sign(message,one)
order=int('fffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364141',16)
high=sig[:32]+(order-int.from_bytes(sig[32:],'big')).to_bytes(32,'big')
assert not c.ecdsa_verify(high,message,point)
assert c.ecdsa_signature_normalize(high)==sig
keypair=c.keypair_create(one)
assert c.schnorrsig_sign(message,keypair)==c.schnorrsig_sign(message,one)
try:c.schnorrsig_sign(message,keypair[:32]+bytes(64));assert False
except ValueError:pass
private=bytearray(one)
c.ec_privkey_tweak_add(private,one)
assert private==two
public=bytearray(point)
c.ec_pubkey_tweak_mul(public,two)
assert public==c.ec_pubkey_create(two)
c.context_randomize(None)
assert not c.context_status()['randomized']
for i in range(3):gc.collect()
assert camera.settings()['rust_heap_bytes']==baseline
print('@@PASS actual-native-curves-bip32-bip340-ecdsa-ecdh',(time.ticks_ms()-start)&0xffffffff)
