#!/usr/bin/env python3
"""Native in-memory JSON -> full WB graph, using embedded J2S reflection.

JSON parsing, calibration traversal, enum conversion and decimal conversion all
execute pinned ARM code. Adapters implement bounded allocation and libc memory
operations only; strtod executes the cached matching uClibc ARM implementation.
No hardware or JSON/math/output replacement occurs in the emulator.
Clock is fixed at epoch zero; timezone/configuration file opens report absent.
"""

import argparse
import hashlib
import json
import struct
from pathlib import Path

from awb_reference import RUNTIME, OriginalAwb
from differential import BINARY, HEAP, ROOT, OriginalArm, regs
from unicorn import UC_HOOK_INTR

LIBC = ROOT / ".tools/reverse-engineering/uclibc-runtime/libuClibc-1.0.31.so"
WB_NAME = b"CalibDbV2_Wb_Para_V32_t\0"
WB_BYTES = 0x83C


class NativeJson(OriginalAwb):
    def __init__(self):
        assert (
            hashlib.sha256(BINARY.read_bytes()).hexdigest()
            == "ff4cb39532e145c2317ac426038a2d57c629940a91d0d8812014e12c9a3c4dc9"
        )
        super().__init__(stdlib=True)
        assert (
            hashlib.sha256(LIBC.read_bytes()).hexdigest()
            == "b62e80f7f6c3f104548c91a02429c2ca9734dada97179938240e2075778465fb"
        )
        assert (
            hashlib.sha256(RUNTIME.read_bytes()).hexdigest()
            == "421df6d09247848a7f733d25ef45b726bc6366c8fc12be84751f6b408c1d92cd"
        )
        self.libc = OriginalArm(LIBC, tls=True)
        # uClibc errno lives below TP in its pthread descriptor.
        self.libc.uc.mem_map(0x8FF0000, 0x10000)
        self.syscalls = []
        self.libc.uc.hook_add(UC_HOOK_INTR, self.syscall)
        self.arena = HEAP + 0x10000
        self.allocations = {}
        self.free_blocks = []
        self.allocate_context = False
        self.strtod_calls = 0
        self.module_lookups = 0
        self.creating_single = False
        self.adapters = {}

    def syscall(self, uc, interrupt, user):
        number = uc.reg_read(regs.UC_ARM_REG_R7)
        assert interrupt == 2 and number == 5, (interrupt, number)
        # Sandboxed open of timezone configuration is absent; actual libc
        # handles ENOENT and computes its documented UTC fallback itself.
        self.syscalls.append({"number": number, "result": -2})
        uc.reg_write(regs.UC_ARM_REG_R0, (-2) & 0xFFFFFFFF)

    def allocate(self, size):
        assert 0 < size <= 0x80000
        rounded = (size + 15) & ~15
        if self.allocate_context and size == 0x36CC:
            self.allocate_context = False
            pointer = HEAP
        else:
            for i, (pointer, available) in enumerate(self.free_blocks):
                if available >= rounded:
                    self.free_blocks.pop(i)
                    if available > rounded:
                        self.free_blocks.append(
                            (pointer + rounded, available - rounded)
                        )
                    break
            else:
                pointer = self.arena
                self.arena += rounded
                assert self.arena <= HEAP + 0x100000, "Native JSON heap exhausted"
        self.allocations[pointer] = rounded
        return pointer

    def release(self, pointer):
        if pointer:
            assert pointer in self.allocations, hex(pointer)
            self.free_blocks.append((pointer, self.allocations.pop(pointer)))
            self.free_blocks.sort()
            merged = []
            for p, n in self.free_blocks:
                if merged and merged[-1][0] + merged[-1][1] == p:
                    merged[-1] = (merged[-1][0], merged[-1][1] + n)
                else:
                    merged.append((p, n))
            self.free_blocks = merged

    def string(self, pointer, maximum=0x80000):
        data = bytearray()
        for i in range(0, maximum, 256):
            chunk = bytes(self.uc.mem_read(pointer + i, min(256, maximum - i)))
            if b"\0" in chunk:
                return bytes(data) + chunk.split(b"\0", 1)[0]
            data.extend(chunk)
        raise AssertionError("Unterminated native string")

    def hook(self, uc, address, size, user):
        if self.creating_single and address == 0xCD598:
            # Exact single-AWB constprop.2 module lookup. The caller's opaque
            # calibration handle resolves to the real native J2S WB graph.
            assert uc.reg_read(regs.UC_ARM_REG_R0) == HEAP + 0x7310
            self.module_lookups += 1
            uc.reg_write(regs.UC_ARM_REG_R0, self.wb)
            uc.reg_write(regs.UC_ARM_REG_PC, uc.reg_read(regs.UC_ARM_REG_LR))
            return
        name = self.stubs.get(address)
        if name not in (
            "malloc",
            "calloc",
            "realloc",
            "free",
            "strdup",
            "strlen",
            "strcmp",
            "strncmp",
            "strncpy",
            "strtod",
            "snprintf",
            "sqrtf",
            "powf",
            "atan2f",
            "__aeabi_idivmod",
            "__aeabi_uidivmod",
            "gettimeofday",
            "localtime",
            "sprintf",
            "fopen64",
        ):
            return super().hook(uc, address, size, user)
        self.adapters[name] = self.adapters.get(name, 0) + 1
        a, b, c = [
            uc.reg_read(r)
            for r in (regs.UC_ARM_REG_R0, regs.UC_ARM_REG_R1, regs.UC_ARM_REG_R2)
        ]
        result = a
        if name in ("malloc", "calloc"):
            n = a * b if name == "calloc" else a
            result = self.allocate(max(1, n))
            if name == "calloc":
                uc.mem_write(result, bytes(n))
        elif name == "free":
            self.release(a)
        elif name == "realloc":
            result = self.allocate(max(1, b))
            if a:
                uc.mem_write(result, bytes(uc.mem_read(a, min(b, self.allocations[a]))))
                self.release(a)
        elif name == "strdup":
            data = self.string(a) + b"\0"
            result = self.allocate(len(data))
            uc.mem_write(result, data)
        elif name == "strlen":
            result = len(self.string(a))
        elif name in ("strcmp", "strncmp"):
            if name == "strncmp":
                first, second = [
                    bytes(uc.mem_read(p, c)).split(b"\0", 1)[0] for p in (a, b)
                ]
            else:
                first, second = self.string(a), self.string(b)
            result = ((first > second) - (first < second)) & 0xFFFFFFFF
        elif name == "strncpy":
            data = self.string(b)[:c]
            uc.mem_write(a, data + bytes(c - len(data)))
        elif name == "fopen64":
            self.syscalls.append(
                {
                    "adapter": "fopen64",
                    "path": self.string(a).decode(errors="replace"),
                    "result": None,
                }
            )
            result = 0
        elif name == "localtime":
            self.libc.uc.mem_write(HEAP, bytes(uc.mem_read(a, 4)))
            pointer = self.libc.invoke("localtime", [HEAP], instructions=1_000_000)
            result = HEAP + 0x7100
            uc.mem_write(result, bytes(self.libc.uc.mem_read(pointer, 44)))
        elif name == "gettimeofday":
            if a:
                uc.mem_write(a, bytes(8))
            if b:
                uc.mem_write(b, bytes(8))
            result = 0
        elif name in ("__aeabi_idivmod", "__aeabi_uidivmod"):
            self.runtime.invoke(name, [a, b])
            result = self.runtime.uc.reg_read(regs.UC_ARM_REG_R0)
            uc.reg_write(
                regs.UC_ARM_REG_R1, self.runtime.uc.reg_read(regs.UC_ARM_REG_R1)
            )
        elif name in ("sqrtf", "powf", "atan2f"):
            count = 1 if name == "sqrtf" else 2
            values = [
                struct.unpack(
                    "<f",
                    struct.pack("<I", uc.reg_read(getattr(regs, f"UC_ARM_REG_S{i}"))),
                )[0]
                for i in range(count)
            ]
            self.libc.invoke(name, floats=values)
            uc.reg_write(regs.UC_ARM_REG_S0, self.libc.uc.reg_read(regs.UC_ARM_REG_S0))
        elif name == "sprintf":
            args = [
                uc.reg_read(r)
                for r in (
                    regs.UC_ARM_REG_R0,
                    regs.UC_ARM_REG_R1,
                    regs.UC_ARM_REG_R2,
                    regs.UC_ARM_REG_R3,
                )
            ]
            fmt = self.string(b)
            assert b"%s" not in fmt, fmt
            self.libc.uc.mem_write(HEAP + 0xE1000, fmt + b"\0")
            args[0] = HEAP + 0xE0000
            args[1] = HEAP + 0xE1000
            stack = bytes(uc.mem_read(uc.reg_read(regs.UC_ARM_REG_SP), 256))
            result = self.libc.invoke(
                "sprintf", args, stack=stack, instructions=1_000_000
            )
            assert 0 <= result < 256
            uc.mem_write(a, bytes(self.libc.uc.mem_read(HEAP + 0xE0000, result + 1)))
        elif name == "snprintf":
            # Run the real formatting implementation with the caller's memory
            # and ARM vararg stack, then return only its bounded destination.
            self.libc.uc.mem_write(HEAP, bytes(uc.mem_read(HEAP, 0x100000)))
            args = [
                uc.reg_read(r)
                for r in (
                    regs.UC_ARM_REG_R0,
                    regs.UC_ARM_REG_R1,
                    regs.UC_ARM_REG_R2,
                    regs.UC_ARM_REG_R3,
                )
            ]
            self.libc.uc.mem_write(HEAP + 0xE1000, self.string(c) + b"\0")
            args[0] = HEAP + 0xE0000
            args[2] = HEAP + 0xE1000
            if not HEAP <= args[3] < HEAP + 0x100000:
                self.libc.uc.mem_write(HEAP + 0xE2000, self.string(args[3]) + b"\0")
                args[3] = HEAP + 0xE2000
            stack = bytes(uc.mem_read(uc.reg_read(regs.UC_ARM_REG_SP), 256))
            result = self.libc.invoke(
                "snprintf", args, stack=stack, instructions=1_000_000
            )
            if b:
                uc.mem_write(a, bytes(self.libc.uc.mem_read(HEAP + 0xE0000, b)))
        elif name == "strtod":
            # cJSON passes a bounded, NUL-terminated number buffer. Preserve the
            # real ARM double and end-pointer semantics across emulator heaps.
            data = self.string(a, 256) + b"\0"
            self.libc.uc.mem_write(HEAP, data)
            self.libc.invoke("strtod", [HEAP, HEAP + 0x1000], instructions=1_000_000)
            uc.reg_write(regs.UC_ARM_REG_D0, self.libc.uc.reg_read(regs.UC_ARM_REG_D0))
            if b:
                end = struct.unpack("<I", self.libc.uc.mem_read(HEAP + 0x1000, 4))[0]
                uc.mem_write(b, struct.pack("<I", a + end - HEAP))
            self.strtod_calls += 1
        uc.reg_write(regs.UC_ARM_REG_R0, result)
        uc.reg_write(regs.UC_ARM_REG_PC, uc.reg_read(regs.UC_ARM_REG_LR))

    def parse(self, wb):
        """Parse the real wb_v32 JSON object into its complete native pointer graph."""
        payload = json.dumps(wb, separators=(",", ":")).encode() + b"\0"
        text = self.allocate(len(payload))
        self.uc.mem_write(text, payload)
        name = self.allocate(len(WB_NAME))
        self.uc.mem_write(name, WB_NAME)
        self.ctx = HEAP + 0x7000
        self.wb = HEAP + 0x8000
        self.uc.mem_write(self.ctx, bytes(56))
        self.uc.mem_write(self.wb, bytes(WB_BYTES))
        self.invoke("_Z8j2s_initP7j2s_ctx", [self.ctx])
        self.invoke(
            "_Z17j2s_modify_structP7j2s_ctxPKcS2_Pv",
            [self.ctx, text, name, self.wb],
            instructions=150_000_000,
        )
        self.status = self.uc.reg_read(regs.UC_ARM_REG_R0)
        assert self.status == 0, hex(self.status)
        self.release(text)
        self.release(name)
        return self.wb

    def initialize(self):
        """Execute actual AwbInitV32, keeping its linked graph at original addresses."""
        self.allocate_context = True
        self.uc.mem_write(HEAP + 0x7040, bytes(4))
        self.invoke(
            "_Z10AwbInitV32PP12awb_contex_sP23CalibDbV2_Wb_Para_V32_s",
            [HEAP + 0x7040, self.wb],
            instructions=150_000_000,
        )
        status = self.uc.reg_read(regs.UC_ARM_REG_R0)
        context = struct.unpack("<I", self.uc.mem_read(HEAP + 0x7040, 4))[0]
        assert status == 0 and context == HEAP, (status, hex(context))
        return context

    def create_single(self):
        """Execute the complete SDK single-camera constructor at mapped CD5F4.

        The only wrapper adapter resolves its opaque calibration handle to the
        actual J2S-parsed WB pointer. AwbInit and scale/default state stores all
        execute natively; no initialized context fields are written here.
        """
        self.allocate_context = True
        output, config = HEAP + 0x7040, HEAP + 0x7300
        self.uc.mem_write(output, bytes(4))
        self.uc.mem_write(config, bytes(16))
        self.uc.mem_write(config + 0xC, struct.pack("<I", HEAP + 0x7310))
        symbol = "single-awb-create-context"
        self.symbols[symbol] = self.resolve_symbol("create_context", 0xCD5F4)
        self.creating_single = True
        try:
            self.invoke(symbol, [output, config], instructions=150_000_000)
        finally:
            self.creating_single = False
        context = struct.unpack("<I", self.uc.mem_read(output, 4))[0]
        assert context == HEAP, hex(context)
        assert struct.unpack("<I", self.uc.mem_read(HEAP + 0x369C, 4))[0] == 1
        assert self.uc.mem_read(HEAP + 0x3698, 1) == b"\0"
        return context

    def prepare(self, width=2304, height=1296, working_mode=0):
        """Actual AwbPrepareV32 with caller geometry; retain native init flags."""
        self.uc.mem_write(HEAP + 0x34, struct.pack("<I", working_mode))
        self.uc.mem_write(HEAP + 0x40, struct.pack("<II", width, height))
        status = self.invoke(
            "_Z13AwbPrepareV32P12awb_contex_s", [HEAP], instructions=150_000_000
        )
        assert status == 0, hex(status)
        return bytes(self.uc.mem_read(HEAP + 0x2E90, 1204))

    def bind(self, black_level=None, digital_gain=1.0, iso=50.0):
        """Execute AwbReCfgPregnBlc on actual native context and SDK record.

        Optional black_level fields match the 32-byte BLC result ABI:
        enabled:bool, fixed:[i16;4], stage1_enabled:bool, stage1:[i16;4],
        offset:i16, gain:f32. Inputs are caller-owned BLS results, not derived
        from or substituted into output bytes. Existing native remosaic,
        software pregain and AWB offset calibration stay untouched.
        """
        struct.pack("<ff", iso, digital_gain)  # Validate f32 representation.
        self.uc.mem_write(HEAP + 0x5C, struct.pack("<ff", iso, digital_gain))
        pointer = 0
        if black_level is not None:
            b = black_level
            assert isinstance(b["enabled"], bool) and isinstance(
                b["stage1_enabled"], bool
            )
            assert len(b["fixed"]) == len(b["stage1"]) == 4
            data = bytearray(32)
            data[0] = b["enabled"]
            data[10] = b["stage1_enabled"]
            struct.pack_into("<4h", data, 2, *b["fixed"])
            struct.pack_into("<4h", data, 12, *b["stage1"])
            struct.pack_into("<h", data, 22, b["offset"])
            struct.pack_into("<f", data, 24, b["gain"])
            pointer = HEAP + 0x7200
            self.uc.mem_write(pointer, bytes(data))
        self.uc.mem_write(HEAP + 0x6C, struct.pack("<I", pointer))
        self.uc.mem_write(HEAP + 0x7240, bytes(20))
        symbol = next(n for n in self.symbols if "AwbReCfgPregnBlc" in n)
        self.invoke(
            symbol, [HEAP, 0, HEAP + 0x7240, HEAP + 0x2E90], instructions=1_000_000
        )
        return bytes(self.uc.mem_read(HEAP + 0x2E90, 1204))

    def snapshot(self):
        """Preserve native linked-list addresses for a downstream joined executor."""
        return {
            "context_ptr": HEAP,
            "heap": bytes(self.uc.mem_read(HEAP, 0x100000)),
            "arena": self.arena,
        }

    def summary(self):
        raw = bytes(self.uc.mem_read(self.wb, WB_BYTES))
        return {
            "status": self.status,
            "wb_pointer": hex(self.wb),
            "wb_bytes": WB_BYTES,
            "wb_sha256": hashlib.sha256(raw).hexdigest(),
            "heap_highwater": self.arena - HEAP,
            "live_allocations": len(self.allocations),
            "strtod_calls": self.strtod_calls,
            "module_lookups": self.module_lookups,
            "adapters": self.adapters,
            "binary_sha256": hashlib.sha256(BINARY.read_bytes()).hexdigest(),
            "libc_sha256": hashlib.sha256(LIBC.read_bytes()).hexdigest(),
            "runtime_sha256": hashlib.sha256(RUNTIME.read_bytes()).hexdigest(),
            "syscalls": self.syscalls,
        }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--compare-sdk",
        type=Path,
        help="Optional existing 1204-byte SDK snapshot; no output bytes are changed",
    )
    args = parser.parse_args()
    path = (
        ROOT / ".tools/reverse-engineering/iqfiles/sc3336_CMK-OT2119-PC1_30IRC-F16.json"
    )
    assert (
        hashlib.sha256(path.read_bytes()).hexdigest()
        == "8c816c0f83c6d4d951d5d4335e9c63a0893cd4f99c501f3f3558bbbca9d2c94a"
    )
    wb = json.loads(path.read_text())["main_scene"][0]["sub_scene"][0]["scene_isp32"][
        "wb_v32"
    ]
    native = NativeJson()
    native.parse(wb)
    context = native.create_single()
    record = native.prepare()
    report = native.summary()
    report.update(
        context_ptr=hex(context),
        prepare_status=0,
        sdk_bytes=len(record),
        sdk_sha256=hashlib.sha256(record).hexdigest(),
    )
    if args.compare_sdk:
        expected = args.compare_sdk.read_bytes()
        assert len(expected) == 1204
        report["sdk_differences"] = [
            {"offset": hex(i), "native": a, "snapshot": b}
            for i, (a, b) in enumerate(zip(record, expected))
            if a != b
        ]
    print(json.dumps(report, indent=2))
