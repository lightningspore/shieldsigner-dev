#!/usr/bin/env python3
"""Classify brightness using the actual common-initialized native layout."""

import hashlib, json, runpy, struct, subprocess, sys
from pathlib import Path
from differential import ROOT, BINARY, HEAP


def main():
    manifest = json.loads(
        (ROOT / "reverse-engineering/rkaiq/artifacts.json").read_text()
    )
    iq = ROOT / ".tools/reverse-engineering/iqfiles" / manifest["iqFiles"][0]["name"]
    sha = hashlib.sha256(BINARY.read_bytes()).hexdigest()
    iq_sha = hashlib.sha256(iq.read_bytes()).hexdigest()
    assert (
        sha == manifest["binaries"][0]["sha256"]
        and iq_sha == manifest["iqFiles"][0]["sha256"]
    )
    ext = json.loads(iq.read_bytes())["main_scene"][0]["sub_scene"][0]["scene_isp32"][
        "wb_v32"
    ]["autoExtPara"]
    reference = runpy.run_path(str(Path(__file__).with_name("awb-iq-common.py")))
    arm = reference["Original"]()
    inputs = []
    expected = []
    coverage = {}
    for i in range(32):
        e = json.loads(json.dumps(ext))
        if i:
            e["lumaValueMatrix"] = [i + 1000 * j for j in range(16)]
            e["division"].update(
                lumaValThLow=100 + i,
                lumaValThLow2=200 + i,
                lumaValThHigh=6000 + i,
                lumaValThHigh2=12000 + i,
            )
        arm.run(e)  # Executes the complete original common initializer.
        cfg = bytes(arm.uc.mem_read(HEAP + 0x1000, 0x600))
        count = struct.unpack_from("<I", cfg, 0x164)[0]
        assert count == 16
        boundaries = list(struct.unpack_from("<17I", cfg, 0x168))
        thresholds = list(struct.unpack_from("<4I", cfg, 0x1A8))
        assert (
            boundaries[:16] == e["lumaValueMatrix"] and boundaries[-1] == thresholds[0]
        )
        last = e["lumaValueMatrix"][-1]
        samples = (
            e["lumaValueMatrix"]
            + [0, last - 1, last + 1, 0xFFFFFFFF]
            + [n + d for n in thresholds for d in (-1, 0, 1)]
        )
        assert len(samples) == 32
        for luma in samples:
            before = bytearray([0xA6]) * 16
            struct.pack_into("<i", before, 8, i % 7 - 3)
            arm.uc.mem_write(HEAP + 0x20000, bytes(before))
            stack = struct.pack("<5I", *thresholds[1:], HEAP + 0x20004, HEAP + 0x20008)
            arm.invoke(
                "_Z8AwbCalLVjiPjjjjjP8LVType_sP15EnvironmentLV_e",
                [luma, count, HEAP + 0x1168, thresholds[0]],
                stack=stack,
            )
            after = bytes(arm.uc.mem_read(HEAP + 0x20000, 16))
            assert after[:4] == before[:4] and after[12:] == before[12:]
            assert bytes(arm.uc.mem_read(HEAP + 0x1000, len(cfg))) == cfg
            level = struct.unpack_from("<I", after, 4)[0]
            environment = struct.unpack_from("<i", after, 8)[0]
            expected.append(
                dict(level=level, environment=environment, boundaries=boundaries)
            )
            inputs.append(
                "awb-iq-environment "
                + json.dumps(
                    dict(iq=e, luma=luma, previous=i % 7 - 3), separators=(",", ":")
                )
            )
            coverage[str(environment)] = coverage.get(str(environment), 0) + 1
    assert set(coverage) == set(map(str, range(16)))
    assert set(arm.calls) <= {"memcpy"} and not arm.runtime_calls
    payload = "\n".join(inputs) + "\n"

    def compare(command):
        p = subprocess.run(
            command, input=payload, text=True, capture_output=True, check=True
        )
        actual = [json.loads(line) for line in p.stdout.splitlines()]
        assert len(actual) == len(expected)
        for i, (a, b) in enumerate(zip(actual, expected)):
            assert a == b, (i, a, b)

    compare([str(ROOT / "firmware/rkaiq-rs/target/release/numeric-fixture")])
    replay = "--arm" in sys.argv
    if replay:
        d = ROOT / "firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release"
        compare(
            [
                "docker",
                "run",
                "--rm",
                "-i",
                "--platform",
                "linux/arm/v7",
                "--network=none",
                "--mount",
                f"type=bind,src={d},dst=/bincheck,readonly",
                "alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd",
                "/bincheck/numeric-fixture",
            ]
        )
    report = dict(
        binarySha256=sha,
        iqSha256=iq_sha,
        initializations=32,
        classifications=len(inputs),
        mismatches=0,
        arm=replay,
        environmentCoverage=coverage,
        elfEntries=dict(initializer="0xc8450", classifier="0xc9f68"),
        scope="Complete original common initializer followed by original brightness classification over its real contiguous strategy table, including all sixteen environment buckets.",
        limitations=[
            "Pinned calibration plus finite monotonic synthetic brightness matrices and thresholds; full AWB initialization/session processing remains separate.",
            "Other preprocessing/history, hardware reconfiguration and live AWB are not executed by this comparison.",
        ],
    )
    (ROOT / "reverse-engineering/rkaiq/awb-iq-environment-equivalence.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
