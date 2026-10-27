#!/usr/bin/env python3
"""Strict pinned-header ARM32 profile packer for differential execution.

Pointers are 32-bit emulated addresses. Fixed tables may have a shorter active
JSON prefix; their remaining native storage is explicitly zero-filled.
"""
import re,ctypes,json,struct,hashlib,subprocess
from differential import ROOT
from pathlib import Path
manifest=json.loads((ROOT/'reverse-engineering/rkaiq/artifacts.json').read_text())
HEADER_HASHES={}
for name in ['aec_head.h','sensorinfo_head.h','moduleinfo_head.h','rk_aiq_comm.h']:
 entry=next(x for x in manifest['headers'] if x['name']==name)
 assert hashlib.sha256((ROOT/'.tools/reverse-engineering/headers'/name).read_bytes()).hexdigest()==entry['sha256']
 HEADER_HASHES[name]=entry['sha256']
text=''.join((ROOT/'.tools/reverse-engineering/headers'/name).read_text() for name in ['aec_head.h','sensorinfo_head.h','moduleinfo_head.h']);text=re.sub(r'/\*.*?\*/|//[^\n]*','',text,flags=re.S)
macros={k:int(v) for k,v in re.findall(r'^#define\s+(\w+)\s+\(?(\d+)\)?',text,re.M)}
enums={};values={}
for raw in [text,(ROOT/'.tools/reverse-engineering/headers/rk_aiq_comm.h').read_text()]:
 raw=re.sub(r'/\*.*?\*/|//[^\n]*','',raw,flags=re.S)
 for body,name in re.findall(r'typedef\s+enum\s+\w*\s*\{(.*?)\}\s*(\w+)\s*;',raw,re.S):
  if name not in re.findall(r'}\s*(\w+)\s*;',text) and name not in ['RKAiqOPMode_t','rk_aiq_working_mode_t','rk_aiq_isp_hdr_mode_t','rk_aiq_sensor_hdr_line_mode_t']:continue
  enums[name]=ctypes.c_int32;n=0
  for part in body.split(','):
   part=part.strip()
   if not part:continue
   if '=' in part:
    k,v=map(str.strip,part.split('=',1))
    try:n=int(v,0)
    except ValueError:
     key,increment=re.fullmatch(r'(\w+)\s*\+\s*(\d+)',v).groups();n=values[key]+int(increment)
   else:k=part
   values[k]=n;n+=1
schemas={name:body for body,name in re.findall(r'typedef\s+struct\s+\w+\s*\{(.*?)\}\s*(\w+)\s*;',text,re.S)}
common=(ROOT/'.tools/reverse-engineering/headers/rk_aiq_comm.h').read_text();common=re.sub(r'/\*.*?\*/|//[^\n]*','',common,flags=re.S);schemas.update({name:body for body,name in re.findall(r'typedef\s+struct\s+\w+\s*\{(.*?)\}\s*(\w+)\s*;',common,re.S) if name.startswith('Cam')})
types={'int16_t':ctypes.c_int16,'short':ctypes.c_int16,'bool':ctypes.c_uint8,'uint8_t':ctypes.c_uint8,'uint16_t':ctypes.c_uint16,'uint32_t':ctypes.c_uint32,'int':ctypes.c_int32,'float':ctypes.c_float};types.update(enums);fields={}
def layout(name):
 if name in types:return types[name]
 result=[];metadata=[]
 for declaration in schemas[name].split(';'):
  declaration=declaration.strip()
  if not declaration:continue
  m=re.fullmatch(r'(\w+)\s*(\*)?\s*(\w+)\s*(?:\[(\w+)\])?',declaration);assert m,declaration
  base,ptr,key,count=m.groups();t=ctypes.c_uint32 if ptr else layout(base)
  if count:t=t*int(macros.get(count,count))
  result.append((key,t));metadata.append((base,bool(ptr),key,count))
 t=type(name,(ctypes.Structure,),{'_fields_':result});types[name]=t;fields[name]=metadata;return t
class Packer:
 def __init__(self):self.next=0x2120000;self.blocks=[]
 def pack(self,name,value):
  t=layout(name)
  if name in enums:return struct.pack('<i',values[value] if isinstance(value,str) else value)
  if name in ['int16_t','short','float','int','uint8_t','uint16_t','uint32_t','bool']:
   return bytes(t(value))
  out=bytearray(ctypes.sizeof(t))
  for base,ptr,key,count in fields[name]:
   assert key in value,(name,key)
   x=value[key]
   if ptr:
    assert isinstance(x,list),(name,key)
    if key+'_len' in value:assert value[key+'_len']==len(x),(name,key)
    blob=b''.join(self.pack(base,v) for v in x);pointer=self.next if blob else 0
    if blob:
     self.next+=(len(blob)+3)&~3;assert self.next<=0x2200000,'Profile pointer arena exhausted';self.blocks.append((pointer,blob))
    data=struct.pack('<I',pointer)
   elif count:
    n=int(macros.get(count,count));assert len(x)<=n,(name,key,len(x),n)
    data=b''.join(self.pack(base,v) for v in x)
   else:data=self.pack(base,x)
   o=getattr(t,key).offset;out[o:o+len(data)]=data
  return bytes(out)

def verify_arm_layout():
 layout('CalibDb_Aec_ParaV2_t');layout('CalibDb_Sensor_ParaV2_t');layout('CalibDb_Module_ParaV2_t')
 common_text=(ROOT/'.tools/reverse-engineering/headers/rk_aiq_comm.h').read_text()
 source=['#include <stdint.h>','#include <stdbool.h>','#include <stddef.h>']
 for decl,name in re.findall(r'(typedef\s+enum\s+\w*\s*\{.*?\}\s*(\w+)\s*;)',common_text,re.S):
  if name in ['RKAiqOPMode_t','rk_aiq_working_mode_t','rk_aiq_isp_hdr_mode_t','rk_aiq_sensor_hdr_line_mode_t']:source.append(decl)
 for decl,name in re.findall(r'(typedef\s+struct\s+\w+\s*\{.*?\}\s*(\w+)\s*;)',common_text,re.S):
  if name in fields:source.append(decl)
 for name in ['aec_head.h','sensorinfo_head.h','moduleinfo_head.h']:
  raw=(ROOT/'.tools/reverse-engineering/headers'/name).read_text()
  raw=re.sub(r'^#include[^\n]*','',raw,flags=re.M).replace('RKAIQ_BEGIN_DECLARE','').replace('RKAIQ_END_DECLARE','');source.append(raw)
 assertions=0
 for name in fields:
  t=types[name];source.append(f'_Static_assert(sizeof({name})=={ctypes.sizeof(t)},"{name} size");');assertions+=1
  for _,_,key,_ in fields[name]:source.append(f'_Static_assert(offsetof({name},{key})=={getattr(t,key).offset},"{name}.{key}");');assertions+=1
 output=ROOT/'dist/reverse-engineering/ae-profile-layout.c';output.parent.mkdir(parents=True,exist_ok=True);output.write_text('\n'.join(source)+'\n')
 result=subprocess.run(['mise','exec','zig@0.15.2','--','zig','cc','-target','arm-linux-musleabihf','-std=c11','-c',str(output),'-o',str(output.with_suffix('.o'))],capture_output=True,text=True)
 if result.returncode:raise RuntimeError('ARM SDK layout validation failed:\n'+result.stderr)
 return assertions
