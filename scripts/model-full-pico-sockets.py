"""Nominal Harwin/socket mating envelopes; not manufacturer-supplied CAD."""
from pathlib import Path
import cadquery as cq

root=Path(__file__).resolve().parents[1];folder=root/'variants/full-size-pico/models'
body=cq.Workplane('XY').box(2.5,51,7.1,centered=(True,True,False)).translate((0,0,.4))
for i in range(20):
 y=24.13-2.54*i
 body=body.cut(cq.Workplane('XY').box(.9,.9,8,centered=(True,True,False)).translate((0,y,0)))
assembly=cq.Assembly(name='Harwin_M20_7862042_nominal')
assembly.add(body,name='housing',color=cq.Color(.06,.06,.065))
for i in range(20):
 x=-1.65 if i%2==0 else 1.65;y=24.13-2.54*i
 tail=cq.Workplane('XY').box(.7,.6,.4,centered=(True,True,False)).translate((x,y,0))
 assembly.add(tail,name=f'tail_{i+1}',color=cq.Color(.72,.73,.75))
assembly.save(str(folder/'Harwin-M20-7862042-nominal.step'))
male=cq.Assembly(name='Pico_two_male_headers_nominal')
for row,x in enumerate([-8.89,8.89]):
 male.add(cq.Workplane('XY').box(2.54,50.8,2.54,centered=(True,True,False)).translate((x,0,7.5)),name=f'insulator_{row}',color=cq.Color(.06,.06,.065))
 for i in range(20):
  pin=cq.Workplane('XY').box(.64,.64,10.2,centered=(True,True,False)).translate((x,24.13-2.54*i,1.5))
  male.add(pin,name=f'pin_{row}_{i}',color=cq.Color(.8,.68,.22))
male.save(str(folder/'Pico-mating-headers-nominal.step'))
print('Saved nominal 7.5 mm sockets / 10.04 mm module underside mating envelopes')
