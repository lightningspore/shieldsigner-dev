import {Fragment} from 'react'
import {N} from './pill/nets'
import {PowerInput} from './pill/sections/PowerInput'
import {HostInterface} from './pill/sections/HostInterface'
import {Buttons} from './pill/sections/Buttons'
import {CardSocket} from './pill/sections/CardSocket'
import {SmartcardInterface} from './pill/sections/SmartcardInterface'
import {DisplayInterface} from './pill/sections/DisplayInterface'
import {TestPoints} from './pill/sections/TestPoints'
import {Artwork} from './pill/Artwork'
import {BoardLegends} from './pill/BoardLegends'
import {Mechanics,capsuleOutline} from './pill/Mechanics'

/** Independent, source-authored ShieldSigner pill carrier.
 * Native KiCad remains the electrical/mechanical comparison reference.
 * Compiles using ordinary tscircuit rendering, without a geometry postprocessor.
 */
export default function PillCarrier({routing=true}:{routing?:boolean}={}) {
  return <board width={160} height={70} thickness={1.6} outline={capsuleOutline()}
    layers={2} isViaInPadAllowed routeRemaining={routing} autorouter="auto-local" autorouterVersion="beta_pipeline9"  minTraceWidth={.2} defaultTraceWidth={.2}
    minBoardEdgeClearance={.2} minPadEdgeToPadEdgeClearance={.15}
    minTraceToPadEdgeClearance={.2} minViaHoleDiameter={.3} minViaPadDiameter={.6}
    pcbStyle={{silkscreenTextPosition:'none',viaHoleDiameter:.3,viaPadDiameter:.6}}
    solderMaskColor="green" silkscreenColor="white" schAutoLayoutEnabled={false} schMaxTraceDistance={3}>
    {[...new Set(Object.values(N))].map(selector=><Fragment key={selector}><net name={selector.slice(4)}/></Fragment>)}
    <PowerInput/><HostInterface/><Buttons/><SmartcardInterface/><CardSocket/><DisplayInterface/><TestPoints/>
    <Mechanics/><BoardLegends/><Artwork/>
    {routing&&<>
      <copperpour name="GND_TOP" layer="top" connectsTo={N.GND} clearance={.2} boardEdgeMargin={.21}/>
      <copperpour name="GND_BOTTOM" layer="bottom" connectsTo={N.GND} clearance={.2} boardEdgeMargin={.21}/>
    </>}
  </board>
}
