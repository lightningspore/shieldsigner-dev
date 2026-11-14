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
rkbin = ROOT/'.tools/rkbin'
build = ROOT/'build'
build.mkdir(exist_ok=True)
def run(argv, cwd=ROOT):
    subprocess.run(argv, cwd=cwd, check=True)
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
             for p in [raw, build/'hello-download.bin', ROOT/'link.ld', ROOT/'Cargo.toml', ROOT/'.cargo/config.toml', *sorted((ROOT/'src').rglob('*.rs'))]}
},indent=2)+'\n')
print('Built',build/'hello-download.bin')
