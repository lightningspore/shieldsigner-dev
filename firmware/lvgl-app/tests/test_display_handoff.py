import sys,unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from runtime import Runtime
class DisplayHandoffTests(unittest.TestCase):
 def prepare(self):
  events=[];app=Runtime.__new__(Runtime)
  app.host=SimpleNamespace(close=lambda:events.append('closed'))
  app.binary='public';app.pixel_sink=lambda *args:None
  app.width=app.height=240;app.screensaver_timeout_ms=120000
  app.low_since={'KEY3':0};app.current=51
  app.configure_screensaver=lambda value:events.append(('saver',value))
  return app,events
 def test_reader_stops_before_hardware_then_new_host_then_input_reset(self):
  app,events=self.prepare()
  def host(binary,sink,**geometry):events.append(('host',geometry));return SimpleNamespace()
  with patch('runtime.NativeHost',side_effect=host):
   app.reconfigure_display(320,240,lambda:events.append('hardware'))
  self.assertEqual(events,['closed','hardware',('host',dict(width=320,height=240)),('saver',120000)])
  self.assertEqual((app.width,app.height),(320,240))
  self.assertTrue(app.waiting_release);self.assertIsNone(app.current);self.assertEqual(app.low_since,{})
 def test_unsupported_geometry_keeps_existing_owner(self):
  app,events=self.prepare()
  with self.assertRaises(ValueError):app.reconfigure_display(128,128,lambda:events.append('hardware'))
  self.assertEqual(events,[])
 def test_failed_hardware_does_not_start_pixel_writer(self):
  app,events=self.prepare()
  def fail():raise OSError('public fixture')
  with patch('runtime.NativeHost') as host:
   with self.assertRaises(OSError):app.reconfigure_display(320,240,fail)
   host.assert_not_called()
  self.assertEqual(events,['closed']);self.assertEqual((app.width,app.height),(240,240))

 def test_closed_runtime_cannot_resurrect_a_native_owner(self):
  app,events=self.prepare();app.closed=True
  with patch('runtime.NativeHost') as host:
   with self.assertRaises(RuntimeError):app.reconfigure_display(320,240,lambda:events.append('hardware'))
   host.assert_not_called()
  self.assertEqual(events,[])
