"""Render a deliberately captured PUBLIC test framebuffer as PNG, host-side only.

Usage: uv run python firmware/lvgl-app/render_rgb565.py input.rgb565 output.png
Never capture or export wallet/seed screens with this diagnostic tool.
"""
from pathlib import Path
import struct,sys,zlib

def render(source,destination,width=240,height=240):
    raw=Path(source).read_bytes()
    if len(raw)!=width*height*2:raise ValueError('RGB565 framebuffer size mismatch')
    rgb=bytearray()
    for y in range(height):
        rgb.append(0) # PNG filter: none.
        for x in range(width):
            i=(y*width+x)*2;n=int.from_bytes(raw[i:i+2],'big')
            rgb.extend(((n>>11)*255//31,((n>>5)&63)*255//63,(n&31)*255//31))
    def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
    png=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>2I5B',width,height,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(rgb))+chunk(b'IEND',b'')
    Path(destination).write_bytes(png)
if __name__=='__main__':render(*sys.argv[1:])
