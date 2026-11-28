import { Resvg } from '@resvg/resvg-js'
import { readFileSync, writeFileSync } from 'node:fs'
for (const name of ['gerber-top','gerber-bottom','header-assembly','panel-proposal']) {
 const path=`variants/full-size-pico/manufacturing/${name}`
 writeFileSync(`${path}.png`,new Resvg(readFileSync(`${path}.svg`),{fitTo:{mode:'width',value:1800}}).render().asPng())
}
console.log('Rendered the actual Gerbers, header placement and separate panel proposal.')
