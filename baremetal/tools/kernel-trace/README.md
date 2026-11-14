# Temporary REF camera write tracing

**Do not run the recorded unload sequence.** It crashed the stock CIF async-notifier teardown before any modified camera module loaded. `failed-unload-sequence.sh.txt` is retained as diagnostic evidence, not an executable deployment path. REF was recovered by warm reset; a corrected teardown or a different tracing strategy must be established before another attempt.

This GPL-2.0-only runtime module is separate from the original MIT bare-metal implementation. It records vendor driver register writes for observation; it does not replace any REF boot image or persistent module file.

`instrument_reference.py` patches only the ignored checkout of SDK commit `0b5c1f30ca6333b7ec5af70d26511da9ef8d39af`. Instrumented MMIO writes go through a bounded, IRQ-safe recorder that performs the write and records its order/timestamp under one lock. Sensor I²C writes are recorded after successful completion; GRF values are recorded after the original regmap call. Inter-block nanosecond timestamps are observations, not a guarantee of all hardware settling times.

Block IDs:1=CIF,2=CSI D-PHY,3=CSI host,5=SC3336 register writes,6=PHY GRF,7=system GRF. No ISP write instrumentation yet. Capture requires a stopped trace with `dropped=0` before interpreting the event list as complete. Capacity32,768 events (~768KB RAM).

The replacement-module deployment approach is abandoned after two stock graph teardown failures. Do not unload camera modules or use the failed detach helper. The recorder and source patches remain diagnostic/development artifacts. Current work follows `LIVE-TRACE-DESIGN.md`, with original modules and their device graph kept intact. No live call redirection has been applied. Keep original `/oem/usr/ko` files unchanged. Kernel preparation currently requires the vendor ARM GCC8.3 toolchain and the Python3 `python` alias in the container.

Enable/clear: write1 to `/sys/kernel/debug/baremetal_camera_trace/control`. Stop: write0. Read `events` only after stopping. All raw logs and image files remain under ignored `baremetal/logs/phase-7/`.
