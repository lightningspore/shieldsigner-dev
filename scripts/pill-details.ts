import {readFileSync} from 'node:fs'
import {createHash} from 'node:crypto'

type Point = {x:number,y:number}
type Shape = {outer_ring:{vertices:Point[]},inner_rings:{vertices:Point[]}[]}
export type PillDetails = {
  source:{path:string,sha256:string}, engine:string, thickness:number,
  layers:Record<string,Shape[]>, texts:{text:string,layer:string,visible:boolean}[],
  models:{reference:string,path:string,sha256:string,show:boolean}[],
  inventory:unknown[], pads:unknown[], courtyards:{reference:string,layer:string,shape:Shape}[]
}
export const readPillDetails = ():PillDetails => JSON.parse(readFileSync('src/generated/pill-details.json','utf8'))

/** Circuit JSON's native BRep retains counters in letters and logo cut-outs. */
export function attachPillDetails(circuit:any[]) {
  const details=readPillDetails()
  if(createHash('sha256').update(readFileSync(details.source.path)).digest('hex')!==details.source.sha256)
    throw new Error('Stale native details: run mise run tscircuit:pill:build')
  const board=circuit.find(e=>e.type==='pcb_board')
  board.thickness=details.thickness
  board.default_via_tented_on_top=true
  board.default_via_tented_on_bottom=true
  const subcircuit_id=board.subcircuit_id
  // Replace core's default chip boxes and automatically inferred paste apertures.
  // Mask apertures are explicit native geometry; do not also infer pad openings.
  for(let i=circuit.length-1;i>=0;i--)
    if(['cad_component','pcb_solder_paste'].includes(circuit[i].type))circuit.splice(i,1)
  for(const e of circuit)
    if(['pcb_smtpad','pcb_plated_hole'].includes(e.type))e.is_covered_with_solder_mask=true
  for(const [name,shapes]of Object.entries(details.layers)) {
    const layer=name.startsWith('B.')?'bottom':'top'
    for(const [i,shape]of shapes.entries()) {
      const id=`native_${name.replaceAll('.','_')}_${i}`
      const common={layer,subcircuit_id,pcb_component_id:''}
      if(name.endsWith('.SilkS'))circuit.push({type:'pcb_silkscreen_graphic',pcb_silkscreen_graphic_id:id,
        ...common,shape:'brep',brep_shape:shape})
      else if(name.endsWith('.Paste')||name.endsWith('.Mask')) {
        if(shape.inner_rings.length)throw new Error(`Unexpected aperture holes on ${name}`)
        const type=name.endsWith('.Paste')?'pcb_solder_paste':'pcb_soldermask_opening'
        circuit.push({type,[`${type}_id`]:id,...common,shape:'polygon',points:shape.outer_ring.vertices})
      } else if(name.endsWith('.Fab')) {
        // A connected path can represent counters without filling their interiors:
        // each inner contour returns along the same bridge to the outer contour.
        const route=[...shape.outer_ring.vertices,shape.outer_ring.vertices[0]]
        for(const hole of shape.inner_rings)route.push(hole.vertices[0],...hole.vertices,hole.vertices[0],route[0])
        circuit.push({type:'pcb_fabrication_note_path',pcb_fabrication_note_path_id:id,...common,
          route,stroke_width:0,is_filled:true,has_stroke:false})
      }
    }
  }
  const courtyardOwners = new Set<string>()
  for(const [i,courtyard] of details.courtyards.entries()) {
    const sc=circuit.find(e=>e.type==='source_component'&&e.name===courtyard.reference)
    const pc=circuit.find(e=>e.type==='pcb_component'&&e.source_component_id===sc.source_component_id)
    courtyardOwners.add(pc.pcb_component_id)
    circuit.push({type:'pcb_courtyard_outline',pcb_courtyard_outline_id:`native_courtyard_${i}`,
      pcb_component_id:pc.pcb_component_id,subcircuit_id,layer:courtyard.layer,
      outline:[...courtyard.shape.outer_ring.vertices,courtyard.shape.outer_ring.vertices[0]]})
  }
  for(let i=circuit.length-1;i>=0;i--)
    if(circuit[i].type==='pcb_component_missing_courtyard_warning'&&courtyardOwners.has(circuit[i].pcb_component_id))circuit.splice(i,1)
  const modelData=JSON.parse(readFileSync('dist/pill-tscircuit/models.json','utf8'))
  if(modelData.source.sha256!==details.source.sha256 || JSON.stringify(modelData.modelSources)!==JSON.stringify(details.models) ||
    modelData.converterSha256!==createHash('sha256').update(readFileSync('scripts/convert-pill-models.mjs')).digest('hex'))
    throw new Error('Stale converted models: run mise run tscircuit:pill:build')
  for(const model of details.models)
    if(createHash('sha256').update(readFileSync(model.path)).digest('hex')!==model.sha256)
      throw new Error(`Retained STEP model changed: ${model.path}`)
  for(const model of modelData.assets) {
    if(createHash('sha256').update(readFileSync(`dist/pill-tscircuit/${model.path}`)).digest('hex')!==model.sha256)
      throw new Error(`Converted GLB changed: ${model.path}`)
    const sc=circuit.find(e=>e.type==='source_component'&&e.name===model.reference)
    const pc=circuit.find(e=>e.type==='pcb_component'&&e.source_component_id===sc.source_component_id)
    circuit.push({type:'cad_component',cad_component_id:`native_model_${model.reference}`,
      source_component_id:sc.source_component_id,pcb_component_id:pc.pcb_component_id,subcircuit_id,
      position:model.position,rotation:{x:0,y:0,z:0},size:model.size,layer:pc.layer,
      model_glb_url:model.url,model_unit_to_mm_scale_factor:1000,
      model_origin_position:{x:0,y:0,z:0},model_origin_alignment:'unknown',
      model_object_fit:'contain_within_bounds',anchor_alignment:'center'})
  }
  return details
}

/** SVG plate in board coordinates, used for independent per-layer review. */
export function detailLayerSvg(shapes:Shape[],width:number,height:number) {
  const paths=shapes.map(shape=>`<path d="${[shape.outer_ring,...shape.inner_rings].map(r=>
    'M'+r.vertices.map(p=>`${p.x},${-p.y}`).join('L')+'Z').join(' ')}"/>`).join('')
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="${-width/2} ${-height/2} ${width} ${height}" width="${width}mm" height="${height}mm"><g fill="white" fill-rule="evenodd">${paths}</g></svg>`
}
