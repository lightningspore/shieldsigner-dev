/** Exact Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder lands; retained upstream/local library attribution.
 * Local +X right, +Y up. Parent component supplies side and rotation.
 */
export function Capacitor0805HandSolderFootprint() {
  return <footprint>
    <smtpad portHints={["pin1"]} pcbX={-1.0375} pcbY={0} shape="rect" width={1.175} height={1.45} cornerRadius={0.25000005000000003} solderMaskMargin={0.038} noSolderPaste={false} coveredWithSolderMask={false} />
    <smtpad portHints={["pin2"]} pcbX={1.0375} pcbY={0} shape="rect" width={1.175} height={1.45} cornerRadius={0.25000005000000003} solderMaskMargin={0.038} noSolderPaste={false} coveredWithSolderMask={false} />
    <courtyardoutline outline={[{"x":-1.875,"y":-0.975},{"x":1.875,"y":-0.975},{"x":1.875,"y":0.975},{"x":-1.875,"y":0.975}]} />
    <silkscreenpath route={[{"x":-0.261252,"y":0.735},{"x":0.261252,"y":0.735}]} strokeWidth={0.12} />
    <silkscreenpath route={[{"x":-0.261252,"y":-0.735},{"x":0.261252,"y":-0.735}]} strokeWidth={0.12} />
    <fabricationnotepath route={[{"x":-1.0,"y":0.625},{"x":1.0,"y":0.625},{"x":1.0,"y":-0.625},{"x":-1.0,"y":-0.625},{"x":-1.0,"y":0.625}]} strokeWidth={0.1} />
  </footprint>
}
