/** Exact ShieldSigner:AP2112K_SOT25_reflow lands; retained upstream/local library attribution.
 * Local +X right, +Y up. Parent component supplies side and rotation.
 */
export function Ap2112Sot25Footprint() {
  return <footprint>
    <smtpad portHints={["pin1"]} pcbX={-0.95} pcbY={-1.2} shape="rect" width={0.55} height={0.8} cornerRadius={0.11000000000000001} solderMaskMargin={0.038} noSolderPaste={false} coveredWithSolderMask={false} />
    <smtpad portHints={["pin2"]} pcbX={0} pcbY={-1.2} shape="rect" width={0.55} height={0.8} cornerRadius={0.11000000000000001} solderMaskMargin={0.038} noSolderPaste={false} coveredWithSolderMask={false} />
    <smtpad portHints={["pin3"]} pcbX={0.95} pcbY={-1.2} shape="rect" width={0.55} height={0.8} cornerRadius={0.11000000000000001} solderMaskMargin={0.038} noSolderPaste={false} coveredWithSolderMask={false} />
    <smtpad portHints={["pin4"]} pcbX={0.95} pcbY={1.2} shape="rect" width={0.55} height={0.8} cornerRadius={0.11000000000000001} solderMaskMargin={0.038} noSolderPaste={false} coveredWithSolderMask={false} />
    <smtpad portHints={["pin5"]} pcbX={-0.95} pcbY={1.2} shape="rect" width={0.55} height={0.8} cornerRadius={0.11000000000000001} solderMaskMargin={0.038} noSolderPaste={false} coveredWithSolderMask={false} />
    <courtyardoutline outline={[{"x":1.795,"y":1.895},{"x":1.795,"y":-1.895},{"x":-1.795,"y":-1.895},{"x":-1.795,"y":1.895}]} />
    <fabricationnotepath route={[{"x":-1.45,"y":0.8},{"x":1.45,"y":0.8}]} strokeWidth={0.05} />
    <fabricationnotepath route={[{"x":-1.45,"y":-0.8},{"x":-1.45,"y":0.8}]} strokeWidth={0.05} />
    <fabricationnotepath route={[{"x":1.45,"y":0.8},{"x":1.45,"y":-0.8}]} strokeWidth={0.05} />
    <fabricationnotepath route={[{"x":1.45,"y":-0.8},{"x":-1.45,"y":-0.8}]} strokeWidth={0.05} />
  </footprint>
}
