# Copyright2021 SeedSigner; MIT, see ../LICENSE.SeedSigner
# Generated original PSBT field defaults.
DEFAULTS = {
    'PSBTOverviewScreen': {
        'spend_amount': 0,
        'change_amount': 0,
        'fee_amount': 0,
        'num_inputs': 0,
        'num_self_transfer_outputs': 0,
        'num_change_outputs': 0,
        'destination_addresses': None,
        'has_op_return': False,
        'is_high_fee_tx': False,
    },
    'PSBTMathScreen': {
        'input_amount': 0,
        'num_inputs': 0,
        'spend_amount': 0,
        'num_recipients': 0,
        'fee_amount': 0,
        'change_amount': 0,
        'is_high_fee_tx': False,
    },
    'PSBTAddressDetailsScreen': {'address': None, 'amount': 0},
    'PSBTChangeDetailsScreen': {
        'amount': 0,
        'address': None,
        'is_multisig': False,
        'fingerprint': None,
        'derivation_path': None,
        'is_change_derivation_path': True,
        'derivation_path_addr_index': 0,
        'is_change_addr_verified': False,
    },
    'PSBTOpReturnScreen': {'op_return_data': None},
    'PSBTFinalizeScreen': {'is_rbf': False, 'locktime_text': None},
}
