#!/usr/bin/env python3
"""Check composed AWB payload isolation and deterministic host/ARM assembly.
This is an integration check, not whole native startup equivalence.
"""

import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
from differential import ROOT


def main():
    iq = (
        ROOT / ".tools/reverse-engineering/iqfiles/sc3336_CMK-OT2119-PC1_30IRC-F16.json"
    )
    iq_sha = hashlib.sha256(iq.read_bytes()).hexdigest()
    assert iq_sha == "8c816c0f83c6d4d951d5d4335e9c63a0893cd4f99c501f3f3558bbbca9d2c94a"
    with tempfile.TemporaryDirectory(prefix="shieldsigner-awb-assembly-") as temp:
        out = Path(temp)
        binary = ROOT / "firmware/rkaiq-rs/target/release/camera-probe"

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
        assert (
            hashlib.sha256(base).hexdigest()
            == "b5e031ec216f3a007d6b9b6c21bcd6b726d7edda0a6b98913016b66fe91ef2cd"
        )
        assert (
            hashlib.sha256(ae).hexdigest()
            == "2ffab69fcf67ac36ea58c446352acbcc6fcdb51079ae0afdf0377adce29cdebc"
        )
        assert len(awb) == 11145 and len(sdk) == 1204
        for i in (0, 8, 16):
            assert struct.unpack_from("<Q", awb, i)[0] == (
                struct.unpack_from("<Q", ae, i)[0] | (1 << 22)
            )
        assert awb[24:0xF4] == ae[24:0xF4] and awb[0x41B:] == ae[0x41B:]
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
        if "--arm" in sys.argv:
            d = ROOT / "firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release"
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
            arm="--arm" in sys.argv,
            preservesExistingAeAndFixedWb=True,
            scope="Offline composed FAST linear BayerNR/Gain1 measurement candidate",
            limitations=[
                "Complete original startup composition equivalence and hardware validation are pending.",
                "Normal time-share/HDR/OTP startup composition remains separate; no automatic WB controller is enabled.",
            ],
        )
        (
            ROOT / "reverse-engineering/rkaiq/awb-startup-assembly-validation.json"
        ).write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
