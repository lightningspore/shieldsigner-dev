# Native scan preview and progress

The app scanner now composites camera pixels with the original native LVGL
instruction text, fragment progress bar and added/repeated/missed frame indicator.
It uses the original source scan loop and decoder progress calculation.

`ui.scan_begin`, `scan_frame`, `scan_status`, `scan_state` and `scan_end` own one
scan surface. Each NV12 frame is synchronously center-cropped and converted using
the existing BT.601 RGB565 converter into a separate 115200-byte native heap
buffer. No camera/DMA pointer is retained. LVGL composes this image with the
original camera overlay widgets and flushes through the existing LCD/shadow path.
The buffer is wiped on release; this is not a whole-memory erasure guarantee.

Screen replacement, scan completion, cancellation and exceptions release the
surface. Original animation/widget handles and image cache entries are removed
before freeing the backing storage. `ui.blank()` also replaces the active LVGL
root and updates the framebuffer shadow; the Python renderer uses it during
private-screen cleanup. The raw diagnostic `display.blit_nv12` API remains separate.
A camera stop failure retains its active ownership flag for a later retry.

The public multipart fixture exposed three MicroPython port issues: native
binascii needs an ASCII buffer rather than a string; the source transformer must
preserve local variables that shadow imports; and the original Base43 decoder
needs `reversed(v)` and a list reverse buffer instead of a stepped bytes slice and
bytearray.reverse. The source algorithm and its leading-zero behavior remain
unchanged, checked against the original CPython implementation.

Reproduce host checks with `mise run baremetal:check`, prepare independent pixels
with `mise run baremetal:app:scan:overlay:prepare`, and run the selected DUT1 RAM
image with `mise run baremetal:app:scan:overlay:dut1:gate`. The gate checks RGB
vectors, borrowed-input mutation, original widget states, repeated teardown and
native heap stability. Actual ZXing/original decoder tests cover repeated,
missing and out-of-order fragments, full PSBT byte retrieval and error/interrupt
cleanup. Fixtures are public; they do not qualify optical focus, camera scanning
reliability, wallet signing or hardware security. See the evidence receipt for
individual results. The earlier unexplained reset remains open.
