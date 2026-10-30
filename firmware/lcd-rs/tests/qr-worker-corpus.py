"""Run the native transport against the actual reader and public luma fixtures.

The reader may be an explicit QEMU launcher. This proves protocol/decoder
integration, not optical capture, GUI integration or hardware performance.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time
import socket
import struct
import threading

from shieldsigner_lcd import QrWorker, FrameReceiver, PreviewRenderer

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--reader", required=True)
parser.add_argument("--fixtures", type=Path, required=True)
args = parser.parse_args()
manifest = json.loads((args.fixtures / "manifest.json").read_text())
client = QrWorker(args.reader, 10)
left,right=socket.socketpair()
receiver=FrameReceiver(left.fileno(),framerate=120)
renderer=PreviewRenderer()
cases = []
try:
    for fixture in manifest:
        name = fixture["name"]
        pixels = (args.fixtures / (name + ".luma")).read_bytes()
        expected = (args.fixtures / (name + ".payload")).read_bytes()
        assert hashlib.sha256(pixels).hexdigest() == fixture["inputSha256"]
        assert hashlib.sha256(expected).hexdigest() == fixture["payloadSha256"]
        started = time.monotonic()
        payload=pixels+bytes([128])*(640*480//2)
        packet=struct.pack('<8sIIII',b'SSNV12F1',640,480,len(cases)+1,len(payload))+payload
        sender=threading.Thread(target=right.sendall,args=(packet,));sender.start()
        frame=receiver.read(0,1);sender.join()
        assert frame is not None
        actual = client.decode_frame(frame)
        # Compare direct-frame preview to the already qualified byte interface.
        assert renderer.render_frame(frame,90)==renderer.render_luma(pixels,640,480,90)
        assert actual == expected, name
        cases.append({"name": name, "payloadBytes": len(expected),
                      "byteExact": True, "seconds": time.monotonic() - started})
    assert client.decode_luma(bytes([255]) * (640 * 480), 640, 480) is None
    statistics = client.statistics()
    assert statistics[:4] == (1, len(cases) + 1, len(cases), 0), statistics
finally:
    client.close()
    receiver.close()
    left.close();right.close()
assert client.worker_pid is None
print(json.dumps({"passed": True, "nativeReceptionQrAndPreview": True, "cases": cases, "blankReturnsNone": True,
                  "workerReused": True, "workerClosed": True,
                  "statistics": statistics, "opticalQualified": False}, indent=2))
