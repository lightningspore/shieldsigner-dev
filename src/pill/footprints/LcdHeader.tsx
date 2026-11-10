/** Exact ShieldSigner:LCD_SPI_8_Pill lands; retained upstream/local library attribution.
 * Local +X right, +Y up. Parent component supplies side and rotation.
 */
export function LcdHeaderFootprint() {
  return <footprint insertionDirection="from_above">
    <platedhole portHints={["pin1"]} pcbX={0} pcbY={0} shape="circular_hole_with_rect_pad" rectPadWidth={1.7} rectPadHeight={1.7} holeDiameter={1.0} solderMaskMargin={0.038} />
    <platedhole portHints={["pin2"]} pcbX={0} pcbY={2.54} shape="circle" outerDiameter={1.7} holeDiameter={1.0} solderMaskMargin={0.038} />
    <platedhole portHints={["pin3"]} pcbX={0} pcbY={5.08} shape="circle" outerDiameter={1.7} holeDiameter={1.0} solderMaskMargin={0.038} />
    <platedhole portHints={["pin4"]} pcbX={0} pcbY={7.62} shape="circle" outerDiameter={1.7} holeDiameter={1.0} solderMaskMargin={0.038} />
    <platedhole portHints={["pin5"]} pcbX={0} pcbY={10.16} shape="circle" outerDiameter={1.7} holeDiameter={1.0} solderMaskMargin={0.038} />
    <platedhole portHints={["pin6"]} pcbX={0} pcbY={12.7} shape="circle" outerDiameter={1.7} holeDiameter={1.0} solderMaskMargin={0.038} />
    <platedhole portHints={["pin7"]} pcbX={0} pcbY={15.24} shape="circle" outerDiameter={1.7} holeDiameter={1.0} solderMaskMargin={0.038} />
    <platedhole portHints={["pin8"]} pcbX={0} pcbY={17.78} shape="circle" outerDiameter={1.7} holeDiameter={1.0} solderMaskMargin={0.038} />
    <courtyardoutline outline={[{"x":1.795,"y":19.495},{"x":1.795,"y":-1.795},{"x":-1.795,"y":-1.795},{"x":-1.795,"y":19.495}]} />
    <fabricationnotepath route={[{"x":-1.27,"y":19.05},{"x":1.27,"y":19.05}]} strokeWidth={0.05} />
    <fabricationnotepath route={[{"x":-1.27,"y":-1.27},{"x":-1.27,"y":19.05}]} strokeWidth={0.05} />
    <fabricationnotepath route={[{"x":1.27,"y":19.05},{"x":1.27,"y":-1.27}]} strokeWidth={0.05} />
    <fabricationnotepath route={[{"x":1.27,"y":-1.27},{"x":-1.27,"y":-1.27}]} strokeWidth={0.05} />
  </footprint>
}
