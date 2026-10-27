#!/usr/bin/env python3
"""Challenge a production AWB session with explicitly transformed captured data.

This is numerical/CPU replay, not an optical lighting change. Original ARM
comparison covers the persistent measurement-stability gate, not full native
joined-controller equivalence.
"""
import argparse
import hashlib
import importlib
import json
from pathlib import Path
import shlex
import struct
import subprocess
import tempfile
import tomllib
import uuid

from differential import BINARY, HEAP, ROOT
from awb_reference import RUNTIME

OriginalStability = importlib.import_module("awb-stability").OriginalStability
SYMBOL = "_Z22IsMeasureResultStable4P12awb_contex_sPK30rk_aiq_awb_stat_blk_res_v201_s"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("samples", type=Path)
    parser.add_argument("--adb")
    parser.add_argument("--board-binary")
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    frames = [(args.samples / ("group-{}.translated.bin".format(i))).read_bytes() for i in range(2)]
    assert all(len(raw) == 7680 and struct.unpack_from("<i", raw, 0x1D78)[0] == i for i, raw in enumerate(frames))
    metadata = [json.loads((args.samples / ("group-{}.json".format(i))).read_text()) for i in range(2)]
    iq_path = ROOT / ".tools/reverse-engineering/iqfiles/sc3336_CMK-OT2119-PC1_30IRC-F16.json"
    assert digest(iq_path) == "8c816c0f83c6d4d951d5d4335e9c63a0893cd4f99c501f3f3558bbbca9d2c94a"
    wb = json.loads(iq_path.read_text())["main_scene"][0]["sub_scene"][0]["scene_isp32"]["wb_v32"]
    changed = []
    for frame in frames:
        raw = bytearray(frame)
        # Simulated raw R*0.75, B*1.25: aggregate raw sums change directly;
        # accumulated white-point correction gains change inversely. Counts,
        # calibrated groups, exposure and configuration identity stay fixed.
        for index, factor in [(0, .75), (2, 1.25)]:
            offset = 0x1DE8 + index*8
            struct.pack_into("<q", raw, offset, round(struct.unpack_from("<q", raw, offset)[0]*factor))
        for light in range(raw[0x1D74]):
            for region in range(2):
                offset = light*48+region*24
                for channel, factor in [(8, 1/.75), (16, 1/1.25)]:
                    struct.pack_into("<q", raw, offset+channel, round(struct.unpack_from("<q", raw, offset+channel)[0]*factor))
        changed.append(bytes(raw))
    brightness = sum(m["normalizedBrightness"] for m in metadata)/2
    iso = sum(m["iso"] for m in metadata)/2
    stages = [("baseline", frames, 40, brightness), ("color-step", changed, 40, brightness),
              ("restore", frames, 40, brightness), ("brightness-step", frames, 20, brightness*.35)]
    value = {"iq": wb, "dimensions": [2304,1296], "sample_scale":1, "iso":iso,
             "stages":[{"raw":[raw.hex() for raw in records], "cycles":cycles,
                        "normalized_brightness":luma} for _,records,cycles,luma in stages]}
    line = "awb-captured-sequence " + json.dumps(value,separators=(",", ":")) + "\n"
    result = subprocess.run([str(ROOT/"firmware/rkaiq-rs/target/release/numeric-fixture")],
                            input=line,text=True,capture_output=True,check=True)
    actual = json.loads(result.stdout)
    assert "error" not in actual, actual
    board_digest = None
    if args.adb:
        assert args.board_binary and Path(args.board_binary).is_absolute()
        remote = "/tmp/ss-awb-scene-" + uuid.uuid4().hex + ".private.txt"
        adb = ["adb", "-s", args.adb]
        board_digest = subprocess.check_output(adb+["shell","sha256sum "+shlex.quote(args.board_binary)],text=True).split()[0]
        assert board_digest == digest(ROOT/"firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release/numeric-fixture")
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary)/"input.private.txt"
            source.write_text(line)
            source.chmod(0o600)
            try:
                subprocess.run(adb+["push",str(source),remote],check=True,capture_output=True)
                board = subprocess.run(adb+["shell",shlex.quote(args.board_binary)+" < "+remote],
                                       check=True,text=True,capture_output=True)
                assert json.loads(board.stdout) == actual, "Host and physical ARM replay differ"
            finally:
                subprocess.run(adb+["shell","rm -f "+remote],check=True,capture_output=True)
    assert digest(BINARY) == "ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9"
    assert digest(RUNTIME) == "421df6d09247848a7f733d25ef45b726bc6366c8fc12be84751f6b408c1d92cd"
    arm = OriginalStability()
    history = [[0]*4 for _ in range(8)]
    summaries = []
    index = 0
    native_calls = 0
    for stage, (_,records,cycles,_) in enumerate(stages):
        rows = actual["frames"][index:index+cycles*len(records)]
        for row in rows:
            raw = records[row["record"]]
            if row["continuation"] == "Ready":
                context = bytearray(0x3700)
                cfg, meta, stat = HEAP+0x10000, HEAP+0x20000, HEAP+0x30000
                struct.pack_into("<I", context, 0x8C, cfg)
                struct.pack_into("<I", context, 0x2DEC, meta)
                context[0x334A] = row["preparationRequested"]
                struct.pack_into("<32I", context, 0x334C, *sum(history, []))
                arm.uc.mem_write(HEAP,bytes(context))
                arm.uc.mem_write(cfg,bytes(0x500))
                arm.uc.mem_write(cfg+0x398,struct.pack("<i",2))
                arm.uc.mem_write(cfg+0x4B0,struct.pack("<f",row["stabilityThreshold"]))
                arm.uc.mem_write(meta,bytes(0x80))
                arm.uc.mem_write(meta+8,raw[0x1D78:0x1D7C])
                arm.uc.mem_write(stat,bytes(8)+raw[0x1DE8:0x1E00])
                arm.invoke(SYMBOL,[HEAP,stat])
                native_calls += 1
                after=bytes(arm.uc.mem_read(HEAP,0x3700))
                history=[list(struct.unpack_from("<4I",after,0x334C+i*16)) for i in range(8)]
                assert after[0x3348]==row["stabilityMask"] and bool(after[0x334A])==row["updateAfterGate"]
                assert history[:4]==row["historyBits"], (stage,index,row)
            index += 1
        summaries.append({"name":stages[stage][0],"frames":len(rows),
                          "calculations":sum(row["calculated"] for row in rows),
                          "tailCalculations":sum(row["calculated"] for row in rows[-16:]),
                          "firstGain":rows[0]["gain"],"lastGain":rows[-1]["gain"]})
    assert summaries[0]["tailCalculations"]==0, "Baseline did not settle"
    assert summaries[1]["calculations"]>0, "Color change did not wake the controller"
    assert max(abs(a-b) for a,b in zip(summaries[0]["lastGain"],summaries[1]["lastGain"]))>.02
    assert summaries[2]["calculations"]>0, "Restoration did not wake the controller"
    base_gain,shift_gain,restored_gain=(summaries[i]["lastGain"] for i in range(3))
    shift_distance=max(abs(a-b) for a,b in zip(base_gain,shift_gain))
    restored_distance=max(abs(a-b) for a,b in zip(base_gain,restored_gain))
    assert shift_gain[0]>base_gain[0] and shift_gain[3]<base_gain[3], "Wrong color correction direction"
    assert restored_distance<shift_distance/2, "Restored input did not recover toward baseline"
    assert all(stage["tailCalculations"]==0 for stage in summaries), "A stage did not settle"
    assert summaries[3]["calculations"]>0, "Brightness change did not wake the controller"
    report={"kind":"controlled-captured-statistics-awb-scene-change-replay","passed":True,
            "frames":len(actual["frames"]),"hostMatchesPhysicalArm":bool(args.adb),
            "version":tomllib.loads((ROOT/"firmware/rkaiq-rs/Cargo.toml").read_text())["package"]["version"],
            "rustHostSha256":digest(ROOT/"firmware/rkaiq-rs/target/release/numeric-fixture"),"rustArmSha256":board_digest,
            "nativeStabilityMismatches":0,"nativeStabilityCalls":native_calls,"nativeBinarySha256":digest(BINARY),
            "captureHashes":[digest(args.samples/("group-{}.translated.bin".format(i))) for i in range(2)],
            "stages":summaries,"hardwareWrites":False,"forcedStageUpdates":False,
            "limitations":["Measured input pairs were explicitly transformed; no physical scene/color change is claimed.",
                           "Original ARM equivalence covers the persistent stability gate, not the entire joined native controller.",
                           "Brightness and ISO are fixed controlled replay inputs except the declared brightness step."]}
    args.report.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


if __name__ == "__main__":
    main()
