#!/usr/bin/env python3
"""Compare JSON demosaic ISO selection through hardware/kernel conversion to ARM."""
import argparse,copy,hashlib,json,math,random,re,runpy,struct,subprocess
from pathlib import Path
from differential import ROOT,BINARY,HEAP,f32
OriginalDemosaic=runpy.run_path(str(Path(__file__).with_name('isp-demosaic.py')))['OriginalDemosaic']
TYPES={'float':('f',4),'int':('i',4),'bool':('B',1),'unsigned char':('B',1),'unsigned short':('H',2)}
GROUPS=[('CalibDbV2_Debayer_GInterp_t','g_interp'),('CalibDbV2_Debayer_GDirectWgt_t','g_drctwgt'),('CalibDbV2_Debayer_GFilter_t','g_filter'),('CalibDbV2_Debayer_CFilter_t','c_filter')]
def schema(header):
 header=re.sub(r'//[^\n]*|/\*.*?\*/','',header,flags=re.S);out={}
 for body,name in re.findall(r'typedef struct CalibDbV2_Debayer_\w+ \{(.*?)\}\s*(CalibDbV2_Debayer_\w+_t);',header,re.S):
  fields=[]
  for kind,key,count in re.findall(r'(unsigned char|unsigned short|float|int|bool|CalibDbV2_\w+_t)\s+(\w+)\s*(?:\[([^]]+)\])?;',body):
   fields.append((kind,key,13 if count=='DEBAYER_ISO_STEP_MAX' else int(count or 1)))
  out[name]=fields
 return out
def pack_record(schemas,name,value):
 out=bytearray()
 for kind,key,count in schemas[name]:
  size=TYPES[kind][1] if kind in TYPES else 4;out.extend(bytes((-len(out))%size))
  if kind in TYPES:
   data=value[key] if count!=1 else [value[key]]
   out.extend(struct.pack('<'+TYPES[kind][0]*count,*data))
  else:out.extend(pack_record(schemas,kind,value[key]))
 out.extend(bytes((-len(out))%4));return bytes(out)
class OriginalSelection(OriginalDemosaic):
 def run_selected(self,v,calibration):
  context=HEAP;self.uc.mem_write(context,bytes([0x55])*0x600);self.uc.mem_write(context+8,struct.pack('<i',2));self.uc.mem_write(context+0x7c,calibration);self.uc.mem_write(context+0x444,bytes.fromhex(v['previous']));before=bytes(self.uc.mem_read(context,0x600))
  assert self.invoke('_Z15AdebayerProcessP17AdebayerContext_si',[context,v['iso']])==0
  after=bytearray(self.uc.mem_read(context,0x600));selected=bytes(after[0x444:0x4c8]);after[0x444:0x4c8]=before[0x444:0x4c8];assert bytes(after)==before,'Unexpected context mutation'
  # Process preserves hardware/cache and calibration storage. The separately
  # verified converter consumes only the selected record and prior cache.
  converted=super().run(dict(kind='quantize',seed=v['seed'],hardware=v['hardware'],selected=selected.hex()))
  return selected.hex()+':'+converted
def main():
 p=argparse.ArgumentParser();p.add_argument('--cases',type=int,default=1000);p.add_argument('--emit-dir',type=Path);a=p.parse_args()
 manifest=json.loads((ROOT/'reverse-engineering/rkaiq/artifacts.json').read_text());source=manifest['iqFiles'][0];iqpath=ROOT/'.tools/reverse-engineering/iqfiles'/source['name'];assert hashlib.sha256(iqpath.read_bytes()).hexdigest()==source['sha256']
 item=next(x for x in manifest['headers'] if x['name']=='debayer_head.h');header=ROOT/'.tools/reverse-engineering/headers'/item['name'];assert hashlib.sha256(header.read_bytes()).hexdigest()==item['sha256'];schemas=schema(header.read_text())
 iq=json.loads(iqpath.read_text());profile=iq['main_scene'][0]['sub_scene'][0]['scene_isp32']['debayer_v2']['param'];assert len(pack_record(schemas,'CalibDbV2_Debayer_Tuning_t',profile))==968
 binary_sha=hashlib.sha256(BINARY.read_bytes()).hexdigest();assert binary_sha==next(x['sha256'] for x in manifest['binaries'] if x['name']==BINARY.name)
 from exposure import RUNTIME
 runtime_sha=hashlib.sha256(RUNTIME.read_bytes()).hexdigest();assert runtime_sha==manifest['uclibcRuntime']['memberSha256']
 arm=OriginalSelection();rng=random.Random(0x4953444d);inputs=[];expected=[];coverage={};profile_cases=0
 for i in range(a.cases):
  actual_profile=i>=max(0,a.cases-100);param=copy.deepcopy(profile)
  if not actual_profile:
   param['debayer_en']=i//2%2
   for key,count in [('lowfreq_filter1',4),('highfreq_filter2',4),('c_alpha_gaus_coe',3),('c_guid_gaus_coe',3),('c_ce_gaus_coe',3)]:param[key]=[rng.randrange(-1000,1001) for _ in range(count)]
   for name,key in GROUPS:
    table=param[key];iso=f32(rng.uniform(1,100));knots=[]
    for j in range(13):knots.append(iso);iso=f32(iso+rng.choice([1.1,5.5,10.75,50.5,100.25]))
    table['iso']=knots
    for kind,field,count in schemas[name]:
     if field=='iso':continue
     if kind=='unsigned char':table[field]=[rng.randrange(256) for _ in range(13)]
     elif kind=='unsigned short':table[field]=[rng.randrange(65536) for _ in range(13)]
     else:
      low,high=(.02,2.) if field=='debayer_cfilter_str' else (.1,16.) if field=='debayer_wgtslope' else (.001,1.) if field=='debayer_bf_sgm' else (-.1,15.) if field=='debayer_wet_clip' else (-.1,1.) if field=='debayer_wet_ghost' else (-10.,100.)
      table[field]=[f32(rng.uniform(low,high)) for _ in range(13)]
  else:profile_cases+=1
  knots=param[GROUPS[i%4][1]]['iso'];j=i//4%13
  iso=[-1,math.floor(knots[0])-1,math.floor(knots[j]),math.ceil(knots[j]),math.ceil(knots[-1])+1,rng.randrange(0,math.ceil(knots[-1])+2)][i//52%6]
  if actual_profile:
   profile_knots=param['g_interp']['iso'];points=[-1,0]
   for j,knot in enumerate(profile_knots):
    points.extend([int(knot)-1,int(knot),int(knot)+1])
    if j<12:points.append(int((knot+profile_knots[j+1])/2))
   points.extend([int(profile_knots[-1])+1,2147483647]);iso=points[(profile_cases-1)%len(points)]
  previous=bytearray(rng.randbytes(132));previous[0]=0;hardware=bytearray(rng.randbytes(112));hardware[0]=i%2
  v=dict(calibration=param,iso=iso,previous=previous.hex(),hardware=hardware.hex(),seed=rng.randrange(0xffffffff))
  inputs.append('demosaic-select '+json.dumps(v,separators=(',',':')));expected.append(arm.run_selected(v,pack_record(schemas,'CalibDbV2_Debayer_Tuning_t',param)))
  for _,key in GROUPS:
   high=next((j for j,x in enumerate(param[key]['iso']) if f32(iso)<x),13);position=f'{"sdk" if actual_profile else "synthetic"}:{key}:{high}';coverage[position]=coverage.get(position,0)+1
 actual=subprocess.run([str(ROOT/'firmware/rkaiq-rs/target/release/numeric-fixture')],input='\n'.join(inputs)+'\n',text=True,capture_output=True,check=True).stdout.splitlines();assert len(actual)==len(expected)
 mismatches=[dict(case=i,input=inputs[i],expected=x,actual=y) for i,(x,y) in enumerate(zip(expected,actual)) if x!=y]
 report=dict(binarySha256=binary_sha,runtimeSha256=runtime_sha,iqFile=source['name'],iqSha256=source['sha256'],scenePointer='/main_scene/0/sub_scene/0/scene_isp32/debayer_v2/param',seed='0x4953444d',cases=a.cases,sdkProfileCases=profile_cases,mismatchCount=len(mismatches),inputIsoCoverage=coverage,nativeRuntimeFunctions=sorted(arm.math_calls),nativeRuntimeImportedCalls=sorted(set(arm.math.calls)),scope='Explicit-scene demosaic JSON loader, native automatic Process/SelectParam, selected-value quantization and full ISP32 packing; all selected/hardware/cache bytes and masks/block compared',limitations=['Python independently packs the public SDK calibration declaration; native IQ JSON/BIN parsing is not executed.','Checked knots are finite, nonnegative, at most 16777216, and strictly increasing after integer truncation; malformed/degenerate tables are rejected.','Only the automatic processing branch is reconstructed; outer frame/update-state lifecycle and live ISP queues remain unfinished.','The SDK SC3336 profile is a pinned reference, not camera-module/lens qualification.'])
 if mismatches:report['firstMismatches']=mismatches[:3]
 (ROOT/'reverse-engineering/rkaiq/demosaic-selection-equivalence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='inputIsoCoverage'},indent=2));assert not mismatches
 if a.emit_dir:
  a.emit_dir.mkdir(parents=True,exist_ok=True);(a.emit_dir/'inputs.txt').write_text('\n'.join(inputs)+'\n');(a.emit_dir/'expected.txt').write_text('\n'.join(expected)+'\n');(a.emit_dir/'sc3336-demosaic-subset.json').write_text(json.dumps(dict(_source=dict(**source,scenePointer=report['scenePointer']),param=profile),indent=2)+'\n')
if __name__=='__main__':main()
