import {PowerNet} from "../PowerNet"
import {BidirectionalTvsSymbol} from "../symbols/BidirectionalTvs"
import {N} from "../nets"
import {Capacitor0805HandSolderFootprint} from "../footprints/Capacitor0805HandSolder"
import {Capacitor0805HandSolderModel} from "../models/Capacitor0805HandSolder"
import {GctUsb4125Footprint} from "../footprints/GctUsb4125"
import {GctUsb4125Model} from "../models/GctUsb4125"
import {Led0805HandSolderFootprint} from "../footprints/Led0805HandSolder"
import {Led0805HandSolderModel} from "../models/Led0805HandSolder"
import {PowerHeaderFootprint} from "../footprints/PowerHeader"
import {PowerHeaderModel} from "../models/PowerHeader"
import {Resistor0805HandSolderFootprint} from "../footprints/Resistor0805HandSolder"
import {Resistor0805HandSolderModel} from "../models/Resistor0805HandSolder"
import {Sod123FFootprint} from "../footprints/Sod123F"
import {Sod123FModel} from "../models/Sod123F"

/** PowerInput: electrical intent, values, pin roles and layout are edited here. */
export function PowerInput() { return <schematicsheet name="PowerInput" displayName="PowerInput">
  <group name="PowerInput" schLayout={{layoutMode:"none"}}>
  <connector
    name="J301"
    allowOffBoard
    pcbX={-31.49}
    pcbY={-31.431}
    pcbRotation={0.0}
    layer="bottom"
    schX={-7}
    schY={0}
    pinLabels={{"pin1":"CC1","pin2":"VBUS_A","pin3":"GND_A","pin4":"CC2","pin5":"VBUS_B","pin6":"GND_B","pin7":"SHIELD1","pin8":"SHIELD2","pin9":"SHIELD3","pin10":"SHIELD4"}}
    standard="usb_c"
    schPinArrangement={{rightSide:["CC1","CC2"],topSide:["VBUS_A"],bottomSide:["GND_A"]}}
    schWidth={1.8}
    schHeight={1.0}
    internallyConnectedPins={[["VBUS_A","VBUS_B"],["GND_A","GND_B","SHIELD1","SHIELD2","SHIELD3","SHIELD4"]]}
    pinCount={10}
    connections={{CC1:N.USB_CC1,CC2:N.USB_CC2}}
    pinAttributes={{"VBUS_A":{"providesPower":true,"providesVoltage":5},"VBUS_B":{"providesPower":true,"providesVoltage":5},"GND_A":{"providesGround":true}}}
    footprint={<GctUsb4125Footprint />}
    cadModel={GctUsb4125Model}
    manufacturerPartNumber={"USB4125-GF-A-0190"}
    supplierPartNumbers={{jlcpcb:["C5246813"]}}
  />
  <PowerNet pin=".J301 .VBUS_A" net={N.V5}/>
  <PowerNet pin=".J301 .GND_A" net={N.GND}/>
  <PowerNet pin=".J301 .VBUS_B" net={N.V5}/>
  <PowerNet pin=".J301 .GND_B" net={N.GND}/>
  <PowerNet pin=".J301 .SHIELD1" net={N.GND}/>
  <PowerNet pin=".J301 .SHIELD2" net={N.GND}/>
  <PowerNet pin=".J301 .SHIELD3" net={N.GND}/>
  <PowerNet pin=".J301 .SHIELD4" net={N.GND}/>
  <resistor
    name="R301"
    pcbX={-40.87}
    pcbY={-23.881}
    pcbRotation={0.0}
    layer="bottom"
    schX={-3}
    schY={-2}
    resistance="5.1k"
    connections={{pin1:N.USB_CC2}}
    footprint={<Resistor0805HandSolderFootprint />}
    cadModel={Resistor0805HandSolderModel}
    manufacturerPartNumber={"0805W8F5101T5E"}
    supplierPartNumbers={{jlcpcb:["C27834"]}}
    schRotation={-90.0}
  />
  <PowerNet pin=".R301 .pin2" net={N.GND}/>
  <resistor
    name="R302"
    pcbX={-27.01}
    pcbY={-23.891}
    pcbRotation={180}
    layer="bottom"
    schX={-3}
    schY={2}
    resistance="5.1k"
    connections={{pin1:N.USB_CC1}}
    footprint={<Resistor0805HandSolderFootprint />}
    cadModel={Resistor0805HandSolderModel}
    manufacturerPartNumber={"0805W8F5101T5E"}
    supplierPartNumbers={{jlcpcb:["C27834"]}}
    schRotation={-90.0}
  />
  <PowerNet pin=".R302 .pin2" net={N.GND}/>
  <capacitor
    name="C301"
    pcbX={-40.77}
    pcbY={-21.861}
    pcbRotation={0.0}
    layer="bottom"
    schX={1}
    schY={0}
    capacitance="100nF"
   
    footprint={<Capacitor0805HandSolderFootprint />}
    cadModel={Capacitor0805HandSolderModel}
    manufacturerPartNumber={"CC0805KRX7R9BB104"}
    supplierPartNumbers={{jlcpcb:["C49678"]}}
    schRotation={-90.0}
  />
  <PowerNet pin=".C301 .pin1" net={N.V5}/>
  <PowerNet pin=".C301 .pin2" net={N.GND}/>
  <capacitor
    name="C302"
    pcbX={-40.72}
    pcbY={-19.881}
    pcbRotation={0.0}
    layer="bottom"
    schX={2.5}
    schY={0}
    capacitance="10uF"
   
    footprint={<Capacitor0805HandSolderFootprint />}
    cadModel={Capacitor0805HandSolderModel}
    manufacturerPartNumber={"CL21A106KAYNNNE"}
    supplierPartNumbers={{jlcpcb:["C15850"]}}
    schRotation={-90.0}
  />
  <PowerNet pin=".C302 .pin1" net={N.V5}/>
  <PowerNet pin=".C302 .pin2" net={N.GND}/>
  <diode
    name="D301"
    pcbX={-30.59}
    pcbY={-21.4835}
    pcbRotation={90.0}
    layer="bottom"
    schX={6}
    schY={1.5}
    displayName="5 V bidirectional TVS"
    symbol={<BidirectionalTvsSymbol />}
   
    footprint={<Sod123FFootprint />}
    cadModel={Sod123FModel}
    manufacturerPartNumber={"SMF5.0CA"}
    supplierPartNumbers={{jlcpcb:["C19077498"]}}
  />
  <PowerNet pin=".D301 .pin1" net={N.V5}/>
  <PowerNet pin=".D301 .pin2" net={N.GND}/>
  <led
    name="D302"
    pinLabels={{pin1:"anode",pin2:"cathode"}}
    color="green"
    schRotation={-90}
    pcbX={-38.9222}
    pcbY={-32.6458}
    pcbRotation={180}
    layer="bottom"
    schX={11}
    schY={3}
    connections={{pin2:N.POWER_LED_K}}
    footprint={<Led0805HandSolderFootprint />}
    cadModel={Led0805HandSolderModel}
    manufacturerPartNumber={"KT-0805G"}
    supplierPartNumbers={{jlcpcb:["C2297"]}}
  />
  <PowerNet pin=".D302 .pin1" net={N.V5}/>
  <resistor
    name="R303"
    pcbX={-38.8968}
    pcbY={-29.9788}
    pcbRotation={0.0}
    layer="bottom"
    schX={11}
    schY={0}
    resistance="560"
    connections={{pin2:N.POWER_LED_K}}
    footprint={<Resistor0805HandSolderFootprint />}
    cadModel={Resistor0805HandSolderModel}
    manufacturerPartNumber={"0805W8F5600T5E"}
    supplierPartNumbers={{jlcpcb:["C28636"]}}
    schRotation={90.0}
  />
  <PowerNet pin=".R303 .pin1" net={N.GND}/>
  <connector
    name="J302"
    kicadFootprintMetadata={{attributes:{exclude_from_bom:true}}}
    kicadSymbolMetadata={{inBom:false}}
    schPinArrangement={{topSide:["V5"],bottomSide:["GND"]}}
    schWidth={0.8}
    schHeight={0.8}
    pcbX={-23.0}
    pcbY={-30.421}
    pcbRotation={90.0}
    layer="top"
    schX={15}
    schY={0}
    pinLabels={{"pin1":"V5","pin2":"GND"}}
    pinCount={2}
   
    footprint={<PowerHeaderFootprint />}
    cadModel={PowerHeaderModel}
    schRotation={-90.0}
  />
  <PowerNet pin=".J302 .V5" net={N.V5}/>
  <PowerNet pin=".J302 .GND" net={N.GND}/>
  </group>
</schematicsheet> }
