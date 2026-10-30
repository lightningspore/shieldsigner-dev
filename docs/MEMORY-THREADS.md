# Memory and threads on the Luckfox Mini

ShieldSigner runs on a single-core Luckfox Pico Mini with 64 MiB of physical RAM. The app, camera buffers and image processing compete for that small budget. The current development image uses deferred imports, bounded frame queues and compressed RAM swap to keep camera scanning responsive.

Measurements below were taken on 29 October 2026 with the 0.0.39-dev image and a 240×240 ST7789 display. They describe this configuration, not every Luckfox model or future release.

## Where the physical RAM goes

Linux reports about 45 MiB in `MemTotal`. Another 12 MiB is reserved for camera DMA; roughly 7 MiB is in other kernel/platform reservations that have not been fully attributed. With the app and camera stopped, an earlier measurement found about 32 MiB available.

`MemAvailable` includes memory Linux expects it can reclaim, such as file cache. It is more useful than `MemFree` for estimating headroom. Resident PSS attributes physical pages to processes while apportioning shared pages; RSS counts shared pages in each process. Virtual address space is not physical RAM consumption.

## Python memory during Scan

A snapshot of the normal app after boot, menu navigation and entering Scan measured:

| Process | Threads | Resident PSS | Logical swapped pages |
|---|---:|---:|---:|
| Python app | 7 | 13.7 MiB | 13.8 MiB |
| Rust camera | 5 | 8.9 MiB | 0.08 MiB |
| ZXing QR worker | 1 | 0.67 MiB | 0 |

These sequential reads fluctuate. The numbers are a snapshot, not allocation limits or simultaneous high-water marks. Before Scan, Python had four threads and about 17.5 MiB resident PSS, with 10.9 MiB logically swapped. Resident memory can fall when Scan opens because Linux compresses less-used app pages to make room for the camera.

Python's process includes:

- The interpreter, imported module dictionaries, functions, classes and constants.
- App objects, screen state and Python-managed data.
- Pillow images, drawing canvases, fonts and caches.
- Received frame data and temporary image conversions.
- Thread stacks, allocator overhead and native libraries loaded into Python, including the Rust LCD extension.

The separate Rust camera and ZXing processes are outside Python's PSS. All seven Python threads share the same modules and heap; the app is not copied seven times. Python allocators may retain freed space for reuse, so releasing an object need not immediately reduce RSS. Object-by-object and module-by-module attribution is future profiling work; no percentages are assigned to these categories.

## Imports and startup peaks

An import executes a module's top-level code, creates objects and recursively imports dependencies. Modules generally remain cached for the process lifetime. Optional background preloading now stays disabled in the small-RAM profile: screens load when needed, while required seed and encrypted-QR storage initialization still runs.

Scan also previously imported two SLIP39 destination screens from `seed_views`, pulling in a larger dependency graph immediately. Those original classes now resolve only when their SLIP39 branch is used. Features remain available; first entry can take longer, and imported modules are not automatically unloaded afterward. A separate test with wallet, smartcard and settings modules preloaded also passed, so successful scanning is not limited to an empty optional import graph. The memory saving attributable to imports alone has not been isolated.

One measured startup fix is independent of imports: verifying the roughly 8 MiB QR executable used to read the entire file into a temporary Python buffer. SHA-256 now streams 64 KiB chunks. On-board isolated peak RSS fell from 18,088 KiB to 10,076 KiB with the identical hash result, a 7.82 MiB transient saving. This verifies the expected executable; it is not memory required for decoding a QR and is not a steady-state saving.

## Threads and how they cooperate

During the measured Scan there were 13 application threads across three processes. Other OS services and kernel threads are not included.

| Python thread | Work |
|---|---|
| Main app | Navigation, QR requests and decoded-result handling |
| MicroSD monitor | Waits for insert/remove notifications |
| Wipe timer | Checks the configured inactivity wipe policy |
| RNG monitor | Periodically samples the system RNG |
| Camera reader | Receives frames from the Rust camera process |
| Camera log drainer | Drains the child process pipe so logging cannot block capture |
| Live preview | Prepares images and calls the LCD driver |

The camera process has five threads for control/AE/AWB/ISP parameters, image capture, ISP statistics, raw-buffer bridging and frame transport. ZXing has one worker thread. Loading screens and notifications may temporarily change counts. These roles come from the implementation; Linux's thread names do not individually identify every Python class.

```text
Camera hardware and ISP
        |
Rust camera process (5 threads)
        | local socket
Python app (7 threads during Scan)
        |-- main Scan loop --> ZXing process (1 thread) --> decoded result
        |-- live preview --> Rust LCD extension --> SPI --> display
```

The board exposes one CPU core. Threads let waiting operations overlap: while SPI, camera input or a socket is waiting, another runnable thread can execute. They do not create 13-way CPU execution. Camera/ISP hardware can operate independently of CPU scheduling.

Python's GIL generally permits one thread to execute Python code at a time. The Rust LCD extension releases it during conversion and SPI waits. The camera and ZXing run in separate processes outside Python's GIL, while still sharing the same single CPU. Each thread needs its own stack and kernel bookkeeping, but stack address-space reservations are not necessarily fully resident.

## LCD pixel buffers

The Rust LCD extension runs inside Python and creates no dedicated process or thread. For the current 240×240 profile:

| Allocation | Pixel bytes | Lifetime |
|---|---:|---|
| Rust RGB565 output buffer | 115,200 bytes / 112.5 KiB | Reused for successive frames |
| Packed Python RGB input | 172,800 bytes / 168.75 KiB | Temporary for each display update |

The shim calls `image.convert('RGB').tobytes()` and Rust converts those bytes into its reusable output buffer. Pillow canvases, converted image storage, fonts, object overhead, mapped extension code and kernel SPI buffers add to those figures. Pillow's internal RGB storage can exceed the three-byte-per-pixel packed payload. The table is an exact pixel-buffer calculation, not a measurement of the LCD's complete memory cost. The display controller's own screen memory is separate from Luckfox RAM.

A 640×480 camera frame is about 450 KiB in NV12 or 900 KiB as packed RGB. QR decoding uses the full-resolution grayscale plane while only the preview is reduced for display. Bounded queues and latest-frame delivery prevent a slow preview or decoder from accumulating an unbounded history of frames.

## Compressed RAM swap

Zram compresses less-used pages in RAM; it does not write swap to the microSD. This profile provides a 16 MiB logical swap device with an 8 MiB compressed-allocation limit and LZO compression. Logical swapped bytes must not be added to physical RAM consumption at their uncompressed size.

In the normal Scan snapshot, zram's allocator occupied about 7.1 MiB of actual RAM and the logical swap device was nearly full. Available RAM was about 8.2 MiB. The same snapshot showed 10.6 MiB camera DMA, 4.4 MiB unreclaimable kernel slab, 0.49 MiB system-wide kernel stacks and 0.38 MiB system-wide page tables. These are different accounting views, not a disjoint pie chart to sum with process PSS and available cache.

## Measured continuous operation

![Available RAM, process memory and camera DMA through a 20-minute hardware soak](../reverse-engineering/rkaiq/memory/memory-packed-image-1200.png)

The exact packaged app/camera/QR/LCD files passed a 20-minute physical-board run from a read-only compressed-rootfs mount: 17,811 frames, 5,929 renders, 7,042 QR calls, zero errors/reconnects, exit status 0 and clean owner/DMA teardown. Across 871 steady camera-phase samples, available RAM was 7.79–11.70 MiB, median 10.36 MiB. Median PSS was 14.73 MiB app, 5.69 MiB camera and 0.52 MiB QR worker; compressed-swap allocation was 6.73–6.93 MiB.

The soak retained the existing kernel/Python/zram setup. The later normal-app snapshot above is from the newly booted image and a different menu/import history, so its memory numbers differ. A completed soak does not establish optical QR success, physical Back navigation or every boot scenario.

[Download the soak result](../reverse-engineering/rkaiq/memory/gui-packed-image-1200-result.json). The detailed diagnostic chronology and reproduction commands are in [the repository memory report](https://github.com/lightningspore/shieldsigner-dev/blob/main/docs/CAMERA-MEMORY.md).
