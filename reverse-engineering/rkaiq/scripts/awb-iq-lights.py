#!/usr/bin/env python3
"""Compare loaded SC3336 light priors and spatial gains with original ARM."""

import hashlib, json, random, runpy, struct, subprocess, sys
from pathlib import Path
from differential import BINARY, ROOT, f32
from awb_reference import RUNTIME, OriginalAwb


def main():
    manifest = json.loads(
        (ROOT / "reverse-engineering/rkaiq/artifacts.json").read_text()
    )
    iq = ROOT / ".tools/reverse-engineering/iqfiles" / manifest["iqFiles"][0]["name"]
    iq_sha = hashlib.sha256(iq.read_bytes()).hexdigest()
    binary_sha = hashlib.sha256(BINARY.read_bytes()).hexdigest()
    runtime_sha = hashlib.sha256(RUNTIME.read_bytes()).hexdigest()
    assert (
        iq_sha == manifest["iqFiles"][0]["sha256"]
        and binary_sha == manifest["binaries"][0]["sha256"]
        and runtime_sha == manifest["gccRuntime"]["memberSha256"]
    )
    wb = json.loads(iq.read_bytes())["main_scene"][0]["sub_scene"][0]["scene_isp32"][
        "wb_v32"
    ]
    lights = wb["autoPara"]["lightSources"]
    ext = wb["autoExtPara"]
    probability = runpy.run_path(str(Path(__file__).with_name("awb-probability.py")))
    high = runpy.run_path(str(Path(__file__).with_name("awb-high-gain.py")))
    p_arm = OriginalAwb(stdlib=True)
    h_arm = high["Original"](stdlib=True)
    rng = random.Random(0x49514C54)
    inputs = []
    expected = []
    kinds = {
        "CALIB_AWB_DOOR_TYPE_INDOOR": 1,
        "CALIB_AWB_DOOR_TYPE_AMBIGUITY": 2,
        "CALIB_AWB_DOOR_TYPE_OUTDOOR": 3,
    }
    for i in range(128):
        gain = lambda: [
            f32(rng.uniform(0.5, 4.0)),
            1.0,
            1.0,
            f32(rng.uniform(0.5, 4.0)),
        ]
        brightness = [0, 1023, 1024, 1025, 4096, 8191, 8192, 8193, 0xFFFFFFFF][i % 9]
        p = dict(
            seed=i,
            xy=i % 2,
            frame=i,
            fast=bool(i % 3 == 0),
            near=0.01,
            far=2.0,
            gain=gain(),
            brightness=brightness,
            thresholds=[100, 200, 400, 800],
            sample=[0.0, 2.0, 8.0, 128.0, 8192.0, 262144.0][i % 6],
            absolute=10.0,
            relative=0.1,
            lights=[],
        )
        h = dict(
            fast=p["fast"],
            brightness=brightness,
            xy=i % 2,
            group=i % 16,
            default=ext["defaultNightGain"],
            knots=ext["lumaValueMatrix"],
            percentages=ext["defaultNightGainWeight"],
            lights=[],
        )
        for j, c in enumerate(lights):
            p["lights"].append(
                dict(
                    gain=c["standardGainValue"],
                    kind=kinds[c["doorType"]],
                    count=[0, 1, 10, 100, 5000][(i + j) % 5],
                    knots=c["weight"]["lumaValue"],
                    weights=c["weight"]["weight"],
                    oldLuma=0.75,
                    statisticGain=gain(),
                )
            )
            h["lights"].append(
                dict(
                    selected_count=[0, 1, 100][(i + j) % 3],
                    selected_gain=gain(),
                    extra_count=[0, 1, 25][(i + j) % 3],
                    extra_gain=gain(),
                    extra_enabled=bool((i + j) % 2),
                    low=c["dayGainLvThSet"][0],
                    high=c["dayGainLvThSet"][1],
                    low_gain=c["defaultDayGainLow"],
                    high_gain=c["defaultDayGainHigh"],
                    percentage=c["staWeight"][i % 16],
                    probability=f32(rng.uniform(0.01, 1.0)),
                )
            )
        expected.extend([probability["run"](p_arm, p), high["native"](h_arm, h)])
        p["light_iq"] = h["light_iq"] = wb
        # Wrong duplicated manual values prove the parser feeds both algorithms.
        for l in p["lights"]:
            l.update(gain=[9.0, 9.0, 9.0, 9.0], kind=-1, knots=[0.0], weights=[0.0])
        for l in h["lights"]:
            l.update(
                low=0,
                high=0,
                low_gain=[9.0, 9.0, 9.0, 9.0],
                high_gain=[9.0, 9.0, 9.0, 9.0],
                percentage=0,
            )
        inputs.extend(
            [
                "awb-probability " + json.dumps(p, separators=(",", ":")),
                "awb-high-gain " + json.dumps(h, separators=(",", ":")),
            ]
        )
    assert (
        not p_arm.calls
        and not h_arm.calls
        and not p_arm.runtime.calls
        and not h_arm.runtime.calls
    )
    bits = lambda x: struct.unpack("<I", struct.pack("<f", x))[0]
    fs = lambda a: list(map(bits, a))
    expected.append(
        dict(
            first=next(
                i
                for i, c in enumerate(lights)
                if c["name"] == ext["lightSourceForFirstFrame"]
            ),
            lights=[
                dict(
                    name=c["name"],
                    kind=kinds[c["doorType"]],
                    reference=fs(c["standardGainValue"]),
                    uv=[fs(c["uvRegion"]["u"]), fs(c["uvRegion"]["v"])],
                    xy=[fs(c["xyRegion"]["normal"]), fs(c["xyRegion"]["big"])],
                    yuv_knots=fs(c["rtYuvRegion"]["thcurve_u"]),
                    yuv_thresholds=fs(c["rtYuvRegion"]["thcure_th"]),
                    yuv_line=fs(c["rtYuvRegion"]["lineVector"]),
                    yuv_distance=bits(c["rtYuvRegion"]["disP1P2"]),
                )
                for c in lights
            ],
        )
    )
    inputs.append("awb-lights-parse " + json.dumps(wb, separators=(",", ":")))
    for i in range(10):
        v = json.loads(json.dumps(wb))
        c = v["autoPara"]["lightSources"][0]
        if i == 0:
            v["autoPara"]["lightSources_len"] -= 1
        elif i == 1:
            c["doorType"] = "UNKNOWN"
        elif i == 2:
            c["staWeight"][0] = 256
        elif i == 3:
            c["dayGainLvThSet"][0] = 1.5
        elif i == 4:
            c["weight"]["weight_len"] += 1
        elif i == 5:
            c["weight"]["lumaValue"][1] = c["weight"]["lumaValue"][0]
        elif i == 6:
            v["autoExtPara"]["lightSourceForFirstFrame"] = "missing"
        elif i == 7:
            c["name"] = v["autoPara"]["lightSources"][1]["name"]
        elif i == 8:
            c["standardGainValue"][0] = 1e100
        elif i == 9:
            c["uvRegion"]["u"].pop()
        inputs.append("awb-lights-parse " + json.dumps(v, separators=(",", ":")))
    payload = "\n".join(inputs) + "\n"

    def compare(command):
        p = subprocess.run(
            command, input=payload, text=True, capture_output=True, check=True
        )
        actual = p.stdout.splitlines()
        assert len(actual) == len(expected) + 10
        for i, (a, b) in enumerate(zip(actual, expected)):
            result = a if isinstance(b, str) else json.loads(a)
            assert result == b, (i, result, b)
        for a in actual[len(expected) :]:
            assert set(json.loads(a)) == {"error"}

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
        binarySha256=binary_sha,
        iqSha256=iq_sha,
        runtimeSha256=runtime_sha,
        lightCount=len(lights),
        probabilityCases=128,
        highGainCases=128,
        metadataChecks=1,
        malformedRejections=10,
        mismatches=0,
        arm=replay,
        scope="JSON-loaded seven-light references/priors and spatial calibration used in original probability/weighted-gain and complete high-gain call-tree comparisons.",
        limitations=[
            "Shared global settings, statistics and extra-region flag remain explicit inputs; full AWB initialization is not replayed.",
            "Detection geometry is checked as parsed metadata, not yet applied to hardware reconfiguration.",
            "Finite synthetic statistics; no live automatic-white-balance qualification.",
        ],
    )
    (ROOT / "reverse-engineering/rkaiq/awb-iq-lights-equivalence.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
