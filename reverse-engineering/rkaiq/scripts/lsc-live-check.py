#!/usr/bin/env python3
"""Check real submitted LSC records through original constructor/callback/converter."""

import argparse
import hashlib
import importlib
import json
from pathlib import Path
import struct
from differential import ROOT, BINARY

frames_ref = importlib.import_module("lsc-initialized")
converter_ref = importlib.import_module("isp-lsc")


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
    records = [e for e in events if e.get("event") == "automatic-lsc-processed"]
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
        "lsc_v2"
    ]
    initial_report = json.loads(path(".initial.json").read_text())
    startup = initial_report["lscStartup"]

    def frame(current, damping):
        return dict(
            current=current,
            damping=damping,
            force=False,
            bypass=False,
        )

    frames = [frame(startup["current"], 0.0)] + [
        frame(e["current"], e["damping"]) for e in records
    ]
    expected = frames_ref.OriginalConstructor().run(
        dict(calibration=cal, frames=frames)
    )
    assert expected[0]["updated"] and expected[0]["result"] == startup["result"]
    converter = converter_ref.OriginalLsc()

    def packed(result):
        raw = bytes.fromhex(
            converter.run_lsc(
                dict(parameters=bytes(11145).hex(), result=result, enabled=True)
            )["parameters"]
        )
        return raw[0x894:0x1225].hex()

    initial = path(".initial.bin").read_bytes()
    assert len(initial) == 11145
    assert struct.unpack_from("<Q", initial, 8)[0] & (1 << 4)
    assert initial[0x894:0x1225].hex() == packed(expected[0]["result"])
    for record, reference in zip(records, expected[1:]):
        assert record["updated"] == reference["updated"]
        assert record["result"] == reference["result"], record["frame"]
        assert record["converged"] == reference["converged"]
        assert record["controllerFrames"] == reference["frameCount"]
        if record["updated"]:
            assert record["packed"] == packed(reference["result"])
        else:
            assert record["packed"] is None
    report = dict(
        passed=True,
        processedLscFrames=len(records),
        startupLscEnabled=True,
        startupNativeCallbackAndPackingMatch=True,
        updatedFrames=sum(r["updated"] for r in records),
        noUpdateFrames=sum(not r["updated"] for r in records),
        queuedBatches=sum(r["queuedBatch"] for r in records),
        resultBytesComparedPerFrame=2442,
        packedBytesComparedPerUpdate=2449,
        processedStatistics=final[0]["processedStatistics"],
        parameterSubmissions=final[0]["parameterSubmissions"],
        maxParameterSnapshots=final[0]["maxParameterSnapshots"],
        allInputsMatchExactFrameAwbAndAssociatedAe=True,
        originalBinarySha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),
        ownerLogSha256=hashlib.sha256(path(".log").read_bytes()).hexdigest(),
        initialParametersSha256=hashlib.sha256(initial).hexdigest(),
        scope="Real startup/runtime inputs through full original AlscInit/AlscPrepare, LSC processing descriptor callback and complete ISP32 LSC converter. Accepted driver submissions checked, no vendor runtime loaded on board.",
        limitations=[
            "Native JSON parsing not executed; SDK scene/allocator and libc string/memory boundaries explicit. Original native module lookup, constructor, controller, callback and uClibc sqrtf execute.",
            "Exposure association labels are not independent physical sensor-gain timing proof.",
            "QBUF acceptance does not prove each proposal reached hardware before shutdown.",
            "Optical QR and image-quality/color-accuracy qualification remain open.",
        ],
    )
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
