import{readFileSync,writeFileSync,readdirSync}from'node:fs'
import{Resvg}from'@resvg/resvg-js'
const dir='dist/pill-native'
for(const name of ['pcb-top','pcb-bottom','schematic',...readdirSync(`${dir}/schematics`).filter(p=>p.endsWith('.svg')).map(p=>`schematics/${p.slice(0,-4)}`)]) {
 let svg=readFileSync(`${dir}/${name}.svg`,'utf8')
 if(name==='pcb-bottom')svg=svg.replace(/(<svg[^>]*>)/,'$1<g transform="translate(1600 0) scale(-1 1)">').replace('</svg>','</g></svg>')
 writeFileSync(`${dir}/${name}.png`,new Resvg(svg,{fitTo:{mode:'width',value:name==='schematic'?1800:1600}}).render().asPng())
}
