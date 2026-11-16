# SPDX-License-Identifier: MIT
# Diagnostic luma-row export for local hardware evidence.
import camera
import binascii

camera.init()
frame = camera.capture()
print('@@LUMA_BEGIN 640 480')
for y in range(480):
    print('@@LUMA', y, binascii.hexlify(frame[y * 640 : (y + 1) * 640]).decode())
print('@@LUMA_END')
