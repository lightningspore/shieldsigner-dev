/** Two opposing avalanche junctions, not a polarity-sensitive rectifier. */
export function BidirectionalTvsSymbol({reference="D301"}:{reference?:string}={}) { return <symbol>
  <schematictext text={reference} schX={0} schY={1} fontSize={.2}/>
  <schematicpath points={[{x:-1.5,y:0},{x:-.9,y:0}]} strokeWidth={.06} />
  <schematicpath points={[{x:-.9,y:-.55},{x:-.9,y:.55},{x:0,y:0},{x:-.9,y:-.55}]} strokeWidth={.06} />
  <schematicpath points={[{x:.9,y:-.55},{x:.9,y:.55},{x:0,y:0},{x:.9,y:-.55}]} strokeWidth={.06} />
  <schematicpath points={[{x:0,y:-.55},{x:0,y:.55}]} strokeWidth={.06} />
  <schematicpath points={[{x:.9,y:0},{x:1.5,y:0}]} strokeWidth={.06} />
  <port name="pin1" pinNumber={1} direction="left" schX={-1.5} schY={0} />
  <port name="pin2" pinNumber={2} direction="right" schX={1.5} schY={0} />
</symbol> }
