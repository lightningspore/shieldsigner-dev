#!/usr/bin/env python3
"""Original gain-mode incomplete-measurement entry through its full common tail."""

import hashlib
import importlib.util
import json
import random
import struct
import subprocess
import sys

from awb_reference import OriginalAwb
from differential import BINARY, HEAP, ROOT, f32, regs

spec = importlib.util.spec_from_file_location(
    "awb_adjust_reference", __file__.replace("awb-postprocess.py", "awb-gain-adjust.py")
)
adjust = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adjust)


class Original(OriginalAwb):
    def hook(self, uc, address, size, user):
        if address == (self.symbols.get("xcam_print_log", 0) & ~1):
            uc.reg_write(regs.UC_ARM_REG_PC, uc.reg_read(regs.UC_ARM_REG_LR))
            return
        name = self.stubs.get(address)
        if name in ("malloc", "free"):
            value = uc.reg_read(regs.UC_ARM_REG_R0)
            if name == "malloc":
                assert 0 < value <= 1020
                pointer = self.arena
                self.arena += (value + 15) & ~15
                self.live.add(pointer)
                uc.mem_write(pointer, bytes([0xA7]) * value)
                uc.reg_write(regs.UC_ARM_REG_R0, pointer)
            else:
                assert value in self.live
                self.live.remove(value)
            uc.reg_write(regs.UC_ARM_REG_PC, uc.reg_read(regs.UC_ARM_REG_LR))
            return
        super().hook(uc, address, size, user)

    def run(self, v):
        n = len(v["lights"])
        context = bytearray([0x5A]) * 0x4000
        config = bytearray(0x800)
        calibration = bytearray(0x800)
        results = bytearray([0x6B]) * (n * 0xA0)
        clip_knots = v.get("clip_knots", [2000.0, 5000.0, 8000.0])
        clip_lower = v.get("clip_lower", [0.2] * 3)
        clip_upper = v.get("clip_upper", [0.2] * 3)
        curves = struct.pack(
            "<" + "f" * (len(clip_knots) * 3), *clip_knots, *clip_upper, *clip_lower
        )
        table = adjust.encode(v["lut"])
        for offset, pointer in [(0x8C, 0x8000), (0x80, 0x9000), (0x33E4, 0x20000)]:
            struct.pack_into("<I", context, offset, HEAP + pointer)
        context[0x13C] = 0
        context[0x348C] = v["clipped"]
        struct.pack_into("<I", context, 0x33D8, v["brightness"])
        struct.pack_into("<f", context, 0x33DC, v.get("sample", 0.0))
        struct.pack_into("<f", context, 0x58, v.get("iso", 100.0))
        struct.pack_into("<f", context, 0x33B4, v["tolerance"])
        for offset in [0x334C, 0x353C]:
            struct.pack_into("<4f", context, offset, *v["candidate"])
        struct.pack_into("<4f", context, 0x352C, *v["previous"])
        struct.pack_into("<2f", context, 0x3484, v["coefficient"], 0.9)
        for offset, value in [
            (0x34A4, 2.0),
            (0x34B4, 3.0),
            (0x34D4, 4.0),
            (0x34E4, 5.0),
            (0x350C, 6.0),
            (0x351C, 7.0),
        ]:
            struct.pack_into("<4f", context, offset, *([value] * 4))
        struct.pack_into("<2f", context, 0x34F8, 12.0, 13.0)
        struct.pack_into("<2f", context, 0x3504, 14.0, 15.0)
        config[0x138], config[0x1E8] = n, v["target"]
        config[0x122], config[0x123], config[0x124] = (
            v.get("bounds_enabled", v["clip"]),
            v["clip"] and v["daylight"],
            v["offset_enabled"],
        )
        struct.pack_into("<4f", config, 0x128, *v["offsets"])
        struct.pack_into("<I", config, 0x1D4, v.get("daylight_threshold", 100))
        for offset, value in [
            (0x340, v["damped_convergence"]),
            (0x344, v["history_convergence"]),
            (0x4AC, v["damping_threshold"]),
        ]:
            struct.pack_into("<f", config, offset, value)
        struct.pack_into(
            "<f4I",
            config,
            0x36C,
            v.get("daylight_minimum", 5000.0),
            len(clip_knots),
            HEAP + 0x12000,
            HEAP + 0x12000 + 4 * len(clip_knots),
            HEAP + 0x12000 + 8 * len(clip_knots),
        )
        for offset, line in [(0x348, v["first"]), (0x358, v["second"])]:
            struct.pack_into("<3fI", config, offset, *line[:3], line[3])
        calibration[0x538] = v["adjust"]
        struct.pack_into(
            "<4I",
            calibration,
            0x53C,
            v.get("sample_selector", 1),
            v.get("temperature_mode", True),
            HEAP + 0x10000,
            1,
        )
        for i, light in enumerate(v["lights"]):
            struct.pack_into(
                "<4ff", results, i * 0xA0 + 0x64, *light["gain"], light["probability"]
            )
        for key, offset, address in [
            ("raw_history", 0x3498, HEAP + 0x30000),
            ("output_history", 0x3490, HEAP + 0x31000),
        ]:
            values = v[key]
            head = HEAP + offset
            nodes = [address + i * 32 for i in range(len(values))]
            struct.pack_into(
                "<II",
                context,
                offset,
                nodes[0] if nodes else head,
                nodes[-1] if nodes else head,
            )
            for i, gain in enumerate(values):
                self.uc.mem_write(
                    nodes[i],
                    struct.pack(
                        "<II4f",
                        nodes[i + 1] if i + 1 < len(nodes) else head,
                        nodes[i - 1] if i else head,
                        *gain,
                    ),
                )
        extra = (
            self.setup_controller(v, context, config, calibration, results)
            if "controller" in v
            else []
        )
        if "outer" in v.get("controller", {}):
            self.setup_outer(v, context, config)
        if "scene_iq" in v.get("controller", {}):
            self.setup_scene(v, context, config, calibration, extra)
        blocks = [
            (0, context),
            (0x8000, config),
            (0x9000, calibration),
            (0x10000, table),
            (0x12000, curves),
            (0x20000, results),
        ] + extra
        for offset, data in blocks:
            self.uc.mem_write(HEAP + offset, bytes(data))
        self.arena, self.live = HEAP + 0x50000, set()
        self.invoke(
            (
                "gain-frame-continuation"
                if "dispatch" in v.get("controller", {})
                else "_Z13AwbCalAwbGainP12awb_contex_s"
                if "outer" in v.get("controller", {})
                else "_Z18AwbCalGainByWbModeP12awb_contex_s"
            ),
            [HEAP],
            instructions=3000000,
        )
        after = bytearray(self.uc.mem_read(HEAP, len(context)))
        output = {
            name: list(struct.unpack_from("<4I", after, offset))
            for name, offset in [
                ("current", 0x353C),
                ("previous", 0x352C),
                ("raw", 0x34A4),
                ("clipped_gain", 0x34B4),
                ("adjust_before", 0x34D4),
                ("adjust_after", 0x34E4),
                ("offset_gain", 0x350C),
                ("damped", 0x351C),
            ]
        }
        output.update(
            coordinates_before=list(struct.unpack_from("<2I", after, 0x34F8)),
            coordinates_after=list(struct.unpack_from("<2I", after, 0x3504)),
            coefficient=struct.unpack_from("<I", after, 0x3484)[0],
            effective=struct.unpack_from("<I", after, 0x3488)[0],
            clipped=bool(after[0x348C]),
            updated=bool(after[0x34A0]),
            converged=bool(after[0x3694]),
            damping_stable=bool(after[0x3346]),
        )
        temperature = lambda at: dict(
            valid=bool(after[at]),
            cct=struct.unpack_from("<I", after, at + 4)[0],
            ccri=struct.unpack_from("<I", after, at + 8)[0],
        )
        output["temperature"] = temperature(0x3658)
        output["top"] = [temperature(0x3664 + 12 * i) for i in range(4)]
        for i in range(5):
            at = 0x3658 + i * 12
            assert after[at + 1 : at + 4] == context[at + 1 : at + 4]
        word = lambda address: struct.unpack("<I", self.uc.mem_read(address, 4))[0]
        for key, offset in [("raw_history", 0x3498), ("output_history", 0x3490)]:
            values = []
            head = HEAP + offset
            node, previous = word(head), head
            while node != head:
                assert len(values) < 32 and word(node + 4) == previous
                values.append(
                    list(struct.unpack("<4I", self.uc.mem_read(node + 8, 16)))
                )
                previous, node = node, word(node)
            assert word(head + 4) == previous
            output[key] = values
        extra_nodes = self.read_controller(v, after, output) if "controller" in v else 0
        assert (
            len(self.live)
            == sum(
                len(output[k]) - len(v[k]) for k in ["raw_history", "output_history"]
            )
            + extra_nodes
        )
        for offset, size in [
            (0x33CC, 4),
            (0x34A4, 16),
            (0x34A0, 1),
            (0x3694, 1),
            (0x3346, 1),
            (0x348C, 1),
            (0x353C, 16),
            (0x3484, 8),
            (0x351C, 16),
            (0x3490, 16),
            (0x34B4, 16),
            (0x34D4, 16),
            (0x34E4, 16),
            (0x34F4, 24),
            (0x350C, 16),
            (0x3658, 60),
        ]:
            after[offset : offset + size] = context[offset : offset + size]
        assert after == context, (
            "Unexpected common-tail context write",
            [(hex(i), a, b) for i, (a, b) in enumerate(zip(after, context)) if a != b][
                :24
            ],
        )
        for offset, data in blocks[1:]:
            actual = bytes(self.uc.mem_read(HEAP + offset, len(data)))
            if offset == 0x20000 and "controller" in v:
                actual = self.read_controller_lights(actual, data, output)
            if offset == 0x8000 and "dispatch" in v.get("controller", {}):
                actual = bytearray(actual)
                actual[0x4B4:0x4B8] = data[0x4B4:0x4B8]
            assert actual == data
        return output


def main():
    manifest = json.loads(
        (ROOT / "reverse-engineering/rkaiq/artifacts.json").read_text()
    )
    sha = hashlib.sha256(BINARY.read_bytes()).hexdigest()
    assert sha == next(
        v["sha256"] for v in manifest["binaries"] if v["name"] == BINARY.name
    )
    arm = Original()
    rng = random.Random(0x504F5354)
    cases, expected = [], []
    for i in range(256):
        gain = lambda: [
            f32(rng.uniform(0.5, 4.0)),
            1.0,
            1.0,
            f32(rng.uniform(0.5, 4.0)),
        ]
        candidate = [1.0] * 4 if i % 5 == 0 else gain()
        v = dict(
            candidate=candidate,
            previous=[0.0] * 4 if i % 11 == 0 else gain(),
            coefficient=f32([0.0, 0.5, 0.9, 1.0][i % 4]),
            raw_history=[[1.0] * 4 for _ in range(i % 7)],
            output_history=[gain() for _ in range(i % 5)],
            target=[0, 1, 2, 4, 8][i % 5],
            tolerance=[0.0, 0.01, 0.1, 1.0][i // 5 % 4],
            history_convergence=[0.0, 0.01, 0.1, 1.0][i // 7 % 4],
            damped_convergence=[0.0, 0.01, 0.1, 10.0][i // 11 % 4],
            damping_threshold=[0.0, 0.01, 0.1, 10.0][i // 13 % 4],
            clip=bool(i % 2),
            adjust=bool(i // 2 % 2),
            offset_enabled=bool(i // 4 % 2),
            offsets=[f32(rng.uniform(-2, 2)) for _ in range(4)],
            clipped=bool(i // 8 % 2),
            daylight=bool(i // 16 % 2),
            brightness=[100, 101][i // 32 % 2],
            first=[-0.8, -0.6, -2.4, i % 13 != 0],
            second=[1.0, -0.0002, 0.5, i % 17 != 0],
            lights=[],
        )
        x = [1000.0 + 1000 * j for j in range(9)]
        y = [-1.0 + 0.2 * j for j in range(11)]
        v["lut"] = dict(
            sample=0.0,
            x=x,
            y=y,
            mapped_x=[f32(xx + 20.0) for yy in y for xx in x],
            mapped_y=[f32(yy + 0.01) for yy in y for xx in x],
        )
        for j in range(255 if i % 127 == 0 else 4 + i % 5):
            light = dict(gain=gain(), probability=f32(rng.choice([0.0, 0.1, 0.5, 1.0])))
            if i % 19 == 0:
                light["gain"][1] = 0.0
            v["lights"].append(light)
        cases.append(v)
        expected.append(arm.run(v))
    assert set(arm.calls) <= {"memcpy"} and not arm.runtime.calls
    inputs = "".join(
        "awb-postprocess " + json.dumps(v, separators=(",", ":")) + "\n" for v in cases
    )

    def compare(command):
        p = subprocess.run(command, input=inputs, text=True, capture_output=True)
        assert p.returncode == 0, (len(p.stdout.splitlines()), p.stderr)
        actual = [json.loads(line) for line in p.stdout.splitlines()]
        assert len(actual) == len(expected)
        for i, (a, b) in enumerate(zip(expected, actual)):
            assert a == b, (i, a, b)

    compare([str(ROOT / "firmware/rkaiq-rs/target/release/numeric-fixture")])
    replay = "--arm" in sys.argv
    if replay:
        directory = (
            ROOT / "firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release"
        )
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
                f"type=bind,src={directory},dst=/bincheck,readonly",
                "alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd",
                "/bincheck/numeric-fixture",
            ]
        )
    report = dict(
        binarySha256=sha,
        cases=len(cases),
        mismatches=0,
        arm=replay,
        elfEntry="0xc72b8",
        scope="Original gain-mode function using incomplete-measurement fallback followed by full common history/clip/adjust/offset/damping/convergence/metadata tail, through normal return",
        limitations=[
            "Strategy result is explicit and normalized by the original incomplete-measurement prefix; complete-measurement high/low strategy composition is separate.",
            "Finite checked inputs, 4-255 metadata lights, bounded histories. Native fewer-than-four metadata indexing is excluded.",
            "Standard allocation/memory/logging are adapters; all policy/numerical/sort/CCT bodies execute.",
            "Undefined adjustment validity cache words are excluded, with defined coordinate values compared.",
            "Calibration initialization, full outer lifecycle and live AWB integration remain unfinished.",
        ],
    )
    (ROOT / "reverse-engineering/rkaiq/awb-postprocess-equivalence.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
