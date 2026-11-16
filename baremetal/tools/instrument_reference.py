"""Insert narrow trace hooks into the exact, ignored GPL vendor source checkout.

Driver code stays under its upstream license. No driver implementation is copied
into the MIT bare-metal crate. Fail on unexpected source rather than approximate a patch.
"""

from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
repo = ROOT / '.tools/kernel-reference'
kernel = repo / 'sysdrv/source/kernel'
assert (
    subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip()
    == '0b5c1f30ca6333b7ec5af70d26511da9ef8d39af'
)
header = '''/* SPDX-License-Identifier: GPL-2.0-only */
#ifndef BAREMETAL_CAMERA_TRACE_H
#define BAREMETAL_CAMERA_TRACE_H
#include <linux/io.h>
extern void bm_trace_mmio(u32 block,u32 offset,u32 value,void __iomem *address);
extern void bm_trace_value(u32 block,u32 offset,u32 value,u32 width);
#endif
'''
(kernel / 'include/linux/baremetal_trace.h').write_text(header)


def patch(relative, changes):
    # Always derive from the pinned original, making repeated runs deterministic.
    original = subprocess.check_output(
        ['git', '-C', str(repo), 'show', 'HEAD:sysdrv/source/kernel/' + relative], text=True
    )
    text = original
    if '#include' in text:
        text = text.replace('#include', '#include <linux/baremetal_trace.h>\n#include', 1)
    else:
        raise RuntimeError('No include anchor: ' + relative)
    for old, new, count in changes:
        found = text.count(old)
        if found != count:
            raise RuntimeError(f'{relative}: expected {count} anchors, got {found}: {old}')
        text = text.replace(old, new)
    (kernel / relative).write_text(text)
    print(relative)


patch(
    'drivers/media/platform/rockchip/cif/hw.h',
    [
        ('writel(val, (addr) + (base))', 'bm_trace_mmio(1, (addr), (val), (addr) + (base))', 1),
        (
            'writel(readl((addr) + (base)) | (val), (addr) + (base))',
            'bm_trace_mmio(1, (addr), readl((addr) + (base)) | (val), (addr) + (base))',
            1,
        ),
        (
            'writel(readl((addr) + (base)) & (val), (addr) + (base))',
            'bm_trace_mmio(1, (addr), readl((addr) + (base)) & (val), (addr) + (base))',
            1,
        ),
    ],
)
patch(
    'drivers/media/platform/rockchip/cif/mipi-csi2.c',
    [('writel(val, (addr) + (base))', 'bm_trace_mmio(3, (addr), (val), (addr) + (base))', 1)],
)
patch(
    'drivers/phy/rockchip/phy-rockchip-csi2-dphy-hw.c',
    [
        (
            'writel(value, hw->hw_base_addr + reg->offset)',
            'bm_trace_mmio(2, reg->offset, value, hw->hw_base_addr + reg->offset)',
            1,
        ),
        (
            'writel(read_val, hw->hw_base_addr + reg->offset)',
            'bm_trace_mmio(2, reg->offset, read_val, hw->hw_base_addr + reg->offset)',
            1,
        ),
        (
            'regmap_write(hw->regmap_sys_grf, reg->offset, val);',
            'do { regmap_write(hw->regmap_sys_grf, reg->offset, val); bm_trace_value(7, reg->offset, val, 4); } while (0);',
            1,
        ),
        (
            'regmap_write(hw->regmap_grf, reg->offset, val);',
            'do { regmap_write(hw->regmap_grf, reg->offset, val); bm_trace_value(6, reg->offset, val, 4); } while (0);',
            1,
        ),
    ],
)
patch(
    'drivers/media/i2c/sc3336.c',
    [
        (
            'if (i2c_master_send(client, buf, len + 2) != len + 2)\n\t\treturn -EIO;\n\treturn 0;',
            'if (i2c_master_send(client, buf, len + 2) != len + 2)\n\t\treturn -EIO;\n\tbm_trace_value(5, reg, val, len);\n\treturn 0;',
            1,
        )
    ],
)
