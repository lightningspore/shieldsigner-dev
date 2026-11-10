/** Exact LED_SMD:LED_0805_2012Metric_Pad1.15x1.40mm_HandSolder lands; retained upstream/local library attribution.
 * Local +X right, +Y up. Parent component supplies side and rotation.
 */
export function Led0805HandSolderFootprint() {
  return <footprint>
    <smtpad portHints={["pin2"]} pcbX={-1.025} pcbY={0} shape="rect" width={1.15} height={1.4} cornerRadius={0.24999965} solderMaskMargin={0.038} noSolderPaste={false} coveredWithSolderMask={false} />
    <smtpad portHints={["pin1"]} pcbX={1.025} pcbY={0} shape="rect" width={1.15} height={1.4} cornerRadius={0.24999965} solderMaskMargin={0.038} noSolderPaste={false} coveredWithSolderMask={false} />
    <courtyardoutline outline={[{"x":1.845,"y":-0.945},{"x":1.845,"y":0.945},{"x":-1.845,"y":0.945},{"x":-1.845,"y":-0.945}]} />
    <silkscreenpath route={[{"x":-1.86,"y":-0.96},{"x":1.0,"y":-0.96}]} strokeWidth={0.12} />
    <silkscreenpath route={[{"x":-1.86,"y":0.96},{"x":-1.86,"y":-0.96}]} strokeWidth={0.12} />
    <silkscreenpath route={[{"x":1.0,"y":0.96},{"x":-1.86,"y":0.96}]} strokeWidth={0.12} />
    <fabricationnotepath route={[{"x":-1.0,"y":-0.6},{"x":1.0,"y":-0.6}]} strokeWidth={0.1} />
    <fabricationnotepath route={[{"x":-1.0,"y":0.3},{"x":-1.0,"y":-0.6}]} strokeWidth={0.1} />
    <fabricationnotepath route={[{"x":-0.7,"y":0.6},{"x":-1.0,"y":0.3}]} strokeWidth={0.1} />
    <fabricationnotepath route={[{"x":1.0,"y":-0.6},{"x":1.0,"y":0.6}]} strokeWidth={0.1} />
    <fabricationnotepath route={[{"x":1.0,"y":0.6},{"x":-0.7,"y":0.6}]} strokeWidth={0.1} />
  </footprint>
}
