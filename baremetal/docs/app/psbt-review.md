# PSBT review policy

The generated `seedsigner_port.psbt_parser` retains the complete pinned original
PSBTParser policy and all methods. It shares the existing original error-leaf
classes with the strict raw loader, preserving exception identity. Type/import/
formatting boundaries use the common source port; logger calls are omitted.
`app/psbt-review-provenance.json` pins original/output hashes and changes.

The actual pinned embit0.8.0 finalizer is supplied as `embit/finalizer.py`, unchanged
apart from attribution. It is a dependency of the original approval/signing View;
no replacement transaction policy or cryptographic implementation is introduced.

Host preparation:

```sh
uv run --python 3.13 python baremetal/tools/prepare_psbt_review.py
uv run --python 3.13 --with embit==0.8.0 python baremetal/tools/prepare_psbt_review_gate.py
mise run baremetal:check
```

The independent host pass compares the port against unmodified original policy
bodies on all 116 original public corpus transactions:45 accepted and 71 refused.
It also checks original target refusal codes, accounting and required advisories.
A raw framing refusal can precede the table's embit-refusal bucket; both original
and port pipelines reject identically. Eight normal v0/v2 fixtures sign all their
inputs using real embit crypto, verify each signature, finalize the full PSBT and
check exact original trimmed PSBT output. These are public all-zero BIP39 fixtures,
not private wallet data. A fixed public clock makes host locktime checks stable.

The generated `micropython/psbt_review_gate.py` prepares all 116 native corpus cases
plus those8 signing cases. It has NOT been run on hardware in this checkpoint.
Two timestamp-locktime cases explicitly assert FeatureUnavailable for the missing
actual Unix clock provider. `psbt_clock` delegates only actual standard time/date
functions; boot uptime is never presented as Unix time.

Integration notes:

- Freeze `seedsigner_port/psbt_parser.py`, `seedsigner_port/psbt_clock.py` and
  `embit/finalizer.py`.
- Map `seedsigner.models.psbt_parser` to `seedsigner_port.psbt_parser` instead of
  the error-only leaf. The full module imports/re-exports the same leaf errors,
  so existing strict framing and callers retain their identities.
- Enable real `MICROPY_PY_BUILTINS_FROZENSET (1)` for native UI builds. The original
  `RiskWarning.INFORMATIONAL` requires it; CORE_FEATURES currently disables it.
- Resolve the original PSBT View/screen and animated signed-QR dependencies
  separately. No placeholder review or automatic approval is supplied here.

Descriptor-specific provider methods, WIF-specific workflows, timestamp clock
integration, native model/signature gates, the actual approval/cancel UI and QR
export remain separate qualification work. No board, USB, SD, REF or DUT0 access
was performed; no claim of production signing/entropy/security qualification.

The new `prepare_psbt_views.py` retains all 23 original PSBT View classes and
methods, including refusal routes, warnings and explicit transaction approval.
The original refusal presentation dataclass has an explicit field constructor;
lazy factories replace unavailable subclass introspection with the exact pinned
source subclass list. The source clock boundary remains explicit.

Six PSBT screen facades reuse the existing native Linux contracts and exact
integer amount formatters, with original screen field defaults. Host tests compare
all six contracts, invalid UTF8/NUL OP_RETURN handling, maximum supply formatting,
and demonstrate that the original Back path exits before any signing provider.
These scripted host checks do not qualify native UI operation.

Views integration freezes `view_psbt`, `psbt_formatting`, `psbt_contracts`,
`psbt_screen_defaults`, and `psbt_screens`. Alias original PSBT views/screens to
these modules. The shared screen dispatcher must dispatch only PSBT names to
`psbt_screens.configuration`; that facade delegates base ButtonList fields back
to the common dispatcher before applying the original PSBT-specific contract.
The signed UR QR provider remains the original export dependency. Full native
review/approval/cancel/export qualification remains to be run by the parent.

`uv run --python 3.13 python baremetal/tools/prepare_psbt_flow_gate.py` prepares
`micropython/psbt_flow_gate.py` from the same public NORMAL-1 p2wpkh fixture and
trimmed-output hash used by the eight host signing cases. It has not been run.
It calls the actual original Destination/View chain and native renderer, injects
real `ui.key` navigation/select events, and does not replace screen return values.
Two complete review passes reach the approval screen: the first presses Back and
asserts original PSBT bytes/signature count are unchanged; the second approves,
verifies native change ownership, displays original UR export, and decodes the
actual LCD framebuffer QR frames into UR PSBT bytes. It verifies every exported
signature against the original input sighash and checks exact trimmed-output hash.

Required providers: actual Seed derivation/storage/wipe; original PSBT model and
View aliases; six native screen contracts; LoadingScreenThread; real embit signing,
DER verification and finalizer; UrPsbtQrEncoder; native QRDisplayScreen animation;
UR decoder/registry; native renderer/key/framebuffer and QR decoder. Missing or
unreviewed routes fail instead of substituting approvals or export encodings.
The gate uses only mainnet public all-zero BIP39 test material, no wall clock,
smartcard, camera or microSD writes. Running the gate requires root coordination
once a device test window is available. `mpy-cross` syntax compilation passed;
that does not establish native runtime success.
