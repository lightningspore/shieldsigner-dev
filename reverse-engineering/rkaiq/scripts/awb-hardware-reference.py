#!/usr/bin/env python3
"""Full native ReconfigHwParaV32 boundary on a copied, real post-gain context.

No hardware, numerical substitution, or SDK output patching. `Reference.from_joined`
copies the caller's complete emulated heap; `seed` supplies missing hardware IQ
pointers and an explicit current SDK snapshot. Calls execute original ARM code.
The sole non-memory adapter is an explicit deterministic timeString cohort token.
"""

import hashlib
import importlib
import struct

from awb_reference import OriginalAwb
from differential import BINARY, HEAP, OriginalArm, regs


class Reference(OriginalAwb):
    def __init__(self, signature=b"AWB-REFERENCE-COHORT"):
        assert (
            hashlib.sha256(BINARY.read_bytes()).hexdigest()
            == "ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9"
        )
        super().__init__(stdlib=True)
        assert b"\0" not in signature and len(signature) < 64
        self.signature = signature + b"\0"
        self.next = HEAP + 0xA0000
        self.time_calls = 0

    @classmethod
    def from_joined(cls, joined, **kwargs):
        assert getattr(joined, "arena", HEAP) < HEAP + 0xA0000
        result = cls(**kwargs)
        result.uc.mem_write(HEAP, bytes(joined.uc.mem_read(HEAP, 0x100000)))
        return result

    def hook(self, uc, address, size, user):
        if address == (self.symbols.get("timeString", 0) & ~1):
            self.time_calls += 1
            uc.reg_write(regs.UC_ARM_REG_R0, self.timestamp)
        elif address == (self.symbols.get("xcam_get_awb_log_level", 0) & ~1):
            for r in (regs.UC_ARM_REG_R0, regs.UC_ARM_REG_R1):
                uc.mem_write(uc.reg_read(r), b"\0")
        elif self.stubs.get(address) == "malloc":
            n = uc.reg_read(regs.UC_ARM_REG_R0)
            assert 0 < n < 65536
            uc.reg_write(regs.UC_ARM_REG_R0, self.put(bytes(n)))
        elif self.stubs.get(address) == "free":
            pass  # Bounded monotonic scratch arena; no address reuse required.
        elif self.stubs.get(address) == "memcmp":
            a, b, n = [
                uc.reg_read(r)
                for r in (regs.UC_ARM_REG_R0, regs.UC_ARM_REG_R1, regs.UC_ARM_REG_R2)
            ]
            a, b = bytes(uc.mem_read(a, n)), bytes(uc.mem_read(b, n))
            uc.reg_write(regs.UC_ARM_REG_R0, ((a > b) - (a < b)) & 0xFFFFFFFF)
        elif self.stubs.get(address) == "__aeabi_idivmod":
            self.runtime.invoke(
                "__aeabi_idivmod",
                [uc.reg_read(regs.UC_ARM_REG_R0), uc.reg_read(regs.UC_ARM_REG_R1)],
            )
            for r in (regs.UC_ARM_REG_R0, regs.UC_ARM_REG_R1):
                uc.reg_write(r, self.runtime.uc.reg_read(r))
        else:
            return super().hook(uc, address, size, user)
        uc.reg_write(regs.UC_ARM_REG_PC, uc.reg_read(regs.UC_ARM_REG_LR))

    def put(self, data):
        pointer = self.next
        self.next += (len(data) + 15) & ~15
        assert self.next < HEAP + 0x100000, (
            "Reference calibration/scratch arena exhausted"
        )
        self.uc.mem_write(pointer, bytes(data))
        return pointer

    def floats(self, values):
        return self.put(struct.pack("<" + "f" * len(values), *values))

    def seed(
        self,
        wb,
        record,
        *,
        capacity=4,
        minimum_count=None,
        previous_weights=None,
        strategy_signature=None,
    ):
        """Preserve post-gain context; assemble hardware fields from actual IQ.

        `record` is the exact currently effective 1204-byte SDK record. Default
        capacity4 is ISP32's physical detector count. Existing strategy counters,
        completion, sample brightness, damping and histogram remain caller-owned.
        previous_weights optionally supplies all nine unrounded native cache
        floats; omission models freshly zeroed hardware calibration, not a
        reconstructed historical cache inferred from rounded SDK bytes.
        strategy_signature optionally supplies the exact 64-byte initial cohort
        name at strategy+0x440; omission preserves the copied strategy name.
        This is input state, distinct from the timeString adapter used only
        when native update predicates request a new signature.
        Normal non-reserved time-share scheduling is initialized by native ARM.
        """
        assert len(record) == 1204 and 1 <= capacity <= 4
        auto = wb["autoPara"]
        lights = auto["lightSources"]
        assert 1 <= len(lights) <= 7
        assert len(auto["extraWpRange"]) == 7
        ptr = lambda o: struct.unpack("<I", self.uc.mem_read(HEAP + o, 4))[0]
        iq_pointer, strategy_pointer = ptr(0x80), ptr(0x8C)
        assert iq_pointer and strategy_pointer
        iq = bytearray(self.uc.mem_read(iq_pointer, 0x300))
        cal = bytearray(0x400)
        if previous_weights is not None:
            assert len(previous_weights) == 9
            struct.pack_into("<9f", cal, 0x298, *previous_weights)
        word = lambda b, o, n: struct.pack_into("<I", b, o, n)
        source = auto["rawSelectPara"]
        modes = [
            "CALIB_AWB_INPUT_RAW_FIXED",
            "CALIB_AWB_INPUT_RAW_AUTO",
            "CALIB_AWB_INPUT_BAYERNR",
            "CALIB_AWB_INPUT_DRC",
        ]
        word(cal, 4, modes.index(source["frameChooseMode"]))
        cal[8] = source["frameChoose"]
        # Existing converter refs establish these as u16 enable fields.
        struct.pack_into("<H", cal, 0x38, int(auto["uvDetectionEnable"]) * 0x0101)
        struct.pack_into("<H", cal, 0x3C, int(auto["yuvDetectionEnable"]) * 0x0101)
        cal[0x44] = capacity
        limits = auto["limitRange"]
        word(cal, 0xF4, self.floats(limits["lumaValue"]))
        word(cal, 0xF8, len(limits["lumaValue"]))
        for o, key in zip(
            (0xFC, 0x104, 0x10C, 0x114, 0x11C, 0x124, 0x12C, 0x134),
            ("maxR", "minR", "maxG", "minG", "maxB", "minB", "maxY", "minY"),
        ):
            assert len(limits[key]) == len(limits["lumaValue"])
            word(cal, o, self.floats([x * 16 for x in limits[key]]))
        # Execute native region quantizers in an independent scratch emulator.
        arm = OriginalArm(BINARY)
        uv_arm = importlib.import_module("awb-measurement-uv").Original()
        xy_records, yuv_records, uv_records = [], [], []
        for light in lights:
            x, y = light["xyRegion"], light["rtYuvRegion"]
            arm.uc.mem_write(HEAP, struct.pack("<8f", *(x["normal"] + x["big"])))
            arm.uc.mem_write(HEAP + 0x1000, bytes(48))
            arm.invoke(
                next(n for n in arm.symbols if "JsonXyParaFixed3" in n),
                [HEAP, HEAP + 0x1000],
            )
            xy_records.append(bytes(arm.uc.mem_read(HEAP + 0x1000, 48)))
            arm.uc.mem_write(
                HEAP,
                struct.pack(
                    "<18fB3x",
                    *(y["thcurve_u"] + y["thcure_th"] + y["lineVector"]),
                    y["disP1P2"],
                ),
            )
            arm.uc.mem_write(HEAP + 0x1000, bytes(32))
            arm.invoke(
                next(n for n in arm.symbols if "JsonRtYuvParaFixed2" in n),
                [HEAP, HEAP + 0x1000],
            )
            yuv_records.append(bytes(arm.uc.mem_read(HEAP + 0x1000, 32)))
            uv_records.append(
                bytes.fromhex(
                    uv_arm.run(light["uvRegion"]["u"], light["uvRegion"]["v"])
                )
            )
        for o, data in ((0x154, yuv_records), (0x158, uv_records), (0x174, xy_records)):
            word(cal, o, self.put(b"".join(data)))
        for i, region in enumerate(auto["extraWpRange"]):
            curve = region["weightInculde"]
            word(
                iq,
                0x13C + i * 40,
                1 if region["mode"] == "CALIB_AWB_EXCLUDE_WP_MODE" else 3,
            )
            struct.pack_into(
                "<4I",
                iq,
                0x150 + i * 40,
                self.floats(curve["lumaValue"]),
                len(curve["lumaValue"]),
                self.floats(curve["weight"]),
                len(curve["weight"]),
            )
        weight = auto["wpDiffLumaWeight"]
        word(iq, 0x258, weight["wpDiffWeiEnableTh"]["wpDiffWeiLvValueTh"])
        iq[0x265:0x26D] = bytes(bool(x) for x in weight["perfectBin"])
        rows = bytearray()
        for row in weight["wpDiffWeightLvSet"]:
            records = b"".join(
                struct.pack("<10f", r["ratioValue"], *r["weight"])
                for r in row["ratioSet"]
            )
            rows += struct.pack(
                "<fII", row["LvValue"], self.put(records), len(row["ratioSet"])
            )
        struct.pack_into(
            "<II", iq, 0x270, self.put(rows), len(weight["wpDiffWeightLvSet"])
        )
        self.uc.mem_write(iq_pointer, bytes(iq))
        self.calibration = self.put(cal)
        self.uc.mem_write(HEAP + 0x130, struct.pack("<I", self.calibration))
        self.uc.mem_write(HEAP + 0x2E90, record)
        # Native initializer writes exactly the 164-byte scheduling subobject.
        schedule = self.put(bytes(164))
        self.invoke(
            next(n for n in self.symbols if "AwbTimeShareInit" in n),
            [len(lights), capacity, 0, schedule],
        )
        self.uc.mem_write(
            strategy_pointer + 0x394, bytes(self.uc.mem_read(schedule, 164))
        )
        if minimum_count is not None:
            self.uc.mem_write(
                strategy_pointer + 0x49C, struct.pack("<f", minimum_count)
            )
        if strategy_signature is not None:
            assert len(strategy_signature) == 64 and b"\0" in strategy_signature
            self.uc.mem_write(strategy_pointer + 0x440, strategy_signature)
        self.timestamp = self.put(self.signature)
        self.strategy = strategy_pointer

    def run(self):
        """Execute the complete native function, returning raw output and side effects."""
        self.invoke(
            "_Z17ReconfigHwParaV32P12awb_contex_s", [HEAP], instructions=1_000_000
        )
        return {
            "record": bytes(self.uc.mem_read(HEAP + 0x2E90, 1204)),
            "previous_region": bytes(self.uc.mem_read(HEAP + 0x32D4, 4)),
            "pending": bytes(self.uc.mem_read(self.strategy + 0x94, 1)),
            "signature": bytes(self.uc.mem_read(self.strategy + 0x440, 64)),
            "weight_cache": bytes(self.uc.mem_read(self.calibration + 0x298, 36)),
            "time_calls": self.time_calls,
        }
