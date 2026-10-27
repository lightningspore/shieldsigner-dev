#!/usr/bin/env python3
"""Check real submitted CCM records through original constructor/callback/converter."""

import argparse
import hashlib
import importlib
import json
from pathlib import Path
import struct
from differential import ROOT, BINARY

frames_ref = importlib.import_module("ccm-frames")
converter_ref = importlib.import_module("isp-ccm")


def f32(v):
    return struct.unpack("<f", struct.pack("<f", v))[0]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("base", type=Path)
    p.add_argument("--report", type=Path, required=True)
    args = p.parse_args()

    def path(suffix):
        return Path(str(args.base) + suffix)

    events = []
    for line in path(".log").read_text().splitlines():
        try:
            value = json.loads(line)
        except ValueError:
            continue
        if isinstance(value, dict):
            events.append(value)
    records = [e for e in events if e.get("event") == "automatic-ccm-processed"]
    final = [e for e in events if e.get("event") == "automatic-ae-finished"]
    assert len(final) == 1 and final[0]["success"] and final[0]["automaticWhiteBalance"]
    assert any(
        e.get("event") == "first-frame-finished" and e.get("success") for e in events
    )
    assert len(records) >= 10 and all(
        a["frame"] < b["frame"] for a, b in zip(records, records[1:])
    )
    awb = {
        e["frame"]: e for e in events if e.get("event") == "automatic-awb-statistics"
    }
    for record in records:
        assert record["exposureFrame"] <= record["frame"]
        assert record["queuedBatch"] or not record["updated"]
        gains = [f32(v) for v in record["gains"]]
        wb = [f32(v) for v in awb[record["frame"]]["gain"]]
        current = [
            f32(f32(gains[0] * gains[1]) * gains[2]),
            f32(wb[0] / wb[1]),
            f32(wb[3] / wb[2]),
        ]
        assert [f32(v) for v in record["current"]] == current
        assert record["damping"] == awb[record["frame"]]["ccmDamping"]
    iq = (
        ROOT / ".tools/reverse-engineering/iqfiles/sc3336_CMK-OT2119-PC1_30IRC-F16.json"
    )
    cal = json.loads(iq.read_text())["main_scene"][0]["sub_scene"][0]["scene_isp32"][
        "ccm_calib_v2"
    ]
    initial_report = json.loads(path(".initial.json").read_text())
    startup = initial_report["ccmStartup"]

    def frame(current, damping):
        return dict(
            current=current,
            damping=damping,
            active=True,
            attributes=False,
            reconfigure=False,
            gray=False,
            softwareGray=False,
        )

    frames = [frame(startup["current"], 0.0)] + [
        frame(e["current"], e["damping"]) for e in records
    ]
    expected = frames_ref.OriginalFrames(BINARY).run(
        dict(calibration=cal, frames=frames)
    )
    assert expected[0]["updated"] and expected[0]["output"] == startup["result"]
    converter = converter_ref.OriginalCcm(BINARY)

    def packed(result):
        raw = bytes.fromhex(
            converter.run_ccm(dict(parameters=bytes(11145).hex(), result=result))
        )
        return raw[0x12BB:0x130A].hex()

    initial = path(".initial.bin").read_bytes()
    assert len(initial) == 11145
    assert struct.unpack_from("<Q", initial, 8)[0] & (1 << 8)
    assert initial[0x12BB:0x130A].hex() == packed(expected[0]["output"])
    for record, reference in zip(records, expected[1:]):
        assert record["updated"] == reference["updated"]
        assert record["result"] == reference["output"], record["frame"]
        assert record["informationConverged"] == reference["informationConverged"]
        assert record["converged"] == reference["converged"]
        assert record["controllerFrames"] == reference["frames"]
        if record["updated"]:
            assert record["packed"] == packed(reference["output"])
        else:
            assert record["packed"] is None
    report = dict(
        passed=True,
        processedCcmFrames=len(records),
        startupCcmEnabled=True,
        startupNativeCallbackAndPackingMatch=True,
        updatedFrames=sum(r["updated"] for r in records),
        noUpdateFrames=sum(not r["updated"] for r in records),
        queuedBatches=sum(r["queuedBatch"] for r in records),
        resultBytesComparedPerFrame=156,
        packedBytesComparedPerUpdate=79,
        processedStatistics=final[0]["processedStatistics"],
        parameterSubmissions=final[0]["parameterSubmissions"],
        maxParameterSnapshots=final[0]["maxParameterSnapshots"],
        allInputsMatchExactFrameAwbAndAssociatedAe=True,
        originalBinarySha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),
        ownerLogSha256=hashlib.sha256(path(".log").read_bytes()).hexdigest(),
        initialParametersSha256=hashlib.sha256(initial).hexdigest(),
        scope="Real startup/runtime inputs through full original AccmInit, CCM processing descriptor callback and complete ISP32 CCM converter. Accepted driver submissions checked, no vendor runtime loaded on board.",
        limitations=[
            "Native JSON parsing not executed; SDK scene/allocator and libc string/memory boundaries explicit. Original native module lookup, constructor, controller, callback and uClibc floorf execute.",
            "Exposure association labels are not independent physical sensor-gain timing proof.",
            "QBUF acceptance does not prove each proposal reached hardware before shutdown.",
            "Optical QR and image-quality/color-accuracy qualification remain open.",
        ],
    )
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
