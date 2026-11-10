import assert from 'node:assert/strict'
import {readFileSync,readdirSync} from 'node:fs'
import {createHash} from 'node:crypto'
import {inspectPillSchema} from './pill-schema'
const dir='dist/pill-native'
const circuit:any[]=JSON.parse(readFileSync(`${dir}/board.circuit.json`,'utf8'))
const report=JSON.parse(readFileSync(`${dir}/build-report.json`,'utf8'))
for(const [path,sha] of Object.entries(report.sourceSha256))
  assert.equal(createHash('sha256').update(readFileSync(path)).digest('hex'),sha,`Source changed; run mise run tscircuit:pill:build (${path})`)
inspectPillSchema(circuit)
assert.deepEqual(circuit.filter(e=>e.type.endsWith('_error')),[],'Native renderer must pass without suppressing errors')
const sources=circuit.filter(e=>e.type==='source_component')
const counts=Object.fromEntries([...new Set(sources.map(e=>e.ftype))].map(t=>[t,sources.filter(e=>e.ftype===t).length]))
assert.equal(sources.length,60)
// Catch symbols that compile electrically but accidentally hide their terminals.
const portOwners=new Map(circuit.filter(e=>e.type==='source_port').map(e=>[e.source_port_id,e.source_component_id]))
for(const part of sources) {
  const expected=({J301:4,J302:2,J601:10,J701:8,U202:22,U601:25,U701:5}as Record<string,number>)[part.name]
    ??(part.ftype==='subassembly'?0:part.ftype==='simple_test_point'?1:2)
  assert.equal(circuit.filter(e=>e.type==='schematic_port'&&portOwners.get(e.source_port_id)===part.source_component_id).length,expected,`${part.name}: visible schematic terminals`)
}
assert.equal(counts.simple_chip,9,'Three IC/module devices and six native solderjumpers use the core simple_chip record')
assert.equal(counts.simple_resistor,10)
assert.equal(counts.simple_capacitor,11)
assert.equal(counts.simple_push_button,8)
assert.equal(counts.simple_test_point,12)
assert.equal(counts.simple_connector,4)
assert.equal(circuit.filter(e=>e.type==='schematic_sheet').length,7)
assert.equal(circuit.filter(e=>e.type==='pcb_hole').length,8)
assert(circuit.some(e=>e.type==='pcb_trace'&&e.route.length>2),'Native router must produce real routed connections')
assert(circuit.some(e=>e.type==='pcb_via'),'Native router must generate inter-layer routing')
assert(!circuit.some(e=>e.pcb_trace_id?.startsWith('reference_')))
assert(circuit.filter(e=>e.type==='pcb_copper_pour').length>=2)
const graphics=circuit.filter(e=>e.type==='pcb_silkscreen_graphic')
assert.equal(graphics.filter(e=>e.layer==='top').length,2,'Front shield contours')
assert.equal(graphics.filter(e=>e.layer==='bottom'&&e.brep_shape.outer_ring.vertices[0].x<0).length,2,'Rear shield contours')
assert.equal(graphics.filter(e=>e.layer==='bottom'&&e.brep_shape.outer_ring.vertices[0].x>0).length,12,'Space logo contours')
assert(circuit.some(e=>e.type==='pcb_silkscreen_text'&&e.text==='denver.space'))
assert.equal(circuit.filter(e=>e.type==='cad_component'&&e.model_glb_url).length,42)
// Enforce the architectural contract: source owns the design, not native snapshots.
for(const path of ['src/PillCarrier.tsx',...readdirSync('src/pill',{recursive:true}).filter(p=>typeof p==='string'&&/\.tsx?$/.test(p)).map(p=>`src/pill/${p}`)]) {
  const source=readFileSync(path,'utf8')
  assert(!/src\/generated|\.\.\/generated|pill-board\.json|pill-details\.json|\.kicad_pcb|readFileSync|pcbRouteCache/.test(source),`Runtime snapshot dependency in ${path}`)
}
console.log('Checked semantic component types, seven functional sheets, native routing/pours, source-owned artwork/models and absence of runtime KiCad imports or geometry patches.')
