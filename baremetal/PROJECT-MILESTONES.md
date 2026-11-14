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

Primary user-visible performance metric: power-on to a usable SeedSigner main
screen with working input, plus camera readiness through the app. The user
reports the current boot/app path takes at least about30s. This is a reported
baseline, not our measured value. Internal13.1ms payload-to-interpreter timing
excludes ROM/DDR/loading and does not include SeedSigner or demonstrate an
end-to-end speedup. Preserve the original standalone power-to-REPL gate too.

Update: standalone runtime SD boot and full API/camera tests now pass on the
authorized spare4GB card, with a5Hz LED heartbeat. The ROM loads unchanged DDR
and our runtime directly. Cold power-edge/first-frame timing and app/assets
storage remain unfinished; no usable SeedSigner app boot result exists yet.

Current user priority: port SeedSigner buttons, LCD and camera on the existing Linux-tested board (240x240 bench profile). Smartcard software is excluded. Exact cold-power benchmarking is deferred by user instruction and must not delay app work. UART2 overlaps bench buttons; provide another debug transport before reconnecting. Existing SPI loopback must be removed before LCD output.

User confirmed third device: Luckfox Pico Mini A, RV1103, no onboard flash; use microSD boot. Preserve existing wired REF/DUT fixture. USB debugging remains an explicit priority, including REPL/script transfer and reconnect/recovery tests, alongside the actual app port.

USB update: RAM CDC/script transfer, large output, Ctrl-C, reopening and USB warm
reset now pass. DUT1 has a USB-only console and proven UART-pad release. User
added DUT1 with the bench LCD/buttons; DUT0 camera observes its screen. Continue
app work with this setup while the user is away. Standalone USB SD boot remains
open; no need to reconnect or rewire the existing fixture.
