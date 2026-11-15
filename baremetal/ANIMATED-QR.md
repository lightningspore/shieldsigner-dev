# Original animated QR transport and UR sources

This is a source/host-tested integration candidate. Neither new native gate has
run on a board yet; the user's SD-booted DUT1 was left untouched.

`seedsigner_port.qr_display` now follows the existing native Linux adapter in
`firmware/lvgl-app/python/qr_output.py` and the original QRDisplayThread:

- Show the first original encoder part and advance animated parts every1/6second
  (rounded upward by1ms clock/input service resolution).
- Hold frames while the real native brightness tip is visible; restart the
  encoder when the tip closes, preserving the important first fountain parts.
- Keep original brightness steps and save brightness once on normal exit.
- Use original text/byte encoding modes, a two-module border and no new density
  control. The existing512-byte per-frame bound remains.
- Clear the owning native screen in finally on normal exit, errors and interrupts.

The actual native QR screen already supplies `qr_display_set_frame` and
`qr_display_is_tip_active`. Typed `ui.qr_frame(buffer)` and `ui.qr_tip_active()`
wrappers expose those functions without a subprocess or fake thread. Frame
encoding/copying is synchronous; C++ exceptions return through the existing error
boundary before MicroPython raises. The frame API requires an active QR screen
and1..512bytes.

`ui.qr_exit_key()` retains the real keypad key when the QR screen reports its
exit. This preserves existing event tuples and lets `cancel_on_back=True` return
Back only for actual LEFT, as the original app does. Root replacement/blank clears
that snapshot. Touch/programmatic exits have no assumed key identity.

Original UR2 files from the pinned app and the exact `urtypes` commit in its
requirements are copied without protocol changes. All31source/output hashes are
in `app/ur-provenance.json`; original notices and full licenses are retained in
`app/LICENSE.UR2` and `app/LICENSE.urtypes`. UR2's deterministic Xoshiro generator
is the original fountain-fragment mixer; it is not wallet entropy or a new RNG
feature. The original fountain constructor's minimum10-byte message constraint
is retained, including its existing assertion for shorter messages.

Regeneration:

```sh
uv run --python 3.13 --with 'urtypes @ https://github.com/selfcustody/urtypes/archive/7fb280eab3b3563dfc57d2733b0bf5cbc0a96a6a.zip' python baremetal/tools/prepare_ur.py
uv run --python 3.13 --with 'urtypes @ https://github.com/selfcustody/urtypes/archive/7fb280eab3b3563dfc57d2733b0bf5cbc0a96a6a.zip' python baremetal/tools/prepare_ur_gate.py
uv run --python 3.13 python baremetal/tools/prepare_animated_qr_gate.py
```

Shared integration still required: freeze every module key in the UR provenance
file and map `seedsigner.helpers.ur2[.*]` imports to `seedsigner_port.ur2[.*]`.
The actual `urtypes` module names remain unchanged. Rebuild the complete runtime
before running either native gate.

Host evidence: six QR cadence/lifecycle tests and three original-source/CBOR/
fountain tests pass. The pinned MicroPython compiler accepts all31UR modules,
the facade and gate scripts. The actual ARM native UI library rebuild succeeds.
A full host suite run passed126tests at this snapshot; other agents may add more.

Prepared, not hardware-run:

- `micropython/ur_core_gate.py`: nine public original CPython frame-oracle cases,
  mixed-only/out-of-order fountain recovery, exact CBOR and registry round trips.
- `micropython/animated_qr_gate.py`: actual original Specter fragments, real native
  framebuffer QR decode, brightness-tip hold/restart, actual left exit identity,
  borrowed-input mutation/length guards and20warm screen teardown cycles.

These gates use known public data. They do not qualify optical scanning, signing,
wallet entropy, production security or the complete app.
