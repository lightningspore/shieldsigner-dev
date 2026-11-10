import {Circuit} from '@tscircuit/core'
import {inspectPillSchema} from './pill-schema'
import {convertCircuitJsonToPcbSvg,convertCircuitJsonToStackedSchematicSheetsSvg,convertCircuitJsonToSchematicSvg} from 'circuit-to-svg'
import {mkdirSync,writeFileSync,readFileSync,readdirSync} from 'node:fs'
import {createHash} from 'node:crypto'
// Standard asset bundling: only imported file URLs are embedded, never PCB geometry.
Bun.plugin({name:'portable-glb-assets',setup(build) {
  build.onLoad({filter:/\.glb$/},async ({path})=>({loader:'js',contents:
    `export default ${JSON.stringify('data:model/gltf-binary;base64,'+Buffer.from(await Bun.file(path).arrayBuffer()).toString('base64'))}`}))
}})

/** Ordinary compilation only: the returned JSON is never patched or filtered. */
export async function compilePill({routing=true,schematicOnly=false}={}) {
  const PillCarrier=(await import('../src/PillCarrier')).default
  const circuit=new Circuit({platform:{pcbDisabled:schematicOnly}})
  circuit.add(<PillCarrier routing={routing}/>)
  await circuit.renderUntilSettled()
  return circuit.getCircuitJson()
}
const directory='dist/pill-native'
if(import.meta.main) {
  const circuit=await compilePill()
  mkdirSync(directory,{recursive:true})
  writeFileSync(`${directory}/board.circuit.json`,JSON.stringify(circuit,null,2)+'\n')
  const schemaCompatibility=inspectPillSchema(circuit)
  writeFileSync(`${directory}/schema-compatibility.json`,JSON.stringify(schemaCompatibility,null,2)+'\n')
  for(const layer of ['top','bottom'] as const)
    writeFileSync(`${directory}/pcb-${layer}.svg`,convertCircuitJsonToPcbSvg(circuit,{layer,width:1600,height:700,showFabricationNotes:false,shouldDrawRatsNest:false}))
  writeFileSync(`${directory}/schematic.svg`,convertCircuitJsonToStackedSchematicSheetsSvg(circuit,{width:1800}))
  const sheets=circuit.filter(e=>e.type==='schematic_sheet')
  mkdirSync(`${directory}/schematics`,{recursive:true})
  for(const sheet of sheets)
    writeFileSync(`${directory}/schematics/${sheet.name}.svg`,convertCircuitJsonToSchematicSvg(circuit,{width:1600,height:1000,schematicSheetId:sheet.schematic_sheet_id}))
  const errors=circuit.filter(e=>e.type.endsWith('_error'))
  const warnings=circuit.filter(e=>e.type.endsWith('_warning'))
  const files=['src/PillCarrier.tsx',...readdirSync('src/pill',{recursive:true}).filter(p=>typeof p==='string').map(p=>`src/pill/${p}`).filter(p=>/\.(tsx?|svg|glb|json)$/.test(p))]
  const sourceSha256=Object.fromEntries(files.map(p=>[p,createHash('sha256').update(readFileSync(p)).digest('hex')]))
  writeFileSync(`${directory}/build-report.json`,JSON.stringify({entry:'src/PillCarrier.tsx',method:'Unmodified native tscircuit render; local routing and recomputed copper pours',sourceSha256,errors,warnings,schemaCompatibility: {status:schemaCompatibility.length?"Upstream core/schema incompatibilities recorded; output unmodified":"valid",records:schemaCompatibility.length},qualification:'Software checks do not qualify assembled hardware'},null,2)+'\n')
  console.log(`Rendered ${circuit.filter(e=>e.type==='source_component').length} source components and ${sheets.length} schematic sheets.`)
  if(errors.length)throw new Error(`${errors.length} native renderer errors; see ${directory}/build-report.json`)
}
