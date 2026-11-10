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

/** SmartcardInterface: electrical intent, values, pin roles and layout are edited here. */
export function SmartcardInterface() { return <schematicsheet name="SmartcardInterface" displayName="SmartcardInterface">
  <group name="SmartcardInterface" schLayout={{layoutMode:"none"}}>
  <chip
    name="U601"
    pcbX={7.0}
    pcbY={20.279}
    pcbRotation={0.0}
    layer="bottom"
    schX={0}
    schY={0}
    pinLabels={{"pin1":"SC2_RST","pin2":"SC2_VCC","pin3":"VDD5","pin4":"SC_C8","pin5":"SC_C4","pin6":"SC_IO","pin7":"SC_CLK","pin8":"SC_RST","pin9":"SC_VCC","pin10":"CARD_DET","pin11":"UART_RX","pin12":"SPI_CLK_CTS","pin13":"SPI_CE_RTS","pin14":"UART_TX","pin15":"TEST","pin16":"USB_DM","pin17":"USB_DP","pin18":"VDD33","pin19":"JTAG_CLK","pin20":"LED_JTAG_TDO","pin21":"SC2_DET_JTAG_TDI","pin22":"RESET","pin23":"SC2_IO","pin24":"SC2_CLK","pin25":"GND"}}
    schPinArrangement={{"leftSide":["pin1","pin2","pin3","pin4","pin5","pin6","pin7","pin8","pin9","pin10","pin11","pin12","pin13"],"rightSide":["pin14","pin15","pin16","pin17","pin18","pin19","pin20","pin21","pin22","pin23","pin24","pin25"]}}
    schWidth={3.75}
    schHeight={2.8}
    connections={{SC_IO:N.SC_IO,SC_CLK:N.SC_CLK_RAW,SC_RST:N.SC_RST,CARD_DET:N.CARD_DET,UART_RX:N.SC_RX,UART_TX:N.SC_TX,TEST:N.SC_TEST,RESET:N.SC_RESET}}
    noConnect={["SC_C8","SC_C4","SC2_RST","SC2_VCC","SPI_CLK_CTS","SPI_CE_RTS","USB_DM","USB_DP","JTAG_CLK","LED_JTAG_TDO","SC2_DET_JTAG_TDI","SC2_IO","SC2_CLK"]}
    pinAttributes={{"VDD5":{"requiresPower":true,"requiresVoltage":5},"VDD33":{"providesPower":true,"providesVoltage":3.3},"GND":{"requiresGround":true}}}
    footprint={<Sec1210QfnFootprint />}
    cadModel={Sec1210QfnModel}
    manufacturerPartNumber={"SEC1210/PV-UR2"}
    supplierPartNumbers={{jlcpcb:["C633309"]}}
  />
  <PowerNet pin=".U601 .VDD5" net={N.V5}/>
  <PowerNet pin=".U601 .SC_VCC" net={N.SC_VCC}/>
  <PowerNet pin=".U601 .VDD33" net={N.SC_VDD33}/>

  <capacitor
    name="C601"
    pcbX={12.3}
    pcbY={25.679}
    pcbRotation={180}
    layer="bottom"
    schX={7}
    schY={-0.8}
    capacitance="100nF"
    connections={{pin1:N.SC_RESET}}
    footprint={<Capacitor0805HandSolderFootprint />}
    cadModel={Capacitor0805HandSolderModel}
    manufacturerPartNumber={"CC0805KRX7R9BB104"}
    supplierPartNumbers={{jlcpcb:["C49678"]}}
    schRotation={-90.0}
  />
  <PowerNet pin=".C601 .pin2" net={N.GND}/>
  <capacitor
    name="C602"
    pcbX={6.5399}
    pcbY={25.7562}
    pcbRotation={0.0}
    layer="bottom"
    schX={-4}
    schY={3.8}
    capacitance="1uF"
   
    footprint={<Capacitor0805HandSolderFootprint />}
    cadModel={Capacitor0805HandSolderModel}
    manufacturerPartNumber={"CL21B105KBFNNNE"}
    supplierPartNumbers={{jlcpcb:["C28323"]}}
    schRotation={-90.0}
  />
  <PowerNet pin=".C602 .pin1" net={N.V5}/>
  <PowerNet pin=".C602 .pin2" net={N.GND}/>
  <capacitor
    name="C603"
    pcbX={0.6}
    pcbY={22.089}
    pcbRotation={0.0}
    layer="bottom"
    schX={4}
    schY={3.8}
    capacitance="1uF"
   
    footprint={<Capacitor0805HandSolderFootprint />}
    cadModel={Capacitor0805HandSolderModel}
    manufacturerPartNumber={"CL21B105KBFNNNE"}
    supplierPartNumbers={{jlcpcb:["C28323"]}}
    schRotation={-90.0}
  />
  <PowerNet pin=".C603 .pin1" net={N.SC_VDD33}/>
  <PowerNet pin=".C603 .pin2" net={N.GND}/>



  <resistor
    name="R601"
    pcbX={9.4}
    pcbY={26.779}
    pcbRotation={270.0}
    layer="bottom"
    schX={6.5}
    schY={1.2}
    resistance="100k"
    connections={{pin1:N.SC_RESET}}
    footprint={<Resistor0805HandSolderFootprint />}
    cadModel={Resistor0805HandSolderModel}
    manufacturerPartNumber={"0805W8F1003T5E"}
    supplierPartNumbers={{jlcpcb:["C149504"]}}
    schRotation={90.0}
  />
  <PowerNet pin=".R601 .pin2" net={N.V5}/>
  <resistor
    name="R602"
    pcbX={-6.9}
    pcbY={20.379}
    pcbRotation={180}
    layer="bottom"
    schX={-5}
    schY={-4}
    resistance="100"
    connections={{pin1:N.HOST_TX,pin2:N.SC_RX}}
    footprint={<Resistor0805HandSolderFootprint />}
    cadModel={Resistor0805HandSolderModel}
    manufacturerPartNumber={"0805W8F1000T5E"}
    supplierPartNumbers={{jlcpcb:["C17408"]}}
  />
  <resistor
    name="R603"
    pcbX={-6.9}
    pcbY={22.379}
    pcbRotation={180}
    layer="bottom"
    schX={5}
    schY={-3}
    resistance="100"
    connections={{pin1:N.HOST_RX,pin2:N.SC_TX}}
    footprint={<Resistor0805HandSolderFootprint />}
    cadModel={Resistor0805HandSolderModel}
    manufacturerPartNumber={"0805W8F1000T5E"}
    supplierPartNumbers={{jlcpcb:["C17408"]}}
  />



  <resistor
    name="R607"
    pcbX={1.65}
    pcbY={19.239}
    pcbRotation={270.0}
    layer="bottom"
    schX={4}
    schY={1.2}
    resistance="10k"
    connections={{pin2:N.SC_TEST}}
    footprint={<Resistor0805HandSolderFootprint />}
    cadModel={Resistor0805HandSolderModel}
    manufacturerPartNumber={"0805W8F1002T5E"}
    supplierPartNumbers={{jlcpcb:["C17414"]}}
    schRotation={90.0}
  />
  <PowerNet pin=".R607 .pin1" net={N.GND}/>
  {/* Exposed-pad return escapes directly through a via, away from peripheral QFN pins. */}
  <trace from=".U601 .GND" to={N.GND} schDisplayLabel="GND" pcbPath={[{x:0,y:0,via:true,fromLayer:"bottom",toLayer:"top"},{x:0,y:0}]} width={0.25}/>
  </group>
</schematicsheet> }
