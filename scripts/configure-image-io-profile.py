#!/usr/bin/env python3
"""Strict opt-in IO profile transform for the pinned public application source.

Never probes hardware. Carrier remains the default. Only FOX_22 can change;
all other model objects and top-level fields must remain identical.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import stat
import subprocess

UPSTREAM_SHA256 = '6444ae780d74e346c5a52b239fb3871c95a05f5f4fd609a9bb11bdb00f6f472a'
TEMPLATE_SHA256 = '605adfc756018897c72544cfb669156efd9e97cca6cb44684c2a55283ca16c94'
OUTPUT_SHA256 = {'carrier': 'c2319b39618467da8e187fdcccf08a6895c8076fd4b64ae9f960ce560dc68a7f',
                 'base-fork': TEMPLATE_SHA256}
DEFAULT_TEMPLATE = Path(__file__).resolve().parents[1] / 'firmware/bench-profiles/base-fork-io-config.json'


def regular_bytes(path):
    path = Path(path)
    if path.is_symlink() or not stat.S_ISREG(path.stat().st_mode):
        raise ValueError('IO configuration must be a regular file, not a symlink')
    return path.read_bytes()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def selected(data):
    models = [item for item in data['models'] if item.get('shortname') == 'FOX_22']
    if len(models) != 1:
        raise ValueError('Expected exactly one FOX_22 model')
    return models[0]


def other_models(data):
    result = copy.deepcopy(data)
    result['models'] = [model for model in result['models'] if model.get('shortname') != 'FOX_22']
    return result


def configure(path, profile='carrier', template=None):
    if profile not in OUTPUT_SHA256:
        raise ValueError('IO profile must be carrier or base-fork')
    path = Path(path)
    source = regular_bytes(path)
    if digest(source) != UPSTREAM_SHA256:
        raise ValueError('IO source differs from exact pinned upstream; review before changing pins')
    original = json.loads(source)
    output = copy.deepcopy(original)
    target = selected(output)
    template_sha = None
    if profile == 'base-fork':
        raw_template = regular_bytes(DEFAULT_TEMPLATE if template is None else template)
        template_sha = digest(raw_template)
        if template_sha != TEMPLATE_SHA256:
            raise ValueError('Base-fork IO template differs from reviewed fixture')
        replacement = selected(json.loads(raw_template))
        # Confirm the fixture itself has no incidental changes to other boards.
        if other_models(json.loads(raw_template)) != other_models(original):
            raise ValueError('Base-fork fixture changes unrelated models')
        target.clear()
        target.update(copy.deepcopy(replacement))
    else:
        target['display']['spi_hz'] = 10_000_000
    if other_models(output) != other_models(original):
        raise ValueError('IO transform changed an unrelated model')
    encoded = (json.dumps(output, indent=2) + '\n').encode()
    if digest(encoded) != OUTPUT_SHA256[profile]:
        raise ValueError('Transformed IO output differs from reviewed profile')
    path.write_bytes(encoded)
    path.chmod(0o644)
    receipt = {'kind': 'shieldsigner-image-io-profile', 'profile': profile,
               'upstreamSha256': UPSTREAM_SHA256, 'templateSha256': template_sha,
               'outputSha256': OUTPUT_SHA256[profile], 'mode': 0o644,
               'onlyModelChanged': 'FOX_22', 'otherModelsUnchanged': True,
               'hardwareQualificationInferred': False}
    verify(path, receipt, profile)
    return receipt


def verify(path, receipt, profile):
    if profile not in OUTPUT_SHA256:
        raise ValueError('IO profile must be carrier or base-fork')
    expected = {'kind': 'shieldsigner-image-io-profile', 'profile': profile,
                'upstreamSha256': UPSTREAM_SHA256,
                'templateSha256': TEMPLATE_SHA256 if profile == 'base-fork' else None,
                'outputSha256': OUTPUT_SHA256[profile], 'mode': 0o644,
                'onlyModelChanged': 'FOX_22', 'otherModelsUnchanged': True,
                'hardwareQualificationInferred': False}
    if receipt != expected:
        raise ValueError('IO receipt differs from selected reviewed profile')
    path = Path(path)
    if digest(regular_bytes(path)) != OUTPUT_SHA256[profile]:
        raise ValueError('Installed IO configuration changed after selection')
    if stat.S_IMODE(path.stat().st_mode) != 0o644:
        raise ValueError('Installed IO configuration mode must be exactly 0644')
    return receipt


SDK_REVISION = '0b5c1f30ca6333b7ec5af70d26511da9ef8d39af'
DTS_DIR = 'sysdrv/source/kernel/arch/arm/boot/dts'
DTS_NAME = 'rv1103g-luckfox-pico-mini.dts'
DTSI_NAME = 'rv1103-luckfox-pico-ipc.dtsi'
DTS_SHA256 = 'b13bb1d796b0b1e2967a2def8104f79c872883694f1e64c024df187cd23b5aa0'
DTSI_SHA256 = 'ae383101204a94e50b37bc255086f9fe7955f0b293ef3338d8b611d728b4d52e'
UART2_OVERRIDE = b'''
/* ShieldSigner base-fork resource policy: GPIO42/43 are buttons, not UART2.
 * Apply after upstream console removal, which enables UART2 as a peripheral. */
&uart2 {
\tstatus = "disabled";
};
'''
PCSCD_SOURCE_SHA256 = '51d83ab6cb5f8e532818fb4fa59c02c25bca367233f4204a8523521579cb32a6'
PCSCD_HOLD = b'''#!/bin/sh
# ShieldSigner base-fork: UART2 belongs to GPIO42/43 buttons, not a card reader.
case "${1:-start}" in
    status) echo "pcscd held by base-fork IO resource policy"; exit 3 ;;
    *) echo "pcscd UART2 autostart held by base-fork IO resource policy"; exit 0 ;;
esac
'''


def sdk_revision(sdk):
    return subprocess.check_output(['git', '-C', str(sdk), 'rev-parse', 'HEAD'], text=True).strip()


def configure_kernel(sdk, profile='carrier'):
    """Only base-fork reserves UART2 pins as buttons; after SDK console patches."""
    if profile not in OUTPUT_SHA256:
        raise ValueError('IO profile must be carrier or base-fork')
    if profile == 'carrier':
        return {'kind': 'shieldsigner-io-kernel-policy', 'ioProfile': 'carrier', 'changed': False}
    sdk = Path(sdk)
    if sdk_revision(sdk) != SDK_REVISION:
        raise ValueError('IO kernel policy requires the reviewed SDK revision')
    dts = sdk / DTS_DIR / DTS_NAME
    dtsi = sdk / DTS_DIR / DTSI_NAME
    original, shared = regular_bytes(dts), regular_bytes(dtsi)
    if digest(shared) != DTSI_SHA256:
        raise ValueError('IPC DTSI differs from reviewed post-console source')
    if original.endswith(UART2_OVERRIDE):
        original = original[:-len(UART2_OVERRIDE)]
    if digest(original) != DTS_SHA256:
        raise ValueError('Mini DTS differs from reviewed post-console source')
    result = original + UART2_OVERRIDE
    dts.write_bytes(result)
    receipt = {'kind': 'shieldsigner-io-kernel-policy', 'ioProfile': 'base-fork',
               'sdkRevision': SDK_REVISION, 'dts': DTS_NAME, 'dtsi': DTSI_NAME,
               'originalDtsSha256': DTS_SHA256, 'dtsSha256': digest(result),
               'unchangedDtsiSha256': DTSI_SHA256, 'uart2Node': '/serial@ff4c0000',
               'uart2Status': 'disabled', 'buttonGlobalLines': [42, 43],
               'compiledDtbQualification': False}
    verify_kernel(sdk, receipt, profile)
    return receipt


def verify_kernel(sdk, receipt, profile):
    if profile == 'carrier':
        expected = {'kind': 'shieldsigner-io-kernel-policy', 'ioProfile': 'carrier', 'changed': False}
        if receipt != expected:
            raise ValueError('Carrier kernel policy receipt changed')
        return receipt
    if profile != 'base-fork' or receipt.get('ioProfile') != 'base-fork':
        raise ValueError('Kernel IO policy profile mismatch')
    sdk = Path(sdk)
    content = regular_bytes(sdk / DTS_DIR / DTS_NAME)
    if not content.endswith(UART2_OVERRIDE) or digest(content[:-len(UART2_OVERRIDE)]) != DTS_SHA256:
        raise ValueError('Missing exact last-wins UART2 disabled override')
    if sdk_revision(sdk) != SDK_REVISION or digest(regular_bytes(sdk / DTS_DIR / DTSI_NAME)) != DTSI_SHA256:
        raise ValueError('Kernel IO policy SDK/shared source changed')
    expected = {'kind': 'shieldsigner-io-kernel-policy', 'ioProfile': 'base-fork',
                'sdkRevision': SDK_REVISION, 'dts': DTS_NAME, 'dtsi': DTSI_NAME,
                'originalDtsSha256': DTS_SHA256, 'dtsSha256': digest(content),
                'unchangedDtsiSha256': DTSI_SHA256, 'uart2Node': '/serial@ff4c0000',
                'uart2Status': 'disabled', 'buttonGlobalLines': [42, 43],
                'compiledDtbQualification': False}
    if receipt != expected:
        raise ValueError('Kernel IO policy receipt changed')
    return receipt


def configure_resources(root, profile='carrier'):
    if profile not in OUTPUT_SHA256:
        raise ValueError('IO profile must be carrier or base-fork')
    if profile == 'carrier':
        return {'kind': 'shieldsigner-io-resource-policy', 'ioProfile': 'carrier', 'changed': False}
    service = Path(root) / 'etc/init.d/S60pcscd'
    original = regular_bytes(service)
    if digest(original) != PCSCD_SOURCE_SHA256 and original != PCSCD_HOLD:
        raise ValueError('Unreviewed PCSC service source; do not replace')
    service.write_bytes(PCSCD_HOLD)
    service.chmod(0o755)
    receipt = {'kind': 'shieldsigner-io-resource-policy', 'ioProfile': 'base-fork',
               'pcscdAutostart': 'held', 'pcscdPath': 'etc/init.d/S60pcscd',
               'upstreamServiceSha256': PCSCD_SOURCE_SHA256,
               'installedServiceSha256': digest(PCSCD_HOLD), 'mode': 0o755,
               'requiredCompiledUart2Status': 'disabled', 'buttonGlobalLines': [42, 43],
               'physicalPinQualificationInferred': False}
    verify_resources(root, receipt, profile)
    return receipt


def verify_resources(root, receipt, profile):
    if profile == 'carrier':
        expected = {'kind': 'shieldsigner-io-resource-policy', 'ioProfile': 'carrier', 'changed': False}
        if receipt != expected:
            raise ValueError('Carrier resource policy receipt changed')
        return receipt
    if profile != 'base-fork':
        raise ValueError('IO profile must be carrier or base-fork')
    expected = {'kind': 'shieldsigner-io-resource-policy', 'ioProfile': 'base-fork',
                'pcscdAutostart': 'held', 'pcscdPath': 'etc/init.d/S60pcscd',
                'upstreamServiceSha256': PCSCD_SOURCE_SHA256,
                'installedServiceSha256': digest(PCSCD_HOLD), 'mode': 0o755,
                'requiredCompiledUart2Status': 'disabled', 'buttonGlobalLines': [42, 43],
                'physicalPinQualificationInferred': False}
    if receipt != expected:
        raise ValueError('Base-fork resource receipt differs from reviewed policy')
    service = Path(root) / expected['pcscdPath']
    if regular_bytes(service) != PCSCD_HOLD or stat.S_IMODE(service.stat().st_mode) != 0o755:
        raise ValueError('PCSC held service bytes or mode changed')
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('io_config', type=Path, nargs='?')
    action = parser.add_mutually_exclusive_group()
    action.add_argument('--kernel-sdk', type=Path)
    action.add_argument('--rootfs', type=Path)
    parser.add_argument('--profile', choices=OUTPUT_SHA256, default='carrier')
    parser.add_argument('--template', type=Path)
    parser.add_argument('--receipt', type=Path, required=True)
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    if args.io_config and (args.kernel_sdk or args.rootfs):
        parser.error("Select exactly one IO configuration, kernel or rootfs action")
    if args.kernel_sdk:
        target, config_fn, verify_fn = args.kernel_sdk, configure_kernel, verify_kernel
    elif args.rootfs:
        target, config_fn, verify_fn = args.rootfs, configure_resources, verify_resources
    elif args.io_config:
        target, config_fn, verify_fn = args.io_config, configure, verify
    else:
        parser.error('Provide io_config, --kernel-sdk or --rootfs')
    if args.verify:
        result = verify_fn(target, json.loads(args.receipt.read_text()), args.profile)
    else:
        if args.receipt.exists() or args.receipt.is_symlink():
            parser.error('Choose a new receipt path')
        result = config_fn(target, args.profile, args.template) if config_fn is configure else config_fn(target, args.profile)
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
