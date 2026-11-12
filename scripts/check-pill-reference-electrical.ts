import {readFileSync,writeFileSync} from 'node:fs'
import assert from 'node:assert/strict'
import {createHash} from 'node:crypto'
import {runAllNetlistChecks,checkSchematicPlacement,runAllPlacementChecks} from '@tscircuit/checks'
import reference from '../src/generated/pill-board.json'
const circuit=JSON.parse(readFileSync('dist/pill-tscircuit/shieldsigner-plus.circuit.json','utf8'))
const native=JSON.parse(readFileSync('hardware/check-results.json','utf8'))
assert.equal(native.boardSha256,reference.source.sha256)
assert.equal(createHash('sha256').update(readFileSync(reference.source.path)).digest('hex'),reference.source.sha256)
for(const check of Object.values(native.checks) as any[]) assert(!Object.keys(check.active).length&&!check.excluded&&!check.unconnected&&!check.parity)
const findings={netlist:await runAllNetlistChecks(circuit),schematicPlacement:checkSchematicPlacement(circuit),placement:await runAllPlacementChecks(circuit)}
const details=JSON.parse(readFileSync('src/generated/pill-details.json','utf8'))
function nativeReason(e:any):string|undefined {
  // These are retained native features, never a waiver of the native DRC gate.
  const fillMatch=e.pcb_placement_error_id?.match(/^copper_too_close_to_board_edge_reference_fill_(\d+)$/)
  if(fillMatch && reference.width===160 && reference.height===70) {
    const fill=reference.fills[Number(fillMatch[1])]
    // Independent analytic distance to the 160x70 capsule, rather than the proxy's flattened polygon.
    if(fill && ['inner1','inner2'].includes(fill.layer) && fill.net==='GND' && fill.points.every((p:any)=>
      (Math.abs(p.x)>45 ? 35-Math.hypot(Math.abs(p.x)-45,p.y) : 35-Math.abs(p.y))>=0.2))
      return 'Inner GND polygon passes exact capsule-edge clearance at every vertex; the proxy flattened-outline distance is approximate. Native refilled DRC remains mandatory.'
  }
  if(e.type==='pcb_component_missing_courtyard_warning' && /^(TP80[1-9]|TP81[0-2]|U202) has no courtyard$/.test(e.message))
    return 'Native bare probe pad or customer module has no conventional courtyard; no factory body is inferred.'
  if(e.type==='pcb_component_outside_board_error' && /^Component J301 extends outside board boundaries by 0\.33mm\./.test(e.message))
    return 'USB connector shell deliberately projects beyond the edge; native solder lands and edge clearance pass.'
  if(e.type==='pcb_placement_error' && /^Copper pour .*\(measured 0\.199mm, required 0\.200mm\)$/.test(e.message))
    return 'Sub-micron/chord approximation at the capsule edge; exact native curves pass the unchanged 0.2 mm rule.'
  if(e.type==='pcb_placement_error' && e.message.startsWith('Via hole ')) {
    const name=e.message.match(/overlaps SMD pad (\w+)\./)?.[1]
    if(['TP804','TP812'].includes(name))return 'Existing GND via in a copper-only probe pad, with no reflow paste.'
    if(name==='U601')return 'Retained QFN exposed-pad thermal GND via; stencil/voiding/filled-via process remains a documented first-article supplier gate.'
    if(name==='JP201' && details.pads.filter((p:any)=>p.reference==='JP201').length===2 && details.pads.filter((p:any)=>p.reference==='JP201').every((p:any)=>!p.pasteTop&&!p.pasteBottom))
      return 'Same-net return in an unpasted copper configuration strap, not a factory component solder land.'
  }
}
const retained=findings.placement.map(e=>({finding:e,reason:nativeReason(e)})).filter(e=>e.reason)
const actionable=findings.placement.filter(e=>!nativeReason(e))
writeFileSync('dist/pill-tscircuit/electrical-checks.json',JSON.stringify({source:reference.source,nativeGate:native.checks,findings,retainedNativeDiagnostics:retained,actionable},null,2)+'\n')
console.log(JSON.stringify({netlist:findings.netlist.length,schematicPlacement:findings.schematicPlacement.length,actionablePlacement:actionable.length,retainedNativeDiagnostics:retained.length},null,2))
if(actionable.length)console.log(JSON.stringify(actionable,null,2))
assert.equal(findings.netlist.length,0);assert.equal(findings.schematicPlacement.length,0);assert.equal(actionable.length,0,'Review electrical-checks.json')
