import { readFileSync, writeFileSync } from "node:fs"
import { AutoroutingPipelineSolver } from "@tscircuit/capacity-autorouter"

// Route native disconnected nets with the built-in pipeline. Previously routed
// copper becomes fixed geometry for the next net. Native KiCad DRC is the gate.
const input = JSON.parse(readFileSync("dist/full-size-pico/routing-input.json", "utf8"))
Object.assign(input, {
  nominalTraceWidth: 0.25,
  minViaPadDiameter: 0.6,
  minViaHoleDiameter: 0.3,
  minTraceToPadEdgeClearance: 0.35,
  minViaEdgeToPadEdgeClearance: 0.35,
  defaultObstacleMargin: 0.35,
})
const traces: any[] = []
const failed: string[] = []
for (const connection of input.connections) {
  console.log(`Routing ${connection.name}`)
  connection.nominalTraceWidth = 0.25
  const solver = new AutoroutingPipelineSolver({ ...input, connections: [connection], obstacles: [...input.obstacles] })
  let steps = 0
  try {
    while (!solver.solved && !solver.failed && ++steps < 5_000_000) solver.step()
    if (!solver.solved) throw new Error(String(solver.error ?? "step limit"))
    const result = solver.getOutputSimpleRouteJson()
    for (const trace of result.traces ?? []) {
      // Some pipeline escape paths use 0.1 mm despite the requested minimum.
      // Enforce the requested width before native DRC; never weaken board rules.
      for (const point of trace.route) if (point.route_type === "wire") point.width = Math.max(0.25, point.width)
      traces.push(trace)
      let previous: any = null
      for (const point of trace.route) {
        if (point.route_type === "via") {
          input.obstacles.push({ type: "rect", center: { x: point.x, y: point.y }, width: 0.8, height: 0.8, layers: ["top", "inner1", "bottom"], connectedTo: [connection.name] })
          previous = { ...point, layer: point.to_layer }
        } else if (point.route_type === "wire") {
          if (previous && previous.layer === point.layer) {
            const dx = point.x - previous.x, dy = point.y - previous.y
            const n = Math.max(1, Math.ceil(Math.hypot(dx, dy) / 0.75)), w = point.width + 0.2
            for (let i = 0; i < n; i++) {
              const x1 = previous.x + dx * i / n, y1 = previous.y + dy * i / n
              const x2 = previous.x + dx * (i + 1) / n, y2 = previous.y + dy * (i + 1) / n
              input.obstacles.push({ type: "rect", center: { x: (x1 + x2) / 2, y: (y1 + y2) / 2 }, width: Math.abs(x2 - x1) + w, height: Math.abs(y2 - y1) + w, layers: [point.layer], connectedTo: [connection.name] })
            }
          }
          previous = point
        } else previous = null
      }
    }
    console.log(`Routed ${connection.name}; ${traces.length} traces total`)
  } catch (error) {
    failed.push(connection.name)
    console.error(`Unrouted ${connection.name}: ${error}`)
  }
  writeFileSync("dist/full-size-pico/routing-output.json", JSON.stringify({ traces, failed }, null, 2) + "\n")
}
console.log(`Built-in routing produced ${traces.length} traces; ${failed.length} nets remain.`)
