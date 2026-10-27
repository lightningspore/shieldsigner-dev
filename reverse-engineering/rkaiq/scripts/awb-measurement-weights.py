#!/usr/bin/env python3
"""Compare full original AWB luma-weight reconfiguration including damping."""

import hashlib
import json
import random
import struct
import subprocess
import sys
from differential import OriginalArm, ROOT, BINARY, HEAP, regs


class Original(OriginalArm):
    def hook(self, uc, address, size, user):
        name = self.stubs.get(address)
        a, b, c = [
            uc.reg_read(r)
            for r in (regs.UC_ARM_REG_R0, regs.UC_ARM_REG_R1, regs.UC_ARM_REG_R2)
        ]
        if name == "malloc":
            assert a < 65536
            pointer = self.next
            self.next += (a + 15) & ~15
            uc.mem_write(pointer, bytes(a))
            uc.reg_write(regs.UC_ARM_REG_R0, pointer)
        elif name == "free":
            pass
        elif name == "memcmp":
            first = bytes(uc.mem_read(a, c))
            second = bytes(uc.mem_read(b, c))
            value = (first > second) - (first < second)
            uc.reg_write(regs.UC_ARM_REG_R0, value & 0xFFFFFFFF)
        else:
            return super().hook(uc, address, size, user)
        uc.reg_write(regs.UC_ARM_REG_PC, uc.reg_read(regs.UC_ARM_REG_LR))

    def run(self, v):
        context = bytearray(0x3700)
        record = bytearray([0xA5]) * 1204
        record[0x2E:0x30] = bytes(v["enable"])
        context[0x2E90 : 0x2E90 + 1204] = record
        struct.pack_into("<I", context, 0x80, HEAP + 0x10000)
        struct.pack_into("<I", context, 0x130, HEAP + 0x20000)
        struct.pack_into("<I", context, 0x8C, HEAP + 0x30000)
        struct.pack_into("<I", context, 0x33AC, v["frame"])
        struct.pack_into("<I", context, 0x33D8, v["brightness"])
        struct.pack_into("<f", context, 0x3484, v["damping"])
        struct.pack_into("<8i", context, 0x2D44, *v["histogram"])
        iq = bytearray(0x300)
        iq[0x265:0x26D] = bytes(v["perfect"])
        struct.pack_into("<I", iq, 0x258, v["minimum_brightness"])
        struct.pack_into("<II", iq, 0x270, HEAP + 0x40000, len(v["rows"]))
        cal = bytearray(0x400)
        struct.pack_into("<9f", cal, 0x298, *v["previous"])
        algorithm = bytearray(0x600)
        struct.pack_into("<f", algorithm, 0x49C, v["minimum_count"])
        tables = bytearray(len(v["rows"]) * 12)
        for i, row in enumerate(v["rows"]):
            pointer = HEAP + 0x41000 + i * 0x1000
            struct.pack_into(
                "<fII", tables, i * 12, row["brightness"], pointer, len(row["ratios"])
            )
            data = b"".join(
                struct.pack("<10f", ratio, *weights)
                for ratio, weights in zip(row["ratios"], row["weights"])
            )
            self.uc.mem_write(pointer, data)
        for offset, data in (
            (0, context),
            (0x10000, iq),
            (0x20000, cal),
            (0x30000, algorithm),
            (0x40000, tables),
        ):
            self.uc.mem_write(HEAP + offset, bytes(data))
        self.next = HEAP + 0x60000
        self.invoke(next(n for n in self.symbols if "ReconfigLumaWeight" in n), [HEAP])
        after = bytes(self.uc.mem_read(HEAP, len(context)))
        after_cal = bytes(self.uc.mem_read(HEAP + 0x20000, len(cal)))
        for start, end in ((0x31E1, 0x31EA), (0x31EC, 0x31F0), (0x3347, 0x3348)):
            context[start:end] = after[start:end]
        assert after == context
        cal[0x298:0x2BC] = after_cal[0x298:0x2BC]
        assert cal == after_cal
        return dict(
            reached=bool(after[0x3347]),
            cache=list(struct.unpack_from("<9I", after_cal, 0x298)),
            record=after[0x2E90 : 0x2E90 + 1204].hex(),
        )


def main():
    sha = hashlib.sha256(BINARY.read_bytes()).hexdigest()
    assert sha == "ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9"
    arm = Original(BINARY)
    rng = random.Random(0x41575754)
    cases = []
    expected = []
    for i in range(192):
        rows = []
        for j in range(1 + i % 4):
            ratios = [0.0, 0.1, 0.5, 1.0]
            if i % 7 == 0:
                ratios = [0.0, 0.1, 0.100001, 1.0]
            rows.append(
                dict(
                    brightness=j * 1000,
                    ratios=ratios,
                    weights=[[rng.random() for _ in range(9)] for _ in ratios],
                )
            )
        v = dict(
            frame=i % 8,
            brightness=[0, 500, 1000, 1500, 5000][i % 5],
            histogram=[(i + j) % 17 for j in range(8)],
            perfect=[bool(j % 2) for j in range(8)],
            minimum_count=0.0 if i % 6 else 10000.0,
            minimum_brightness=0 if i % 6 else 10000,
            damping=[0.0, 0.1, 0.5, 0.9, 1.0][i % 5],
            enable=[i % 4 != 0, i % 7 == 0],
            previous=[rng.uniform(0, 63) for _ in range(9)],
            rows=rows,
        )
        if i % 9 == 0:
            v["histogram"] = [0] * 8
            v["minimum_count"] = -1.0
        cases.append(v)
        expected.append(arm.run(v))
    iq = (
        ROOT / ".tools/reverse-engineering/iqfiles/sc3336_CMK-OT2119-PC1_30IRC-F16.json"
    )
    iq_sha = hashlib.sha256(iq.read_bytes()).hexdigest()
    assert iq_sha == "8c816c0f83c6d4d951d5d4335e9c63a0893cd4f99c501f3f3558bbbca9d2c94a"
    wb = json.loads(iq.read_text())["main_scene"][0]["sub_scene"][0]["scene_isp32"][
        "wb_v32"
    ]
    w = wb["autoPara"]["wpDiffLumaWeight"]
    for brightness in (0, 256, 4096, 8192, 16384):
        v = dict(
            frame=10,
            brightness=brightness,
            histogram=[10, 20, 30, 40, 50, 60, 70, 80],
            perfect=[bool(x) for x in w["perfectBin"]],
            minimum_count=0.0,
            minimum_brightness=w["wpDiffWeiEnableTh"]["wpDiffWeiLvValueTh"],
            damping=0.5,
            enable=[True, True],
            previous=[63.0] * 9,
            iq=wb,
            rows=[
                dict(
                    brightness=r["LvValue"],
                    ratios=[x["ratioValue"] for x in r["ratioSet"]],
                    weights=[x["weight"] for x in r["ratioSet"]],
                )
                for r in w["wpDiffWeightLvSet"]
            ],
        )
        cases.append(v)
        expected.append(arm.run(v))
    inputs = "".join(
        "awb-measurement-weights " + json.dumps(v, separators=(",", ":")) + "\n"
        for v in cases
    )

    def compare(command):
        actual = [
            json.loads(line)
            for line in subprocess.run(
                command, input=inputs, text=True, capture_output=True, check=True
            ).stdout.splitlines()
        ]
        assert len(actual) == len(expected)
        for i, (a, b) in enumerate(zip(actual, expected)):
            assert a == b, (
                i,
                a["reached"],
                b["reached"],
                a["cache"],
                b["cache"],
                next(
                    (
                        j // 2
                        for j, (x, y) in enumerate(zip(a["record"], b["record"]))
                        if x != y
                    ),
                    None,
                ),
            )

    compare([str(ROOT / "firmware/rkaiq-rs/target/release/numeric-fixture")])
    if "--arm" in sys.argv:
        d = ROOT / "firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release"
        compare(
            [
                "docker",
                "run",
                "--rm",
                "-i",
                "--platform",
                "linux/arm/v7",
                "--network=none",
                "--mount",
                f"type=bind,src={d},dst=/bincheck,readonly",
                "alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd",
                "/bincheck/numeric-fixture",
            ]
        )
    report = dict(
        binarySha256=sha,
        cases=len(cases),
        iqLoaderCases=5,
        iqSha256=iq_sha,
        mismatches=0,
        arm="--arm" in sys.argv,
        scope="Complete original ReconfigLumaWeight return, interpolation, CalWeight FMA damping, record/cache preservation",
        limitations=[
            "Allocation, memory copy/compare and free are explicit adapters; numerical native bodies execute.",
            "Histogram and runtime gating inputs are explicit; outer measurement reconfiguration remains separate.",
        ],
    )
    (
        ROOT / "reverse-engineering/rkaiq/awb-measurement-weights-equivalence.json"
    ).write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
