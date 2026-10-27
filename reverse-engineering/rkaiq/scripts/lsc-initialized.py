#!/usr/bin/env python3
"""Full LSC native constructor/prepare then persistent processing callback."""

import importlib
import struct
from differential import HEAP, regs, u32

reference = importlib.import_module("lsc-frames")


class OriginalConstructor(reference.OriginalFrames):
    def hook(self, uc, address, size, user):
        name = self.stubs.get(address)
        if name in ("malloc", "sprintf"):
            a, b, c, d = [
                uc.reg_read(r)
                for r in (
                    regs.UC_ARM_REG_R0,
                    regs.UC_ARM_REG_R1,
                    regs.UC_ARM_REG_R2,
                    regs.UC_ARM_REG_R3,
                )
            ]
            if name == "malloc":
                if a == 0xD7AC:
                    result = HEAP + 0x60000
                else:
                    assert 0 < a <= 4096
                    result = self.bump
                    self.bump += (a + 7) & ~7
                    assert self.bump < HEAP + 0x30000
                uc.mem_write(result, bytes(a))
            else:
                # Controlled libc formatting boundary, only the native constant
                # format used to concatenate resolution and table suffix.
                assert self.string(b) == b"%s_%s"
                text = self.string(c) + b"_" + self.string(d)
                assert len(text) < 64
                uc.mem_write(a, text + b"\0")
                result = len(text)
            uc.reg_write(regs.UC_ARM_REG_R0, result)
            uc.reg_write(regs.UC_ARM_REG_PC, uc.reg_read(regs.UC_ARM_REG_LR))
            return
        super().hook(uc, address, size, user)

    def initialize(self, value):
        cal = value["calibration"]
        self.bump = HEAP + 0x20000
        root, resolutions, ills, tables = [
            HEAP + x for x in (0x19000, 0x18000, 0x4000, 0x30000)
        ]
        self.uc.mem_write(
            root,
            struct.pack(
                "<B3xIIB3xIIII",
                cal["common"]["enable"],
                resolutions,
                1,
                cal["alscCoef"]["damp_enable"],
                ills,
                len(cal["alscCoef"]["illAll"]),
                tables,
                len(cal["tbl"]["tableAll"]),
            ),
        )
        r = cal["common"]["resolutionAll"][0]
        self.uc.mem_write(resolutions, bytes(96))
        self.uc.mem_write(resolutions, r["name"].encode() + b"\0")
        self.uc.mem_write(
            resolutions + 32,
            struct.pack("<32H", *r["lsc_sect_size_x"], *r["lsc_sect_size_y"]),
        )
        for i, ill in enumerate(cal["alscCoef"]["illAll"]):
            p = ills + i * 68
            used = HEAP + 0x18400 + i * 160
            gains, vig = HEAP + 0x10000 + i * 256, HEAP + 0x11000 + i * 256
            self.uc.mem_write(p, bytes(68))
            self.uc.mem_write(p, struct.pack("<I", ill["usedForCase"]))
            self.uc.mem_write(p + 4, ill["name"].encode() + b"\0")
            self.uc.mem_write(
                p + 36,
                struct.pack(
                    "<2f6I",
                    *ill["wbGain"],
                    used,
                    len(ill["tableUsed"]),
                    gains,
                    len(ill["gains"]),
                    vig,
                    len(ill["vig"]),
                ),
            )
            for j, u in enumerate(ill["tableUsed"]):
                self.uc.mem_write(used + j * 32, bytes(32))
                self.uc.mem_write(used + j * 32, u["name"].encode() + b"\0")
            self.uc.mem_write(
                gains, struct.pack("<" + "f" * len(ill["gains"]), *ill["gains"])
            )
            self.uc.mem_write(
                vig, struct.pack("<" + "f" * len(ill["vig"]), *ill["vig"])
            )
        for i, t in enumerate(cal["tbl"]["tableAll"]):
            p = tables + i * 2412
            self.uc.mem_write(p, bytes(100))
            for offset, key in ((0, "name"), (32, "resolution"), (64, "illumination")):
                self.uc.mem_write(p + offset, t[key].encode() + b"\0")
            self.uc.mem_write(p + 96, struct.pack("<f", t["vignetting"]))
            grids = sum(
                [
                    t[k]["uCoeff"]
                    for k in (
                        "lsc_samples_red",
                        "lsc_samples_greenR",
                        "lsc_samples_greenB",
                        "lsc_samples_blue",
                    )
                ],
                [],
            )
            self.uc.mem_write(p + 100, struct.pack("<1156H", *grids))

        # Original runtime module lookup is shared SDK infrastructure, not stubbed.
        def u(a):
            return u32(self.uc.mem_read(a, 4))

        got = (u(0x1292AC) + 0x129198 + u(0x1292B0)) & 0xFFFFFFFF
        self.uc.mem_write(u(got), struct.pack("<I", 32))
        table = (u(0x1292B4) + 0x1291AE) & 0xFFFFFFFF
        assert u(table) == 32
        modules = u(table + 4)
        offset = None
        for i in range(100):
            p, off = struct.unpack("<II", self.uc.mem_read(modules + i * 8, 8))
            if not p:
                break
            if self.string(p) == b"lsc_v2":
                offset = off
                break
        assert offset is not None
        self.module_offset = offset
        config, pp = HEAP + 0x71000, HEAP + 0x72000
        self.uc.mem_write(config, bytes(64))
        self.uc.mem_write(config + 24, struct.pack("<I", root - offset))
        self.uc.mem_write(pp, bytes(4))
        assert self.invoke("AlscInit", [pp, config]) == 0
        ctx = u(pp)
        assert ctx == HEAP + 0x60000 and u(ctx) == root
        assert self.uc.mem_read(ctx + 0xD78C, 8) == struct.pack("<2f", 0.2, 0.05)
        assert self.uc.mem_read(ctx + 0xD798, 12) == struct.pack(
            "<3f", -1.0, -1.0, -1.0
        )
        assert u(ctx + 0x1CAC) == 0 and u(ctx + 0x1CB4) == 2
        assert bytes(self.uc.mem_read(ctx + 0xD7A4, 2)) == bytes(2)
        assert self.uc.mem_read(ctx + 0xD794, 1) == b"\x01"
        # The normal prepare callback supplies the selected resolution name.
        self.uc.mem_write(ctx + 0x54, r["name"].encode() + b"\0")
        assert self.invoke("AlscPrepare", [ctx], instructions=1000000) == 0
        return ctx


if __name__ == "__main__":
    reference.main(OriginalConstructor, initialized=True)
