import {shieldSvg} from './artwork/shield'
import {spaceRearSvg} from './artwork/space-rear'
import {shieldRearSvg} from './artwork/shield-rear'
/** Logo art is reusable; all ordinary lettering is editable silkscreentext. */
export function Artwork() {return <>
  <silkscreengraphic imageUrl={shieldSvg} width={4} height={4.25} pcbX={-58} pcbY={-21.421} layer="top"/>
  <silkscreengraphic imageUrl={shieldRearSvg} width={10} height={10.625} pcbX={-59} pcbY={2.579} layer="bottom"/>
  <silkscreengraphic imageUrl={spaceRearSvg} width={30} height={9.62} pcbX={56.5} pcbY={-16.921} layer="bottom"/>
  <silkscreencircle pcbX={59} pcbY={2.579} radius={5.5} strokeWidth={.3} layer="bottom"/>
  <silkscreenpath route={[{x:58,y:6.579},{x:61,y:2.579},{x:59,y:2.579},{x:60,y:-1.421},{x:57,y:2.579},{x:59,y:2.579},{x:58,y:6.579}]} strokeWidth={.35} layer="bottom"/>
</>}
