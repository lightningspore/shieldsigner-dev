# SPDX-License-Identifier: MIT
# Native RAM settings, PUBLIC fixtures only; no storage read/write or driver changes.
from seedsigner_port.settings_store import Settings
from seedsigner_port.settings_schema import SettingsConstants as C,SettingsDefinition as D
from seedsigner_port.settings_platform import UnsupportedSettingsAction
import gc
import ui
blocked=False
try:
    Settings()
except Exception:
    blocked=True
assert blocked
s=Settings.get_instance()
assert s is Settings.get_instance()
assert s.get_platform_default_hardware_config()=='mini-pcb240'
assert s.OS_ENVIRONMENT=='baremetal' and not s.is_seedsigner_os()
assert s.get_value(C.SETTING__SMARTCARD_INTERFACES)==[]
assert s.get_value(C.SETTING__PERSISTENT_SETTINGS)=='D'
assert s.get_value(C.SETTING__CAMERA_ROTATION)==270
key=C.SETTING__ENCRYPTION_ITER
for value in (0,9,1001,True,False,10.5,'bad','99999999999999999999999999'):
    s.set_value(key,10,save=False)
    s.set_value(key,value,save=False)
    assert s.get_value(key)==10
for value,expected in ((10,10),(1000,1000),('24',24)):
    s.set_value(key,value,save=False)
    assert s.get_value(key)==expected
s.set_value(key,10,save=False)
name,parsed=s.parse_settingsqr('settings::v1 name=Public_Test network=T sigs=ss,ms pbkdf2_iterations=0')
assert name=='Public Test'
s.update(parsed,persist=False,validate=True)
assert s.get_value(key)==10 and s.get_value(C.SETTING__NETWORK)=='T'
assert len(s.get_multiselect_value_display_names(C.SETTING__SIG_TYPES))==2
assert s.get_value_display_name(C.SETTING__NETWORK)
for key,value in ((C.SETTING__PERSISTENT_SETTINGS,'E'),(C.SETTING__SMARTCARD_INTERFACES,['usb']),(C.SETTING__DISPLAY_CONFIGURATION,'st7735_128x128'),(C.SETTING__LOCALE,'es')):
    before=dict(s._data)
    try:
        s.update({C.SETTING__NETWORK:'M',key:value})
        assert False
    except UnsupportedSettingsAction:
        pass
    assert s._data==before
s.save()
s.flush_save()
gc.collect()
baseline=ui.status()['heap_bytes']
for number in range(30):
    s.update({C.SETTING__NETWORK:'M' if number%2==0 else 'T'},persist=False,validate=True)
    gc.collect()
assert ui.status()['heap_bytes']==baseline
assert s.get_value(C.SETTING__SMARTCARD_INTERFACES)==[]
assert s.get_value(C.SETTING__PERSISTENT_SETTINGS)=='D'
assert s.get_value(C.SETTING__CAMERA_ROTATION)==270
print('@@NATIVE_SETTINGS_STORE',len(s._data),baseline,s.get_value(C.SETTING__NETWORK))
print('@@PASS original-settings-ram-data')
