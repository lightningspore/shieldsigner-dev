import json
from pathlib import Path
from queue import Queue
import sys
import tempfile
from types import SimpleNamespace as N
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from camera_scan import run_scan
class Status:
    FALSE=0;PART_COMPLETE=1;PART_EXISTING=2;COMPLETE=3;INVALID=5
class Host:
    timeout=1;error=None
    def __init__(self):self.events=Queue();self.operations=[]
    def send(self,op,**args):
        self.operations.append(op)
        if op=='scan':self.events.put(dict(event='screen_ready',request=args['request']))
        if op=='scan_stop':self.events.put(dict(event='scan_stopped'))
    def next_event(self):return self.events.get(timeout=1)
    def send_preview(self,*args,**kwargs):self.events.put(dict(event='preview_ready'))
class CameraScanTests(unittest.TestCase):
    def run_case(self,payload=b'',start_error=False,decode_error=False,model_error=False,cleanup_interrupt=False):
        stream=N(is_stopped=True,owner_exit_code=0)
        def start():
            if start_error:raise OSError('camera unavailable')
            stream.is_stopped=False;return stream
        stream.start=start;stream.read=lambda:object();stream.stop=lambda:setattr(stream,'is_stopped',True)
        reader=N(closed=False,stats={})
        def decode(frame):
            if decode_error:raise TimeoutError('QR worker deadline')
            return payload
        reader.decode=decode;reader.close=lambda:setattr(reader,'closed',True)
        received=[]
        def add_data(data):
            received.append(data)
            if model_error:raise ValueError('decoder rejected input')
            return Status.INVALID
        decoder=N(add_data=add_data,get_percent_complete=lambda **k:0)
        def poll():
            if cleanup_interrupt and stream.is_stopped:raise RuntimeError('late lifecycle interruption')
        host=Host();runtime=N(request=0,last_key=10,host=host,reset_input=lambda:None,poll_input=poll)
        modules={
            'shieldsigner_native_stream':N(NativeVideoStream=lambda **kwargs:stream),
            'shieldsigner_lcd':N(PreviewRenderer=lambda *args:N(render_frame=lambda *a:(240,180,bytes(129600)))),
            'shieldsigner_qr_decoder':N(RustTransportQrReader=lambda *a:reader),
            'seedsigner.models.decode_qr':N(DecodeQRStatus=Status),
            'seedsigner.models.settings':N(Settings=N(get_instance=lambda:N(get_value=lambda *a:270)),SettingsConstants=N(SETTING__CAMERA_ROTATION='rotation')),
        }
        with tempfile.TemporaryDirectory() as directory:
            config=Path(directory)/'config.json';config.write_text('{}')
            with patch.dict(sys.modules,modules),patch.dict('os.environ',{'SHIELDSIGNER_CAMERA_CONFIG':str(config)}):
                error=None
                try:value=run_scan(runtime,dict(decoder=decoder))
                except Exception as exc:error=exc;value=None
        return N(error=error,value=value,stream=stream,reader=reader,received=received,host=host,runtime=runtime)
    def test_empty_binary_payload_reaches_original_decoder(self):
        result=self.run_case(payload=b'')
        self.assertIsNone(result.error);self.assertEqual(result.received,[b''])
        self.assertTrue(result.reader.closed);self.assertTrue(result.stream.is_stopped)
        self.assertEqual(result.host.operations[-1],'scan_stop')
    def test_camera_start_failure_still_closes_worker_and_overlay(self):
        result=self.run_case(start_error=True)
        self.assertIsInstance(result.error,OSError);self.assertTrue(result.reader.closed);self.assertTrue(result.stream.is_stopped)
        self.assertEqual(result.host.operations[-1],'scan_stop')
    def test_qr_timeout_stops_camera_and_overlay(self):
        result=self.run_case(decode_error=True)
        self.assertIsInstance(result.error,TimeoutError);self.assertTrue(result.reader.closed);self.assertTrue(result.stream.is_stopped)
        self.assertEqual(result.host.operations[-1],'scan_stop')
    def test_model_failure_stops_both_native_owners(self):
        result=self.run_case(model_error=True)
        self.assertIsInstance(result.error,ValueError);self.assertTrue(result.reader.closed);self.assertTrue(result.stream.is_stopped)
        self.assertEqual(result.host.operations[-1],'scan_stop')
    def test_late_lifecycle_event_does_not_mask_primary_worker_error(self):
        result=self.run_case(decode_error=True,cleanup_interrupt=True)
        self.assertIsInstance(result.error,TimeoutError)
        self.assertEqual(str(result.error),'QR worker deadline')
        self.assertTrue(result.reader.closed);self.assertTrue(result.stream.is_stopped)
        self.assertEqual(result.host.operations[-1],'scan_stop')
if __name__=='__main__':unittest.main()
