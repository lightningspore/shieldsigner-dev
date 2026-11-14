# SPDX-License-Identifier: MIT
# Run only on DUT0's camera fixture, not the LCD target.
import camera
camera.init()
frame=camera.capture()
print('@@RGB_BEGIN 160 120')
for y in range(0,480,4):
    row=''
    for x in range(0,640,4):
        c=frame[y*640+x]-16
        uv=307200+(y//2)*640+(x//2)*2
        d=frame[uv]-128
        e=frame[uv+1]-128
        r=max(0,min(255,(298*c+409*e+128)>>8))
        g=max(0,min(255,(298*c-100*d-208*e+128)>>8))
        b=max(0,min(255,(298*c+516*d+128)>>8))
        digits='0123456789abcdef'
        row+=digits[r>>4]+digits[r&15]+digits[g>>4]+digits[g&15]+digits[b>>4]+digits[b&15]
    print('@@RGB',row)
print('@@RGB_END')
print('@@PASS camera-observer')
