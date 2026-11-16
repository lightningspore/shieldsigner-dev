# SPDX-License-Identifier: MIT
"""PUBLIC testnet demo fixtures for the QR screen (never use for real funds).

Seed: the standard BIP39 test mnemonic "abandon x11 about" (fingerprint 73c5da0a).
Address: its testnet native-segwit receive address m/84'/1'/0'/0/0.
PSBT: a synthetic, unsigned testnet spend of a made-up UTXO paid to that seed
(m/84'/1'/0'/0/0), sending to a second public test seed's address with change
back to m/84'/1'/0'/1/0. Fully deterministic; SeedSigner can review and sign it
when Settings > Network is Testnet. It is never valid on-chain.
"""

from functools import lru_cache
from embit import bip32, bip39, script
from embit.networks import NETWORKS
from embit.psbt import PSBT, DerivationPath
from embit.transaction import Transaction, TransactionInput, TransactionOutput
from embit.wordlists.bip39 import WORDLIST

WORDS = ['abandon'] * 11 + ['about']
OTHER = ['zoo'] * 11 + ['wrong']  # second public test seed: payment destination
NET = NETWORKS['test']


def _root(words):
    return bip32.HDKey.from_seed(bip39.mnemonic_to_seed(' '.join(words)), version=NET['xprv'])


def _key(root, path):
    return root.derive(path).key.get_public_key()


@lru_cache(None)
def seedqr():
    return ''.join('%04d' % WORDLIST.index(w) for w in WORDS)


@lru_cache(None)
def address(index=0):
    return script.p2wpkh(_key(_root(WORDS), "m/84h/1h/0h/0/%d" % index)).address(NET)


@lru_cache(None)
def psbt(amount=250_000, send=120_000, fee=1_410):
    root = _root(WORDS)
    fp = root.my_fingerprint
    recv = _key(root, "m/84h/1h/0h/0/0")
    change = _key(root, "m/84h/1h/0h/1/0")
    dest = script.p2wpkh(_key(_root(OTHER), "m/84h/1h/0h/0/0"))
    prev = bytes.fromhex('5eed' * 16)  # synthetic previous txid
    tx = Transaction(
        vin=[TransactionInput(prev, 0, sequence=0xFFFFFFFD)],
        vout=[
            TransactionOutput(send, dest),
            TransactionOutput(amount - send - fee, script.p2wpkh(change)),
        ],
    )
    p = PSBT(tx)
    p.inputs[0].witness_utxo = TransactionOutput(amount, script.p2wpkh(recv))
    p.inputs[0].bip32_derivations[recv] = DerivationPath(fp, bip32.parse_path("m/84h/1h/0h/0/0"))
    p.outputs[1].bip32_derivations[change] = DerivationPath(fp, bip32.parse_path("m/84h/1h/0h/1/0"))
    return p.serialize()


def summary():
    raw = psbt()
    p = PSBT.parse(raw)
    return {
        'fingerprint': _root(WORDS).my_fingerprint.hex(),
        'address': address(),
        'psbt_bytes': len(raw),
        'send_to': p.tx.vout[0].script_pubkey.address(NET),
        'send_sats': p.tx.vout[0].value,
        'change_sats': p.tx.vout[1].value,
        'fee_sats': p.fee(),
    }


if __name__ == '__main__':
    print(summary())
