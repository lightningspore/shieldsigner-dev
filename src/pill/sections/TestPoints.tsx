import {PowerNet} from "../PowerNet"
import {N} from "../nets"
import {TestPadFootprint} from "../footprints/TestPad"

/** TestPoints: electrical intent, values, pin roles and layout are edited here. */
export function TestPoints() { return <schematicsheet name="TestPoints" displayName="TestPoints">
  <group name="TestPoints" schLayout={{layoutMode:"none"}}>
  <testpoint doNotPlace
    name="TP801"
    pcbX={-28.482909}
    pcbY={-21.785909}
    pcbRotation={180}
    layer="bottom"
    schX={-12}
    schY={8}
   
    footprint={<TestPadFootprint />}
    cadModel={null}
  />
  <PowerNet pin=".TP801 .pin1" net={N.V5}/>
  <testpoint doNotPlace
    name="TP802"
    pcbX={5.359632}
    pcbY={14.486}
    pcbRotation={180}
    layer="bottom"
    schX={-4}
    schY={8}
   
    footprint={<TestPadFootprint />}
    cadModel={null}
  />
  <PowerNet pin=".TP802 .pin1" net={N.V3V3}/>
  <testpoint doNotPlace
    name="TP803"
    pcbX={-28.195667}
    pcbY={14.189}
    pcbRotation={0}
    layer="top"
    schX={4}
    schY={8}
   
    footprint={<TestPadFootprint />}
    cadModel={null}
  />
  <PowerNet pin=".TP803 .pin1" net={N.LCD_3V3}/>
  <testpoint doNotPlace
    name="TP804"
    pcbX={-14.4}
    pcbY={1.179}
    pcbRotation={180}
    layer="bottom"
    schX={12}
    schY={8}
   
    footprint={<TestPadFootprint />}
    cadModel={null}
  />
  <PowerNet pin=".TP804 .pin1" net={N.GND}/>
  <testpoint doNotPlace
    name="TP805"
    pcbX={23.437674}
    pcbY={18.458259}
    pcbRotation={180}
    layer="bottom"
    schX={-12}
    schY={0}
   
    footprint={<TestPadFootprint />}
    cadModel={null}
  />
  <PowerNet pin=".TP805 .pin1" net={N.SC_VCC}/>
  <testpoint doNotPlace
    name="TP806"
    pcbX={-3.7475}
    pcbY={20.2265}
    pcbRotation={180}
    layer="bottom"
    schX={-4}
    schY={0}
    connections={{pin1:N.SC_TX}}
    footprint={<TestPadFootprint />}
    cadModel={null}
  />
  <testpoint doNotPlace
    name="TP807"
    pcbX={-2.625}
    pcbY={17.104}
    pcbRotation={180}
    layer="bottom"
    schX={4}
    schY={0}
    connections={{pin1:N.SC_RX}}
    footprint={<TestPadFootprint />}
    cadModel={null}
  />
  <testpoint doNotPlace
    name="TP808"
    pcbX={17.76}
    pcbY={15.499}
    pcbRotation={180}
    layer="bottom"
    schX={12}
    schY={0}
    connections={{pin1:N.SC_CLK}}
    footprint={<TestPadFootprint />}
    cadModel={null}
  />
  <testpoint doNotPlace
    name="TP809"
    pcbX={9.866667}
    pcbY={15.901222}
    pcbRotation={180}
    layer="bottom"
    schX={-12}
    schY={-8}
    connections={{pin1:N.SC_IO}}
    footprint={<TestPadFootprint />}
    cadModel={null}
  />
  <testpoint doNotPlace
    name="TP810"
    pcbX={33.64375}
    pcbY={0.654}
    pcbRotation={180}
    layer="bottom"
    schX={-4}
    schY={-8}
    connections={{pin1:N.CARD_DET}}
    footprint={<TestPadFootprint />}
    cadModel={null}
  />
  <testpoint doNotPlace
    name="TP811"
    pcbX={19.482705}
    pcbY={4.493605}
    pcbRotation={180}
    layer="bottom"
    schX={4}
    schY={-8}
    connections={{pin1:N.SC_RST}}
    footprint={<TestPadFootprint />}
    cadModel={null}
  />
  <testpoint doNotPlace
    name="TP812"
    pcbX={-24.444}
    pcbY={-23.807}
    pcbRotation={180}
    layer="bottom"
    schX={12}
    schY={-8}
   
    footprint={<TestPadFootprint />}
    cadModel={null}
  />
  <PowerNet pin=".TP812 .pin1" net={N.GND}/>
  </group>
</schematicsheet> }
