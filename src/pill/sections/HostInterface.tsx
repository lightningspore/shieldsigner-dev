import {PowerNet} from "../PowerNet"
import {N} from "../nets"
import {Capacitor0805HandSolderFootprint} from "../footprints/Capacitor0805HandSolder"
import {Capacitor0805HandSolderModel} from "../models/Capacitor0805HandSolder"
import {LuckfoxMiniFootprint} from "../footprints/LuckfoxMini"
import {LuckfoxMiniModel} from "../models/LuckfoxMini"
import {SolderJumperFootprint} from "../footprints/SolderJumper"

/** HostInterface: electrical intent, values, pin roles and layout are edited here. */
export function HostInterface() { return <schematicsheet name="HostInterface" displayName="HostInterface">
  <group name="HostInterface" schLayout={{layoutMode:"none"}}>
  <chip
    name="U202"
    pcbX={-24.8725}
    pcbY={15.459}
    pcbRotation={0.0}
    layer="bottom"
    schX={0}
    schY={0}
    internallyConnectedPins={[["VBUS","VBUS_CAST"],["GND","GND_CAST"],["V3V3_OUT","V3V3_OUT_CAST"],["UART_TX","UART_TX_CAST"],["UART_RX","UART_RX_CAST"],["SPI_CS","SPI_CS_CAST"],["SPI_SCLK","SPI_SCLK_CAST"],["SPI_MOSI","SPI_MOSI_CAST"],["LCD_RST","LCD_RST_CAST"],["LCD_DC","LCD_DC_CAST"],["KEY3","KEY3_CAST"],["LEFT","LEFT_CAST"],["UP","UP_CAST"],["I2C_SDA","I2C_SDA_CAST"],["I2C_SCL","I2C_SCL_CAST"],["PRESS","PRESS_CAST"],["DOWN","DOWN_CAST"],["RIGHT","RIGHT_CAST"],["KEY1","KEY1_CAST"],["KEY2","KEY2_CAST"],["GND2","GND2_CAST"],["V1V8_OUT","V1V8_OUT_CAST"]]}
    pinLabels={{"pin1":"VBUS","pin2":"GND","pin3":"V3V3_OUT","pin4":"UART_TX","pin5":"UART_RX","pin6":"SPI_CS","pin7":"SPI_SCLK","pin8":"SPI_MOSI","pin9":"LCD_RST","pin10":"LCD_DC","pin11":"KEY3","pin12":"LEFT","pin13":"UP","pin14":"I2C_SDA","pin15":"I2C_SCL","pin16":"PRESS","pin17":"DOWN","pin18":"RIGHT","pin19":"KEY1","pin20":"KEY2","pin21":"GND2","pin22":"V1V8_OUT","pin23":"VBUS_CAST","pin24":"GND_CAST","pin25":"V3V3_OUT_CAST","pin26":"UART_TX_CAST","pin27":"UART_RX_CAST","pin28":"SPI_CS_CAST","pin29":"SPI_SCLK_CAST","pin30":"SPI_MOSI_CAST","pin31":"LCD_RST_CAST","pin32":"LCD_DC_CAST","pin33":"KEY3_CAST","pin34":"LEFT_CAST","pin35":"UP_CAST","pin36":"I2C_SDA_CAST","pin37":"I2C_SCL_CAST","pin38":"PRESS_CAST","pin39":"DOWN_CAST","pin40":"RIGHT_CAST","pin41":"KEY1_CAST","pin42":"KEY2_CAST","pin43":"GND2_CAST","pin44":"V1V8_OUT_CAST"}}
    schPinArrangement={{"leftSide":["pin1","pin2","pin3","pin4","pin5","pin6","pin7","pin8","pin9","pin10","pin11"],"rightSide":["pin12","pin13","pin14","pin15","pin16","pin17","pin18","pin19","pin20","pin21","pin22"]}}
    schWidth={2.7}
    schHeight={2.4}
    connections={{UART_TX:N.HOST_TX,SPI_CS:N.HOST_CS,UART_RX:N.HOST_RX,SPI_SCLK:N.LCD_SCLK,SPI_MOSI:N.LCD_MOSI,LCD_RST:N.LCD_RST,LCD_DC:N.LCD_DC,KEY3:N.Key3,LEFT:N.JoystickLeft,UP:N.JoystickUp,PRESS:N.JoystickPress,DOWN:N.JoystickDown,RIGHT:N.JoystickRight,KEY1:N.Key1,KEY2:N.Key2}}
    noConnect={["V1V8_OUT","V1V8_OUT_CAST","I2C_SDA","I2C_SDA_CAST","I2C_SCL","I2C_SCL_CAST"]}
    pinAttributes={{"VBUS":{"requiresPower":true,"requiresVoltage":5},"V3V3_OUT":{"providesPower":true,"providesVoltage":3.3},"GND":{"requiresGround":true},"GND2":{"requiresGround":true}}}
    footprint={<LuckfoxMiniFootprint />}
    cadModel={LuckfoxMiniModel}
    manufacturerPartNumber={"LuckFox_Pico_MINI"}
  />
  <PowerNet pin=".U202 .VBUS" net={N.V5}/>
  <PowerNet pin=".U202 .GND" net={N.GND}/>
  <PowerNet pin=".U202 .V3V3_OUT" net={N.V3V3}/>
  <PowerNet pin=".U202 .GND2" net={N.GND}/>
  <capacitor
    name="C201"
    pcbX={-20.24}
    pcbY={14.179}
    pcbRotation={90.0}
    layer="bottom"
    schX={-4}
    schY={4}
    capacitance="10uF"
   
    footprint={<Capacitor0805HandSolderFootprint />}
    cadModel={Capacitor0805HandSolderModel}
    manufacturerPartNumber={"CL21A106KAYNNNE"}
    supplierPartNumbers={{jlcpcb:["C15850"]}}
    schRotation={-90.0}
  />
  <PowerNet pin=".C201 .pin1" net={N.V5}/>
  <PowerNet pin=".C201 .pin2" net={N.GND}/>
  <solderjumper doNotPlace
    name="JP201"
    pcbX={37.5064}
    pcbY={6.2924}
    pcbRotation={0.0}
    layer="bottom"
    schX={-7}
    schY={4}
    pinCount={2}
    bridged={true}
    connections={{pin2:N.LCD_BL}}
    footprint={<SolderJumperFootprint bridged />}
    cadModel={null}
  />
  <PowerNet pin=".JP201 .pin1" net={N.V3V3}/>
  <solderjumper doNotPlace
    name="JP202"
    schRotation={90}
    pcbX={31.639}
    pcbY={6.2924}
    pcbRotation={180}
    layer="bottom"
    schX={-7}
    schY={0}
    pinCount={2}
    bridged={false}
    connections={{pin1:N.LEGACY_BL,pin2:N.LCD_BL}}
    footprint={<SolderJumperFootprint />}
    cadModel={null}
  />
  <solderjumper doNotPlace
    name="JP203"
    pcbX={21.86}
    pcbY={11.982}
    pcbRotation={0.0}
    layer="bottom"
    schX={-7}
    schY={-4}
    pinCount={2}
    bridged={true}
    connections={{pin1:N.LEGACY_CS,pin2:N.HOST_CS}}
    footprint={<SolderJumperFootprint bridged />}
    cadModel={null}
  />
  <solderjumper doNotPlace
    name="JP204"
    pcbX={24.9334}
    pcbY={6.267}
    pcbRotation={0.0}
    layer="bottom"
    schX={-10}
    schY={-4}
    pinCount={2}
    bridged={false}
    connections={{pin1:N.LEGACY_BL,pin2:N.HOST_CS}}
    footprint={<SolderJumperFootprint />}
    cadModel={null}
  />
  <solderjumper doNotPlace
    name="JP205"
    pcbX={28.5656}
    pcbY={11.9566}
    pcbRotation={180}
    layer="bottom"
    schX={4.5}
    schY={4}
    pinCount={2}
    bridged={true}
    connections={{pin1:N.LEGACY_CS,pin2:N.LCD_CS}}
    footprint={<SolderJumperFootprint bridged />}
    cadModel={null}
  />
  <solderjumper doNotPlace
    name="JP206"
    pcbX={34.6362}
    pcbY={11.9566}
    pcbRotation={0.0}
    layer="bottom"
    schX={4.5}
    schY={0}
    pinCount={2}
    bridged={false}
    connections={{pin2:N.LCD_CS}}
    footprint={<SolderJumperFootprint />}
    cadModel={null}
    schRotation={90.0}
  />
  <PowerNet pin=".JP206 .pin1" net={N.GND}/>
  </group>
</schematicsheet> }
