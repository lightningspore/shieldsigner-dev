# SPDX-License-Identifier: MIT
"""Actual Mini PCB input/debounce with shared controller activity tracking."""
from seedsigner_port.buttons import ButtonInput,NAMES
from seedsigner_port import clock
class HardwareButtons(ButtonInput):
    _instance=None
    @classmethod
    def get_instance(cls):
        if cls._instance is None:cls._instance=cls()
        return cls._instance
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.update_last_input_time()
    def update_last_input_time(self):self.last_input_time=int(clock.time()*1000)
    def poll(self,keys=None):
        value=super().poll(keys)
        if value is not None:self.update_last_input_time()
        return value
class HardwareButtonsConstants:
    ALL_KEYS=NAMES
    KEYS__ANYCLICK=('KEY_PRESS','KEY1','KEY2','KEY3')
for _name in NAMES:setattr(HardwareButtonsConstants,_name,_name)
