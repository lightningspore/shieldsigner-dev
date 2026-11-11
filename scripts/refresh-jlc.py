#!/usr/bin/env python3
"""Snapshot public JLCPCB catalog identities/availability without account writes."""
import argparse,csv,concurrent.futures,datetime,hashlib,json,re,time,urllib.request,urllib.error
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--only',nargs='+',help='Refresh only these LCSC codes, preserving other existing records')
parser.add_argument('--output',type=Path,help='Override the selected board catalog path')
parser.add_argument('--standard-fpc',action='store_true',help='Use historical FPC identities and catalog instead of the main board')
parser.add_argument('--dry-run',action='store_true',help='Print codes and output path without network requests or writes')
args=parser.parse_args()
if args.only:
 ids=set(args.only)
elif args.standard_fpc:
 board=json.loads((ROOT/'src/generated/reference-board.json').read_text())
 ids={c['lcsc'] for c in board['components'] if c.get('lcsc')}
 ids.update(['C2931360','C7278475','C633310'])
else:
 with (ROOT/'hardware/manufacturing/bom-jlcpcb.csv').open(newline='') as file:
  ids={r['LCSC Part #'] for r in csv.DictReader(file)}
args.output=args.output or ROOT/('docs/jlc-catalog.json' if args.standard_fpc else 'hardware/jlc-catalog.json')
assert ids and all(re.fullmatch(r'C[0-9]+',code) for code in ids),'Expected LCSC codes such as C633309'
if args.dry_run:
 print(json.dumps({'codes':sorted(ids),'output':str(args.output)},indent=2))
 raise SystemExit(0)
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
  flight=''.join(chunks);decoder=json.JSONDecoder();records=[];price_tiers=[]
  # React server data can contain length-prefixed strings between records.
  # Decode object starts, not assumed record IDs or a hypothetical public API.
  for m in re.finditer(r'\{',flight):
   try:obj,n=decoder.raw_decode(flight[m.start():])
   except json.JSONDecodeError:continue
   if isinstance(obj,dict) and obj.get('componentCode')==code:
    if obj.get('componentModelEn'):records.append(obj)
    if isinstance(obj.get('productPrice'),(int,float)) and obj.get('startNumber') is not None:price_tiers.append({k:obj[k] for k in ['startNumber','endNumber','productPrice']})
  if not records:raise RuntimeError('Catalog identity not present in server-rendered page')
  merged={}
  for obj in sorted(records,key=len):merged.update({k:v for k,v in obj.items() if not isinstance(v,str) or not v.startswith('$')})
  fields=['componentModelEn','componentBrandEn','componentSpecificationEn','describe','componentLibraryType','assemblyMode','canPresaleNumber','overseasStockCount','preMinPurchaseNum','leastPatchNumber','lossNumber','initialPrice','needAuditFlag','dataManualUrl','noBuyReason','isBuyComponent','attributes']
  result={k:merged[k] for k in fields if k in merged};result['priceTiers']=sorted({p['startNumber']:p for p in price_tiers}.values(),key=lambda p:p['startNumber']);result.update(code=code,url=url,checkedAt=datetime.datetime.now(datetime.timezone.utc).isoformat(),htmlSha256=hashlib.sha256(text.encode()).hexdigest(),status='public_catalog_snapshot')
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
