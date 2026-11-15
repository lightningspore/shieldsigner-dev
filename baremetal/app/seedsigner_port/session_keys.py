# Copyright2021 SeedSigner; MIT, see ../LICENSE.SeedSigner
_SEEDKEEPER_KEYS_ATTR = 'luckfox_release_keys'

def clear_rekey_keys(controller):
    setattr(controller, _SEEDKEEPER_KEYS_ATTR, None)
_BIP85_CACHE_ATTR = 'luckfox_bip85_cache'

def clear_bip85_cache(controller):
    setattr(controller, _BIP85_CACHE_ATTR, {})

def clear_signing_keys(controller):
    """Drop every release-signing private key this module holds: the cached
    BIP85 derivations and any SeedKeeper-loaded keys not yet consumed."""
    clear_bip85_cache(controller)
    clear_rekey_keys(controller)
