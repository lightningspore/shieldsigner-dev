import * as THREE from 'three'
import { OrbitControls } from 'three/addons/controls/OrbitControls.js'
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js'

function mount(root) {
  if (root.dataset.ready) return
  root.dataset.ready = 'true'
  const canvas = root.querySelector('canvas')
  const status = root.querySelector('[role="status"]')
  let renderer
  try { renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true }) }
  catch { root.dataset.failed='true'; status.textContent = '3D preview unavailable. Download the GLB model below.'; return }
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2))
  renderer.setClearColor(0xf1f0e9, 1)
  const scene = new THREE.Scene()
  const camera = new THREE.PerspectiveCamera(35, 1, 0.1, 5000)
  camera.up.set(0, 0, 1)
  const controls = new OrbitControls(camera, canvas)
  controls.enableDamping = true
  controls.listenToKeyEvents(canvas)
  const ambient = new THREE.HemisphereLight(0xffffff, 0x777777, 2.3)
  ambient.position.set(0, 0, 1); scene.add(ambient)
  for (const [position, intensity] of [[[100,-150,250],3], [[-150,100,80],1.5]]) {
    const light = new THREE.DirectionalLight(0xffffff, intensity)
    light.position.set(...position); scene.add(light)
  }
  const loader = new GLTFLoader()
  let model, size, sequence = 0
  function reset() {
    if (!model) return
    const bounds = new THREE.Box3().setFromObject(model)
    const centre = bounds.getCenter(new THREE.Vector3())
    size = bounds.getSize(new THREE.Vector3()).length()
    controls.target.copy(centre)
    const vertical = THREE.MathUtils.degToRad(camera.fov)
    const horizontal = 2*Math.atan(Math.tan(vertical/2)*camera.aspect)
    const distance = (size/2)/Math.sin(Math.min(vertical,horizontal)/2)*1.1
    camera.position.copy(centre).add(new THREE.Vector3(0.65,-0.95,0.9).normalize().multiplyScalar(distance))
    camera.near = size/1000; camera.far = size*15
    camera.updateProjectionMatrix(); controls.update()
  }
  async function load(mode) {
    const request = ++sequence
    status.textContent = 'Loading 3D assembly…'
    try {
      const gltf = await loader.loadAsync(root.dataset[mode])
      if (request !== sequence) return
      if (model) {
        scene.remove(model)
        model.traverse(o => { o.geometry?.dispose(); if (o.material) (Array.isArray(o.material)?o.material:[o.material]).forEach(m=>m.dispose()) })
      }
      model = gltf.scene; scene.add(model); reset()
      status.textContent = mode === 'exploded' ? 'Exploded assembly loaded. Drag to rotate; scroll to zoom.' : 'Assembled case loaded. Drag to rotate; scroll to zoom.'
      root.dataset.loaded = mode
      root.querySelectorAll('[data-mode]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.mode === mode)))
    } catch { root.dataset.failed='true'; status.textContent = 'Could not load the 3D preview. Download the GLB model below.' }
  }
  root.querySelectorAll('[data-mode]').forEach(button => button.addEventListener('click', () => load(button.dataset.mode)))
  root.querySelector('[data-reset]').addEventListener('click', reset)
  const observer = new ResizeObserver(() => {
    const width = canvas.clientWidth, height = canvas.clientHeight
    renderer.setSize(width, height, false); camera.aspect = width/height; camera.updateProjectionMatrix()
  })
  observer.observe(canvas)
  let frame
  function draw() { frame=requestAnimationFrame(draw); controls.update(); renderer.render(scene,camera) }
  draw(); load('assembled')
  root.cleanup = () => {
    ++sequence; cancelAnimationFrame(frame); observer.disconnect(); controls.dispose()
    model?.traverse(o => {
      o.geometry?.dispose()
      if (o.material) (Array.isArray(o.material)?o.material:[o.material]).forEach(m=>m.dispose())
    })
    renderer.dispose()
  }
}
function init() { document.querySelectorAll('[data-enclosure-viewer]').forEach(mount) }
// Ordinary document navigation owns the WebGL lifecycle.
init()
