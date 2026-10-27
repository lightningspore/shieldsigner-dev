#!/usr/bin/env python3
"""Persistent native AE -> submission -> SOF -> effective map -> AE composition."""
import copy,hashlib,json,runpy,struct,subprocess,sys,tempfile
from pathlib import Path
from differential import ROOT,BINARY,HEAP
load=lambda name:runpy.run_path(str(Path(__file__).with_name(name)))
Session=load('ae-session.py')['Original'];Translator=load('ae-linear-translation.py')['OriginalLinear'];Association=load('exposure-association.py')['Original'];Sensor=load('sensor-submission.py')['Original']
def sensor_state(sensor):
 current=struct.unpack('<I',sensor.uc.mem_read(HEAP+0x258,4))[0]
 return dict(pending=sensor.pending(),current=sensor.exposure(current),effective=[dict(frame=k,record=sensor.exposure(v)) for k,v in sorted(sensor.map.items())])
def main():
 manifest=json.loads((ROOT/'reverse-engineering/rkaiq/artifacts.json').read_text());binary_sha=hashlib.sha256(BINARY.read_bytes()).hexdigest();assert binary_sha==manifest['binaries'][0]['sha256']
 iq=ROOT/'.tools/reverse-engineering/iqfiles/sc3336_CMK-OT2119-PC1_30IRC-F16.json';iq_bytes=iq.read_bytes();assert hashlib.sha256(iq_bytes).hexdigest()=='8c816c0f83c6d4d951d5d4335e9c63a0893cd4f99c501f3f3558bbbca9d2c94a';profile=json.loads(iq_bytes)
 runtime=ROOT/'.tools/reverse-engineering/uclibc-runtime/libuClibc-1.0.31.so';assert hashlib.sha256(runtime.read_bytes()).hexdigest()==manifest['uclibcRuntime']['memberSha256']
 with tempfile.TemporaryDirectory() as d:
  file=Path(d)/'params.bin';subprocess.run([str(ROOT/'firmware/rkaiq-rs/target/release/camera-probe'),'make-initial-parameters',str(iq),str(file),'--ae-measurements'],capture_output=True,check=True);initial=file.read_bytes()
 changed=bytearray(initial);struct.pack_into('<4H',changed,0x1225,256,384,512,640);parameters={0:initial,3:bytes(changed)}
 cases=[];expected=[];counts=dict(statistics=0,invalid=0,missing_parameters=0,sofs=0,writes=0,write_failures=0,exact=0,fallback=0)
 translator=Translator();lookup=Association()
 for k in range(4):
  p=copy.deepcopy(profile);ae=p['main_scene'][0]['sub_scene'][0]['scene_isp32']['ae_calib'];ae['LinearAeCtrl']['InitExp']['InitTimeValue']=[.003,.005][k%2];ae['CommCtrl']['AecSpeed']['SmoothEn']=0 if k==3 else 1
  delay=[0,1,2,2][k];p['sensor_calib']['CISExpUpdate']['Linear'].update(time_update=delay,gain_update=delay)
  native=Session();native.prepare(dict(profile=p,frame=1360,width=2304,height=1296));sensor=Sensor();sensor.seed(bytes.fromhex(native.snapshot()['previous']));sensor.uc.mem_write(HEAP+0x274,struct.pack('<i',delay))
  v=dict(profile=p,initial=native.snapshot()['previous'],parameters=[dict(id=n,bytes=b.hex()) for n,b in parameters.items()],events=[]);results=[dict(kind='initial',state=native.snapshot(),sensor=sensor_state(sensor))]
  def sof(frame,fail):
   sensor.fail=fail;v['events'].append(dict(kind='sof',frame=frame,fail=fail));state=sensor.sof(frame);results.append(dict(kind='sof',sensor=state,state=native.snapshot()));counts['sofs']+=1
   if state['written'] is not None:counts['writes']+=1
   if state['status']!=0:counts['write_failures']+=1
  for frame in range(16):
   if not (k%2 and frame==1):sof(frame,2 if k>=2 and frame in [5,9] else 0)
   if k==2 and frame==8:sof(frame,0)
   raw=bytearray(13040);level=[45,45,3,0,120,240,45,45][(frame+k)%8]
   for j in range(225):
    value=min(255,level+j%3);struct.pack_into('<I',raw,0x390+j*4,(value*4095//255)|((value*1023//255)<<12)|((value*1023//255)<<22))
   struct.pack_into('<I',raw,0x1400+level*4,1000);flags=0x5d80 if frame!=4 else 1<<8;parameter_id=99 if frame==7 else [0,0,3,3][frame%4];struct.pack_into('<3I',raw,0x32e0,flags,frame,parameter_id)
   v['events'].append(dict(kind='stats',raw=raw.hex()))
   if flags&((1<<8)|(1<<12))!=((1<<8)|(1<<12)):
    result=dict(kind='stats',status='no-measurement');counts['invalid']+=1
   elif parameter_id not in parameters:
    result=dict(kind='stats',status='error',error=f'Missing parameter snapshot {parameter_id}');counts['missing_parameters']+=1
   else:
    keys=sorted(sensor.map);status,identity=map(int,lookup.run(dict(frames=keys,requested=frame)).split(','));selected=keys[identity-10];record=sensor.exposure(sensor.map[selected]);exact=selected==frame
    translated=translator.translate(bytes(raw),parameters[parameter_id]);assert translated!='invalid';body=bytearray(translator.uc.mem_read(HEAP+0x40008,0x2ff8))+bytearray(8);mean=struct.unpack_from('<H',body,0x2e20)[0];body[0x2e28:0x2e28+244]=bytes.fromhex(record)
    native.uc.mem_write(HEAP+0x1d0000,bytes(body));native.wrappers(frame,False,HEAP+0x1d0000)
    count=struct.unpack('<I',native.uc.mem_read(HEAP+0x1e3014,4))[0];records=[bytes(native.uc.mem_read(HEAP+0x1e3018+244*i,244)).hex() for i in range(count)]
    sensor.submit(native.snapshot()['previous'],records)
    result=dict(kind='stats',status='processed',selected_frame=selected,exact=exact,mean=mean);counts['statistics']+=1;counts['exact' if exact else 'fallback']+=1
   result.update(state=native.snapshot(),sensor=sensor_state(sensor));results.append(result)
  for frame in range(16,19):sof(frame,0)
  cases.append(v);expected.append(results);print(f'Native AE runtime {k+1}: {len(v["events"])} events',file=sys.stderr,flush=True)
 inputs=''.join('ae-runtime '+json.dumps(v,separators=(',',':'))+'\n' for v in cases);(ROOT/'dist/reverse-engineering/ae-runtime-replay.json').write_text(json.dumps(dict(inputs=inputs,expected=expected)))
 def compare(command):
  r=subprocess.run(command,input=inputs,text=True,capture_output=True)
  if r.returncode:raise RuntimeError(r.stderr)
  actual=[json.loads(line) for line in r.stdout.splitlines()];assert len(actual)==len(expected)
  def difference(a,b,path):
   if a==b:return None
   if isinstance(a,dict) and isinstance(b,dict):
    for k in a:
     d=difference(a[k],b.get(k),path+[k])
     if d:return d
   elif isinstance(a,list) and isinstance(b,list):
    if len(a)!=len(b):return path+['length',len(a),len(b)]
    for i,(x,y) in enumerate(zip(a,b)):
     d=difference(x,y,path+[i])
     if d:return d
   else:return path+[str(a)[:80],str(b)[:80]]
  for i,(a,b) in enumerate(zip(expected,actual)):assert a==b,difference(a,b,[i])
 compare([str(ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture')])
 if '--arm' in sys.argv:
  directory=ROOT/'firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release';compare(['docker','run','--rm','-i','--platform','linux/arm/v7','--network=none','--mount',f'type=bind,src={directory},dst=/bincheck,readonly','alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd','/bincheck/numeric-fixture'])
 report=dict(binarySha256=binary_sha,profileSha256=hashlib.sha256(iq_bytes).hexdigest(),runtimeSha256=manifest['uclibcRuntime']['memberSha256'],sequences=len(cases),events=sum(len(v['events']) for v in cases),counts=counts,mismatches=0,armReplayPassed='--arm' in sys.argv,scope='Persistent ordinary AE runtime composition: raw translation and native lookup use the native SOF-produced exposure map; complete AE wrappers submit native publication records into native batch replacement, SOF and isolated sensor-writer bodies.',limitations=['Independent emulators exchange explicit record bytes across recovered object interfaces; C++ object ownership/containers, translator access/run gating, device reads/ioctls, DPCC and logs retain documented harness boundaries.','Initial effective exposure is explicitly seeded after AE initial publication; startup immediate sensor programming remains external.','Declared profile delays drive scheduling keys. Synthetic raw scenes do not model optical feedback; reported failed writes remain in the native effective map and do not prove physical application.','Fixed-rate ordinary linear source-1 profile subset; live event collection, parameter accumulation, ISP gain updates, reconfiguration, AWB and physical latency qualification remain incomplete.'])
 (ROOT/'reverse-engineering/rkaiq/ae-runtime-equivalence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
