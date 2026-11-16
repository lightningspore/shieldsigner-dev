# Copyright2021 SeedSigner; MIT, see ../LICENSE.SeedSigner
from seedsigner_port.decode_platform import FeatureUnavailable


class RejectCode:
    """
    Why a psbt was refused. See `InvalidPSBTError`.

    These are the constructions with no innocent explanation -- a psbt is only
    built this way to make the review screens say something other than what the
    signature will actually authorise. Conditions that are merely unusual, and
    that an honest coordinator might legitimately produce, belong in
    `RiskWarning` instead, where they are shown but do not block.
    """

    MIXED_INPUTS = 'MIXED_INPUTS'
    MISSING_UTXO = 'MISSING_UTXO'
    NEGATIVE_FEE = 'NEGATIVE_FEE'
    AMOUNT_OUT_OF_RANGE = 'AMOUNT_OUT_OF_RANGE'
    INVALID_WITNESS_UTXO = 'INVALID_WITNESS_UTXO'
    EXTRANEOUS_WITNESS_SCRIPT = 'EXTRANEOUS_WITNESS_SCRIPT'
    UTXO_MISMATCH = 'UTXO_MISMATCH'
    SCRIPT_HASH_MISMATCH = 'SCRIPT_HASH_MISMATCH'
    UNREACHABLE_CHANGE_PATH = 'UNREACHABLE_CHANGE_PATH'
    NONZERO_OP_RETURN = 'NONZERO_OP_RETURN'
    UNSUPPORTED_SIGHASH = 'UNSUPPORTED_SIGHASH'
    CHANGE_INDEX_TOO_FAR = 'CHANGE_INDEX_TOO_FAR'
    UNSUPPORTED_PSBT_VERSION = 'UNSUPPORTED_PSBT_VERSION'
    TX_MODIFIABLE = 'TX_MODIFIABLE'
    UNDISPLAYABLE_OUTPUT = 'UNDISPLAYABLE_OUTPUT'
    WRONG_VERSION_FIELD = 'WRONG_VERSION_FIELD'
    MALFORMED_ENCODING = 'MALFORMED_ENCODING'
    INVALID_TRANSACTION = 'INVALID_TRANSACTION'
    FORGED_OUTPUT_OWNERSHIP = 'FORGED_OUTPUT_OWNERSHIP'
    FORGED_INPUT_OWNERSHIP = 'FORGED_INPUT_OWNERSHIP'
    SURPLUS_DERIVATIONS = 'SURPLUS_DERIVATIONS'
    MIXED_DERIVATION_MAPS = 'MIXED_DERIVATION_MAPS'
    MISLABELED_OUTPUT_OWNERSHIP = 'MISLABELED_OUTPUT_OWNERSHIP'
    INCONSISTENT_FINGERPRINTS = 'INCONSISTENT_FINGERPRINTS'
    SEED_CANNOT_SIGN = 'SEED_CANNOT_SIGN'


class InvalidPSBTError(Exception):
    """
    The psbt is well-formed enough for embit to parse, but SeedSigner refuses to
    present or sign it.

    Distinct from an unexpected exception: this is a decision, and the UI shows
    it to the user as a warning rather than as a crash.
    """

    def __init__(self, message, code=None):
        super().__init__(message)
        self.code = code
