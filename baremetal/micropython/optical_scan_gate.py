# SPDX-License-Identifier: MIT
# Optical end-to-end scan: original ScanView + native scan screen + real camera.
# The host (tools/optical_scan_test.py) shows a PUBLIC QR on a monitor and
# prepends CASE='<name>'. Prints the original routing result; host asserts it.
import ui,gc,time,hashlib,machine
from seedsigner_port.renderer import Renderer
from seedsigner_port.controller import Controller
from seedsigner_port.view_scan import ScanView
print('@@OPTICAL_RESET_BEFORE',machine.last_reset());machine.clear_reset_record()
ui.init()
Renderer._instance=None;Renderer.configure_instance()
Controller._instance=None;c=Controller.get_instance()
view=ScanView();t=time.ticks_ms()
try:
    d=view.run()
finally:
    c.camera.stop_video_stream_mode()
ms=time.ticks_ms()-t;dec=view.decoder
info={'case':CASE,'ms':ms,'view':d.View_cls.__name__,'complete':dec.is_complete,'qr_type':str(dec.qr_type)}
if dec.is_psbt:
    p=dec.get_psbt();info['psbt_sha256']=hashlib.sha256(p.serialize()).hexdigest()[:16];info['inputs']=len(p.inputs);info['outputs']=len(p.outputs)
if dec.is_address:info['address']=dec.get_address()
if dec.is_seed:
    words=dec.get_seed_phrase();info['words']=len(words);info['first_last']=(words[0],words[-1]) # PUBLIC test seed only
print('@@SCAN_RESULT',info)
gc.collect()
