import {PowerNet} from "../PowerNet"
import {N} from "../nets"
import {CkPts636Footprint} from "../footprints/CkPts636"
import {CkPts636Model} from "../models/CkPts636"

/** Buttons: electrical intent, values, pin roles and layout are edited here. */
export function Buttons() { return <schematicsheet name="Buttons" displayName="Buttons">
  <group name="Buttons" schLayout={{layoutMode:"none"}}>
  <pushbutton
    name="SW501"
    pcbX={-70.02}
    pcbY={0.0}
    pcbRotation={90.0}
    layer="top"
    schX={-10.5}
    schY={0}
    connections={{pin1:N.JoystickLeft}}
    footprint={<CkPts636Footprint />}
    cadModel={CkPts636Model}
    manufacturerPartNumber={"PTS636SK25SMTRLFS"}
    supplierPartNumbers={{jlcpcb:["C2689642"]}}
    schRotation={-90.0}
  />
  <PowerNet pin=".SW501 .pin2" net={N.GND}/>
  <pushbutton
    name="SW502"
    pcbX={-59.53}
    pcbY={10.494}
    pcbRotation={90.0}
    layer="top"
    schX={-3.5}
    schY={0}
    connections={{pin1:N.JoystickUp}}
    footprint={<CkPts636Footprint />}
    cadModel={CkPts636Model}
    manufacturerPartNumber={"PTS636SK25SMTRLFS"}
    supplierPartNumbers={{jlcpcb:["C2689642"]}}
    schRotation={-90.0}
  />
  <PowerNet pin=".SW502 .pin2" net={N.GND}/>
  <pushbutton
    name="SW503"
    pcbX={-59.53}
    pcbY={0.0}
    pcbRotation={135.0}
    layer="top"
    schX={3.5}
    schY={0}
    connections={{pin1:N.JoystickPress}}
    footprint={<CkPts636Footprint courtyardWidth={9.09} />}
    cadModel={CkPts636Model}
    manufacturerPartNumber={"PTS636SK25SMTRLFS"}
    supplierPartNumbers={{jlcpcb:["C2689642"]}}
    schRotation={-90.0}
  />
  <PowerNet pin=".SW503 .pin2" net={N.GND}/>
  <pushbutton
    name="SW504"
    pcbX={-59.53}
    pcbY={-10.426}
    pcbRotation={180.0}
    layer="top"
    schX={10.5}
    schY={0}
    connections={{pin1:N.JoystickDown}}
    footprint={<CkPts636Footprint />}
    cadModel={CkPts636Model}
    manufacturerPartNumber={"PTS636SK25SMTRLFS"}
    supplierPartNumbers={{jlcpcb:["C2689642"]}}
    schRotation={-90.0}
  />
  <PowerNet pin=".SW504 .pin2" net={N.GND}/>
  <pushbutton
    name="SW505"
    pcbX={-49.08}
    pcbY={0.0}
    pcbRotation={0}
    layer="top"
    schX={-10.5}
    schY={-9}
    connections={{pin1:N.JoystickRight}}
    footprint={<CkPts636Footprint />}
    cadModel={CkPts636Model}
    manufacturerPartNumber={"PTS636SK25SMTRLFS"}
    supplierPartNumbers={{jlcpcb:["C2689642"]}}
    schRotation={-90.0}
  />
  <PowerNet pin=".SW505 .pin2" net={N.GND}/>
  <pushbutton
    name="SW506"
    pcbX={58.88}
    pcbY={10.284}
    pcbRotation={-45.0}
    layer="top"
    schX={-3.5}
    schY={-9}
    connections={{pin1:N.Key1}}
    footprint={<CkPts636Footprint courtyardWidth={9.09} />}
    cadModel={CkPts636Model}
    manufacturerPartNumber={"PTS636SK25SMTRLFS"}
    supplierPartNumbers={{jlcpcb:["C2689642"]}}
    schRotation={-90.0}
  />
  <PowerNet pin=".SW506 .pin2" net={N.GND}/>
  <pushbutton
    name="SW507"
    pcbX={58.88}
    pcbY={0.014}
    pcbRotation={90.0}
    layer="top"
    schX={3.5}
    schY={-9}
    connections={{pin1:N.Key2}}
    footprint={<CkPts636Footprint />}
    cadModel={CkPts636Model}
    manufacturerPartNumber={"PTS636SK25SMTRLFS"}
    supplierPartNumbers={{jlcpcb:["C2689642"]}}
    schRotation={-90.0}
  />
  <PowerNet pin=".SW507 .pin2" net={N.GND}/>
  <pushbutton
    name="SW508"
    pcbX={58.88}
    pcbY={-10.316}
    pcbRotation={45.0}
    layer="top"
    schX={10.5}
    schY={-9}
    connections={{pin1:N.Key3}}
    footprint={<CkPts636Footprint courtyardWidth={9.09} />}
    cadModel={CkPts636Model}
    manufacturerPartNumber={"PTS636SK25SMTRLFS"}
    supplierPartNumbers={{jlcpcb:["C2689642"]}}
    schRotation={-90.0}
  />
  <PowerNet pin=".SW508 .pin2" net={N.GND}/>
  </group>
</schematicsheet> }
