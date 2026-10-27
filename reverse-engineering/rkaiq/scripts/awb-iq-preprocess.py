#!/usr/bin/env python3
"""JSON-loaded independent AWB curve groups through native preprocessing."""

import hashlib, json, random, runpy, struct, subprocess, sys
from pathlib import Path
from awb_reference import RUNTIME
from differential import ROOT, BINARY, HEAP, f32


def main():
    m = json.loads((ROOT / "reverse-engineering/rkaiq/artifacts.json").read_text())
    iq = ROOT / ".tools/reverse-engineering/iqfiles" / m["iqFiles"][0]["name"]
    sha = hashlib.sha256(BINARY.read_bytes()).hexdigest()
    iq_sha = hashlib.sha256(iq.read_bytes()).hexdigest()
    runtime_sha = hashlib.sha256(RUNTIME.read_bytes()).hexdigest()
    assert (
        sha == m["binaries"][0]["sha256"]
        and iq_sha == m["iqFiles"][0]["sha256"]
        and runtime_sha == m["gccRuntime"]["memberSha256"]
    )
    ext = json.loads(iq.read_bytes())["main_scene"][0]["sub_scene"][0]["scene_isp32"][
        "wb_v32"
    ]["autoExtPara"]
    reference = runpy.run_path(str(Path(__file__).with_name("awb-preprocess.py")))
    arm = reference["Original"]()
    rng = random.Random(0x43555256)
    inputs = []
    expected = []
    decisions = {}
    metadata_cases = 0
    for i in range(192):
        e = json.loads(json.dumps(ext))
        if i >= 24:
            for j, (obj, keys) in enumerate(
                [
                    (
                        e["smartRun"]["cfg"],
                        ["lvVarTh", "wbgainAlgDiffTh", "wbgainHwDiffTh"],
                    ),
                    (e["division"]["wpNumTh"], ["low", "high"]),
                    (
                        e["xyRegionStableSelection"]["wpNumTh"],
                        ["forBigType", "forExtraType"],
                    ),
                    (e["runInterval"], ["intervalValue"]),
                    (e["tolerance"], ["toleranceValue"]),
                ]
            ):
                n = 1 + (i + j) % 5
                obj.update(
                    lumaValue=[float(k * 1000) for k in range(n)], lumaValue_len=n
                )
                for key in keys:
                    obj[key] = [
                        f32(
                            rng.uniform(
                                0,
                                3
                                if key == "intervalValue"
                                else 250
                                if key in ["low", "high", "forBigType", "forExtraType"]
                                else 0.1,
                            )
                        )
                        for _ in range(n)
                    ]
                    obj[key + "_len"] = n
            e["smartRun"]["enable"] = bool(i % 2)
        v = dict(
            mode=i % 3,
            update=bool(i % 2),
            enabled=True,
            countdown=[-1, 0, 20][i // 3 % 3],
            source=None
            if i % 5 == 0
            else [f32(rng.uniform(0, 5)), f32(rng.uniform(0, 5))],
            choice=i % 3,
            working=[0, 1, 16][i % 3],
            fallback=[0, 512, 10000][i % 3],
            override_enabled=bool(i % 4 == 0),
            override_valid=True,
            override=float(i % 8 * 1000),
            block=[15, 15],
            scale=1,
            frame=[0, 1, 2, 17, 100, 0xFFFFFFFF][i // 3 % 6],
            knots=[0.0, 1000.0, 200000.0],
            smart0=[0.0] * 3,
            smart1=[0.0] * 3,
            smart2=[0.0] * 3,
            intervals=[0.0] * 3,
            points0=[0.0] * 3,
            points1=[0.0] * 3,
            regions0=[0.0] * 3,
            regions1=[0.0] * 3,
        )
        v["curves"] = dict(
            smart=e["smartRun"]["cfg"],
            points=e["division"]["wpNumTh"],
            regions=e["xyRegionStableSelection"]["wpNumTh"],
            interval=e["runInterval"],
            enabled=e["smartRun"]["enable"],
        )
        if i % 2:
            v["metadata"] = dict(
                history=[128, 512],
                target=4,
                boundaries=[0, 128, 1024, 65536, 262144],
                thresholds=[110, 200, 65536, 65600],
                convergence=[bool(i % 4), True],
            )
            metadata_cases += 1
        v["common_iq"] = e
        out = arm.run(v)
        expected.append(out)
        key = str(out["decision"])
        decisions[key] = decisions.get(key, 0) + 1
        v["preprocess_iq"] = e
        inputs.append("awb-preprocess " + json.dumps(v, separators=(",", ":")))
        # Evaluate the separately used tolerance curve with original interpolation.
        x = e["tolerance"]["lumaValue"]
        y = e["tolerance"]["toleranceValue"]
        brightness = [0, 256, 512, 32768, 131072, 0xFFFFFFFF][i % 6]
        arm.uc.mem_write(HEAP + 0xA0000, struct.pack("<" + "f" * len(x), *x))
        arm.uc.mem_write(HEAP + 0xA0100, struct.pack("<" + "f" * len(y), *y))
        arm.invoke(
            "_Z13interpolationPKfS0_ifPf",
            [HEAP + 0xA0000, HEAP + 0xA0100, len(x), HEAP + 0xA0200],
            floats=[float(brightness)],
        )
        tolerance = struct.unpack("<I", arm.uc.mem_read(HEAP + 0xA0200, 4))[0]
        expected.append(
            dict(
                enabled=bool(e["smartRun"]["enable"]),
                lengths=[
                    len(e["smartRun"]["cfg"]["lumaValue"]),
                    len(e["runInterval"]["lumaValue"]),
                    len(e["division"]["wpNumTh"]["lumaValue"]),
                    len(e["xyRegionStableSelection"]["wpNumTh"]["lumaValue"]),
                    len(x),
                ],
                tolerance=tolerance,
            )
        )
        inputs.append(
            "awb-preprocess-parse "
            + json.dumps(dict(iq=e, brightness=brightness), separators=(",", ":"))
        )
    for i in range(8):
        e = json.loads(json.dumps(ext))
        if i == 0:
            e["smartRun"]["cfg"]["lvVarTh_len"] += 1
        elif i == 1:
            e["division"]["wpNumTh"]["high"].pop()
        elif i == 2:
            e["runInterval"]["lumaValue"] = [0, 0, 1, 2]
        elif i == 3:
            e["tolerance"]["toleranceValue"][0] = 1e100
        elif i == 4:
            e["smartRun"]["enable"] = 2
        elif i == 5:
            del e["xyRegionStableSelection"]["wpNumTh"]["forExtraType"]
        elif i == 6:
            e["runInterval"].update(
                lumaValue=list(range(9)),
                lumaValue_len=9,
                intervalValue=[0] * 9,
                intervalValue_len=9,
            )
        elif i == 7:
            e["smartRun"]["cfg"]["lumaValue_len"] = 0
        inputs.append(
            "awb-preprocess-parse "
            + json.dumps(dict(iq=e, brightness=0), separators=(",", ":"))
        )
    payload = "\n".join(inputs) + "\n"

    def compare(command):
        p = subprocess.run(
            command, input=payload, text=True, capture_output=True, check=True
        )
        actual = [json.loads(s) for s in p.stdout.splitlines()]
        assert len(actual) == len(expected) + 8
        for i, (a, b) in enumerate(zip(actual, expected)):
            assert a == b, (i, a, b)
        for a in actual[len(expected) :]:
            assert set(a) == {"error"}

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
        runtimeSha256=runtime_sha,
        preprocessCases=192,
        toleranceCases=192,
        metadataConfiguredCases=metadata_cases,
        commonEnvironmentLayout=True,
        decisions=decisions,
        malformedRejections=8,
        mismatches=0,
        arm=replay,
        scope="Owned independent IQ curves through native numerical preprocessor prefix and optional environment/history continuation, plus native tolerance interpolation.",
        limitations=[
            "Stops at metadata exit or PrepareMeasureResult entry; complete measurement preparation and gain/hardware continuation are not executed here.",
            "First 24 cases use unmodified IQ curves; later cases vary independent knot grids/lengths to exercise interpolation and ordering.",
            "Explicit geometry/exposure/history inputs; full IQ/session initialization and live AWB remain unfinished.",
        ],
    )
    (ROOT / "reverse-engineering/rkaiq/awb-iq-preprocess-equivalence.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
