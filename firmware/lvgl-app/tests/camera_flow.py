"""Real Rust camera/ZXing -> original DecodeQR -> LVGL, metadata-only receipt.

Uses whatever the camera sees without logging, saving or returning QR values.
A real-camera startup cancellation is followed by repeated open/preview/decode
or cancellation runs. Optical payload interpretation is not fixture qualification.
"""
import json
import os
from pathlib import Path
import sys
import time
sys.path[:0]=[str(Path(__file__).resolve().parent),'/usr/lib/shieldsigner-camera/python','/opt/src']
os.environ['SHIELDSIGNER_SMALL_RAM']='1'
long_soak='--long-soak' in sys.argv
memory_cycles='--memory-cycles' in sys.argv
production_policy=long_soak or memory_cycles
restore_policy=None
if production_policy:
    from dependency_policy import install as dependencies
    restore_policy=dependencies('/opt/src',Path(__file__).parent/'source-guards.json')
    from startup_policy import install as startup
    startup('/opt/src','/usr/lib/shieldsigner-camera/python')
from resources import process_snapshot

from runtime import Runtime,install_view_dispatch
from seedsigner.models.decode_qr import DecodeQR
from seedsigner.gui.screens.scan_screens import ScanScreen
class Buttons:
    def load(self,delay):self.delay=delay;self.start=None;self.next_report=30
    def __call__(self):
        now=time.monotonic()
        if self.start is None:self.start=now
        if long_soak and now-self.start>=self.next_report:
            print(json.dumps(dict(event='soak-heartbeat',elapsedSeconds=int(now-self.start))),flush=True)
            self.next_report+=30
        return {'KEY_LEFT'} if now-self.start>self.delay else set()
buttons=Buttons();rectangles=0
hardware=None
if '--display' in sys.argv:
    from luckfox import LuckfoxHardware
    hardware=LuckfoxHardware()
def pixels(area,data):
    global rectangles
    rectangles+=1
    if hardware is not None:hardware.pixels(area,data)
runtime=Runtime(sys.argv[1],pixels,buttons)
restore=install_view_dispatch(runtime,'/opt/src',Path(__file__).parent/'source-guards.json')
if '--tools-loaded' in sys.argv:
    import seedsigner.views.tools_views
cycles=[]
try:
    delays=[.3,8,8,8,8,8] if memory_cycles else [.3,90,90,90] if long_soak else [.3,30,30] if '--soak' in sys.argv else [.3,4,4]
    baseline=process_snapshot(os.getpid())
    for delay in delays:
        decoder=DecodeQR()
        if '--soak' in sys.argv or production_policy:
            from seedsigner.models.decode_qr import DecodeQRStatus
            # Keep the duration controlled even if an incidental QR is visible.
            # This is a lifecycle control, not optical/decoder qualification.
            decoder.add_data=lambda payload:DecodeQRStatus.FALSE
        started=time.monotonic()
        buttons.load(delay)
        outcome=ScanScreen(decoder=decoder,instructions_text='Scan a QR code',framerate=6).display()
        stats=runtime.camera_stats
        assert stats['cameraStopped'] and stats['ownerExitCode']==0,stats
        dma=Path('/sys/kernel/debug/dma_buf/bufinfo').read_text().splitlines()[-1]
        assert dma=='Total 0 objects, 0 bytes',dma
        snapshot=process_snapshot(os.getpid())
        import gc
        collected=gc.collect() if memory_cycles else None
        cycles.append(dict(postClosePython=snapshot,postCollectionPython=process_snapshot(os.getpid()) if memory_cycles else None,collectedObjects=collected,postCloseNative=process_snapshot(runtime.host.child.pid),seconds=round(time.monotonic()-started,3),cancelled=outcome is False,complete=bool(decoder.is_complete),stats=stats,dma=dma))
    assert cycles[0]['cancelled'], 'Startup cancellation was not exercised'
    assert any(cycle['stats']['frames']>0 for cycle in cycles[1:]), 'No live camera preview frame was exercised'
    if production_policy:
        assert all(cycle['stats']['frames']>0 and cycle['stats']['qr']['calls']>0 for cycle in cycles[1:])
        assert len({cycle['postClosePython']['Threads'] for cycle in cycles[1:]})==1, 'Thread count changed after live-session cleanup'
        assert not any(name==prefix or name.startswith(prefix+'.') for name in sys.modules for prefix in ('pyzbar','cv2','numpy','qrcode.image.styledpil'))
    print(json.dumps(dict(passed=True,longSoak=long_soak,productionDependencyPolicy=production_policy,memoryCycles=memory_cycles,baselinePython=baseline,soak='--soak' in sys.argv or long_soak,toolsLoaded='--tools-loaded' in sys.argv,cycles=cycles,rectangles=rectangles,physicalCamera=True,physicalDisplay=hardware is not None,physicalButtons=False,qrValuesCaptured=False,scope='Real-camera lifecycle and original decoder API; not a known optical test vector')))
finally:
    restore();runtime.close()
    if hardware is not None:hardware.close()
    if restore_policy is not None:restore_policy()
