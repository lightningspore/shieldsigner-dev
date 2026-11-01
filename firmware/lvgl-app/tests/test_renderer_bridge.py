import sys,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from renderer_bridge import install
from contracts import UnmigratedScreen
class RendererBridgeTests(unittest.TestCase):
    def test_no_canvas_legacy_rejection_and_restore(self):
        class Renderer:
            _instance=None
            def initialize_display(self):raise AssertionError('PIL renderer initialized')
        original=Renderer.initialize_display;calls=[]
        settings=SimpleNamespace(get_value=lambda key,**kw:'st7789_240x240' if key=='display' else 'E')
        modules={'seedsigner.models.settings':SimpleNamespace(Settings=SimpleNamespace(get_instance=lambda:settings)),
                 'seedsigner.models.settings_definition':SimpleNamespace(SettingsConstants=SimpleNamespace(SETTING__DISPLAY_CONFIGURATION='display',SETTING__DISPLAY_COLOR_INVERTED='invert',OPTION__ENABLED='E'))}
        hardware=SimpleNamespace(lcd=SimpleNamespace(set_color_inversion=lambda value:calls.append(value)))
        restore=install(SimpleNamespace(clear=lambda:calls.append('clear')),hardware,Renderer)
        try:
            with patch.dict(sys.modules,modules):Renderer.configure_instance()
            instance=Renderer._instance
            self.assertIsNone(instance.canvas);self.assertIsNone(instance.draw)
            self.assertEqual(instance.canvas_width,240)
            with self.assertRaises(UnmigratedScreen):instance.show_image()
            instance.display_blank_screen()
            self.assertEqual(calls,[True,'clear'])
        finally:restore()
        self.assertIsNone(Renderer._instance)
        self.assertIs(Renderer.initialize_display,original)
        self.assertFalse(hasattr(Renderer,'configure_instance'))

    def test_geometry_change_uses_runtime_handoff_and_updates_canvas_metadata(self):
        class Renderer:
            _instance=None
            def initialize_display(self):pass
        values={'display':'st7789_320x240','invert':'D'};events=[]
        settings=SimpleNamespace(get_value=lambda key,**kwargs:values[key])
        modules={'seedsigner.models.settings':SimpleNamespace(Settings=SimpleNamespace(get_instance=lambda:settings)),
                 'seedsigner.models.settings_definition':SimpleNamespace(SettingsConstants=SimpleNamespace(SETTING__DISPLAY_CONFIGURATION='display',SETTING__DISPLAY_COLOR_INVERTED='invert',OPTION__ENABLED='E'))}
        hardware=SimpleNamespace(lcd=SimpleNamespace(),configure_display=lambda *args:events.append(('hardware',args)))
        runtime=SimpleNamespace(width=240,height=240)
        def handoff(width,height,configure):
            events.append(('handoff',width,height));configure();runtime.width=width;runtime.height=height
        runtime.reconfigure_display=handoff
        restore=install(runtime,hardware,Renderer)
        try:
            with patch.dict(sys.modules,modules):
                Renderer.configure_instance();instance=Renderer._instance
                self.assertEqual((instance.canvas_width,instance.canvas_height),(320,240))
                self.assertEqual(instance._display_size,(320,240));self.assertIsNone(instance.canvas)
                values['display']='st7789_240x240';instance.initialize_display()
                self.assertEqual(instance._display_size,(240,240))
            self.assertEqual(events,[('handoff',320,240),('hardware',(320,240,False)),('handoff',240,240),('hardware',(240,240,False))])
        finally:restore()
