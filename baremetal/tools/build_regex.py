# SPDX-License-Identifier: MIT
"""Pinned PCRE2-8 without JIT/OS features for original app regex syntax."""
import hashlib,json,shutil,subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1]
source=root/'.tools/pcre2';pin='b2bd4254b379b9d7dc9a3dda060a7e27009ccdff'
if not source.exists():
    subprocess.run(['git','clone','--depth','1','--branch','pcre2-10.46','https://github.com/PCRE2Project/pcre2.git',str(source)],check=True)
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip()==pin
assert not subprocess.check_output(['git','status','--porcelain'],cwd=source,text=True).strip()
out=root/'build/regex';out.mkdir(parents=True,exist_ok=True)
patched=out/'source'
if patched.exists():shutil.rmtree(patched)
shutil.copytree(source,patched,ignore=shutil.ignore_patterns('.git'))
p=patched/'src/pcre2_compile.c';text=p.read_text()
for old,new in [('int32_t min = 0;', 'int min = 0;'),('int32_t max = REPEAT_UNLIMITED;', 'int max = REPEAT_UNLIMITED;')]:
    assert text.count(old)==1,old
    text=text.replace(old,new)
p.write_text(text)
cfg=json.loads((root/'cxx-toolchain.json').read_text());tools=root/'.tools'/cfg['directory']/'bin'
flags='-Os -mthumb -mcpu=cortex-a7 -mfloat-abi=soft -mno-unaligned-access -ffunction-sections -fdata-sections -fno-pie'
toolchain=out/'toolchain.cmake';toolchain.write_text(f'''set(CMAKE_SYSTEM_NAME Generic)
set(CMAKE_TRY_COMPILE_TARGET_TYPE STATIC_LIBRARY)
set(CMAKE_C_COMPILER "{tools}/arm-none-eabi-gcc")
set(CMAKE_C_FLAGS_INIT "{flags}")
''')
subprocess.run(['cmake','-S',str(patched),'-B',str(out/'cmake-port'),'-DCMAKE_TOOLCHAIN_FILE='+str(toolchain),'-DBUILD_SHARED_LIBS=OFF','-DPCRE2_BUILD_PCRE2_8=ON','-DPCRE2_BUILD_PCRE2_16=OFF','-DPCRE2_BUILD_PCRE2_32=OFF','-DPCRE2_BUILD_PCRE2GREP=OFF','-DPCRE2_BUILD_TESTS=OFF','-DPCRE2_SUPPORT_JIT=OFF','-DPCRE2_SUPPORT_UNICODE=ON','-DCMAKE_BUILD_TYPE=MinSizeRel'],check=True)
subprocess.run(['cmake','--build',str(out/'cmake-port'),'--target','pcre2-8-static','-j4'],check=True)
archive=out/'libsignerregex.a';shutil.copyfile(out/'cmake-port/libpcre2-8.a',archive)
shutil.copyfile(source/'LICENCE.md',out/'PCRE2-LICENCE')
(out/'manifest.json').write_text(json.dumps({'url':'https://github.com/PCRE2Project/pcre2','commit':pin,'version':'10.46','licenseSha256':hashlib.sha256((source/'LICENCE.md').read_bytes()).hexdigest(),'toolchain':cfg,'flags':flags,'sourceAdaptation':{'file':'src/pcre2_compile.c','change':'read_repeat_counts min/max locals use int instead of int32_t to match read_number(int*) on ARM newlib; both are32bits','patchedSha256':hashlib.sha256((patched/'src/pcre2_compile.c').read_bytes()).hexdigest()},'unicode':True,'jit':False,'archiveSha256':hashlib.sha256(archive.read_bytes()).hexdigest()},indent=2)+'\n')
