# SPDX-License-Identifier: MIT
"""Prepare an experimental ROM SD image as regular files; never access devices.

Format facts: pinned Luckfox U-Boot tools/rkcommon.c header0_info_v2 and
scripts/spl.sh. Original validation/packaging code; vendor DDR stays unchanged.
"""
import argparse
import configparser
import hashlib
import json
from pathlib import Path
import struct
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SECTOR = 512
SD_OFFSET = 64 * SECTOR


def sha(data):
    return hashlib.sha256(data).hexdigest()


def inspect_idblock(data, expected):
    """Reject corrupt/truncated headers, DMA addresses and substituted stages."""
    if len(data) < 2048:
        raise ValueError('truncated ID block')
    magic, reserved, layout, flags = struct.unpack_from('<4I', data)
    if (magic, reserved, layout, flags) != (0x534e4b52, 0, (2 << 16) | 384, 1):
        raise ValueError('unsupported ROM header')
    if hashlib.sha256(data[:1536]).digest() != data[1536:1568]:
        raise ValueError('header SHA256 mismatch')
    end = 2048
    entries = []
    for index, stage in enumerate(expected):
        at = 120 + index * 88
        size_offset, address, flag, counter = struct.unpack_from('<4I', data, at)
        offset = (size_offset & 65535) * SECTOR
        size = (size_offset >> 16) * SECTOR
        if address != 0xffffffff or flag != 0 or counter != index + 1:
            raise ValueError('unexpected stage metadata')
        if offset != end or size < len(stage) or size % 2048 or offset + size > len(data):
            raise ValueError('invalid stage extent')
        body = data[offset:offset + size]
        if hashlib.sha256(body).digest() != data[at + 24:at + 56]:
            raise ValueError('stage SHA256 mismatch')
        if body[:len(stage)] != stage or any(body[len(stage):]):
            raise ValueError('stage differs from pinned input or nonzero padding')
        entries.append({'offset': offset, 'paddedBytes': size,
                        'inputBytes': len(stage), 'inputSha256': sha(stage)})
        end = offset + size
    if len(expected) != 2 or end != len(data):
        raise ValueError('unexpected trailing data or stage count')
    return entries


def validate_payload(payload, manifest, profile):
    expected='app-autostart' if profile=='app' else 'fast-boot'
    if manifest['features']!=expected or manifest['files']['build/hello.bin']!=sha(payload):
        raise ValueError('Build matching '+expected+' payload first')
    if profile=='app' and manifest.get('usbSerial')!='rv1103-dut1':
        raise ValueError('App SD image requires the actual DUT1 LCD/button profile')


def compose_sd_image(idblock):
    # Preserve the historical2MiB minimum; native app includes frozen assets and
    # needs a larger regular-file image. No SDK partitions/U-Boot are appended.
    unit=1024*1024
    size=((max(2*unit,SD_OFFSET+len(idblock))+unit-1)//unit)*unit
    image=bytearray(size);image[SD_OFFSET:SD_OFFSET+len(idblock)]=idblock
    return image


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile',choices=('runtime','app'),default='runtime')
    args=parser.parse_args()
    prefix='app' if args.profile=='app' else 'runtime'
    build = ROOT / 'build'
    rkbin = ROOT / '.tools/rkbin'
    pins = json.loads((ROOT / 'stock-loader.json').read_text())
    for name in ['RKBOOT/RV1106MINIALL.ini', 'tools/boot_merger',
                 'bin/rv11/rv1106_ddr_924MHz_v1.16.bin']:
        if sha((rkbin / name).read_bytes()) != pins['files'][name]:
            raise SystemExit('Changed packaging input: ' + name)
    payload = (build / 'hello.bin').read_bytes()
    manifest = json.loads((build / 'hello-manifest.json').read_text())
    validate_payload(payload,manifest,args.profile)
    # NEWIDB uses the exact stage bytes, without the legacy four-byte magic.
    (rkbin / 'sd-runtime.bin').write_bytes(payload)
    ini = configparser.ConfigParser()
    ini.optionxform = str
    ini.read(rkbin / 'RKBOOT/RV1106MINIALL.ini')
    ini['LOADER_OPTION']['FlashBoot'] = 'sd-runtime.bin'
    ini['OUTPUT']['PATH'] = 'sd-download-unused.bin'
    ini['OUTPUT']['IDB_PATH'] = 'sd-idblock.img'
    ini['FLAG']['CREATE_IDB'] = 'true'
    with (rkbin / 'sd-runtime.ini').open('w') as stream:
        ini.write(stream, space_around_delimiters=False)
    subprocess.run(['docker', 'run', '--rm', '--platform', 'linux/amd64',
        '-v', str(rkbin) + ':/work', '-w', '/work',
        'alpine:3.21@sha256:bc21487101ae47172509130ee1092cc273a831968d64b617776d1f69c81e42ab',
        './tools/boot_merger', 'sd-runtime.ini'], check=True)
    data = (rkbin / 'sd-idblock.img').read_bytes()
    ddr = (rkbin / ini['LOADER_OPTION']['FlashData']).read_bytes()
    entries = inspect_idblock(data, [ddr, payload])
    image=compose_sd_image(data)
    (build / (prefix+'-idblock.img')).write_bytes(data)
    (build / (prefix+'-sd.img')).write_bytes(image)
    report = {'status': 'prepared-not-hardware-boot-verified', 'storageWrites': False, 'profile':args.profile, 'features':manifest['features'], 'usbSerial':manifest.get('usbSerial'),
        'sdOffsetBytes': SD_OFFSET, 'sdOffsetSectors': 64, 'idblockBytes': len(data),
        'stages': entries, 'imageBytes': len(image), 'imageSha256': sha(image),
        'idblockSha256': sha(data), 'payloadSha256': sha(payload),
        'sourceManifestSha256': sha((build / 'hello-manifest.json').read_bytes()),
        'limits': ['No card write or ROM SD boot test performed.',
                  'ROM maximum second-stage size remains hardware-unverified.',
                  'Raw image only; app code/assets are frozen in payload, no filesystem or partition table.',
                  'The usual SDK 512KiB ID-block partition is not used; no U-Boot follows.']}
    (build / (prefix+'-sd-manifest.json')).write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
