# SPDX-License-Identifier: MIT
# Copyright (c) 2021 SeedSigner; MIT, see ../LICENSE.SeedSigner.
# Formatting adapted from kdmukAI-bot/seedsigner fd9ba8fc766f715668bc37fbb5485499def9e52f.
# Source-backed native contract; upstream source/notice pinned in provenance.
from seedsigner_port.decode_platform import dependency as _dependency, FeatureUnavailable

"""Transaction display contracts; original Views/parser still decide/sign."""
NAMES = {
    'PSBTOverviewScreen',
    'PSBTMathScreen',
    'PSBTAddressDetailsScreen',
    'PSBTChangeDetailsScreen',
    'PSBTOpReturnScreen',
    'PSBTFinalizeScreen',
}


def configure(name, a, cfg):
    settings = _dependency('seedsigner.models.settings', 'Settings').get_instance()
    network = settings.get_value(
        _dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__NETWORK
    )
    for field in ('input_amount', 'spend_amount', 'fee_amount', 'change_amount', 'amount'):
        if field in a and (type(a[field]) is not int or a[field] < 0):
            raise ValueError('Invalid transaction amount: ' + field)
    cfg['is_bottom_list'] = True
    if name == 'PSBTOverviewScreen':
        cfg['top_nav']['title'] = _dependency('gettext', 'gettext')('Review Transaction')
        cfg['button_list'] = [_dependency('gettext', 'gettext')('Review details')]
        amount = a['spend_amount'] if a.get('destination_addresses') else a['change_amount']
        cfg['btc_amount'] = _dependency('seedsigner_port.psbt_formatting', 'btc_amount_from_sats')(
            amount
        )
        for field in (
            'num_inputs',
            'num_self_transfer_outputs',
            'num_change_outputs',
            'has_op_return',
            'is_high_fee_tx',
        ):
            cfg[field] = a.get(field, False if field.startswith(('has_', 'is_')) else 0)
        cfg['destination_addresses'] = a.get('destination_addresses') or []
        cfg['labels'] = {
            'input_n': _dependency('gettext', 'gettext')('input {}'),
            'one_input': _dependency('gettext', 'gettext')('1 input'),
            'recipient_n': _dependency('gettext', 'gettext')('recipient {}'),
            'recipient_1': _dependency('gettext', 'gettext')('recipient 1'),
            'recipient_singular': _dependency('gettext', 'gettext')('recipient'),
            'ellipsis_series': '...',
            'self_transfer': _dependency('gettext', 'gettext')('self-transfer'),
            'fee': _dependency('gettext', 'gettext')('fee')
            + (' (!)' if a.get('is_high_fee_tx') else ''),
            'op_return': 'OP_RETURN',
            'change': _dependency('gettext', 'gettext')('change'),
        }
        return ('psbt_overview_screen', cfg)
    if name == 'PSBTMathScreen':
        cfg['top_nav']['title'] = _dependency('gettext', 'gettext')('Transaction Math')
        cfg['button_list'] = [_dependency('gettext', 'gettext')('Review recipients')]
        btc = a['input_amount'] > 1000000
        number = (
            _dependency('seedsigner_port.psbt_formatting', 'format_btc')
            if btc
            else _dependency('seedsigner_port.psbt_formatting', 'format_sats')
        )
        cfg['amounts'] = {
            'input': number(a['input_amount']),
            'spend': number(a['spend_amount']),
            'fee': str(a['fee_amount'])
            if btc
            else _dependency('seedsigner_port.psbt_formatting', 'format_sats')(a['fee_amount']),
            'change': number(a['change_amount']),
        }
        cfg['denomination'] = 'btc' if btc else 'sats'
        cfg['num_recipients'] = a['num_recipients']
        cfg['is_high_fee_tx'] = bool(a.get('is_high_fee_tx'))
        cfg['labels'] = {
            'inputs': _dependency('seedsigner_port.psbt_screens', 'ngettext')(
                'input', 'inputs', a['num_inputs']
            ),
            'recipients': _dependency('seedsigner_port.psbt_screens', 'ngettext')(
                'recipient', 'recipients', a['num_recipients']
            ),
            'fee': _dependency('gettext', 'gettext')('fee')
            + (' (!)' if a.get('is_high_fee_tx') else ''),
            'change': _dependency('gettext', 'gettext')('{} change').format(
                _dependency('gettext', 'gettext')('btc')
                if btc
                else _dependency('gettext', 'gettext')('sats')
            ),
        }
        return ('psbt_math_screen', cfg)
    if name in ('PSBTAddressDetailsScreen', 'PSBTChangeDetailsScreen'):
        cfg['btc_amount'] = _dependency('seedsigner_port.psbt_formatting', 'btc_amount_from_sats')(
            a['amount']
        )
        cfg['address'] = a['address']
        cfg['network'] = network
        if name == 'PSBTAddressDetailsScreen':
            return ('psbt_address_details_screen', cfg)
        kind = (
            _dependency('gettext', 'gettext')('change address')
            if a.get('is_change_derivation_path', True)
            else _dependency('gettext', 'gettext')('receive address')
        )
        cfg['address_type_label'] = (
            kind
            + ' '
            + _dependency('gettext', 'gettext')('#')
            + str(a.get('derivation_path_addr_index', 0))
        )
        cfg['is_verified'] = bool(a.get('is_change_addr_verified'))
        cfg['verified_text'] = _dependency('gettext', 'gettext')('Address verified!')
        return ('psbt_change_details_screen', cfg)
    if name == 'PSBTOpReturnScreen':
        data = a['op_return_data']
        try:
            text = data.decode('utf-8')
            if '\x00' in text:
                raise UnicodeError('NUL is not visible text')
            cfg['text'] = text if text else _dependency('gettext', 'gettext')('Empty OP_RETURN')
        except UnicodeError:
            cfg['hex'] = data.hex()
            cfg['hex_label'] = _dependency('gettext', 'gettext')('raw hex data')
        return ('psbt_op_return_screen', cfg)
    if name == 'PSBTFinalizeScreen':
        cfg.pop('initial_selected_index', None)
        cfg['top_nav']['title'] = _dependency('gettext', 'gettext')('Sign Transaction')
        cfg['status_type'] = 'custom'
        cfg['icon'] = '\ue921'
        cfg['icon_color'] = '#409CFF'
        cfg['warning_edges'] = False
        lines = [_dependency('gettext', 'gettext')('Click to approve this transaction')]
        if a.get('is_rbf'):
            lines.append(_dependency('gettext', 'gettext')('Replaceable (RBF)'))
        if a.get('locktime_text'):
            lines.append(a['locktime_text'])
        cfg['text'] = '\n\n'.join(lines)
        return ('large_icon_status_screen', cfg)
    raise NotImplementedError(name)
