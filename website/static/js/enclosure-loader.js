(() => {
  let loading
  function load() {
    const viewer=document.querySelector('[data-enclosure-viewer]')
    if (viewer && !loading) loading=import(viewer.dataset.viewerScript).catch(() => {
      viewer.querySelector('[role="status"]').textContent='Preview unavailable. Download a GLB model below.'
      loading=null
    })
  }
  const deferred=document.querySelector('[data-enclosure-viewer][data-defer-viewer]')
  if (deferred && 'IntersectionObserver' in window) {
    const observer=new IntersectionObserver(entries => {
      if (entries.some(entry => entry.isIntersecting)) { load(); observer.disconnect() }
    }, { rootMargin:'100px' })
    observer.observe(deferred)
  } else load()
})()
