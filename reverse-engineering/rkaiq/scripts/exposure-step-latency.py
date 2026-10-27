#!/usr/bin/env python3
"""Measure bounded shutter-effect frame intervals on the physical SC3336.

Uses fixed gain/frame length and large increasing/decreasing shutter steps.
Missing statistics frames produce intervals; they are never filled in.
"""

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shlex
import subprocess


def median(values):
    ordered = sorted(values)
    middle = len(ordered) // 2
    return (
        ordered[middle]
        if len(ordered) % 2
        else (ordered[middle - 1] + ordered[middle]) / 2
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--serial", required=True)
    for name in ["binary", "plan", "dim-iq", "bright-iq", "prefix"]:
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--local", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if not PurePosixPath(args.prefix).is_absolute():
        parser.error("--prefix must be an absolute persistent board path")
    args.local.mkdir(parents=True, exist_ok=True)
    adb = ["adb", "-s", args.serial]

    def shell(command):
        return subprocess.check_output(adb + ["shell", command], text=True).strip()

    hashes = {
        name: shell("sha256sum " + shlex.quote(value)).split()[0]
        for name, value in [
            ("binary", args.binary),
            ("dimIq", args.dim_iq),
            ("brightIq", args.bright_iq),
            ("plan", args.plan),
        ]
    }
    cases = []
    for direction, iq, initial, target in [
        ("increase", args.dim_iq, 0.003, 0.024),
        ("decrease", args.bright_iq, 0.024, 0.003),
    ]:
        for frame in [18, 19, 20]:
            basename = args.prefix + "-" + direction + "-" + str(frame)
            assert (
                shell("test ! -e " + shlex.quote(basename + ".log") + " && echo absent")
                == "absent"
            )
            command = [
                args.binary,
                "first-frame-sc3336",
                args.plan,
                iq,
                "/dev/video20",
                "/dev/video11",
                basename,
                "/dev/video19",
                "--step-at",
                str(frame),
                "--step-seconds",
                str(target),
            ]
            remote = (
                shlex.join(command)
                + " > "
                + shlex.quote(basename + ".log")
                + ' 2>&1; result=$?; echo "$result" > '
                + shlex.quote(basename + ".exit")
            )
            shell(remote)
            for suffix in [
                ".log",
                ".exit",
                ".stats.raw.json",
                ".initial.json",
                ".json",
            ]:
                subprocess.run(
                    adb
                    + [
                        "pull",
                        basename + suffix,
                        str(args.local / (Path(basename).name + suffix)),
                    ],
                    check=True,
                    capture_output=True,
                )
            result = analyze(args.local / Path(basename).name, frame, initial, target)
            cases.append(result)
            print(json.dumps(result), flush=True)
    low = max(case["effectDelayFrames"][0] for case in cases)
    high = min(case["effectDelayFrames"][1] for case in cases)
    assert low <= high, "No common exposure effect delay across observations"
    assert low <= 2 <= high, (
        "Observed shutter delay conflicts with configured two-frame delay"
    )
    report = {
        "kind": "physical-sc3336-shutter-step-response",
        "passed": True,
        "hashes": hashes,
        "cases": cases,
        "commonDelayIntervalFrames": [low, high],
        "configuredSchedulerTimeDelayFrames": 2,
        "configuredTimeDelayConsistent": True,
        "scope": "Large shutter-only steps at three SOF phases, two directions, same scene and fixed analogue gain/frame length",
        "limitations": [
            "Sparse statistics yield inclusive frame intervals; no missing sample is invented.",
            "Gain, digital gain and frame-length changes are not qualified by this test.",
            "This does not qualify every runtime scheduling/load condition or full physical frame/exposure association.",
        ],
    }
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"passed": True, "commonDelayIntervalFrames": [low, high]}))


def analyze(base, step_frame, initial, target):
    def path(suffix):
        return Path(str(base) + suffix)

    assert int(path(".exit").read_text()) == 0, "Capture failed: " + str(base)
    events = []
    for line in path(".log").read_text().splitlines():
        try:
            value = json.loads(line)
            if isinstance(value, dict):
                events.append(value)
        except ValueError:
            pass
    finished = [
        event for event in events if event.get("event") == "first-frame-finished"
    ]
    steps = [event for event in events if event.get("event") == "exposure-step-applied"]
    starts = [
        event for event in events if event.get("event") == "initial-exposure-derived"
    ]
    assert len(finished) == len(steps) == len(starts) == 1 and finished[0]["success"]
    event = steps[0]
    assert (
        event["sofFrameId"] == step_frame
        and event["requestedCode"] == event["readbackCode"]
    )
    assert not event["gainChanged"] and not event["frameLengthChanged"]
    assert abs(starts[0]["seconds"] - initial) < 1e-6 and starts[0]["gain"] == 1
    assert (
        event["clock"] == "CLOCK_MONOTONIC"
        and event["writeEndNs"] >= event["writeStartNs"] >= event["sofTimestampNs"]
    )
    rows = json.loads(path(".stats.raw.json").read_text())["recentFrames"]
    assert all(a["frameId"] < b["frameId"] for a, b in zip(rows, rows[1:]))
    assert all(row["parametersId"] == 0 for row in rows), (
        "Unexpected ISP parameter change"
    )
    means = [
        (row["frameId"], row["aeLinear"]["weightedMeanLuma"])
        for row in rows
        if row["aeLinear"].get("valid")
    ]
    before = [mean for frame, mean in means if step_frame - 8 <= frame < step_frame]
    after = [mean for frame, mean in means if frame >= step_frame + 4]
    assert len(before) >= 3 and len(after) >= 3
    baseline, settled = median(before), median(after)
    difference = settled - baseline
    assert abs(difference) > max(1.0, abs(baseline) * 0.25), "Weak shutter response"
    assert (difference > 0) == (target > initial)
    fractions = [
        (frame, (mean - baseline) / difference)
        for frame, mean in means
        if frame >= step_frame - 1
    ]
    unchanged = [frame for frame, fraction in fractions if fraction <= 0.2]
    changed = [frame for frame, fraction in fractions if fraction >= 0.8]
    partial = [frame for frame, fraction in fractions if 0.2 < fraction < 0.8]
    assert unchanged and changed and max(unchanged) < min(changed) and not partial, (
        "Unresolved/partial transition"
    )
    first, last = min(changed), max(unchanged)
    interval = [max(0, last + 1 - step_frame), first - step_frame]
    assert 0 <= interval[0] <= interval[1] <= 5
    return {
        "name": base.name,
        "stepSof": step_frame,
        "initialSeconds": initial,
        "targetSeconds": target,
        "shutterCodes": [event["beforeCode"], event["requestedCode"]],
        "writeStartAfterSofUs": (event["writeStartNs"] - event["sofTimestampNs"])
        / 1000,
        "writeDurationUs": (event["writeEndNs"] - event["writeStartNs"]) / 1000,
        "baselineLuma": baseline,
        "settledLuma": settled,
        "lastUnchangedFrame": last,
        "firstChangedFrame": first,
        "effectDelayFrames": interval,
        "observedFractions": [
            [frame, round(fraction, 6)] for frame, fraction in fractions
        ],
        "logSha256": hashlib.sha256(path(".log").read_bytes()).hexdigest(),
        "statisticsSummarySha256": hashlib.sha256(
            path(".stats.raw.json").read_bytes()
        ).hexdigest(),
    }


if __name__ == "__main__":
    main()
