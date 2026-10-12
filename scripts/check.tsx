import * as schemas from "circuit-json"
import assert from "node:assert/strict"
import { readFileSync } from "node:fs"
import { createHash } from "node:crypto"
import { Circuit } from "@tscircuit/core"
import { compileBoard } from "./build"
import reference from "../src/generated/reference-board.json"
import Preview from "../src/index"

assert.equal(reference.source.sha256, createHash("sha256").update(readFileSync(reference.source.path)).digest("hex"), "KiCad changed: run mise run generate before checking the port")
assert.deepEqual(reference.components.filter(p=>p.dnp).map(p=>p.name).sort(), ["J302", "R404", "R408"])
for (const [ref,rail] of [["R403", "+3.3V"], ["R409", "GND"]]) {
  const part = reference.components.find(p=>p.name===ref)!
  assert(!part.dnp && part.pads.some(p=>p.net===rail), `Wrong LCD strap: ${ref}`)
}
const circuit = await compileBoard()
for (const e of circuit) schemas.any_circuit_element.parse(e)
const count = (type: string) => circuit.filter(e => e.type === type).length
assert.equal(count("source_component"), reference.components.length)
assert.equal(count("source_net"), reference.nets.length)
assert.equal(count("pcb_trace"), reference.segments.length)
assert.equal(count("pcb_via"), reference.vias.length)
assert.equal(count("pcb_copper_pour"), reference.fills.length)
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
