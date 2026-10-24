#!/usr/bin/env python3
"""Illustrate LDO heat sensitivity; no software-only thermal qualification."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--vin', type=float, default=5.25,
                    help='Planning input voltage, not a measured or guaranteed bound')
parser.add_argument('--vout', type=float, default=3.1,
                    help='Planning low output voltage for dissipation sensitivity')
parser.add_argument('--ambient-c', type=float, default=40,
                    help='Planning local ambient, including enclosure heating')
args = parser.parse_args()
assert 0 < args.vout < args.vin and -40 <= args.ambient_c <= 85
rows = []
for current in [.12, .15, .2, .3, .6]:
    power = (args.vin - args.vout) * current
    rows.append({'lcdCurrentMa': current * 1000, 'ldoDissipationW': round(power, 4),
                 'illustrativeRiseC': round(power * 184, 2),
                 'illustrativeJunctionC': round(args.ambient_c + power * 184, 2)})
pcb = ROOT / 'variants/lcd-module-2.8/kicad/SeedSigner-Plus-smartcard-pico.kicad_pcb'
report = {
    'boardSha256': hashlib.sha256(pcb.read_bytes()).hexdigest(),
    'qualification': 'Planning sensitivity calculation only; actual thermal resistance, load and temperature are unmeasured.',
    'inputs': {'vinV': args.vin, 'voutV': args.vout, 'localAmbientC': args.ambient_c,
               'datasheetSot25ThetaJaCPerW': 184},
    'formulas': ['P = (Vin - Vout) * Ilcd', 'illustrative Tj = local ambient + P * thetaJA'],
    'cases': rows,
    'sources': {
        'ldo': {'path': 'reference/pdfs/Diodes-AP2112.pdf',
                'facts': 'Page 3: SOT25 thetaJA 184 C/W; absolute max junction 150 C. Page 8: 3.3V variant electrical characteristics. The 600mA rating is not a usable thermal budget at arbitrary dropout.'},
        'lcd': {'path': 'reference/pdfs/HOTHMI-HTM-TFT028A16-SPI.pdf',
                'facts': 'Page 8: VCC/IOVCC 3.1-3.6V, 3.3V nominal; backlight current 120mA typical; total operation current not specified.'}
    },
    'limitations': [
        'The 5.25V input, 3.1V output and 40C ambient are selected planning assumptions, not measured operating conditions or component guarantees.',
        '184 C/W comes from datasheet conditions and is not a measured bound for this copper, airflow or enclosure.',
        'Calculation omits regulator ground current and temperature-dependent behavior; it cannot certify junction temperature.',
        'Large calculated temperatures are extrapolations; regulation and thermal shutdown invalidate that steady operating assumption.',
        'The LCD 120mA backlight figure is not total module current. Obtain total current on the actual module.'
    ],
    'firstArticleMeasurements': [
        'Measure whole LCD module current; do not derive it solely from the backlight typical figure.',
        'Capture LCD_3V3 startup minimum/maximum and display/camera/card combined-load transients; check against 3.1-3.6V LCD operating range.',
        'Record U701 case temperature, local ambient, enclosure state, input voltage, load pattern and run duration until temperature stabilizes.',
        'Check repeated cold and warm starts, regulator cycling, display faults and rail droop. Stop on unexpected current or temperature.',
        'Choose intended maximum ambient and establish a justified thermal margin before approving repeats; case temperature alone is not junction temperature.'
    ],
    'decision': 'Do not justify the present LCD supply using the 600mA headline rating. Measure actual load and thermal behavior before repeat builds; consider a revised supply if margin is inadequate.'
}
out = ROOT / 'variants/lcd-module-2.8/manufacturing/lcd-power-budget.json'
out.write_text(json.dumps(report, indent=2) + '\n')
for row in rows:
    print(f"{row['lcdCurrentMa']:.0f}mA: {row['ldoDissipationW']:.3f}W, illustrative Tj {row['illustrativeJunctionC']:.1f}C (not qualification)")
