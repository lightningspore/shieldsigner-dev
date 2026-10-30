"""Explicit diagnostic GPIO-read overlay: physical inputs remain active.

No GPIO writes, network listener or extra thread. Local request file is bounded,
validated and consumed once. Synthetic input tests software navigation only.
"""
import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import threading
import time

REVIEWED_BUTTONS='951c7106064fc4f352de583a061d535b22686f7d2aed03f2b839df48d8450e3e'
KEYS={'KEY_UP','KEY_DOWN','KEY_LEFT','KEY_RIGHT','KEY_PRESS','KEY1','KEY2','KEY3'}

class ButtonControl:
    def __init__(self,directory,clock=time.monotonic):
        self.directory=Path(directory);self.directory.mkdir(mode=0o700)
        self.clock=clock;self.lock=threading.Lock();self.next_poll=0
        self.key=None;self.until=0;self.last_id=None;self.capture=None
        self.status('ready')

    def status(self,state):
        p=self.directory/'status.json';tmp=p.with_suffix('.tmp')
        tmp.write_text(json.dumps({'state':state,'id':self.last_id,'key':self.key,'pid':os.getpid()})+'\n')
        tmp.chmod(0o600);tmp.replace(p)

    def pressed(self,key):
        with self.lock:
            now=self.clock()
            if self.key is not None and now>=self.until:
                self.key=None;self.status('released')
            if now>=self.next_poll:
                self.next_poll=now+0.025
                capture_request=self.directory/'screen.request'
                if self.capture is not None and capture_request.exists():
                    capture_request.unlink()
                    self.capture(self.directory/'screen.png')
                request=self.directory/'request.json'
                try:
                    with request.open('rb') as f:raw=f.read(513)
                    request.unlink()
                except FileNotFoundError:raw=None
                if raw is not None:
                    try:
                        data=json.loads(raw)
                        if len(raw)>512 or set(data)!={'key','holdMs','id'}:raise ValueError()
                        if data['key'] not in KEYS or type(data['holdMs']) is not int or not 30<=data['holdMs']<=1500:raise ValueError()
                        if not isinstance(data['id'],str) or not re.fullmatch('[a-zA-Z0-9_-]{1,48}',data['id']):raise ValueError()
                        if self.key is not None or data['id']==self.last_id:raise ValueError()
                    except (ValueError,TypeError,KeyError):
                        self.status('rejected')
                    else:
                        self.key=data['key'];self.until=now+data['holdMs']/1000;self.last_id=data['id'];self.status('pressed')
            return key==self.key and now<self.until

class PinOverlay:
    def __init__(self,pin,key,control):self.pin=pin;self.key=key;self.control=control
    def read(self):
        injected=self.control.pressed(self.key)
        return self.pin.read() and not injected
    def __getattr__(self,name):return getattr(self.pin,name)


def install(app_root,directory=None):
    root=Path(app_root).resolve();source=root/'seedsigner/hardware/buttons.py'
    if hashlib.sha256(source.read_bytes()).hexdigest()!=REVIEWED_BUTTONS:raise ValueError('Unreviewed buttons source')
    module=importlib.import_module('seedsigner.hardware.buttons')
    if Path(module.__file__).resolve()!=source or not module.USING_GPIO:raise ValueError('Expected reviewed GPIO implementation')
    control=ButtonControl(directory or '/tmp/shieldsigner-buttons-'+str(os.getpid()))
    cls=module.HardwareButtons;original=cls.get_instance.__func__
    @classmethod
    def get_instance(cls):
        instance=original(cls)
        if not getattr(instance,'_diagnostic_button_control',False):
            instance._gpio_pins={key:PinOverlay(pin,key,control) for key,pin in instance._gpio_pins.items()}
            instance._diagnostic_button_control=True
        return instance
    cls.get_instance=get_instance
    current=Path('/tmp/shieldsigner-button-control-current.json');tmp=current.with_suffix('.tmp')
    tmp.write_text(json.dumps({'directory':str(control.directory),'pid':os.getpid()})+'\n');tmp.chmod(0o600);tmp.replace(current)
    return control
