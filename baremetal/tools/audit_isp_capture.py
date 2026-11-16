# SPDX-License-Identifier: MIT
"""Validate bounded ISP feedback evidence; visual comparison remains external."""

import argparse
import json
from pathlib import Path
import re


def audit(text):
    if '@@FAIL' in text:
        raise ValueError('Firmware failure marker')
    ae = [
        tuple(map(int, row))
        for row in re.findall(
            r'@@ISP_3A_AE frame=(\d+) mean_q8=(\d+) proposed_lines=(\d+) proposed_gain=(\d+)', text
        )
    ]
    awb = [
        (int(frame), tuple(map(float, gains.split(', '))))
        for frame, gains in re.findall(
            r'@@ISP_3A_AWB frame=(\d+) complete=(?:true|false) gain=\[([^]]+)\]', text
        )
    ]
    if [r[0] for r in ae] != list(range(32)) or [r[0] for r in awb] != list(range(32)):
        raise ValueError('Missing/repeated/out-of-order algorithm frames')
    updates = [
        tuple(map(int, row))
        for row in re.findall(
            r'@@ISP_FEEDBACK_FRAME frame=(\d+) measured_parameters=(\d+) boundary_updates=(\d+)',
            text,
        )
    ]
    if updates != [(i, i - 1, i) for i in range(1, 32)]:
        raise ValueError('Frame/configuration/IRQ update association')
    gains = re.findall(r'@@ISP_GAIN_READBACK matched=(\d+) checked=6 unresolved_gain2=2', text)
    if gains != ['6'] * 31:
        raise ValueError('Missing/mismatching gain readbacks')
    masks = [int(m, 16) for m in re.findall(r'@@ISP_STATS mask=(0x[0-9a-f]+)', text)]
    if len(masks) != 32 or any(m & 0x1120 != 0x1120 for m in masks):
        raise ValueError('Incomplete primary AE/histogram/AWB measurements')
    if len({r[2:] for r in ae[-12:]}) != 1 or len({r[1] for r in awb[-12:]}) != 1:
        raise ValueError('Final12 control decisions have not settled')
    if not all(v > 0 for v in awb[-1][1]):
        raise ValueError('Invalid final AWB gains')
    final = ae[-1][2:]
    ae_settle = next(
        i
        for i in range(32)
        if all(
            abs(r[2] - final[0]) <= final[0] * 0.05 and abs(r[3] - final[1]) <= final[1] * 0.05
            for r in ae[i:]
        )
    )
    wb_final = awb[-1][1]
    wb_settle = next(
        i
        for i in range(32)
        if all(all(abs(v - f) <= f * 0.02 for v, f in zip(r[1], wb_final)) for r in awb[i:])
    )
    if '@@ISP_3A_FEEDBACK_DIAGNOSTIC 32-frames; normal-timeshare; not-full-gate' not in text:
        raise ValueError('Missing bounded completion marker')
    return {
        'frames': 32,
        'irqAppliedUpdates': 31,
        'matchingGainReadbacks': 186,
        'finalExposureLines': final[0],
        'finalGainCode': final[1],
        'finalWhiteBalance': wb_final,
        'exposureWithin5PercentFromFrame': ae_settle,
        'whiteBalanceWithin2PercentFromFrame': wb_settle,
        'exactStableTailFrames': 12,
        'visualReviewRequired': True,
        'limits': [
            'Bounded linear profile; no long-run allocation qualification.',
            'Two gain2 readbacks remain unresolved; six other gain words checked each update.',
            'Statistics association uses controlled triggers and sensor settling, not external electrical timing measurement.',
        ],
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('serial', type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(args.serial.read_text(errors='replace')), indent=2))
