"""Reproduce font metadata and audit notice inputs; never assert permission gaps closed."""
import argparse,json,subprocess
from pathlib import Path
from sources import HERE,DIST,LOCK,fetch
from artifact_paths import LVGL_SOURCES,CHECKS
from build_manifest import sha256

def audit(output):
    for name in ('application','screens','language-packs','lvgl'):fetch(name)
    environment=json.loads((HERE/'locale-builder.lock.json').read_text())
    command=['docker','run','--rm','--platform',environment['platform'],'--network','none','--mount',f'type=bind,source={LVGL_SOURCES},target=/inputs,readonly','--mount',f'type=bind,source={HERE/"font_metadata.py"},target=/metadata.py,readonly','--entrypoint','python3',environment['image'],'/metadata.py']
    metadata=json.loads(subprocess.check_output(command,text=True))
    saved=json.loads((HERE/'licenses/font-name-records.json').read_text())
    if metadata!=saved:raise ValueError('Font metadata differs from reviewed notice inventory')
    header=(LVGL_SOURCES/'screens/components/nlohmann_json/include/nlohmann/json.hpp').read_text().splitlines()[:9]
    if not any('SPDX-License-Identifier: MIT' in line for line in header):raise ValueError('Unexpected JSON header license')
    top_level=subprocess.check_output(['git','-C',str(LVGL_SOURCES/'screens'),'ls-tree','--name-only','HEAD'],text=True).splitlines()
    licenses={path.name:dict(sha256=sha256(path),bytes=path.stat().st_size) for path in sorted((HERE/'licenses').iterdir()) if path.is_file()}
    zig=Path(subprocess.check_output(['mise','where','zig@0.15.2'],text=True).strip())
    toolchain_sources={'Zig-MIT.txt':'LICENSE','musl-COPYRIGHT.txt':'lib/libc/musl/COPYRIGHT','libcxx-LICENSE.txt':'lib/libcxx/LICENSE.TXT','libcxxabi-LICENSE.txt':'lib/libcxxabi/LICENSE.TXT','libunwind-LICENSE.txt':'lib/libunwind/LICENSE.TXT'}
    for notice,relative in toolchain_sources.items():
        if sha256(zig/relative)!=licenses[notice]['sha256']:raise ValueError('Compiler runtime notice mismatch: '+notice)
    gaps=['Pinned LVGL screens core has no top-level license grant; obtain applicable permission/terms before claiming redistribution closure.','SeedSigner custom icon font has no embedded copyright/license records; provenance/terms remain to be established.','Original application/OS dependency notices remain the image integration owner; this audits the added LVGL payload only.']
    report=dict(kind='shieldsigner-lvgl-notice-audit',schema=1,sourcePins=LOCK,fontMetadataToolSha256=sha256(HERE/'font_metadata.py'),fontMetadataEnvironment=environment,fontFiles=len(metadata),fontMetadataReproduced=True,zigVersion='0.15.2',toolchainNoticeSources=toolchain_sources,jsonHeaderNotice=header,screenTopLevelFiles=top_level,notices=licenses,licenseClosureVerified=False,gaps=gaps)
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    return dict(fontFiles=len(metadata),fontMetadataReproduced=True,noticeFiles=len(licenses),licenseClosureVerified=False,output=str(output))

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,default=CHECKS/'lvgl/licenses/notice-audit.json');args=parser.parse_args()
    print(json.dumps(audit(args.output),indent=2))
if __name__=='__main__':main()
