# Hardware gate: execute through the UART REPL, not a host Python interpreter.
from machine import Pin, I2C, SPI
import time
import gc
import camera

pin = Pin(52, Pin.OUT, value=0)
for value in [0, 1, 0, 1, 0]:
    pin.value(value)
    time.sleep_ms(2)
    assert pin.value() == value
pin = Pin(52, Pin.IN)
print("@@PASS phase-9-gpio")

i2c = I2C(4, freq=100000)
assert i2c.readfrom_mem(0x30, 0x3107, 2, addrsize=16) == b"\xcc\x41"
original = i2c.readfrom_mem(0x30, 0x4501, 1, addrsize=16)
i2c.writeto_mem(0x30, 0x4501, original, addrsize=16)
assert i2c.readfrom_mem(0x30, 0x4501, 1, addrsize=16) == original
print("@@PASS phase-9-i2c")

tx = bytearray([i & 255 for i in range(4096)])
rx = bytearray(4096)
for hz in [1000000, 10000000, 50000000]:
    spi = SPI(0, baudrate=hz)
    spi.write_readinto(tx, rx)
    assert rx == tx
spi.write_readinto(rx, rx)
assert rx == tx
print("@@PASS phase-9-spi")

start = time.ticks_ms()
time.sleep_ms(20)
assert time.ticks_ms() - start >= 20
print("@@PASS phase-9-time")

baseline = camera.settings()["rust_heap_bytes"]
camera.init()
frame = camera.capture()
assert len(frame) == 460800
try:
    frame[0] = 0
    assert False
except TypeError:
    pass
samples = [frame[i] for i in range(0, 307200, 997)]
assert max(samples) > min(samples) + 10
assert camera.settings()["rust_heap_bytes"] == baseline
print("@@PASS phase-9-camera")

camera.settings(ae_target=48, exposure_seed=160)
second = camera.capture()
settings = camera.settings()
assert len(second) == 460800
assert settings["ae_target"] == 48 and settings["exposure_seed"] == 160
assert settings["rust_heap_bytes"] == baseline
registers = i2c.readfrom_mem(0x30, 0x3e00, 3, addrsize=16)
actual = ((registers[0] & 15) << 12) | (registers[1] << 4) | (registers[2] >> 4)
assert actual == settings["exposure_lines"]
print("@@CAMERA_SETTINGS", settings)
print("@@PASS phase-9-camera-settings")

for _ in range(10):
    temporary = [bytearray(257) for _ in range(128)]
    temporary = None
    gc.collect()
try:
    bytearray(9 * 1024 * 1024)
    assert False
except MemoryError:
    pass
gc.collect()
try:
    Pin(99, Pin.OUT)
    assert False
except ValueError:
    pass
try:
    camera.settings(exposure_seed=-2)
    assert False
except ValueError:
    pass
camera.settings(ae_target=0, exposure_seed=122)
print("@@PASS phase-9-gc-exceptions")
print("@@PASS phase-9")
