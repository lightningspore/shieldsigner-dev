"""Build original no_std stage 2 and package it with the unchanged vendor DDR blob."""
import configparser
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--features', default='')
args = parser.parse_args()
features=set(args.features.split(','))
runtime_info={}
inputs = []
if features & {'isp-3a-test','runtime-board'}:
    for name, size, digest in [
        ('sc3336-iq.json', 432259, '8c816c0f83c6d4d951d5d4335e9c63a0893cd4f99c501f3f3558bbbca9d2c94a'),
        ('isp-initial-parameters.bin', 11145, '25fa983c0dfc6313290336d25614db461be205cafaf9aa7598274be80fdded82'),
        ('isp-awb-sdk.bin', 1204, '4c081c95fe115f1c52ca84223e7a75cf647e64d3573accdcf5fa6c9c6352ccd1'),
    ]:
        path = ROOT/'.tools'/name
        if not path.exists() or path.stat().st_size != size or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise SystemExit(f'Missing/changed reference input {name}; see PHASE-8-STATUS.md')
        inputs.append(path)
rkbin = ROOT/'.tools/rkbin'
build = ROOT/'build'
build.mkdir(exist_ok=True)
def run(argv, cwd=ROOT):
    subprocess.run(argv, cwd=cwd, check=True)
if features & {'runtime-repl','runtime-board'}:
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT/'.tools/micropython',text=True).strip()
    if revision!='78ff170de9e32c79db6e64d3e33d2bd60002bdcd':
        raise SystemExit('Unexpected MicroPython revision; see PHASE-9-RUNTIME.md')
    run(['uv','run','--python','3.13','make','-C',str(ROOT/'micropython'),'-j4',
         'BOARD_BINDINGS='+('1' if 'runtime-board' in features else '0')])
    archive=ROOT/'build'/('micropython-board' if 'runtime-board' in features else 'micropython')/'libmicropython.a'
    runtime_info={'micropythonRevision':revision,'archiveSha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
                  'newlibHeaderPackage':(ROOT/'.tools/newlib/package.txt').read_text().strip()}
run(['mise', 'exec', 'rust@1.93.1', '--', 'cargo', 'build', '--release'] +
    (['--features', args.features] if args.features else []))
elf = ROOT/'target/armv7a-none-eabi/release/rv1103-bringup'
raw = build/'hello.bin'
run(['arm-none-eabi-objcopy', '-O', 'binary', str(elf), str(raw)])
shutil.copyfile(raw, rkbin/'hello-stage2.bin')
ini = configparser.ConfigParser()
ini.optionxform = str
ini.read(rkbin/'RKBOOT/RV1106MINIALL.ini')
ini['CODE472_OPTION']['Path1'] = 'hello-stage2.bin'
ini['OUTPUT']['PATH'] = 'hello-download.bin'
ini['FLAG']['CREATE_IDB'] = 'false'
with (rkbin/'hello.ini').open('w') as f: ini.write(f, space_around_delimiters=False)
run(['docker','run','--rm','--platform','linux/amd64','-v',str(rkbin)+':/work','-w','/work',
     'alpine:3.21@sha256:bc21487101ae47172509130ee1092cc273a831968d64b617776d1f69c81e42ab',
     './tools/boot_merger','hello.ini'])
shutil.copyfile(rkbin/'hello-download.bin', build/'hello-download.bin')
(build/'hello-manifest.json').write_text(json.dumps({
    'entryAddress':'0x00000000', 'stackTop':'0x00400000',
    'features': args.features,
    'note':'Entry and stack proven by Phase 2 ten-run gate; added features require their own DUT proof.',
    'files':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
             for p in [raw, build/'hello-download.bin', ROOT/'link.ld', ROOT/'Cargo.toml', ROOT/'Cargo.lock', ROOT/'build.rs', ROOT/'.cargo/config.toml', *sorted((ROOT/'src').rglob('*.rs')), *sorted((ROOT/'micropython').glob('*')), *inputs] if p.is_file()},
    'algorithmSources': {str(p.relative_to(ROOT.parent)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in [ROOT.parent/'firmware/rkaiq-rs/Cargo.toml', *sorted((ROOT.parent/'firmware/rkaiq-rs/src').glob('*.rs'))]} if 'isp' in args.features or 'runtime-board' in features else {},
    'runtime':runtime_info,
},indent=2)+'\n')
print('Built',build/'hello-download.bin')
