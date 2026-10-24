#!/usr/bin/env python3
"""Set the reviewed HOTHMI clock in an app checkout or staged rootfs io_config.json."""
import argparse
import json
from pathlib import Path


def configure(path):
    data = json.loads(path.read_text())
    profiles = [p for p in data['models'] if p.get('shortname') == 'FOX_22']
    if len(profiles) != 1:
        raise ValueError('Expected exactly one FOX_22 profile')
    display = profiles[0]['display']
    expected = {'dc': ['/dev/gpiochip1', 20], 'rst': ['/dev/gpiochip1', 19],
                'bl': 'disabled', 'spi_bus': 0, 'spi_device': 0}
    if any(display.get(k) != v for k, v in expected.items()):
        raise ValueError('Display pin assignment differs from reviewed carrier')
    if display.get('cs') == 'disabled':
        raise ValueError('Carrier defaults require kernel-managed CS')
    if display.get('spi_hz', 40_000_000) not in (40_000_000, 10_000_000):
        raise ValueError('Unreviewed SPI speed; preserve and review existing settings')
    display['spi_hz'] = 10_000_000
    path.write_text(json.dumps(data, indent=2) + '\n')
    return data


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('io_config', type=Path)
    args = parser.parse_args()
    configure(args.io_config)
    print('FOX_22: HOTHMI SPI set to 10 MHz; other profiles unchanged')
