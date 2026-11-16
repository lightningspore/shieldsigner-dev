# SPDX-License-Identifier: MIT
# PUBLIC known mnemonic/passphrase and independent CPython results only.
from seedsigner_port.seed import Seed
from seedsigner_port import embit_utils
from seedsigner_port.encode_qr import StaticXpubQrEncoder, SpecterLegacyXPubQrEncoder
from seedsigner_port.settings_schema import SettingsConstants as C
from embit import bip32
import gc, machine, time

record = machine.last_reset()
print('@@XPUB_RESET_BEFORE', record)
assert record is None or record['reason'] == 2
machine.clear_reset_record()
machine.set_reset_marker(0x58505542)
words = [
    'abandon',
    'amount',
    'liar',
    'amount',
    'expire',
    'adjust',
    'cage',
    'candy',
    'arch',
    'gather',
    'drum',
    'buyer',
]
cases = [
    (
        'M',
        'ss',
        'leg',
        0,
        "m/44'/0'/0'",
        'xpub6CrwKFeSbUCEpqk12HoBjTjpW4AA9M8UUdadn3zs6c2gbcdu9uhbmNKMMdxatEMhQozvcrV4g5FpqcimP56tRPczob39n9fLgRwtqnfndf3',
        "[4f4fbd02/44'/0'/0']xpub6CrwKFeSbUCEpqk12HoBjTjpW4AA9M8UUdadn3zs6c2gbcdu9uhbmNKMMdxatEMhQozvcrV4g5FpqcimP56tRPczob39n9fLgRwtqnfndf3",
        [
            (0, False, '1KboJce5wveWRd7KBR38vjcGHdwgJNkWRr'),
            (7, True, '1L98JCqhG1dx3poiy9s24TBGygDgyXpjwz'),
        ],
    ),
    (
        'M',
        'ss',
        'leg',
        7,
        "m/44'/0'/7'",
        'xpub6CrwKFeSbUCF7NwWFyy2kLRLqQ9q43ZDe5m9NaDdhwMBVt7nPZ7uxwh22sXarwD2o5ZyQfDGiFaLmcYTJYtuuUPENwa9DXZfgDX81XB7ufn',
        "[4f4fbd02/44'/0'/7']xpub6CrwKFeSbUCF7NwWFyy2kLRLqQ9q43ZDe5m9NaDdhwMBVt7nPZ7uxwh22sXarwD2o5ZyQfDGiFaLmcYTJYtuuUPENwa9DXZfgDX81XB7ufn",
        [
            (0, False, '1KfZZxcBwhsjgWWiXrma4TRxrJKC1woXS8'),
            (7, True, '12j71wZVnc9idX8agZnV5G4uQnuqp15u5J'),
        ],
    ),
    (
        'M',
        'ss',
        'nes',
        0,
        "m/49'/0'/0'",
        'ypub6YGykLeYmwKdjZQFqUmr4xfeFKZgmex8CphZ5nhJUvWkGfkfoodk5BhrEdp7kEozzmkqezEkb79GP8aVmys4JQWvo1A6EtF5CBPu6aniZTa',
        "[4f4fbd02/49'/0'/0']ypub6YGykLeYmwKdjZQFqUmr4xfeFKZgmex8CphZ5nhJUvWkGfkfoodk5BhrEdp7kEozzmkqezEkb79GP8aVmys4JQWvo1A6EtF5CBPu6aniZTa",
        [
            (0, False, '381qhvXEmERwKWL9o8X7APnjbKAJDu7MJ3'),
            (7, True, '3LH7oN8gKyzkSkbtWR1imuCE3eSrSw1T9E'),
        ],
    ),
    (
        'M',
        'ss',
        'nes',
        7,
        "m/49'/0'/7'",
        'ypub6YGykLeYmwKe53TZWSymkZzyRrUejNyZrpLoTL7pabzPB5m3hyymUNW8usKmaZGpU6rYaBAKhgHWzr95jQuPWprBcJG79Nmi9NWZMbsF62v',
        "[4f4fbd02/49'/0'/7']ypub6YGykLeYmwKe53TZWSymkZzyRrUejNyZrpLoTL7pabzPB5m3hyymUNW8usKmaZGpU6rYaBAKhgHWzr95jQuPWprBcJG79Nmi9NWZMbsF62v",
        [
            (0, False, '3NsJ1n5cheisNUB8SM9i4JewbhyUgyR7oA'),
            (7, True, '34mvwxbCwsdnsPEoTB21KRiwEfXLBvWZzg'),
        ],
    ),
    (
        'M',
        'ss',
        'nat',
        0,
        "m/84'/0'/0'",
        'zpub6s7nZx8HjMQ8mDGtp5XTgbRXhYa9sUBdojXGEEYaKX4xcGGv9QSJNeBSmYyK2vVNsZYTLxvybUffnJpu2naZ9LY33YDUu9qd52D7Rk7owcd',
        "[4f4fbd02/84'/0'/0']zpub6s7nZx8HjMQ8mDGtp5XTgbRXhYa9sUBdojXGEEYaKX4xcGGv9QSJNeBSmYyK2vVNsZYTLxvybUffnJpu2naZ9LY33YDUu9qd52D7Rk7owcd",
        [
            (0, False, 'bc1q5gxzrugds23phf3xd2rw097sv0zaw43ql88nvd'),
            (7, True, 'bc1q528lyx5hlkfglz82eymmymeqef2h784e869san'),
        ],
    ),
    (
        'M',
        'ss',
        'nat',
        7,
        "m/84'/0'/7'",
        'zpub6s7nZx8HjMQ95TvEvYQR6pnhvVvD88MyEVjRFMracU2UtmZvHPh5TPGf5WgoGLhbv88pUn32tynM8Xrkj5y1X1fUydzWmx332grZsmAU75q',
        "[4f4fbd02/84'/0'/7']zpub6s7nZx8HjMQ95TvEvYQR6pnhvVvD88MyEVjRFMracU2UtmZvHPh5TPGf5WgoGLhbv88pUn32tynM8Xrkj5y1X1fUydzWmx332grZsmAU75q",
        [
            (0, False, 'bc1q8zy2wedjjtdlhfqa4au0zcx27xlunjsgff8v8k'),
            (7, True, 'bc1qv5dukfq8656jr5qpq6978g9jxaz38799nnsnkq'),
        ],
    ),
    (
        'M',
        'ss',
        'tr',
        0,
        "m/86'/0'/0'",
        'xpub6CiWF9aPFjaQRZs8q4RPBTSAnnigDgCZBcALdzDSuGFSVfTUCGVLtbshXzj3JUPawbQfH4D8ysHB5Nfk71NbhAtGJWW8Sw7ENv6bHmzbUJG',
        "[4f4fbd02/86'/0'/0']xpub6CiWF9aPFjaQRZs8q4RPBTSAnnigDgCZBcALdzDSuGFSVfTUCGVLtbshXzj3JUPawbQfH4D8ysHB5Nfk71NbhAtGJWW8Sw7ENv6bHmzbUJG",
        [
            (0, False, 'bc1p2cv9wg04gk0zalydr8kly9khd4t8np56unrqj0gc20qzm0rc32ascsh7qw'),
            (7, True, 'bc1p396gyadqc00d93wqv703c9cq5nlwsj4v24yc2d32xnj57rvm0u8q6amlyp'),
        ],
    ),
    (
        'M',
        'ss',
        'tr',
        7,
        "m/86'/0'/7'",
        'xpub6CiWF9aPFjaQjr1oE9FRpu43kM6Gmv6QjaTQqy4ADgPSYjazDrgCmG129AaHaTMPZiMxxkRdpYe9aaha5wkTr7iLsSLaouyAYkpLFZbdhQT',
        "[4f4fbd02/86'/0'/7']xpub6CiWF9aPFjaQjr1oE9FRpu43kM6Gmv6QjaTQqy4ADgPSYjazDrgCmG129AaHaTMPZiMxxkRdpYe9aaha5wkTr7iLsSLaouyAYkpLFZbdhQT",
        [
            (0, False, 'bc1p3ltx4ezs6af97vlh7fzt5rnw50t2lgd3rxjy8a9yezlucj7k75csruwtvp'),
            (7, True, 'bc1pmrj744k3p8shs62pynylfkkel6zs3lc7vmw6dydrptgr7cp2nhds7fxhxd'),
        ],
    ),
    (
        'M',
        'ms',
        'leg',
        0,
        "m/45'",
        'xpub68UJtQx3RHwkmuh8szXb4ZpWm58b2gAcBZfsiHiTYLQMuu5EYUQ2pEAK5ywBz18aqs9dXNSS3bfkj7p7RoyRM5LqLTbUoHA1e4nFmrrupWf',
        "[4f4fbd02/45']xpub68UJtQx3RHwkmuh8szXb4ZpWm58b2gAcBZfsiHiTYLQMuu5EYUQ2pEAK5ywBz18aqs9dXNSS3bfkj7p7RoyRM5LqLTbUoHA1e4nFmrrupWf",
        [],
    ),
    (
        'M',
        'ms',
        'leg',
        7,
        "m/45'",
        'xpub68UJtQx3RHwkmuh8szXb4ZpWm58b2gAcBZfsiHiTYLQMuu5EYUQ2pEAK5ywBz18aqs9dXNSS3bfkj7p7RoyRM5LqLTbUoHA1e4nFmrrupWf',
        "[4f4fbd02/45']xpub68UJtQx3RHwkmuh8szXb4ZpWm58b2gAcBZfsiHiTYLQMuu5EYUQ2pEAK5ywBz18aqs9dXNSS3bfkj7p7RoyRM5LqLTbUoHA1e4nFmrrupWf",
        [],
    ),
    (
        'M',
        'ms',
        'nes',
        0,
        "m/48'/0'/0'/1'",
        'Ypub6kBhRPEZhVE2rLPdX3L5iSdx5tx72kmwMT3joxrTaZEWtD9uHdrZZbsfBjuqhRzVuf1iF9gxLSDEtYm5bGkaCcAYF3SLF3UB2JeBQvXhZRd',
        "[4f4fbd02/48'/0'/0'/1']Ypub6kBhRPEZhVE2rLPdX3L5iSdx5tx72kmwMT3joxrTaZEWtD9uHdrZZbsfBjuqhRzVuf1iF9gxLSDEtYm5bGkaCcAYF3SLF3UB2JeBQvXhZRd",
        [],
    ),
    (
        'M',
        'ms',
        'nes',
        7,
        "m/48'/0'/7'/1'",
        'Ypub6jWNvhySpZ9FDyW7e2EU6nuFipfokWwx6dNKdGzWTv65HpuZ27Nv3UG6P4B9wZzz1xNEkoygaSCZGwAXmoSCjeUjTM7bzNsJXC3MWQfdjjv',
        "[4f4fbd02/48'/0'/7'/1']Ypub6jWNvhySpZ9FDyW7e2EU6nuFipfokWwx6dNKdGzWTv65HpuZ27Nv3UG6P4B9wZzz1xNEkoygaSCZGwAXmoSCjeUjTM7bzNsJXC3MWQfdjjv",
        [],
    ),
    (
        'M',
        'ms',
        'nat',
        0,
        "m/48'/0'/0'/2'",
        'Zpub751xj3uUrAmWkxyK1PLTVtYz1hXSUVQgBCxrZbktTS2yQSVvkjQpdKnuNuYwk8boWesgNwbzJ9gfdfxW7Ty9r4Hr47tDMzG3CNFXyqCwXe4',
        "[4f4fbd02/48'/0'/0'/2']Zpub751xj3uUrAmWkxyK1PLTVtYz1hXSUVQgBCxrZbktTS2yQSVvkjQpdKnuNuYwk8boWesgNwbzJ9gfdfxW7Ty9r4Hr47tDMzG3CNFXyqCwXe4",
        [],
    ),
    (
        'M',
        'ms',
        'nat',
        7,
        "m/48'/0'/7'/2'",
        'Zpub74LeENeMyEgj7xnHhmxaWVPCvZgchddcnhyoRdsezeJRt568zaKREvSEuQnRHhYfcGyM2jvJkyM2ynt5M3G433g4GTqH1GHKsa3hucLq9zA',
        "[4f4fbd02/48'/0'/7'/2']Zpub74LeENeMyEgj7xnHhmxaWVPCvZgchddcnhyoRdsezeJRt568zaKREvSEuQnRHhYfcGyM2jvJkyM2ynt5M3G433g4GTqH1GHKsa3hucLq9zA",
        [],
    ),
    (
        'T',
        'ss',
        'leg',
        0,
        "m/44'/1'/0'",
        'tpubDDkWPe374AWiH3QWE49ShEUXZYJWqn9P3pmCwNgh8hMbfcWKwcZhY2TUje3xkSrBhxJfjeXKrwDDgHorZAxxmm8jzpSvrfcb8sxTgnDBaUb',
        "[4f4fbd02/44'/1'/0']tpubDDkWPe374AWiH3QWE49ShEUXZYJWqn9P3pmCwNgh8hMbfcWKwcZhY2TUje3xkSrBhxJfjeXKrwDDgHorZAxxmm8jzpSvrfcb8sxTgnDBaUb",
        [
            (0, False, 'mjUJveDE9BZp1gZMxemLia3GgAPYLXisU6'),
            (7, True, 'mugam7uUFHmtakGW3AgmJ9yVTAG4yDsKo4'),
        ],
    ),
    (
        'T',
        'ss',
        'leg',
        7,
        "m/44'/1'/7'",
        'tpubDDkWPe374AWia6bVr49EiNofkdKTDZSbxyq5kyEoJJLwecGETd2byMeStNmdZnidipVTbngbBeYQSnjE1RPXnePPNjaJQ9m6jkdhMRuMP5M',
        "[4f4fbd02/44'/1'/7']tpubDDkWPe374AWia6bVr49EiNofkdKTDZSbxyq5kyEoJJLwecGETd2byMeStNmdZnidipVTbngbBeYQSnjE1RPXnePPNjaJQ9m6jkdhMRuMP5M",
        [
            (0, False, 'mwCYnUBsS3Kf1oiayepaBoKvLbpH69JJ1j'),
            (7, True, 'mtgm57x1Z5MTMSGstnu3Lfb6J4cfZ5u55p'),
        ],
    ),
    (
        'T',
        'ss',
        'nes',
        0,
        "m/49'/1'/0'",
        'upub5EjbpQTDURkYsYY86zVAsKD8QTDYGmisQbsgL7nbbxdGTZoWpR7fSbkUkuQvrYQbsg5DZvrCEYkMWBTwMH4U3ecDmEaEbFARKVof6jkaCAg',
        "[4f4fbd02/49'/1'/0']upub5EjbpQTDURkYsYY86zVAsKD8QTDYGmisQbsgL7nbbxdGTZoWpR7fSbkUkuQvrYQbsg5DZvrCEYkMWBTwMH4U3ecDmEaEbFARKVof6jkaCAg",
        [
            (0, False, '2NB4JGupiZd5Cdw2Ui3ThDkXmHA13dPpWWn'),
            (7, True, '2N4gptweeUzKL875vDzVBcvyM6Wiy522S7Y'),
        ],
    ),
    (
        'T',
        'ss',
        'nes',
        7,
        "m/49'/1'/7'",
        'upub5EjbpQTDURkZALuPYcn64pgrhU3ucqLoQtsqmAsoaM6WUwxjttGpHomp4PfyGJr3hvoqkGE7ZGMWGnZi5Bm9exV28z2FVpXxV8Aofomgzq8',
        "[4f4fbd02/49'/1'/7']upub5EjbpQTDURkZALuPYcn64pgrhU3ucqLoQtsqmAsoaM6WUwxjttGpHomp4PfyGJr3hvoqkGE7ZGMWGnZi5Bm9exV28z2FVpXxV8Aofomgzq8",
        [
            (0, False, '2N2KPQazkvpEyagQy3EEUFFY9FvzJ2W81Ua'),
            (7, True, '2NEWKgo3Y76e4oTYTPF2XycgVd8D5AYVZ9x'),
        ],
    ),
    (
        'T',
        'ss',
        'nat',
        0,
        "m/84'/1'/0'",
        'vpub5Y15X1sbL6WDU7ukgvY7ptchJcmeWSBwxWjKjcZRYt5kjYrMzyAic9GvtQhMbdrU6BFSiTDsC668AdPzpnwooKuMvC8EtFfn6xA2Rcgd22D',
        "[4f4fbd02/84'/1'/0']vpub5Y15X1sbL6WDU7ukgvY7ptchJcmeWSBwxWjKjcZRYt5kjYrMzyAic9GvtQhMbdrU6BFSiTDsC668AdPzpnwooKuMvC8EtFfn6xA2Rcgd22D",
        [
            (0, False, 'tb1q4p5heuz43c3fl2zxrlpalhhrns988x3ujs7xnf'),
            (7, True, 'tb1q0qtn6e2l3aep250hlac25ljqk3we7e0eysr0m0'),
        ],
    ),
    (
        'T',
        'ss',
        'nat',
        7,
        "m/84'/1'/7'",
        'vpub5Y15X1sbL6WDmWVujJ8vXXFWdHDemtVY3XSLMrUkfCT9YCPFZpC3EZXwC57rgpKGAQKkVnGKvqdnD5YdkEgKtvyXrz21eSdG5w6VM2aDrf5',
        "[4f4fbd02/84'/1'/7']vpub5Y15X1sbL6WDmWVujJ8vXXFWdHDemtVY3XSLMrUkfCT9YCPFZpC3EZXwC57rgpKGAQKkVnGKvqdnD5YdkEgKtvyXrz21eSdG5w6VM2aDrf5",
        [
            (0, False, 'tb1q4qcxgu5h3q4j05qps28zxchryqx05h24ddm2d0'),
            (7, True, 'tb1qznq2xtgszfuz6pw0y2y43w2xzyzetc4rw2j3dw'),
        ],
    ),
    (
        'T',
        'ss',
        'tr',
        0,
        "m/86'/1'/0'",
        'tpubDDch1E4wVZVKw63LJkbRSkATDSbcyt5tFv1Rmmh6eamPDnpCK97QHXb257q4vFhWyuq8YZcEtKfvE4Ftf6of2L4RA6ikwYLSCN4RHU73dAT',
        "[4f4fbd02/86'/1'/0']tpubDDch1E4wVZVKw63LJkbRSkATDSbcyt5tFv1Rmmh6eamPDnpCK97QHXb257q4vFhWyuq8YZcEtKfvE4Ftf6of2L4RA6ikwYLSCN4RHU73dAT",
        [
            (0, False, 'tb1pxxhmh0pd8dewwv4308h27ryd8nmdnchszsrfvl54q7uqe8xgrhms79plk6'),
            (7, True, 'tb1pshzd97veq54kjhu66mgk7d0jr3nxvy9lu0x5hjjyqt978j3y2lxqufqquq'),
        ],
    ),
    (
        'T',
        'ss',
        'tr',
        7,
        "m/86'/1'/7'",
        'tpubDDch1E4wVZVLESzD93PQNKPDpPRpCHGdjYs9sbGQSkQC4d3ygijnP6rXPCSNDtoRwPWkTw7LNdP183rEMbcAAzcptvSvRQgpNy9r1yJ7fMz',
        "[4f4fbd02/86'/1'/7']tpubDDch1E4wVZVLESzD93PQNKPDpPRpCHGdjYs9sbGQSkQC4d3ygijnP6rXPCSNDtoRwPWkTw7LNdP183rEMbcAAzcptvSvRQgpNy9r1yJ7fMz",
        [
            (0, False, 'tb1pplwmkv3sjlnvvz74seuwp578h3uxx92cjely4tl2ruy9ac0n69wsyvdmvm'),
            (7, True, 'tb1pmmqtx7jg2pvf0c45veuayydskyy9908tr7lk24raxl5lazhw8q7qpy8lmf'),
        ],
    ),
    (
        'T',
        'ms',
        'leg',
        0,
        "m/45'",
        'tpubD8qwQemj8ZuD3hszLBWgGV9t6CEF24ffjCGB4qmbtFAFfBjwchF7xfq9L21yWW5pdmgY8wxJahVoRJJipfpfEWo8Q4LnUopFE2NfXsYADhG',
        "[4f4fbd02/45']tpubD8qwQemj8ZuD3hszLBWgGV9t6CEF24ffjCGB4qmbtFAFfBjwchF7xfq9L21yWW5pdmgY8wxJahVoRJJipfpfEWo8Q4LnUopFE2NfXsYADhG",
        [],
    ),
    (
        'T',
        'ms',
        'leg',
        7,
        "m/45'",
        'tpubD8qwQemj8ZuD3hszLBWgGV9t6CEF24ffjCGB4qmbtFAFfBjwchF7xfq9L21yWW5pdmgY8wxJahVoRJJipfpfEWo8Q4LnUopFE2NfXsYADhG',
        "[4f4fbd02/45']tpubD8qwQemj8ZuD3hszLBWgGV9t6CEF24ffjCGB4qmbtFAFfBjwchF7xfq9L21yWW5pdmgY8wxJahVoRJJipfpfEWo8Q4LnUopFE2NfXsYADhG",
        [],
    ),
    (
        'T',
        'ms',
        'nes',
        0,
        "m/48'/1'/0'/1'",
        'Upub5Tkm6uvqCSxQh7fdZroyggx62n1KbbjY4hWYYhqMmX57T1YAzPc5rDy2sVRonQLh4VUzKCYxHrCmGjABKHcTvJtGvhXoFbJ95XrgATkTxiu',
        "[4f4fbd02/48'/1'/0'/1']Upub5Tkm6uvqCSxQh7fdZroyggx62n1KbbjY4hWYYhqMmX57T1YAzPc5rDy2sVRonQLh4VUzKCYxHrCmGjABKHcTvJtGvhXoFbJ95XrgATkTxiu",
        [],
    ),
    (
        'T',
        'ms',
        'nes',
        7,
        "m/48'/1'/7'/1'",
        'Upub5SUNJtc5HprtJQCMNFb2KsGKN7uau4Z9toPvE37vcYHTbu9B6B7Ybu28PMMxajbaongGU27jHYbX5zFvgXnNgCy3gVFBjWuqjc7kxwLUf8K',
        "[4f4fbd02/48'/1'/7'/1']Upub5SUNJtc5HprtJQCMNFb2KsGKN7uau4Z9toPvE37vcYHTbu9B6B7Ybu28PMMxajbaongGU27jHYbX5zFvgXnNgCy3gVFBjWuqjc7kxwLUf8K",
        [],
    ),
    (
        'T',
        'ms',
        'nat',
        0,
        "m/48'/1'/0'/2'",
        'Vpub5nb2QabkM8VtZkaZFaoPpVoumNceZUG5ouUp5X9gTsRo2jAjRGABDsNwxdUuZhaZTsNipowPX59tjWfYGTPxPQDz4pWywUnLGsPBNhXp6My',
        "[4f4fbd02/48'/1'/0'/2']Vpub5nb2QabkM8VtZkaZFaoPpVoumNceZUG5ouUp5X9gTsRo2jAjRGABDsNwxdUuZhaZTsNipowPX59tjWfYGTPxPQDz4pWywUnLGsPBNhXp6My",
        [],
    ),
    (
        'T',
        'ms',
        'nat',
        7,
        "m/48'/1'/7'/2'",
        'Vpub5mJdcZGzSWQNB6s15ht2Rw2WFjjASED9JXxD39AhfPxzmsncoR2ngU97f5gPN37EtgiMZD5syiHeTLcAP2ZAAC7tztJaJY3DZ7vimHg1WZ7',
        "[4f4fbd02/48'/1'/7'/2']Vpub5mJdcZGzSWQNB6s15ht2Rw2WFjjASED9JXxD39AhfPxzmsncoR2ngU97f5gPN37EtgiMZD5syiHeTLcAP2ZAAC7tztJaJY3DZ7vimHg1WZ7",
        [],
    ),
    (
        'R',
        'ss',
        'leg',
        0,
        "m/44'/1'/0'",
        'tpubDDkWPe374AWiH3QWE49ShEUXZYJWqn9P3pmCwNgh8hMbfcWKwcZhY2TUje3xkSrBhxJfjeXKrwDDgHorZAxxmm8jzpSvrfcb8sxTgnDBaUb',
        "[4f4fbd02/44'/1'/0']tpubDDkWPe374AWiH3QWE49ShEUXZYJWqn9P3pmCwNgh8hMbfcWKwcZhY2TUje3xkSrBhxJfjeXKrwDDgHorZAxxmm8jzpSvrfcb8sxTgnDBaUb",
        [
            (0, False, 'mjUJveDE9BZp1gZMxemLia3GgAPYLXisU6'),
            (7, True, 'mugam7uUFHmtakGW3AgmJ9yVTAG4yDsKo4'),
        ],
    ),
    (
        'R',
        'ss',
        'leg',
        7,
        "m/44'/1'/7'",
        'tpubDDkWPe374AWia6bVr49EiNofkdKTDZSbxyq5kyEoJJLwecGETd2byMeStNmdZnidipVTbngbBeYQSnjE1RPXnePPNjaJQ9m6jkdhMRuMP5M',
        "[4f4fbd02/44'/1'/7']tpubDDkWPe374AWia6bVr49EiNofkdKTDZSbxyq5kyEoJJLwecGETd2byMeStNmdZnidipVTbngbBeYQSnjE1RPXnePPNjaJQ9m6jkdhMRuMP5M",
        [
            (0, False, 'mwCYnUBsS3Kf1oiayepaBoKvLbpH69JJ1j'),
            (7, True, 'mtgm57x1Z5MTMSGstnu3Lfb6J4cfZ5u55p'),
        ],
    ),
    (
        'R',
        'ss',
        'nes',
        0,
        "m/49'/1'/0'",
        'upub5EjbpQTDURkYsYY86zVAsKD8QTDYGmisQbsgL7nbbxdGTZoWpR7fSbkUkuQvrYQbsg5DZvrCEYkMWBTwMH4U3ecDmEaEbFARKVof6jkaCAg',
        "[4f4fbd02/49'/1'/0']upub5EjbpQTDURkYsYY86zVAsKD8QTDYGmisQbsgL7nbbxdGTZoWpR7fSbkUkuQvrYQbsg5DZvrCEYkMWBTwMH4U3ecDmEaEbFARKVof6jkaCAg",
        [
            (0, False, '2NB4JGupiZd5Cdw2Ui3ThDkXmHA13dPpWWn'),
            (7, True, '2N4gptweeUzKL875vDzVBcvyM6Wiy522S7Y'),
        ],
    ),
    (
        'R',
        'ss',
        'nes',
        7,
        "m/49'/1'/7'",
        'upub5EjbpQTDURkZALuPYcn64pgrhU3ucqLoQtsqmAsoaM6WUwxjttGpHomp4PfyGJr3hvoqkGE7ZGMWGnZi5Bm9exV28z2FVpXxV8Aofomgzq8',
        "[4f4fbd02/49'/1'/7']upub5EjbpQTDURkZALuPYcn64pgrhU3ucqLoQtsqmAsoaM6WUwxjttGpHomp4PfyGJr3hvoqkGE7ZGMWGnZi5Bm9exV28z2FVpXxV8Aofomgzq8",
        [
            (0, False, '2N2KPQazkvpEyagQy3EEUFFY9FvzJ2W81Ua'),
            (7, True, '2NEWKgo3Y76e4oTYTPF2XycgVd8D5AYVZ9x'),
        ],
    ),
    (
        'R',
        'ss',
        'nat',
        0,
        "m/84'/1'/0'",
        'vpub5Y15X1sbL6WDU7ukgvY7ptchJcmeWSBwxWjKjcZRYt5kjYrMzyAic9GvtQhMbdrU6BFSiTDsC668AdPzpnwooKuMvC8EtFfn6xA2Rcgd22D',
        "[4f4fbd02/84'/1'/0']vpub5Y15X1sbL6WDU7ukgvY7ptchJcmeWSBwxWjKjcZRYt5kjYrMzyAic9GvtQhMbdrU6BFSiTDsC668AdPzpnwooKuMvC8EtFfn6xA2Rcgd22D",
        [
            (0, False, 'bcrt1q4p5heuz43c3fl2zxrlpalhhrns988x3use8tyq'),
            (7, True, 'bcrt1q0qtn6e2l3aep250hlac25ljqk3we7e0exe6zvx'),
        ],
    ),
    (
        'R',
        'ss',
        'nat',
        7,
        "m/84'/1'/7'",
        'vpub5Y15X1sbL6WDmWVujJ8vXXFWdHDemtVY3XSLMrUkfCT9YCPFZpC3EZXwC57rgpKGAQKkVnGKvqdnD5YdkEgKtvyXrz21eSdG5w6VM2aDrf5',
        "[4f4fbd02/84'/1'/7']vpub5Y15X1sbL6WDmWVujJ8vXXFWdHDemtVY3XSLMrUkfCT9YCPFZpC3EZXwC57rgpKGAQKkVnGKvqdnD5YdkEgKtvyXrz21eSdG5w6VM2aDrf5",
        [
            (0, False, 'bcrt1q4qcxgu5h3q4j05qps28zxchryqx05h240yz86x'),
            (7, True, 'bcrt1qznq2xtgszfuz6pw0y2y43w2xzyzetc4rvrtu68'),
        ],
    ),
    (
        'R',
        'ss',
        'tr',
        0,
        "m/86'/1'/0'",
        'tpubDDch1E4wVZVKw63LJkbRSkATDSbcyt5tFv1Rmmh6eamPDnpCK97QHXb257q4vFhWyuq8YZcEtKfvE4Ftf6of2L4RA6ikwYLSCN4RHU73dAT',
        "[4f4fbd02/86'/1'/0']tpubDDch1E4wVZVKw63LJkbRSkATDSbcyt5tFv1Rmmh6eamPDnpCK97QHXb257q4vFhWyuq8YZcEtKfvE4Ftf6of2L4RA6ikwYLSCN4RHU73dAT",
        [
            (0, False, 'bcrt1pxxhmh0pd8dewwv4308h27ryd8nmdnchszsrfvl54q7uqe8xgrhmsnuterq'),
            (7, True, 'bcrt1pshzd97veq54kjhu66mgk7d0jr3nxvy9lu0x5hjjyqt978j3y2lxq3s2xf6'),
        ],
    ),
    (
        'R',
        'ss',
        'tr',
        7,
        "m/86'/1'/7'",
        'tpubDDch1E4wVZVLESzD93PQNKPDpPRpCHGdjYs9sbGQSkQC4d3ygijnP6rXPCSNDtoRwPWkTw7LNdP183rEMbcAAzcptvSvRQgpNy9r1yJ7fMz',
        "[4f4fbd02/86'/1'/7']tpubDDch1E4wVZVLESzD93PQNKPDpPRpCHGdjYs9sbGQSkQC4d3ygijnP6rXPCSNDtoRwPWkTw7LNdP183rEMbcAAzcptvSvRQgpNy9r1yJ7fMz",
        [
            (0, False, 'bcrt1pplwmkv3sjlnvvz74seuwp578h3uxx92cjely4tl2ruy9ac0n69wsf48aep'),
            (7, True, 'bcrt1pmmqtx7jg2pvf0c45veuayydskyy9908tr7lk24raxl5lazhw8q7qvadewn'),
        ],
    ),
    (
        'R',
        'ms',
        'leg',
        0,
        "m/45'",
        'tpubD8qwQemj8ZuD3hszLBWgGV9t6CEF24ffjCGB4qmbtFAFfBjwchF7xfq9L21yWW5pdmgY8wxJahVoRJJipfpfEWo8Q4LnUopFE2NfXsYADhG',
        "[4f4fbd02/45']tpubD8qwQemj8ZuD3hszLBWgGV9t6CEF24ffjCGB4qmbtFAFfBjwchF7xfq9L21yWW5pdmgY8wxJahVoRJJipfpfEWo8Q4LnUopFE2NfXsYADhG",
        [],
    ),
    (
        'R',
        'ms',
        'leg',
        7,
        "m/45'",
        'tpubD8qwQemj8ZuD3hszLBWgGV9t6CEF24ffjCGB4qmbtFAFfBjwchF7xfq9L21yWW5pdmgY8wxJahVoRJJipfpfEWo8Q4LnUopFE2NfXsYADhG',
        "[4f4fbd02/45']tpubD8qwQemj8ZuD3hszLBWgGV9t6CEF24ffjCGB4qmbtFAFfBjwchF7xfq9L21yWW5pdmgY8wxJahVoRJJipfpfEWo8Q4LnUopFE2NfXsYADhG",
        [],
    ),
    (
        'R',
        'ms',
        'nes',
        0,
        "m/48'/1'/0'/1'",
        'Upub5Tkm6uvqCSxQh7fdZroyggx62n1KbbjY4hWYYhqMmX57T1YAzPc5rDy2sVRonQLh4VUzKCYxHrCmGjABKHcTvJtGvhXoFbJ95XrgATkTxiu',
        "[4f4fbd02/48'/1'/0'/1']Upub5Tkm6uvqCSxQh7fdZroyggx62n1KbbjY4hWYYhqMmX57T1YAzPc5rDy2sVRonQLh4VUzKCYxHrCmGjABKHcTvJtGvhXoFbJ95XrgATkTxiu",
        [],
    ),
    (
        'R',
        'ms',
        'nes',
        7,
        "m/48'/1'/7'/1'",
        'Upub5SUNJtc5HprtJQCMNFb2KsGKN7uau4Z9toPvE37vcYHTbu9B6B7Ybu28PMMxajbaongGU27jHYbX5zFvgXnNgCy3gVFBjWuqjc7kxwLUf8K',
        "[4f4fbd02/48'/1'/7'/1']Upub5SUNJtc5HprtJQCMNFb2KsGKN7uau4Z9toPvE37vcYHTbu9B6B7Ybu28PMMxajbaongGU27jHYbX5zFvgXnNgCy3gVFBjWuqjc7kxwLUf8K",
        [],
    ),
    (
        'R',
        'ms',
        'nat',
        0,
        "m/48'/1'/0'/2'",
        'Vpub5nb2QabkM8VtZkaZFaoPpVoumNceZUG5ouUp5X9gTsRo2jAjRGABDsNwxdUuZhaZTsNipowPX59tjWfYGTPxPQDz4pWywUnLGsPBNhXp6My',
        "[4f4fbd02/48'/1'/0'/2']Vpub5nb2QabkM8VtZkaZFaoPpVoumNceZUG5ouUp5X9gTsRo2jAjRGABDsNwxdUuZhaZTsNipowPX59tjWfYGTPxPQDz4pWywUnLGsPBNhXp6My",
        [],
    ),
    (
        'R',
        'ms',
        'nat',
        7,
        "m/48'/1'/7'/2'",
        'Vpub5mJdcZGzSWQNB6s15ht2Rw2WFjjASED9JXxD39AhfPxzmsncoR2ngU97f5gPN37EtgiMZD5syiHeTLcAP2ZAAC7tztJaJY3DZ7vimHg1WZ7',
        "[4f4fbd02/48'/1'/7'/2']Vpub5mJdcZGzSWQNB6s15ht2Rw2WFjjASED9JXxD39AhfPxzmsncoR2ngU97f5gPN37EtgiMZD5syiHeTLcAP2ZAAC7tztJaJY3DZ7vimHg1WZ7",
        [],
    ),
]
seed = Seed(words, passphrase='PUBLIC')
started = time.ticks_ms()
for number, (network, sig, kind, account, path, expected, payload, addresses) in enumerate(cases):
    assert embit_utils.get_standard_derivation_path(network, sig, kind, account) == path
    encoder = StaticXpubQrEncoder(seed=seed, derivation=path, network=network, sig_type=sig)
    assert encoder.xpub_base58 == expected and encoder.next_part() == payload
    assert encoder.cur_part() == payload and encoder.seq_len() == 1 and encoder.is_complete
    for index, change, address in addresses:
        assert (
            embit_utils.get_single_sig_address(
                encoder.xpub, kind, index, change, C.map_network_to_embit(network)
            )
            == address
        )
    for density in (C.DENSITY__LOW, C.DENSITY__MEDIUM, C.DENSITY__HIGH):
        animated = SpecterLegacyXPubQrEncoder(
            seed=seed, derivation=path, network=network, sig_type=sig, qr_density=density
        )
        parts = [animated.next_part() for _ in range(animated.seq_len())]
        assert (
            ''.join(
                part.split(' ', 1)[1] if part.startswith('p') and ' ' in part else part
                for part in parts
            )
            == payload
        )
        assert animated.is_complete and animated.next_part() == parts[0]
        animated.restart()
        assert animated.next_part() == parts[0]
    gc.collect()
    print('@@PASS public-original-xpub-address-encoders', number, network, sig, kind, account)
seed.wipe()
assert machine.last_reset() is None
print('@@XPUB_CORE_MS', time.ticks_ms() - started)
