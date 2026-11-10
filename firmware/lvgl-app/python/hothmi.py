"""HTM-TFT028A16-SPI initialization, HOTHMI Rev 0-0 pp.17-19.

Manufacturer register values, not the generic square ST7789 panel profile.
SPI remains MSB-first RGB565. Physical panel revision/orientation need testing.
"""
import json
from pathlib import Path
import time
from types import MethodType

PROFILE = 'hothmi_htm_tft028a16_spi'
IMAGE_PROFILE = Path('/usr/share/shieldsigner-lvgl/panel-profile.json')

# (command, parameters, delay seconds). Reset uses the pinned driver's longer
# 10/10/150 ms sequence; preserve >=120 ms after reset and after Sleep Out.
INITIALIZATION = (
    (0x11, (), .150),
    (0xB2, (0x0C,0x0C,0x00,0x33,0x33), 0),
    (0xB7, (0x35,), 0),
    (0xB0, (0x00,0xE0), 0),
    (0xBB, (0x2B,), 0),
    (0xC0, (0x2C,), 0),
    (0xC2, (0x01,), 0),
    (0xC3, (0x11,), 0),
    (0xC4, (0x20,), 0),
    (0xC6, (0x0F,), 0),
    (0xD0, (0xA4,0xA1), 0),
    (0xE0, (0xD0,0x00,0x05,0x0E,0x15,0x0D,0x37,0x43,0x47,0x09,0x15,0x12,0x16,0x19), 0),
    (0xE1, (0xD0,0x00,0x05,0x0D,0x0C,0x06,0x2D,0x44,0x40,0x0E,0x1C,0x18,0x16,0x19), 0),
    (0x2A, (0x00,0x00,0x00,0xEF), 0),
    (0x2B, (0x00,0x00,0x01,0x3F), 0),
    (0x21, (), 0),
    (0x36, (0xA0,), 0),
    (0x3A, (0x55,), 0),
    (0x29, (), .020),
)

def image_profile(path=IMAGE_PROFILE):
    path=Path(path)
    if not path.exists():return None
    if path.is_symlink():raise ValueError('Panel profile must be a regular image file')
    data=json.loads(path.read_text())
    if data!={'profile':PROFILE}:raise ValueError('Unreviewed panel profile')
    return PROFILE

def initialize(display):
    display.reset()
    for command,parameters,delay in INITIALIZATION:
        display.command(command)
        for value in parameters:display.data(value)
        if delay:time.sleep(delay)

def install(display):
    if (display.width,display.height)!=(320,240):raise ValueError('HOTHMI profile requires 320x240')
    if display._display_initialized:raise ValueError('Select HOTHMI before panel initialization')
    display.init=MethodType(initialize,display)
