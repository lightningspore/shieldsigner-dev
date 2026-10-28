#!/usr/bin/env python3
"""Collect pinned runtime license files for the camera kit and image bundle."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[3]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
args.output.mkdir(parents=True, exist_ok=True)
files = []


def copy(source, relative):
    target = args.output / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    files.append(relative)


def write(relative, text):
    target = args.output / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text)
    files.append(relative)


copy(ROOT / 'LICENSE', 'ShieldSigner-LICENSE')
zxing = ROOT / '.tools/zxing-cpp-3.1.1'
revision = subprocess.check_output(['git', '-C', str(zxing), 'rev-parse', 'HEAD'], text=True).strip()
assert revision == '287c85df6f961c8efbfb5ffd736cd9457b8b890e'
copy(zxing / 'LICENSE', 'zxing-cpp/LICENSE')
comments = []
for path in sorted((zxing / 'core/src/libzueci').glob('*')):
    if path.suffix not in ('.c', '.h'):
        continue
    for comment in re.findall(r'/\*.*?\*/', path.read_text(), re.S):
        if any(word in comment for word in ('Copyright', 'Permission', 'SPDX-License-Identifier')):
            comments.append(path.name + '\n' + comment + '\n')
write('libzueci/SOURCE-NOTICES.txt', '\n'.join(comments))
write('libzueci/BSD-3-Clause.txt', '''Copyright (C) 2022 gitlost

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice,
   this list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.
3. Neither the name of the copyright holder nor the names of its contributors
   may be used to endorse or promote products derived from this software
   without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
''')
zigroot = Path(subprocess.check_output(['mise', 'where', 'zig@0.15.2'], text=True).strip())
for component in ('libcxx', 'libcxxabi'):
    copy(zigroot / 'lib' / component / 'LICENSE.TXT', component + '/LICENSE.TXT')
copy(zigroot / 'LICENSE', 'zig-runtime/LICENSE')
for name in ('COPYRIGHT', 'COPYRIGHT.txt'):
    path = zigroot / 'lib/libc/musl' / name
    if path.exists():
        copy(path, 'musl/' + name)
sysroot = Path(subprocess.check_output(['mise', 'exec', 'rust@1.93.1', '--', 'rustc', '--print', 'sysroot'], text=True).strip())
for name in ('LICENSE-APACHE', 'LICENSE-MIT', 'COPYRIGHT.html'):
    path = sysroot / 'share/doc/rust' / name
    if path.exists():
        copy(path, 'rust-runtime/' + name)
metadata = json.loads(subprocess.check_output(['mise', 'exec', 'rust@1.93.1', '--', 'cargo', 'metadata', '--locked', '--format-version', '1', '--manifest-path', str(ROOT / 'firmware/rkaiq-rs/Cargo.toml')], text=True))
crates = []
for package in metadata['packages']:
    if package['name'] == 'shieldsigner-rkaiq':
        continue
    names = []
    for path in sorted(Path(package['manifest_path']).parent.iterdir()):
        if path.is_file() and path.name.upper().startswith(('LICENSE', 'LICENCE', 'COPYRIGHT', 'COPYING')):
            name = package['name'] + '-' + package['version'] + '/' + path.name
            copy(path, name)
            names.append(name)
    crates.append({'crate': package['name'], 'version': package['version'],
                   'declaredLicense': package['license'], 'files': names})
write('DEPENDENCIES.json', json.dumps({'zxingVersion': '3.1.1', 'zxingSourceRevision': revision,
      'sourceUrl': 'https://github.com/zxing-cpp/zxing-cpp/tree/' + revision,
      'compiler': 'mise Zig0.15.2 C++20 Cortex-A7/musl and Rust1.93.1', 'crates': crates}, indent=2) + '\n')
manifest = {'kind': 'camera-runtime-notices', 'files': [
    {'name': name, 'sha256': hashlib.sha256((args.output / name).read_bytes()).hexdigest()}
    for name in sorted(files)]}
(args.output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
print(json.dumps({'files': len(files), 'output': str(args.output)}))
