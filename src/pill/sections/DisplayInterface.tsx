import {PowerNet} from "../PowerNet"
import {N} from "../nets"
import {Ap2112Sot25Footprint} from "../footprints/Ap2112Sot25"
import {Ap2112Sot25Model} from "../models/Ap2112Sot25"
import {Capacitor0805HandSolderFootprint} from "../footprints/Capacitor0805HandSolder"
import {Capacitor0805HandSolderModel} from "../models/Capacitor0805HandSolder"
import {LcdHeaderFootprint} from "../footprints/LcdHeader"
import {LcdHeaderModel} from "../models/LcdHeader"

/** DisplayInterface: electrical intent, values, pin roles and layout are edited here. */
export function DisplayInterface() { return <schematicsheet name="DisplayInterface" displayName="DisplayInterface">
  <group name="DisplayInterface" schLayout={{layoutMode:"none"}}>
  <chip
    name="U701"
    pcbX={-18.0}
    pcbY={23.579}
    pcbRotation={0}
    layer="top"
    schX={0}
    schY={0}
    pinLabels={{"pin1":"VIN","pin2":"GND","pin3":"EN","pin4":"NC","pin5":"VOUT"}}
    schPinArrangement={{leftSide:["VIN","EN"],rightSide:["VOUT","NC"],bottomSide:["GND"]}}
    schWidth={1.85}
    schHeight={1.0}
   
    noConnect={["NC"]}
    pinAttributes={{"VIN":{"requiresPower":true,"requiresVoltage":5},"VOUT":{"providesPower":true,"providesVoltage":3.3},"GND":{"requiresGround":true}}}
    footprint={<Ap2112Sot25Footprint />}
    cadModel={Ap2112Sot25Model}
    manufacturerPartNumber={"AP2112K-3.3TRG1"}
    supplierPartNumbers={{jlcpcb:["C51118"]}}
  />
  <PowerNet pin=".U701 .VIN" net={N.V5}/>
  <PowerNet pin=".U701 .GND" net={N.GND}/>
  <PowerNet pin=".U701 .EN" net={N.V5}/>
  <PowerNet pin=".U701 .VOUT" net={N.LCD_3V3}/>
  <capacitor
    name="C701"
    pcbX={-22.0}
    pcbY={23.579}
    pcbRotation={0}
    layer="top"
    schX={-2.5}
    schY={1.8}
    capacitance="10uF"
   
    footprint={<Capacitor0805HandSolderFootprint />}
    cadModel={Capacitor0805HandSolderModel}
    manufacturerPartNumber={"CL21A106KAYNNNE"}
    supplierPartNumbers={{jlcpcb:["C15850"]}}
    schRotation={-90.0}
  />
  <PowerNet pin=".C701 .pin1" net={N.V5}/>
  <PowerNet pin=".C701 .pin2" net={N.GND}/>
  <capacitor
    name="C702"
    pcbX={-14.0}
    pcbY={23.579}
    pcbRotation={0}
    layer="top"
    schX={2.5}
    schY={1.8}
    capacitance="10uF"
   
    footprint={<Capacitor0805HandSolderFootprint />}
    cadModel={Capacitor0805HandSolderModel}
    manufacturerPartNumber={"CL21A106KAYNNNE"}
    supplierPartNumbers={{jlcpcb:["C15850"]}}
    schRotation={-90.0}
  />
  <PowerNet pin=".C702 .pin1" net={N.LCD_3V3}/>
  <PowerNet pin=".C702 .pin2" net={N.GND}/>
  <connector
    name="J701"
    pcbX={-35.5}
    pcbY={-8.89}
    pcbRotation={0}
    layer="top"
    schX={5}
    schY={0}
    pinLabels={{"pin1":"BL","pin2":"RST","pin3":"DC","pin4":"CS","pin5":"SCLK","pin6":"MOSI","pin7":"GND","pin8":"VCC"}}
    pinCount={8}
    connections={{BL:N.LCD_BL,RST:N.LCD_RST,DC:N.LCD_DC,CS:N.LCD_CS,SCLK:N.LCD_SCLK,MOSI:N.LCD_MOSI}}
    footprint={<LcdHeaderFootprint />}
    cadModel={LcdHeaderModel}
  />
  <PowerNet pin=".J701 .GND" net={N.GND}/>
  <PowerNet pin=".J701 .VCC" net={N.LCD_3V3}/>
  </group>
</schematicsheet> }
