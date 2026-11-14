"""Build original no_std stage 2 and package it with the unchanged vendor DDR blob."""
import configparser
import argparse
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--features', default='')
parser.add_argument('--usb-serial', help='Development USB identity:1..32 ASCII letters/digits/_/-')
args = parser.parse_args()
if args.usb_serial and not re.fullmatch(r'[A-Za-z0-9_-]{1,32}',args.usb_serial):
    parser.error('Invalid USB serial')
build_env = os.environ.copy()
build_env.pop('RV1103_USB_SERIAL',None)
if args.usb_serial: build_env['RV1103_USB_SERIAL']=args.usb_serial
features=set(args.features.split(','))
if 'app-ui' in features:
    features.update({'native-ui','mini-pcb-ui'})
if 'mini-pcb-ui' in features:
    features.add('bench-ui')
if 'native-ui' in features:
    features.update({'usb-console','native-hashes','native-unicode'})
if features & {'native-hashes','native-unicode'}:
    features.add('usb-console')
if 'bench-ui' in features:
    features.add('usb-only')
if 'usb-only' in features:
    features.add('usb-console')
if 'usb-console' in features:
    features.add('app-runtime')
if 'app-runtime' in features:
    features.add('fast-boot')
if 'fast-boot' in features:
    features.add('runtime-board')
runtime_info={}
if 'native-ui' in features:
    subprocess.run(['mise','run','baremetal:ui:library:build'],cwd=ROOT.parent,check=True)
    subprocess.run(['uv','run','--python','3.13','python',str(ROOT/'tools/build_qr.py')],check=True)
    subprocess.run(['uv','run','--python','3.13','python',str(ROOT/'tools/build_regex.py')],check=True)
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
    subprocess.run(argv, cwd=cwd, check=True, env=build_env)
if features & {'runtime-repl','runtime-board'}:
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT/'.tools/micropython',text=True).strip()
    if revision!='78ff170de9e32c79db6e64d3e33d2bd60002bdcd':
        raise SystemExit('Unexpected MicroPython revision; see PHASE-9-RUNTIME.md')
    lib=ROOT/'.tools/micropython/lib/micropython-lib'
    if not (lib/'README.md').exists():
        run(['git','submodule','update','--init','--depth','1','lib/micropython-lib'],cwd=ROOT/'.tools/micropython')
    lib_revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=lib,text=True).strip()
    if lib_revision!='6ae440a8a144233e6e703f6759b7e7a0afaa37a4':
        raise SystemExit('Unexpected pinned MicroPython library revision')
    run(['uv','run','--python','3.13','make','-C',str(ROOT/'.tools/micropython/mpy-cross'),'-j4'])
    run(['uv','run','--python','3.13','make','-C',str(ROOT/'micropython'),'-j4',
         'BOARD_BINDINGS='+('1' if 'runtime-board' in features else '0'),
         'NATIVE_UI='+('1' if 'native-ui' in features else '0')])
    archive=ROOT/'build'/('micropython-ui' if 'native-ui' in features else 'micropython-board' if 'runtime-board' in features else 'micropython')/'libmicropython.a'
    runtime_info={'micropythonRevision':revision,'micropythonLibRevision':lib_revision,
                  'mpyCrossSha256':hashlib.sha256((ROOT/'.tools/micropython/mpy-cross/build/mpy-cross').read_bytes()).hexdigest(),'archiveSha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
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
    'entryAddress':'0x00000000', 'stackTop':('0x01c00000' if 'native-ui' in features else '0x00400000'),
    'features': args.features,
    'note':('Native UI memory layout requires its own Phase12 gate; excludes cold-power/app timing.' if 'native-ui' in features else 'Entry and stack proven by Phase 2 ten-run gate; added features require their own DUT proof.'),
    'files':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
             for p in [raw, build/'hello-download.bin', ROOT/'link.ld', ROOT/'link-ui.ld', ROOT/'Cargo.toml', ROOT/'Cargo.lock', ROOT/'build.rs', ROOT/'.cargo/config.toml', *sorted((ROOT/'src').rglob('*.rs')), *sorted((ROOT/'micropython').glob('*')), *sorted((ROOT/'app').rglob('*.py')), *([ROOT/'hash-core/Cargo.toml',*sorted((ROOT/'hash-core/src').rglob('*.rs'))] if 'native-hashes' in features else []), *inputs] if p.is_file()},
    'algorithmSources': {str(p.relative_to(ROOT.parent)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in [ROOT.parent/'firmware/rkaiq-rs/Cargo.toml', *sorted((ROOT.parent/'firmware/rkaiq-rs/src').glob('*.rs'))]} if 'isp' in args.features or 'runtime-board' in features else {},
    'runtime':runtime_info,
    'nativeHashes':{'core':'hash-core','dependencyLockSha256':hashlib.sha256((ROOT/'Cargo.lock').read_bytes()).hexdigest(),'preparedLibraries':json.loads((ROOT/'app/hash-libs-provenance.json').read_text()),'note':'Streaming hashes, HMAC and service-aware PBKDF2 prerequisites; not full seed/wallet qualification'} if 'native-hashes' in features else None,
    'nativeMnemonic':{'shamir':json.loads((ROOT/'app/shamir-provenance.json').read_text()),'aezeed':json.loads((ROOT/'app/aezeed-provenance.json').read_text())} if 'native-ui' in features else None,
    'nativeEmbitModels':json.loads((ROOT/'app/embit-models-provenance.json').read_text()) if 'native-ui' in features else None,
    'nativePsbtFraming':json.loads((ROOT/'app/psbt-framing-provenance.json').read_text()) if 'native-ui' in features else None,
    'nativeBip39':json.loads((ROOT/'app/bip39-provenance.json').read_text()) if 'native-ui' in features else None,
    'nativeUnicode':json.loads((ROOT/'unicode/provenance.json').read_text()) if 'native-unicode' in features else None,
    'nativeRegex':json.loads((ROOT/'build/regex/manifest.json').read_text()) if 'native-ui' in features else None,
    'nativeQr':json.loads((ROOT/'build/qr/manifest.json').read_text()) if 'native-ui' in features else None,
    'nativeUi':json.loads((ROOT/'build/ui/manifest.json').read_text()) if 'native-ui' in features else None,
    'usbSerial':(args.usb_serial or 'rv1103-dev-001') if 'usb-console' in features else None,
},indent=2)+'\n')
print('Built',build/'hello-download.bin')
