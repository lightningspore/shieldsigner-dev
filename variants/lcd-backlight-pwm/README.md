# Dedicated LCD backlight PWM · 0.0.8-dev candidate

Open [the KiCad project](kicad/SeedSigner-Plus-smartcard-pico.kicad_pro). This is the checked **next-revision candidate**, based on the released 0.0.7 pill. The current released Gerbers, BOM/CPL, website model, fit kit and JLC cart still describe 0.0.7. No cart was changed. Promote and regenerate matching manufacturing/review assets before ordering this revision.

## Always-on remains the default

| Mode | JP201 | JP202 | Power-up behavior |
| --- | --- | --- | --- |
| **Always on — factory default** | Closed | Open | BL_E held high from host 3.3 V; works without PWM software |
| Optional brightness control | Open | Closed | R703 holds the PWM/control signal low (backlight off) until the GPIO drives it |

Keep **JP203 and JP205 closed; JP204 and JP206 open** in both modes. Change solder straps with power disconnected. Never close JP201 and JP202 together: that would tie the GPIO to 3.3 V. JP204's former CS-to-backlight branch is now disconnected and marked no-connect in the schematic; leave that legacy spare jumper open.

The module defines **BL_E low = off, high = on**. Under PWM, 0% high duty is off, 100% is full-on, and intermediate duty cycles are the brightness-control path to qualify on the actual screen. This is a logic-enable connection; the GPIO does not supply the roughly 120 mA backlight load. LCD power stays on the existing dedicated LCD_3V3 regulator.

## Hardware change

- U202 **physical header pin 14**, **GPIO1_D2**, is reassigned from unused I2C3 SDA to the dedicated **LCD_PWM** net. The RV1103 pin mux supports **PWM0_M1** on this pad. This is GPIO bank 1, line 26; it is not Linux PWM channel 14.
- LCD_PWM routes to **JP202 pin 1**. JP202 pin 2 stays on **RPI_BACKLIGHT**, reaching **J701 carrier pin 1 / HOTHMI vendor pin 8 BL_E**.
- **R703 = 5.1 kΩ, 0805**, pulls LCD_PWM to GND. It uses the same **0805W8F5101T5E / LCSC C27834** identity already used by R301/R302. The 3.3 V high-state resistor current is approximately **0.647 mA**. This adds **one fitted resistor, no additional catalog SKU**: the candidate has 36 SMT components; the released 35-component BOM is not its purchase file.
- The old JP202-to-JP204 copper branch is removed. SPI CS stays on U202 pin 6 and its original default path. UART, buttons, LCD data/reset, power rails, module headers, supports and case interfaces retain their existing mappings and positions.
- R703 is on the front at (150, 107) mm, under the supported display. Its existing 0805 model is shared with the released project; no case or header-height change is introduced.

The candidate reuses the released project-local STEP models via explicit relative paths into `../lcd-module-2.8/kicad/3dmodels`; keep both variant directories when opening this project. Footprint/symbol libraries are included locally.

## Validation

Run `mise run variant:lcd:pwm` at repository root. The baseline SHA guard rejects replay against a different released PCB. The task creates the candidate, fills planes with pinned native KiCad, then runs ERC plus DRC with schematic parity and no exclusions. Any finding, incomplete connection or parity issue fails the task.

An independent topology audit verifies both jumper modes, the separate CS path, resistor nets, all existing component poses and pad nets, and every retained original track/via's geometry and net assignment. Only the nine obsolete backlight-branch track segments are removed. This catches unintended net reassignment while routing/filling, rather than relying only on a clean DRC report.

[check-results.json](check-results.json) records the candidate and baseline board hashes, checks and intended population. Full native reports and front/back review SVGs are under `dist/backlight-pwm/`. The released project is checksum-checked after the build to ensure it was not edited.

## Firmware and first-article qualification

Always-on mode needs no brightness firmware change. For optional PWM, disable **I2C3** on GPIO1_D2 and enable **pwm0m1** in the final device tree, following the [official Luckfox PWM documentation](https://wiki.luckfox.com/Luckfox-Pico-Plus-Mini/PWM/). Confirm the final running image actually muxes **PWM0_M1**, not the Mini's unrelated default PWM10/11 outputs used by buttons. Identify the PWM controller from the live device tree; do not assume the sysfs pwmchip number.

The retained [HOTHMI module drawing/datasheet](../../reference/pdfs/HOTHMI-HTM-TFT028A16-SPI.pdf), page 6, specifies BL_E high/on and low/off. It does **not** give a qualified PWM frequency or duty-cycle/brightness curve. The hardware exposes the appropriate 3.3 V enable path; smooth dimming remains a module/firmware bench check.

On one powered first article, first verify static low/off and high/on at BL_E. Then scope PWM at the actual LCD header and check multiple duty cycles and frequencies, including low brightness, camera interaction/flicker, current and boot/shutdown behavior. Establish a stable frequency range on the purchased module revision before declaring the brightness feature qualified. If the module does not respond properly to BL_E PWM, keep the always-on strap setting; changing the regulator voltage is not a supported brightness method.
