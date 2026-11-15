# SPDX-License-Identifier: MIT
"""Shared actual native renderer, with cooperative controller service ownership."""
from seedsigner_port.native_ui import ScreenSession
from seedsigner_port.hardware_buttons import HardwareButtons
class Renderer:
    _instance=None
    canvas_width=240
    canvas_height=240
    is_screenshot_generator=False
    def __init__(self,backend=None,buttons=None):
        import ui
        self.backend=backend if backend is not None else ui
        self.backend.init()
        self.buttons=buttons if buttons is not None else HardwareButtons.get_instance()
        self.session=ScreenSession(backend=self.backend,buttons=self.buttons,service=self.service)
    @classmethod
    def configure_instance(cls,backend=None,buttons=None):
        if cls._instance is not None:raise RuntimeError('Renderer already configured')
        cls._instance=cls(backend,buttons)
        return cls._instance
    @classmethod
    def get_instance(cls):
        if cls._instance is None:return cls.configure_instance()
        return cls._instance
    def service(self):
        from seedsigner_port.controller import Controller
        if Controller._instance is not None:Controller._instance.service()
    def run_screen(self,screen_class,args):
        self.service()
        return self.session.run_screen(screen_class,args)
    def display_blank_screen(self):
        self.backend.blank()
        self.session.current=None;self.session._button_count=None
