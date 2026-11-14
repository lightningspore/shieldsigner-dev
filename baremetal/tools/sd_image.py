# SPDX-License-Identifier: MIT
"""Prepare an experimental ROM SD image as regular files; never access devices.

Format facts: pinned Luckfox U-Boot tools/rkcommon.c header0_info_v2 and
scripts/spl.sh. Original validation/packaging code; vendor DDR stays unchanged.
"""
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


def main():
    build = ROOT / 'build'
    rkbin = ROOT / '.tools/rkbin'
    pins = json.loads((ROOT / 'stock-loader.json').read_text())
    for name in ['RKBOOT/RV1106MINIALL.ini', 'tools/boot_merger',
                 'bin/rv11/rv1106_ddr_924MHz_v1.16.bin']:
        if sha((rkbin / name).read_bytes()) != pins['files'][name]:
            raise SystemExit('Changed packaging input: ' + name)
    payload = (build / 'hello.bin').read_bytes()
    manifest = json.loads((build / 'hello-manifest.json').read_text())
    if manifest['features'] != 'fast-boot' or manifest['files']['build/hello.bin'] != sha(payload):
        raise SystemExit('Build fast-boot first; payload must match its manifest')
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
    image = bytearray(2 * 1024 * 1024)
    if SD_OFFSET + len(data) > len(image):
        raise SystemExit('ID block exceeds image reservation')
    image[SD_OFFSET:SD_OFFSET + len(data)] = data
    (build / 'runtime-idblock.img').write_bytes(data)
    (build / 'runtime-sd.img').write_bytes(image)
    report = {'status': 'prepared-not-hardware-boot-verified', 'storageWrites': False,
        'sdOffsetBytes': SD_OFFSET, 'sdOffsetSectors': 64, 'idblockBytes': len(data),
        'stages': entries, 'imageBytes': len(image), 'imageSha256': sha(image),
        'idblockSha256': sha(data), 'payloadSha256': sha(payload),
        'sourceManifestSha256': sha((build / 'hello-manifest.json').read_bytes()),
        'limits': ['No card write or ROM SD boot test performed.',
                  'ROM maximum second-stage size remains hardware-unverified.',
                  'Raw image only; no app filesystem or partition table yet.',
                  'The usual SDK 512KiB ID-block partition is not used; no U-Boot follows.']}
    (build / 'runtime-sd-manifest.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
