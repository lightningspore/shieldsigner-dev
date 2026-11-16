"""Exercise the actual observer assembly with ABI-clobbering callees under ARM emulation."""

from pathlib import Path
import subprocess
import unittest
from elftools.elf.elffile import ELFFile
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_CPSR

ROOT = Path(__file__).resolve().parents[1]


class WrapperStateTest(unittest.TestCase):
    def test_register_stack_flags_and_snapshot(self):
        folder = ROOT / 'build/trace-wrapper-test'
        folder.mkdir(parents=True, exist_ok=True)
        stub = folder / 'stubs.S'
        stub.write_text('''.syntax unified
.thumb
.text
.balign 4
.global arm_heavy_mb
.thumb_func
arm_heavy_mb:
    movs r0,#1
    movs r1,#2
    movs r2,#3
    movs r3,#4
    mov r12,r3
    bx lr
.global bm_trace_io_snapshot
.thumb_func
bm_trace_io_snapshot:
    movs r0,#8
    movs r1,#9
    movs r2,#10
    movs r3,#11
    mov r12,r3
    bx lr
''')
        elf_path = folder / 'wrapper.elf'
        raw_path = folder / 'wrapper.bin'
        subprocess.run(
            [
                'arm-none-eabi-gcc',
                '-mcpu=cortex-a7',
                '-mthumb',
                '-nostdlib',
                '-Wl,-Ttext=0x10000',
                '-Wl,-e,bm_io_wrapper',
                str(ROOT / 'tools/kernel-trace/live_io_wrapper.S'),
                str(stub),
                '-o',
                str(elf_path),
            ],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ['arm-none-eabi-objcopy', '-O', 'binary', str(elf_path), str(raw_path)], check=True
        )
        with elf_path.open('rb') as f:
            symtab = ELFFile(f).get_section_by_name('.symtab')
            symbols = {s.name: s['st_value'] & ~1 for s in symtab.iter_symbols()}
        uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        uc.mem_map(0x10000, 4096)
        uc.mem_write(0x10000, raw_path.read_bytes())
        uc.mem_map(0x20000000, 0x4000)
        uc.mem_map(0x30000, 4096)
        values = [0x11110000 + i * 0x101 for i in range(13)]
        for i, value in enumerate(values):
            uc.reg_write(UC_ARM_REG_R0 + i, value)
        stack = 0x20002000
        ret = 0x30001
        flags = 0x680F0033
        uc.reg_write(UC_ARM_REG_CPSR, flags)
        uc.reg_write(UC_ARM_REG_SP, stack)
        uc.reg_write(UC_ARM_REG_LR, ret)
        snapshots = []

        def observe(_, address, size, user):
            if address == symbols['bm_trace_io_snapshot']:
                pointer = uc.reg_read(UC_ARM_REG_R0)
                words = [
                    int.from_bytes(uc.mem_read(pointer + i * 4, 4), 'little') for i in range(14)
                ]
                snapshots.append(words)

        uc.hook_add(UC_HOOK_CODE, observe)
        uc.emu_start(symbols['bm_io_wrapper'] | 1, ret & ~1, count=100)
        self.assertEqual(snapshots, [values + [ret]])
        self.assertEqual([uc.reg_read(UC_ARM_REG_R0 + i) for i in range(13)], values)
        self.assertEqual(uc.reg_read(UC_ARM_REG_SP), stack)
        self.assertEqual(uc.reg_read(UC_ARM_REG_LR), ret)
        self.assertEqual(uc.reg_read(UC_ARM_REG_CPSR) & 0xF80F0000, flags & 0xF80F0000)


if __name__ == '__main__':
    unittest.main()
