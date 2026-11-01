import sys,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from toast_bridge import install
class ToastTests(unittest.TestCase):
    def test_original_content_and_condition_native_show_stop(self):
        class Overlay:
            def __post_init__(self):raise AssertionError('PIL toast initialized')
        class Manager:
            def run(self):raise AssertionError('PIL toast thread used')
        original=Overlay.__post_init__;sent=[]
        host=SimpleNamespace(send=lambda op,**kw:sent.append((op,kw)))
        restore=install(SimpleNamespace(host=host),SimpleNamespace(ToastOverlay=Overlay,BaseToastOverlayManagerThread=Manager))
        try:
            overlay=Overlay();overlay.__post_init__()
            loader=SimpleNamespace(activation_delay=0,duration=0,keep_running=True,hw_inputs=SimpleNamespace(has_any_input=lambda:False),should_keep_running=lambda:True,toast=SimpleNamespace(label_text='Public notice',icon_name='glyph',color='blue',font_color='white'))
            with patch('toast_bridge.time.monotonic',side_effect=[0,0,1]):Manager.run(loader)
            self.assertEqual([op for op,_ in sent],['toast','toast_stop'])
            spec=sent[0][1]
            self.assertEqual(spec['text'],'Public notice');self.assertEqual(spec['outline'],'#0000ff');self.assertEqual(spec['font'],'#ffffff')
            self.assertEqual(sent[1][1]['token'],spec['token'])
        finally:restore()
        self.assertIs(Overlay.__post_init__,original)
