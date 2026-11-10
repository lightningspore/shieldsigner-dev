/** Exact ShieldSigner:PowerHeader_1x02_P2.54mm lands; retained upstream/local library attribution.
 * Local +X right, +Y up. Parent component supplies side and rotation.
 */
export function PowerHeaderFootprint() {
  return <footprint insertionDirection="from_above">
    <platedhole portHints={["pin1"]} pcbX={0} pcbY={0} shape="circular_hole_with_rect_pad" rectPadWidth={1.7} rectPadHeight={1.7} holeDiameter={1.0} solderMaskMargin={0.038} />
    <platedhole portHints={["pin2"]} pcbX={0} pcbY={-2.54} shape="circle" outerDiameter={1.7} holeDiameter={1.0} solderMaskMargin={0.038} />
    <courtyardoutline outline={[{"x":1.765,"y":-4.315},{"x":-1.765,"y":-4.315},{"x":-1.765,"y":1.765},{"x":1.765,"y":1.765}]} />
    <silkscreenpath route={[{"x":-1.38,"y":1.38},{"x":0.0,"y":1.38}]} strokeWidth={0.12} />
    <silkscreenpath route={[{"x":-1.38,"y":-0.0},{"x":-1.38,"y":1.38}]} strokeWidth={0.12} />
    <silkscreenpath route={[{"x":1.38,"y":-1.27},{"x":1.38,"y":-3.92}]} strokeWidth={0.12} />
    <silkscreenpath route={[{"x":-1.38,"y":-1.27},{"x":1.38,"y":-1.27}]} strokeWidth={0.12} />
    <silkscreenpath route={[{"x":-1.38,"y":-1.27},{"x":-1.38,"y":-3.92}]} strokeWidth={0.12} />
    <silkscreenpath route={[{"x":-1.38,"y":-3.92},{"x":1.38,"y":-3.92}]} strokeWidth={0.12} />
    <fabricationnotepath route={[{"x":1.27,"y":1.27},{"x":1.27,"y":-3.81}]} strokeWidth={0.1} />
    <fabricationnotepath route={[{"x":-0.635,"y":1.27},{"x":1.27,"y":1.27}]} strokeWidth={0.1} />
    <fabricationnotepath route={[{"x":-1.27,"y":0.635},{"x":-0.635,"y":1.27}]} strokeWidth={0.1} />
    <fabricationnotepath route={[{"x":1.27,"y":-3.81},{"x":-1.27,"y":-3.81}]} strokeWidth={0.1} />
    <fabricationnotepath route={[{"x":-1.27,"y":-3.81},{"x":-1.27,"y":0.635}]} strokeWidth={0.1} />
  </footprint>
}
