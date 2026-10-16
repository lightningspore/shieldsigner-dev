(() => {
  let loading
  function load() {
    const viewer=document.querySelector('[data-enclosure-viewer]')
    if (viewer && !loading) loading=import(viewer.dataset.viewerScript).catch(() => {
      viewer.querySelector('[role="status"]').textContent='Preview unavailable. Download a GLB model below.'
      loading=null
    })
  }
  document.addEventListener('htmx:load',load)
  load()
})()
