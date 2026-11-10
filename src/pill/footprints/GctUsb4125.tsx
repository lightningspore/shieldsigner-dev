/** Exact ShieldSigner:GCT_USB4125_GF_A lands; retained upstream/local library attribution.
 * Local +X right, +Y up. Parent component supplies side and rotation.
 */
export function GctUsb4125Footprint() {
  return <footprint insertionDirection="from_bottom">
    <smtpad portHints={["pin1"]} pcbX={-0.5} pcbY={3.38} shape="rect" width={0.7} height={1.2} cornerRadius={0.175} solderMaskMargin={0.038} noSolderPaste={false} coveredWithSolderMask={false} />
    <smtpad portHints={["pin2"]} pcbX={1.52} pcbY={3.38} shape="rect" width={0.8} height={1.2} cornerRadius={0.2} solderMaskMargin={0.038} noSolderPaste={false} coveredWithSolderMask={false} />
    <smtpad portHints={["pin3"]} pcbX={2.75} pcbY={3.38} shape="rect" width={0.76} height={1.2} cornerRadius={0.19} solderMaskMargin={0.038} noSolderPaste={false} coveredWithSolderMask={false} />
    <smtpad portHints={["pin4"]} pcbX={0.5} pcbY={3.38} shape="rect" width={0.7} height={1.2} cornerRadius={0.175} solderMaskMargin={0.038} noSolderPaste={false} coveredWithSolderMask={false} />
    <smtpad portHints={["pin5"]} pcbX={-1.52} pcbY={3.38} shape="rect" width={0.8} height={1.2} cornerRadius={0.2} solderMaskMargin={0.038} noSolderPaste={false} coveredWithSolderMask={false} />
    <smtpad portHints={["pin6"]} pcbX={-2.75} pcbY={3.38} shape="rect" width={0.76} height={1.2} cornerRadius={0.19} solderMaskMargin={0.038} noSolderPaste={false} coveredWithSolderMask={false} />
    <platedhole portHints={["pin7"]} pcbX={-4.32} pcbY={-1.1} shape="pill" outerWidth={1.1} outerHeight={1.7} holeWidth={0.6} holeHeight={1.2} solderMaskMargin={0.038} />
    <platedhole portHints={["pin8"]} pcbX={-4.32} pcbY={2.7} shape="pill" outerWidth={1.1} outerHeight={1.7} holeWidth={0.6} holeHeight={1.2} solderMaskMargin={0.038} />
    <platedhole portHints={["pin9"]} pcbX={4.32} pcbY={-1.1} shape="pill" outerWidth={1.1} outerHeight={1.7} holeWidth={0.6} holeHeight={1.2} solderMaskMargin={0.038} />
    <platedhole portHints={["pin10"]} pcbX={4.32} pcbY={2.7} shape="pill" outerWidth={1.1} outerHeight={1.7} holeWidth={0.6} holeHeight={1.2} solderMaskMargin={0.038} />
    <courtyardoutline outline={[{"x":-5.315,"y":4.475},{"x":-5.315,"y":-3.895},{"x":5.315,"y":-3.895},{"x":5.315,"y":4.475}]} />
    <silkscreenpath route={[{"x":4.58,"y":-2.0},{"x":4.58,"y":-3.51}]} strokeWidth={0.12} />
    <silkscreenpath route={[{"x":-4.58,"y":-2.0},{"x":-4.58,"y":-3.51}]} strokeWidth={0.12} />
    <silkscreenpath route={[{"x":-4.58,"y":-3.51},{"x":4.58,"y":-3.51}]} strokeWidth={0.12} />
    <fabricationnotepath route={[{"x":4.58,"y":1.9},{"x":4.58,"y":-0.1}]} strokeWidth={0.12} />
    <fabricationnotepath route={[{"x":4.47,"y":3.4},{"x":4.47,"y":-3.4}]} strokeWidth={0.1} />
    <fabricationnotepath route={[{"x":-4.47,"y":3.4},{"x":4.47,"y":3.4}]} strokeWidth={0.1} />
    <fabricationnotepath route={[{"x":-4.47,"y":3.4},{"x":-4.47,"y":-3.4}]} strokeWidth={0.1} />
    <fabricationnotepath route={[{"x":-4.47,"y":-3.4},{"x":4.47,"y":-3.4}]} strokeWidth={0.1} />
    <fabricationnotepath route={[{"x":-4.58,"y":1.9},{"x":-4.58,"y":-0.1}]} strokeWidth={0.12} />
  </footprint>
}
