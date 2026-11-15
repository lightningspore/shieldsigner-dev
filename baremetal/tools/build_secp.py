# SPDX-License-Identifier: MIT
"""Build pinned libsecp256k1 for actual native curve operations; no host OS API."""
import hashlib,json,shutil,subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1];pin=json.loads((root/'secp/source.json').read_text())
source=root/'.tools/secp256k1'
if not source.exists():
 subprocess.run(['git','clone',pin['repository'],str(source)],check=True)
 subprocess.run(['git','checkout',pin['commit']],cwd=source,check=True)
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip()==pin['commit']
assert not subprocess.check_output(['git','status','--porcelain'],cwd=source,text=True).strip()
out=root/'build/secp';out.mkdir(parents=True,exist_ok=True)
tools=root/'.tools'/json.loads((root/'cxx-toolchain.json').read_text())['directory']/'bin'
flags='-Os -mthumb -mcpu=cortex-a7 -mfloat-abi=soft -mno-unaligned-access -ffunction-sections -fdata-sections -fno-builtin'
(out/'toolchain.cmake').write_text(f'''set(CMAKE_SYSTEM_NAME Generic)
set(CMAKE_TRY_COMPILE_TARGET_TYPE STATIC_LIBRARY)
set(CMAKE_C_COMPILER "{tools}/arm-none-eabi-gcc")
set(CMAKE_C_FLAGS_INIT "{flags}")
''')
args=['cmake','-S',str(source),'-B',str(out/'cmake'),'-DCMAKE_TOOLCHAIN_FILE='+str(out/'toolchain.cmake'),'-DCMAKE_BUILD_TYPE=MinSizeRel','-DBUILD_SHARED_LIBS=OFF','-DSECP256K1_ASM=OFF','-DSECP256K1_USE_EXTERNAL_DEFAULT_CALLBACKS=ON','-DSECP256K1_BUILD_BENCHMARK=OFF','-DSECP256K1_BUILD_TESTS=OFF','-DSECP256K1_BUILD_EXHAUSTIVE_TESTS=OFF','-DSECP256K1_BUILD_CTIME_TESTS=OFF','-DSECP256K1_BUILD_EXAMPLES=OFF','-DSECP256K1_ENABLE_MODULE_ECDH=ON','-DSECP256K1_ENABLE_MODULE_EXTRAKEYS=ON','-DSECP256K1_ENABLE_MODULE_SCHNORRSIG=ON','-DSECP256K1_ENABLE_MODULE_RECOVERY=ON','-DSECP256K1_ENABLE_MODULE_ELLSWIFT=OFF','-DSECP256K1_ECMULT_WINDOW_SIZE='+str(pin['ecmultWindow']),'-DSECP256K1_ECMULT_GEN_KB='+str(pin['ecmultGenKb'])]
subprocess.run(args,check=True);subprocess.run(['cmake','--build',str(out/'cmake'),'-j4'],check=True)
archive=out/'libsignersecp.a';shutil.copyfile(out/'cmake/lib/libsecp256k1.a',archive)
shutil.copyfile(source/'COPYING',out/'COPYING')
receipt={**pin,'archiveSha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'configuration':'ARM32 portable C, no asm, small constant-time precomputation tables, actual ECDH/extrakeys/Schnorr/recovery modules','note':'Primitive implementation, not entropy or whole-wallet qualification'}
(out/'manifest.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
