# Linux ISP reference capture

This data was collected using PLAN's explicit exception for parallel reference capture while Phase 7 awaited a suitable scene. Phase 7 has since passed on the DUT; these reference captures remain inputs for Phase 8, not its qualification.

REF uses the installed project Rust camera-probe and factory SC3336 calibration. The runtime pipeline is raw TX `/dev/video0` → raw RX `/dev/video18` → ISP `/dev/v4l-subdev3`, parameters20, image 11, statistics19, SOF subdev0. Output was changed from native 2304×1296 to 640×480 NV12 so the bridge/image buffers fit12MiB CMA. Optional bay3d/ynr/cnr/sharp were disabled with `SHIELDSIGNER_IQ_MODULES=none`; this does not disable every ISP or controller module.

All scene data, binary snapshots and detailed logs below are ignored local artifacts under `logs/ref-isp/`.

| Capture | Evidence | What it proves |
| --- | --- | --- |
| Fixed startup | `bm-isp-fixed.nv12*`; command log in `logs/phase-7/ref-isp-fixed-capture.txt` |460800 byte NV12 frame,11145 byte Rust-generated parameters,3 raw completions, clean queue teardown |
| Rust AE/AWB | `auto-capture.txt`, `auto-summary.json`, `bm-isp-auto.nv12*` |33 raw completions, no dropped records,22 statistics records,21 parameter submissions; AE/AWB loops executed |
| Fixed streaming registers | `fixed-register-capture.txt`, `fixed-registers.jsonl`, `fixed-register-snapshot/` |32512 byte ISP resource snapshot while active,91 raw completions, no dropped records or cleanup errors |
| REF health afterward | `post-reference-raw-capture.txt`, `final-reference-state.txt` | Original3,981,312 byte raw capture still works; no temporary bm modules; historical taint4096 unchanged |

Fixed-startup luma mean was 1.7465/255; the automatic result rose to 31.2315/255 but remains mostly noise. Both previews were decoded with the existing Rust frame-preview and inspected. AE had 14 exact exposure lookups among22 statistics records and 19 control decisions. The final statistics record lacked an exact exposure match. The CLI explicitly leaves physical parameter application/frame timing and cold start unverified. These observations do not establish usable convergence, colour quality, or a DUT hardware gate.

The saved automatic statistics buffer is13040 bytes. Associated AWB SDK/configuration and translated records are preserved alongside it. Use the original source's frame/parameter association semantics when replaying these records; do not infer physical timing from an event named “finished.”

## Readback is not a write table

`audit_isp_awb_reference.py` compares selected fixed-reference AWB fields to the captured parameter buffer. Six channel pairs and the AWB enable state match after interpreting the read representation; two gain 2 pairs remain unresolved and are reported as such.

The pinned SDK's `isp_params_v32.c` writes AWB gain channels in16-bit halves. Its `hw.c` explicitly excludes AWB1 gain registers from ordinary readback restoration because read and write values differ. Captured offsets0x530/0x534 show12-bit spacing on read, including the non-unity red/blue pair. Copying their raw readback words into a write replay would therefore change the gains. Preserve the parameter representation and original register programming semantics for eventual DUT work. The register audit does not prove full-module/frame application.

REF is back at fixed sensor controls: VBLANK64, exposure 122, analogue gain 128, with VGA ISP output retained. These are runtime changes, not boot-storage modifications. No vendor rkaiq process was started; normal V4L2 queues and temporary public clock references were used.

The original dark reference previews do not establish visual quality or convergence. Phase 7 later passed with a repositioned target. Phase 8 must still demonstrate actual DUT ISP output/statistics/3A and obtain suitable side-by-side reference images; these older captures cannot substitute for that gate.
