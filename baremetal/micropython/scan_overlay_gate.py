# SPDX-License-Identifier: MIT
# Public synthetic NV12 color fields; actual LVGL widgets/owned buffers/LCD path.
import ui, json, hashlib, gc, machine, time

ui.init()
ui.overlays(0, 0)
ui.overlays(5)
ui.overlays(2)
print('@@RESET_BEFORE_SCAN', machine.last_reset())
machine.clear_reset_record()
machine.set_reset_marker(0x5343414E)


def center():
    p = ui.framebuffer()
    offset = (120 * 240 + 120) * 2
    return (p[offset] << 8) | p[offset + 1]


def hashframe():
    return hashlib.sha256(ui.framebuffer()).hexdigest()


def settle():
    for _ in range(25):
        ui.tick()
        time.sleep_ms(5)


caption = '< back\nScan your SeedQR'
frame = bytearray(b'\x10' * (640 * 480) + b'\x80' * (640 * 240))
try:
    ui.scan_frame(frame)
    assert False
except RuntimeError:
    pass
for text in ('bad\0text', 'x' * 193):
    try:
        ui.scan_begin(text)
        assert False
    except ValueError:
        pass
assert not ui.scan_state()['active']
ui.scan_begin(caption)
assert ui.scan_state()['active'] == 1 and ui.scan_state()['frames'] == 0
ui.scan_frame(frame)
assert center() == 0
before = hashframe()
frame[: 640 * 480] = b'\xeb' * (640 * 480)
ui.tick()
assert hashframe() == before  # Borrowed source mutations cannot alter owned RGB.
ui.scan_frame(frame)
assert center() == 65535 and ui.scan_state()['frames'] == 2
white = hashframe()
try:
    ui.scan_begin(caption)
    assert False
except RuntimeError:
    pass
assert ui.scan_state()['frames'] == 2
try:
    ui.scan_frame(b'short')
    assert False
except ValueError:
    pass
try:
    ui.scan_status(101, 0, True)
    assert False
except ValueError:
    pass
ui.scan_status(37, 1, True)
settle()
added = hashframe()
assert ui.scan_state() == {
    'active': 1,
    'frames': 2,
    'progress': 37,
    'frame_status': 1,
    'scanning': 1,
}
ui.scan_status(37, 2, True)
settle()
repeated = hashframe()
ui.scan_status(37, 3, True)
settle()
miss = hashframe()
assert len(set((white, added, repeated, miss))) == 4
ui.scan_status(0, 3, False)
settle()
assert hashframe() == white
ui.scan_end()
assert not ui.scan_state()['active'] and center() == 0
ui.scan_end()
print('@@PASS native-scan-owned-nv12-colors-instructions-progress-status-close')
# Crop/BT.601/endian truth: red input field remains exactly RGB565 red at center.
frame[: 640 * 480] = bytes([81]) * (640 * 480)
frame[640 * 480 :] = bytes([90, 240]) * (640 * 240 // 2)
ui.scan_begin(caption)
ui.scan_frame(frame)
assert center() == 0xF800
home = json.dumps(
    {'top_nav': {'title': 'Home'}, 'button_list': ['Scan', 'Seeds', 'Tools', 'Settings']}
)
ui.render('main_menu_screen', home)
assert not ui.scan_state()['active']
before = hashframe()
ui.scan_end()
assert hashframe() == before
print('@@PASS native-scan-generic-screen-replacement-releases-owner')
for _ in range(3):
    ui.scan_begin(caption)
    ui.scan_frame(frame)
    ui.scan_status(37, 2, True)
    ui.scan_end()
    ui.render('main_menu_screen', home)
baseline = ui.status()['heap_bytes']
for n in range(20):
    ui.scan_begin(caption)
    ui.scan_frame(frame)
    ui.scan_status(37, 2, True)
    if n % 2:
        ui.scan_end()
    ui.render('main_menu_screen', home)
    gc.collect()
    assert not ui.scan_state()['active'] and ui.status()['heap_bytes'] == baseline
assert machine.last_reset() is None
print('@@PASS native-scan-20-owned-surface-teardowns-stable', baseline)
ui.scan_begin(caption)
ui.scan_frame(frame)
ui.blank()
assert not ui.scan_state()['active'] and bytes(ui.framebuffer()) == bytes(240 * 240 * 2)
ui.render('main_menu_screen', home)
print('@@PASS native-blank-releases-active-surface-and-clears-shadow')
del frame
gc.collect()
