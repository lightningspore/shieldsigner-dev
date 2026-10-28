"""Build a static ARM QR-only ZXing benchmark using pinned source and mise Zig."""
from pathlib import Path
import shlex
import subprocess

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / ".tools/zxing-cpp-3.1.1"
BUILD = ROOT / "dist/reverse-engineering/qr-native-build"
COMMIT = "287c85df6f961c8efbfb5ffd736cd9457b8b890e"


def run(*args):
    subprocess.run([str(arg) for arg in args], cwd=ROOT, check=True)


if not SOURCE.exists():
    run("git", "clone", "--depth", "1", "--branch", "v3.1.1",
        "https://github.com/zxing-cpp/zxing-cpp.git", SOURCE)
assert subprocess.check_output(["git", "-C", str(SOURCE), "rev-parse", "HEAD"], text=True).strip() == COMMIT
BUILD.mkdir(parents=True, exist_ok=True)
zig = Path(subprocess.check_output(["mise", "where", "zig@0.15.2"], text=True).strip()) / "zig"
for name, language in [("cc", "cc"), ("cxx", "c++")]:
    path = BUILD / name
    path.write_text("#!/bin/sh\nexec " + shlex.quote(str(zig)) + " " + language +
                    " -target arm-linux-musleabihf -mcpu=cortex_a7 \"$@\"\n")
    path.chmod(0o755)
toolchain = BUILD / "toolchain.cmake"
toolchain.write_text(f'''set(CMAKE_SYSTEM_NAME Linux)
set(CMAKE_SYSTEM_PROCESSOR armv7)
set(CMAKE_C_COMPILER "{BUILD / 'cc'}")
set(CMAKE_CXX_COMPILER "{BUILD / 'cxx'}")
set(CMAKE_TRY_COMPILE_TARGET_TYPE STATIC_LIBRARY)
''')
project = BUILD / "project"
project.mkdir(exist_ok=True)
project.joinpath("CMakeLists.txt").write_text(f'''cmake_minimum_required(VERSION 3.16)
project(QrNativeBench LANGUAGES C CXX)
set(CMAKE_CXX_STANDARD 20)
add_subdirectory("{SOURCE}" zxing)
add_executable(qr-native-bench "{ROOT / 'reverse-engineering/rkaiq/scripts/qr-native-bench.cpp'}")
target_link_libraries(qr-native-bench PRIVATE ZXing::ZXing)
target_link_options(qr-native-bench PRIVATE -static)
add_executable(qr-native-threshold "{ROOT / 'reverse-engineering/rkaiq/scripts/qr-native-threshold.cpp'}")
target_link_libraries(qr-native-threshold PRIVATE ZXing::ZXing)
target_link_options(qr-native-threshold PRIVATE -static)
add_executable(shieldsigner-qr-reader "{ROOT / 'reverse-engineering/rkaiq/scripts/shieldsigner-qr-reader.cpp'}")
target_link_libraries(shieldsigner-qr-reader PRIVATE ZXing::ZXing)
target_link_options(shieldsigner-qr-reader PRIVATE -static)
''')
options = ["-DBUILD_SHARED_LIBS=OFF", "-DZXING_READERS=ON", "-DZXING_WRITERS=OFF",
           "-DZXING_EXAMPLES=OFF", "-DZXING_C_API=OFF", "-DZXING_DISABLE_PCH=ON"]
options += ["-DZXING_ENABLE_" + name + "=OFF" for name in ["1D", "AZTEC", "DATAMATRIX", "MAXICODE", "PDF417"]]
run("cmake", "-S", project, "-B", BUILD / "cmake", "-DCMAKE_BUILD_TYPE=Release",
    "-DCMAKE_TOOLCHAIN_FILE=" + str(toolchain), *options)
run("cmake", "--build", BUILD / "cmake", "--target", "qr-native-bench", "qr-native-threshold", "shieldsigner-qr-reader", "--parallel", "6")
print(BUILD / "cmake/qr-native-bench")
