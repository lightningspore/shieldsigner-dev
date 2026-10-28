#!/usr/bin/env python3
"""Check exact camera-kit release inputs without creating or replacing an archive."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tomllib

from elftools.elf.elffile import ELFFile
from elftools.common.exceptions import ELFError

ROOT = Path(__file__).resolve().parents[3]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--allow-dirty", action="store_true",
                        help="Development inspection only; package.py always requires committed inputs")
    args = parser.parse_args()
    checks = []

    def check(name, operation):
        try:
            result = operation()
            if result is False:
                raise ValueError("Required condition is false")
            checks.append({"name": name, "passed": True})
        except (AssertionError, OSError, ValueError, KeyError, TypeError, ELFError) as exc:
            checks.append({"name": name, "passed": False, "error": str(exc) or type(exc).__name__})

    def equal(actual, expected, message):
        if actual != expected:
            raise ValueError(message)

    dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip())
    if not args.allow_dirty:
        check("source-committed-and-clean", lambda: equal(dirty, False, "Commit source/evidence before freezing"))
    arm = ROOT / "firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release"
    native = ROOT / "dist/reverse-engineering/qr-native-build/cmake/shieldsigner-qr-reader"
    research = ROOT / "reverse-engineering/rkaiq"
    version = tomllib.loads((ROOT / 'firmware/rkaiq-rs/Cargo.toml').read_text())['package']['version']
    isp_name = 'isp-' + version.removesuffix('-dev') + '-fresh-hardware-validation'
    records = {}
    for name in ["arm-smoke", "application-integration-hardware-validation", "native-qr-integration-hardware-validation", isp_name]:
        check(name + ":read", lambda name=name: records.update({name: json.loads((research / (name + ".json")).read_text())}))

    def static_arm(path):
        with path.open("rb") as source:
            elf = ELFFile(source)
            equal(elf['e_machine'], 'EM_ARM', "Expected ARM ELF")
            equal(any(segment['p_type'] == 'PT_INTERP' for segment in elf.iter_segments()), False,
                  "Dynamic interpreter present")
            dynamic = elf.get_section_by_name('.dynamic')
            equal(dynamic is not None and any(tag.entry.d_tag == 'DT_NEEDED' for tag in dynamic.iter_tags()), False,
                  "Unexpected dynamic library dependency")

    for name, path in [(name, arm / name) for name in ['camera-probe', 'numeric-fixture', 'frame-preview']] + [('shieldsigner-qr-reader', native)]:
        check(name + ":static-arm", lambda path=path: static_arm(path))
    smoke = records.get('arm-smoke', {})
    for name in ['camera-probe', 'numeric-fixture', 'frame-preview']:
        check(name + ":exact-smoke-binary", lambda name=name: equal(digest(arm / name), smoke['binaries'][name], "ARM smoke binary hash is stale"))
    application = records.get('application-integration-hardware-validation', {})
    check("application:passed", lambda: application['passed'] is True)
    check("application:source-list", lambda: {'shieldsigner_integration.py', 'shieldsigner_video_stream.py', 'integration_hardware_check.py'} <= set(application['sourceSha256']))
    check("application:exact-camera", lambda: equal(application['cameraBinarySha256'], digest(arm / 'camera-probe'), "Application camera binary is stale"))
    for name, expected in application.get('sourceSha256', {}).items():
        check("application:source-name:" + name, lambda name=name: Path(name).name == name)
        check("application:source:" + name, lambda name=name, expected=expected: equal(
            digest(ROOT / 'firmware/rkaiq-rs/python' / name), expected, "Application Python source is stale"))
    qr = records.get('native-qr-integration-hardware-validation', {})
    check("native-qr:passed", lambda: qr['passed'] is True)
    check("native-qr:exact-worker", lambda: equal(qr['nativeWorkerSha256'], digest(native), "Native QR worker is stale"))
    check("native-qr:source-list", lambda: {'shieldsigner_qr_decoder.py', 'native_qr_hardware_check.py'} <= set(qr['pythonSourcesSha256']))
    for name, expected in qr.get('pythonSourcesSha256', {}).items():
        check("native-qr:source-name:" + name, lambda name=name: Path(name).name == name)
        check("native-qr:source:" + name, lambda name=name, expected=expected: equal(
            digest(ROOT / 'firmware/rkaiq-rs/python' / name), expected, "Native QR Python source is stale"))
    isp = records.get(isp_name, {})
    check('fresh-isp:passed', lambda: isp['passed'] is True)
    check('fresh-isp:exact-camera', lambda: equal(isp['cameraBinarySha256'], digest(arm / 'camera-probe'), 'Fresh ISP camera binary is stale'))
    check('fresh-isp:exact-qr-worker', lambda: equal(isp['qrReaderBinarySha256'], digest(native), 'Fresh ISP QR worker is stale'))
    for module in ['cnr', 'baynr', 'lsc', 'ccm', 'dpcc', 'demosaic', 'awb-translation', 'awb-joined']:
        check('fresh-isp:native-' + module, lambda module=module: isp['nativeReferences'][module]['passed'] is True)
    for module in ['bay3d', 'ynr', 'sharp']:
        check('fresh-isp:native-' + module, lambda module=module: isp['nativeReferences']['new-blocks']['modules'][module]['passed'] is True)
    check('fresh-isp:actual-application', lambda: isp['application']['ownerExitCode'] == 0 and
          isp['application']['receivedFrames'] >= 20 and isp['application']['installedCameraUnchanged'] is True)
    check('fresh-isp:joined-native-awb', lambda: isp['awbJoined']['framesCompared'] >= 32 and
          isp['awbJoined']['mismatchingFrames'] == 0 and
          isp['awbJoined']['matchesActualLiveOwnerGains'] == isp['awbJoined']['framesCompared'] and
          isp['awbJoined']['nativeCalibrationAndContextInitializationExecuted'] is True)
    report = {"kind": "camera-kit-release-preflight", "version": version,
              "sourceRevision": subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
              "sourceWorktreeDirty": dirty, "allowDirty": args.allow_dirty,
              "passed": all(check['passed'] for check in checks), "checks": checks,
              "scope": "Exact release input checks; does not build an image or qualify physical UI/lighting/power-cycle behavior"}
    if args.report:
        args.report.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
