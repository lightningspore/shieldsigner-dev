# Copyright2021 SeedSigner; MIT, see ../LICENSE.SeedSigner
# Generated original helpers; unported providers fail on use.
from seedsigner_port.decode_platform import dependency as _dependency,FeatureUnavailable
def get_standard_derivation_path(network=_dependency('seedsigner.models.settings_definition', 'SettingsConstants').MAINNET, wallet_type=_dependency('seedsigner.models.settings_definition', 'SettingsConstants').SINGLE_SIG, script_type=_dependency('seedsigner.models.settings_definition', 'SettingsConstants').NATIVE_SEGWIT, account=0):
    if network == _dependency('seedsigner.models.settings_definition', 'SettingsConstants').MAINNET:
        network_path = "0'"
    elif network == _dependency('seedsigner.models.settings_definition', 'SettingsConstants').TESTNET:
        network_path = "1'"
    elif network == _dependency('seedsigner.models.settings_definition', 'SettingsConstants').REGTEST:
        network_path = "1'"
    else:
        raise Exception('Unexpected network')
    if wallet_type == _dependency('seedsigner.models.settings_definition', 'SettingsConstants').SINGLE_SIG:
        if script_type == _dependency('seedsigner.models.settings_definition', 'SettingsConstants').LEGACY_P2PKH:
            return "m/44'/{0}/{1}'".format(network_path, account)
        elif script_type == _dependency('seedsigner.models.settings_definition', 'SettingsConstants').NESTED_SEGWIT:
            return "m/49'/{0}/{1}'".format(network_path, account)
        elif script_type == _dependency('seedsigner.models.settings_definition', 'SettingsConstants').NATIVE_SEGWIT:
            return "m/84'/{0}/{1}'".format(network_path, account)
        elif script_type == _dependency('seedsigner.models.settings_definition', 'SettingsConstants').TAPROOT:
            return "m/86'/{0}/{1}'".format(network_path, account)
        else:
            raise Exception('Unexpected script type')
    elif wallet_type == _dependency('seedsigner.models.settings_definition', 'SettingsConstants').MULTISIG:
        if script_type == _dependency('seedsigner.models.settings_definition', 'SettingsConstants').LEGACY_P2PKH:
            return "m/45'".format()
        elif script_type == _dependency('seedsigner.models.settings_definition', 'SettingsConstants').NESTED_SEGWIT:
            return "m/48'/{0}/{1}'/1'".format(network_path, account)
        elif script_type == _dependency('seedsigner.models.settings_definition', 'SettingsConstants').NATIVE_SEGWIT:
            return "m/48'/{0}/{1}'/2'".format(network_path, account)
        elif script_type == _dependency('seedsigner.models.settings_definition', 'SettingsConstants').TAPROOT:
            raise Exception('Taproot multisig not yet supported')
        else:
            raise Exception('Unexpected script type')
    else:
        raise Exception('Unexpected wallet type')

def is_standard_derivation(derivation_path, script_type, network):
    """
    Returns True if the derivation_path matches the standard BIP path for the
    given script_type, network, and any account 0-9.  For example, native segwit
    on mainnet must be m/84'/0'/<account>' for singlesig or
    m/48'/0'/<account>'/2' for multisig.
    """
    for wallet_type in (_dependency('seedsigner.models.settings_definition', 'SettingsConstants').SINGLE_SIG, _dependency('seedsigner.models.settings_definition', 'SettingsConstants').MULTISIG):
        for account in range(10):
            try:
                standard = get_standard_derivation_path(network=network, wallet_type=wallet_type, script_type=script_type, account=account)
                if derivation_path == standard:
                    return True
            except FeatureUnavailable:
                raise
            except Exception:
                pass
    return False

def get_expanded_search_derivation_paths(network=_dependency('seedsigner.models.settings_definition', 'SettingsConstants').MAINNET):
    """
    Returns a list of derivation paths for expanded address search.
    Includes all standard single sig paths (BIP44/49/84/86) for accounts
    0-9 for BOTH mainnet and testnet coin types, plus non-standard paths
    used by various wallets.

    Both coin types are included because some wallets use cross-network
    derivation paths (e.g. a testnet derivation path to produce a
    mainnet-formatted address).

    NOTE: This function intentionally does NOT consult the user's
    Settings for enabled script types. All standard derivation paths
    are always returned so the expanded search can act as a recovery
    tool regardless of which script types the user has enabled.
    """
    paths = []
    script_types = [_dependency('seedsigner.models.settings_definition', 'SettingsConstants').NATIVE_SEGWIT, _dependency('seedsigner.models.settings_definition', 'SettingsConstants').NESTED_SEGWIT, _dependency('seedsigner.models.settings_definition', 'SettingsConstants').LEGACY_P2PKH, _dependency('seedsigner.models.settings_definition', 'SettingsConstants').TAPROOT]
    networks = [network]
    alt_network = _dependency('seedsigner.models.settings_definition', 'SettingsConstants').TESTNET if network == _dependency('seedsigner.models.settings_definition', 'SettingsConstants').MAINNET else _dependency('seedsigner.models.settings_definition', 'SettingsConstants').MAINNET
    networks.append(alt_network)
    for net in networks:
        for script_type in script_types:
            for account in range(10):
                path = get_standard_derivation_path(network=net, wallet_type=_dependency('seedsigner.models.settings_definition', 'SettingsConstants').SINGLE_SIG, script_type=script_type, account=account)
                if path not in paths:
                    paths.append(path)
    paths.append("m/0'/0")
    paths.append('m/0')
    return paths

def normalize_descriptor_str(descriptor_str):
    """
    Ensure descriptor keys include branch/index wildcards so the Address Explorer
    can derive distinct receive and change addresses for each index.

    Two cases are handled:

    1. Keys already have a receive-only path (``/0/*``): replace with ``/{0,1}/*``
       so change addresses can also be derived.
    2. Keys have an origin but no trailing path at all: append ``/{0,1}/*`` so
       per-index derivation works correctly.

    The function is safe to call on descriptors that are already normalised —
    those are returned unchanged.
    """
    orig = descriptor_str
    try:
        if _dependency('re', None).search("\\[[0-9a-fA-F]+/[0-9/h\\']+\\].*?/0/\\*", descriptor_str):
            p = _dependency('re', None).compile("(\\[[0-9a-fA-F]+/[0-9/h\\']+\\].*?)(/0/\\*)")
            descriptor_str = p.sub('\\1/{0,1}/*', descriptor_str)
        elif _dependency('re', None).search("\\[[0-9a-fA-F]+/[0-9/h\\']+\\][a-zA-Z0-9]*(?=[,)])", descriptor_str):
            p = _dependency('re', None).compile("(\\[[0-9a-fA-F]+/[0-9/h\\']+\\][a-zA-Z0-9]*)([,)])")
            descriptor_str = p.sub('\\1/{0,1}/*\\2', descriptor_str)
    except FeatureUnavailable:
        raise
    except Exception:
        descriptor_str = orig
    return descriptor_str

def get_single_sig_address(xpub, script_type=_dependency('seedsigner.models.settings_definition', 'SettingsConstants').NATIVE_SEGWIT, index=0, is_change=False, embit_network='main'):
    if is_change:
        pubkey = xpub.derive([1, index]).key
    else:
        pubkey = xpub.derive([0, index]).key
    if script_type == _dependency('seedsigner.models.settings_definition', 'SettingsConstants').LEGACY_P2PKH:
        return _dependency('embit', None).script.p2pkh(pubkey).address(network=_dependency('embit.networks', 'NETWORKS')[embit_network])
    elif script_type == _dependency('seedsigner.models.settings_definition', 'SettingsConstants').NESTED_SEGWIT:
        return _dependency('embit', None).script.p2sh(_dependency('embit', None).script.p2wpkh(pubkey)).address(network=_dependency('embit.networks', 'NETWORKS')[embit_network])
    elif script_type == _dependency('seedsigner.models.settings_definition', 'SettingsConstants').NATIVE_SEGWIT:
        return _dependency('embit', None).script.p2wpkh(pubkey).address(network=_dependency('embit.networks', 'NETWORKS')[embit_network])
    elif script_type == _dependency('seedsigner.models.settings_definition', 'SettingsConstants').TAPROOT:
        return _dependency('embit', None).script.p2tr(pubkey).address(network=_dependency('embit.networks', 'NETWORKS')[embit_network])

def get_multisig_address(descriptor, index=0, is_change=False, embit_network='main'):
    if is_change:
        branch_index = 1
    else:
        branch_index = 0
    if descriptor.is_segwit or descriptor.is_legacy:
        return descriptor.derive(index, branch_index=branch_index).script_pubkey().address(network=_dependency('embit.networks', 'NETWORKS')[embit_network])
    elif descriptor.is_taproot:
        raise Exception('Taproot verification not yet implemented!')
    raise Exception('{0} address verification not yet implemented!'.format(descriptor.script_pubkey().script_type()))

def get_multisig_policy(descriptor):
    """Extract (threshold, n) from a basic multisig descriptor."""
    if not descriptor.is_basic_multisig:
        raise ValueError('Expected a basic multisig descriptor, got: {0}'.format(descriptor.brief_policy))
    return (str(descriptor.miniscript.args[0]), str(len(descriptor.keys)))

def get_embit_network_name(settings_name):
    """ Convert SeedSigner SettingsConstants for `network` to embit's NETWORK key """
    lookup = {_dependency('seedsigner.models.settings_definition', 'SettingsConstants').MAINNET: 'main', _dependency('seedsigner.models.settings_definition', 'SettingsConstants').TESTNET: 'test', _dependency('seedsigner.models.settings_definition', 'SettingsConstants').REGTEST: 'regtest'}
    return lookup.get(settings_name)

def parse_derivation_path(derivation_path):
    """
    Parses a derivation path into its related SettingsConstants equivalents.

    Primarily only supports single sig derivation paths.

    May return None for fields it cannot parse.
    """
    derivation_path = derivation_path.replace("'", 'h')
    sections = derivation_path.split('/')
    if len(sections) < 3 or sections[1] == '48h':
        return dict(script_type=None, network=None, is_change=None, index=None, wallet_derivation_path=None, clean_match=False)
    lookups = {'script_types': {'44h': _dependency('seedsigner.models.settings_definition', 'SettingsConstants').LEGACY_P2PKH, '49h': _dependency('seedsigner.models.settings_definition', 'SettingsConstants').NESTED_SEGWIT, '84h': _dependency('seedsigner.models.settings_definition', 'SettingsConstants').NATIVE_SEGWIT, '86h': _dependency('seedsigner.models.settings_definition', 'SettingsConstants').TAPROOT}, 'networks': {'0h': _dependency('seedsigner.models.settings_definition', 'SettingsConstants').MAINNET, '1h': [_dependency('seedsigner.models.settings_definition', 'SettingsConstants').TESTNET, _dependency('seedsigner.models.settings_definition', 'SettingsConstants').REGTEST]}}
    details = dict()
    details['script_type'] = lookups['script_types'].get(sections[1])
    if not details['script_type']:
        details['script_type'] = _dependency('seedsigner.models.settings_definition', 'SettingsConstants').CUSTOM_DERIVATION
    details['network'] = lookups['networks'].get(sections[2])
    if sections[-2] in ['0', '1']:
        details['is_change'] = sections[-2] == '1'
    else:
        details['is_change'] = None
    if sections[-1].isascii() and sections[-1].isdigit():
        details['index'] = int(sections[-1])
    else:
        details['index'] = None
    if details['is_change'] is not None and details['index'] is not None:
        details['wallet_derivation_path'] = '/'.join(sections[:-2])
    else:
        details['wallet_derivation_path'] = None
    details['clean_match'] = True
    for k, v in details.items():
        if v is None:
            details['clean_match'] = False
            break
    return details

def sign_message(root, derivation, msg, compressed=True):
    """
        from: https://github.com/cryptoadvance/specter-diy/blob/b58a819ef09b2bca880a82c7e122618944355118/src/apps/signmessage/signmessage.py

        Sign a Bitcoin message using a BIP-32 root key and derivation path.
        Use seed.get_root(network) to obtain the root key — never
        bip32.HDKey.from_seed(seed.seed_bytes) directly (see AGENTS.md).
    """
    msghash = _dependency('hashlib', 'sha256')(_dependency('hashlib', 'sha256')(b'\x18Bitcoin Signed Message:\n' + _dependency('embit', 'compact').to_bytes(len(msg)) + msg).digest()).digest()
    prv = root.derive(derivation).key
    sig = _dependency('embit.util', 'secp256k1').ecdsa_sign_recoverable(msghash, prv._secret)
    flag = sig[64]
    sig = _dependency('embit', 'ec').Signature(sig[:64])
    c = 4 if compressed else 0
    flag = bytes([27 + flag + c])
    ser = flag + _dependency('embit.util', 'secp256k1').ecdsa_signature_serialize_compact(sig._sig)
    return _dependency('binascii', 'b2a_base64')(ser).strip().decode()

def get_xpub(seed_bytes, derivation_path, embit_network='main'):
    root = _dependency('embit', 'bip32').HDKey.from_seed(seed_bytes, version=_dependency('embit.networks', 'NETWORKS')[embit_network]['xprv'])
    xprv = root.derive(derivation_path)
    xpub = xprv.to_public()
    return xpub
