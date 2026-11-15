# Copyright2021 SeedSigner; MIT, see ../LICENSE.SeedSigner
# Generated original full policy; unported providers fail on use.
from seedsigner_port.decode_platform import dependency as _dependency,FeatureUnavailable
from seedsigner_port.psbt_errors import RejectCode,InvalidPSBTError
class OPCODES:
    OP_RETURN = 106
    OP_PUSHDATA1 = 76
    OP_PUSHDATA2 = 77
    OP_PUSHDATA4 = 78
    OP_CHECKLOCKTIMEVERIFY = 177
    OP_CHECKSEQUENCEVERIFY = 178
MAX_MONEY = 21000000 * 100000000
DUST_THRESHOLD = 546
HIGH_FEE_NUMERATOR = 1
HIGH_FEE_DENOMINATOR = 10
DEFAULT_CHANGE_INDEX_LOOKAHEAD = 100
LOCKTIME_TIMESTAMP_THRESHOLD = 500000000
RBF_SEQUENCE_CEILING = 4294967294
SEQUENCE_FINAL = 4294967295
SEQUENCE_LOCKTIME_DISABLE_FLAG = 1 << 31
SEQUENCE_LOCKTIME_MASK = 65535
FAR_FUTURE_LOCKTIME_SECONDS = 2 * 365 * 24 * 60 * 60
SIGHASH_DEFAULT = 0
SIGHASH_ALL = 1

class RiskWarning:
    """
    Conditions worth showing the user before they approve. Unlike RejectCode
    these do not block signing; they are surfaced for review.
    """
    HIGH_FEE = 'HIGH_FEE'
    HIGH_FEE_RATE = 'HIGH_FEE_RATE'
    DUST_OUTPUT = 'DUST_OUTPUT'
    FUTURE_LOCKTIME = 'FUTURE_LOCKTIME'
    LOCKTIME_FAR_FUTURE = 'LOCKTIME_FAR_FUTURE'
    RELATIVE_TIMELOCK = 'RELATIVE_TIMELOCK'
    SCRIPT_TIMELOCK = 'SCRIPT_TIMELOCK'
    RBF = 'RBF'
    UNVERIFIED_INPUT_AMOUNTS = 'UNVERIFIED_INPUT_AMOUNTS'
    INFORMATIONAL = frozenset({RBF})

class PSBTParser:
    """
    Reads a psbt on behalf of one seed and works out everything the signing flow shows the
    user before they approve: the wallet policy (script type, plus m-of-n and the
    cosigners for multisig), the amount coming in, what is being spent, what comes back as
    change, the fee, where the spend is going, and any OP_RETURN payload.

    Constructing it with a seed parses immediately; see parse() for what that establishes
    in what order and which psbts it turns away.

    The parse fully processes the psbt, validates what it can, then stores the organized
    results in the instance attributes (spend_amount, fee_amount, destination_addresses,
    etc.). Note that change_data and change_amount cover EVERY output coming back to this
    seed, including self-transfers to a receive address. The view layer tells the two
    apart by the branch index in the derivation path.

    A psbt is written by an untrusted coordinator. The metadata it carries about keys
    (fingerprints, derivation paths, xpubs) is a claim, not a fact. The onus is on us to
    verify by re-deriving from the signing seed. For multisig, verification depends on the
    user providing a "known good" descriptor (i.e. can be trusted) from which we can
    verify the outputs by deriving from the cosigners' xpubs.

    This class makes the difference visible in its own names:

      claimed_...   coordinator-supplied metadata (fingerprints, derivation paths, xpubs).
                    Safe to read and display; never safe to make a decision on.
      verified_...  a fact this device proved by re-deriving from the signing seed and
                    matching real key material. Only assigned by code that performed that
                    derivation.

    Invariant: no verified_ value is ever assigned from a claimed_ value without an
    intervening re-derivation from self.root or from a user-supplied "known good"
    descriptor.

    The invariant is enforced, not merely documented: a claim that cannot be turned
    into a fact is refused rather than displayed. See RejectCode for the specific
    constructions that have no honest explanation, and RiskWarning for the ones that
    do and are surfaced for review instead.
    """
    MAX_CACHED_DERIVATIONS = 1000
    HIGH_FEES_WARNING_THRESHOLD = 25

    def __init__(self, p, seed=None, *, root=None, root_path=None, master_fingerprint=None, network=_dependency('seedsigner.models.settings', 'SettingsConstants').MAINNET, change_index_lookahead=None, reference_time=None, max_fee_rate=None, block_anchor=None, multisig_descriptor=None):
        self.psbt = p
        self.seed = seed
        self.network = network
        self.root = root
        self.root_path = root_path or []
        self.root_path_str = _dependency('embit', 'bip32').path_to_str(self.root_path) if self.root_path else 'm'
        self.master_fingerprint = master_fingerprint
        self.reference_time = reference_time
        self.block_anchor = block_anchor
        self.multisig_descriptor = multisig_descriptor
        self.unidentified_change_outputs = []
        self.change_index_lookahead = change_index_lookahead if change_index_lookahead is not None else PSBTParser._configured_change_index_lookahead()
        self.policy = None
        self.spend_amount = 0
        self.change_amount = 0
        self.change_data = []
        self.fee_amount = 0
        self.input_amount = 0
        self.num_inputs = 0
        self.verified_input_prefixes = set()
        self.verified_max_input_index = -1
        self.can_verify_derivations = False
        self.destination_addresses = []
        self.destination_amounts = []
        self.op_return_payloads = []
        self.op_return_amount = 0
        self.risk_warnings = set()
        self.fee_rate = 0.0
        self.max_fee_rate = max_fee_rate if max_fee_rate is not None else PSBTParser._configured_max_fee_rate()
        self.locktime_is_enforced = False
        self.locktime = 0
        self.is_high_fee = False
        self.verified_input_derivation_paths = []
        self.verified_output_derivation_paths = []
        if self.seed is not None or self.root is not None:
            self.parse()

    @staticmethod
    def _configured_change_index_lookahead():
        """
        The user's Change Gap Limit, or the default if settings aren't available
        (the parser is usable standalone, e.g. from tests and scripts).
        """
        try:
            return _dependency('seedsigner.models.settings', 'Settings').get_instance().get_value(_dependency('seedsigner.models.settings', 'SettingsConstants').SETTING__CHANGE_INDEX_LOOKAHEAD)
        except FeatureUnavailable:
            raise
        except Exception as e:
            pass
            return DEFAULT_CHANGE_INDEX_LOOKAHEAD

    def get_change_data(self, change_num):
        if change_num < len(self.change_data):
            return self.change_data[change_num]

    @property
    def num_change_outputs(self):
        return len(self.change_data)

    @property
    def is_multisig(self):
        """
            Multisig psbts will have "m" and "n" defined in policy
        """
        return isinstance(self.policy, dict) and 'm' in self.policy

    @property
    def num_destinations(self):
        return len(self.destination_addresses)

    @property
    def op_return_data(self):
        """The first OP_RETURN payload, or None. See op_return_payloads for all of them."""
        return self.op_return_payloads[0] if self.op_return_payloads else None

    def _set_root(self):
        if self.seed is not None:
            if isinstance(self.seed, _dependency('seedsigner.models.wif', 'WIFKey')):
                self.root = self.seed.privkey
            else:
                self.root = self.seed.get_root(self.network)
        elif self.root is None:
            raise RuntimeError('No seed or root key available')

    def parse(self):
        """
        Establishes, in order:

          0. _validate_psbt_version / _check_tx_modifiable / _assert_v2_complete /
             _check_tx_structure: the psbt must be one whose bytes can only mean one
             transaction, and one consensus could accept, before any of its claims are
             worth reading. See RejectCode.

          1. _fill_missing_fingerprints: backfills all-zero fingerprints, but only for
             scopes the seed provably derives.

          2. _verify_claimed_derivation_paths: each input and output scope that claims to
             be controlled by the seed is verified. Raises InvalidPSBTError with
             RejectCode.FORGED_[INPUT|OUTPUT]_OWNERSHIP if a claimed scope fails
             verification. The claims that survive are then checked for shape
             (_verify_claim_shapes: SURPLUS_DERIVATIONS, MIXED_DERIVATION_MAPS) and,
             on outputs, against the script they sit on
             (_verify_output_claims_match_scripts: FORGED_OUTPUT_OWNERSHIP).

          3. _reject_if_seed_cannot_sign: raises RejectCode.SEED_CANNOT_SIGN if none of
             the inputs can be signed by the seed. A mismatch rather than an attack,
             caught here so the flow can say so before showing a transaction.

             Steps 2 and 3 need a BIP32 tree to derive against, so both are skipped when
             there is none -- WIF / BIP38 signing, or a seedless multisig pre-parse. See
             can_verify_derivations.

          4. _parse_inputs: every input must resolve to the same policy, otherwise
             RejectCode.MIXED_INPUTS. Each input is also structurally validated here
             (RejectCode.MISSING_UTXO, UNSUPPORTED_SIGHASH, and the rest).

             A policy is one of:
               - single-sig: the script type alone. Says nothing about keys.
               - multisig, cosigners resolved: script type, m-of-n, and the cosigner
                 xpubs that every key in the script was traced back to.
               - multisig, cosigners unresolved: script type and m-of-n only.
                 _get_policy doesn't propagate cosigner errors, so two such policies match
                 without anything having tied them to the same keys. TODO: don't let a
                 policy with no cosigner information pass as a match.

          5. _parse_outputs: organizes the output data (amounts, destination_addresses,
             etc.) and verifies the ownership of the outputs that come back to this seed
             via:
             - single-sig: Rebuild the output script from the seed and match it against
               the committed scriptPubKey.
             - multisig: Match each of the seed's verified keys against the pubkeys in
               the script the output commits to.
             Every change_data entry after this point will carry a derivation path that
             our seed provably owns.

        Optimization via child_key_derivation_cache:
        Parsing traverses a derivation path down to an individual address one level at a
        time, over and over, and where that traversal begins depends on the wallet.

        Single-sig traverses the full path down from our own master key, on every OUTPUT
        the PSBT claims is ours.

        Multisig instead traverses just the last two levels down from each cosigner's
        account xpub, once per cosigner, on every INPUT and on every OUTPUT carrying the
        multisig script.

        Deriving each level costs a hash and an elliptic curve operation, and these
        traversals overlap heavily: everything in one account shares the same opening
        levels, differing only in the address at the end.

        So every level derived during this parse is kept in a cache and reused. See
        _derive_with_cache_via_indices.

        Note that the cache is only useful within a single parse so it is not preserved.
        """
        if self.psbt is None:
            pass
            return False
        self._validate_psbt_version()
        self._check_tx_modifiable()
        self._assert_v2_complete()
        self._check_tx_structure()
        if self.seed is not None and self.root is None:
            self._set_root()
        self.can_verify_derivations = self.root is not None and hasattr(self.root, 'derive')
        child_key_derivation_cache = {}
        self._fill_missing_fingerprints(child_key_derivation_cache)
        self._verify_claimed_derivation_paths(child_key_derivation_cache)
        self._verify_claim_shapes()
        self._verify_output_claims_match_scripts()
        self._reject_mislabeled_outputs(child_key_derivation_cache)
        self._reject_if_seed_cannot_sign()
        rt = self._parse_inputs(child_key_derivation_cache)
        if rt == False:
            return False
        if self.root is None and self.seed is None and (not self.is_multisig):
            raise RuntimeError('No seed or root key available')
        rt = self._parse_outputs(child_key_derivation_cache)
        if rt == False:
            return False
        self._reject_inconsistent_fingerprints(child_key_derivation_cache)
        self.is_high_fee = self.has_high_fee()
        return True

    @staticmethod
    def _is_witness_program(script_pubkey):
        """
        A witness program per BIP-141: a single version byte (OP_0, or OP_1
        through OP_16) followed by a 2-40 byte push.

        Tested structurally rather than against a list of known script types, so
        that a future witness version isn't mistaken for a fabricated prevout.
        """
        data = script_pubkey.data
        if len(data) < 4 or len(data) > 42:
            return False
        version_byte = data[0]
        if version_byte != 0 and (not 81 <= version_byte <= 96):
            return False
        push_len = data[1]
        return 2 <= push_len <= 40 and push_len == len(data) - 2

    def _check_fee_rate(self):
        """
        Flag a fee that is extortionate *per byte*, which the share-of-inputs
        check cannot see.

        The two miss opposite things. A 9%-of-inputs fee on a large consolidation
        stays under the relative threshold while burning a fortune; a modest
        absolute fee on a tiny transaction can be a wild rate. Both are worth a
        look, so both are checked.

        The threshold is a setting because fee rates move by orders of magnitude
        between quiet periods and congestion -- see
        SettingsConstants.ALL_MAX_FEE_RATES. Warning only: paying a high rate is
        sometimes exactly what the user intends.
        """
        if self.fee_amount <= 0:
            return
        threshold = self.max_fee_rate
        if not threshold or threshold <= 0:
            return
        try:
            vsize = self.estimate_vsize()
        except FeatureUnavailable:
            raise
        except Exception as e:
            pass
            return
        if vsize <= 0:
            return
        self.fee_rate = self.fee_amount / vsize
        if self.fee_rate >= threshold:
            self.risk_warnings.add(RiskWarning.HIGH_FEE_RATE)

    @staticmethod
    def _configured_max_fee_rate():
        """
        The user's Max Fee Rate in sat/vB, resolving AUTO against
        resources/latest-block.json. 0 means the check is off.
        """
        try:
            configured = _dependency('seedsigner.models.settings', 'Settings').get_instance().get_value(_dependency('seedsigner.models.settings_definition', 'SettingsConstants').SETTING__MAX_FEE_RATE)
        except FeatureUnavailable:
            raise
        except Exception as e:
            pass
            configured = _dependency('seedsigner.models.settings_definition', 'SettingsConstants').DEFAULT_MAX_FEE_RATE
        if configured != _dependency('seedsigner.models.settings_definition', 'SettingsConstants').MAX_FEE_RATE__AUTO:
            return configured
        try:
            rate = _dependency('seedsigner.controller', 'Controller').RECENT_MAX_FEE_RATE
            if rate and rate > 0:
                return rate
        except FeatureUnavailable:
            raise
        except Exception as e:
            pass
        return _dependency('seedsigner.models.settings_definition', 'SettingsConstants').FALLBACK_MAX_FEE_RATE

    def _check_far_future_locktime(self, locktime):
        """
        Flag a locktime sitting years beyond when this psbt was created.

        The device has no RTC, so it cannot ask what today is. When a psbt is
        loaded from microSD its file mtime is a usable stand-in: it was written by
        a machine that did have a clock. `reference_time` carries that; it is None
        for QR-delivered psbts, where no such hint exists.

        SECURITY PROPERTY: this may only ever *raise* a warning, never suppress
        one. A file mtime is attacker-influenceable -- whoever wrote the file
        chose it -- so a forged mtime can hide a long lock. That is acceptable
        precisely because the fallback is the existing behaviour: the locktime is
        still stated on the approval screen either way. An attacker who forges the
        mtime buys back the status quo and nothing more. What they must never be
        able to do is use it to turn a warning off, which is why nothing here
        clears a warning and why an implausible reference is discarded rather than
        trusted.
        """
        if not self.locktime_is_enforced or not locktime:
            return
        if not self.reference_time or self.reference_time <= 0:
            return
        if locktime >= LOCKTIME_TIMESTAMP_THRESHOLD:
            locktime_as_time = locktime
        else:
            if not self.block_anchor:
                return
            anchor_height, anchor_time = self.block_anchor
            if anchor_height <= 0 or anchor_time <= 0:
                return
            locktime_as_time = anchor_time + (locktime - anchor_height) * 600
        if locktime_as_time - self.reference_time >= FAR_FUTURE_LOCKTIME_SECONDS:
            self.risk_warnings.add(RiskWarning.LOCKTIME_FAR_FUTURE)

    @staticmethod
    def _estimate_input_vsize(inp):
        """
        Virtual size this input will occupy once signed, in vbytes.

        The psbt is unsigned, so the signature is not there to measure. Its size
        is however almost entirely determined by the script type, and the parts
        that vary (low-S DER encoding is 71 or 72 bytes) vary by a byte or two --
        irrelevant at the resolution a "is this fee rate absurd" check needs.

        Witness data is quarter-weight, hence the /4 terms.
        """
        vsize = 41.0
        utxo = inp.witness_utxo
        if utxo is None and inp.non_witness_utxo is not None:
            utxo = inp.non_witness_utxo.vout[inp.vout]
        if utxo is None:
            return vsize
        script_type = utxo.script_pubkey.script_type()
        SIG = 72
        PUBKEY = 33
        if script_type == 'p2wpkh':
            return vsize + (1 + (1 + SIG) + (1 + PUBKEY)) / 4
        if script_type == 'p2tr':
            return vsize + (1 + (1 + 64)) / 4
        if script_type == 'p2wsh':
            m, n = PSBTParser._multisig_m_n(inp.witness_script)
            if m is None:
                script_len = len(inp.witness_script.data) if inp.witness_script else 34
                return vsize + (1 + (1 + SIG) + (1 + script_len)) / 4
            script_len = len(inp.witness_script.data)
            witness = 1 + 1 + m * (1 + SIG) + (1 + script_len)
            return vsize + witness / 4
        if script_type == 'p2sh':
            redeem = inp.redeem_script
            if redeem is not None and PSBTParser._is_witness_program(redeem):
                vsize += 1 + len(redeem.data)
                if len(redeem.data) == 22:
                    return vsize + (1 + (1 + SIG) + (1 + PUBKEY)) / 4
                m, _n = PSBTParser._multisig_m_n(inp.witness_script)
                m = m or 1
                script_len = len(inp.witness_script.data) if inp.witness_script else 34
                return vsize + (1 + 1 + m * (1 + SIG) + (1 + script_len)) / 4
            m, _n = PSBTParser._multisig_m_n(redeem)
            m = m or 1
            script_len = len(redeem.data) if redeem else 34
            return vsize + 1 + m * (1 + SIG) + (1 + script_len)
        if script_type == 'p2pkh':
            return vsize + (1 + SIG) + (1 + PUBKEY)
        return vsize + (1 + SIG) + (1 + PUBKEY)

    @staticmethod
    def _multisig_m_n(script):
        """(m, n) for a bare multisig script, or (None, None)."""
        if script is None:
            return (None, None)
        try:
            m, n, _pubkeys = PSBTParser._parse_multisig(script)
            return (m, n)
        except FeatureUnavailable:
            raise
        except Exception:
            return (None, None)

    def estimate_vsize(self):
        """
        Virtual size of the finished transaction, in vbytes.

        Needed because a fee is only interpretable as a rate. 50,000 sats is
        nothing on a 200-input consolidation and extortionate on a 1-in 2-out
        payment, and the absolute-fee check (fee as a share of inputs) cannot
        tell those apart.
        """
        tx = self.psbt.tx
        vsize = 8.0
        vsize += PSBTParser._varint_size(len(tx.vin))
        vsize += PSBTParser._varint_size(len(tx.vout))
        has_witness = any((PSBTParser._is_witness_program((inp.witness_utxo or (inp.non_witness_utxo.vout[inp.vout] if inp.non_witness_utxo else None)).script_pubkey) if inp.witness_utxo or inp.non_witness_utxo else False for inp in self.psbt.inputs))
        if has_witness:
            vsize += 0.5
        for inp in self.psbt.inputs:
            vsize += PSBTParser._estimate_input_vsize(inp)
        for vout in tx.vout:
            script_len = len(vout.script_pubkey.data)
            vsize += 8 + PSBTParser._varint_size(script_len) + script_len
        return vsize

    @staticmethod
    def _varint_size(n):
        if n < 253:
            return 1
        if n <= 65535:
            return 3
        if n <= 4294967295:
            return 5
        return 9

    def _validate_psbt_version(self):
        """
        Refuse a psbt that declares a format we do not implement.

        BIP-174 defines version 0 (the field may be absent, which means 0) and
        BIP-370 defines version 2; both are supported here. Any other value is a
        future or unknown format whose fields we would misread, so it is refused
        rather than guessed at.

        A v2 psbt has no PSBT_GLOBAL_UNSIGNED_TX -- inputs and outputs carry their
        own fields (PSBT_IN_PREVIOUS_TXID, PSBT_OUT_AMOUNT, ...). Two further checks
        apply to v2 specifically: _check_tx_modifiable refuses a transaction a
        coordinator may still change after we sign, and _assert_v2_complete refuses
        one whose mandatory per-input/per-output fields are missing.
        """
        version = getattr(self.psbt, 'version', None)
        if version in (None, 0, 2):
            return
        raise InvalidPSBTError('PSBT version {0} is not supported.'.format(version), code=RejectCode.UNSUPPORTED_PSBT_VERSION)

    def _check_tx_modifiable(self):
        """
        Refuse a v2 psbt whose transaction may still be modified after signing.

        BIP-370 PSBT_GLOBAL_TX_MODIFIABLE (key 0x06) is a one-byte flag field: bit 0
        allows adding or removing inputs, bit 1 outputs. A nonzero value means the
        coordinator can change what we are about to sign -- add an output that steals
        our coins, drop the destination, and so on -- after we have approved exactly
        what the screen showed. That voids the review entirely, so it is a refusal
        rather than a warning.

        embit does not parse this key into a named field (it lands in psbt.unknown),
        so it must be inspected explicitly. Absent means final: BIP-370 treats a
        missing TX_MODIFIABLE as 0x00, and the valid corpus vectors omit it.

        Only meaningful for v2 -- on a v0 psbt key 0x06 is just an unknown field with
        no modifiability semantics, so it must not trigger this refusal there.
        """
        if getattr(self.psbt, 'version', None) != 2:
            return
        value = self.psbt.unknown.get(b'\x06')
        if value is None:
            return
        if int.from_bytes(value, 'little') & 3:
            raise InvalidPSBTError('Modifiable (TX_MODIFIABLE): inputs or outputs can change after you sign.', code=RejectCode.TX_MODIFIABLE)

    def _assert_v2_complete(self):
        """
        Refuse a v2 psbt that omits fields BIP-370 makes mandatory per input and
        output, before any of its values are trusted for display or signing.

        embit parses a v2 record even when required fields are missing -- it simply
        leaves the slot empty: an output's amount becomes None (which would later die
        on `0 <= None`, a crash screen rather than a decision), an output's script
        becomes blank, and an input can lose its previous txid/vout while keeping a
        witness_utxo. Each of those is refused here instead of reaching the
        accounting or signing code half-described:

          * every input must name the utxo it spends (previous txid + vout) as well
            as carry utxo data -- the latter already trips MISSING_UTXO in
            _validate_input, exactly as for v0;
          * every output must carry an amount and a script.
        """
        if getattr(self.psbt, 'version', None) != 2:
            return
        for i, inp in enumerate(self.psbt.inputs):
            if inp.txid is None or inp.vout is None:
                raise InvalidPSBTError('Input {0} has no previous output (txid/vout).'.format(i), code=RejectCode.MISSING_UTXO)
        vout = self.psbt.tx.vout
        for i, out in enumerate(vout):
            value = out.value
            if value is None or not 0 <= value <= MAX_MONEY:
                raise InvalidPSBTError('Output {0} has no valid amount.'.format(i), code=RejectCode.AMOUNT_OUT_OF_RANGE)
            script = out.script_pubkey
            if script is None or len(script.data) == 0:
                raise InvalidPSBTError('Output {0} has no script.'.format(i), code=RejectCode.UNDISPLAYABLE_OUTPUT)

    def _check_tx_structure(self):
        """
        Refuse a transaction consensus would reject whatever it paid, and outputs with
        nothing to show.

        * No inputs: not a transaction. (No outputs is refused too, but in
          _parse_outputs, so that a more specific finding about the inputs -- a
          SIGHASH_SINGLE with no output to commit to, say -- is the one reported.)
        * The same outpoint spent twice: invalid, and its amount would be counted
          twice, into the fee on screen.
        * An output with an empty script: nothing to show the user. (Checked here for
          v0 too; _assert_v2_complete covers the v2 fields being absent.)
        """
        if not self.psbt.inputs:
            raise InvalidPSBTError('The transaction has no inputs.', code=RejectCode.INVALID_TRANSACTION)
        seen = set()
        for i, inp in enumerate(self.psbt.inputs):
            outpoint = (inp.txid, inp.vout)
            if outpoint in seen:
                raise InvalidPSBTError('Input {0} spends the same output as an earlier input.'.format(i), code=RejectCode.INVALID_TRANSACTION)
            seen.add(outpoint)
        for i, out in enumerate(self.psbt.tx.vout):
            if out.script_pubkey is None or len(out.script_pubkey.data) == 0:
                raise InvalidPSBTError('Output {0} has no script.'.format(i), code=RejectCode.UNDISPLAYABLE_OUTPUT)

    @staticmethod
    def _validate_input(index, inp):
        """
        Structural checks on a single input, before any of its values are
        trusted for display.

        A signature commits to the input amount (BIP-143) and to the script being
        satisfied. If the psbt's own description of the prevout is internally
        inconsistent, nothing derived from it -- the fee, the amounts on screen --
        means anything.
        """
        witness_utxo = inp.witness_utxo
        non_witness_utxo = inp.non_witness_utxo
        if witness_utxo is None and non_witness_utxo is None:
            raise InvalidPSBTError('Input {0} has no utxo'.format(index), code=RejectCode.MISSING_UTXO)
        if non_witness_utxo is not None:
            if non_witness_utxo.txid() != inp.txid:
                raise InvalidPSBTError('Input {0} previous tx does not match the txid it spends.'.format(index), code=RejectCode.UTXO_MISMATCH)
            if inp.vout is None or not 0 <= inp.vout < len(non_witness_utxo.vout):
                raise InvalidPSBTError('Input {0} spends an output its previous tx does not have.'.format(index), code=RejectCode.UTXO_MISMATCH)
        if witness_utxo is not None and non_witness_utxo is not None:
            real = non_witness_utxo.vout[inp.vout]
            if witness_utxo.value != real.value or witness_utxo.script_pubkey.data != real.script_pubkey.data:
                raise InvalidPSBTError('Input {0} utxo does not match the previous tx.'.format(index), code=RejectCode.UTXO_MISMATCH)
        utxo = witness_utxo if witness_utxo is not None else non_witness_utxo.vout[inp.vout]
        if not 0 <= utxo.value <= MAX_MONEY:
            raise InvalidPSBTError('Input {0} amount out of range: {1}'.format(index, utxo.value), code=RejectCode.AMOUNT_OUT_OF_RANGE)
        script_pubkey = utxo.script_pubkey
        script_type = script_pubkey.script_type()
        allowed_sighash = (None, SIGHASH_ALL)
        if script_type == 'p2tr':
            allowed_sighash += (SIGHASH_DEFAULT,)
        if inp.sighash_type not in allowed_sighash:
            raise InvalidPSBTError('Input {0} needs sighash {1:#04x}, not SIGHASH_ALL.'.format(index, inp.sighash_type), code=RejectCode.UNSUPPORTED_SIGHASH)
        if witness_utxo is not None and (not (PSBTParser._is_witness_program(script_pubkey) or script_type == 'p2sh')):
            raise InvalidPSBTError('Input {0} utxo declares a {1} script.'.format(index, script_type), code=RejectCode.INVALID_WITNESS_UTXO)
        effective_type = script_type
        if script_type == 'p2sh':
            if inp.redeem_script is None:
                raise InvalidPSBTError('Input {0} is p2sh with no redeem_script.'.format(index), code=RejectCode.SCRIPT_HASH_MISMATCH)
            if _dependency('embit', 'script').p2sh(inp.redeem_script).data != script_pubkey.data:
                raise InvalidPSBTError('Input {0} redeem_script does not match.'.format(index), code=RejectCode.SCRIPT_HASH_MISMATCH)
            effective_type = inp.redeem_script.script_type()
            if non_witness_utxo is None and effective_type not in ('p2wpkh', 'p2wsh'):
                raise InvalidPSBTError('Input {0} is legacy p2sh with no previous tx.'.format(index), code=RejectCode.INVALID_WITNESS_UTXO)
        if effective_type == 'p2wsh':
            if inp.witness_script is None:
                raise InvalidPSBTError('Input {0} is p2wsh with no witness_script.'.format(index), code=RejectCode.SCRIPT_HASH_MISMATCH)
            expected = inp.redeem_script if script_type == 'p2sh' else script_pubkey
            if _dependency('embit', 'script').p2wsh(inp.witness_script).data != expected.data:
                raise InvalidPSBTError('Input {0} witness_script does not match.'.format(index), code=RejectCode.SCRIPT_HASH_MISMATCH)
        elif inp.witness_script is not None:
            raise InvalidPSBTError('Input {0} has a stray witness_script.'.format(index), code=RejectCode.EXTRANEOUS_WITNESS_SCRIPT)

    def _parse_inputs(self, child_key_derivation_cache):
        self.input_amount = 0
        self.num_inputs = len(self.psbt.inputs)
        self.verified_input_prefixes = set()
        self.verified_max_input_index = -1
        for i, inp in enumerate(self.psbt.inputs):
            PSBTParser._validate_input(i, inp)
            if self.can_verify_derivations:
                for public_key, derivation, is_taproot in self._scope_keyed_derivations(inp):
                    if not derivation:
                        continue
                    if not self._verify_derivation(inp, public_key, derivation, child_key_derivation_cache, is_taproot=is_taproot):
                        continue
                    if len(derivation) >= 2:
                        self.verified_input_prefixes.add(tuple(derivation[:-2]))
                    self.verified_max_input_index = max(self.verified_max_input_index, derivation[-1] & 2147483647)
            if inp.witness_utxo:
                self.input_amount += inp.witness_utxo.value
                script_pubkey = inp.witness_utxo.script_pubkey
            elif inp.non_witness_utxo:
                self.input_amount += inp.utxo.value
                script_pubkey = inp.script_pubkey
            inp_policy = PSBTParser._get_policy(inp, script_pubkey, self.psbt.xpubs, child_key_derivation_cache)
            if self.policy == None:
                self.policy = inp_policy
            elif self.policy != inp_policy:
                raise InvalidPSBTError('Mixed inputs in the transaction', code=RejectCode.MIXED_INPUTS)
        if self.input_amount > MAX_MONEY:
            raise InvalidPSBTError('Inputs total {0} sats, more than can exist.'.format(self.input_amount), code=RejectCode.AMOUNT_OUT_OF_RANGE)

    @staticmethod
    def is_reachable_derivation(derivation, input_prefixes):
        """
        Whether a wallet scanning for this seed's addresses will ever find this
        one.

        The expectation is taken from the inputs rather than hardcoded: every
        input is a utxo the wallet already found, so the account prefix they
        share -- everything above the trailing branch/index pair -- is proof of
        where this wallet actually keeps its keys. A change output has to sit
        under that same prefix, on the receive (0) or change (1) branch.

        Deriving the rule from the inputs rather than asserting a fixed depth
        lets a genuinely unusual wallet layout work unchanged, while still
        refusing a change path that has been moved somewhere the wallet will
        never look.

        `input_prefixes` is None when no evidence could be gathered at all --
        the psbt carries no input bip32 derivations, or there was no key to
        verify them against (WIF/BIP38, or a seedless multisig pre-parse). Only
        the branch is checked then.

        An *empty set* is different and deliberately fails everything: we had a
        key to verify with and still gathered nothing, either because the inputs
        carried no derivations or because none held up. Such a psbt cannot be
        signed anyway -- without a usable input derivation there is no key to
        sign with -- and treating "no evidence" as permission would let an
        attacker switch the check off just by withholding it.
        """
        if len(derivation) < 2:
            return False
        if derivation[-2] not in (0, 1):
            return False
        if input_prefixes is not None and tuple(derivation[:-2]) not in input_prefixes:
            return False
        return True

    @staticmethod
    def _scope_derivations(scope):
        """Every claimed bip32 derivation on a scope, taproot and non-taproot alike."""
        derivations = [d.derivation for d in scope.bip32_derivations.values()]
        derivations += [d.derivation for _, d in scope.taproot_bip32_derivations.values()]
        return derivations

    @staticmethod
    def _first_claimed_derivation_path(scope):
        """
        The first coordinator-claimed derivation path on a scope, or None.

        Only used when there is no BIP32 tree to verify against (the seedless
        multisig pre-parse), where the change_data has to carry some path for the
        view to display and the descriptor check is what ultimately verifies the
        output.
        """
        for derivation_path_obj in scope.bip32_derivations.values():
            return list(derivation_path_obj.derivation)
        for _leaf_hashes, derivation_path_obj in scope.taproot_bip32_derivations.values():
            return list(derivation_path_obj.derivation)
        return None

    @staticmethod
    def _scope_keyed_derivations(scope):
        """
        Every claimed derivation paired with the pubkey it claims to produce, and
        whether that claim is a taproot one. Taproot keys are stored x-only and so
        have to be compared differently -- see seed_owns_pubkey.
        """
        triples = [(pub, d.derivation, False) for pub, d in scope.bip32_derivations.items()]
        triples += [(pub, d.derivation, True) for pub, (_, d) in scope.taproot_bip32_derivations.items()]
        return triples

    @staticmethod
    def _input_commits_to_key(inp, derived_key):
        """
        Whether the input being spent actually commits to `derived_key`.

        Re-deriving proves a path belongs to this seed, but not that it is the
        path of *this utxo*: an attacker holding the account xpub can supply a
        matched path/pubkey pair from somewhere else in our own tree. Only the
        prevout's script says which key really unlocks these coins.
        """
        utxo = inp.witness_utxo or (inp.non_witness_utxo.vout[inp.vout] if inp.non_witness_utxo else None)
        if utxo is None:
            return False
        script_pubkey = utxo.script_pubkey
        script_type = script_pubkey.script_type()
        if script_type == 'p2sh' and inp.redeem_script is not None:
            script_pubkey = inp.redeem_script
            script_type = script_pubkey.script_type()
        sec = derived_key.key.sec()
        if script_type == 'p2wpkh':
            return _dependency('embit', 'script').p2wpkh(derived_key).data == script_pubkey.data
        if script_type == 'p2pkh':
            return _dependency('embit', 'script').p2pkh(derived_key).data == script_pubkey.data
        if script_type == 'p2wsh':
            return inp.witness_script is not None and sec in inp.witness_script.data
        if script_type == 'p2tr':
            if inp.taproot_internal_key is not None:
                return inp.taproot_internal_key.xonly() == derived_key.key.xonly()
            return _dependency('embit', 'script').p2tr(derived_key).data == script_pubkey.data
        if script_type is None:
            return sec in script_pubkey.data
        return False

    def _verify_derivation(self, inp, public_key, derivation, child_key_derivation_cache=None, is_taproot=False):
        """
        Whether this seed really does produce `public_key` at `derivation`, *and*
        whether the utxo being spent actually commits to that key.

        The path and the pubkey both come from the coordinator, so on their own
        they are a matched pair of claims -- an attacker who knows our xpub can
        supply a self-consistent lie drawn from elsewhere in our own tree. Both
        halves are needed: re-deriving makes it a fact about this seed, and the
        script check makes it a fact about this utxo.

        The first half is seed_owns_pubkey, which compares x-only for taproot and
        the full key for ecdsa. The second half is this file's own contribution
        and has no equivalent upstream.
        """
        if not self.can_verify_derivations:
            return False
        try:
            if not PSBTParser.seed_owns_pubkey(self.root, derivation, public_key, child_key_derivation_cache, is_taproot=is_taproot, root_path=self.root_path):
                return False
            derived = PSBTParser._derive_with_cache_via_indices(self.root, derivation[len(self.root_path):], child_key_derivation_cache)
        except FeatureUnavailable:
            raise
        except Exception as e:
            pass
            return False
        return PSBTParser._input_commits_to_key(inp, derived)

    def _parse_outputs(self, child_key_derivation_cache):
        """
        Sorts each output into change coming back to this seed, an external spend, or
        OP_RETURN data, and totals the amounts for each. Note that self-transfer/receive
        outputs are also considered "change".

        Most of the work here is sorting through the psbt's claims about which, if any,
        outputs are paying a key that can be derived from our seed, and then doing all
        possible independent verifications for the given output data.

        The refusals this raises carry RejectCode (see InvalidPSBTError) rather than a
        dedicated exception type per condition; the view layer routes on the code.
        """
        '********************* How output ownership is determined *********************\n        Many outputs are obviously NOT ours. An output is only considered possible\n        change if its policy matches the inputs\' policy "shape" (script type, plus m-of-n\n        for multisig; see parse()); anything else is recorded as an external spend.\n\n        The psbt will usually annotate which key(s) a change output pays (see embit\'s\n        bip32_derivations and taproot_bip32_derivations), but this is just a claim\n        supplied by the coordinator. These annotations are not authoritative. But such\n        claims are significant; if our checks prove that the claim is false, we consider\n        the deception an attack.\n\n        -- Proving the claim --\n        The output\'s scriptPubKey determines where the value ACTUALLY goes. But the\n        scriptPubKey only contains a hash of the spending conditions (note: taproot uses a\n        tweaked key instead), so we can\'t simply inspect the scriptPubKey to determine if\n        the output is ours.\n\n        We must build our own version of the scriptPubKey via:\n          * single sig: derive a key from our seed using the claimed derivation path.\n          * multisig: hash the claimed witness_script or redeem_script, then check that a\n            key derived from our seed is among that script\'s keys.\n\n        That leaves us holding two independent answers about the same output: which key it\n        commits to (our rebuild, matched against the scriptPubKey), and which key the psbt\n        says it commits to (the claim). We evaluate the output on those two facts:\n\n                                     | claims this seed     | doesn\'t claim this seed\n            -------------------------+----------------------+-------------------------\n            commits to our key       | presumed change      | contradiction\n            commits to another key   | contradiction        | presumed external spend\n\n        If our two answers contradict each other, the psbt has been caught in a deception.\n        We raise an exception and reject the psbt.\n\n        Multisig change can\'t be fully verified until later in the process, so we use\n        "presumed" to avoid conveying a false impression of certainty. Single sig carries\n        its own note later in this function about its guarantees.\n\n        (note one exception: no taproot mismatch is rejected. A script tree tweaks our\n        internal key, so an honest taproot change output fails to match too, and we cannot\n        yet tell that apart from an output that claims our key but pays someone else. All\n        taproot mismatches pass as EXTERNAL spends and are never considered "change".)\n        ******************************************************************************'
        self.spend_amount = 0
        self.change_amount = 0
        self.change_data = []
        self.fee_amount = 0
        self.op_return_amount = 0
        self.op_return_payloads = []
        self.risk_warnings = set()
        self.destination_addresses = []
        self.destination_amounts = []
        vout = self.psbt.tx.vout
        if not vout:
            raise InvalidPSBTError('The transaction has no outputs.', code=RejectCode.INVALID_TRANSACTION)
        for i, out in enumerate(self.psbt.outputs):
            value = vout[i].value
            if not 0 <= value <= MAX_MONEY:
                raise InvalidPSBTError('Output {0} amount out of range: {1}'.format(i, value), code=RejectCode.AMOUNT_OUT_OF_RANGE)
            out_policy = PSBTParser._get_policy(out, vout[i].script_pubkey, self.psbt.xpubs, child_key_derivation_cache)
            is_presumed_change = False
            if PSBTParser._policy_shape_matches(out_policy, self.policy):
                singlesig_derivation_path = None
                multisig_script = None
                rebuilt_script_pubkey = _dependency('embit', 'script').Script(b'')
                if self.policy['type'] == 'p2wsh':
                    multisig_script = out.witness_script
                    rebuilt_script_pubkey = _dependency('embit', 'script').p2wsh(multisig_script)
                elif self.policy['type'] == 'p2sh-p2wsh':
                    multisig_script = out.witness_script
                    rebuilt_script_pubkey = _dependency('embit', 'script').p2sh(_dependency('embit', 'script').p2wsh(multisig_script))
                elif self.policy['type'] == 'p2sh':
                    multisig_script = out.redeem_script
                    rebuilt_script_pubkey = _dependency('embit', 'script').p2sh(multisig_script)
                elif self.policy['type'] in ('p2pkh', 'p2sh-p2wpkh', 'p2wpkh'):
                    if len(out.bip32_derivations) > 1:
                        raise InvalidPSBTError('Output {0} names more than one key for a single-key script.'.format(i), code=RejectCode.SURPLUS_DERIVATIONS)
                    if len(out.bip32_derivations.values()) == 1 and self.can_verify_derivations:
                        singlesig_derivation_path = list(out.bip32_derivations.values())[0]
                        seed_public_key = PSBTParser._derive_with_cache_via_derivation_path(self.root, singlesig_derivation_path, child_key_derivation_cache, root_path=self.root_path).get_public_key()
                        rebuilt_script_pubkey = PSBTParser._build_singlesig_script(self.policy['type'], seed_public_key)
                    else:
                        pass
                elif self.policy['type'] == 'p2tr':
                    taproot_entries = list(out.taproot_bip32_derivations.values())
                    if len(taproot_entries) == 0:
                        pass
                    else:
                        internal_key_claims = sum((1 for leaf_hashes, _ in taproot_entries if not leaf_hashes))
                        if internal_key_claims > 1:
                            raise InvalidPSBTError('Output {0} names more than one taproot internal key.'.format(i), code=RejectCode.SURPLUS_DERIVATIONS)
                        if len(taproot_entries) == 1 and internal_key_claims == 1 and self.can_verify_derivations:
                            leaf_hashes, singlesig_derivation_path = taproot_entries[0]
                            seed_public_key = PSBTParser._derive_with_cache_via_derivation_path(self.root, singlesig_derivation_path, child_key_derivation_cache, root_path=self.root_path).get_public_key()
                            rebuilt_script_pubkey = PSBTParser._build_singlesig_script(self.policy['type'], seed_public_key)
                        else:
                            pass
                else:
                    raise InvalidPSBTError('Unsupported script type: {0}'.format(self.policy['type']), code=RejectCode.UNDISPLAYABLE_OUTPUT)
                verified_derivation_paths = self.verified_output_derivation_paths[i] if self.can_verify_derivations else []
                if rebuilt_script_pubkey.data == vout[i].script_pubkey.data:
                    if singlesig_derivation_path is not None:
                        if verified_derivation_paths == []:
                            raise InvalidPSBTError('Output {0} pays this seed at {1} but does not claim it there.'.format(i, _dependency('embit', 'bip32').path_to_str(singlesig_derivation_path.derivation)), code=RejectCode.MISLABELED_OUTPUT_OWNERSHIP)
                        if verified_derivation_paths != [singlesig_derivation_path]:
                            raise RuntimeError('Output {0} verified at a path it does not pay'.format(i))
                        is_presumed_change = True
                    elif multisig_script is not None:
                        if not self.can_verify_derivations:
                            if self.multisig_descriptor is not None and self._descriptor_owns_output(self.multisig_descriptor, i):
                                is_presumed_change = True
                            else:
                                self.unidentified_change_outputs.append(i)
                        elif verified_derivation_paths == []:
                            for derivation_path_obj in out.bip32_derivations.values():
                                seed_public_key = PSBTParser._derive_with_cache_via_derivation_path(self.root, derivation_path_obj, child_key_derivation_cache, root_path=self.root_path).get_public_key()
                                if PSBTParser._multisig_script_contains_key(multisig_script, seed_public_key):
                                    raise InvalidPSBTError("Output {0} commits to this seed's key at {1} but claims another fingerprint and/or key there.".format(i, _dependency('embit', 'bip32').path_to_str(derivation_path_obj.derivation)), code=RejectCode.MISLABELED_OUTPUT_OWNERSHIP)
                            pass
                        else:
                            for verified_derivation_path in verified_derivation_paths:
                                seed_public_key = PSBTParser._derive_with_cache_via_derivation_path(self.root, verified_derivation_path, child_key_derivation_cache, root_path=self.root_path).get_public_key()
                                if not PSBTParser._multisig_script_contains_key(multisig_script, seed_public_key):
                                    raise InvalidPSBTError('Output {0} claims this seed at {1} but its committed script does not hold that key.'.format(i, _dependency('embit', 'bip32').path_to_str(verified_derivation_path.derivation)), code=RejectCode.FORGED_OUTPUT_OWNERSHIP)
                            if len(out.bip32_derivations) > self.policy['n']:
                                raise InvalidPSBTError('Output {0} claims more keys than its script uses.'.format(i), code=RejectCode.SURPLUS_DERIVATIONS)
                            is_presumed_change = True
                            input_cosigners = self.policy.get('cosigners')
                            output_cosigners = out_policy.get('cosigners')
                            if input_cosigners is not None and input_cosigners != output_cosigners:
                                is_presumed_change = False
                            if is_presumed_change and 'cosigners' not in self.policy:
                                if self.multisig_descriptor is None or not self._descriptor_owns_output(self.multisig_descriptor, i):
                                    is_presumed_change = False
                                    self.unidentified_change_outputs.append(i)
                elif verified_derivation_paths != [] and self.policy['type'] != 'p2tr':
                    raise InvalidPSBTError('Output {0} claims this seed at {1} but its committed script contradicts that.'.format(i, _dependency('embit', 'bip32').path_to_str(verified_derivation_paths[0].derivation)), code=RejectCode.FORGED_OUTPUT_OWNERSHIP)
            if is_presumed_change:
                derivations = self._scope_derivations(out)
                unreachable = [d for d in derivations if not PSBTParser.is_reachable_derivation(d, self.verified_input_prefixes if self.can_verify_derivations else None)]
                if unreachable:
                    raise InvalidPSBTError('Change path {0} is outside this wallet.'.format(_dependency('embit', 'bip32').path_to_str(unreachable[0])), code=RejectCode.UNREACHABLE_CHANGE_PATH)
                if self.change_index_lookahead > 0 and self.verified_max_input_index >= 0:
                    ceiling = self.verified_max_input_index + self.change_index_lookahead
                    for derivation in derivations:
                        index = derivation[-1] & 2147483647
                        if index > ceiling:
                            raise InvalidPSBTError('Change index {0} past gap limit (inputs {1}).'.format(index, self.verified_max_input_index), code=RejectCode.CHANGE_INDEX_TOO_FAR)
            if vout[i].script_pubkey.data[0] == OPCODES.OP_RETURN:
                payload = PSBTParser._op_return_payload(vout[i].script_pubkey.data)
                if payload is None:
                    raise InvalidPSBTError('Output {0} OP_RETURN data is malformed.'.format(i), code=RejectCode.UNDISPLAYABLE_OUTPUT)
                self.op_return_payloads.append(payload)
                self.op_return_amount += vout[i].value
                if vout[i].value > 0:
                    raise InvalidPSBTError('Output {0} burns {1} sats in an OP_RETURN.'.format(i, vout[i].value), code=RejectCode.NONZERO_OP_RETURN)
            elif is_presumed_change:
                addr = vout[i].script_pubkey.address(_dependency('embit.networks', 'NETWORKS')[_dependency('seedsigner.models.settings', 'SettingsConstants').map_network_to_embit(self.network)])
                verified_path = self.verified_output_derivation_paths[i][0].derivation if self.can_verify_derivations else PSBTParser._first_claimed_derivation_path(out)
                self.change_data.append({'output_index': i, 'address': addr, 'amount': vout[i].value, 'verified_derivation_path': verified_path})
                self.change_amount += vout[i].value
            else:
                try:
                    addr = vout[i].script_pubkey.address(_dependency('embit.networks', 'NETWORKS')[_dependency('seedsigner.models.settings', 'SettingsConstants').map_network_to_embit(self.network)])
                except (ValueError, _dependency('embit.base', 'EmbitError')) as e:
                    raise InvalidPSBTError('Output {0} script cannot be shown as an address.'.format(i), code=RejectCode.UNDISPLAYABLE_OUTPUT) from e
                self.destination_addresses.append(addr)
                self.destination_amounts.append(vout[i].value)
                self.spend_amount += vout[i].value
        self.fee_amount = self.psbt.fee()
        if self.fee_amount < 0:
            raise InvalidPSBTError('Outputs exceed inputs by {0} sats'.format(-self.fee_amount), code=RejectCode.NEGATIVE_FEE)
        accounted = self.spend_amount + self.change_amount + self.op_return_amount + self.fee_amount
        if accounted != self.input_amount:
            raise InvalidPSBTError('Amounts do not add up: {0} vs {1} in.'.format(accounted, self.input_amount), code=RejectCode.AMOUNT_OUT_OF_RANGE)
        self._collect_risk_warnings()
        return True

    @staticmethod
    def _amount_is_unproven(inp):
        """
        A segwit v0 input (native or p2sh-wrapped) with no previous transaction: its
        amount is the coordinator's word, and only its own signature commits to it.
        See RiskWarning.UNVERIFIED_INPUT_AMOUNTS. Taproot commits to every input's
        amount, and a legacy input without a previous transaction is already refused.
        """
        if inp.non_witness_utxo is not None or inp.witness_utxo is None:
            return False
        script_type = inp.witness_utxo.script_pubkey.script_type()
        if script_type == 'p2sh' and inp.redeem_script is not None:
            script_type = inp.redeem_script.script_type()
        return script_type in ('p2wpkh', 'p2wsh')

    def _collect_risk_warnings(self):
        """
        Flag the things a user would want to know before approving, none of
        which make the transaction invalid.
        """
        if self.input_amount > 0 and self.fee_amount * HIGH_FEE_DENOMINATOR >= self.input_amount * HIGH_FEE_NUMERATOR:
            self.risk_warnings.add(RiskWarning.HIGH_FEE)
        self._check_fee_rate()
        if len(self.psbt.inputs) >= 2 and any((PSBTParser._amount_is_unproven(inp) for inp in self.psbt.inputs)):
            self.risk_warnings.add(RiskWarning.UNVERIFIED_INPUT_AMOUNTS)
        for vout in self.psbt.tx.vout:
            if vout.script_pubkey.data and vout.script_pubkey.data[0] == OPCODES.OP_RETURN:
                continue
            if vout.value < DUST_THRESHOLD:
                self.risk_warnings.add(RiskWarning.DUST_OUTPUT)
                break
        self.locktime_is_enforced = any((vin.sequence != SEQUENCE_FINAL for vin in self.psbt.tx.vin))
        locktime = self.psbt.tx.locktime or 0
        self.locktime = locktime
        if self.locktime_is_enforced and locktime >= LOCKTIME_TIMESTAMP_THRESHOLD and (locktime > _dependency('seedsigner_port.psbt_clock', None).time()):
            self.risk_warnings.add(RiskWarning.FUTURE_LOCKTIME)
        for vin in self.psbt.tx.vin:
            if vin.sequence < RBF_SEQUENCE_CEILING:
                self.risk_warnings.add(RiskWarning.RBF)
                break
        self._check_far_future_locktime(locktime)
        if (self.psbt.tx.version or 0) >= 2:
            for vin in self.psbt.tx.vin:
                if vin.sequence & SEQUENCE_LOCKTIME_DISABLE_FLAG:
                    continue
                if vin.sequence & SEQUENCE_LOCKTIME_MASK:
                    self.risk_warnings.add(RiskWarning.RELATIVE_TIMELOCK)
                    break
        vout = self.psbt.tx.vout
        for i, out in enumerate(self.psbt.outputs):
            committed = PSBTParser._committed_output_script(out, vout[i].script_pubkey)
            if committed is not None and PSBTParser._script_has_timelock(committed):
                self.risk_warnings.add(RiskWarning.SCRIPT_TIMELOCK)
                break

    @staticmethod
    def _committed_output_script(out, script_pubkey):
        """The supplied witness or redeem script this output is provably locked by, if any."""
        if out.witness_script is not None:
            wsh = _dependency('embit', 'script').p2wsh(out.witness_script).data
            if wsh == script_pubkey.data or _dependency('embit', 'script').p2sh(_dependency('embit', 'script').Script(wsh)).data == script_pubkey.data:
                return out.witness_script
        if out.redeem_script is not None and _dependency('embit', 'script').p2sh(out.redeem_script).data == script_pubkey.data:
            return out.redeem_script
        return None

    @staticmethod
    def _script_ops(data):
        """
        Yields (opcode, pushed_bytes) for each operation in a script; pushed_bytes is
        None for anything that is not a push. A push that runs past the end of the
        script yields what is there and stops.
        """
        pos = 0
        while pos < len(data):
            op = data[pos]
            pos += 1
            if 1 <= op <= 75:
                length = op
            elif op == OPCODES.OP_PUSHDATA1:
                length, pos = (int.from_bytes(data[pos:pos + 1], 'little'), pos + 1)
            elif op == OPCODES.OP_PUSHDATA2:
                length, pos = (int.from_bytes(data[pos:pos + 2], 'little'), pos + 2)
            elif op == OPCODES.OP_PUSHDATA4:
                length, pos = (int.from_bytes(data[pos:pos + 4], 'little'), pos + 4)
            else:
                yield (op, None)
                continue
            yield (op, data[pos:pos + length])
            pos += length

    @staticmethod
    def _script_has_timelock(sc):
        """
        Whether a script runs OP_CHECKLOCKTIMEVERIFY or OP_CHECKSEQUENCEVERIFY.
        Walks the opcodes rather than searching the bytes, so a push that happens
        to contain 0xb1 or 0xb2 is not mistaken for one.
        """
        return any((op in (OPCODES.OP_CHECKLOCKTIMEVERIFY, OPCODES.OP_CHECKSEQUENCEVERIFY) for op, _pushed in PSBTParser._script_ops(sc.data)))

    @staticmethod
    def _op_return_payload(data):
        """
        The data an OP_RETURN script carries: everything its pushes push, in order.
        None if anything after the OP_RETURN is not a complete data push -- a push
        that runs past the end of the script, or a non-push opcode -- since no
        display of it would be faithful.

        Payloads of 75 bytes or fewer are pushed directly (OP_RETURN <len> <data>),
        which is how Bitcoin Core writes them; OP_PUSHDATA1 is only for longer ones.
        Slicing at a fixed offset dropped the first byte of every short payload.
        """
        body = data[1:]
        payload = b''
        pos = 0
        while pos < len(body):
            op = body[pos]
            pos += 1
            if op == 0:
                continue
            if op <= 75:
                length = op
            elif op in (OPCODES.OP_PUSHDATA1, OPCODES.OP_PUSHDATA2, OPCODES.OP_PUSHDATA4):
                width = {OPCODES.OP_PUSHDATA1: 1, OPCODES.OP_PUSHDATA2: 2, OPCODES.OP_PUSHDATA4: 4}[op]
                if pos + width > len(body):
                    return None
                length = int.from_bytes(body[pos:pos + width], 'little')
                pos += width
            else:
                return None
            if pos + length > len(body):
                return None
            payload += body[pos:pos + length]
            pos += length
        return payload

    @staticmethod
    def trim(tx):
        trimmed_psbt = _dependency('embit', 'psbt').PSBT(tx.tx)
        for i, inp in enumerate(tx.inputs):
            if inp.final_scriptwitness:
                trimmed_psbt.inputs[i].final_scriptwitness = inp.final_scriptwitness
            else:
                trimmed_psbt.inputs[i].partial_sigs = inp.partial_sigs
        return trimmed_psbt

    @staticmethod
    def sig_count(tx):
        cnt = 0
        for i, inp in enumerate(tx.inputs):
            if inp.final_scriptwitness is not None:
                cnt += 1
            else:
                cnt += len(list(inp.partial_sigs.keys()))
        return cnt

    @staticmethod
    def _get_policy(scope, scriptpubkey, xpubs, child_key_derivation_cache):
        """Parse scope and get policy"""
        script_type = scriptpubkey.script_type()
        if script_type == 'p2sh':
            if scope.witness_script is not None:
                script_type = 'p2sh-p2wsh'
            elif scope.redeem_script is not None and scope.redeem_script.script_type() == 'p2wpkh':
                script_type = 'p2sh-p2wpkh'
        policy = {'type': script_type}
        script = None
        if script_type:
            if 'p2wsh' in script_type and scope.witness_script is not None:
                script = scope.witness_script
            elif 'p2sh' == script_type and scope.redeem_script is not None:
                script = scope.redeem_script
            if script is not None:
                try:
                    m, n, pubkeys = PSBTParser._parse_multisig(script)
                except (ValueError, _dependency('embit.base', 'EmbitError')) as e:
                    pass
                    return policy
                try:
                    cosigners = PSBTParser._get_cosigners(pubkeys, scope.bip32_derivations, xpubs, child_key_derivation_cache)
                    policy.update({'m': m, 'n': n, 'cosigners': cosigners})
                except FeatureUnavailable:
                    raise
                except:
                    policy.update({'m': m, 'n': n})
        return policy

    @staticmethod
    def _policy_shape_matches(policy_a, policy_b):
        """
        Compares two policies on the shape of the script they describe: the script type,
        plus m-of-n for multisig.

        A policy can also carry the cosigners resolved from the coordinator's global
        xpubs. Those are never authoritative here, and comparing them would let a psbt
        decide which of its own outputs get verified: one misannotated fingerprint makes
        that output's cosigners fail to resolve, and the output then stops matching the
        inputs' policy. Shape comes from the scriptPubKey and the supplied script, and the
        caller proves ownership rather than assuming it.
        """
        for field in ('type', 'm', 'n'):
            if policy_a.get(field) != policy_b.get(field):
                return False
        return True

    @staticmethod
    def _build_singlesig_script(policy_type, public_key):
        """
        Builds the scriptPubKey that pays public_key under the given single-sig
        policy_type.
        """
        if policy_type == 'p2pkh':
            return _dependency('embit', 'script').p2pkh(public_key)
        if policy_type == 'p2sh-p2wpkh':
            return _dependency('embit', 'script').p2sh(_dependency('embit', 'script').p2wpkh(public_key))
        if policy_type == 'p2wpkh':
            return _dependency('embit', 'script').p2wpkh(public_key)
        if policy_type == 'p2tr':
            return _dependency('embit', 'script').p2tr(public_key)
        raise RuntimeError('Not a single-sig script type: {0}'.format(policy_type))

    @staticmethod
    def _parse_multisig(multisig_script):
        """Takes a script and extracts m,n and pubkeys from it"""
        if len(multisig_script.data) < 37 or multisig_script.data[-1] != 174:
            raise ValueError('Not a multisig script')
        m = multisig_script.data[0] - 80
        if m < 1 or m > 16:
            raise ValueError('Invalid multisig script')
        n = multisig_script.data[-2] - 80
        if n < m or n > 16:
            raise ValueError('Invalid multisig script')
        s = _dependency('io', 'BytesIO')(multisig_script.data)
        s.read(1)
        pubkeys = []
        for i in range(n):
            char = s.read(1)
            if char != b'!':
                raise ValueError('Invlid pubkey')
            pubkeys.append(_dependency('embit', 'ec').PublicKey.parse(s.read(33)))
        if s.read() != multisig_script.data[-2:]:
            raise ValueError('Invalid multisig script')
        return (m, n, pubkeys)

    @staticmethod
    def _multisig_script_contains_key(multisig_script, public_key):
        """
        Determines whether multisig_script includes the provided public_key.
        """
        m, n, pubkeys = PSBTParser._parse_multisig(multisig_script)
        return any((pubkey.sec() == public_key.sec() for pubkey in pubkeys))

    @staticmethod
    def _derive_with_cache_via_indices(parent_key, derivation_path, child_key_derivation_cache=None):
        """
        Derives the key that sits at the given derivation path below parent_key, reusing
        any levels along the way that have already been derived during this parse.

        A derivation path is traversed one level at a time, and two derivation paths that
        begin the same way share those opening levels. Each level reached is stored in the
        cache, so a later derivation running through that level picks it up instead of
        deriving it a second time.

        Entries are keyed on (id(parent_key), derivation_path_so_far), the path traversed
        down from that parent to reach this point. id() is the Python built-in for an
        object's identity; the parent belongs in the key because a multisig parse runs
        these same derivations below each cosigner's xpub in turn.

        Each entry also holds on to the parent it was derived from. id() is only the
        object's address, which Python is free to hand to a new object once the original
        is released. Keeping the parent means its address cannot be reused for as long as
        the entry it belongs to is alive.

        Keying on the parent's fingerprint was rejected: four bytes is small enough for a
        malicious coordinator to grind a deliberate collision, and the cosigner xpubs come
        from the psbt.

        The cache stops accepting new levels at MAX_CACHED_DERIVATIONS.
        """
        if child_key_derivation_cache is None:
            return parent_key.derive(derivation_path)
        derived_key = parent_key
        derivation_path_so_far = ()
        for index in derivation_path:
            derivation_path_so_far += (index,)
            cache_key = (id(parent_key), derivation_path_so_far)
            cached_entry = child_key_derivation_cache.get(cache_key)
            if cached_entry is None:
                already_derived = derived_key.child(index)
                if len(child_key_derivation_cache) < PSBTParser.MAX_CACHED_DERIVATIONS:
                    child_key_derivation_cache[cache_key] = (parent_key, already_derived)
            else:
                cached_parent, already_derived = cached_entry
            derived_key = already_derived
        return derived_key

    @staticmethod
    def _derive_with_cache_via_derivation_path(parent_key, derivation_path, child_key_derivation_cache=None, root_path=None):
        """
        _derive_with_cache_via_indices for a psbt entry: derives at the entry's full
        derivation path below parent_key.

        The DerivationPath.fingerprint is completely ignored; this function allows for
        deriving a key even when it's known that the fingerprint doesn't match (e.g. to
        catch a false claim).

        The entry's path is always measured from the master key. When parent_key is not
        the master (a smartcard's account-level xpub), root_path names where it sits and
        that many leading levels are dropped before deriving. See PSBTParser.root_path.
        """
        indices = derivation_path.derivation
        if root_path:
            indices = indices[len(root_path):]
        return PSBTParser._derive_with_cache_via_indices(parent_key, indices, child_key_derivation_cache)

    @staticmethod
    def _get_cosigners(pubkeys, derivations, xpubs, child_key_derivation_cache):
        """
        Traces every key in a multisig script back to the global xpub it was derived
        from, then returns the xpubs it found as a sorted list of base58 strings.

        Args:
          * pubkeys: The keys that actually appear in the script (the witness script for
            segwit; the redeem script for legacy p2sh). Extracted by _get_policy(). One
            per cosigner.

          * derivations: (embit's bip32_derivations) Each pubkey's associated fingerprint
            and full derivation path (e.g. m/48'/0'/0'/2'/1/5). A dict keyed on each
            pubkey.

          * xpubs: aka "global xpubs". The account-level xpub, with its associated
            fingerprint and derivation path, but only down to the account level (e.g.
            m/48'/0'/0'/2'). A dict keyed on each xpub.

        The derivations and xpubs are unproven claims provided by the coordinator. So we
        take each pubkey's claimed derivation path and check whether one of the xpubs
        really derives that pubkey.

        The resulting cosigners list consists of each xpub that provably derives each of
        the script's keys. But that is ALL it proves. We have no way to verify who those
        xpubs actually belong to; the coordinator can list any xpubs it likes.

        The list is sorted so that two scripts holding the same wallet's keys in a
        different order resolve to the same cosigners.

        Note that the bip32_derivations and the global xpubs are both optional psbt
        fields. If either is omitted or incomplete, this function raises rather than
        return a partial list.
        """
        if not xpubs:
            raise ValueError('No global xpubs supplied')
        if not derivations:
            raise ValueError('No derivation paths supplied')
        cosigners = []
        for i, pubkey in enumerate(pubkeys):
            if pubkey not in derivations:
                raise ValueError('Missing derivation')
            der = derivations[pubkey]
            for xpub in xpubs:
                origin_der = xpubs[xpub]
                if origin_der.derivation == der.derivation[:-2]:
                    derived_key = PSBTParser._derive_with_cache_via_indices(xpub, der.derivation[-2:], child_key_derivation_cache)
                    if derived_key.key == pubkey:
                        cosigners.append(xpub.to_base58())
                        break
        if len(cosigners) != len(pubkeys):
            raise RuntimeError("Can't get all cosigners")
        return sorted(cosigners)

    @staticmethod
    def get_input_fingerprints(psbt):
        """
            Exctracts the fingerprint from each input's derivation path.

            TODO: It's unclear if these derivations/fingerprints would ever be missing.
            Research on PSBT standard and known wallet coordinator implementations
            needed.
        """
        fingerprints = set()
        for input in psbt.inputs:
            for pub, derivation_path in input.bip32_derivations.items():
                fingerprints.add(_dependency('binascii', 'hexlify')(derivation_path.fingerprint).decode())
            for pub, (leaf_hashes, derivation_path) in input.taproot_bip32_derivations.items():
                if len(leaf_hashes) > 0:
                    raise Exception('Signing script path spends is not yet implemented')
                fingerprints.add(_dependency('binascii', 'hexlify')(derivation_path.fingerprint).decode())
        return list(fingerprints)

    @staticmethod
    def wif_can_sign_any_input(psbt, wif_key):
        """
            Returns True if a raw private key controls any input of this psbt.

            A WIF has no BIP32 tree, so the fingerprint routing that steers seeds finds
            nothing to match -- and the psbt an Electrum watch-only single-address wallet
            exports carries no derivation fields at all, so there is nothing to match
            against either. Both facts made ``has_matching_input_fingerprint`` answer
            False for keys that sign the transaction perfectly well.

            The test applied here is the one embit's ``PSBT.sign_with`` itself uses: the
            key's pubkey, or its hash160, appearing in the input's script. Taproot is
            checked against the input's declared internal key, since a p2tr scriptPubkey
            holds the *tweaked* output key rather than the one we hold.

            Like has_matching_input_fingerprint this is only a routing hint. It verifies
            nothing; real verification happens once the key reaches a PSBTParser.
        """
        try:
            pub = wif_key.privkey.get_public_key()
        except FeatureUnavailable:
            raise
        except Exception:
            return False
        sec = pub.sec()
        pkh = _dependency('embit', 'hashes').hash160(sec)
        xonly = pub.xonly()
        for inp in psbt.inputs:
            internal_key = getattr(inp, 'taproot_internal_key', None)
            if internal_key is not None:
                try:
                    if internal_key.xonly() == xonly:
                        return True
                except FeatureUnavailable:
                    raise
                except Exception:
                    pass
            script_obj = inp.witness_script or inp.redeem_script
            if script_obj is None:
                utxo = None
                try:
                    utxo = inp.utxo
                except FeatureUnavailable:
                    raise
                except Exception:
                    utxo = None
                if utxo is None:
                    continue
                script_obj = utxo.script_pubkey
            data = getattr(script_obj, 'data', None)
            if not data:
                continue
            if sec in data or pkh in data:
                return True
        return False

    @staticmethod
    def has_matching_input_fingerprint(psbt, seed=None, network=_dependency('seedsigner.models.settings', 'SettingsConstants').MAINNET, *, root=None):
        """
            Extracts the claimed fingerprint from each psbt input. Returns True if any
            match the provided seed.

            This is merely a routing hint to help the user select a seed that looks like
            it should be able to sign the psbt; it verifies nothing. Actual verification
            only begins once a seed has been selected and passed into a PSBTParser
            instance.
        """
        if seed is not None:
            seed_fingerprint = seed.get_fingerprint(network)
        elif root is not None:
            seed_fingerprint = _dependency('binascii', 'hexlify')(root.child(0).fingerprint).decode()
        else:
            return False

        def check_fingerprint_match(public_key, derivation_path_obj, is_taproot):
            """Check fingerprint match with missing fingerprint fallback"""
            if _dependency('binascii', 'hexlify')(derivation_path_obj.fingerprint).decode() == seed_fingerprint:
                return True
            if derivation_path_obj.fingerprint == b'\x00\x00\x00\x00':
                try:
                    if root is not None:
                        fallback_root = root
                    elif hasattr(seed, 'get_root'):
                        fallback_root = seed.get_root(network)
                    else:
                        fallback_root = _dependency('embit', 'bip32').HDKey.from_seed(seed.seed_bytes, version=_dependency('embit.networks', 'NETWORKS')[_dependency('seedsigner.models.settings', 'SettingsConstants').map_network_to_embit(network)]['xprv'])
                    return PSBTParser.seed_owns_pubkey(fallback_root, derivation_path_obj.derivation, public_key, child_key_derivation_cache=None, is_taproot=is_taproot)
                except FeatureUnavailable:
                    raise
                except Exception as e:
                    pass
            return False
        for input in psbt.inputs:
            for public_key, derivation_path_obj in input.bip32_derivations.items():
                if check_fingerprint_match(public_key, derivation_path_obj, is_taproot=False):
                    return True
            for public_key, (leaf_hashes, derivation_path_obj) in input.taproot_bip32_derivations.items():
                if check_fingerprint_match(public_key, derivation_path_obj, is_taproot=True):
                    return True
        return False

    @staticmethod
    def seed_owns_pubkey(root, claimed_derivation_path, public_key, child_key_derivation_cache, is_taproot=False, root_path=None):
        """
        Returns True if the signing seed (root) really does derive public_key at
        claimed_derivation_path.

        This is the canonical ownership check. The fingerprint a psbt or a descriptor
        carries alongside a key is metadata that whoever wrote the file chose, so it can
        say anything. Ownership is established here and only here, by deriving the key
        again from the seed and comparing the actual key material.

        claimed_derivation_path is always the psbt's full path, measured from the master
        key. `root` need not be the master key: a smartcard exports an account-level xpub
        and nothing below it, so root_path names where that xpub sits and the leading
        levels are dropped before deriving. See PSBTParser.root_path.
        """
        if root_path:
            if list(claimed_derivation_path[:len(root_path)]) != list(root_path):
                return False
            claimed_derivation_path = claimed_derivation_path[len(root_path):]
        derived_public_key = PSBTParser._derive_with_cache_via_indices(root, claimed_derivation_path, child_key_derivation_cache).get_public_key()
        if is_taproot:
            return derived_public_key.xonly() == public_key.xonly()
        return derived_public_key == public_key

    @staticmethod
    def _get_seed_derivation_paths(scope, root, child_key_derivation_cache, seed_fingerprint, root_path=None):
        """
        Scans the derivation path(s) in the provided input or output scope to determine
        which, if any, are provably derived from the signing seed (for multisig a path is
        provided per key; if the seed is part of the multisig, one of the n paths will
        match). Returns every verified DerivationPath entry, in the order the psbt lists
        them. An input or output that does not claim any of our keys yields an empty list.

        Every key in the scope that claims this seed's fingerprint is re-derived and
        checked. A claim that does not hold up raises InvalidPSBTError with
        RejectCode.FORGED_[OUTPUT|INPUT]_OWNERSHIP. This includes fingerprint collisions
        (two different keys with the same 4-byte fingerprint):
        * On the output side, a collision is considered an attack.
        * On the input side it is merely disallowed because it is unsignable by embit.

        seed_fingerprint is passed in rather than read off `root`, because `root` is not
        always the master key: with a smartcard it is an account-level xpub whose own
        fingerprint is not the one the psbt names. See PSBTParser.master_fingerprint.

        One edge case: A scope may carry more than one entry that verifies against this
        seed.
          * Foolish as it may be, a multisig could honestly use this seed in two cosigner
            slots, each at its own derivation path.
          * More importantly: a malicious psbt could list a second claim of ours as a
            decoy, at a path our seed really does derive but whose key the committed
            script has no use for.

        This function only checks and returns the DerivationPath entry for each key that
        derives from our seed. What those entries mean for the psbt is determined
        elsewhere.

        The path itself is still whatever the psbt supplied: it can be any length or
        shape, since any path that derives from the seed will pass. Whether the path is
        one the user's wallet would ever look at is a separate question.
        """
        verified_derivation_paths = []

        def _check_claim(public_key, derivation_path_obj, is_taproot):
            if derivation_path_obj.fingerprint != seed_fingerprint:
                return
            if not PSBTParser.seed_owns_pubkey(root, derivation_path_obj.derivation, public_key, child_key_derivation_cache, is_taproot=is_taproot, root_path=root_path):
                code = RejectCode.FORGED_INPUT_OWNERSHIP if isinstance(scope, _dependency('embit.psbt', 'InputScope')) else RejectCode.FORGED_OUTPUT_OWNERSHIP
                raise InvalidPSBTError("Key at {0} claims this seed's fingerprint but does not derive from it".format(_dependency('embit', 'bip32').path_to_str(derivation_path_obj.derivation)), code=code)
            verified_derivation_paths.append(derivation_path_obj)
        for public_key, derivation_path_obj in scope.bip32_derivations.items():
            _check_claim(public_key, derivation_path_obj, is_taproot=False)
        for public_key, (leaf_hashes, derivation_path_obj) in scope.taproot_bip32_derivations.items():
            _check_claim(public_key, derivation_path_obj, is_taproot=True)
        return verified_derivation_paths

    def _verify_claimed_derivation_paths(self, child_key_derivation_cache):
        """
        Verifies every derivation path entry that claims this seed's fingerprint. The
        result, stored in verified_[input|output]_derivation_paths, is the list of
        verified DerivationPath entries for each input/output scope (empty where no entry
        claimed this seed).

        The coordinator-supplied fingerprints cannot be trusted as-is. We must derive and
        verify the ownership of each one that claims to belong to this seed.

        Outputs are verified before inputs; a false claim on an output (e.g. fake-change
        forgery) is likely an attack whereas a false claim on an input is merely
        unsignable.

        Raises InvalidPSBTError with RejectCode.FORGED_[OUTPUT|INPUT]_OWNERSHIP on the
        first false claim detected.

        Does nothing when there is no BIP32 tree to derive against -- WIF / BIP38
        signing, or a seedless multisig pre-parse. Both lists stay empty, which
        _reject_if_seed_cannot_sign reads as "no evidence expected" rather than as
        "no ownership found".
        """
        if not self.can_verify_derivations:
            return
        seed_fingerprint = self.master_fingerprint or self.root.my_fingerprint
        self.verified_output_derivation_paths = [PSBTParser._get_seed_derivation_paths(out, self.root, child_key_derivation_cache, seed_fingerprint, self.root_path) for out in self.psbt.outputs]
        self.verified_input_derivation_paths = [PSBTParser._get_seed_derivation_paths(inp, self.root, child_key_derivation_cache, seed_fingerprint, self.root_path) for inp in self.psbt.inputs]

    def _reject_if_seed_cannot_sign(self):
        """
        Rejects the psbt when none of its inputs rely on a key derived by this seed.

        We detect it here, early, so the psbt can be rejected without sending the user
        through the full verification flow only for signing to fail at the end anyway.

        (embit's sign_with is marginally more permissive: it also signs an input whose
        script names the master key directly, with no derivation. That runs against how HD
        wallets are built. The master key is a derivation root, not a spending key, so no
        standard wallet produces such a psbt. We deliberately ignore this case.

        Similarly, it's not worth the effort to verify that each key is included in its
        input's script. A psbt that excludes a key in that way would be nonsensical but
        harmless: the excluded key cannot spend the input, so nothing of this seed's is
        at risk.)

        Skipped when there is no BIP32 tree to derive against, because then nothing was
        verified and an empty result is not evidence of absence. WIF / BIP38 signing
        matches its key against the input script in _parse_inputs instead.
        """
        if not self.can_verify_derivations:
            return
        for verified_derivation_paths in self.verified_input_derivation_paths:
            if len(verified_derivation_paths) > 0:
                return
        raise InvalidPSBTError('None of the inputs in this transaction are controlled by this seed.', code=RejectCode.SEED_CANNOT_SIGN)

    @staticmethod
    def is_change_branch(derivation_path):
        """
        Returns True if the next-to-last element of the derivation path is the change
        branch (1).
        """
        return len(derivation_path) >= 2 and derivation_path[-2] == 1

    def _seed_claims(self, scope):
        """
        The (ecdsa, taproot) claims in a scope that name this seed's fingerprint.
        Taproot entries are (pubkey, leaf_hashes).
        """
        seed_fingerprint = self.master_fingerprint or self.root.my_fingerprint
        ecdsa = [pub for pub, d in scope.bip32_derivations.items() if d.fingerprint == seed_fingerprint]
        taproot = [(pub, leaf_hashes) for pub, (leaf_hashes, d) in scope.taproot_bip32_derivations.items() if d.fingerprint == seed_fingerprint]
        return (ecdsa, taproot)

    def _verify_claim_shapes(self):
        """
        Refuses claims that are each individually true but could not all be true
        of one honest wallet's scope.

        Runs after _verify_claimed_derivation_paths, so every claim here already
        re-derives from the seed; a claim that does not is reported as forged
        rather than as mis-shaped.

        * MIXED_DERIVATION_MAPS: a scope naming this seed in both the ecdsa and
          the taproot derivation maps. A script is one or the other.
        * SURPLUS_DERIVATIONS: a single-key output naming this seed more than
          once. Only one of those keys can be the one the script pays, so the
          rest are decoys for a checker that reads only the first entry.
        """
        if not self.can_verify_derivations:
            return
        vout = self.psbt.tx.vout
        scopes = [(out, vout[i].script_pubkey) for i, out in enumerate(self.psbt.outputs)]
        scopes += [(inp, None) for inp in self.psbt.inputs]
        for scope, script_pubkey in scopes:
            ecdsa, taproot = self._seed_claims(scope)
            if ecdsa and taproot:
                raise InvalidPSBTError('A transaction entry names this seed as both an ecdsa and a taproot key.', code=RejectCode.MIXED_DERIVATION_MAPS)
            if script_pubkey is None:
                continue
            script_type = script_pubkey.script_type()
            is_single_key = script_type in ('p2pkh', 'p2wpkh') or (script_type == 'p2sh' and scope.redeem_script is not None and (scope.redeem_script.script_type() == 'p2wpkh'))
            key_path_claims = [pub for pub, leaf_hashes in taproot if not leaf_hashes]
            if is_single_key and len(ecdsa) > 1 or (script_type == 'p2tr' and len(key_path_claims) > 1):
                raise InvalidPSBTError("A single-key output names more than one of this seed's keys.", code=RejectCode.SURPLUS_DERIVATIONS)

    @staticmethod
    def _output_commits_to_key(out, script_pubkey, public_key):
        """
        Whether an output's scriptPubKey is locked to `public_key`. None when the
        psbt does not carry enough to tell (a script-hash output with no script
        supplied), which is left to the rest of the parse to judge.

        The output-side counterpart of _input_commits_to_key.
        """
        sec = public_key.sec()
        script_type = script_pubkey.script_type()
        if script_type == 'p2wpkh':
            return _dependency('embit', 'script').p2wpkh(public_key).data == script_pubkey.data
        if script_type == 'p2pkh':
            return _dependency('embit', 'script').p2pkh(public_key).data == script_pubkey.data
        if script_type == 'p2wsh':
            if out.witness_script is None:
                return None
            return _dependency('embit', 'script').p2wsh(out.witness_script).data == script_pubkey.data and sec in out.witness_script.data
        if script_type == 'p2sh':
            if _dependency('embit', 'script').p2sh(_dependency('embit', 'script').p2wpkh(public_key)).data == script_pubkey.data:
                return True
            redeem = out.redeem_script
            if redeem is None:
                return None
            if _dependency('embit', 'script').p2sh(redeem).data != script_pubkey.data:
                return False
            if redeem.script_type() == 'p2wsh':
                witness = out.witness_script
                return witness is not None and _dependency('embit', 'script').p2wsh(witness).data == redeem.data and (sec in witness.data)
            if redeem.script_type() == 'p2wpkh':
                return False
            return sec in redeem.data
        return None

    def _verify_output_claims_match_scripts(self):
        """
        Refuses an output whose derivation names one of this seed's keys when the
        output's script is not locked to that key.

        _verify_claimed_derivation_paths proves the key is ours. That is only half
        of an ownership claim: a psbt can annotate a stranger's output with a
        genuine key and path of ours, and the key check alone passes it. Such an
        output is not labelled change (the script comparison in _parse_outputs
        fails), so it would be shown as an ordinary payment with no hint that the
        psbt tried to pass it off as ours.

        Taproot claims are not checked here. A key-path claim can still sit under
        a script tree this parser does not reconstruct, so a mismatch is not proof
        of a lie; such outputs are simply never labelled change.
        """
        if not self.can_verify_derivations:
            return
        vout = self.psbt.tx.vout
        for i, out in enumerate(self.psbt.outputs):
            ecdsa, _taproot = self._seed_claims(out)
            for public_key in ecdsa:
                if PSBTParser._output_commits_to_key(out, vout[i].script_pubkey, public_key) is False:
                    raise InvalidPSBTError("Output {0} is annotated with one of this seed's keys, but its script pays a different key.".format(i), code=RejectCode.FORGED_OUTPUT_OWNERSHIP)

    def _reject_mislabeled_outputs(self, child_key_derivation_cache):
        """
        Refuses an output whose derivation names a foreign fingerprint on a key this
        seed actually derives at that path.

        The mirror image of FORGED_OUTPUT_OWNERSHIP: there the psbt claims a key of
        someone else's is ours; here it claims a key of ours is someone else's. The
        second costs nothing directly, but it is still the psbt misdescribing who owns
        its outputs, and ownership is decided by re-derivation in both directions.

        All-zero fingerprints were already filled in by _fill_missing_fingerprints, so
        an xpub imported without its fingerprint (issue #359) does not land here.
        """
        if not self.can_verify_derivations:
            return
        seed_fingerprint = self.master_fingerprint or self.root.my_fingerprint
        for i, out in enumerate(self.psbt.outputs):
            claims = [(pub, d, False) for pub, d in out.bip32_derivations.items()]
            claims += [(pub, d, True) for pub, (_, d) in out.taproot_bip32_derivations.items()]
            for public_key, derivation_path_obj, is_taproot in claims:
                if derivation_path_obj.fingerprint == seed_fingerprint:
                    continue
                try:
                    ours = PSBTParser.seed_owns_pubkey(self.root, derivation_path_obj.derivation, public_key, child_key_derivation_cache, is_taproot=is_taproot, root_path=self.root_path)
                except FeatureUnavailable:
                    raise
                except Exception as e:
                    pass
                    ours = False
                if ours:
                    raise InvalidPSBTError("Output {0} pays this seed but is labelled as another wallet's.".format(i), code=RejectCode.MISLABELED_OUTPUT_OWNERSHIP)

    def _reject_inconsistent_fingerprints(self, child_key_derivation_cache):
        """
        Refuses a psbt where a key's derivation entry and the global xpub that derives
        that key name different master fingerprints.

        Keys are matched to xpubs by derivation, not by fingerprint, so a mislabel
        changes nothing downstream -- but it is a self-contradictory psbt, which is
        refused like the others. All-zero fingerprints are skipped on either side:
        coordinators write 00000000 for a fingerprint they do not know.
        """
        zero = bytes(4)
        for scope in list(self.psbt.inputs) + list(self.psbt.outputs):
            for public_key, derivation_path_obj in scope.bip32_derivations.items():
                if derivation_path_obj.fingerprint == zero:
                    continue
                path = derivation_path_obj.derivation
                for xpub, origin in self.psbt.xpubs.items():
                    if origin.fingerprint == zero or origin.fingerprint == derivation_path_obj.fingerprint:
                        continue
                    if len(path) < 2 or list(origin.derivation) != list(path[:-2]):
                        continue
                    try:
                        derived = PSBTParser._derive_with_cache_via_indices(xpub, path[-2:], child_key_derivation_cache)
                    except FeatureUnavailable:
                        raise
                    except Exception:
                        continue
                    if derived.key == public_key:
                        raise InvalidPSBTError("A key's fingerprint disagrees with the xpub that derives it.", code=RejectCode.INCONSISTENT_FINGERPRINTS)

    def verify_multisig_output(self, descriptor, change_num):
        """
        Whether a change output really is the known-good descriptor's.

        embit's Descriptor.owns stops at the first derivation that names one of the
        descriptor's keys. A psbt listing a genuine entry first and a decoy after it
        therefore passes, while the same entries in the other order fail. Here
        every entry that names a descriptor key has to derive this output's script,
        and has to be one of the keys that script actually contains.
        """
        return self._descriptor_owns_output(descriptor, self.get_change_data(change_num)['output_index'])

    def _descriptor_owns_output(self, descriptor, i):
        """See verify_multisig_output; takes an output index rather than a change number."""
        output = self.psbt.outputs[i]
        script_pubkey = self.psbt.tx.vout[i].script_pubkey
        if not output.bip32_derivations:
            return descriptor.owns(output)
        if script_pubkey.script_type() != descriptor.scriptpubkey_type():
            return False
        matched = False
        for public_key, derivation_path_obj in output.bip32_derivations.items():
            res = descriptor.check_derivation(derivation_path_obj)
            if res is None:
                continue
            idx, branch_idx = res
            derived = descriptor.derive(idx, branch_index=branch_idx)
            if derived.script_pubkey().data != script_pubkey.data:
                return False
            committed = derived.witness_script() or derived.redeem_script()
            if committed is not None:
                if committed.script_type() == 'p2wpkh':
                    if _dependency('embit', 'script').p2wpkh(public_key).data != committed.data:
                        return False
                elif public_key.sec() not in committed.data:
                    return False
            matched = True
        return matched

    def _fill_missing_fingerprints(self, child_key_derivation_cache):
        """
        Fix for when fingerprint is missing (defaults to all zeros). Happens when the user
        creates a new wallet in an external coordinator but only provides the xpub
        (fingerprint and derivation path are omitted).

        Filling the missing fingerprints allows SeedSigner to correctly identify inputs /
        outputs that belong to the signing seed.

        see: https://github.com/SeedSigner/seedsigner/issues/359
        """
        if not self.root:
            return 0
        if not isinstance(self.root, _dependency('embit', 'bip32').HDKey):
            return 0

        def _fill_scope(scope):
            """Helper function to fill missing fingerprints in a scope (input/output)"""

            def _get_updated_fingerprint(public_key, derivation_path_obj, is_taproot):
                if derivation_path_obj.fingerprint != b'\x00\x00\x00\x00':
                    return None
                if PSBTParser.seed_owns_pubkey(self.root, derivation_path_obj.derivation, public_key, child_key_derivation_cache, is_taproot=is_taproot, root_path=self.root_path):
                    return _dependency('embit.psbt', 'DerivationPath')(self.master_fingerprint or self.root.my_fingerprint, derivation_path_obj.derivation)
                return None
            for public_key, derivation_path_obj in list(scope.bip32_derivations.items()):
                new_derivation = _get_updated_fingerprint(public_key, derivation_path_obj, is_taproot=False)
                if new_derivation:
                    scope.bip32_derivations[public_key] = new_derivation
                    pass
            for public_key, (leaf_hashes, derivation_path_obj) in list(scope.taproot_bip32_derivations.items()):
                new_derivation = _get_updated_fingerprint(public_key, derivation_path_obj, is_taproot=True)
                if new_derivation:
                    scope.taproot_bip32_derivations[public_key] = (leaf_hashes, new_derivation)
                    pass
        for inp in self.psbt.inputs:
            _fill_scope(inp)
        for out in self.psbt.outputs:
            _fill_scope(out)

    def get_total_output_value(self, include_change=False):
        """
            Returns the sum of all outputs (fee not included).

            `change_data` holds every output that comes back to this seed, which is two
            different things: change, and self-transfers to one of our own receive
            addresses. With `include_change=False` only the change is subtracted;
            self-transfers stay in the total, since the user chose to send funds there
            just as they did for any external recipient. The two are told apart the way
            the views do it, by `is_change_branch` on the derivation path the parse
            proved this seed owns.

            Used to decide whether the fee is high relative to what is actually being
            sent, and whether to warn.
        """
        total = sum((out.value for out in self.psbt.tx.vout))
        if include_change:
            return total
        true_change = sum((entry['amount'] for entry in self.change_data if PSBTParser.is_change_branch(entry['verified_derivation_path'])))
        return total - true_change

    def has_high_fee(self):
        """
            Returns True if the fee is high.
            i.e. fee amount > <HIGH_FEES_WARNING_THRESHOLD>% of total outputs excluding change
        """
        total_output_value_excluding_change = self.get_total_output_value()
        if total_output_value_excluding_change <= 0:
            return False
        else:
            return self.fee_amount > self.HIGH_FEES_WARNING_THRESHOLD / 100 * total_output_value_excluding_change
