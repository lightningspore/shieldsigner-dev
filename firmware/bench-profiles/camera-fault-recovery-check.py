import sys,os,json,time
from pathlib import Path
sys.path[:0]=['/usr/lib/shieldsigner-camera/python','/opt/src']
os.environ['SHIELDSIGNER_CAMERA_CONFIG']='/usr/lib/shieldsigner-camera/owner.json'
os.environ['SHIELDSIGNER_QR_READER']='/usr/lib/shieldsigner-camera/shieldsigner-qr-reader'
from shieldsigner_integration import install_camera_backend
m=install_camera_backend(Path('/opt/src'));c=m.Camera.get_instance()
def frames(n):
 deadline=time.monotonic()+15
 while c._video_stream.frames_received<n:
  if c._video_stream.error:raise c._video_stream.error
  if time.monotonic()>deadline:raise TimeoutError('Expected camera frames')
  time.sleep(.1)
report={'test':'managed-camera-owner-SIGKILL-and-reopen','imageOrQrSaved':False}
try:
 c.start_video_stream_mode(resolution=(640,480),framerate=6);frames(5)
 s=c._video_stream;s._owner.kill();s._owner.wait(timeout=5)
 try:c.stop_video_stream_mode()
 except RuntimeError as e:report['failureReported']=type(e).__name__
 report['failedReferenceDetached']=c._video_stream is None
 assert report['failedReferenceDetached']
 c.start_video_stream_mode(resolution=(640,480),framerate=6);frames(10)
 report['freshFrames']=c._video_stream.frames_received
 c.stop_video_stream_mode();report['freshStopClean']=c._video_stream is None
 report['success']=report.get('failureReported')=='RuntimeError' and report['freshStopClean']
 print(json.dumps(report),flush=True)
finally:
 if c._video_stream is not None:c.stop_video_stream_mode()
