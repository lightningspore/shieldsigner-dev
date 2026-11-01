"""Build native branding from pinned application PNGs using upstream converter.

Pillow is a build-host dependency only. Generated files stay under dist.
"""
from pathlib import Path
import hashlib,importlib.util,json,sys
from PIL import Image,ImageChops
app,screens,out=map(Path,sys.argv[1:]);out.mkdir(parents=True,exist_ok=True)
spec=importlib.util.spec_from_file_location('upstream_png_to_lvgl',screens/'scripts/png_to_lvgl.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
manifest=[]
for relative,name in [('logo_black_240.png','shieldsigner_logo_img'),('partners/sese_logo.png','shieldsigner_upstream_img')]:
    source=app/'src/seedsigner/resources/img'/relative
    with Image.open(source) as image:
        image=image.convert('RGB')
        box=ImageChops.difference(image,Image.new('RGB',image.size,'black')).getbbox()
        if box is None:raise ValueError('Pinned branding image is empty')
        image=image.crop(box)
        if image.width>240 or image.height>240:raise ValueError('Branding exceeds Mini display')
        png=out/(name+'.png');image.save(png)
        module.convert(str(png),str(out/(name+'.c')),image.height,name)
        manifest.append(dict(source=relative,sourceSha256=hashlib.sha256(source.read_bytes()).hexdigest(),crop=box,size=image.size,symbol=name))
(out/'branding.json').write_text(json.dumps(manifest,indent=2)+'\n')

# Embed the pinned application's exact fixed-width face for diagnostic columns.
font_source=app/'src/seedsigner/resources/fonts/Inconsolata-Regular.ttf'
font=font_source.read_bytes()
rows=[','.join('0x%02x'%value for value in font[i:i+16]) for i in range(0,len(font),16)]
(out/'shieldsigner_mono_ttf.c').write_text('#include <stdint.h>\nconst uint8_t shieldsigner_mono_ttf[]={\n'+',\n'.join(rows)+'\n};\nconst uint32_t shieldsigner_mono_ttf_len=sizeof(shieldsigner_mono_ttf);\n')
(out/'font.json').write_text(json.dumps(dict(source='src/seedsigner/resources/fonts/Inconsolata-Regular.ttf',sourceSha256=hashlib.sha256(font).hexdigest(),bytes=len(font),nativePixels=16),indent=2)+'\n')
