"""Cross-build pinned quirc in default and float configurations for Luckfox."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / ".tools/quirc"
OUTPUT = ROOT / "dist/reverse-engineering/quirc-native-build"
COMMIT = "927d680904dc95fdff4cd9d022eb374b438ff8f2"


def run(*args):
    subprocess.run([str(arg) for arg in args], cwd=ROOT, check=True)


if not SOURCE.exists():
    run("git", "clone", "--depth", "1", "https://github.com/dlbeer/quirc.git", SOURCE)
head = subprocess.check_output(["git", "-C", str(SOURCE), "rev-parse", "HEAD"], text=True).strip()
if head != COMMIT:
    run("git", "-C", SOURCE, "fetch", "--depth", "1", "origin", COMMIT)
    run("git", "-C", SOURCE, "checkout", "--detach", COMMIT)
OUTPUT.mkdir(parents=True, exist_ok=True)
sources = [SOURCE / "lib" / name for name in ["quirc.c", "identify.c", "decode.c", "version_db.c"]]
for name, flags in [("quirc-default", []), ("quirc-float", ["-DQUIRC_FLOAT_TYPE=float", "-DQUIRC_USE_TGMATH"])]:
    run("mise", "exec", "zig@0.15.2", "--", "zig", "cc", "-target", "arm-linux-musleabihf",
        "-mcpu=cortex_a7", "-O3", "-static", "-I" + str(SOURCE / "lib"), *flags,
        ROOT / "reverse-engineering/rkaiq/scripts/quirc-native-bench.c", *sources, "-lm", "-o", OUTPUT / name)
    print(OUTPUT / name)
