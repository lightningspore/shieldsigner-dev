/** Exact Resistor_SMD:R_0805_2012Metric_Pad1.20x1.40mm_HandSolder lands; retained upstream/local library attribution.
 * Local +X right, +Y up. Parent component supplies side and rotation.
 */
export function Resistor0805HandSolderFootprint() {
  return <footprint>
    <smtpad portHints={["pin1"]} pcbX={-1.0} pcbY={0} shape="rect" width={1.2} height={1.4} cornerRadius={0.2499996} solderMaskMargin={0.038} noSolderPaste={false} coveredWithSolderMask={false} />
    <smtpad portHints={["pin2"]} pcbX={1.0} pcbY={0} shape="rect" width={1.2} height={1.4} cornerRadius={0.2499996} solderMaskMargin={0.038} noSolderPaste={false} coveredWithSolderMask={false} />
    <courtyardoutline outline={[{"x":-1.845,"y":0.945},{"x":-1.845,"y":-0.945},{"x":1.845,"y":-0.945},{"x":1.845,"y":0.945}]} />
    <silkscreenpath route={[{"x":-0.227064,"y":0.735},{"x":0.227064,"y":0.735}]} strokeWidth={0.12} />
    <silkscreenpath route={[{"x":-0.227064,"y":-0.735},{"x":0.227064,"y":-0.735}]} strokeWidth={0.12} />
    <fabricationnotepath route={[{"x":1.0,"y":0.625},{"x":1.0,"y":-0.625}]} strokeWidth={0.1} />
    <fabricationnotepath route={[{"x":1.0,"y":-0.625},{"x":-1.0,"y":-0.625}]} strokeWidth={0.1} />
    <fabricationnotepath route={[{"x":-1.0,"y":0.625},{"x":1.0,"y":0.625}]} strokeWidth={0.1} />
    <fabricationnotepath route={[{"x":-1.0,"y":-0.625},{"x":-1.0,"y":0.625}]} strokeWidth={0.1} />
  </footprint>
}
