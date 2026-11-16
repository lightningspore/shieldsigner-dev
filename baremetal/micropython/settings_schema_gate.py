# SPDX-License-Identifier: MIT
# Original schema/parser against PUBLIC fixtures, no persisted/user settings.
from seedsigner_port.settings_schema import (
    SettingsConstants as C,
    SettingsDefinition as D,
    SettingsEntry,
    SettingsQR,
    InvalidSettingsQRData,
)
import json
import gc
import ui

assert len(D.settings_entries) == 60
assert C.get_detected_languages() == [('en', 'English')]
assert len(D.get_defaults()) == 60
entry = D.get_settings_entry(C.SETTING__ENCRYPTION_ITER)
assert (entry.default_value, entry.min_value, entry.max_value) == (10, 10, 1000)
# Parser is not the setter: raw free-entry bounds must be enforced before apply.
assert (
    SettingsQR.parse_settingsqr('settings::v1 pbkdf2_iterations=0')[1][C.SETTING__ENCRYPTION_ITER]
    == 0
)
assert SettingsEntry.__eq__(entry, object()) is NotImplemented
copy = D.get_defaults()
copy[C.SETTING__SIG_TYPES].append('public-copy-test')
assert 'public-copy-test' not in D.get_defaults()[C.SETTING__SIG_TYPES]
name, parsed = SettingsQR.parse_settingsqr('settings::v1 name=Public_Test network=T sigs=ss,ms')
assert name == 'Public Test' and parsed[C.SETTING__NETWORK] == 'T'
assert parsed[C.SETTING__SIG_TYPES] == ['ss', 'ms']
assert (
    SettingsQR.parse_settingsqr('settings::v1 qr_brightness=1.5')[1][C.SETTING__QR_BRIGHTNESS]
    == 1.5
)
assert abs(float('1.23456789012345') - 1.23456789012345) < 1e-14
assert 1.0 + 1.0 / 1099511627776.0 > 1.0
for text in (
    'invalid',
    'settings::v2 network=M',
    'settings::v1 network=invalid',
    'settings::v1 network=',
):
    try:
        SettingsQR.parse_settingsqr(text)
        assert False
    except InvalidSettingsQRData:
        pass
baseline = ui.status()['heap_bytes']
for n in range(30):
    SettingsQR.parse_settingsqr('settings::v1 network=M qr_brightness=1.5')
    gc.collect()
assert ui.status()['heap_bytes'] == baseline
print('@@SETTINGS_PUBLIC_SCHEMA', json.dumps(D.to_dict()))
print('@@SETTINGS_SCHEMA_HEAP', baseline)
print('@@PASS original-settings-schema-parser')
