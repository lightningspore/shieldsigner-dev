import {PowerNet} from "../PowerNet"
import {N} from "../nets"
import {AmphenolSmartcardFootprint} from "../footprints/AmphenolSmartcard"
import {AmphenolSmartcardModel} from "../models/AmphenolSmartcard"
import {Capacitor0805HandSolderFootprint} from "../footprints/Capacitor0805HandSolder"
import {Capacitor0805HandSolderModel} from "../models/Capacitor0805HandSolder"
import {Resistor0805HandSolderFootprint} from "../footprints/Resistor0805HandSolder"
import {Resistor0805HandSolderModel} from "../models/Resistor0805HandSolder"
import {Sec1210QfnFootprint} from "../footprints/Sec1210Qfn"
import {Sec1210QfnModel} from "../models/Sec1210Qfn"

/** ISO-7816 socket, clock damping and contact biasing. */
export function CardSocket(){return <schematicsheet name="CardSocket" displayName="Smartcard socket"><group name="CardSocket" schLayout={{layoutMode:"none"}}>
  <connector
    name="J601"
    pcbX={11.42}
    pcbY={-20.371}
    pcbRotation={0.0}
    layer="bottom"
    schX={0}
    schY={0}
    pinLabels={{"pin1":"VCC","pin2":"RST","pin3":"CLK","pin4":"RFU1","pin5":"GND","pin6":"VPP","pin7":"IO","pin8":"RFU2","pin9":"DETECT_GND","pin10":"DETECT"}}
    pinCount={10}
    connections={{RST:N.SC_RST,CLK:N.SC_CLK,IO:N.SC_IO,DETECT:N.CARD_DET}}
    noConnect={["RFU1","RFU2"]}
    footprint={<AmphenolSmartcardFootprint />}
    cadModel={AmphenolSmartcardModel}
    manufacturerPartNumber={"7312P0225A13LF"}
    supplierPartNumbers={{jlcpcb:["C5417011"]}}
  />
  <PowerNet pin=".J601 .VCC" net={N.SC_VCC}/>
  <PowerNet pin=".J601 .GND" net={N.GND}/>
  <PowerNet pin=".J601 .VPP" net={N.SC_VCC}/>
  <PowerNet pin=".J601 .DETECT_GND" net={N.GND}/>
  <capacitor
    name="C604"
    pcbX={21.0472}
    pcbY={0.379}
    pcbRotation={180}
    layer="bottom"
    schX={3}
    schY={2}
    capacitance="1uF"
   
    footprint={<Capacitor0805HandSolderFootprint />}
    cadModel={Capacitor0805HandSolderModel}
    manufacturerPartNumber={"CL21B105KBFNNNE"}
    supplierPartNumbers={{jlcpcb:["C28323"]}}
    schRotation={-90.0}
  />
  <PowerNet pin=".C604 .pin1" net={N.SC_VCC}/>
  <PowerNet pin=".C604 .pin2" net={N.GND}/>
  <capacitor
    name="C605"
    pcbX={15.891}
    pcbY={20.219}
    pcbRotation={270.0}
    layer="bottom"
    schX={-3}
    schY={-1.5}
    capacitance="33pF"
    connections={{pin1:N.SC_RST}}
    footprint={<Capacitor0805HandSolderFootprint />}
    cadModel={Capacitor0805HandSolderModel}
    manufacturerPartNumber={"CC0805JRNPO9BN330"}
    supplierPartNumbers={{jlcpcb:["C107115"]}}
    schRotation={-90.0}
  />
  <PowerNet pin=".C605 .pin2" net={N.GND}/>
  <capacitor
    name="C606"
    pcbX={13.9098}
    pcbY={20.2444}
    pcbRotation={270.0}
    layer="bottom"
    schX={-5}
    schY={-1.5}
    capacitance="33pF"
    connections={{pin1:N.SC_CLK}}
    footprint={<Capacitor0805HandSolderFootprint />}
    cadModel={Capacitor0805HandSolderModel}
    manufacturerPartNumber={"CC0805JRNPO9BN330"}
    supplierPartNumbers={{jlcpcb:["C107115"]}}
    schRotation={-90.0}
  />
  <PowerNet pin=".C606 .pin2" net={N.GND}/>
  <resistor
    name="R604"
    pcbX={12.0}
    pcbY={17.379}
    pcbRotation={180}
    layer="bottom"
    schX={-4}
    schY={2}
    resistance="47"
    connections={{pin1:N.SC_CLK_RAW,pin2:N.SC_CLK}}
    footprint={<Resistor0805HandSolderFootprint />}
    cadModel={Resistor0805HandSolderModel}
    manufacturerPartNumber={"0805W8F470JT5E"}
    supplierPartNumbers={{jlcpcb:["C17714"]}}
  />
  <resistor
    name="R605"
    pcbX={16.4}
    pcbY={17.379}
    pcbRotation={0.0}
    layer="bottom"
    schX={3}
    schY={0}
    resistance="10k"
    connections={{pin2:N.SC_RST}}
    footprint={<Resistor0805HandSolderFootprint />}
    cadModel={Resistor0805HandSolderModel}
    manufacturerPartNumber={"0805W8F1002T5E"}
    supplierPartNumbers={{jlcpcb:["C17414"]}}
    schRotation={90.0}
  />
  <PowerNet pin=".R605 .pin1" net={N.GND}/>
  <resistor
    name="R606"
    pcbX={11.954}
    pcbY={20.1936}
    pcbRotation={90.0}
    layer="bottom"
    schX={3}
    schY={-3.5}
    resistance="100k"
    connections={{pin2:N.SC_IO}}
    footprint={<Resistor0805HandSolderFootprint />}
    cadModel={Resistor0805HandSolderModel}
    manufacturerPartNumber={"0805W8F1003T5E"}
    supplierPartNumbers={{jlcpcb:["C149504"]}}
    schRotation={90.0}
  />
  <PowerNet pin=".R606 .pin1" net={N.GND}/>
</group></schematicsheet>}
