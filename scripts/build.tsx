import { Circuit } from "@tscircuit/core"
import { convertCircuitJsonToPcbSvg, convertCircuitJsonToSchematicSvg } from "circuit-to-svg"
import { mkdirSync, writeFileSync, readFileSync } from "node:fs"
import { createHash } from "node:crypto"
import { ShieldSignerPlus, type ReferenceBoard } from "../src/ShieldSignerPlus"
import {attachPillDetails, detailLayerSvg} from "./pill-details"
import standardReference from "../src/generated/reference-board.json"

/** Reuse pinned reference copper rather than silently rerouting a card reader.
 * All electrical components, ports, footprints and net connections are rendered
 * by native TSX. Copper is mapped onto the rendered IDs and checked below.
 */
export async function compileBoard(options: {writeReport?: boolean, data?: ReferenceBoard, outputDir?: string, allowedOutside?: string[]} = {}) {
  const reference: ReferenceBoard = options.data ?? standardReference
  const outputDir = options.outputDir ?? "dist"
  if (createHash("sha256").update(readFileSync(reference.source.path)).digest("hex") !== reference.source.sha256) throw new Error(`KiCad changed: run mise run ${options.data?.bridges ? "tscircuit:pill:generate" : "generate"}`)
  const root = new Circuit()
  root.add(<ShieldSignerPlus data={reference} />)
  await root.renderUntilSettled()
  const circuit: any[] = root.getCircuitJson()
  const errors = circuit.filter((e) => e.type.endsWith("_error"))
  // Module/switch body bounding boxes span the intentional board notch.
  // Verify every actual land below before recording these known box warnings.
  const unexpected = errors.filter(e => e.type !== "pcb_component_outside_board_error" || !(options.allowedOutside ?? ["SW503", "U202"]).includes(circuit.find(c => c.source_component_id === e.source_component_id && c.type === "source_component")?.name))
  if (unexpected.length) throw new Error(JSON.stringify(unexpected, null, 2))
  const components = circuit.filter(e => e.type === "source_component")
  const nets = new Map(circuit.filter(e => e.type === "source_net").map(e => [e.name,e]))
  const netIds = new Map(reference.nets.map(n => [n.label,nets.get(n.name)?.source_net_id]))
  const board = circuit.find(e => e.type === "pcb_board")
  for (const part of reference.components) {
    const source = components.find(e => e.name === part.name)
    if (!source) throw new Error(`Missing component ${part.name}`)
    const pcb = circuit.find(e => e.type === "pcb_component" && e.source_component_id === source.source_component_id)
    // pcb_component.center is the footprint bounding-box center, not its
    // KiCad origin. Individual land geometry is the placement authority.
    pcb.layer = part.layer
    for (const pad of part.pads) {
      const port = circuit.find(e => e.type === "source_port" && e.source_component_id === source.source_component_id && e.port_hints?.includes(pad.port))
      if (!port) throw new Error(`Missing ${part.name}.${pad.port}`)
      const pcbPort = circuit.find(e => e.type === "pcb_port" && e.source_port_id === port.source_port_id)
      const primitives = circuit.filter(e => (e.type === "pcb_smtpad" || e.type === "pcb_plated_hole") && e.pcb_port_id === pcbPort?.pcb_port_id)
      if (primitives.length !== 1) throw new Error(`Expected one physical land for ${part.name}.${pad.port}: ${primitives.length}`)
      const physical = primitives[0]
      if (physical.shape !== "polygon" && Math.hypot(physical.x-pad.absolute.x,physical.y-pad.absolute.y) > 1e-4) {
        throw new Error(`Pad moved: ${part.name}.${pad.port}`)
      }
      if (physical.shape === "polygon") {
        const expected = pad.polygon.map(p => ({x:p.x+pad.absolute.x,y:p.y+pad.absolute.y}))
        if (physical.points.length !== expected.length || expected.some((p,i) => Math.hypot(p.x-physical.points[i].x,p.y-physical.points[i].y)>1e-4)) {
          throw new Error(`Polygon changed: ${part.name}.${pad.port}`)
        }
      }
    }
  }
  // Retain native ownership of mechanical holes, so a footprint's own hole
  // is not mistaken for an unrelated object intersecting its courtyard.
  const holes = circuit.filter(e=>e.type === "pcb_hole")
  for (const [index,hole] of reference.holes.entries()) {
    const name = (hole as typeof hole & {reference?:string}).reference
    if (!name) continue
    const source = components.find(e=>e.name === name)
    const owner = circuit.find(e=>e.type === "pcb_component" && e.source_component_id === source?.source_component_id)
    const physical = holes[index]
    if (!owner || !physical || Math.hypot(physical.x-hole.x,physical.y-hole.y)>1e-4) throw new Error(`Hole ownership mismatch: ${name}`)
    physical.pcb_component_id = owner.pcb_component_id
  }
  for (const n of reference.nets) {
    const net = nets.get(n.name)
    if (!net) throw new Error(`Missing net ${n.label}`)
    net.name = n.label
  }
  const common = {subcircuit_id:board.subcircuit_id}
  const traceIds = new Map<string,string>()
  for (const trace of circuit.filter(e=>e.type === "source_trace")) {
    for (const id of trace.connected_source_net_ids ?? []) if (!traceIds.has(id)) traceIds.set(id,trace.source_trace_id)
  }
  for (const [i,s] of reference.segments.entries()) {
    const net = netIds.get(s.net)
    if (!net) throw new Error(`Copper has unknown net: ${s.net}`)
    circuit.push({type:"pcb_trace",pcb_trace_id:`reference_track_${i}`,source_trace_id:traceIds.get(net),...common,
      route:[s.start,s.end].map(p=>({route_type:"wire",...p,width:s.width,layer:s.layer})),
      trace_length:Math.hypot(s.start.x-s.end.x,s.start.y-s.end.y)})
  }
  for (const [i,v] of reference.vias.entries()) {
    const net = netIds.get(v.net)
    if (!net) throw new Error(`Via has unknown net: ${v.net}`)
    const key = circuit.find(e=>e.type === "source_net" && e.source_net_id===net)?.subcircuit_connectivity_map_key
    circuit.push({type:"pcb_via",pcb_via_id:`reference_via_${i}`,x:v.x,y:v.y,
      hole_diameter:v.holeDiameter,outer_diameter:v.outerDiameter,layers:reference.copperLayers ?? ["top","bottom"],
      from_layer:"top",to_layer:"bottom",subcircuit_connectivity_map_key:key,source_trace_id:traceIds.get(net),...common})
  }
  for (const [i,fill] of reference.fills.entries()) circuit.push({
    type:"pcb_copper_pour",pcb_copper_pour_id:`reference_fill_${i}`,shape:"polygon",points:fill.points,
    layer:fill.layer,source_net_id:netIds.get(fill.net),covered_with_solder_mask:true,...common,
  })
  for (const [i,bridge] of (reference.bridges ?? []).entries()) circuit.push({
    type:"pcb_copper_pour", pcb_copper_pour_id:`reference_bridge_${i}`, shape:"polygon",
    points:bridge.points, layer:bridge.layer, source_net_id:netIds.get(bridge.nets[0]),
    covered_with_solder_mask:false, ...common,
  })
  // Normalize fields emitted inconsistently by this core version.
  for (const e of circuit) {
    if (e.type === "pcb_component") {
      e.display_offset_x = String(e.display_offset_x)
      e.display_offset_y = String(e.display_offset_y)
    }
    if (e.type === "pcb_hole" && e.pcb_component_id === null) delete e.pcb_component_id
    if (e.type === "pcb_plated_hole" && e.shape === "circular_hole_with_rect_pad") { e.hole_ccw_rotation = 0; e.ccw_rotation = 0; e.hole_shape = "circle"; e.pad_shape = "rect" }
  }
  const details = reference.bridges ? attachPillDetails(circuit) : undefined
  if (options.writeReport) {
    mkdirSync(outputDir, {recursive:true})
    writeFileSync(`${outputDir}/validation-report.json`, JSON.stringify({
      source: reference.source,
      nativeDetails: details ? {engine:details.engine,layers:Object.fromEntries(Object.entries(details.layers).map(([name,shapes])=>[name,shapes.length])),modelInstances:details.models.length,textItems:details.texts.length} : undefined,
      scope: "Pad, artwork, aperture, courtyard and model fidelity; not hardware qualification",
      preservedWarnings: [...errors,...circuit.filter(e=>e.type.endsWith("_warning"))],
      assemblyDnp: reference.components.filter(p=>p.dnp).map(p=>p.name),
      routing: "Pinned KiCad copper appended after native render; clearance/connectivity DRC not rerun on appended copper",
    }, null, 2)+"\n")
  }
  return circuit.filter(e => !errors.includes(e))
}

if (import.meta.main) {
  const pill = process.argv.includes('--pill')
  const reference: ReferenceBoard = pill ? (await import('../src/generated/pill-board.json')).default : standardReference
  const outputDir = pill ? 'dist/pill-tscircuit' : 'dist'
  const circuit = await compileBoard({writeReport:true, data:reference, outputDir, allowedOutside:pill ? [] : undefined})
  mkdirSync(outputDir,{recursive:true})
  writeFileSync(`${outputDir}/shieldsigner-plus.circuit.json`,JSON.stringify(circuit,null,2)+"\n")
  for (const layer of ["top","bottom"] as const) writeFileSync(`${outputDir}/pcb-${layer}.svg`,convertCircuitJsonToPcbSvg(circuit,{layer,width:1600,height:700,shouldDrawRatsNest:false,matchBoardAspectRatio:true,showFabricationNotes:false,showCourtyards:false}))
  if (pill) {
    const details = JSON.parse(readFileSync('src/generated/pill-details.json','utf8'))
    mkdirSync(`${outputDir}/layers`,{recursive:true})
    for(const [name,shapes] of Object.entries(details.layers))
      writeFileSync(`${outputDir}/layers/${name}.svg`,detailLayerSvg(shapes as any,reference.width,reference.height))
  }
  writeFileSync(`${outputDir}/schematic.svg`,convertCircuitJsonToSchematicSvg(circuit,{width:2200,height:1800}))
  const bom = reference.components.map(p=>({reference:p.name,value:p.value,footprint:p.footprint,layer:p.layer,x:p.x,y:p.y,dnp:p.dnp,excludeFromBom:p.excludeFromBom,lcsc:p.lcsc,datasheet:p.datasheet}))
  writeFileSync(`${outputDir}/bom.json`,JSON.stringify(bom,null,2)+"\n")
  mkdirSync(`${outputDir}/tscircuit-preview`,{recursive:true})
  writeFileSync(`${outputDir}/tscircuit-preview/board.circuit.json`, JSON.stringify(circuit,null,2)+"\n")
  console.log(`Built ${reference.components.length} components, ${reference.nets.length} nets, ${reference.segments.length} reference tracks and ${reference.vias.length} vias.`)
}
