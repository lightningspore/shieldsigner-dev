"""Private guarded Camera + existing Rust stream; metadata only, no saved pixels."""
import json,os,sys,time
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parent),'/opt/src','/usr/lib/shieldsigner-camera/python']
from guards import verify
from resources import process_snapshot,system_snapshot
verify('/opt/src',Path(__file__).parent/'source-guards.json')
from entropy_camera import create,start
os.environ['SHIELDSIGNER_FRONTEND_BACKEND']='rust'
os.environ['SHIELDSIGNER_SMALL_RAM']='1'
camera=create();checks=[]
try:
    for cycle in range(2):
        started=time.monotonic();stream=None
        try:
            start(camera);stream=camera._video_stream
            image=None;deadline=time.monotonic()+20
            while image is None and time.monotonic()<deadline:image=camera.read_video_stream(as_image=True)
            assert image is not None and image.mode=='RGB'
            assert image.size in ((640,480),(480,640))
            preview=camera.read_video_stream(as_image=True,preview=True)
            assert preview is not None and preview.mode=='RGB'
            checks.append(dict(cycle=cycle,frameSize=list(image.size),previewSize=list(preview.size),transport=stream.transport,backend=stream.backend_info,seconds=round(time.monotonic()-started,3),python=process_snapshot(os.getpid()),system=system_snapshot()))
            image=None;preview=None
        finally:camera.stop_video_stream_mode()
        assert camera._video_stream is None and stream.is_stopped
        assert stream.owner_exit_code==0
        checks[-1].update(ownerExitCode=stream.owner_exit_code,stopped=True)
    print(json.dumps(dict(passed=True,checks=checks,physicalCamera=True,physicalDisplay=False,pixelsSaved=False,walletGenerated=False,entropyQualityQualified=False,fullLvglEntropyFlowQualified=False)),flush=True)
finally:camera.stop_video_stream_mode()
