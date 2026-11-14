# Remaining project milestones

User expanded the scope after Phase9's first hardware script passed. Preserve
these requirements through future checkpoints; the project is not over at the
interpreter prompt.

1. **Standalone microSD boot.** Package the unchanged DDR initialization and our
   runtime for the actual RV1103 ROM boot path, verify a bootable card image,
   then obtain the user's authorization and physical fresh-card action before
   any persistent write. Never overwrite REF's existing Linux reference card.
   Measure reset→REPL and reset→first usable frame. This retains Phase10's fast
   boot objective; current RAM-load tests do not establish standalone boot.
2. **USB debugging without UART wires.** Investigate the RV1103 USB device
   controller/PHY and provide ADB or a comparably convenient USB console/REPL.
   USB device support is now explicitly in scope. A USB CDC REPL may be the
   smallest useful path; do not promise ADB's Linux shell/filesystem semantics
   on a bare-metal runtime. Prove recovery, reconnect and script transfer before
   removing the REF UART bridge.
3. **SeedSigner app on MicroPython and the PCB.** Inventory the actual app/source
   on REF and preserve its license and behavior. Map CPython/OS/Pillow/threading
   dependencies to viable MicroPython/Rust modules. Reuse proven Rust camera/3A,
   add the PCB's real LCD and button drivers, then have the user reconnect the
   board after pin/power/test-jumper checks. Verify navigation, display, camera
   acquisition and the app's QR/signing workflows on the assembled hardware.
   A screen demo or import test alone does not qualify the app port.

Keep REF's working Linux installation as the comparison/recovery reference until
its replacement is verified. No camera holding is needed for current checks;
comparison images were already saved. Request physical actions only when the
next concrete hardware step needs them. Commit after completed stage gates and
keep NOTES/HISTORY/evidence current. Full logs/private images remain local.
