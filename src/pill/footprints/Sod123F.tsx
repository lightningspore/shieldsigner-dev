/** Exact Diode_SMD:D_SOD-123F lands; retained upstream/local library attribution.
 * Local +X right, +Y up. Parent component supplies side and rotation.
 */
export function Sod123FFootprint() {
  return <footprint>
    <smtpad portHints={["pin1"]} pcbX={-1.4} pcbY={0} shape="rect" width={1.1} height={1.1} cornerRadius={0.25000000003} solderMaskMargin={0.038} noSolderPaste={false} coveredWithSolderMask={false} />
    <smtpad portHints={["pin2"]} pcbX={1.4} pcbY={0} shape="rect" width={1.1} height={1.1} cornerRadius={0.25000000003} solderMaskMargin={0.038} noSolderPaste={false} coveredWithSolderMask={false} />
    <courtyardoutline outline={[{"x":-2.195,"y":-1.145},{"x":2.195,"y":-1.145},{"x":2.195,"y":1.145},{"x":-2.195,"y":1.145}]} />
    <silkscreenpath route={[{"x":-2.21,"y":1.0},{"x":1.65,"y":1.0}]} strokeWidth={0.12} />
    <silkscreenpath route={[{"x":-2.21,"y":1.0},{"x":-2.21,"y":-1.0}]} strokeWidth={0.12} />
    <silkscreenpath route={[{"x":-2.21,"y":-1.0},{"x":1.65,"y":-1.0}]} strokeWidth={0.12} />
    <fabricationnotepath route={[{"x":-1.4,"y":0.9},{"x":1.4,"y":0.9}]} strokeWidth={0.1} />
    <fabricationnotepath route={[{"x":1.4,"y":0.9},{"x":1.4,"y":-0.9}]} strokeWidth={0.1} />
    <fabricationnotepath route={[{"x":0.25,"y":0.4},{"x":0.25,"y":-0.4}]} strokeWidth={0.1} />
    <fabricationnotepath route={[{"x":-0.75,"y":0.0},{"x":-0.35,"y":0.0}]} strokeWidth={0.1} />
    <fabricationnotepath route={[{"x":-0.35,"y":0.0},{"x":-0.35,"y":0.55}]} strokeWidth={0.1} />
    <fabricationnotepath route={[{"x":-0.35,"y":0.0},{"x":0.25,"y":0.4}]} strokeWidth={0.1} />
    <fabricationnotepath route={[{"x":-0.35,"y":0.0},{"x":-0.35,"y":-0.55}]} strokeWidth={0.1} />
    <fabricationnotepath route={[{"x":0.25,"y":0.0},{"x":0.75,"y":0.0}]} strokeWidth={0.1} />
    <fabricationnotepath route={[{"x":0.25,"y":-0.4},{"x":-0.35,"y":0.0}]} strokeWidth={0.1} />
    <fabricationnotepath route={[{"x":-1.4,"y":-0.9},{"x":-1.4,"y":0.9}]} strokeWidth={0.1} />
    <fabricationnotepath route={[{"x":1.4,"y":-0.9},{"x":-1.4,"y":-0.9}]} strokeWidth={0.1} />
  </footprint>
}
