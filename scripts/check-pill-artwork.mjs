/** Independent raster comparison: tscircuit BRep silk vs KiCad's SVG plotter. */
import {Resvg} from '@resvg/resvg-js'
import {readFileSync,writeFileSync} from 'node:fs'
const ref=JSON.parse(readFileSync('src/generated/pill-board.json','utf8'))
const report={source:ref.source,renderWidth:3200,tolerancePixels:1,sides:{}}
for(const [side,layer]of [['top','F.SilkS'],['bottom','B.SilkS']]) {
  let native=readFileSync(`dist/pill-tscircuit/native-silk-${side}.svg`,'utf8')
  native=native.replace(/viewBox="[^"]+"/,`viewBox="${ref.origin.x-ref.width/2} ${ref.origin.y-ref.height/2} ${ref.width} ${ref.height}"`)
  native=native.replace(/width="[^"]+" height="[^"]+"/,`width="${ref.width}mm" height="${ref.height}mm"`)
  const port=readFileSync(`dist/pill-tscircuit/layers/${layer}.svg`,'utf8')
  const a=new Resvg(native,{fitTo:{mode:'width',value:report.renderWidth}}).render()
  const b=new Resvg(port,{fitTo:{mode:'width',value:report.renderWidth}}).render()
  if(a.width!==b.width||a.height!==b.height)throw new Error('Different image dimensions')
  const masks=[a.pixels,b.pixels].map(rgba=>{const out=new Uint8Array(a.width*a.height);for(let i=0;i<out.length;i++)out[i]=rgba[i*4+3]>127?1:0;return out})
  let pixels=[0,0],missing=[0,0]
  for(let which=0;which<2;which++)for(let y=0;y<a.height;y++)for(let x=0;x<a.width;x++) {
    const i=y*a.width+x
    if(!masks[which][i])continue
    pixels[which]++
    let covered=false
    for(let dy=-1;dy<=1&&!covered;dy++)for(let dx=-1;dx<=1;dx++)
      if(x+dx>=0&&x+dx<a.width&&y+dy>=0&&y+dy<a.height&&masks[1-which][(y+dy)*a.width+x+dx]){covered=true;break}
    if(!covered)missing[which]++
  }
  const unmatched=missing.map((n,i)=>n/pixels[i])
  report.sides[side]={nativePixels:pixels[0],portPixels:pixels[1],unmatchedNativeFraction:unmatched[0],unmatchedPortFraction:unmatched[1]}
  writeFileSync(`dist/pill-tscircuit/native-silk-${side}.png`,a.asPng())
  writeFileSync(`dist/pill-tscircuit/port-silk-${side}.png`,b.asPng())
  // Subpixel curve tessellation / stroke joins are allowed; lost artwork is not.
  if(unmatched.some(n=>n>.01))throw new Error(`${side} silkscreen differs from native: ${JSON.stringify(report.sides[side])}`)
}
writeFileSync('dist/pill-tscircuit/artwork-comparison.json',JSON.stringify(report,null,2)+'\n')
console.log(JSON.stringify(report,null,2))
