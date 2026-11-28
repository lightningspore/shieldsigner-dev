import { compileBoard } from './build'
import reference from '../variants/full-size-pico/reference-board.json'
import { mkdirSync, writeFileSync } from 'node:fs'
const outputDir='dist/full-size-pico/experimental'
const circuit=await compileBoard({data:reference as any,outputDir,writeReport:true,allowedOutside:[],attachNativeDetails:false})
mkdirSync(outputDir,{recursive:true})
writeFileSync(`${outputDir}/full-pico.circuit.json`,JSON.stringify(circuit,null,2)+'\n')
console.log('Compiled the isolated native reference with its exact lands, nets and copper; main preview unchanged.')
