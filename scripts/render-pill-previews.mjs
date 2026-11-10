/** Raster previews of the compiled tscircuit output; bottom is viewed from below. */
import {Resvg} from '@resvg/resvg-js'
import {readFileSync,writeFileSync} from 'node:fs'
for(const side of ['top','bottom']) {
  let svg=readFileSync(`dist/pill-tscircuit/pcb-${side}.svg`,'utf8')
  if(side==='bottom') {
    const width=Number(svg.match(/<svg[^>]* width="([\d.]+)"/)[1])
    svg=svg.replace(/(<svg[^>]*>)/,`$1<g transform="translate(${width} 0) scale(-1 1)">`).replace('</svg>','</g></svg>')
    writeFileSync('dist/pill-tscircuit/pcb-bottom-view.svg',svg)
  }
  writeFileSync(`dist/pill-tscircuit/pcb-${side}.png`,new Resvg(svg,{fitTo:{mode:'width',value:1600}}).render().asPng())
}
