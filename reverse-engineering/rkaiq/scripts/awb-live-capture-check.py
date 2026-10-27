#!/usr/bin/env python3
"""Check normal time-share capture evidence, including the zero-ID regression.

Reads private local artifacts only. Original-ARM numerical translation is an
independent check supplied via --native-report; this script does not emulate it.
"""

import argparse
import hashlib
import json
from pathlib import Path
import struct


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("base", type=Path)
    ap.add_argument("--native-report", type=Path)
    ap.add_argument("--report", type=Path)
    ap.add_argument("--min-submissions", type=int, default=0)
    args = ap.parse_args()

    def path(suffix):
        return Path(str(args.base) + suffix)

    events = []
    for line in path(".log").read_text().splitlines():
        try:
            v = json.loads(line)
            if isinstance(v, dict):
                events.append(v)
        except json.JSONDecodeError:
            pass
    finished = [v for v in events if v.get("event") == "first-frame-finished"]
    assert len(finished) == 1 and finished[0]["success"], (
        "Capture did not finish successfully"
    )
    ae = [v for v in events if v.get("event") == "automatic-ae-statistics"]
    awb = [v for v in events if v.get("event") == "automatic-awb-statistics"]
    assert len(awb) > 2 and len(ae) > 2, "Too few controller events"
    ids = {0} | {v["frame"] for v in ae if v["frame"] != 0}
    assert all(v["parametersId"] in ids for v in awb), "Unknown parameter ID"
    assert any(v["parametersId"] != 0 for v in awb), (
        "Runtime batches never changed parameter ID"
    )
    assert any(v["group"] == -1 and v["activeLights"] == 4 for v in awb), (
        "No FAST startup evidence"
    )
    for group, count in [(0, 4), (1, 3)]:
        assert any(
            v["group"] == group
            and v["physicalLights"] == count
            and v["activeLights"] == 7
            for v in awb
        ), f"Normal group {group} not observed"
    normal = [v for v in awb if v["group"] >= 0]
    assert any(not v["complete"] and not v["calculated"] for v in normal), (
        "No incomplete-cohort hold evidence"
    )
    assert any(v["complete"] and v["calculated"] for v in normal), (
        "No complete normal calculation"
    )
    for previous, current in zip(awb, awb[1:]):
        assert current["frame"] > previous["frame"], "Non-increasing AWB statistics"
        if not current["calculated"]:
            assert current["gain"] == previous["gain"], "Held frame changed gain"
    raw = path(".stats.raw").read_bytes()
    assert len(raw) in (13036, 13040)
    frame, parameter = struct.unpack_from("<II", raw, 0x32E4)
    translated = json.loads(path(".awb-translated.json").read_text())
    assert (frame, parameter) == (translated["frameId"], translated["parametersId"])
    sdk = path(".awb-effective-sdk.bin").read_bytes()
    decoded = path(".awb-translated.bin").read_bytes()
    assert len(sdk) == 1204 and len(decoded) == 7680
    assert sdk[0x48] == decoded[0x1D74]
    assert sdk[0x450:0x464] == decoded[0x1D78:0x1D8C]
    assert sdk[0x464:0x4A4] == decoded[0x1D8C:0x1DCC]
    image = json.loads(path(".json").read_text())
    image_saved = image.get("sceneImageSaved", True)
    assert isinstance(image_saved, bool)
    assert image["captureKind"] == "image" and image["bytes"] == 460800
    if image_saved:
        assert args.base.stat().st_size == 460800, "Wrong image byte count"
    else:
        assert image["payloadSaved"] is False and not args.base.exists(), (
            "Unexpected scene image"
        )

    numerical = False
    if args.native_report:
        native = json.loads(args.native_report.read_text())
        assert native["bytesCompared"] == 7680 and native["mismatches"] == 0
        assert native["parametersId"] == parameter and native["frameId"] == frame
        assert native["snapshotSha256"] == hashlib.sha256(sdk).hexdigest()
        assert native["statisticsSha256"] == hashlib.sha256(raw).hexdigest()
        assert native["translatedSha256"] == hashlib.sha256(decoded).hexdigest()
        numerical = True
    ae_summary = next(v for v in events if v.get("event") == "automatic-ae-finished")
    assert ae_summary["processedStatistics"] == len(ae), "Missing AE log events"
    submissions = ae_summary.get("parameterSubmissions")
    peak = ae_summary.get("maxParameterSnapshots")
    retired = ae_summary.get("retiredParameterSnapshots")
    if args.min_submissions:
        assert submissions is not None and submissions >= args.min_submissions, (
            "Too few successful parameter submissions"
        )
        assert peak is not None and peak <= 128, "Unbounded resident snapshot history"
        assert retired is not None and retired > 0, "No snapshots retired"
        assert ae_summary["parameterSnapshots"] <= 128
        assert len(ae_summary["sensorWrites"]) <= ae_summary["sensorTraceLimit"]
        assert len(ae_summary["sensorQueries"]) <= ae_summary["sensorTraceLimit"]
        queue = next(
            v for v in events if v.get("event") == "finished" and "callTraceLimit" in v
        )
        assert len(queue["calls"]) <= queue["callTraceLimit"]
    report = dict(
        kind="normal-timeshare-live-capture-check",
        passed=True,
        aeFrames=len(ae),
        awbFrames=len(awb),
        normalFrames=len(normal),
        normalGroups=sorted({v["group"] for v in normal}),
        finalFrame=frame,
        finalParametersId=parameter,
        maxActiveLights=max(v["activeLights"] for v in awb),
        nativeTranslationChecked=numerical,
        sceneImageSaved=image_saved,
        parameterSubmissions=submissions,
        maxParameterSnapshots=peak,
        retiredParameterSnapshots=retired,
        scope="Logged controller transitions, registered IDs, held gains, raw header and saved effective SDK metadata; no physical-latency/color-accuracy qualification",
    )
    if args.report:
        args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
