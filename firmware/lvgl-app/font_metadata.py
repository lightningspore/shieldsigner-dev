"""Read public copyright/license name records in the pinned font-builder image."""
import json,hashlib
from pathlib import Path
from fontTools.ttLib import TTFont
roots=['application/src/seedsigner/resources/fonts','screens/components/seedsigner/assets','language-packs/fonts']
rows=[]
for root in roots:
 for path in sorted((Path('/inputs')/root).iterdir()):
  if path.suffix.lower() not in ('.ttf','.otf'):continue
  font=TTFont(path);names={}
  for identifier in (0,1,2,3,5,6,13,14):
   values=[]
   for item in font['name'].names:
    if item.nameID==identifier:
     value=item.toUnicode()
     if value not in values:values.append(value)
   names[str(identifier)]=values
  font.close();rows.append(dict(path=str(path.relative_to('/inputs')),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),names=names))
print(json.dumps(rows,ensure_ascii=False,indent=2))
