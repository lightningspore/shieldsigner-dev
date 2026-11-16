# SPDX-License-Identifier: MIT
"""Normalize observed register facts for original bare-metal replay development."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def parse_trace(path):
    text = path.read_text()
    header = text.splitlines()[0]
    fields = dict(re.findall(r'(applied|count|dropped|errors)=(\d+)', header))
    if fields.get('applied') != '0' or fields.get('dropped') != '0' or fields.get('errors') != '0':
        raise ValueError('Trace must be restored, complete and error-free')
    events = []
    for line in text.splitlines()[1:]:
        index, ns, kind, site, address, value, width = map(lambda s: int(s, 0), line.split())
        if index != len(events):
            raise ValueError('Noncontiguous event sequence')
        if events and ns < events[-1]['ns']:
            raise ValueError('Nonmonotonic timestamp')
        events.append(
            dict(
                index=index, ns=ns, kind=kind, site=site, address=address, value=value, width=width
            )
        )
    if len(events) != int(fields['count']):
        raise ValueError('Truncated trace')
    return events


def clock_spec(kernel):
    """Clock selectors/gates actually named by pinned clock driver, plus camera resets."""
    source = (kernel / 'drivers/clk/rockchip/clk-rv1106.c').read_text()
    header = (kernel / 'drivers/clk/rockchip/clk.h').read_text()
    bases = {
        name: int(value, 16)
        for name, value in re.findall(r'#define\s+(RV1106_\w+CRU_BASE)\s+(0x[0-9A-Fa-f]+)', header)
    }
    formulas = {}
    for name, constant, base in re.findall(
        r'#define\s+(RV1106_\w*CLK(?:SEL|GATE)_CON)\(x\)\s+\(\(x\) \* 0x4 \+ (0x[0-9a-f]+)(?: \+ (RV1106_\w+CRU_BASE))?\)',
        header,
    ):
        formulas[name] = int(constant, 16) + bases.get(base, 0)
    registers = {}
    for name, index in re.findall(r'(RV1106_\w*CLK(?:SEL|GATE)_CON)\((\d+)\)', source):
        if name not in formulas:
            raise ValueError('Unknown clock formula ' + name)
        address = 0xFF3A0000 + formulas[name] + int(index) * 4
        registers[address] = f'{name}({index})'
    for pll in [0, 8, 16, 24]:
        for index in range(pll, pll + 4):
            registers[0xFF3B0000 + index * 4] = f'PLL_CON({index})'
    registers[0xFF3B0280] = 'MODE_CON'
    for address, name in [
        (0xFF3B4A00, 'VI_SOFTRST0'),
        (0xFF3B4A04, 'VI_SOFTRST1'),
        (0xFF050014, 'VI_GRF_CSIPHY_CON5'),
    ]:
        registers[address] = name
    return {
        'scope': 'partial: source-named CRU clock selectors/gates, PLLs, VI resets and D-PHY GRF; no reserved-register scan',
        'registers': [
            {'address': f'0x{address:08x}', 'name': name}
            for address, name in sorted(registers.items())
        ],
    }


def generate(trace):
    events = parse_trace(trace)
    start = next(
        i
        for i, e in enumerate(events)
        if e['kind'] == 2 and e['address'] == 0x100 and e['value'] == 1
    )
    setup = events[: start + 1]
    # Replay configuration only. Never import REF DMA addresses as DUT addresses.
    result = []
    for event in setup:
        e = dict(event)
        if e['kind'] == 0 and (
            e['width'] != 4
            or not any(
                low <= e['address'] < high
                for low, high in [
                    (0xFFA10000, 0xFFA20000),
                    (0xFFA20000, 0xFFA30000),
                    (0xFF3E8000, 0xFF3F0000),
                ]
            )
        ):
            raise ValueError('Unreviewed MMIO write')
        if e['kind'] == 2 and (
            e['width'] != 1 or not 0 <= e['address'] <= 65535 or not 0 <= e['value'] <= 255
        ):
            raise ValueError('Unreviewed sensor write')
        if e['kind'] == 1:
            if e['site'] != 16 or e['address'] != 0x50014 or e['width'] != 4:
                raise ValueError('Unreviewed regmap site')
            e['address'] += 0xFF000000
        if e['kind'] not in [0, 1, 2]:
            raise ValueError('Unknown event kind')
        if e['address'] in [0xFFA10124, 0xFFA10128]:
            e['value'] = 0x03000000 if e['address'] == 0xFFA10124 else 0x03400000
        result.append(e)
    return {
        'scope': 'development replay facts; not a validated driver or complete clock/power setup',
        'traceSha256': hashlib.sha256(trace.read_bytes()).hexdigest(),
        'observations': len(events),
        'setupObservations': len(result),
        'kindCounts': dict(Counter(e['kind'] for e in events)),
        'frame': {
            'width': 2304,
            'height': 1296,
            'stride': 3072,
            'bytes': 3981312,
            'fourcc': 'BG10',
        },
        'dmaBuffers': [0x03000000, 0x03400000],
        'setup': result,
    }


def rust_setup(facts):
    lines = [
        '// SPDX-License-Identifier: MIT',
        '// Register facts observed on REF; original replay representation.',
        '// Trace SHA256: ' + facts['traceSha256'],
        '#[cfg(feature = "camera-replay")]',
        'pub const SETUP: &[(u8, usize, u32, u32)] = &[',
    ]
    previous = facts['setup'][0]['ns']
    for event in facts['setup']:
        delay = (event['ns'] - previous + 999) // 1000
        previous = event['ns']
        if event['width'] not in [1, 4]:
            raise ValueError('Unreviewed replay width')
        lines.append(
            '    (%d, 0x%08x, 0x%08x, %d),'
            % (event['kind'], event['address'], event['value'], delay)
        )
    addresses = {e['address'] for e in facts['setup'] if e['kind'] != 2}
    addresses.update(
        [
            0xFF3B036C,
            0xFF3B4300,
            0xFF3B4800,
            0xFF3B4804,
            0xFF3B4A00,
            0xFF3B4A04,
            0xFF558054,
            0xFF558058,
        ]
    )
    lines.extend(["];", 'pub const READBACK: &[usize] = &['])
    lines.extend('    0x%08x,' % address for address in sorted(addresses))
    return '\n'.join(lines + ["];", ''])


def rust_sensor_mode(facts):
    sensor = [e for e in facts['setup'] if e['kind'] == 2]
    end = next(i for i, e in enumerate(sensor) if e['address'] == 0x37F9 and e['value'] == 0x47)
    preset = [e for e in sensor[: end + 1] if e['address'] != 0x103]
    lines = [
        '// SPDX-License-Identifier: MIT',
        '// SC3336 2304x1296 RAW10 analog/timing preset observed on REF.',
        '// Register facts only; original driver logic is in sc3336.rs.',
        '// Trace SHA256: ' + facts['traceSha256'],
        'pub const MODE_PRESET: &[(u16,u8)] = &[',
    ]
    lines.extend('    (0x%04x,0x%02x),' % (e['address'], e['value']) for e in preset)
    return '\n'.join(lines + ["];", ''])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('trace', type=Path)
    parser.add_argument(
        '--kernel', type=Path, default=ROOT / '.tools/kernel-reference/sysdrv/source/kernel'
    )
    args = parser.parse_args()
    output = ROOT / 'logs/phase-7'
    facts = generate(args.trace)
    (output / 'camera-replay-facts.json').write_text(json.dumps(facts, indent=2) + '\n')
    (ROOT / 'src/camera_replay_data.rs').write_text(rust_setup(facts))
    folder = ROOT / 'src/camera'
    folder.mkdir(exist_ok=True)
    (folder / 'sensor_mode.rs').write_text(rust_sensor_mode(facts))
    spec = clock_spec(args.kernel)
    (output / 'clock-snapshot-spec.json').write_text(json.dumps(spec, indent=2) + '\n')
    print(
        'Generated replay facts and',
        len(spec['registers']),
        'reviewable clock/config reads; no hardware writes.',
    )
