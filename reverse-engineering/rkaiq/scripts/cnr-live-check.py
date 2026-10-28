#!/usr/bin/env python3
"""Real CNR startup/runtime through native CIS metadata, controller and packing."""

import argparse
import hashlib
import importlib
import json
from pathlib import Path
import struct
from differential import ROOT, BINARY

frames_ref = importlib.import_module("cnr-frames")
converter_ref = importlib.import_module("isp-cnr")
cis_ref = importlib.import_module("ae-cis")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("base", type=Path)
    p.add_argument("--report", type=Path, required=True)
    p.add_argument(
        "--startup-only",
        action="store_true",
        help="Compare startup despite failed capture; never qualifies live capture",
    )
    args = p.parse_args()

    def path(s):
        return Path(str(args.base) + s)

    events = []
    for line in path(".log").read_text().splitlines():
        try:
            v = json.loads(line)
        except ValueError:
            continue
        if isinstance(v, dict):
            events.append(v)
    records = [e for e in events if e.get("event") == "automatic-cnr-processed"]
    final = [e for e in events if e.get("event") == "automatic-ae-finished"]
    assert len(final) == 1
    if not args.startup_only:
        assert final[0]["success"] and final[0]["automaticWhiteBalance"]
        assert any(
            e.get("event") == "first-frame-finished" and e.get("success")
            for e in events
        )
    else:
        records = []
    assert any(
        e.get("event") == "baynr-sensor-features-checked"
        and e["nrSwitchUnsupported"]
        and not e["dcgSupported"]
        for e in events
    )
    assert (args.startup_only or len(records) >= 10) and all(
        a["frame"] < b["frame"] for a, b in zip(records, records[1:])
    )
    requested_startup = json.loads(path(".initial.json").read_text())["cnrStartup"]
    seeds = [e for e in events if e.get("event") == "cnr-controller-startup"]
    assert len(seeds) == 1
    startup = seeds[0]
    assert (
        startup["matchesInitialRegisters"]
        and startup["result"] == requested_startup["result"]
    )
    initial_records = [r for r in records if r["exposureFrame"] == 0]
    assert args.startup_only or initial_records
    for r in initial_records:
        for key in ("seconds", "gains", "dcg", "snr", "blc"):
            assert r[key] == startup[key], (key, r[key], startup[key])

    assert requested_startup["requiresNrSwitchUnsupported"]
    assert startup["geometry"] == requested_startup["geometry"]
    assert startup["geometry"] == [2304, 1296]

    def frame(r):
        return {k: r[k] for k in ("seconds", "gains", "blc", "snr", "gray", "force")}

    frames = [frame(startup)] + [frame(r) for r in records]
    cis = cis_ref.OriginalCis(BINARY)
    for r in [startup, *records]:
        raw = bytearray(244)
        struct.pack_into("<4f", raw, 0, r["seconds"], *r["gains"])
        struct.pack_into("<i", raw, 20, r["dcg"])
        actual = cis.run(dict(noise=None, records=[raw.hex()], header=bytes(24).hex()))
        assert bytes.fromhex(actual[0])[240] == r["snr"]
        assert not r["gray"]
        if "frame" in r:
            assert r["exposureFrame"] <= r["frame"]
            assert r["queuedBatch"] or not r["updated"]
    iq = (
        ROOT / ".tools/reverse-engineering/iqfiles/sc3336_CMK-OT2119-PC1_30IRC-F16.json"
    )
    cal = json.loads(iq.read_text())["main_scene"][0]["sub_scene"][0]["scene_isp32"][
        "cnr_v30"
    ]
    original = frames_ref.OriginalFrames()
    expected = original.run(
        dict(
            calibration=cal,
            frames=frames,
            result=bytes(66).hex(),
            geometry=startup["geometry"],
        )
    )
    assert expected[0]["updated"] and expected[0]["result"] == startup["result"]
    assert (
        expected[0]["exposure"] == startup["exposure"]
        and expected[0]["selected"] == startup["selected"]
    )
    converter = converter_ref.OriginalCnr()

    def packed(result):
        return bytes.fromhex(
            converter.run_cnr(dict(parameters=bytes(11145).hex(), result=result))
        )[0x2A08:0x2A43].hex()

    initial = path(".initial.bin").read_bytes()
    assert len(initial) == 11145
    assert struct.unpack_from("<Q", initial, 8)[0] & (1 << 39)
    assert initial[0x2A08:0x2A43].hex() == packed(expected[0]["result"])
    for r, w in zip(records, expected[1:], strict=True):
        assert r["updated"] == w["updated"] and r["result"] == w["result"], r["frame"]
        assert r["exposure"] == w["exposure"] and r["selected"] == w["selected"], r[
            "frame"
        ]
        assert r["iso"] == struct.unpack_from("<i", bytes.fromhex(w["exposure"]), 60)[0]
        assert r["packed"] == (packed(w["result"]) if r["updated"] else None)
    report = dict(
        passed=True,
        startupOnly=args.startup_only,
        captureSucceeded=final[0]["success"],
        liveCaptureQualified=not args.startup_only and final[0]["success"],
        processedCnrFrames=len(records),
        startupCnrEnabled=True,
        startupNativeCallbackAndPackingMatch=True,
        updatedFrames=sum(r["updated"] for r in records),
        noUpdateFrames=sum(not r["updated"] for r in records),
        queuedBatches=sum(r["queuedBatch"] for r in records),
        resultBytesComparedPerFrame=66,
        selectedBytesComparedPerFrame=180,
        exposureBytesComparedPerFrame=88,
        startupMatchesAssociatedInitialRecord=bool(initial_records),
        requestedStartupSeconds=requested_startup["seconds"],
        effectiveStartupSeconds=startup["seconds"],
        packedBytesComparedPerUpdate=59,
        processedStatistics=final[0]["processedStatistics"],
        parameterSubmissions=final[0]["parameterSubmissions"],
        maxParameterSnapshots=final[0]["maxParameterSnapshots"],
        allInputsUseAssociatedAe=True,
        nativeCisDcgFallbackChecked=True,
        nrSwitchUnsupportedChecked=True,
        bay3dDisabled=not bool(struct.unpack_from("<Q", initial, 8)[0] & (1 << 37)),
        originalBinarySha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),
        ownerLogSha256=hashlib.sha256(path(".log").read_bytes()).hexdigest(),
        initialParametersSha256=hashlib.sha256(initial).hexdigest(),
        scope=("STARTUP ONLY; no live capture pass. " if args.startup_only else "")
        + "Real startup/runtime inputs through complete native sensor SNR helpers, CNR constructor, prepare/processing callbacks, calibration, selection, quantizer/original double log and full ISP32 dispatcher conversion. No vendor library runs on board.",
        limitations=[
            "General JSON parsing and C++ scheduling framework not executed; SDK calibration/AE/BLC records, allocation, strings and diagnostics are explicit boundaries.",
            "Associated AE records are scheduler reports, not independent physical sensor timing proof; QBUF acceptance does not prove final proposals applied before shutdown.",
            "Normal no-NR-switch/DCG-disabled profile; actual BAY3D enable is recorded; manual/HDR/optional sensor switching and optical QR/image-quality qualification remain open.",
        ],
    )
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
