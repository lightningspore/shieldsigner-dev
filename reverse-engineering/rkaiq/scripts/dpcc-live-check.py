#!/usr/bin/env python3
"""Compare successfully enqueued live DPCC records with native callback/packing."""

import argparse
import hashlib
import importlib
import json
from pathlib import Path
import struct

from differential import ROOT, BINARY, HEAP, regs

reference = importlib.import_module("dpcc-automatic")


class OriginalLive(reference.OriginalAutomatic):
    def __init__(self):
        super().__init__()
        for name, address in self.symbols.items():
            if "SharedItemBaseEE12get_cast_ptr" in name:
                self.stubs[address & ~1] = "dpcc-live-cast"

    def hook(self, uc, address, size, user):
        if self.stubs.get(address) == "dpcc-live-cast":
            uc.reg_write(regs.UC_ARM_REG_R0, HEAP + 0x80000)
            uc.reg_write(regs.UC_ARM_REG_PC, uc.reg_read(regs.UC_ARM_REG_LR))
            return
        super().hook(uc, address, size, user)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("base", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    def path(suffix):
        return Path(str(args.base) + suffix)

    events = []
    for line in path(".log").read_text().splitlines():
        try:
            value = json.loads(line)
            if isinstance(value, dict):
                events.append(value)
        except ValueError:
            pass
    updates = [x for x in events if x.get("event") == "automatic-dpcc-submitted"]
    finished = [x for x in events if x.get("event") == "automatic-ae-finished"]
    assert (
        len(finished) == 1
        and finished[0]["success"]
        and finished[0]["automaticWhiteBalance"]
    )
    assert len(updates) >= 2 and len({x["iso"] for x in updates}) >= 2
    assert all(a["frame"] < b["frame"] for a, b in zip(updates, updates[1:]))
    assert all(x["exposureFrame"] <= x["frame"] for x in updates)
    arm = OriginalLive()
    header = ROOT / ".tools/reverse-engineering/headers/adpcc_head.h"
    schema = reference.schema_full(header.read_text())
    iq = (
        ROOT / ".tools/reverse-engineering/iqfiles/sc3336_CMK-OT2119-PC1_30IRC-F16.json"
    )
    cal = json.loads(iq.read_text())["main_scene"][0]["sub_scene"][0]["scene_isp32"][
        "adpcc_calib"
    ]["DpccTuningPara"]
    source, _ = reference.pack_full(
        schema, "CalibDbDpccV20_t", cal, arm, [HEAP + 0x60000]
    )
    arm.uc.mem_write(HEAP + 0x20000, source)
    arm.uc.mem_write(HEAP + 0x1000, bytes(4))
    assert (
        arm.invoke(
            "_Z9AdpccInitPP14AdpccContext_sP21CamCalibDbV2Context_s",
            [HEAP + 0x1000, HEAP],
        )
        == 0
    )
    context = HEAP + 0x40000
    inp, out, result, exposure = [
        HEAP + x for x in (0x10000, 0x11000, 0x12000, 0x13000)
    ]
    arm.uc.mem_write(inp, bytes(64))
    arm.uc.mem_write(inp, struct.pack("<I", context))
    arm.uc.mem_write(inp + 24, struct.pack("<I", exposure))
    arm.uc.mem_write(out, bytes(16))
    arm.uc.mem_write(out + 4, struct.pack("<I", result))
    arm.uc.mem_write(result, bytes(192))
    arm.symbols["dpcc-frame"] = arm.resolve_symbol("processing", 0x12A67C)
    proxy, smart, cpp, isp, vtable, params = [
        HEAP + x for x in (0x80000, 0x81000, 0x82000, 0x83000, 0x8600C, 0x90000)
    ]
    arm.uc.mem_write(isp, bytes(0x3000))
    arm.uc.mem_write(isp, struct.pack("<I", vtable))
    arm.uc.mem_write(vtable - 12, bytes(4))
    arm.uc.mem_write(proxy, bytes(0x100))
    arm.uc.mem_write(proxy + 100, struct.pack("<I", 6))
    arm.uc.mem_write(proxy + 0x6C, struct.pack("<I", cpp))
    arm.uc.mem_write(smart, struct.pack("<II", proxy, 0))
    for event in updates:
        arm.uc.mem_write(
            exposure, struct.pack("<4f", 0.003, *event["gains"]) + bytes(228)
        )
        arm.invoke("dpcc-frame", [inp, out])
        assert arm.uc.mem_read(out, 1)[0] == 1
        assert struct.unpack("<i", arm.uc.mem_read(context + 48, 4))[0] == event["iso"]
        native = bytes(arm.uc.mem_read(result, 192))
        assert native.hex() == event["result"]
        arm.uc.mem_write(cpp, bytes(8) + native)
        arm.uc.mem_write(params, bytes(11145))
        assert (
            arm.invoke(
                "_ZN5RkCam11Isp32Params24convert3aResultsToIspCfgERN4XCam8SmartPtrINS_14SharedItemBaseEEEPvb",
                [isp, smart, params, 0],
            )
            == 1
        )
        assert bytes(arm.uc.mem_read(params + 0x7DA, 186)).hex() == event["packed"]
        assert all(
            struct.unpack("<Q", arm.uc.mem_read(params + o, 8))[0] & 1
            for o in (0, 8, 16)
        )
    initial = path(".initial.bin").read_bytes()
    assert len(initial) == 11145 and struct.unpack_from("<Q", initial, 8)[0] & 1
    assert initial[0x7DA:0x894].hex() == updates[0]["packed"], (
        "Startup/runtime DPCC differ at the initial ISO"
    )
    report = {
        "passed": True,
        "updates": len(updates),
        "isoRange": [min(x["iso"] for x in updates), max(x["iso"] for x in updates)],
        "frames": [x["frame"] for x in updates],
        "isos": [x["iso"] for x in updates],
        "resultBytesComparedPerUpdate": 192,
        "packedBytesComparedPerUpdate": 186,
        "startupDpccEnabled": True,
        "startupMatchesFirstRuntimeResult": True,
        "processedStatistics": finished[0]["processedStatistics"],
        "parameterSubmissions": finished[0]["parameterSubmissions"],
        "maxParameterSnapshots": finished[0]["maxParameterSnapshots"],
        "originalBinarySha256": hashlib.sha256(BINARY.read_bytes()).hexdigest(),
        "ownerLogSha256": hashlib.sha256(path(".log").read_bytes()).hexdigest(),
        "initialParametersSha256": hashlib.sha256(initial).hexdigest(),
        "limitations": [
            "Native init retains allocator/IQ-module-lookup/log boundaries, and the dispatcher uses a controlled typed C++ cast.",
            "The callback time input is an unused placeholder in this expert/sensor-auto-disabled path; actual logged gains drive ISO.",
            "Successful QBUF is submission proof, not independent physical register/pixel application proof.",
            "Optical QR and image-quality qualification remain open.",
        ],
    }
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
