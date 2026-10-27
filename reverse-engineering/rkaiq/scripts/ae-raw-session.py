#!/usr/bin/env python3
"""Join native ISP translation, effective-exposure lookup and full AE wrappers."""
import copy,hashlib,json,runpy,struct,subprocess,sys,tempfile
from pathlib import Path
from differential import ROOT,BINARY,HEAP
load=lambda name:runpy.run_path(str(Path(__file__).with_name(name)))
Session=load('ae-session.py')['Original'];Translator=load('ae-linear-translation.py')['OriginalLinear'];Association=load('exposure-association.py')['Original']

def main():
 manifest=json.loads((ROOT/'reverse-engineering/rkaiq/artifacts.json').read_text());binary_sha=hashlib.sha256(BINARY.read_bytes()).hexdigest();assert binary_sha==manifest['binaries'][0]['sha256']
 iq=ROOT/'.tools/reverse-engineering/iqfiles/sc3336_CMK-OT2119-PC1_30IRC-F16.json';raw_iq=iq.read_bytes();profile=json.loads(raw_iq);assert hashlib.sha256(raw_iq).hexdigest()=='8c816c0f83c6d4d951d5d4335e9c63a0893cd4f99c501f3f3558bbbca9d2c94a'
 runtime=ROOT/'.tools/reverse-engineering/uclibc-runtime/libuClibc-1.0.31.so';assert hashlib.sha256(runtime.read_bytes()).hexdigest()==manifest['uclibcRuntime']['memberSha256']
 with tempfile.TemporaryDirectory() as d:
  path=Path(d)/'params.bin';subprocess.run([str(ROOT/'firmware/rkaiq-rs/target/release/camera-probe'),'make-initial-parameters',str(iq),str(path),'--ae-measurements'],capture_output=True,check=True);initial=path.read_bytes()
 alternate=bytearray(initial);struct.pack_into('<4H',alternate,0x1225,256,384,512,640)
 snapshots={0:initial,3:bytes(alternate)};cases=[];expected=[];counts=dict(valid=0,invalid_measurements=0,missing_parameters=0,missing_exposure=0,changed_timing=0,exact=0,fallback=0,control_runs=0,control_skips=0)
 translator=Translator();association=Association()
 for k in range(4):
  p=copy.deepcopy(profile);ae=p['main_scene'][0]['sub_scene'][0]['scene_isp32']['ae_calib'];ae['LinearAeCtrl']['InitExp']['InitTimeValue']=[.003,.005][k%2];ae['CommCtrl']['AecSpeed']['SmoothEn']=0 if k==3 else 1
  v=dict(profile=p,frame=1360,width=2304,height=1296,parameters=[dict(id=n,bytes=b.hex()) for n,b in snapshots.items()],frames=[])
  native=Session();native.prepare(v);results=[dict(status='initial',state=native.snapshot())];effects={0:bytes.fromhex(native.snapshot()['previous'])}
  for frame in range(16):
   raw=bytearray(13040);level=[45,45,3,0,120,240,45,45][(frame+k)%8]
   for j in range(225):
    value=min(255,level+j%3);packed=(value*4095//255)|((value*1023//255)<<12)|((value*1023//255)<<22);struct.pack_into('<I',raw,0x390+j*4,packed)
   struct.pack_into('<I',raw,0x1400+level*4,1000)
   flags=0x5d80 if frame!=4 else 1<<8;parameter_id=99 if frame==7 else [0,0,3,3][frame%4]
   struct.pack_into('<3I',raw,0x32e0,flags,frame,parameter_id)
   entries=[] if frame==10 else [dict(frame=n,record=b.hex()) for n,b in sorted(effects.items())]
   v['frames'].append(dict(raw=raw.hex(),effective=entries))
   if flags&((1<<8)|(1<<12))!=((1<<8)|(1<<12)):
    counts['invalid_measurements']+=1;results.append(dict(status='no-measurement',state=native.snapshot()));continue
   if parameter_id not in snapshots:
    counts['missing_parameters']+=1;results.append(dict(status='error',error=f'Missing parameter snapshot {parameter_id}',state=native.snapshot()));continue
   if not entries:
    counts['missing_exposure']+=1;results.append(dict(status='error',error='No effective exposure records',state=native.snapshot()));continue
   # Native map lookup returns a controlled payload identity (10 + node index).
   selected=association.run(dict(frames=[e['frame'] for e in entries],requested=frame));status,payload=map(int,selected.split(','));index=payload-10;assert 0<=index<len(entries)
   chosen=entries[index];exact=chosen['frame']==frame;counts['exact' if exact else 'fallback']+=1
   result=translator.translate(bytes(raw),snapshots[parameter_id]);assert result!='invalid'
   body=bytearray(translator.uc.mem_read(HEAP+0x40008,0x2ff8))+bytearray(8)
   means=list(struct.unpack_from('<4H',body,0x2e20));assert means==[int(result.split(':')[0]),0,0,0],means
   body[0x2e28:0x2e28+244]=bytes.fromhex(chosen['record'])
   native.uc.mem_write(HEAP+0x1d0000,bytes(body));native.wrappers(frame,False,HEAP+0x1d0000)
   counts['valid']+=1;counts['control_runs' if native.uc.mem_read(native.engine+0x22ed,1)[0] else 'control_skips']+=1
   results.append(dict(status='processed',frame=frame,parameters=parameter_id,exposure_frame=chosen['frame'],exact=exact,mean=means[0],state=native.snapshot()))
   effects[frame+2]=bytes.fromhex(native.snapshot()['previous'])
  # Fixed-timing binding must not silently reinterpret a VBLANK/timing change.
  changed=bytearray(native.exposure());struct.pack_into('<I',changed,232,1361)
  raw=bytearray(raw);struct.pack_into('<3I',raw,0x32e0,0x5d80,16,0)
  v['frames'].append(dict(raw=raw.hex(),effective=[dict(frame=16,record=changed.hex())]))
  counts['changed_timing']+=1;results.append(dict(status='error',error='Incomplete or changed exposure timing; reconfigure the session',state=native.snapshot()))
  cases.append(v);expected.append(results);print(f'Raw native session {k+1}: {len(v["frames"])} input buffers',file=sys.stderr,flush=True)
 inputs=''.join('ae-raw-session '+json.dumps(v,separators=(',',':'))+'\n' for v in cases)
 (ROOT/'dist/reverse-engineering/ae-raw-session-replay.json').write_text(json.dumps(dict(inputs=inputs,expected=expected)))
 def compare(command):
  r=subprocess.run(command,input=inputs,text=True,capture_output=True)
  if r.returncode:raise RuntimeError(r.stderr)
  actual=[json.loads(line) for line in r.stdout.splitlines()];assert len(actual)==len(expected)
  for i,(a,b) in enumerate(zip(expected,actual)):
   assert len(a)==len(b)
   for j,(x,y) in enumerate(zip(a,b)):
    if x!=y:
     if x.get('state')!=y.get('state'):
      for key in x['state']:
       if x['state'][key]!=y['state'][key]:
        aa=x['state'][key];bb=y['state'][key]
        if isinstance(aa,str):aa,bb=bytes.fromhex(aa),bytes.fromhex(bb)
        raise AssertionError((i,j,key,[(n,u,v) for n,(u,v) in enumerate(zip(aa,bb)) if u!=v][:16]))
     raise AssertionError((i,j,{k:v for k,v in x.items() if k!='state'},{k:v for k,v in y.items() if k!='state'}))
 compare([str(ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture')])
 if '--arm' in sys.argv:
  directory=ROOT/'firmware/rkaiq-rs/target/armv7-unknown-linux-musleabihf/release'
  compare(['docker','run','--rm','-i','--platform','linux/arm/v7','--network=none','--mount',f'type=bind,src={directory},dst=/bincheck,readonly','alpine@sha256:ee16d92f96db08d9d2d07da48555a27f3a69d8f0759021dbc601195ed0d2b5bd','/bincheck/numeric-fixture'])
 report=dict(binarySha256=binary_sha,runtimeSha256=manifest['uclibcRuntime']['memberSha256'],profileSha256=hashlib.sha256(raw_iq).hexdigest(),sequences=4,buffers=sum(len(v['frames']) for v in cases),counts=counts,mismatches=0,armReplayPassed='--arm' in sys.argv,scope='Native source-1 ISP32 translation, native effective-exposure lookup and complete SDK AE wrappers versus Rust raw-statistics session entry point; persistent state snapshots compared.',limitations=['Translator object access/run flag/single-ISP predicate and native map ownership/container boundaries remain explicit inherited harness models. Native grid/histogram, map lookup and AE bodies execute.','Parameter snapshot ID validation/lookup and rejection of missing metadata or changed exposure timing are Rust integration policies, not newly recovered vendor parameter-cache/reconfiguration behavior. Parameter snapshots must contain complete accumulated state.','Exposure maps contain explicit predicted effective-frame entries; the two-frame example delay is test input, not measured physical latency.','Source-1/full-range/fixed-rate/ordinary-linear profile subset only. Additional AE modes, live parameter accumulation, SOF coordination, sensor/ISP writes, AWB and physical association remain unfinished.'])
 (ROOT/'reverse-engineering/rkaiq/ae-raw-session-equivalence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
