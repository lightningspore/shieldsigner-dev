import sys,unittest
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from battery_info import sample,configure,PLACEHOLDERS
class BatteryInfoTests(unittest.TestCase):
    def hat(self,detected=True):return SimpleNamespace(is_enabled=lambda:True,detected=detected,get_voltage=lambda:3.7,get_current=lambda:-250,get_power=lambda:0.925,get_percent=lambda:42.3,get_curve_label=lambda:'public fixture')
    def test_values_units_sign_and_precision_match_original(self):
        self.assertEqual(sample(self.hat()),'Load Voltage: 3.700 V\nCurrent: -0.250 A\nPower: 0.925 W\nPercent: 42.3%\nCurve: public fixture')
    def test_missing_sensor_and_disabled_monitor(self):
        hat=self.hat(False);hat.get_voltage=lambda:self.fail('read absent sensor')
        self.assertIn('Load Voltage: --\nCurrent: --',sample(hat))
        hat.is_enabled=lambda:False;hat.get_curve_label=lambda:self.fail('read disabled monitor')
        self.assertIsNone(sample(hat))
    def test_initial_placeholders_use_live_upstream_label(self):
        builder,cfg=configure({'top_nav':{}})
        self.assertEqual(builder,'button_list_screen');self.assertEqual(cfg['text'],PLACEHOLDERS)
        self.assertTrue(cfg['live_info']);self.assertEqual(cfg['button_list'],[])
    def test_formatter_matches_original_update_thread(self):
        import ast
        from contextlib import nullcontext
        source=(Path(__file__).resolve().parents[3]/'dist/firmware/sources/lvgl/application/src/seedsigner/gui/screens/settings_screens.py').read_text()
        cls=next(node for node in ast.parse(source).body if isinstance(node,ast.ClassDef) and node.name=='BatteryInfoScreen')
        thread=next(node for node in cls.body if isinstance(node,ast.ClassDef) and node.name=='UpdateThread')
        method=next(node for node in thread.body if isinstance(node,ast.FunctionDef) and node.name=='run')
        for detected in (False,True):
            values=[];hat=self.hat(detected)
            state=SimpleNamespace(keep_running=True,battery_hat=hat)
            def stop():state.keep_running=False
            state.screen=SimpleNamespace(renderer=SimpleNamespace(lock=nullcontext(),show_image=stop),_replace_info_text=lambda attr,text:values.append(text))
            namespace={'time':SimpleNamespace(sleep=lambda duration:stop())};local={}
            exec(compile(ast.Module(body=[method],type_ignores=[]),'<original battery thread>','exec'),namespace,local)
            local['run'](state)
            self.assertEqual(sample(hat),'\n'.join(values))
