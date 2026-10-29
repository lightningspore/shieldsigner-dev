"""No GPIO/SPI access: validate extension import, wire colors and packing cost."""
import json
import resource
import time
import shieldsigner_lcd

assert shieldsigner_lcd.pack_rgb(bytes([255, 0, 0, 0, 255, 0, 0, 0, 255])) == bytes.fromhex('f80007e0001f')
frame = bytes([255, 128, 16]) * (240*240)
start = time.monotonic()
for _ in range(100):
    packed = shieldsigner_lcd.pack_rgb(frame)
assert len(packed) == 115200 and packed[:2] == bytes.fromhex('fc02')
print(json.dumps({'kind': 'lcd-pyo3-packing-bench', 'frames': 100,
    'elapsedSeconds': time.monotonic()-start, 'maxRssPlatformUnits': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    'pythonAbiImportPassed': True, 'primaryColorsPassed': True,
    'gpioOrSpiAccessed': False, 'hardwareQualified': False}))
