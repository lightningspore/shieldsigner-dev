#!/usr/bin/env python3
"""Download supplier-linked review datasheets; never print temporary signed URLs."""
import json,re,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
cache=ROOT/'reference/research/catalog-cache'
destination=ROOT/'reference/pdfs'
destination.mkdir(parents=True,exist_ok=True)
for code in ['C318938','C668623','C2931360','C5417011','C19077498','C2939938']:
 path=cache/(code+'.html')
 if not path.exists():continue
 chunks=[]
 for m in re.finditer(r'self\.__next_f\.push\((\[.*?\])\)</script>',path.read_text(),re.S):
  try:chunks.extend(x for x in json.loads(m[1]) if isinstance(x,str))
  except:pass
 text=''.join(chunks)
 urls=re.findall(r'https://jlc-prod-smt[^\s"<>]+?x-oss-signature=[0-9a-f]{64}',text)
 urls=[u for u in urls if code+'.pdf' in u]
 try:
  data=urllib.request.urlopen(urls[0],timeout=30).read();assert data.startswith(b'%PDF')
  (destination/(code+'.pdf')).write_bytes(data)
  print(code,'datasheet downloaded',len(data),'bytes')
 except Exception as e:print(code,type(e).__name__)
