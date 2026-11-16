# SPDX-License-Identifier: MIT
"""Invalidate frozen C when its QSTR schema or manifest changes; core stays pinned.

Upstream makemanifest's inner timestamp fast path checks only .mpy inputs, even
when make correctly invokes it because the QSTR header changed.
"""

import subprocess, sys
from pathlib import Path

script, *args = sys.argv[1:]
output = Path(args[args.index('-o') + 1])
build = Path(args[args.index('-b') + 1])
inputs = [
    build / 'genhdr/qstrdefs.preprocessed.h',
    build / 'genhdr/qstrdefs.generated.h',
    Path(args[-1]),
]
if output.exists() and any(
    p.exists() and p.stat().st_mtime_ns > output.stat().st_mtime_ns for p in inputs
):
    output.unlink()
raise SystemExit(subprocess.call([sys.executable, script, *args]))
