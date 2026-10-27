#!/usr/bin/env python3
"""Check observed raw/SOF/trigger/statistics IDs; never claim exposure application."""
import argparse,hashlib,json
from pathlib import Path
def check(log,statistics):
 events=[]
 for line in log.read_text().splitlines():
  try:event=json.loads(line)
  except json.JSONDecodeError:continue
  if isinstance(event,dict):events.append(event)
 bridge=next(e for e in events if e.get('event')=='raw-bridge-finished')
 assert bridge['error'] is None and not bridge['cleanupErrors']
 assert bridge['frameRecordsDropped']==0,'Incomplete bounded trace'
 assert any(e.get('event')=='first-frame-finished' and e['success'] for e in events)
 stats=json.loads(statistics.read_text());assert stats['framesReceived']>0 and not stats['cleanupErrors']
 pairs=[]
 for frame in stats['recentFrames']:
  matches=[r for r in bridge['recentFrames'] if r['rawFrameId']==frame['frameId']]
  assert len(matches)==1,('Missing/ambiguous raw frame',frame['frameId'])
  raw=matches[0]
  assert raw['rxCompleted'] and raw['sofMatched']
  assert raw['sofLookupFrameId']==raw['triggerFrameId']==raw['rawFrameId']
  assert raw['sofTimestampNs']>0
  pairs.append(dict(frameId=frame['frameId'],parametersId=frame['parametersId'],rxSequence=raw['rxSequence']))
 assert pairs and len({p['frameId'] for p in pairs})==len(pairs)
 return dict(logSha256=hashlib.sha256(log.read_bytes()).hexdigest(),statisticsSha256=hashlib.sha256(statistics.read_bytes()).hexdigest(),matchedStatisticsFrames=len(pairs),completedRawFrames=bridge['completedFrames'],queuedRawFrames=len(bridge['recentFrames']),sofMatches=bridge['sofMatches'],sofMissing=bridge['sofMissing'],pairs=pairs,frameIdChainObserved=True,frameExposureAssociationVerified=False,limitations=['Observed matching IDs in one fixed-exposure stream; not proof of sensor register application or exposure-change latency.','RX sequence is recorded for comparison and is not used as the frame key.','Only the retained bounded trace is checked; dropped/incomplete traces are rejected.'])
def main():
 p=argparse.ArgumentParser();p.add_argument('log',type=Path);p.add_argument('statistics',type=Path);p.add_argument('--output',type=Path);a=p.parse_args();report=check(a.log,a.statistics)
 if a.output:a.output.write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report,indent=2))
if __name__=='__main__':main()
