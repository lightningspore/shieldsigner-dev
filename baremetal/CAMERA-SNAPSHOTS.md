# Reliable native camera snapshots

Use an explicit USB identity and an ignored local output path:

```sh
mise run baremetal:camera:snapshot -- --serial rv1103-dut1 \
  --output baremetal/logs/phase-12/inspection.png --ae-target 90
```

The wired observer is `rv1103-dev-001`. The tool starts a real native camera
preview, reads twelve frames by default, copies the final luma into one owned
307,200-byte snapshot and stops the camera. It restores the previous AE target
and exposure seed, and checks the stopped session and settings before export.
`--frames 1..32`, `--ae-target 0|8..200` and `--exposure-seed 1..1352` are optional.
Zero AE target means fixed-exposure mode. These controls do not provide autofocus.

Rows export in small console scripts (80 rows by default), each tagged with the
same SHA-256 identity. This also works on DUT0, whose UART mirroring limits output
speed and caused a single full-frame console dump to exceed its observation
window. No camera restart occurs between chunks. The native snapshot is a copy,
so later reuse of the borrowed ISP buffer cannot silently change it.

The host requires all 480 rows, rejects conflicting rows or snapshot identities,
checks the full reconstructed checksum and then writes the PNG. Cleanup uses the
existing best-effort native owned-buffer wipe and drops its reference. It does
not promise clearing all temporary serial/hex copies or hardware frame buffers.
Each run saves scripts, native console receipts and a final result under an
ignored `baremetal/logs/phase-12/capture-*` directory. Images and exports stay local;
unknown QR payloads are not printed or committed.

The decoder also accepts legacy unhashed exports for old evidence. It explicitly
labels these unverified, rejects mixing legacy and hashed chunks, and supports
`--require-digest` to demand the new format:

```sh
uv run --python 3.13 --with pillow==12.2.0 python \
  baremetal/tools/decode_camera_luma.py result.png chunk-*.txt --require-digest
```

Snapshot validation proves a coherent image transfer, not optical QR decoding or
camera image quality. The current printed-QR capture has its full outline in the
frame; native and desktop decoders still fail. A separate known public QR on the
LCD also fails in the observer setup, where the image is visibly badly out of
focus. No decoder algorithm or default camera settings were changed from those
results. Optical qualification remains open; further software application work
can proceed while the physical setup is unattended.
