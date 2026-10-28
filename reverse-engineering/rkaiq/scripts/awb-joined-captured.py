#!/usr/bin/env python3
"""Diagnostic persistent native AWB replay of associated private group captures.

No hardware access. Numerical helpers, preparation and gain wrapper execute ARM.
Use --hardware-reference to compare native reconfiguration; otherwise it is an
explicit stop boundary. --trace-dir replays up to 32 captured frames once in
recorded order, with each frame's AE inputs and incoming update flag.
The inherited calibrated gain fixture supplies ABI layout; startup is adapted.
"""

import argparse
import hashlib
import importlib
import json
from pathlib import Path
import struct
import subprocess
import sys

from differential import BINARY, HEAP, RETURN, ROOT, OriginalArm, regs
from awb_reference import OriginalAwb

controller = importlib.import_module("awb-gain-controller")
preprocess = importlib.import_module("awb-preprocess")
SYMBOL = "_Z13AwbPreProcV32PK25rk_aiq_awb_stat_res_v32_sP12awb_contex_s"


class Ready(Exception):
    pass


def layout_case():
    """Reuse the maintained scene-fixture ABI builder without running its corpus."""
    saved_run, saved_argv = controller.Original.run, sys.argv
    captured = []

    def take(self, value):
        captured.append(value)
        raise Ready()

    try:
        controller.Original.run = take
        sys.argv = [__file__, "--raw-scene"]
        try:
            controller.main()
        except Ready:
            return captured[0]
    finally:
        controller.Original.run, sys.argv = saved_run, saved_argv


class Joined(controller.Original):
    def prepare_gain(self, value, blocks):
        pass  # Full AwbPreProcV32 owns preparation, never run it twice.

    def invoke(self, name, *args, **kwargs):
        if self.bootstrapping and name == "gain-frame-continuation":
            raise Ready()
        return super().invoke(name, *args, **kwargs)

    def hook(self, uc, address, size, user):
        if not self.bootstrapping:
            if address == (self.symbols.get("xcam_get_awb_log_level", 0) & ~1):
                uc.mem_write(uc.reg_read(regs.UC_ARM_REG_R0), b"\0")
                uc.mem_write(uc.reg_read(regs.UC_ARM_REG_R1), b"\0")
                uc.reg_write(regs.UC_ARM_REG_PC, uc.reg_read(regs.UC_ARM_REG_LR))
                return
            if self.stubs.get(address) == "free" and getattr(
                self, "initializing", False
            ):
                self.live.discard(uc.reg_read(regs.UC_ARM_REG_R0))
                uc.reg_write(regs.UC_ARM_REG_PC, uc.reg_read(regs.UC_ARM_REG_LR))
                return
            if self.stubs.get(address) == "malloc":
                size = uc.reg_read(regs.UC_ARM_REG_R0)
                assert 0 < size < 65536
                pointer = self.arena
                self.arena += (size + 15) & ~15
                assert self.arena < HEAP + 0x100000
                self.live.add(pointer)
                uc.mem_write(pointer, bytes(size))
                uc.reg_write(regs.UC_ARM_REG_R0, pointer)
                uc.reg_write(regs.UC_ARM_REG_PC, uc.reg_read(regs.UC_ARM_REG_LR))
                return
            if address == 0xD803C:
                self.wrapper_calls += 1
            if address == 0xD4260:
                self.reconfigured = True
                uc.reg_write(regs.UC_ARM_REG_PC, RETURN)
                return
            if self.stubs.get(address) == "__aeabi_uidivmod":
                self.runtime.invoke(
                    "__aeabi_uidivmod",
                    [uc.reg_read(regs.UC_ARM_REG_R0), uc.reg_read(regs.UC_ARM_REG_R1)],
                )
                for r in [regs.UC_ARM_REG_R0, regs.UC_ARM_REG_R1]:
                    uc.reg_write(r, self.runtime.uc.reg_read(r))
                uc.reg_write(regs.UC_ARM_REG_PC, uc.reg_read(regs.UC_ARM_REG_LR))
                return
        # dispatch_active stays false: inherited dispatch hook would stop early.
        super().hook(uc, address, size, user)

    def start(self, wb, raw, initial, geometry, seed_previous=False):
        value = layout_case()
        s = value["controller"]
        s["scene_iq"] = wb
        s["measurement"]["raw"] = raw.hex()
        s["measurement"].update(rename=False, seen=False, cache_count=0)
        s.update(
            frame=0,
            prior_sample=0.0,
            variance=0.0,
            environment=0,
            xy_history=[],
            color_history=[],
            high_history=[],
            used_previous=False,
            exclusion_count=0,
            previous_region=0,
        )
        s["outer"].update(
            application_flag=False,
            application_mode=1,
            reference_valid=False,
            matched=False,
            frames=0,
        )
        s["dispatch"].update(update=True, countdown=20, scale=None)
        for light in s["lights"]:
            light["extra"] = False
        value.update(
            raw_history=[],
            output_history=[],
            brightness=0,
            sample=0.0,
            previous=[0.0] * 4,
            candidate=[
                struct.unpack("<f", struct.pack("<I", x))[0] for x in initial["current"]
            ],
            coefficient=0.0,
            offsets=[0.0] * 4,
        )
        self.bootstrapping = True
        try:
            self.run(value)
        except Ready:
            pass
        self.bootstrapping = False
        self.dispatch_active = False
        self.outer_active = True
        self.wrapper_calls = 0
        self.single_calls = self.selected_gain_calls = 0
        seed = bytes(self.uc.mem_read(HEAP, 0x4000))
        c = bytearray(0x4000)
        for offset in [0x80, 0x8C, 0x134, 0x138, 0x240, 0x244, 0x2DEC, 0x33E4]:
            c[offset : offset + 4] = seed[offset : offset + 4]
        c[0xB0:0xB8] = seed[0xB0:0xB8]
        c[0x11C:0x128] = seed[0x11C:0x128]
        cfg = bytearray(self.uc.mem_read(HEAP + 0x8000, 0x800))
        cal = bytearray(self.uc.mem_read(HEAP + 0x9000, 0x800))

        def w(b, o, v):
            struct.pack_into("<I", b, o, v)

        def f(b, o, *v):
            struct.pack_into("<" + "f" * len(v), b, o, *v)

        for o, v in [
            (8, 1),
            (0x28, 2),
            (0x2C, 0),
            (0x34, 0),
            (0x4C, HEAP + 0x7D000),
            (0x33AC, 0),
            (0x33BC, geometry["sampled"][0]),
            (0x33C0, geometry["sampled"][1]),
            (0x33B0, 0),
            (0x33D4, 0),
            (0x33E0, 0),
            (0x369C, 1),
        ]:
            w(c, o, v)
        c[0x3345:0x3348] = bytes(3)
        c[0x2ECE] = c[0x36A0] = c[0x36B8] = 0
        f(c, 0x3480, 0.0)
        for h in [0x3478, 0x3490, 0x3498, 0x355C, 0x3564, 0x3598, 0x35A0]:
            w(c, h, HEAP + h)
            w(c, h + 4, HEAP + h)
        for o in [0x353C, 0x3578]:
            struct.pack_into("<4I", c, o, *initial["current"])
        struct.pack_into("<2H", c, 0x2ED4, 2304, 1296)
        c[0x33B8:0x33BA] = bytes(geometry["block"])
        w(cfg, 0x398, 2)
        w(cfg, 0x158, 4)
        f(cfg, 0x1F0, geometry["absoluteCountThreshold"])
        f(cfg, 0x4A8, 0.001, 0.005, 0.05)
        e = wb["autoExtPara"]
        curves = dict(
            enabled=e["smartRun"]["enable"],
            smart=e["smartRun"]["cfg"],
            points=e["probCalcWp"],
            regions=e["xyRegionStableSelection"]["wpNumTh"],
            interval=e["runInterval"],
        )
        curves["points"] = e["division"]["wpNumTh"]
        preprocess.Original.configure_curves(self, cfg, cal, curves)
        for o, b in [(0, c), (0x8000, cfg), (0x9000, cal)]:
            self.uc.mem_write(HEAP + o, bytes(b))
        self.arena = HEAP + 0x90000
        self.live = set()
        # Execute the original software-result initializer over this calibrated
        # context, rather than guessing its history/current-gain defaults.
        self.uc.mem_write(HEAP + 0x38, struct.pack("<I", 5))
        self.uc.mem_write(HEAP + 0x3C, b"\1")
        self.uc.mem_write(
            HEAP + 0x813C,
            struct.pack(
                "<I",
                next(
                    i
                    for i, l in enumerate(wb["autoPara"]["lightSources"])
                    if l["name"] == e["lightSourceForFirstFrame"]
                ),
            ),
        )
        self.uc.mem_write(HEAP + 0x7E000, struct.pack("<II", 0, 1))
        self.uc.mem_write(HEAP + 0x7E100, struct.pack("<8I", 1, 0, 0, 0, 0, 0, 0, 0))
        self.uc.mem_write(HEAP + 0x7E200, bytes(0x400))
        self.uc.mem_write(HEAP + 0x7E700, bytes(20))
        self.initializing = True
        status = self.invoke(
            next(n for n in self.symbols if "InitinalSwResParaCom2" in n),
            [HEAP + 0x7E000, HEAP + 0x7E100, HEAP + 0x7E200, HEAP + 0x8000],
            stack=struct.pack("<II", HEAP + 0x7E700, HEAP),
        )
        self.initializing = False
        assert status == 0, status
        self.startup = {
            name: list(struct.unpack("<4I", self.uc.mem_read(HEAP + offset, 16)))
            for name, offset in [
                ("gain353C", 0x353C),
                ("gain3578", 0x3578),
                ("previous352C", 0x352C),
            ]
        }
        if seed_previous:
            self.uc.mem_write(HEAP + 0x352C, struct.pack("<4I", *initial["current"]))
        self.uc.mem_write(HEAP + 0x33BC, struct.pack("<2I", *geometry["sampled"]))
        self.uc.mem_write(HEAP + 0x33B8, bytes(geometry["block"]))
        self.uc.mem_write(HEAP + 0x2ED4, struct.pack("<2H", 2304, 1296))

    def adopt_initialized(self, native):
        snapshot = native.snapshot()
        assert snapshot["context_ptr"] == HEAP and snapshot["arena"] < HEAP + 0xA0000
        self.uc.mem_write(HEAP, snapshot["heap"])
        self.bootstrapping = self.dispatch_active = self.initializing = False
        self.outer_active = True
        self.wrapper_calls = self.single_calls = self.selected_gain_calls = 0
        self.arena = snapshot["arena"]
        self.live = set()
        self.startup = {
            name: list(struct.unpack("<4I", self.uc.mem_read(HEAP + offset, 16)))
            for name, offset in [
                ("gain353C", 0x353C),
                ("gain3578", 0x3578),
                ("previous352C", 0x352C),
            ]
        }

    def frame(self, raw, metadata, first):
        self.uc.mem_write(HEAP + 0x70000, raw)
        self.uc.mem_write(HEAP + 0x4C, struct.pack("<I", HEAP + 0x7D000))
        # The single-camera processing callback binds the incoming metadata
        # header at translated-frame +0x1d70 before calling AwbPreProcV32.
        self.uc.mem_write(HEAP + 0x2DEC, struct.pack("<I", HEAP + 0x70000 + 0x1D70))
        self.uc.mem_write(
            HEAP + 0x7D000, struct.pack("<2f", metadata["normalizedBrightness"], 0.0)
        )
        self.uc.mem_write(HEAP + 0x5C, struct.pack("<f", metadata["iso"]))
        self.uc.mem_write(HEAP + 0x3349, bytes([first]))
        self.reconfigured = False
        calls = self.wrapper_calls
        self.invoke(SYMBOL, [HEAP + 0x70000, HEAP], instructions=5000000)
        assert self.uc.reg_read(regs.UC_ARM_REG_PC) == RETURN, (
            "Native replay did not reach bounded return"
        )
        c = bytes(self.uc.mem_read(HEAP, 0x4000))
        cfg_pointer = struct.unpack_from("<I", c, 0x8C)[0]
        cfg = bytes(self.uc.mem_read(cfg_pointer, 0x4B8))
        return dict(
            gainBits=list(struct.unpack_from("<4I", c, 0x353C)),
            controllerFrame=struct.unpack_from("<I", c, 0x33AC)[0],
            countdown=struct.unpack_from("<i", cfg, 0x4B4)[0],
            complete=bool(c[0x13C]),
            activeLights=cfg[0x138],
            reconfigure=self.reconfigured,
            calculated=self.wrapper_calls > calls,
            region=c[0x33FC],
            density=struct.unpack_from("<f", c, 0x33CC)[0],
            dampingCoefficient=struct.unpack_from("<f", c, 0x3484)[0],
            probabilities=[
                struct.unpack(
                    "<f",
                    self.uc.mem_read(
                        struct.unpack_from("<I", c, 0x33E4)[0] + j * 0xA0 + 0x74, 4
                    ),
                )[0]
                for j in range(cfg[0x138])
            ],
            diagnostics=dict(
                sampled=list(struct.unpack_from("<2I", c, 0x33BC)),
                variance=struct.unpack_from("<f", c, 0x3480)[0],
                retained=struct.unpack_from("<I", c, 0x33C8)[0],
                regionThresholds=list(struct.unpack_from("<2f", cfg, 0x38C)),
                countThresholds=list(struct.unpack_from("<2I", cfg, 0x1B8)),
                absoluteRelative=list(struct.unpack_from("<2f", cfg, 0x1F0)),
                rawGainBits=list(struct.unpack_from("<4I", c, 0x34A4)),
                coefficientBits=struct.unpack_from("<I", c, 0x3484)[0],
                effectiveBits=struct.unpack_from("<I", c, 0x3488)[0],
                brightnessBits=struct.unpack_from("<I", c, 0x33DC)[0],
                region=c[0x33FC],
            ),
        )


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "samples", type=Path, nargs="?", help="Legacy paired group capture directory"
    )
    p.add_argument(
        "--trace-dir",
        type=Path,
        help="Replay contiguous frame-NNN capture files once in actual order; overrides paired samples",
    )
    p.add_argument("--cycles", type=int, default=2)
    p.add_argument("--zero-brightness-diagnostic", action="store_true",
                   help="Override only AE brightness metadata to zero; numerical dark-history regression, not a physical dark-scene test")
    p.add_argument(
        "--require-match",
        action="store_true",
        help="Exit nonzero if represented comparison differs; does not qualify excluded boundaries",
    )
    p.add_argument(
        "--seed-previous-diagnostic",
        action="store_true",
        help="Controlled diagnostic only: replace native352C previous vector with initialgain",
    )
    p.add_argument(
        "--fixture",
        type=Path,
        default=ROOT / "firmware/rkaiq-rs/target/release/numeric-fixture",
    )
    p.add_argument(
        "--hardware-reference",
        action="store_true",
        help="Execute native reconfiguration and compare complete next SDK records",
    )
    p.add_argument(
        "--native-initialization",
        action="store_true",
        help="Build native context with original JSON parser, init, prepare and BLC binding",
    )
    p.add_argument("--report", type=Path, required=True)
    a = p.parse_args()
    assert 1 <= a.cycles <= 8

    def fixture(kind, v):
        out = subprocess.run(
            [str(a.fixture)],
            input=kind + " " + json.dumps(v, separators=(",", ":")) + "\n",
            text=True,
            capture_output=True,
            check=True,
        )
        result = json.loads(out.stdout)
        assert "error" not in result, result
        return result

    wb = json.loads(
        (
            ROOT
            / ".tools/reverse-engineering/iqfiles/sc3336_CMK-OT2119-PC1_30IRC-F16.json"
        ).read_text()
    )["main_scene"][0]["sub_scene"][0]["scene_isp32"]["wb_v32"]
    if a.trace_dir:
        paths = sorted(a.trace_dir.glob("frame-*.json"))
        assert 1 <= len(paths) <= 32, "Trace must contain 1..32 frames"
        assert [p.name for p in paths] == [
            f"frame-{i:03d}.json" for i in range(len(paths))
        ], "Trace frame indices must be contiguous from 000"
        meta = [json.loads(p.read_text()) for p in paths]
        raw = [p.with_suffix(".translated.bin").read_bytes() for p in paths]
        sdk_paths = [p.with_suffix(".sdk.bin") for p in paths]
        provenance_paths = []
        for i, (p, m, r, sdk) in enumerate(zip(paths, meta, raw, sdk_paths)):
            assert m["index"] == i and isinstance(m["requestedUpdate"], bool), (
                "Invalid trace index/update metadata"
            )
            assert m["group"] == struct.unpack_from("<i", r, 0x1D78)[0], (
                "Translated group disagrees with sidecar"
            )
            assert len(sdk.read_bytes()) == 1204, "Invalid trace SDK length"
            provenance_paths.extend([p, p.with_suffix(".translated.bin"), sdk])
            stats = p.with_suffix(".stats.raw")
            if stats.exists():
                provenance_paths.append(stats)
        order = list(range(len(raw)))
        incoming_updates = [m["requestedUpdate"] for m in meta]
        initial_sdk = sdk_paths[0]
    else:
        assert a.samples is not None, "Provide paired samples or --trace-dir"
        raw = [(a.samples / f"group-{i}.translated.bin").read_bytes() for i in range(2)]
        meta = [
            json.loads((a.samples / f"group-{i}.json").read_text()) for i in range(2)
        ]
        provenance_paths = [
            a.samples / f"group-{i}.{suffix}"
            for i in range(2)
            for suffix in ["json", "translated.bin"]
        ]
        order = [i for _ in range(a.cycles) for i in range(2)]
        incoming_updates = [index == 0 for index in range(len(order))]
        initial_sdk = a.samples / "group-0.sdk.bin"
    if a.zero_brightness_diagnostic:
        for value in meta:
            value["normalizedBrightness"] = 0.0
    assert all(len(r) == 7680 for r in raw)
    assert all(m["association"] == "exact-registered-snapshot" for m in meta)
    common = dict(iq=wb, dimensions=[2304, 1296], sample_scale=1, iso=meta[0]["iso"])
    initial = fixture(
        "awb-initial-gain-state",
        dict(
            iq=wb,
            first=next(
                i
                for i, l in enumerate(wb["autoPara"]["lightSources"])
                if l["name"] == wb["autoExtPara"]["lightSourceForFirstFrame"]
            ),
        ),
    )
    geometry = fixture("awb-captured-gain", dict(common, raw=raw[0].hex()))["geometry"]
    stages = [
        dict(
            raw=[raw[i].hex()],
            cycles=1,
            iso=meta[i]["iso"],
            normalized_brightness=meta[i]["normalizedBrightness"],
            requested_update=incoming_updates[index],
        )
        for index, i in enumerate(order)
    ]
    sequence = dict(common, stages=stages)
    record = None
    signature = b"RUST-AWB-NORMAL" + bytes(49)
    weights = None
    if a.hardware_reference:
        hardware = importlib.import_module("awb-hardware-reference")
        record = initial_sdk.read_bytes()
        assert len(record) == 1204
        sequence.update(
            initial_measurement=record.hex(), measurement_signature=signature.hex()
        )
    expected = fixture("awb-captured-sequence", sequence)["frames"]
    arm = Joined()
    initialization = None
    if a.native_initialization:
        assert a.trace_dir and a.hardware_reference and not a.seed_previous_diagnostic
        loader = importlib.import_module("awb-json-native")
        iq = json.loads(
            (
                ROOT
                / ".tools/reverse-engineering/iqfiles/sc3336_CMK-OT2119-PC1_30IRC-F16.json"
            ).read_text()
        )
        blc = iq["main_scene"][0]["sub_scene"][0]["scene_isp32"]["ablcV32_calib"]

        def constant(values):
            assert values and all(x == values[0] for x in values)
            return values[0]

        channels = lambda key: [
            int(constant(blc[key]["BLC_Data"][channel]))
            for channel in ["R_Channel", "Gr_Channel", "Gb_Channel", "B_Channel"]
        ]
        ob = blc["BlcObPara"]
        black_level = dict(
            enabled=bool(blc["Blc0TuningPara"]["enable"]),
            fixed=channels("Blc0TuningPara"),
            stage1_enabled=bool(blc["Blc1TuningPara"]["enable"]),
            stage1=channels("Blc1TuningPara"),
            offset=int(constant(ob["BLC_OB_Data"]["isp_ob_Offset"]))
            if ob["enable"]
            else 0,
            gain=constant(ob["BLC_OB_Data"]["isp_ob_preDgain"])
            if ob["enable"]
            else 1.0,
        )
        created = loader.NativeJson()
        created.parse(wb)
        created.create_single()
        created.prepare()
        startup = created.bind(black_level, digital_gain=1.0, iso=50.0)
        assert startup == record, (
            "Complete native startup differs from actual initial SDK record"
        )
        initialization = created.summary()
        arm.adopt_initialized(created)
        provenance_paths.append(Path(__file__).with_name("awb-json-native.py"))
    else:
        arm.start(wb, raw[0], initial, geometry, a.seed_previous_diagnostic)
    converter = OriginalArm(BINARY) if a.native_initialization else None

    def pack_kernel(sdk):
        converter.uc.mem_write(HEAP, bytes(1024))
        converter.uc.mem_write(HEAP + 0x10000, bytes(11145))
        converter.uc.mem_write(HEAP + 0x20000, sdk)
        converter.invoke(
            "_ZN5RkCam11Isp32Params26convertAiqAwbToIsp32ParamsER20isp32_isp_params_cfgRK25rk_aiq_awb_stat_cfg_v32_sb",
            [HEAP, HEAP + 0x10000, HEAP + 0x20000, 1],
        )
        assert not converter.calls, (
            "ISP32 converter unexpectedly needed imported adapters"
        )
        return bytes(converter.uc.mem_read(HEAP + 0x10000, 11145))

    # SDK SmalrangeX/Y are named legacy fields, not padding. Native malloc
    # leaves them uninitialized; ISP32's converter never reads these ranges.
    unused_small_ranges = set(
        j for start in [0x1C4, 0x1F4, 0x224, 0x254] for j in range(start, start + 16)
    )
    rows = []
    for i, reference in enumerate(expected):
        actual = arm.frame(raw[order[i]], meta[order[i]], incoming_updates[i])
        if a.hardware_reference:
            if actual["reconfigure"]:
                native = hardware.Reference.from_joined(
                    arm, signature=b"RUST-AWB-NORMAL"
                )
                if a.native_initialization:
                    # Native calibration graphs stay intact. Cohort names are
                    # an explicit opaque identity input, shared with the trace.
                    native.strategy = struct.unpack(
                        "<I", native.uc.mem_read(HEAP + 0x8C, 4)
                    )[0]
                    native.calibration = struct.unpack(
                        "<I", native.uc.mem_read(HEAP + 0x130, 4)
                    )[0]
                    native.timestamp = native.put(native.signature)
                    native.uc.mem_write(native.strategy + 0x440, signature)
                else:
                    native.seed(
                        wb,
                        record,
                        previous_weights=weights,
                        strategy_signature=signature,
                    )
                configured = native.run()
                record = configured["record"]
                weights = struct.unpack("<9f", configured["weight_cache"])
                # Carry forward actual native side effects, never Rust outputs.
                arm.uc.mem_write(HEAP, bytes(native.uc.mem_read(HEAP, 0x100000)))
            actual["measurement"] = record.hex()
        reference = dict(
            reference,
            gainBits=[
                struct.unpack("<I", struct.pack("<f", g))[0] for g in reference["gain"]
            ],
        )
        differences = {
            k: dict(native=v, rust=reference[k])
            for k, v in actual.items()
            if k in reference and v != reference[k]
        }
        ignored = []
        if a.native_initialization:
            native_record = bytes.fromhex(actual["measurement"])
            rust_record = bytes.fromhex(reference["measurement"])
            different = [
                j for j, (x, y) in enumerate(zip(native_record, rust_record)) if x != y
            ]
            ignored = [j for j in different if j in unused_small_ranges]
            if different and all(j in unused_small_ranges for j in different):
                differences.pop("measurement", None)
            native_kernel, rust_kernel = (
                pack_kernel(native_record),
                pack_kernel(rust_record),
            )
            if native_kernel != rust_kernel:
                differences["packedIspParameters"] = {
                    "nativeSha256": hashlib.sha256(native_kernel).hexdigest(),
                    "rustSha256": hashlib.sha256(rust_kernel).hexdigest(),
                }
        rows.append(
            dict(
                uninitializedUnusedSmallRangeOffsets=ignored,
                index=i,
                sourceFrameId=meta[order[i]].get("frameId"),
                sourceParametersId=meta[order[i]].get("parametersId"),
                requestedUpdate=incoming_updates[i],
                native=actual,
                differences=differences,
            )
        )
    assert arm.wrapper_calls > 0, "Capture never exercised native gain wrapper"
    report = dict(
        kind="joined-native-awb-captured-diagnostic",
        hardwareWrites=False,
        inputMode=("zero-brightness-metadata-diagnostic" if a.zero_brightness_diagnostic
                   else "actual-frame-order" if a.trace_dir else "cyclic-paired-captures"),
        zeroBrightnessDiagnostic=a.zero_brightness_diagnostic,
        seedPreviousDiagnostic=a.seed_previous_diagnostic,
        fullControllerQualified=False,
        nativeStartup=arm.startup,
        nativeInitialization=initialization,
        hardwareReconfigurationCompared=a.hardware_reference,
        packedIspBytesComparedPerFrame=11145 if a.native_initialization else 0,
        unusedSmallRangeExclusions=(
            [
                {
                    "offset": hex(start),
                    "bytes": 16,
                    "field": "SmalrangeX/Y (uninitialized, unused by ISP32)",
                }
                for start in [0x1C4, 0x1F4, 0x224, 0x254]
            ]
            if a.native_initialization
            else []
        ),
        initializedSdkBytesComparedPerFrame=1140 if a.native_initialization else 1204,
        nativeSymbol=SYMBOL,
        rustFixtureSha256=hashlib.sha256(a.fixture.read_bytes()).hexdigest(),
        provenance={
            str(p): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in [
                Path(__file__),
                BINARY,
                ROOT
                / ".tools/reverse-engineering/iqfiles/sc3336_CMK-OT2119-PC1_30IRC-F16.json",
                *provenance_paths,
                *(
                    [initial_sdk, Path(__file__).with_name("awb-hardware-reference.py")]
                    if a.hardware_reference
                    else []
                ),
            ]
        },
        frames=rows,
        wrapperCalls=arm.wrapper_calls,
        boundaries=[
            (
                "Complete native JSON parse, single-camera constructor, AwbInitV32, AwbPrepareV32 and caller-owned BLC binding; module lookup, clock/filesystem/memory adapters explicit."
                if a.native_initialization
                else "Calibrated fixture ABI builder plus native InitinalSwResParaCom2; complete calibration/context construction remains adapted."
            ),
            (
                "Complete native ReconfigHwParaV32 executes after gain; hardware calibration graph and stable cohort signature are explicit inputs."
                if a.hardware_reference
                else "Stops at ReconfigHwParaV32 entry; SDK record generation is not executed."
            ),
            (
                "Recorded statistics/order/ISO/update inputs with AE brightness deliberately forced to zero; not a physical dark-scene capture."
                if a.zero_brightness_diagnostic
                else "Actual captured frame order and per-frame AE/update inputs; capture provenance does not itself qualify optical response."
                if a.trace_dir
                else "Paired captured records replayed cyclically; not a continuous optical scene sequence."
            ),
        ],
        mismatchingFrames=sum(bool(r["differences"]) for r in rows),
    )
    a.report.parent.mkdir(parents=True, exist_ok=True)
    a.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "frames"}, indent=2))
    if a.require_match and report["mismatchingFrames"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
