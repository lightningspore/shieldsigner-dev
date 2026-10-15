#!/usr/bin/env python3
"""Snapshot public JLCPCB catalog identities/availability without account writes."""
import argparse,concurrent.futures,datetime,hashlib,json,re,time,urllib.request,urllib.error
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
board=json.loads((ROOT/'src/generated/reference-board.json').read_text())
ids={c['lcsc'] for c in board['components'] if c.get('lcsc')}
ids.update(['C2931360','C7278475','C633310'])
parser=argparse.ArgumentParser();parser.add_argument('--only',nargs='+');parser.add_argument('--output',type=Path,default=ROOT/'docs/jlc-catalog.json');args=parser.parse_args()
if args.only:ids=set(args.only)
CACHE=ROOT/'reference/research/catalog-cache';CACHE.mkdir(parents=True,exist_ok=True)

def snapshot(code):
 url='https://jlcpcb.com/partdetail/'+code
 path=CACHE/(code+'.html')
 try:
  request=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
  for attempt in range(3):
   try:
    text=urllib.request.urlopen(request,timeout=45).read().decode('utf-8');break
   except urllib.error.HTTPError as error:
    if error.code!=429 or attempt==2:raise
    time.sleep(2*(attempt+1))
  path.write_text(text)
  chunks=[]
  for m in re.finditer(r'self\.__next_f\.push\((\[.*?\])\)</script>',text,re.S):
   try:chunks.extend(x for x in json.loads(m[1]) if isinstance(x,str))
   except json.JSONDecodeError:continue
  flight=''.join(chunks);decoder=json.JSONDecoder();records=[]
  # React server data can contain length-prefixed strings between records.
  # Decode object starts, not assumed record IDs or a hypothetical public API.
  for m in re.finditer(r'\{',flight):
   try:obj,n=decoder.raw_decode(flight[m.start():])
   except json.JSONDecodeError:continue
   if isinstance(obj,dict) and obj.get('componentCode')==code and obj.get('componentModelEn'):records.append(obj)
  if not records:raise RuntimeError('Catalog identity not present in server-rendered page')
  merged={}
  for obj in sorted(records,key=len):merged.update({k:v for k,v in obj.items() if not isinstance(v,str) or not v.startswith('$')})
  fields=['componentModelEn','componentBrandEn','componentSpecificationEn','describe','componentLibraryType','assemblyMode','canPresaleNumber','overseasStockCount','preMinPurchaseNum','leastPatchNumber','lossNumber','initialPrice','needAuditFlag','dataManualUrl','noBuyReason','isBuyComponent','attributes']
  result={k:merged[k] for k in fields if k in merged};result.update(code=code,url=url,checkedAt=datetime.datetime.now(datetime.timezone.utc).isoformat(),htmlSha256=hashlib.sha256(text.encode()).hexdigest(),status='public_catalog_snapshot')
  return result
 except Exception as error:return {'code':code,'url':url,'status':'unverified','error':str(error)}
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:results=list(pool.map(snapshot,sorted(ids)))
if args.only and args.output.exists():
 old=json.loads(args.output.read_text())['parts']
 results=sorted([r for r in old if r['code'] not in ids]+results,key=lambda r:r['code'])
args.output.parent.mkdir(parents=True,exist_ok=True)
args.output.write_text(json.dumps({'note':'Public catalog snapshot, not a stock reservation or confirmed assembly quote. Raw stock field names retained deliberately.','parts':results},indent=2,ensure_ascii=False)+'\n')
for r in results:print(r['code'],r.get('componentModelEn',r.get('error')), 'assembly',r.get('canPresaleNumber'),'overseas',r.get('overseasStockCount'))
assert all(r['status']=='public_catalog_snapshot' for r in results), 'Some catalog lookups failed; retain unverified status and retry.'
