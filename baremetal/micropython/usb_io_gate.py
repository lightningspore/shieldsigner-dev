# SPDX-License-Identifier: MIT
# No GPIO writes: safe on either debug fixture or LCD carrier.
import gc

for length in [0, 1, 511, 512, 513, 4096, 8192, 32768]:
    block = "0123456789abcdef" * (length // 16)
    for index in range(length % 16):
        block += "0123456789abcdef"[index]
    print("@@USB_BYTES", length, block)
    gc.collect()
print("@@PASS usb-io")
