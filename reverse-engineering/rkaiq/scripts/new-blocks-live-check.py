#!/usr/bin/env python3
"""Compare actual BAY3D/YNR/SHARP owner events with complete native helpers.

No synthetic corpus and no device access. --startup-only can inspect a failed
capture but explicitly never reports live capture qualification.
"""

import argparse
import hashlib
import importlib
import json
from pathlib import Path
import struct

from differential import BINARY, HEAP, ROOT, OriginalArm

SPEC = {
    "bay3d": dict(
        calibration="bayertnr_v23", offset=0x2869, size=253, bit=37, result=224
    ),
    "ynr": dict(calibration="ynr_v22", offset=0x2966, size=162, bit=38, result=168),
    "sharp": dict(calibration="sharp_v33", offset=0x2A43, size=175, bit=40, result=178),
}
INPUT_KEYS = ("seconds", "gains", "blc", "snr", "gray", "force")


def native_helpers(module):
    if module == "bay3d":
        helper = importlib.import_module("bay3d-frames")
        owner = helper.OriginalFrames()
        packer = helper.OriginalPacking()
        return owner.run, lambda result: packer.run(
            dict(result=result, parameters=bytes(11145).hex())
        )
    if module == "sharp":
        helper = importlib.import_module("sharp-native-check")
        owner = helper.OriginalSharp()
        return owner.frames, lambda result: owner.packed(result, bytes(11145).hex())
    helper = importlib.import_module("ynr-port-check")
    owner = helper.OriginalFrames()
    packer = OriginalArm(BINARY)

    def packed(result):
        parameters, source = HEAP + 0x10000, HEAP + 0x20000
        packer.uc.mem_write(parameters, bytes(11145))
        packer.uc.mem_write(source, bytes.fromhex(result))
        packer.invoke(
            "_ZN5RkCam11Isp32Params26convertAiqYnrToIsp32ParamsER20isp32_isp_params_cfgR16RK_YNR_Fix_V22_s",
            [HEAP, parameters, source],
        )
        return packer.uc.mem_read(parameters, 11145).hex()

    return owner.run, packed


def check(module, events, initial, metadata, scene, startup_only):
    spec = SPEC[module]
    seeds = [e for e in events if e.get("event") == module + "-controller-startup"]
    assert len(seeds) == 1, f"{module}: expected one enabled startup event"
    seed = seeds[0]
    requested = metadata[module + "Startup"]
    assert seed["matchesInitialRegisters"]
    assert seed["result"] == requested["result"], (
        f"{module}: startup owner/result differs"
    )
    assert seed["geometry"] == requested["geometry"], (
        f"{module}: startup geometry differs"
    )
    assert struct.unpack_from("<Q", initial, 8)[0] & (1 << spec["bit"]), (
        f"{module}: initial module is disabled"
    )
    runtime = [
        e for e in events if e.get("event") == "automatic-" + module + "-processed"
    ]
    if startup_only:
        runtime = []
    else:
        assert runtime, f"{module}: no runtime result events"
        assert all(a["frame"] < b["frame"] for a, b in zip(runtime, runtime[1:])), (
            f"{module}: runtime frame IDs are not increasing"
        )
    logged = [seed, *runtime]
    native, packer = native_helpers(module)
    expected = native(
        dict(
            calibration=scene[spec["calibration"]],
            geometry=seed["geometry"],
            result=bytes(spec["result"]).hex(),
            frames=[{key: event[key] for key in INPUT_KEYS} for event in logged],
        )
    )
    assert len(expected) == len(logged)
    section = slice(spec["offset"], spec["offset"] + spec["size"])
    for index, (event, wanted) in enumerate(zip(logged, expected, strict=True)):
        where = "startup" if index == 0 else f"frame {event['frame']}"
        for field in ("result", "selected", "exposure"):
            assert event[field] == wanted[field], f"{module} {where}: {field} differs"
        packed = bytes.fromhex(packer(wanted["result"]))[section].hex()
        if index == 0:
            assert wanted["updated"], f"{module}: native startup did not calculate"
            assert initial[section].hex() == packed, (
                f"{module}: startup packed bytes differ"
            )
        else:
            assert event["updated"] == wanted["updated"], (
                f"{module} {where}: update gate differs"
            )
            assert event["packed"] == (packed if wanted["updated"] else None), (
                f"{module} {where}: packed bytes differ"
            )
            assert event["exposureFrame"] <= event["frame"], (
                f"{module} {where}: future exposure association"
            )
            assert not event["updated"] or event["queuedBatch"], (
                f"{module} {where}: updated result was not queued"
            )
            assert (
                event["iso"]
                == struct.unpack_from("<i", bytes.fromhex(wanted["exposure"]), 60)[0]
            ), f"{module} {where}: cached ISO differs"
    return dict(
        passed=True,
        startupCompared=True,
        runtimeRecordsCompared=len(runtime),
        updatedRuntimeRecords=sum(e["updated"] for e in runtime),
        heldRuntimeRecords=sum(not e["updated"] for e in runtime),
        resultBytesComparedPerRecord=spec["result"],
        selectedBytesComparedPerRecord=len(bytes.fromhex(seed["selected"])),
        exposureBytesComparedPerRecord=len(bytes.fromhex(seed["exposure"])),
        packedBytesComparedPerUpdate=spec["size"],
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("base", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--modules", nargs="+", choices=tuple(SPEC), default=list(SPEC))
    parser.add_argument("--startup-only", action="store_true")
    args = parser.parse_args()

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
    finished = [e for e in events if e.get("event") == "first-frame-finished"]
    ae_finished = [e for e in events if e.get("event") == "automatic-ae-finished"]
    assert len(finished) == 1, "Missing/ambiguous capture completion event"
    capture_success = bool(finished[0].get("success"))
    if not args.startup_only:
        assert capture_success, (
            "Capture failed; use --startup-only for initialization only"
        )
        assert len(ae_finished) == 1 and ae_finished[0]["success"], (
            "Automatic owner failed"
        )
    initial = path(".initial.bin").read_bytes()
    assert len(initial) == 11145
    metadata = json.loads(path(".initial.json").read_text())
    iq = (
        ROOT / ".tools/reverse-engineering/iqfiles/sc3336_CMK-OT2119-PC1_30IRC-F16.json"
    )
    scene = json.loads(iq.read_text())["main_scene"][0]["sub_scene"][0]["scene_isp32"]
    modules = {}
    for module in args.modules:
        modules[module] = check(
            module, events, initial, metadata, scene, args.startup_only
        )
        print(
            "PASS:",
            module,
            "startup only" if args.startup_only else "startup/runtime",
            flush=True,
        )
    report = dict(
        passed=True,
        startupOnly=args.startup_only,
        captureSucceeded=capture_success,
        liveCaptureQualified=capture_success and not args.startup_only,
        modules=modules,
        originalBinarySha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),
        iqSha256=hashlib.sha256(iq.read_bytes()).hexdigest(),
        ownerLogSha256=hashlib.sha256(path(".log").read_bytes()).hexdigest(),
        initialParametersSha256=hashlib.sha256(initial).hexdigest(),
        scope=(
            "STARTUP ONLY; no live capture qualification. " if args.startup_only else ""
        )
        + "Actual logged inputs through complete native BAY3D/YNR/SHARP helpers; exact startup/runtime selected, cached exposure, fixed result and packed-byte comparisons for requested modules.",
        limitations=[
            "Existing native helper boundaries remain: typed SDK graph, allocation, strings/diagnostics and original math boundaries are documented by each helper.",
            "Exposure association labels and accepted queue submissions are not independent physical timing/register/pixel application proof.",
            "No optical QR, image-quality, LCD/buttons or cold-start qualification follows from this comparison.",
        ],
    )
    args.report.write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
