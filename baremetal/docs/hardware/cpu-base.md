# Phase 3: CPU base (MMU, caches, timer, interrupts)

Phase 2 baseline: `build/phase-2-baseline/` (local ignored artifacts); ten hardware runs proved code entry at DDR address 0 and stack top 0x00400000. UART2 is already configured by the unchanged DDR blob at 115,200 baud. UART R warm reset is the routine recovery path; preserve it during CPU changes.

Register facts from the official local Luckfox SDK (read as reference; implementation remains original):

| Block | Address / interrupt | Reference |
|---|---|---|
| UART2 | 0xff4c0000, 32-bit accesses with 4-byte register spacing; GIC SPI 27 = INTID 59 | `sysdrv/source/kernel/arch/arm/boot/dts/rv1106.dtsi`, uart2 node |
| GIC distributor | 0xff1f1000 | `sysdrv/source/uboot/u-boot/include/configs/rv1106_common.h` |
| GIC CPU interface | 0xff1f2000 | same header |
| CRU first global reset | 0xff3b0c08, key 0xfdb9 | kernel `drivers/clk/rockchip/clk.h` plus U-Boot reset driver; hardware UART reset proven |
| DDR | 0x00000000–0x03ffffff, 64 MB | captured DDR banner |

Next implementation sequence, keeping each change independently recoverable:

1. Read and log CPSR, SCTLR, CNTFRQ and counter progress before assuming loader CPU state.
2. Reserve an aligned 16 KB first-level translation table, separate SVC/IRQ stacks, a small heap and a provisional camera reservation in DDR. Identity-map DDR as normal cacheable memory and peripheral space as device memory.
3. Implement cache maintenance and compare the same bounded memory/loop workload with caches off/on using the architectural counter. Hardware gate requires at least 10x, not compilation.
4. Install exception vectors and GICv2 handling; enable a periodic generic timer interrupt and measure counts over the counter interval (within 1%).
5. Enable UART2 RX interrupt (INTID 59), echo test bytes through REF and retain the R reset command.

Do not begin Phase 4 until the Phase 3 hardware evidence covers benchmark, timer and UART IRQ echo. The completed Phase 3 gate is recorded in `evidence/phase-3.json`.

## Hardware results during implementation

- Initial SCTLR `0x00c52878`: M/C/I off; ACTLR `0x00006000`: SMP clear. Architectural counter reports 24 MHz and advances on DUT.
- Initial cache run improved only ~2.1x. Setting ACTLR.SMP before maintenance/MMU/cache enable produced ~93–96x on the unchanged 262,144-load workload with equal checksums. [Arm Cortex-A7 TRM, ACTLR](https://documentation-service.arm.com/static/602cf701083323480d479d18) requires SMP before caches/MMU/maintenance; cacheable loads are otherwise not cached.
- Timer path uses CNTP and accepts secure/nonsecure physical timer INTIDs 29/30. One-second hardware run counted 999 IRQs against 24,000,004 counter ticks (target 1,000 Hz).
- UART2 INTID 59 echoes RX bytes solely in the handler; polling RX is compiled out of the cpu-base main loop. A 47-byte host/REF/DUT echo test matched exactly.
- Heap: monotonic 4 MB region `[0x00400000,0x00800000)`, aligned atomic bump allocation, no reclaim yet. Hardware check allocates and verifies distinct 4 KB/8 KB patterns and rejects an oversized request. IRQ handlers do not allocate.
- SVC stack top 0x00400000; IRQ stack top 0x00200000. The unmapped 2–3MiB section separates the stacks. Phase 8 exposed corruption with the former64KiB spacing; calibrated3A uses larger temporary records. Image, translation table and BSS constrained below 1 MB by the linker. Provisional camera reservation `[0x03000000,0x04000000)` is 16 MB; actual camera DMA mapping/coherency is Phase 7 work.

Build this feature with `uv run --python 3.13 python baremetal/tools/build_hello.py --features cpu-base` (or the mise CPU build task). Default build remains minimal hello. Final combined hardware gate evidence is recorded in NOTES/HISTORY; compilation is not a gate.
