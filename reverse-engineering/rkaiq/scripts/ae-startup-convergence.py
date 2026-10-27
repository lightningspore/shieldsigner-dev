#!/usr/bin/env python3
"""Check two real closed-loop captures from dim/bright initial conditions."""

import argparse
import hashlib
import json
import math
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def analyze(base, tolerance):
    def path(suffix):
        return Path(str(base) + suffix)

    events = []
    for line in path(".log").read_text().splitlines():
        try:
            value = json.loads(line)
            if isinstance(value, dict):
                events.append(value)
        except ValueError:
            pass
    finished = [x for x in events if x.get("event") == "automatic-ae-finished"]
    assert (
        len(finished) == 1
        and finished[0]["success"]
        and finished[0]["automaticWhiteBalance"]
    )
    initial = json.loads(path(".initial.json").read_text())
    target = initial["initialTargetLuma"]
    rows = json.loads(path(".stats.raw.json").read_text())["recentFrames"]
    samples = [
        (x["frameId"], x["aeLinear"]["weightedMeanLuma"])
        for x in rows
        if x["aeLinear"].get("valid")
    ]
    assert len(samples) >= 100 and all(
        a[0] < b[0] for a, b in zip(samples, samples[1:])
    )
    assert all(math.isfinite(mean) for _, mean in samples)
    tail = samples[-16:]
    average = math.fsum(mean for _, mean in tail) / len(tail)
    assert all(abs(mean - target) <= target * tolerance for _, mean in tail), (
        "Final samples outside 10% target band"
    )
    first = math.fsum(mean for _, mean in samples[:3]) / 3
    assert abs(average - target) < abs(first - target) * 0.3, (
        "Insufficient error reduction"
    )
    last_outside = max(
        (frame for frame, mean in samples if abs(mean - target) > target * tolerance),
        default=-1,
    )
    return {
        "capture": base.name,
        "initialSeconds": initial["requestedExposureSeconds"],
        "initialGain": initial["requestedGain"],
        "targetLuma": target,
        "firstThreeMeanLuma": first,
        "finalSixteenMeanLuma": average,
        "finalSixteenRange": [min(x[1] for x in tail), max(x[1] for x in tail)],
        "lastObservedOutsideBandFrame": last_outside,
        "statisticsFrames": len(samples),
        "processedStatistics": finished[0]["processedStatistics"],
        "parameterSubmissions": finished[0]["parameterSubmissions"],
        "maxParameterSnapshots": finished[0]["maxParameterSnapshots"],
        "samples": samples,
        "logSha256": digest(path(".log")),
        "statisticsSummarySha256": digest(path(".stats.raw.json")),
        "initialReportSha256": digest(path(".initial.json")),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("dim", type=Path)
    parser.add_argument("bright", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--iq", type=Path, required=True)
    args = parser.parse_args()
    iq = json.loads(args.iq.read_text())
    linear = iq["main_scene"][0]["sub_scene"][0]["scene_isp32"]["ae_calib"][
        "LinearAeCtrl"
    ]
    tolerance = linear["ToleranceIn"] / 100
    assert 0 < tolerance < 1
    dim, bright = analyze(args.dim, tolerance), analyze(args.bright, tolerance)
    assert dim["targetLuma"] == bright["targetLuma"]
    target = dim["targetLuma"]
    assert dim["firstThreeMeanLuma"] < target < bright["firstThreeMeanLuma"]
    report = {
        "passed": True,
        "kind": "physical-closed-loop-startup-convergence",
        "cases": [dim, bright],
        "targetBandFraction": tolerance,
        "toleranceOutPercent": linear["ToleranceOut"],
        "iqSha256": digest(args.iq),
        "crossRunDifferenceLuma": abs(
            dim["finalSixteenMeanLuma"] - bright["finalSixteenMeanLuma"]
        ),
        "strictFivePercentCrossRunAgreement": abs(
            dim["finalSixteenMeanLuma"] - bright["finalSixteenMeanLuma"]
        )
        < target * 0.05,
        "interpretation": "Both runs reach the calibrated target band; identical settled brightness is not required by native tolerance gating.",
        "limitations": [
            "Same physical scene, different initial exposure/gain; no optical illumination change.",
            "These runs do not prove all sensor-frame exposure associations or gain-transition timing.",
            "No successful optical QR or broad image-quality qualification is claimed.",
        ],
    }
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps(
            {
                "passed": True,
                "finalMeans": [
                    dim["finalSixteenMeanLuma"],
                    bright["finalSixteenMeanLuma"],
                ],
            }
        )
    )


if __name__ == "__main__":
    main()
