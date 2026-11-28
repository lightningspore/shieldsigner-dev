"""Nominal current mating geometry from XKB X6511WVS and Harwin M20-782 drawings."""
from pathlib import Path
import cadquery as cq
folder=Path(__file__).resolve().parents[1]/'variants/full-size-pico/models'
male=cq.Assembly(name='XKB_R2_20P_SMT_male_nominal')
# Manufacturer component-side drawing: row along X, pin 1 on left, tail -Y.
male.add(cq.Workplane('XY').box(50.8,2.5,2.5,centered=(True,True,False)).translate((0,0,.64)),name='housing',color=cq.Color(.06,.06,.065))
for i in range(20):
 x=-24.13+i*2.54;sign=-1 if i%2==0 else 1
 pin=cq.Workplane('XY').box(.64,.64,8.5,centered=(True,True,False)).translate((x,0,.64))
 tail=cq.Workplane('XY').box(.64,2.4,.64,centered=(True,True,False)).translate((x,sign*1.2,0))
 male.add(pin.union(tail),name=f'contact_{i+1}',color=cq.Color(.8,.68,.22))
male.save(str(folder/'XKB-SMT-male-nominal.step'))
female=cq.Assembly(name='Harwin_M20_7822042_on_Pico_nominal')
for row,x in enumerate([-8.89,8.89]):
 body=cq.Workplane('XY').box(2.5,51.2,8.5,centered=(True,True,False)).translate((x,0,3.14))
 for i in range(20):
  y=-24.13+i*2.54
  body=body.cut(cq.Workplane('XY').box(.9,.9,6.5,centered=(True,True,False)).translate((x,y,3.14)))
  tail=cq.Workplane('XY').box(.25,.65,3,centered=(True,True,False)).translate((x,y,11.64))
  female.add(tail,name=f'tail_{row}_{i}',color=cq.Color(.72,.73,.75))
 female.add(body,name=f'housing_{row}',color=cq.Color(.06,.06,.065))
female.save(str(folder/'Pico-female-sockets-nominal.step'))
print('Nominal module underside 11.64 mm; male pin projection 6 mm; female depth 8.5 mm.')
