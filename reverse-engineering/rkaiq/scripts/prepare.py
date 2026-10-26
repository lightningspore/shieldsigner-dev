#!/usr/bin/env python3
"""Fetch pinned analysis inputs, preserving vendor originals in ignored cache."""
from pathlib import Path
import argparse,hashlib,json,os,platform,shutil,subprocess,urllib.request,zipfile,tarfile
ROOT=Path(__file__).resolve().parents[3]
manifest=json.loads((ROOT/'reverse-engineering/rkaiq/artifacts.json').read_text())
cache=ROOT/'.tools/reverse-engineering';cache.mkdir(parents=True,exist_ok=True)
def fetch(url,target,sha):
 if not target.exists():
  target.parent.mkdir(parents=True,exist_ok=True)
  temp=target.with_suffix(target.suffix+'.partial')
  print('Downloading',target.name,flush=True)
  request=urllib.request.Request(url,headers={'User-Agent':'ShieldSigner-RKAIQ-research'})
  with urllib.request.urlopen(request,timeout=120) as response,temp.open('wb') as out:shutil.copyfileobj(response,out)
  assert hashlib.sha256(temp.read_bytes()).hexdigest()==sha,'Downloaded artifact hash mismatch'
  temp.rename(target)
 assert hashlib.sha256(target.read_bytes()).hexdigest()==sha,'Cached artifact hash mismatch: '+str(target)
parser=argparse.ArgumentParser();parser.add_argument('--ghidra',action='store_true');args=parser.parse_args()
for item in manifest['binaries']:fetch(item['url'],cache/'rkaiq-original'/item['name'],item['sha256'])
for item in manifest.get('headers',[]):fetch(item['url'],cache/'headers'/item['name'],item['sha256'])
for item in manifest.get('kernelHeaders',[]):fetch(item['url'],cache/'kernel-uapi/linux'/item['name'],item['sha256'])
for item in manifest.get('kernelSources',[]):fetch(item['url'],cache/'kernel-source'/item['name'],item['sha256'])
if 'uclibcRuntime' in manifest:
 info=manifest['uclibcRuntime'];folder=cache/'uclibc-runtime';archive=folder/'lib.tar.bz2'
 fetch(info['archiveUrl'],archive,info['archiveSha256'])
 member=folder/Path(info['member']).name
 if not member.exists():
  with tarfile.open(archive) as tar:
   entry=tar.getmember(info['member']);assert entry.isfile()
   member.write_bytes(tar.extractfile(entry).read())
 assert hashlib.sha256(member.read_bytes()).hexdigest()==info['memberSha256'],'Runtime member hash mismatch'
for item in manifest.get('iqFiles',[]):fetch(item['url'],cache/'iqfiles'/item['name'],item['sha256'])
if args.ghidra:
 info=manifest['ghidra'];archive=cache/'ghidra_12.2.zip';fetch(info['url'],archive,info['sha256']);install=cache/info['directory']
 if not install.exists():
  with zipfile.ZipFile(archive) as zipped:
   for item in zipped.infolist():
    dest=(cache/item.filename).resolve();assert dest.is_relative_to(cache.resolve()),'Unexpected archive path'
   zipped.extractall(cache)
   for item in zipped.infolist():
    mode=item.external_attr>>16;dest=cache/item.filename
    if dest.is_file() and mode&0o111:dest.chmod(mode&0o777)
 system=platform.system();arch=platform.machine()
 native={'Darwin':{'arm64':'mac_arm_64','x86_64':'mac_x86_64'},'Linux':{'x86_64':'linux_x86_64','aarch64':'linux_arm_64'}}.get(system,{}).get(arch)
 if native is None:raise SystemExit('No configured native decompiler build for this host')
 destination=install/'Ghidra/Features/Decompiler/os'/native/'decompile'
 if not destination.exists():
  if system!='Darwin':raise SystemExit('Native Ghidra decompiler absent; install/build matching host tools')
  cpp=install/'Ghidra/Features/Decompiler/src/decompile/cpp'
  subprocess.run(['make','-j'+str(min(os.cpu_count() or 1,8)),'ghidra_opt','ARCH_TYPE=-arch '+arch,'ADDITIONAL_FLAGS=-mmacosx-version-min=11.0 -w','OSDIR='+native],cwd=cpp,check=True)
  destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(cpp/'ghidra_opt',destination);destination.chmod(0o755)
 print('Ghidra ready:',install)
print('Pinned original binaries verified')
