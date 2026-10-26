# Recovered camera-service lifecycle

`engine::Engine` reconstructs the successful per-camera controller in the pinned `rkaiq_3A_server` binary. **It still requires a native processing backend**, and is not an installed or working daemon replacement. It contains no dynamic link to RKAIQ.

The daemon's `engine_thread` entry is ELF `0x111a0`; `wait_stream_event` is `0x11148`. Unlike the shared library, these server ELF addresses already include its executable image base. The emulator applies its own additional load offset when executing them.

The native media-discovery routine looks up these entity names:

| Record offset | Entity | Role |
| --- | --- | --- |
| 0x00 | `rkisp-isp-subdev` | ISP subdevice |
| 0x40 | `rkisp-input-params` | Parameter queue and stream-event file descriptor |
| 0x80 | `rkisp-statistics` | ISP statistics queue |
| 0xc0 | `rkisp_mainpath` | Main image stream; passed to the library's sensor-binding lookup |
| 0x100 | Bound sensor entity name | Input to processing-context initialization |

The original controller opens the parameter node read/write, initializes a context using the bound sensor name and its compiled IQ directory, disables the library's own stream-status listener, optionally enables multi-camera concurrency, and prepares **linear mode** with the configured width and height. Its compiled defaults are 2688×1520, not a requirement that every test use that size. Rust receives these settings explicitly.

It subscribes to `0x08000001` (stream start), then `0x08000002` (stream stop), with zero id/flags/reserved fields. It waits for start, calls processing start, waits for stop, calls processing stop with its boolean argument false, and repeats. Unexpected event types are consumed and ignored, including duplicate start while waiting for stop. The native wait routine retries unsuccessful dequeues indefinitely; its ioctl wrapper specifically retries EINTR. The monitor instead has an explicit deadline and reports other errors.

The new Rust core expresses processing operations through `Backend`; a real native implementation must supply initialization, preparation, start/stop and event subscriptions. The error API intentionally differs from the binary: backend errors are returned, failed start/stop leaves the current state unchanged, and preparation failures do not exit the process. The original ignores several return codes and has fatal exits. There is no claimed match for those error paths or for a shutdown path absent from its infinite loop.

## Evidence and reproduction

`mise run camera:rust:lifecycle` executes actual original ARM `engine_thread` instructions under Unicorn. Imported OS/library calls are controlled stubs. The test compares normalized call names and arguments with the compiled Rust controller across 100 deterministic event sequences, both concurrency-flag states and several resolutions. It checks full consumption of supplied events and stops the original at its next dequeue. [Report](lifecycle-equivalence.json).

This proves the tested orchestration and event filtering, **not** the library behavior behind the stubbed calls. The original `__ctype_b` copied external symbol is zero-initialized because this path does not perform character classification; unexpected imported processing calls fail the test. Printed log calls are discarded. No hardware interaction is simulated as proof of real operation.

`camera:rust:layout` cross-compiles pinned kernel UAPI assertions for the 32-byte subscription, legacy ARM32 128-byte event, sequence offset 76, and the original ioctl request numbers. It explicitly models the old-time structure used by this daemon rather than musl's current time64 structure. Kernel-only compiler includes and `__user` annotations are removed from a build copy as during userspace header installation; pinned original downloads remain unchanged.

`camera-probe events` is a bounded real-device observer for those two events on the parameter node. See [HARDWARE-TEST.md](HARDWARE-TEST.md). Independent sensor binding, media graph setup, synchronized queue ownership, complete IQ initialization and the actual processing backend remain implementation/integration work. The separate recovered metadata queue and bounded submission diagnostic are described in [PARAMETERS.md](PARAMETERS.md); they are not wired into this service controller yet.
