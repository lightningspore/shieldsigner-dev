# SPDX-License-Identifier: MIT
"""Summarize an existing REF Rust AE/AWB capture without asserting convergence."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

def objects(text):
    decoder=json.JSONDecoder();position=0
    while position<len(text):
        while position<len(text) and text[position].isspace():position+=1
        try:value,end=decoder.raw_decode(text,position)
        except ValueError:
            end=text.find('\n',position);position=len(text) if end<0 else end+1
            continue
        position=end
        if isinstance(value,dict):yield value

def summarize(log,prefix):
    records=list(objects(log.read_text()));events=[record for record in records if 'event' in record]
    def unique(name):
        found=[event for event in events if event['event']==name]
        if len(found)!=1:raise ValueError('Missing/duplicate event '+name)
        return found[0]
    final=unique('first-frame-finished');ae=unique('automatic-ae-finished');awb=unique('automatic-awb-finished')
    bridge=unique('raw-bridge-finished');statistics=[e for e in events if e['event']=='automatic-ae-statistics']
    if not final.get('success') or final.get('error') is not None or not ae.get('success') or ae.get('error') is not None:raise ValueError('Unsuccessful capture')
    image=prefix.read_bytes();metadata=json.loads(Path(str(prefix)+'.json').read_text())
    if metadata['bytes']!=len(image):raise ValueError('Image length mismatch')
    artifacts=[]
    for path in sorted(prefix.parent.glob(prefix.name+'*')):
        if path.is_file():artifacts.append({'file':path.name,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    wanted=['processedStatistics','parameterSubmissions','physicalApplicationVerified','gain','parametersId','isoInput','measurementConfiguration']
    return {'scope':'Linux REF capture only; no DUT ISP or convergence qualification',
        'logSha256':hashlib.sha256(log.read_bytes()).hexdigest(),'eventCounts':dict(Counter(e['event'] for e in events)),
        'imageFormat':metadata['format'],'imageBytes':len(image),'rawCompletedFrames':bridge.get('completedFrames'),
        'rawRecordsDropped':bridge.get('frameRecordsDropped'),'cleanupErrors':bridge.get('cleanupErrors'),
        'ae':{key:ae[key] for key in wanted if key in ae},'awb':{key:awb[key] for key in wanted if key in awb},
        'aeStatistics':{'records':len(statistics),'exactExposureLookup':sum(e.get('exactExposureLookup',False) for e in statistics),
            'ranControl':sum(e.get('run',False) for e in statistics),'decisions':sum(e.get('decision') is not None for e in statistics),
            'first':statistics[0] if statistics else None,'last':statistics[-1] if statistics else None},
        'convergenceVerified':False,'artifacts':artifacts,
        'limitations':['Physical parameter application is not verified by this summary.',
            'Missing exact exposure associations are preserved, not treated as convergence.',
            'Dark/noisy preview does not qualify image quality; optional noise modules disabled.']}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('log',type=Path);parser.add_argument('prefix',type=Path);parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args();report=summarize(args.log,args.prefix);args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({key:report[key] for key in ['rawCompletedFrames','rawRecordsDropped','ae','awb','convergenceVerified']}))
