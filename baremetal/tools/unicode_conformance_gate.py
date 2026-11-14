# SPDX-License-Identifier: MIT
"""Run Unicode15's complete published row corpus through the real DUT API.

One CDC reader, bounded paste chunks, public data only. This checks all20
relations per published row; unlisted-scalar identity is a separate UAX15 rule.
"""
import argparse,datetime,hashlib,json,secrets,struct,time
from pathlib import Path
import serial
from serial.tools import list_ports
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--identity',action='store_true',help='Check all unlisted Unicode scalars instead of published row relations')
args=parser.parse_args()
root=Path(__file__).resolve().parents[1]
source=root/'.tools/unicode-15.0.0/NormalizationTest.txt'
raw=source.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='fb9ac8cc154a80cad6caac9897af55a4e75176af6f4e2bb6edc2bf8b1d57f326'
packed=bytearray();rows=0;part=None;excluded=set()
for line in raw.decode().splitlines():
 line=line.split('#')[0].strip()
 if line.startswith('@'):part=line;continue
 if not line:continue
 if part.startswith('@Part1'):
  value=line.split(';')[0].split();assert len(value)==1;excluded.add(int(value[0],16))
 fields=line.split(';')[:5];assert len(fields)==5
 for field in fields:
  value=''.join(chr(int(c,16)) for c in field.split()).encode()
  packed.extend(struct.pack('>H',len(value)));packed.extend(value)
 rows+=1
assert rows==19074 and len(excluded)==17029
if args.identity:
 packed=bytearray(0x110000//8)
 for c in excluded:packed[c>>3]|=1<<(c&7)
ports=[p for p in list_ports.comports() if (p.vid,p.pid)==(0x1209,0x0003) and p.serial_number=='rv1103-dev-001'];assert len(ports)==1,ports
folder=root/'logs/phase-12'/(('unicode-identity-' if args.identity else 'unicode-conformance-')+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ'));folder.mkdir(parents=True)
report={'serial':'rv1103-dev-001','scope':'Unicode15 published row corpus through actual normalize API; not exhaustive unlisted-scalar identity','datasetSha256':hashlib.sha256(raw).hexdigest(),'rows':rows,'relations':rows*20,'packedBytes':len(packed),'passed':False,'identityMode':args.identity}
if args.identity:report.update(scope='Every Unicode scalar absent from Part1 is identity under all four forms',excludedScalars=17029,scalarChecks=1095035,relations=4380140)
log=open(folder/'serial.bin','wb');token=secrets.token_hex(12)
def run(console,code,tag,timeout=15):
 console.write(b'\x05');received=bytearray();deadline=time.monotonic()+3
 while b'paste mode' not in received:
  block=console.read(4096);received.extend(block);log.write(block)
  if time.monotonic()>deadline:raise TimeoutError('Paste mode not acknowledged')
 marker=('@@UCD_DONE '+token+' '+tag).encode()
 payload=code.encode()+b"\nprint('"+marker+b"')\n\x04"
 for pos in range(0,len(payload),128):
  console.write(payload[pos:pos+128]);block=console.read(console.in_waiting);received.extend(block);log.write(block);time.sleep(.002)
 deadline=time.monotonic()+timeout
 while b'\n'+marker+b'\r\n' not in received:
  block=console.read(4096);received.extend(block);log.write(block)
  execution=bytes(received).split(b'=== \r\n',1)[-1]
  if b'Traceback (most recent call last)' in execution:raise RuntimeError('Device script raised; see serial evidence')
  if time.monotonic()>deadline:raise TimeoutError('No conformance stage marker')
 log.flush()
try:
 with serial.Serial(ports[0].device,115200,timeout=.1,write_timeout=3,exclusive=True) as console:
  console.write(b'\x03\x02\r');time.sleep(.2);console.reset_input_buffer()
  run(console,"import unicodedata as u\nimport binascii\nimport gc\nimport camera\nimport time\nassert u.unidata_version=='15.0.0'\nfixture=bytearray()",'setup')
  chunk=16384
  for pos in range(0,len(packed),chunk):
   run(console,"fixture.extend(binascii.unhexlify('"+packed[pos:pos+chunk].hex()+"'))\ngc.collect()",str(pos))
   report['uploadedBytes']=min(pos+chunk,len(packed));(folder/'progress.json').write_text(json.dumps(report,indent=2)+'\n')
   print('Uploaded',report['uploadedBytes'],'/',len(packed),flush=True)
  code='''assert len(fixture)==697232
baseline=camera.settings()['rust_heap_bytes']
start=time.ticks_ms()
pos=0
cases=0
checks=0
view=memoryview(fixture)
while pos<len(fixture):
    fields=[]
    for j in range(5):
        n=int.from_bytes(view[pos:pos+2],'big')
        pos+=2
        fields.append(bytes(view[pos:pos+n]).decode())
        pos+=n
    a,b,c,d,e=fields
    for form,targets in [('NFC',(b,b,b,d,d)),('NFD',(c,c,c,e,e)),('NFKC',(d,d,d,d,d)),('NFKD',(e,e,e,e,e))]:
        for text,expected in zip(fields,targets):
            if u.normalize(form,text)!=expected:
                print('@@UCD_FAILURE',cases,form)
                raise AssertionError('Unicode normalization relation failed')
            checks+=1
    cases+=1
    if cases%128==0:gc.collect()
assert cases==19074 and checks==381480
assert camera.settings()['rust_heap_bytes']==baseline
print('@@UCD_FULL_ROWS_PASS',cases,checks,(time.ticks_ms()-start)&0xffffffff)
del fixture,view,fields,a,b,c,d,e
for i in range(3):gc.collect()
'''
  if args.identity:
   code="""assert len(fixture)==139264
baseline=camera.settings()['rust_heap_bytes']
start=time.ticks_ms()
checks=0
scalars=0
for cp in range(0x110000):
    if cp%1024==0:gc.collect()
    if 0xd800<=cp<=0xdfff:continue
    if fixture[cp>>3]&(1<<(cp&7)):continue
    text=chr(cp)
    for form in ('NFC','NFD','NFKC','NFKD'):
        if u.normalize(form,text)!=text:
            print('@@UCD_IDENTITY_FAILURE',cp,form)
            raise AssertionError('Unlisted scalar changed')
        checks+=1
    scalars+=1
assert scalars==1095035 and checks==4380140
assert camera.settings()['rust_heap_bytes']==baseline
print('@@UCD_IDENTITY_PASS',scalars,checks,(time.ticks_ms()-start)&0xffffffff)
del fixture
for i in range(3):gc.collect()
"""
  (folder/'check.py').write_text(code)
  run(console,code,'validate',timeout=1800)
  report['passed']=True
except Exception as error:report['error']=str(error)
finally:
 log.close();(folder/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));print('Evidence:',folder)
raise SystemExit(0 if report['passed'] else 1)
