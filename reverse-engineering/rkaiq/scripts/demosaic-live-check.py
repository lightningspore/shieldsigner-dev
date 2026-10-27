#!/usr/bin/env python3
"""Independently check logged, successfully enqueued live demosaic records."""

import argparse
import hashlib
import importlib
import json
from pathlib import Path
import struct

from differential import ROOT, BINARY, HEAP

reference = importlib.import_module("demosaic-frames")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("log", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    events = []
    for line in args.log.read_text().splitlines():
        try:
            value = json.loads(line)
            if isinstance(value, dict):
                events.append(value)
        except ValueError:
            pass
    submitted = [x for x in events if x.get("event") == "automatic-demosaic-submitted"]
    final = [x for x in events if x.get("event") == "automatic-ae-finished"]
    assert len(final) == 1 and final[0]["success"] and final[0]["automaticWhiteBalance"]
    assert len(submitted) >= 2 and len({x["iso"] for x in submitted}) >= 2
    assert all(a["frame"] < b["frame"] for a, b in zip(submitted, submitted[1:]))
    assert all(x["exposureFrame"] <= x["frame"] for x in submitted)
    assert (
        hashlib.sha256(BINARY.read_bytes()).hexdigest()
        == "ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9"
    )
    source = (
        ROOT
        / "dist/reverse-engineering/demosaic-selection-fixtures/sc3336-demosaic-subset.json"
    )
    calibration = json.loads(source.read_text())["param"]
    headers = list((ROOT / ".tools/reverse-engineering").rglob("debayer_head.h"))
    assert len(headers) == 1
    packed = reference.selection.pack_record(
        reference.selection.schema(headers[0].read_text()),
        "CalibDbV2_Debayer_Tuning_t",
        calibration,
    )
    arm = reference.OriginalFrame()
    arm.symbols["demosaic-frame"] = arm.resolve_symbol("processing", 0x124A2C)
    context, inp, exposure, out, hw, params = [
        HEAP + x for x in (0, 0x2000, 0x3000, 0x4000, 0x5000, 0x6000)
    ]
    arm.uc.mem_write(context, bytes(0x600))
    arm.uc.mem_write(context, b"\1")
    arm.uc.mem_write(context + 8, struct.pack("<i", 2))
    arm.uc.mem_write(context + 0x7C, packed)
    arm.uc.mem_write(context + 0x4C8, struct.pack("<i", 50))
    arm.uc.mem_write(inp, bytes(128))
    arm.uc.mem_write(inp, struct.pack("<I", context))
    arm.uc.mem_write(inp + 24, struct.pack("<I", exposure))
    arm.uc.mem_write(out, bytes(16))
    arm.uc.mem_write(out + 4, struct.pack("<I", hw))
    for event in submitted:
        arm.uc.mem_write(exposure, bytes(244))
        arm.uc.mem_write(exposure + 4, struct.pack("<3f", *event["gains"]))
        assert (
            arm.invoke("demosaic-frame", [inp, out]) == 0
            and arm.uc.mem_read(out, 1)[0] == 1
        )
        assert (
            struct.unpack("<i", arm.uc.mem_read(context + 0x4C8, 4))[0] == event["iso"]
        )
        assert bytes(arm.uc.mem_read(hw, 112)).hex() == event["hardware"]
        arm.uc.mem_write(params, bytes(11145))
        arm.invoke(
            "_ZN5RkCam11Isp32Params31convertAiqAdebayerToIsp32ParamsER20isp32_isp_params_cfgR20AdebayerHwConfigV2_s",
            [context, params, hw],
        )
        assert bytes(arm.uc.mem_read(params + 0x1282, 57)).hex() == event["packed"]
        assert all(
            struct.unpack("<Q", arm.uc.mem_read(params + offset, 8))[0] & (1 << 35)
            for offset in (0, 8, 16)
        )
    report = {
        "passed": True,
        "submittedUpdates": len(submitted),
        "isoRange": [
            min(x["iso"] for x in submitted),
            max(x["iso"] for x in submitted),
        ],
        "frames": [x["frame"] for x in submitted],
        "isos": [x["iso"] for x in submitted],
        "processedStatistics": final[0]["processedStatistics"],
        "parameterSubmissions": final[0]["parameterSubmissions"],
        "maxParameterSnapshots": final[0]["maxParameterSnapshots"],
        "originalBinarySha256": hashlib.sha256(BINARY.read_bytes()).hexdigest(),
        "ownerLogSha256": hashlib.sha256(args.log.read_bytes()).hexdigest(),
        "hardwareBytesComparedPerUpdate": 112,
        "packedBytesComparedPerUpdate": 57,
        "limitations": [
            "Records are logged after successful QBUF; queued final proposals may be cancelled during shutdown.",
            "Scheduler exposure association is not independent physical gain-timing proof.",
            "Diagnostic logging is modeled; original callback, tuning, quantization and converter instructions execute.",
        ],
    }
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
