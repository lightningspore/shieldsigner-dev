# SPDX-License-Identifier: MIT
"""Extract observed ISP writes up to its first RAW read trigger; diagnostic only.

Not a complete bus trace or a portable driver. DMA addresses become explicit
placeholders resolved by the DUT driver, never Linux physical addresses.
"""
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'logs/phase-8/isp-events.txt'

def extract(source, count, expected):
    data = source.read_text().splitlines()
    if data[0] != f'# applied=0 count={count} dropped=0 errors=0; kind0=pre-store-MMIO kind1=successful-regmap kind2=successful-sensor':
        raise ValueError('Review capture provenance/count/errors before regeneration')
    rows = []
    for line in data[1:]:
        seq, timestamp, kind, site, address, value, width = line.split()
        address, value = int(address, 16), int(value, 16)
        if not 0xffa00000 <= address < 0xffa07f00:
            continue
        if kind != '0' or width != '4' or address & 3:
            raise ValueError('Unexpected ISP transaction')
        offset = address - 0xffa00000
        # Explicit buffer roles, not a heuristic treating every large value as DMA.
        role = {0x1408: 1, 0x141c: 2, 0x1890: 3, 0x197c: 4}.get(offset, 0)
        rows.append((offset, 0 if role else value, role))
        if offset == 0x1c00 and value == 0x20820401:
            break
    if len(rows) != expected or rows[-1][:2] != (0x1c00, 0x20820401):
        raise ValueError('Expected first trigger missing')
    return rows

def generate():
    output = ['// SPDX-License-Identifier: MIT',
        '// Observed register facts, partial ISP write profile; diagnostic only.',
        '// Roles: 0 literal, 1 Y output, 2 UV output, 3 RAW input, 4 statistics.']
    for name, source, count, expected in [
        ('WRITES', SOURCE, 1365, 1103),
        ('MEASUREMENT_WRITES', ROOT/'logs/phase-8/isp-auto-events.txt', 16374, 1483),
    ]:
        rows = extract(source, count, expected)
        output += ['// Source SHA256: ' + hashlib.sha256(source.read_bytes()).hexdigest(),
                   '#[allow(dead_code)]', f'pub const {name}: &[(usize, u32, u8)] = &[']
        output += [f'    (0x{offset:04x}, 0x{value:08x}, {role}),' for offset, value, role in rows]
        output += ['];', '']
    (ROOT / 'src/isp_replay_data.rs').write_text('\n'.join(output))
    print('Generated fixed1103/measurement1483 observed ISP writes; first-trigger diagnostics only')

if __name__ == '__main__':
    generate()
