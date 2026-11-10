/** Exact ShieldSigner:CK_PTS636_SK25_G lands; retained upstream/local library attribution.
 * Local +X right, +Y up. Parent component supplies side and rotation.
 */
export function CkPts636Footprint({courtyardWidth = 9.49}: {courtyardWidth?:number} = {}) {
  return <footprint>
    <smtpad portHints={["pin1"]} pcbX={-3.875} pcbY={0} shape="rect" width={1.25} height={2.1} cornerRadius={0.0} solderMaskMargin={0.038} noSolderPaste={false} coveredWithSolderMask={false} />
    <smtpad portHints={["pin2"]} pcbX={3.875} pcbY={0} shape="rect" width={1.25} height={2.1} cornerRadius={0.0} solderMaskMargin={0.038} noSolderPaste={false} coveredWithSolderMask={false} />
    <courtyardoutline outline={[{x:-courtyardWidth/2,y:-3.245},{x:courtyardWidth/2,y:-3.245},{x:courtyardWidth/2,y:3.245},{x:-courtyardWidth/2,y:3.245}]} />
    <fabricationnotepath route={[{"x":3.06,"y":1.81},{"x":3.06,"y":1.0}]} strokeWidth={0.12} />
    <fabricationnotepath route={[{"x":-3.06,"y":1.81},{"x":3.06,"y":1.81}]} strokeWidth={0.12} />
    <fabricationnotepath route={[{"x":3.0,"y":1.75},{"x":3.0,"y":-1.75}]} strokeWidth={0.1} />
    <fabricationnotepath route={[{"x":-3.0,"y":1.75},{"x":3.0,"y":1.75}]} strokeWidth={0.1} />
    <fabricationnotepath route={[{"x":-3.0,"y":1.75},{"x":-3.0,"y":-1.75}]} strokeWidth={0.1} />
    <fabricationnotepath route={[{"x":1.75,"y":1.0},{"x":1.75,"y":-1.0}]} strokeWidth={0.1} />
    <fabricationnotepath route={[{"x":-1.75,"y":1.0},{"x":1.75,"y":1.0}]} strokeWidth={0.1} />
    <fabricationnotepath route={[{"x":1.5,"y":0.8},{"x":1.5,"y":-0.8}]} strokeWidth={0.1} />
    <fabricationnotepath route={[{"x":-1.5,"y":0.8},{"x":1.5,"y":0.8}]} strokeWidth={0.1} />
    <fabricationnotepath route={[{"x":-1.5,"y":0.8},{"x":-1.5,"y":-0.8}]} strokeWidth={0.1} />
    <fabricationnotepath route={[{"x":-1.5,"y":-0.8},{"x":1.5,"y":-0.8}]} strokeWidth={0.1} />
    <fabricationnotepath route={[{"x":1.75,"y":-1.0},{"x":-1.75,"y":-1.0}]} strokeWidth={0.1} />
    <fabricationnotepath route={[{"x":-1.75,"y":-1.0},{"x":-1.75,"y":1.0}]} strokeWidth={0.1} />
    <fabricationnotepath route={[{"x":-3.0,"y":-1.75},{"x":3.0,"y":-1.75}]} strokeWidth={0.1} />
    <fabricationnotepath route={[{"x":3.06,"y":-1.81},{"x":-3.06,"y":-1.81}]} strokeWidth={0.12} />
    <fabricationnotepath route={[{"x":-3.06,"y":-1.81},{"x":-3.06,"y":-1.0}]} strokeWidth={0.12} />
  </footprint>
}
