import {assembly} from '@tscircuit/core'
import {SupportHoleModel} from './models/SupportHole'
/** Capsule dimensions and mounting centres are mechanical interfaces. */
export function capsuleOutline(width=160,height=70) {
  const r=height/2,dx=(width-height)/2
  return Array.from({length:258},(_,i)=>{
    const side=i<129?1:-1, a=(i%129)/128*Math.PI-Math.PI/2
    return {x:side*(dx+r*Math.cos(a)),y:side*r*Math.sin(a)}
  })
}
export function Mechanics() { return <>
  <hole name="DRILL_H701" pcbX={-35.25} pcbY={23.9} diameter={2.7}/>
  <hole name="DRILL_H702" pcbX={47.25} pcbY={23.9} diameter={2.7}/>
  <hole name="DRILL_H703" pcbX={-35.25} pcbY={-23.9} diameter={2.7}/>
  <hole name="DRILL_H704" pcbX={47.25} pcbY={-23.9} diameter={2.7}/>
  <assembly.part name="H701" cadModel={{...SupportHoleModel,positionOffset:{x:-35.25,y:23.9,z:.8}}}/>
  <assembly.part name="H702" cadModel={{...SupportHoleModel,positionOffset:{x:47.25,y:23.9,z:.8}}}/>
  <assembly.part name="H703" cadModel={{...SupportHoleModel,positionOffset:{x:-35.25,y:-23.9,z:.8}}}/>
  <assembly.part name="H704" cadModel={{...SupportHoleModel,positionOffset:{x:47.25,y:-23.9,z:.8}}}/>
</> }
