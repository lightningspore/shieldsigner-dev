"""Draw the exact strip placement and a supplier-controlled assembly-panel proposal."""
from pathlib import Path
import math,json
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'variants/full-size-pico/manufacturing'
# Coordinate proposal only. The assembler generates/reviews the production panel.
y0=54.579;y1=124.579;cy=89.579;rad=35
svg=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="28 26 200 126"><rect x="28" y="26" width="200" height="126" fill="white"/><style>text{font-family:sans-serif;fill:#172c3e} .small{font-size:2.5px}.title{font-size:4px;font-weight:bold}</style><text class="title" x="35" y="33">10-board prototype — one-up panel proposal</text><text class="small" x="35" y="38">NOT FABRICATION DATA. JLCPCB must approve tooling and routed tabs.</text>']
for x in [36,210]:svg.append(f'<rect x="{x}" y="46.579" width="10" height="86" fill="#e2e9ed" stroke="#172c3e" stroke-width=".25"/>')
svg.append(f'<path d="M83,{y0}H173 A35,35 0 0 1 173,{y1}H83 A35,35 0 0 1 83,{y0}Z" fill="#eef5ed" stroke="#24583a" stroke-width=".3"/>')
for y in [cy-12,cy+12]:
 edge=83-math.sqrt(rad*rad-(y-cy)**2)
 for a,b in [(46,edge+1.3),(256-edge-1.3,210)]:svg.append(f'<rect x="{a}" y="{y-1.5}" width="{b-a}" height="3" fill="#d6aa52" stroke="#9d721c" stroke-width=".2"/>')
for x in [41,215]:
 for y in [51.579,127.579]:svg.append(f'<circle cx="{x}" cy="{y}" r="1" fill="white"/><circle cx="{x}" cy="{y}" r=".5" fill="#bd7b24"/>')
 svg.append(f'<circle cx="{x}" cy="89.579" r="1.5" fill="white" stroke="#172c3e" stroke-width=".2"/>')
svg+=['<text class="small" x="95" y="88">160 × 70 mm finished carrier</text>','<text class="small" x="86" y="94">Four routed tabs; 10 mm removable side rails</text>','<text class="small" x="36" y="140">Proposed panel: 184 × 86 mm. Four 1 mm fiducials / 2 mm mask openings.</text>','<text class="small" x="36" y="145">Fiducial centers ≥5 mm from rail edges. Supplier controls final tab/tooling geometry.</text>','</svg>']
(M/'panel-proposal.svg').write_text(''.join(svg))
# Back/component-side view: native X is mirrored; Y follows the PCB drawing.
svg=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 610"><rect width="960" height="610" fill="white"/><style>text{font-family:sans-serif;fill:#172c3e}.title{font-size:23px;font-weight:bold}.body{font-size:15px}.small{font-size:12px}</style><text class="title" x="35" y="33">Full-size Pico: physical header placement</text><text class="body" x="35" y="58">Back/component-side view • J203 and J204 are separate factory placements.</text><path d="M175,90 H535 A140,140 0 0 1 535,370 H175 A140,140 0 0 1 175,90Z" fill="#edf4ef" stroke="#2c6040" stroke-width="2"/>']
px=lambda x:35+(208-x)*4;py=lambda y:90+(y-y0)*4
for ref,x in [('J203',85.3475),('J204',103.1275)]:
 xx=px(x);svg.append(f'<rect x="{xx-5}" y="{py(56.049)}" width="10" height="203.2" fill="#353b41"/>')
 for i in range(20):
  tail=x+(1.8 if i%2==0 else -1.8);svg.append(f'<rect x="{px(tail)-4.4}" y="{py(57.319+i*2.54)-2.54}" width="8.8" height="5.08" fill="#c78832"/>')
 svg.append(f'<circle cx="{xx}" cy="{py(105.579)}" r="5" fill="none" stroke="#b32822" stroke-width="2"/><text class="body" x="{xx-24}" y="{py(109.5)}">{ref}</text>')
svg+=['<text class="body" x="710" y="108">Exact carrier part:</text>','<text class="small" x="710" y="132">XKB X6511WVS-20H-</text>','<text class="small" x="710" y="150">C60D48R2 / C2883777</text>','<text class="small" x="710" y="178">20 contacts per strip</text>','<text class="small" x="710" y="196">Pitch: 2.54 mm</text>','<text class="small" x="710" y="214">Rows: 17.78 mm apart</text>','<text class="small" x="710" y="242">Red circle: part pin 1</text>','<text class="small" x="710" y="260">at native Y = 105.579 mm.</text>','<text class="small" x="710" y="288">Check every R2 SMT tail</text>','<text class="small" x="710" y="306">against the upload preview.</text><text class="small" x="710" y="334">Pico USB / pins 1,40: upper end.</text><text class="small" x="710" y="352">Red marks: XKB part pin 1.</text><text class="body" x="440" y="84">PICO USB END</text>','<text class="title" x="35" y="418">Mating stack (schematic; not to scale)</text>','<rect x="42" y="540" width="550" height="12" fill="#286241"/>','<rect x="170" y="510" width="90" height="25" fill="#353b41"/>','<rect x="170" y="438" width="90" height="72" fill="#59616b"/>','<rect x="160" y="429" width="110" height="9" fill="#286241"/>','<text class="small" x="290" y="444">Pico underside: 11.64 mm above carrier</text>','<text class="small" x="290" y="470">Module-side socket: Harwin M20-7822042, 8.5 mm</text>','<text class="small" x="290" y="496">Male mating pin: 6 mm; socket contact point: 3.41 mm</text>','<text class="small" x="290" y="522">SMT male insulator top: 3.14 mm above carrier</text>','<text class="small" x="35" y="582">Module sockets are customer-fitted to an unheadered Pico. No adapter PCB. Physical fit remains to be verified.</text>','</svg>']
(M/'header-assembly.svg').write_text(''.join(svg))
print('Drew exact header locations and a separately identified supplier panel proposal.')
