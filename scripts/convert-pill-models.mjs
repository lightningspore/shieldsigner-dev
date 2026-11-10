/** Convert the native GLB assembly into portable, per-reference model assets.
 * Native transforms are baked into each mesh; exported GLBs use metres, Z up.
 */
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs'
import {createHash} from 'node:crypto'
import {Box3,Group,Matrix4,Vector3} from 'three'
import {GLTFLoader} from 'three/examples/jsm/loaders/GLTFLoader.js'
import {GLTFExporter} from 'three/examples/jsm/exporters/GLTFExporter.js'
// GLTFExporter only needs the asynchronous Blob reads in this headless pipeline.
globalThis.FileReader = class {
  readAsArrayBuffer(blob) {blob.arrayBuffer().then(value=>{this.result=value;this.onloadend?.()})}
  readAsDataURL(blob) {blob.arrayBuffer().then(value=>{this.result=`data:${blob.type};base64,${Buffer.from(value).toString('base64')}`;this.onloadend?.()})}
}
const reference = JSON.parse(readFileSync('src/generated/pill-board.json','utf8'))
const details = JSON.parse(readFileSync('src/generated/pill-details.json','utf8'))
const bytes=readFileSync('dist/pill-tscircuit/components-native.glb')
const gltf=await new GLTFLoader().parseAsync(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),'')
gltf.scene.updateMatrixWorld(true)
const groups=new Map()
const names=new Set(reference.components.map(p=>p.name))
// KiCad GLB: metres, +Y vertical, +Z toward the bottom of the PCB.
// KiCad's board runs from -0.005 to 1.595 mm; tscircuit centres it at Z=0.
const world=new Matrix4().set(1,0,0,0, 0,0,-1,0, 0,1,0,-(details.thickness/2-.005)/1000, 0,0,0,1)
gltf.scene.traverse(mesh=>{
  if(!mesh.isMesh)return
  let owner=mesh
  while(owner&&!names.has(owner.name.replace(/_\d+$/,'')))owner=owner.parent
  if(!owner)throw new Error(`Unowned native mesh: ${mesh.name}`)
  const part=reference.components.find(p=>p.name===owner.name.replace(/_\d+$/,''))
  const geometry=mesh.geometry.clone()
  geometry.applyMatrix4(mesh.matrixWorld).applyMatrix4(world)
  geometry.translate(-part.x/1000,-part.y/1000,-(part.layer==='bottom'?-details.thickness/2:details.thickness/2)/1000)
  const copy=mesh.clone(false);copy.geometry=geometry;copy.matrixAutoUpdate=true
  copy.position.set(0,0,0);copy.quaternion.identity();copy.scale.set(1,1,1);copy.updateMatrix()
  if(!groups.has(part.name))groups.set(part.name,new Group())
  groups.get(part.name).add(copy)
})
mkdirSync('dist/pill-tscircuit/models',{recursive:true})
const assets=[]
for(const [name,group]of groups){
  const part=reference.components.find(p=>p.name===name)
  const box=new Box3().setFromObject(group)
  const size=box.getSize(new Vector3()).multiplyScalar(1000)
  const output=Buffer.from(await new GLTFExporter().parseAsync(group,{binary:true,onlyVisible:false}))
  const path=`models/${name}.glb`
  writeFileSync(`dist/pill-tscircuit/${path}`,output)
  assets.push({reference:name,path,sha256:createHash('sha256').update(output).digest('hex'),
    sourceSha256:reference.source.sha256,position:{x:part.x,y:part.y,z:part.layer==='bottom'?-details.thickness/2:details.thickness/2},
    size:{x:size.x,y:size.y,z:size.z},
    bounds:{min:box.min.clone().multiplyScalar(1000),max:box.max.clone().multiplyScalar(1000)},
    url:`data:model/gltf-binary;base64,${output.toString('base64')}`})
}
const expected=new Set(details.models.filter(m=>m.show).map(m=>m.reference))
if(assets.length!==expected.size||assets.some(a=>!expected.has(a.reference)))throw new Error('Native model coverage mismatch')
writeFileSync('dist/pill-tscircuit/models.json',JSON.stringify({source:reference.source,modelSources:details.models,converterSha256:createHash('sha256').update(readFileSync('scripts/convert-pill-models.mjs')).digest('hex'),assets},null,2)+'\n')
console.log(`Converted ${assets.length} component assemblies from ${details.models.filter(m=>m.show).length} native model instances.`)
