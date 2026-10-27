#!/usr/bin/env python3
"""Complete native gain-mode composition, optionally with joined single-color."""

import hashlib
import importlib.util
import json
import random
import struct
import subprocess
import sys
from differential import BINARY, HEAP, ROOT, f32
from awb_reference import RUNTIME

spec = importlib.util.spec_from_file_location(
    "awb_post_reference",
    __file__.replace("awb-gain-controller.py", "awb-postprocess.py"),
)
post = importlib.util.module_from_spec(spec)
spec.loader.exec_module(post)
spec_color = importlib.util.spec_from_file_location(
    "awb_color_reference", __file__.replace("awb-gain-controller.py", "awb-color.py")
)
color = importlib.util.module_from_spec(spec_color)
spec_color.loader.exec_module(color)
PROCESS = "_Z22AwbSingleColorProcess226rk_aiq_awb_stat_res_full_sP19CalibDbV2_Awb_Sgc_s6line_sS2_P12sgc_result_sP9list_headPfS7_"


class Original(post.Original, color.OriginalColor):
    def __init__(self):
        super().__init__()
        self.stdlib = True

    def hook(self, uc, address, size, user):
        if address == (self.symbols.get(PROCESS, 0) & ~1):
            self.single_calls += 1
        if address == (
            self.symbols.get("_Z29AwbCalGainForDiffIlluminationiP12awb_contex_s", 0)
            & ~1
        ):
            self.selected_gain_calls += 1
        super().hook(uc, address, size, user)

    def setup_controller(self, v, ctx, cfg, cal, results):
        s = v["controller"]
        n = len(s["lights"])

        def word(data, o, value):
            struct.pack_into("<I", data, o, value & 0xFFFFFFFF)

        ctx[0x13C] = s["complete"]
        ctx[0x33FC] = s["previous_region"]
        ctx[0x33FE] = 255
        ctx[0x3418] = 1
        ctx[0x3419] = s["used_previous"]
        ctx[0xF79] = 0
        for o, value in [
            (0x134, HEAP + 0x61000),
            (0x2DEC, HEAP + 0x66000),
            (0x33BC, 10),
            (0x33C0, 20),
            (0x33C8, 42),
            (0x33D0, 2),
            (0x33AC, s["frame"]),
            (0x2D10, s["exclusion_count"]),
        ]:
            word(ctx, o, value)
        struct.pack_into("<4f", ctx, 0x2D14, 2.0, 1.0, 1.0, 3.0)
        struct.pack_into("<f", ctx, 0x33CC, 0.25)
        struct.pack_into("<f", ctx, 0x33DC, s["prior_sample"])
        struct.pack_into("<f", ctx, 0x3480, s["variance"])
        for o, value in [
            (0x341C, 13.0),
            (0x342C, 8.0),
            (0x3440, 9.0),
            (0x3464, 10.0),
            (0x33E8, 11.0),
            (0x3450, 12.0),
        ]:
            struct.pack_into("<4f", ctx, o, *([value] * 4))
        for o, value in [(0x343C, 0.5), (0x33F8, 0.75), (0x3474, 0.25), (0x3460, 0.75)]:
            struct.pack_into("<f", ctx, o, value)
        struct.pack_into("<4f", ctx, 0x35A8, *s["estimated"])
        cfg[0x380] = s["stabilization"]
        word(cfg, 0x384, s["xy_target"])
        struct.pack_into("<f2f", cfg, 0x388, 0.5, *s["region_thresholds"])
        struct.pack_into("<2I", cfg, 0x1B8, *s["count_thresholds"])
        struct.pack_into("<2f", cfg, 0x1F0, s["absolute"], s["relative"])
        struct.pack_into("<2f", cfg, 0x1C0, 0.01, 2.0)
        struct.pack_into("<4I", cfg, 0x1C8, 100, 200, 400, 800)
        struct.pack_into("<16I", cfg, 0x168, *[100 * i for i in range(16)])
        struct.pack_into("<I", cfg, 0x1A8, 100)
        word(cfg, 0x1B4, 200)
        struct.pack_into("<4f", cfg, 0x1D8, 2.0, 1.0, 1.0, 3.0)
        cfg[0x1F8:0x208] = bytes((i % 6) * 20 for i in range(16))
        word(cfg, 0x368, HEAP + 0x60000)
        cal[0x644] = 0
        struct.pack_into("<i", cal, 0x648, s["mode"])
        struct.pack_into("<iH", cal, 0x658, 2, s["color_target"])
        struct.pack_into(
            "<3f", cal, 0x778, s["estimated_threshold"], 0.5, s["high_threshold"]
        )
        word(cal, 0x43C, HEAP + 0x62000)
        reference = bytearray(n * 0xE4)
        stats = bytearray(n * 0xAC)
        priors = bytearray(n * 0xFC)
        curves = bytearray(n * 0x100)
        for i, l in enumerate(s["lights"]):
            struct.pack_into("<i", reference, i * 0xE4 + 0x64, l["kind"])
            struct.pack_into("<4f", reference, i * 0xE4 + 0x80, *l["reference"])
            struct.pack_into("<II", reference, i * 0xE4 + 0x78, 200, 100)
            struct.pack_into("<4f", reference, i * 0xE4 + 0x90, 3.0, 1.0, 1.0, 2.0)
            struct.pack_into("<4f", reference, i * 0xE4 + 0xA0, 2.0, 1.0, 1.0, 4.0)
            reference[i * 0xE4 + 0x68] = l["percentage"]
            reference[i * 0xE4 + 0xB0] = l["extra"]
            word(ctx, 0x33E0, 0)
            for region in range(3):
                struct.pack_into(
                    "<I4f",
                    stats,
                    i * 0xAC + region * 0x34,
                    l["counts"][region],
                    *l["gains"][region],
                )
            struct.pack_into(
                "<III",
                priors,
                i * 0xFC + 0xEC,
                HEAP + 0x64000 + i * 0x100,
                4,
                HEAP + 0x64040 + i * 0x100,
            )
            struct.pack_into("<4f", curves, i * 0x100, 0.0, 1.0, 2.0, 3.0)
            struct.pack_into("<4f", curves, i * 0x100 + 0x40, *l["prior"])
            for o, x in [
                (0x78, 0.5),
                (0x7C, 0.75),
                (0x80, 1.0),
                (0x94, 1.25),
                (0x98, 0.25),
                (0x9C, 0.75),
            ]:
                struct.pack_into("<f", results, i * 0xA0 + o, x)
            struct.pack_into("<4f", results, i * 0xA0 + 0x84, *([14.0] * 4))
        mode = bytearray(0x100)
        text = b"FASTAWBACT\0" if s["fast"] else b"NORMAL\0"
        mode[0x1C : 0x1C + len(text)] = text
        self.initial_extra = 0
        for key, o, address, gain in [
            ("xy_history", 0x355C, 0x32000, False),
            ("color_history", 0x35A0, 0x33000, False),
            ("high_history", 0x3598, 0x34000, True),
        ]:
            values = s[key]
            head = HEAP + o
            nodes = [HEAP + address + i * 32 for i in range(len(values))]
            word(ctx, o, nodes[0] if nodes else head)
            word(ctx, o + 4, nodes[-1] if nodes else head)
            self.initial_extra += len(values)
            for i, value in enumerate(values):
                links = [
                    nodes[i + 1] if i + 1 < len(nodes) else head,
                    nodes[i - 1] if i else head,
                ]
                self.uc.mem_write(
                    nodes[i],
                    struct.pack("<II4f", *links, *value)
                    if gain
                    else struct.pack("<III", *links, value),
                )
        extra = [
            (0x60000, reference),
            (0x61000, stats),
            (0x62000, priors),
            (0x64000, curves),
            (0x66000, mode),
        ]
        if "single" in s:
            extra += self.setup_single(v, ctx, cal)
        return extra

    def setup_single(self, v, ctx, cal):
        s = v["controller"]["single"]
        ctx[0xF79] = s["grid_valid"]
        struct.pack_into("<675f", ctx, 0xF7C, *(x for rgb in s["grid"] for x in rgb))
        base = 0x644
        cal[base] = 1
        struct.pack_into(
            "<IIIIH",
            cal,
            base + 8,
            HEAP + 0x68000,
            len(s["colors"]),
            HEAP + 0x69000,
            len(s["candidates"]),
            v["controller"]["color_target"],
        )
        struct.pack_into("<f", cal, base + 0x1C, s["alpha"])
        struct.pack_into("<i", cal, base + 0x12C, -1)
        struct.pack_into("<f", cal, 0x774, s["threshold"])
        c = s["confidence"]
        for key, o in [
            ("brightness_knots", 0xBC),
            ("brightness_weights", 0xDC),
            ("density_knots", 0xFC),
            ("density_weights", 0x114),
            ("distance_knots", 0x50),
            ("cct_knots", 0x68),
            ("disagreement_knots", 0x20),
            ("disagreement_weights", 0x38),
        ]:
            struct.pack_into("<" + "f" * len(c[key]), cal, base + o, *c[key])
        for i, values in enumerate(c["distance_weights"]):
            struct.pack_into("<6f", cal, base + 0x74 + 24 * i, *values)
        colors = bytearray(36 * len(s["colors"]))
        for i, v in enumerate(s["colors"]):
            struct.pack_into(
                "<I8f",
                colors,
                i * 36,
                i,
                v["chroma"],
                v["hue"],
                *v["knots"],
                *v["thresholds"],
            )
        candidates = bytearray(28 * len(s["candidates"]))
        for i, values in enumerate(s["candidates"]):
            struct.pack_into("<2f", candidates, i * 28 + 20, *values)
        return [(0x68000, colors), (0x69000, candidates)]

    def read_controller(self, v, after, output):
        result = dict(
            selected=after[0x33FC],
            selection_status=after[0x33FE],
            strategy_flag=bool(after[0x3418]),
            retained=struct.unpack_from("<I", after, 0x33C8)[0],
            kind=struct.unpack_from("<I", after, 0x33D0)[0],
            used_previous=bool(after[0x3419]),
        )
        for key, o in [
            ("density", 0x33CC),
            ("high_low_weight", 0x343C),
            ("temporal_weight", 0x33F8),
            ("spatial_weight", 0x3474),
            ("single_weight", 0x3460),
        ]:
            result[key] = struct.unpack_from("<I", after, o)[0]
        for key, o in [
            ("high_gain", 0x341C),
            ("low_result", 0x342C),
            ("temporal_result", 0x3440),
            ("spatial_result", 0x3464),
            ("temporal_source", 0x33E8),
            ("estimated", 0x35A8),
        ]:
            result[key] = list(struct.unpack_from("<4I", after, o))
        word = lambda p: struct.unpack("<I", self.uc.mem_read(p, 4))[0]
        count = 0
        for key, o, gain in [
            ("xy_history", 0x355C, False),
            ("color_history", 0x35A0, False),
            ("high_history", 0x3598, True),
        ]:
            values = []
            head = HEAP + o
            node = word(head)
            previous = head
            while node != head:
                assert len(values) < 32 and word(node + 4) == previous
                values.append(
                    list(struct.unpack("<4I", self.uc.mem_read(node + 8, 16)))
                    if gain
                    else word(node + 8)
                )
                previous, node = node, word(node)
            assert word(head + 4) == previous
            count += len(values)
            result[key] = values
        output["controller"] = result
        if "single" in v["controller"]:
            base = 0x35B8
            result["single"] = dict(
                selected=struct.unpack_from("<i", after, base + 4)[0],
                color=struct.unpack_from("<i", after, base + 8)[0],
                candidate_counts=list(struct.unpack_from("<14i", after, base + 0xC)),
                color_counts=list(struct.unpack_from("<14i", after, base + 0x44)),
                valid=bool(struct.unpack_from("<I", after, base + 0x7C)[0]),
                disagreements=struct.unpack_from("<i", after, base + 0x80)[0],
                votes=struct.unpack_from("<i", after, base + 0x84)[0],
                mean=struct.unpack_from("<I", after, base + 0x88)[0],
                gain=list(struct.unpack_from("<4I", after, 0x3450)),
            )
            before = self.before_controller
            for o, size in [(0x3450, 20), (0x35BC, 0x88)]:
                after[o : o + size] = before[o : o + size]
        # Remove represented controller writes before the shared unrelated-byte check.
        before = self.before_controller
        for o, size in [
            (0x33C8, 12),
            (0x33E8, 20),
            (0x33FC, 1),
            (0x33FE, 1),
            (0x3418, 2),
            (0x341C, 0x2C),
            (0x3440, 16),
            (0x3464, 20),
            (0x355C, 8),
            (0x3598, 8),
            (0x35A0, 8),
            (0x35A8, 16),
        ]:
            after[o : o + size] = before[o : o + size]
        return count - self.initial_extra + 2 * self.single_calls

    def read_controller_lights(self, actual, before, output):
        after = bytearray(actual)
        lights = []
        for i in range(len(before) // 0xA0):
            lights.append(
                dict(
                    probability=[
                        struct.unpack_from("<I", after, i * 0xA0 + o)[0]
                        for o in [0x74, 0x78, 0x7C, 0x80, 0x94]
                    ],
                    statistic=list(struct.unpack_from("<4I", after, i * 0xA0 + 0x64)),
                    spatial=list(struct.unpack_from("<4I", after, i * 0xA0 + 0x84)),
                    spatial_weight=struct.unpack_from("<I", after, i * 0xA0 + 0x98)[0],
                    extra_weight=struct.unpack_from("<I", after, i * 0xA0 + 0x9C)[0],
                )
            )
            after[i * 0xA0 + 0x64 : i * 0xA0 + 0xA0] = before[
                i * 0xA0 + 0x64 : i * 0xA0 + 0xA0
            ]
        output["controller"]["lights"] = lights
        return bytes(after)

    def invoke(self, name, *args, **kwargs):
        if name == "_Z18AwbCalGainByWbModeP12awb_contex_s":
            self.single_calls = 0
            self.selected_gain_calls = 0
            self.before_controller = bytes(self.uc.mem_read(HEAP, 0x4000))
        return super().invoke(name, *args, **kwargs)


def main():
    manifest = json.loads(
        (ROOT / "reverse-engineering/rkaiq/artifacts.json").read_text()
    )
    sha = hashlib.sha256(BINARY.read_bytes()).hexdigest()
    runtime_sha = hashlib.sha256(RUNTIME.read_bytes()).hexdigest()
    assert sha == manifest["binaries"][0]["sha256"]
    assert runtime_sha == manifest["gccRuntime"]["memberSha256"]
    math_sha = hashlib.sha256(color.MATH.read_bytes()).hexdigest()
    assert math_sha == manifest["uclibcRuntime"]["memberSha256"]
    single = "--single" in sys.argv
    initial_exclusion = "--initial-exclusion" in sys.argv
    assert not (single and initial_exclusion)
    iq_sha = None
    if initial_exclusion:
        iq_file = (
            ROOT / ".tools/reverse-engineering/iqfiles" / manifest["iqFiles"][0]["name"]
        )
        iq_sha = hashlib.sha256(iq_file.read_bytes()).hexdigest()
        assert iq_sha == manifest["iqFiles"][0]["sha256"]

        def find_single(value):
            if isinstance(value, dict):
                if "singleColorProces" in value:
                    yield value
                for child in value.values():
                    yield from find_single(child)
            elif isinstance(value, list):
                for child in value:
                    yield from find_single(child)

        header = (ROOT / ".tools/reverse-engineering/headers/awb_head.h").read_bytes()
        header_sha = hashlib.sha256(header).hexdigest()
        assert header_sha == next(
            h["sha256"] for h in manifest["headers"] if h["name"] == "awb_head.h"
        )
        for name, value in [("INITIAL", 0), ("AUTO", 1), ("ALWAYS", 2)]:
            assert f"AWB_SGC_CALL_{name} = {value}".encode() in header
        iq_profiles = list(find_single(json.loads(iq_file.read_bytes())))
        assert iq_profiles
        assert all(
            p["singleColorProces"]["mode"] == "AWB_SGC_CALL_INITIAL"
            for p in iq_profiles
        )
        assert all(
            p["xyRegionStableSelection"]["wpNumTh"]["forBigType"] == [216]
            and p["xyRegionStableSelection"]["wpNumTh"]["forExtraType"] == [216]
            for p in iq_profiles
        )
    arm = Original()
    rng = random.Random(0x434F4E54)
    cases = []
    expected = []
    coverage = {}
    classifier_calls = 0
    single_coverage = {}
    for i in range(64 if single else 192):
        gain = lambda: [
            f32(rng.uniform(0.5, 4.0)),
            1.0,
            1.0,
            f32(rng.uniform(0.5, 4.0)),
        ]
        n = 4 + i % 5
        v = dict(
            candidate=gain(),
            previous=[0.0] * 4 if i % 11 == 0 else gain(),
            coefficient=[0.0, 0.5, 0.9, 1.0][i % 4],
            raw_history=[[1.0] * 4 for _ in range(i % 6)],
            output_history=[gain() for _ in range(i % 4)],
            target=[0, 1, 2, 4, 8][i % 5],
            tolerance=0.1,
            history_convergence=0.1,
            damped_convergence=0.1,
            damping_threshold=0.2,
            clip=False,
            adjust=False,
            offset_enabled=bool(i % 2),
            offsets=[0.1, -0.1, 0.1, -0.1],
            clipped=False,
            daylight=False,
            brightness=[50, 150, 250, 500][i // 3 % 4],
            first=[-0.8, -0.6, -2.4, i % 17 != 0],
            second=[1.0, -0.0002, 0.5, True],
            lights=[
                dict(gain=gain(), probability=f32(rng.choice([0.0, 0.1, 0.5, 1.0])))
                for _ in range(n)
            ],
        )
        x = [1000.0 + 1000 * j for j in range(9)]
        y = [-1.0 + 0.2 * j for j in range(11)]
        v["lut"] = dict(
            sample=0.0,
            x=x,
            y=y,
            mapped_x=[xx for yy in y for xx in x],
            mapped_y=[yy for yy in y for xx in x],
        )
        mode = i % 3
        previous = 3 if mode == 0 and i % 7 == 0 else i % 2
        s = dict(
            complete=i % 13 != 0,
            mode=mode,
            fast=bool(i // 3 % 2),
            frame=0 if i % 11 == 0 else i,
            prior_sample=f32(rng.uniform(0.0, 3.0)),
            absolute=10.0,
            relative=0.1,
            region_thresholds=[100.0, 50.0],
            count_thresholds=[100, 10],
            stabilization=bool(i % 2),
            xy_target=[0, 2, 4][i % 3],
            variance=float(i % 2),
            previous_region=previous,
            xy_history=[previous for _ in range(i % 4)],
            color_history=[rng.randrange(3) for _ in range(i % 4)],
            color_target=[0, 2, 4][i % 3],
            high_history=[gain() for _ in range(i % 3)],
            estimated=gain(),
            used_previous=bool(i % 2),
            exclusion_count=5 if mode == 0 else 0,
            high_threshold=[0.0, 50000.0, 100000.0][i % 3],
            estimated_threshold=[0.0, 20000.0, 100000.0][i // 3 % 3],
            lights=[],
        )
        for j in range(n):
            counts = [rng.choice([0, 1, 10, 100]) for _ in range(3)] + [0]
            if i % 19 == 0:
                counts[0] = counts[1] = 0
            s["lights"].append(
                dict(
                    counts=counts,
                    gains=[gain(), gain(), gain(), [0.0] * 4],
                    reference=gain(),
                    kind=[1, 2, 3, 4][j % 4],
                    prior=[f32(rng.uniform(0.0, 1.0)) for _ in range(4)],
                    extra=bool(j % 2),
                    percentage=[0, 50, 100, 255][j % 4],
                )
            )
        if single:
            v["raw_history"] = [] if i % 4 < 2 else [[1.0] * 4] * 2
            if i % 8 in (1, 2, 3, 4):
                v["brightness"] = 150
                v["raw_history"] = [] if i % 8 in (1, 2) else [[1.0] * 4] * 2
                for light in s["lights"]:
                    light["counts"] = [1, 1, 0, 0]
            if i % 8 == 4 or i % 16 == 3:
                s["estimated"][0] = 0.0
            s["color_history"] = [rng.randrange(3) for _ in range(i % 4)]
            c = dict(
                brightness_knots=[float(j) for j in range(8)],
                brightness_weights=[0.25 if i % 2 else 0.75] * 8,
                density_knots=[float(j) for j in range(6)],
                density_weights=[1.0] * 6,
                distance_knots=[float(j) for j in range(6)],
                distance_weights=[[1.0] * 6 for _ in range(3)],
                cct_knots=[1000.0, 5000.0, 9000.0],
                disagreement_knots=[float(j) for j in range(6)],
                disagreement_weights=[1.0] * 6,
            )
            s["single"] = dict(
                grid_valid=i % 7 != 0,
                grid=[
                    [0.2, 0.4, 0.6] if i % 3 else [0.6, 0.4, 0.2] for _ in range(225)
                ],
                candidates=[[1.0, 1.0], [2.0, 1.5], [1.5, 2.5]],
                colors=[
                    dict(
                        chroma=30.0,
                        hue=60.0,
                        knots=[1000.0, 5000.0, 9000.0],
                        thresholds=[-1.0 if i % 5 == 0 else 1000000.0] * 3,
                    )
                ],
                alpha=0.5,
                threshold=0.5,
                confidence=c,
            )
        if initial_exclusion:
            # Directed branch test: force the raw Exclusion proposal. Stability
            # is disabled here; this is not replay of a full IQ-initialized frame.
            s.update(
                mode=0,
                complete=True,
                exclusion_count=5,
                previous_region=3,
                stabilization=False,
                xy_target=0,
                region_thresholds=[216.0, 216.0],
            )
            for light in s["lights"]:
                light["counts"][0:2] = [0, 0]
        v["controller"] = s
        cases.append(v)
        expected.append(arm.run(v))
        if initial_exclusion:
            assert expected[-1]["controller"]["selected"] == 3
            assert arm.selected_gain_calls == 0 and arm.single_calls == 0
        classifier_calls += arm.single_calls
        if arm.single_calls:
            observed = expected[-1]["controller"]
            detail = f"mode{mode}:history{bool(v['raw_history'])}:valid{observed['single']['valid']}:weight{observed['single_weight']:08x}"
            single_coverage[detail] = single_coverage.get(detail, 0) + 1
        if single and (i + 1) % 8 == 0:
            print(
                f"Native joined single-color reference: {i + 1}/64",
                file=sys.stderr,
                flush=True,
            )
        key = f"{s['complete']}:{s['mode']}:{expected[-1]['controller']['selected']}"
        coverage[key] = coverage.get(key, 0) + 1
    assert (
        set(arm.calls) <= {"memcpy", "memset"}
        and not arm.runtime.calls
        and not arm.math.calls
    )
    if single:
        assert any(k.startswith("mode1:") for k in single_coverage)
        assert any(k.startswith("mode2:") for k in single_coverage)
        assert any(":validFalse:" in k for k in single_coverage)
        assert any(":validTrue:" in k for k in single_coverage)
    inputs = "".join(
        "awb-gain-controller " + json.dumps(v, separators=(",", ":")) + "\n"
        for v in cases
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
        iqSha256=iq_sha,
        initialExclusionAudit=initial_exclusion,
        enumHeaderSha256=header_sha if initial_exclusion else None,
        runtimeSha256=runtime_sha,
        mathRuntimeSha256=math_sha,
        nativeMathCalls=arm.math_calls,
        classifierCalls=classifier_calls,
        singleColorCoverage=single_coverage,
        nativeRuntimeFunctions=sorted(arm.runtime_functions),
        modeledStringCalls=arm.standard_calls,
        cases=len(cases),
        mismatches=0,
        arm=replay,
        coverage=coverage,
        elfEntry="0xc72b8",
        scope="Whole original gain-mode function: XY/probabilities/high/low/mix/retention plus common processing through ranked metadata",
        limitations=[
            "Directed INITIAL-mode Exclusion: stability disabled, sparse counts, no full IQ initialization."
            if initial_exclusion
            else "Single-color is enabled in this corpus."
            if single
            else "This joined corpus disables single-color; its enabled suite is separate.",
            "Optional clipping/adjustment are disabled; their full native suites remain separate.",
            "Ordinary joined XY regions are Normal/Big; Exclusion is exercised through mode-0 direct aggregate fallback.",
            "Finite explicit calibration and prepared measurements, 4-8 lights and bounded histories; calibration initialization and live frame lifecycle remain unfinished.",
            "Standard allocation, memory, strings and logging are explicit adapters; original numerical and policy bodies execute.",
        ],
    )
    (
        ROOT
        / (
            "reverse-engineering/rkaiq/awb-gain-controller-initial-exclusion-equivalence.json"
            if initial_exclusion
            else "reverse-engineering/rkaiq/awb-gain-controller-single-color-equivalence.json"
            if single
            else "reverse-engineering/rkaiq/awb-gain-controller-equivalence.json"
        )
    ).write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
