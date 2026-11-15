# SPDX-License-Identifier: MIT
"""PUBLIC independent oracle for the native capture/word-page UI gate."""
import hashlib,json
from pathlib import Path
from PIL import Image
from embit import bip39,bip32
root=Path(__file__).resolve().parents[1]
cases=[]
for cycle in (1,2):
    def frame(n):return bytes((i+cycle*16+n)%256 for i in range(256))*1200+bytes([128])*153600
    chain=b''
    for n in range(4,9):
        image=Image.frombytes('L',(640,480),frame(n)[:307200])
        sample=bytes(image.getpixel((int((x+0.5)*640/96),int((y+0.5)*480/96))) for y in range(96) for x in range(96))
        chain=hashlib.sha256(chain+sample).digest()
    digest=hashlib.sha256(chain+frame(10)).digest()
    for count,size in ((12,16),(24,32)):
        words=bip39.mnemonic_from_bytes(digest[:size])
        fingerprint=bip32.HDKey.from_seed(bip39.mnemonic_to_seed(words)).my_fingerprint.hex()
        cases.append((cycle,count,words.split(),fingerprint))
dice=[]
for count,n in ((12,50),(24,99)):
    rolls=('123456'*20)[:n]
    words=bip39.mnemonic_from_bytes(hashlib.sha256(rolls.encode()).digest()[:16 if count==12 else 32])
    fingerprint=bip32.HDKey.from_seed(bip39.mnemonic_to_seed(words)).my_fingerprint.hex()
    dice.append((count,rolls,words.split(),fingerprint))
p=root/'micropython/camera_entropy_flow_gate.py'
text=p.read_text();start=text.index('# BEGIN PUBLIC ORACLE');end=text.index('# END PUBLIC ORACLE')
text=text[:start]+'# BEGIN PUBLIC ORACLE\nfixtures='+repr(cases)+'\ndice_fixtures='+repr(dice)+'\n'+text[end:]
p.write_text(text)
print('Generated public native camera flow oracle:',len(cases))
