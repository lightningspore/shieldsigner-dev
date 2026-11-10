import * as schema from 'circuit-json'
/** The pinned core emits several fields outside its peer circuit-json schema.
 * Record every mismatch, accept only these known upstream field families, and
 * keep the original render untouched. Never use this to waive circuit errors.
 */
const compatibilityFields:Record<string,string[]>={
  schematic_component:['port_arrangement'],schematic_group:['subcircuit_id'],
  pcb_group:['anchor_alignment'],pcb_component:['display_offset_x','display_offset_y'],
  pcb_silkscreen_text:['pcb_component_id'],pcb_silkscreen_path:['pcb_component_id'],
  pcb_silkscreen_circle:['pcb_component_id'],pcb_hole:[''],pcb_plated_hole:[''],
}
export function inspectPillSchema(circuit:any[]) {
  return circuit.flatMap(element=>{
    if(schema.any_circuit_element.safeParse(element).success)return []
    const result=(schema as any)[element.type]?.safeParse(element)
    const issues=result?.error?.issues
    if(!issues)throw new Error(`Unknown Circuit JSON element ${element.type}`)
    const allowed=compatibilityFields[element.type]
    if(!allowed||issues.some((i:any)=>!allowed.includes(String(i.path[0]??''))))
      throw new Error(`Unexpected schema mismatch: ${element.type}: ${JSON.stringify(issues)}`)
    // The unscoped hole union mismatch is only permitted for these core-native shapes.
    if(element.type==='pcb_hole'&&element.hole_shape!=='circle')throw new Error('Unexpected hole shape')
    if(element.type==='pcb_plated_hole'&&element.shape!=='circular_hole_with_rect_pad')throw new Error('Unexpected plated hole shape')
    return [{type:element.type,id:element[`${element.type}_id`],issues}]
  })
}
