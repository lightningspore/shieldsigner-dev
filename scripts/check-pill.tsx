import * as schemas from "circuit-json"
import assert from "node:assert/strict"
import { readFileSync } from "node:fs"
import { createHash } from "node:crypto"
import { Circuit } from "@tscircuit/core"
import { compileBoard } from "./build"
import reference from "../src/generated/pill-board.json"
import {readPillDetails} from "./pill-details"
import Preview from "../src/PillCarrierReference"

assert.equal(reference.source.sha256, createHash("sha256").update(readFileSync(reference.source.path)).digest("hex"), "KiCad changed: run mise run tscircuit:pill:generate before checking the port")
assert.deepEqual(reference.copperLayers, ['top','inner1','inner2','bottom'])
for (const layer of ['inner1','inner2']) {
 const planes=reference.fills.filter(f=>f.layer===layer)
 assert(planes.length>0 && planes.every(f=>f.net==='GND'))
}
assert.equal(reference.width, 160)
assert.equal(reference.height, 70)
assert.equal(reference.components.length, 71)
assert.deepEqual(reference.components.filter(p=>p.dnp).map(p=>p.name), [])
const header = reference.components.find(p=>p.name === 'J701')!
const expected = ['RPI_BACKLIGHT','LCD_RST','LCD_DC','RPI_SPI_CS','LCD_SCLK','LCD_MOSI','GND','LCD_3V3']
assert.equal(header.pads.length, 8)
for (const pad of header.pads) assert.equal(pad.net, expected[Number(pad.number)-1])
assert.deepEqual(reference.bridges.map(b=>b.reference).sort(), ['JP201','JP203','JP205'])
assert(!reference.components.some(p=>p.name === 'J302'))
for (let i=901;i<=908;i++) assert.equal(reference.components.find(p=>p.name === `TP${i}`)?.lcsc,'C2906768')
const circuit = await compileBoard({data:reference, allowedOutside:[]})
for (const e of circuit) schemas.any_circuit_element.parse(e)
const count = (type: string) => circuit.filter(e => e.type === type).length
assert.equal(count("source_component"), reference.components.length)
assert.equal(count("source_net"), reference.nets.length)
assert.equal(count("pcb_trace"), reference.segments.length)
assert.equal(count("pcb_via"), reference.vias.length)
assert.equal(count("pcb_copper_pour"), reference.fills.length + reference.bridges.length)
assert.equal(count("pcb_smtpad") + count("pcb_plated_hole"), reference.components.reduce((n,c)=>n+c.pads.length,0))
const ids = new Set(circuit.filter(e=>e.type === "source_net").map(e=>e.source_net_id))
for (const trace of circuit.filter(e=>e.type === "source_trace")) {
  for (const id of trace.connected_source_net_ids ?? []) assert(ids.has(id), "Dangling net reference")
}
for (const type of ["pcb_trace", "pcb_via"]) {
  for (const item of circuit.filter(e=>e.type === type)) assert(item.source_trace_id, `${type} lost electrical association`)
}
assert(!circuit.some(e=>e.type.endsWith("_error")))
const root = new Circuit()
root.add(<Preview />)
await root.renderUntilSettled()
const preview = root.getCircuitJson()
assert.equal(preview.filter(e=>e.type === "source_component").length, reference.components.length)
assert.equal(preview.filter(e=>e.type === "pcb_smtpad").length, count("pcb_smtpad"))
console.log("Checked pad geometry, component/net/copper counts, electrical associations, and native preview.")

// Compare routed coordinates and layers, not just element counts.
for (const [i,segment] of reference.segments.entries()) {
  const actual = circuit.find(e=>e.pcb_trace_id === `reference_track_${i}`)!
  assert.deepEqual(actual.route, [segment.start, segment.end].map(p=>({route_type:'wire',...p,width:segment.width,layer:segment.layer})))
}
for (const [i,bridge] of reference.bridges.entries()) {
  const actual = circuit.find(e=>e.pcb_copper_pour_id === `reference_bridge_${i}`)!
  assert.deepEqual(actual.points, bridge.points)
  assert.equal(actual.layer, bridge.layer)
  // The electrical bridge must merge both ports' connectivity groups.
  const sc = circuit.find(e=>e.type === 'source_component' && e.name === bridge.reference)!
  const ports = circuit.filter(e=>e.type === 'source_port' && e.source_component_id === sc.source_component_id)
  assert.equal(new Set(ports.map(e=>e.subcircuit_connectivity_map_key)).size, 1)
}
console.log('Checked pill LCD pinout, default copper bridges, assembly metadata and exact track routes.')

const details = readPillDetails()
assert.equal(count('pcb_silkscreen_graphic'), details.layers['F.SilkS'].length + details.layers['B.SilkS'].length)
assert.equal(count('pcb_solder_paste'), details.layers['F.Paste'].length + details.layers['B.Paste'].length)
assert.equal(count('pcb_soldermask_opening'), details.layers['F.Mask'].length + details.layers['B.Mask'].length)
assert.equal(count('pcb_courtyard_outline'), details.courtyards.length)
assert.equal(count('cad_component'), new Set(details.models.filter(m=>m.show).map(m=>m.reference)).size)
assert.equal(count('pcb_hole'), 12, 'Retain the two smartcard footprint Edge.Cuts holes as well as the six drilled holes')
assert.equal(circuit.find(e=>e.type==='pcb_board')!.thickness, 1.6)
for(const [side,native]of [['top','F.SilkS'],['bottom','B.SilkS']]) {
  const graphics=circuit.filter(e=>e.type==='pcb_silkscreen_graphic'&&e.layer===side)
  assert.deepEqual(graphics.map(e=>e.brep_shape),details.layers[native], `Changed ${side} lettering or artwork`)
}
assert(details.texts.some(t=>t.visible&&t.text==='denver.space'))
for(const e of circuit.filter(e=>e.type==='cad_component')) {
  assert(e.model_glb_url.startsWith('data:model/gltf-binary;base64,'))
  const bytes=Buffer.from(e.model_glb_url.split(',')[1],'base64')
  assert.equal(bytes.toString('ascii',0,4),'glTF')
  assert.equal(bytes.readUInt32LE(4),2)
  assert.equal(e.model_unit_to_mm_scale_factor,1000)
  assert.equal(e.position.z,e.layer==='bottom'?-.8:.8, 'Attach native models at the correct board surface')
  assert(Object.values(e.size).every(n=>typeof n==='number'&&n>0&&n<200), 'Model dimensions must be in millimetres')
}
console.log('Checked full silkscreen BReps, native mask/paste apertures, courtyards, footprint holes and embedded GLB model coverage.')
