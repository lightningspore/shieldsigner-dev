# SPDX-License-Identifier: MIT
"""Add narrowly selected original ISP store sites to the proven camera observer.

This covers generic writes, cache flush and RAW-input addresses/triggers. Direct
reset/interrupt/other legacy-version stores are NOT covered; no complete ISP
bus-trace claim is made. It does not patch or access either board.
"""

import json
from live_trace_sites import ROOT, MODULES, read_module, generate_header

ISP_SHA256 = 'e74ecc37c0db9c05b0a37f2eb03adeb7ab479a4e863f23ee7ce6d1961fad4f2c'
SITES = {
    0x836A: 'rkisp_write',
    0x8416: 'rkisp_idx_write',
    0x86A6: 'rkisp_update_regs',
    0x86DC: 'rkisp_update_regs',
    0xC29A: 'update_rawrd',
    0xC5DC: 'update_dmarx',
    0xC5FC: 'update_dmarx',
    0xC61C: 'update_dmarx',
    0xC636: 'update_dmarx',
}


def read_isp():
    module, text = read_module('video_rkisp', SITES, max_ops=8)
    if module['sha256'] != ISP_SHA256:
        raise ValueError('ISP module fingerprint changed; review new ELF first')
    if {site['offset'] for site in module['sites']} != set(SITES):
        raise ValueError('Selected ISP relocations missing')
    for site in module['sites']:
        if site['kind'] != 'mmio' or not site['link']:
            raise ValueError('Unexpected ISP call kind')
        site['function'] = SITES[site['offset']]
    return module, text


def generate():
    modules = [read_module(name)[0] for name in MODULES] + [read_isp()[0]]
    count = sum(len(module['sites']) for module in modules)
    if count != 27:
        raise ValueError('Unexpected combined whitelist count')
    output = ROOT / 'logs/phase-8'
    output.mkdir(parents=True, exist_ok=True)
    (output / 'isp-write-sites.json').write_text(
        json.dumps(
            {
                'modules': modules,
                'sites': count,
                'coverage': 'camera18 plus ISP9 generic/flush/RAW-input sites; partial ISP observation',
                'appliedToHardware': False,
            },
            indent=2,
        )
        + '\n'
    )
    generate_header(modules, ROOT / 'build/isp-trace/live_sites.h', max_ops=8)
    print('Generated27 sites;9 ISP sites; no device access; coverage is partial')


if __name__ == '__main__':
    generate()
