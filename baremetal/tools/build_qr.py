# SPDX-License-Identifier: MIT
"""Build pinned ZXing QR readers for a single foreground bare-metal caller."""

import hashlib
import json
from pathlib import Path
import shutil
import subprocess

root = Path(__file__).resolve().parents[1]
source = root.parent / '.tools/zxing-cpp-3.1.1'
revision = '287c85df6f961c8efbfb5ffd736cd9457b8b890e'
if not source.exists():
    source.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ['git', 'clone', 'https://github.com/zxing-cpp/zxing-cpp.git', str(source)], check=True
    )
    subprocess.run(['git', 'checkout', revision], cwd=source, check=True)
assert (
    subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=source, text=True).strip() == revision
)
assert not subprocess.check_output(
    ['git', 'status', '--porcelain', '--untracked-files=normal'], cwd=source, text=True
).strip()
out = root / 'build/qr'
out.mkdir(parents=True, exist_ok=True)
core = out / 'source'
if core.exists():
    shutil.rmtree(core)
shutil.copytree(source / 'core', core)
shutil.copyfile(source / 'LICENSE', out / 'ZXing-LICENSE')
# No threads exist on this target. Scratch arrays are automatic, not TLS or
# retained statics, so each decode returns every allocation to the Rust heap.
p = core / 'src/ZXConfig.h'
p.write_text(
    p.read_text().replace('#define ZX_THREAD_LOCAL thread_local', '#define ZX_THREAD_LOCAL')
)
p = core / 'src/LocalGrid.cpp'
p.write_text(p.read_text().replace('thread_local std::vector', 'std::vector'))
p = core / 'CMakeLists.txt'
p.write_text(
    p.read_text().replace(
        'find_package(Threads REQUIRED)', 'add_library(Threads::Threads INTERFACE IMPORTED)'
    )
)
config = json.loads((root / 'cxx-toolchain.json').read_text())
tools = root / '.tools' / config['directory'] / 'bin'
flags = '-Os -mthumb -mcpu=cortex-a7 -mfloat-abi=soft -mno-unaligned-access -ffunction-sections -fdata-sections -funwind-tables -fexceptions -fno-pie'
toolchain = out / 'toolchain.cmake'
toolchain.write_text(f'''set(CMAKE_SYSTEM_NAME Generic)
set(CMAKE_TRY_COMPILE_TARGET_TYPE STATIC_LIBRARY)
set(CMAKE_C_COMPILER "{tools}/arm-none-eabi-gcc")
set(CMAKE_CXX_COMPILER "{tools}/arm-none-eabi-g++")
set(CMAKE_C_FLAGS_INIT "{flags}")
set(CMAKE_CXX_FLAGS_INIT "{flags} -fno-rtti -fno-threadsafe-statics")
''')
args = [
    'cmake',
    '-S',
    str(core),
    '-B',
    str(out / 'cmake'),
    '-DCMAKE_TOOLCHAIN_FILE=' + str(toolchain),
    '-DBUILD_SHARED_LIBS=OFF',
    '-DZXING_READERS=ON',
    '-DZXING_WRITERS=OFF',
    '-DCMAKE_BUILD_TYPE=Release',
]
for name in ('1D', 'AZTEC', 'DATAMATRIX', 'MAXICODE', 'PDF417'):
    args.append('-DZXING_ENABLE_' + name + '=OFF')
subprocess.run(args, check=True)
subprocess.run(['cmake', '--build', str(out / 'cmake'), '-j4'], check=True)
bridge = out / 'bridge.o'
subprocess.run(
    [
        str(tools / 'arm-none-eabi-g++'),
        *flags.split(),
        '-std=c++20',
        '-fno-rtti',
        '-fno-threadsafe-statics',
        '-I' + str(core / 'src'),
        '-I' + str(out / 'cmake'),
        '-c',
        str(root / 'qr/bridge.cpp'),
        '-o',
        str(bridge),
    ],
    check=True,
)
archive = out / 'libsignerqr.a'
shutil.copyfile(out / 'cmake/libZXing.a', archive)
subprocess.run([str(tools / 'arm-none-eabi-ar'), 'r', str(archive), str(bridge)], check=True)
receipt = {
    'source': 'https://github.com/zxing-cpp/zxing-cpp',
    'commit': revision,
    'license': 'Apache-2.0',
    'toolchain': config,
    'archiveSha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
    'bridgeSha256': hashlib.sha256((root / 'qr/bridge.cpp').read_bytes()).hexdigest(),
    'adaptations': [
        'No Threads link dependency; single foreground caller',
        'Automatic scratch vectors in ZXConfig/LocalGrid; no TLS or retained heap',
    ],
    'formats': 'QR family only; upstream decoding algorithms unchanged',
}
(out / 'manifest.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(receipt, indent=2))
