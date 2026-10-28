#!/usr/bin/env python3
"""Check composed AWB payload isolation and deterministic host/ARM assembly.
This is an integration check, not whole native startup equivalence.
"""

import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import tempfile
from differential import ROOT, BINARY, HEAP, OriginalArm

AWB_CONVERTER = "_ZN5RkCam11Isp32Params26convertAiqAwbToIsp32ParamsER20isp32_isp_params_cfgRK25rk_aiq_awb_stat_cfg_v32_sb"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--binary",
        type=Path,
        default=ROOT / "firmware/rkaiq-rs/target/release/camera-probe",
    )
    parser.add_argument(
        "--arm-directory",
        type=Path,
        default=ROOT
        / "firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release",
    )
    parser.add_argument("--arm", action="store_true")
    parser.add_argument(
        "--report",
        type=Path,
        default=ROOT / "reverse-engineering/rkaiq/awb-startup-assembly-validation.json",
    )
    args = parser.parse_args()
    iq = (
        ROOT / ".tools/reverse-engineering/iqfiles/sc3336_CMK-OT2119-PC1_30IRC-F16.json"
    )
    iq_sha = hashlib.sha256(iq.read_bytes()).hexdigest()
    assert iq_sha == "8c816c0f83c6d4d951d5d4335e9c63a0893cd4f99c501f3f3558bbbca9d2c94a"
    with tempfile.TemporaryDirectory(prefix="shieldsigner-awb-assembly-") as temp:
        out = Path(temp)
        binary = args.binary

        def run(name, options):
            return json.loads(
                subprocess.run(
                    [
                        str(binary),
                        "make-initial-parameters",
                        str(iq),
                        str(out / name),
                        *options,
                    ],
                    text=True,
                    capture_output=True,
                    check=True,
                ).stdout
            )

        run("base.bin", [])
        run("ae.bin", ["--ae-measurements"])
        report = run("awb.bin", ["--awb-measurements", str(out / "sdk.bin"), "1"])
        base = (out / "base.bin").read_bytes()
        ae = (out / "ae.bin").read_bytes()
        awb = (out / "awb.bin").read_bytes()
        sdk = (out / "sdk.bin").read_bytes()
        assert len(base) == len(ae) == 11145
        # AE setup must preserve the existing AWB block; no whole-record
        # digest is an oracle for unrelated enabled algorithm defaults.
        assert base[0xF4:0x41B] == ae[0xF4:0x41B]
        assert len(awb) == 11145 and len(sdk) == 1204
        for i in (0, 8, 16):
            assert struct.unpack_from("<Q", awb, i)[0] == (
                struct.unpack_from("<Q", ae, i)[0] | (1 << 22)
            )
        assert awb[24:0xF4] == ae[24:0xF4] and awb[0x41B:] == ae[0x41B:]
        # Independent original ARM converter oracle for the complete composed
        # payload, starting from the AE-only bytes rather than expected hashes.
        manifest = json.loads(
            (ROOT / "reverse-engineering/rkaiq/artifacts.json").read_text()
        )
        native_sha = hashlib.sha256(BINARY.read_bytes()).hexdigest()
        assert native_sha == next(
            v["sha256"] for v in manifest["binaries"] if v["name"] == BINARY.name
        )
        native = OriginalArm(BINARY)
        context = bytes([0xA7]) * 1024
        native.uc.mem_write(HEAP, context)
        native.uc.mem_write(HEAP + 0x10000, ae)
        native.uc.mem_write(HEAP + 0x20000, sdk)
        native.invoke(AWB_CONVERTER, [HEAP, HEAP + 0x10000, HEAP + 0x20000, 1])
        expected = bytes(native.uc.mem_read(HEAP + 0x10000, 11145))
        assert awb == expected, (
            "Composed payload differs from original ARM AWB converter"
        )
        assert bytes(native.uc.mem_read(HEAP, 1024)) == context
        assert bytes(native.uc.mem_read(HEAP + 0x20000, 1204)) == sdk
        assert not native.calls, "Native packing should require no imported adapters"
        wb = json.loads(iq.read_text())["main_scene"][0]["sub_scene"][0]["scene_isp32"][
            "wb_v32"
        ]
        limits = wb["autoPara"]["limitRange"]
        expected_limits = tuple(
            round(limits[key][0] * 16)
            for key in ["maxR", "minR", "maxG", "minG", "maxB", "minB", "maxY", "minY"]
        )
        assert struct.unpack_from("<8H", sdk, 0x4A) == expected_limits
        assert sdk[0] == 1
        assert sdk[0x48] == 4 and sdk[0x464:0x46F] == b"FASTAWBACT\0"
        assert struct.unpack_from("<4H", sdk, 0x40) == (0, 0, 2304, 1296)
        assert struct.unpack_from("<3H", sdk, 0x5A) == (256, 256, 256)
        assert struct.unpack_from("<4i", sdk, 0x10) == (256,) * 4
        assert struct.unpack_from("<i", sdk, 0x60)[0] == 238
        assert struct.unpack_from("<4f", sdk, 0x4A4) == (1.0,) * 4
        assert (
            report["automaticWhiteBalance"] is False
            and report["awbMeasurementsConfigured"] is True
        )
        if args.arm:
            d = args.arm_directory
            command = [
                "docker",
                "run",
                "--rm",
                "--platform",
                "linux/arm/v7",
                "--network=none",
                "--mount",
                f"type=bind,src={d},dst=/bincheck,readonly",
                "--mount",
                f"type=bind,src={iq.parent},dst=/iq,readonly",
                "--mount",
                f"type=bind,src={out},dst=/out",
                "alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd",
                "/bincheck/camera-probe",
                "make-initial-parameters",
                "/iq/" + iq.name,
                "/out/arm.bin",
                "--awb-measurements",
                "/out/arm-sdk.bin",
                "1",
            ]
            arm_report = json.loads(
                subprocess.run(
                    command, text=True, capture_output=True, check=True
                ).stdout
            )
            assert (
                (out / "arm.bin").read_bytes() == awb
                and (out / "arm-sdk.bin").read_bytes() == sdk
                and arm_report == report
            )
        result = dict(
            iqSha256=iq_sha,
            parameterSha256=hashlib.sha256(awb).hexdigest(),
            sdkSha256=hashlib.sha256(sdk).hexdigest(),
            parameterBytes=len(awb),
            sdkBytes=len(sdk),
            arm=args.arm,
            armBinarySha256=(
                hashlib.sha256(
                    (args.arm_directory / "camera-probe").read_bytes()
                ).hexdigest()
                if args.arm
                else None
            ),
            binarySha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
            nativeBinarySha256=native_sha,
            scriptSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            nativeAwbConverterMatches=True,
            nativeImportedCalls=native.calls,
            unrelatedBytesPreserved=True,
            wholeRecordHashesAreProvenanceOnly=True,
            preservesExistingAeAndFixedWb=True,
            scope="Offline composed FAST linear BayerNR/Gain1 measurement candidate",
            limitations=[
                "Original converter equivalence covers packing of the emitted SDK record, not independent native derivation of that complete startup record; calibration fields are checked separately.",
                "Offline serialization check only; no hardware capture or optical qualification is performed.",
                "Normal time-share/HDR/OTP startup composition remains separate; no automatic WB controller is enabled.",
            ],
        )
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
