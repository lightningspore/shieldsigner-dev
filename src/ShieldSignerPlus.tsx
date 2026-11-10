import { Fragment } from "react"
import reference from "./generated/reference-board.json"

/** Native tscircuit electrical design. Reference routing is restored by build.tsx.
 * The compiler checks pad positions before reusing that routing.
 * Physical lands with duplicate KiCad numbers receive individual ports tied to
 * the original net (e.g. SEC1210 exposed-pad vias and Pico castellated pads).
 */
type ReferencePart = Omit<(typeof reference.components)[number], 'pins'> & {
  pins: Record<string, string[] | undefined>
}
export type ReferenceBoard = Omit<typeof reference, 'components'> & {
  copperLayers?: string[]
  components: ReferencePart[]
  bridges?: {reference:string, ports:string[], nets:string[], layer:string, points:{x:number,y:number}[]}[]
}

export const ShieldSignerPlus = ({data = reference}: {data?: ReferenceBoard} = {}) => (
  <board
    layers={data.copperLayers?.length === 4 ? 4 : 2}
    width={data.width}
    height={data.height}
    outline={data.outline}
    routingDisabled
    schAutoLayoutEnabled={false}
  >
    {data.holes.map((hole,index) => <Fragment key={index}><hole pcbX={hole.x} pcbY={hole.y} diameter={hole.diameter} /></Fragment>)}
    {data.cutouts.map((points,index) => <Fragment key={index}><cutout shape="polygon" points={points} /></Fragment>)}
    {data.nets.map((net) => <Fragment key={net.name}><net name={net.name} /></Fragment>)}
    {data.components.map((part, index) => (
      <Fragment key={part.name}><chip
        name={part.name}
        manufacturerPartNumber={part.value}
        pinLabels={part.pins as Record<string, string[]>}
        pcbX={part.x}
        pcbY={part.y}
        // Pad geometry is already rotated/projected into board coordinates.
        // Explicit pad layers preserve front/back without a second mirror.
        schX={(index % 7) * 24 - 72}
        schY={-Math.floor(index / 7) * 20}
        footprint={
          <footprint {...(data.bridges && /^(JP|J302$|J701$)/.test(part.name) ? {insertionDirection:"from_above" as const} : {})}>
            {part.pads.map((pad) => pad.type === "thru_hole" ? (
              <Fragment key={pad.port}><platedhole
                portHints={[pad.port]}
                pcbX={pad.x} pcbY={pad.y}
                {...(pad.shape === "oval" ? {
                  shape: "pill" as const, outerWidth: pad.width, outerHeight: pad.height,
                  holeWidth: pad.drill[0], holeHeight: pad.drill[1] ?? pad.drill[0], ccwRotation: pad.rotation,
                } : pad.shape === "rect" ? {
                  shape: "circular_hole_with_rect_pad" as const, holeDiameter: pad.drill[0], rectPadWidth: pad.width, rectPadHeight: pad.height,
                } : {shape:"circle" as const, holeDiameter:pad.drill[0], outerDiameter:pad.width})}
              /></Fragment>
            ) : (
              <Fragment key={pad.port}><smtpad
                portHints={[pad.port]}
                pcbX={pad.x} pcbY={pad.y}
                layer={pad.layer as "top" | "bottom"}
                shape="polygon"
                points={pad.polygon}
              /></Fragment>
            ))}
          </footprint>
        }
      /></Fragment>
    ))}
    {data.bridges?.map(bridge => <Fragment key={bridge.reference}>
      <trace from={`.${bridge.reference} .${bridge.ports[0]}`} to={`.${bridge.reference} .${bridge.ports[1]}`} />
    </Fragment>)}
    {data.nets.flatMap((net) => net.ports.map((port) => (
      <Fragment key={port}><trace from={port} to={`net.${net.name}`} schDisplayLabel={net.label} /></Fragment>
    )))}
  </board>
)
