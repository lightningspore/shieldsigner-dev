import sys
from pathlib import Path
import unittest
from unittest.mock import patch
from queue import Queue
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from runtime import Runtime,KEYS
class Host:
    def __init__(self,*args):self.events=Queue();self.error=None;self.sent=[]
    def send(self,op,**args):
        self.sent.append((op,args))
        if op=='screen':self.events.put(dict(event='screen_ready',request=args['request']))
        if op=='key' and args['pressed']:
            self.events.put(dict(event='button_selected',index=0))
    def next_event(self):return self.events.get(timeout=1)
    def close(self):pass
class RuntimeTests(unittest.TestCase):
    def test_presses_are_debounced_and_returned(self):
        samples=iter([set(),{'KEY_PRESS'},{'KEY_PRESS'},{'KEY_PRESS'}])
        with patch('runtime.NativeHost',Host),patch('runtime.configuration',return_value=('button_list_screen',{'button_list':['One']})),patch('runtime.time.monotonic',side_effect=[0,.01,.02,.05]),patch('runtime.time.sleep'):
            app=Runtime('binary',lambda *a:None,lambda:next(samples))
            self.assertEqual(app.run(object,{}),0)
            presses=[item for op,item in app.host.sent if op=='key' and item['pressed']]
            self.assertEqual(presses,[dict(key=10,pressed=True)])
    def test_key_values_match_lvgl(self):
        self.assertEqual([KEYS[n] for n in ['KEY_UP','KEY_DOWN','KEY_RIGHT','KEY_LEFT','KEY_PRESS']],[17,18,19,20,10])
if __name__=='__main__':unittest.main()

class ActivityTests(unittest.TestCase):
    def test_only_debounced_activity_updates_original_timer(self):
        calls=[]
        with patch('runtime.NativeHost',Host):
            app=Runtime('binary',lambda *a:None,lambda:{'KEY_PRESS'},activity_sink=lambda:calls.append('active'))
            app.waiting_release=False
            with patch('runtime.time.monotonic',side_effect=[0,.01,.03,.10,.30]):
                for _ in range(5):app.poll_input()
            self.assertEqual(calls,['active','active'])

class ScreensaverPolicyTests(unittest.TestCase):
    def test_view_opt_out_is_passed_to_native_builder(self):
        samples=iter([set(),{'KEY_PRESS'},{'KEY_PRESS'},{'KEY_PRESS'}])
        with patch('runtime.NativeHost',Host),patch('runtime.configuration',return_value=('button_list_screen',{'button_list':['One'],'allow_screensaver':True})),patch('runtime.time.monotonic',side_effect=[0,.01,.02,.05]),patch('runtime.time.sleep'):
            app=Runtime('binary',lambda *a:None,lambda:next(samples));app.view_allows_screensaver=False
            self.assertEqual(app.run(object,{}),0)
            config=next(args['config'] for op,args in app.host.sent if op=='screen')
            self.assertFalse(config['allow_screensaver'])

class BriefInputTests(unittest.TestCase):
    def execute(self,samples,times,waiting=False):
        calls=[];samples=iter(samples)
        with patch('runtime.NativeHost',Host):
            app=Runtime('binary',lambda *a:None,lambda:next(samples),activity_sink=lambda:calls.append(1))
            app.waiting_release=waiting
            with patch('runtime.time.monotonic',side_effect=times):
                for _ in times:app.poll_input()
        return app.host.sent,calls
    def test_one_low_sample_across_slow_poll_is_one_complete_tap(self):
        sent,calls=self.execute([{'KEY3'},set(),set()],[0,.05,.06])
        self.assertEqual(sent,[('key',dict(key=51,pressed=True)),('key',dict(key=51,pressed=False))]);self.assertEqual(calls,[1])
    def test_short_bounce_is_not_promoted_to_tap(self):
        sent,calls=self.execute([{'KEY3'},set()],[0,.01])
        self.assertEqual(sent,[]);self.assertEqual(calls,[])
    def test_carried_hold_is_ignored_until_release_then_fresh_press(self):
        sent,calls=self.execute([{'KEY3'},{'KEY3'},set(),{'KEY3'},{'KEY3'},set()],[0,.05,.06,.07,.11,.15],waiting=True)
        self.assertEqual(sent,[('key',dict(key=51,pressed=True)),('key',dict(key=51,pressed=False))]);self.assertEqual(calls,[1])

class IdleFastPathTests(unittest.TestCase):
    def test_idle_retains_lifecycle_polling_without_events_or_activity(self):
        calls=[]
        with patch('runtime.NativeHost',Host):
            app=Runtime('binary',lambda *a:None,lambda:set(),activity_sink=lambda:calls.append('activity'))
            app.waiting_release=False;app.lifecycle_check=lambda:calls.append('lifecycle')
            for _ in range(4):app.poll_input()
            self.assertEqual(calls,['lifecycle']*4)
            self.assertEqual(app.host.sent,[])
