"""Byte-exact Pillow reference for a compiled native extension; no GPIO/SPI."""
import hashlib
import json
from PIL import Image, __version__ as pillow_version
from shieldsigner_lcd import PreviewRenderer

results=[]
for w,h,pw,ph in [(640,480,240,180),(320,240,240,180),(13,7,9,5),(1,1,1,1)]:
    pixels=bytes((x*7+y*13+(x//17)*31)&255 for y in range(h) for x in range(w))
    image=Image.frombytes('L',(w,h),pixels)
    renderer=PreviewRenderer(pw,ph)
    assert renderer.buffer_bytes==pw*ph*3
    for angle in [0,90,180,270]:
        expected=image.resize((pw,ph),Image.Resampling.NEAREST).convert('RGB').rotate(angle,expand=True)
        dw,dh,actual=renderer.render_luma(pixels,w,h,angle)
        assert (dw,dh)==expected.size
        reference=expected.tobytes()
        assert actual==reference, (w,h,pw,ph,angle,next((i for i,(a,b) in enumerate(zip(actual,reference)) if a!=b),None))
        results.append({'source':[w,h],'preview':[pw,ph],'angle':angle,'bytes':len(actual),'sha256':hashlib.sha256(actual).hexdigest()})
    saved=renderer.render_luma(pixels,w,h,0)[2]
    renderer.render_luma(bytes(w*h),w,h,0)
    assert saved==image.resize((pw,ph),Image.Resampling.NEAREST).convert('RGB').tobytes()
    for data,width,height,angle in [(pixels[:-1],w,h,0),(pixels,0,h,0),(pixels,w,h,45)]:
        try:renderer.render_luma(data,width,height,angle)
        except ValueError:pass
        else:raise AssertionError('Invalid preview input accepted')
print(json.dumps({'pillowVersion':pillow_version,'byteExactPillowCases':len(results),'immutableReturnedBytes':True,'invalidInputsRejected':True,'hardwareTouched':False,'cases':results},indent=2))
