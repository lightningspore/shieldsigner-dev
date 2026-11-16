"""Compare generated write predictions with actual Thumb instructions under Unicorn."""

import random
import sys
import unittest
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_MEM_WRITE, UC_HOOK_MEM_UNMAPPED
from unicorn.arm_const import (
    UC_ARM_REG_R0,
    UC_ARM_REG_SP,
    UC_ARM_REG_LR,
    UC_ARM_REG_PC,
    UC_ARM_REG_CPSR,
)

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from live_trace_sites import MODULES, read_module, predict, thumb_call
from c_ir_backend import predict_c, call_c
from isp_trace_sites import read_isp


class CallEncodingTest(unittest.TestCase):
    def test_forward_backward_and_range(self):
        decoder = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
        for pc, target in [(0x100000, 0x110001), (0x110002, 0x100001), (0x100002, 0x100007)]:
            for link in [True, False]:
                self.assertEqual(call_c(pc, target, link), thumb_call(pc, target, link))
                ins = list(decoder.disasm(call_c(pc, target, link), pc))
                self.assertEqual(len(ins), 1)
                self.assertEqual(ins[0].mnemonic, 'bl' if link else 'b.w')
                self.assertEqual(int(ins[0].op_str.removeprefix('#'), 16), target & ~1)
        with self.assertRaises(ValueError):
            thumb_call(0x100000, 0x3000001)


class StorePredictionTest(unittest.TestCase):
    def test_every_whitelisted_mmio_site(self):
        self.check_modules([read_module(name) for name in MODULES], 14)

    def test_selected_isp_mmio_sites(self):
        self.check_modules([read_isp()], 9)

    def check_modules(self, modules, expected_count):
        rng = random.Random(0x1103)
        sites_checked = 0
        for module, text in modules:
            name = module['module']
            for site in module['sites']:
                if site['kind'] != 'mmio':
                    continue
                sites_checked += 1
                for case in range(32):
                    uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
                    mapped = set()

                    def map_page(address):
                        page = address & ~4095
                        if page in mapped:
                            return
                        uc.mem_map(page, 4096)
                        mapped.add(page)
                        # Low values keep indexed offsets small; pointer-shaped inputs are supplied in registers.
                        uc.mem_write(
                            page,
                            b''.join(
                                ((i * 17 + case) & 255).to_bytes(4, 'little') for i in range(1024)
                            ),
                        )

                    def ensure(address, size):
                        for page in range(
                            address & ~4095, ((address + size - 1) & ~4095) + 1, 4096
                        ):
                            map_page(page)

                    base = 0x100000
                    ensure(base, len(text))
                    uc.mem_write(base, text)

                    def read_word(address):
                        ensure(address, 4)
                        return int.from_bytes(uc.mem_read(address, 4), 'little')

                    regs = [0x20000000 + rng.randrange(0, 0x1000, 4) for _ in range(16)]
                    regs[5] = rng.randrange(0, 8)
                    regs[13] = 0x21001000
                    regs[14] = 0x12345679
                    expected = predict(site['program'], regs, base, read_word)
                    self.assertEqual(predict_c(site['program'], regs, base, read_word), expected)
                    for index in range(13):
                        uc.reg_write(UC_ARM_REG_R0 + index, regs[index])
                    uc.reg_write(UC_ARM_REG_SP, regs[13])
                    uc.reg_write(UC_ARM_REG_LR, regs[14])
                    writes = []

                    def invalid(_, access, address, size, value, user):
                        ensure(address, size)
                        return True

                    def written(_, access, address, size, value, user):
                        writes.append((address, value & 0xFFFFFFFF))

                    uc.hook_add(UC_HOOK_MEM_UNMAPPED, invalid)
                    uc.hook_add(UC_HOOK_MEM_WRITE, written)
                    start = base + site['offset'] + 4
                    last = site['program'][-1]
                    end = base + last['pcOffset'] + len(bytes.fromhex(last['bytes']))
                    uc.emu_start(start | 1, end, count=8)
                    self.assertEqual(writes, [expected], (name, site['offset'], case))
        self.assertEqual(sites_checked, expected_count)


if __name__ == '__main__':
    unittest.main()
