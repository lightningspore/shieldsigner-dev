# SPDX-License-Identifier: MIT
"""Independently audit raw-camera serial evidence; visual qualification is manual."""
import argparse
import hashlib
import json
from pathlib import Path
import re

def audit(path):
    raw=path.read_bytes();text=raw.decode('ascii',errors='replace')
    frames=[dict(index=int(i),status=int(status,16),buffer=int(buffer),intervalUs=int(us))
            for i,status,buffer,us in re.findall(r'@@CAM_FRAME (\d+) status=(0x[0-9a-f]+) buffer=(\d+) us=(\d+)',text)]
    if len(frames)!=10 or [f['index'] for f in frames]!=list(range(10)):raise ValueError('Need exactly10 ordered frames')
    previous=None
    for frame in frames:
        status=frame['status'];buffer=frame['buffer']
        if status&0x0f0f0000 or status&0x300 not in [0x100,0x200]:raise ValueError('Receiver error or multiple completions')
        if buffer not in [0,1] or (status&0x300)!=(0x100<<buffer) or buffer==previous:raise ValueError('Nonalternating DMA slots')
        if frame['index']>0 and not 0<frame['intervalUs']<=1_200_000:raise ValueError('Frame interval/stall')
        previous=buffer
    if '@@FAIL' in text or text.count('@@PASS camera-raw-ten-frames')!=1:raise ValueError('Missing successful firmware checks')
    settings=re.search(r'@@CAM_SETTINGS named-driver exposure_lines=(\d+) vts=(\d+) pattern=(true|false)',text)
    if settings is None:raise ValueError('Missing named-driver settings')
    exposure,vts=int(settings[1]),int(settings[2]);pattern=settings[3]=='true'
    sensor={int(reg,16):int(value,16) for reg,value in re.findall(r'@@CAM_SENSOR_REG (0x[0-9a-f]+) (0x[0-9a-f]+)',text)}
    expected={0x320e:vts>>8,0x320f:vts&255,0x3e00:(exposure>>12)&15,
              0x3e01:(exposure>>4)&255,0x3e02:(exposure&15)<<4}
    if not 0<exposure<=vts-8 or any(sensor.get(reg)!=value for reg,value in expected.items()):raise ValueError('Timing readback mismatch')
    if len(sensor)!=9 or bool(sensor[0x4501]&8)!=pattern:raise ValueError('Sensor pattern/readback mismatch')
    changed=re.search(r'@@CAM_DMA changed_words=(\d+)',text)
    if changed is None or int(changed[1])==0:raise ValueError('Unchanged DMA')
    if text.count('@@RGB_BEGIN 192 108')!=1 or text.count('@@RGB_END')!=1:raise ValueError('Incomplete preview framing')
    return {'scope':'mechanical raw capture only; not a visual/phase qualification',
            'serialSha256':hashlib.sha256(raw).hexdigest(),'frames':frames,'frameCount':len(frames),
            'exposureLines':exposure,'frameLines':vts,'patternEnabled':pattern,
            'sensorReadbacks':{hex(reg):hex(value) for reg,value in sensor.items()},
            'changedWords':int(changed[1]),'mechanicalCapturePassed':True,'visualReviewRequired':True}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('serial',type=Path);parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args();report=audit(args.serial);args.output.write_text(json.dumps(report,indent=2)+'\n')
    print('Audited10 alternating clean frames; pattern enabled:',report['patternEnabled'],'; visual review still required')
