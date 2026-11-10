(() => {
  const root = document.querySelector('#talk')
  if (!root) return
  const slides = [...root.querySelectorAll('.talk-slide')]
  const byId = id => root.querySelector(`#talk-${id}`)
  const index = byId('index'), previous = byId('prev'), next = byId('next')
  const start = byId('start'), exit = byId('exit'), notes = byId('notes')
  const fullscreen = byId('fullscreen'), position = byId('position')
  const presenting = () => document.body.classList.contains('talk-presenting')
  const fromHash = () => slides.findIndex(slide => `#${slide.id}` === location.hash)
  let current = Math.max(0, fromHash()), showNotes = false

  function update() {
    slides.forEach((slide, i) => {
      slide.hidden = presenting() && i !== current
      slide.classList.toggle('is-active', i === current)
      if (presenting()) slide.querySelector('.talk-notes').open = showNotes
    })
    index.value = slides[current].id
    position.textContent = `${current + 1} / ${slides.length}`
    previous.disabled = current === 0
    next.disabled = current === slides.length - 1
    start.hidden = presenting()
    exit.hidden = !presenting()
    notes.setAttribute('aria-pressed', String(showNotes))
    document.body.classList.toggle('talk-show-notes', showNotes)
    if (presenting()) slides.slice(current, current + 2).forEach(slide => {
      slide.querySelectorAll('img[loading="lazy"]').forEach(img => { img.loading = 'eager' })
    })
    root.dispatchEvent(new CustomEvent('talk:slidechange', { detail: { id: slides[current].id } }))
  }

  function go(value, { hash = true, focus = true, scroll = true } = {}) {
    current = Math.max(0, Math.min(slides.length - 1, value))
    update()
    if (hash && location.hash !== `#${slides[current].id}`) history.replaceState(null, '', `#${slides[current].id}`)
    if (presenting()) slides[current].scrollTop = 0
    else if (scroll) slides[current].scrollIntoView({ block: 'start' })
    if (focus) slides[current].querySelector('h1,h2,h3').focus({ preventScroll: true })
  }

  function enter() {
    document.body.classList.add('talk-presenting')
    go(current)
  }
  function leave() {
    if (document.fullscreenElement) document.exitFullscreen().catch(() => {})
    document.body.classList.remove('talk-presenting')
    update()
    slides[current].scrollIntoView({ block: 'start' })
    start.focus({ preventScroll: true })
  }
  function toggleNotes() {
    showNotes = !showNotes
    update()
    slides[current].querySelector('.talk-notes').open = showNotes
  }

  start.addEventListener('click', enter)
  exit.addEventListener('click', leave)
  previous.addEventListener('click', () => go(current - 1))
  next.addEventListener('click', () => go(current + 1))
  index.addEventListener('change', () => go(slides.findIndex(slide => slide.id === index.value)))
  notes.addEventListener('click', toggleNotes)
  fullscreen.addEventListener('click', async () => {
    if (!presenting()) enter()
    try {
      if (document.fullscreenElement) await document.exitFullscreen()
      else if (root.requestFullscreen) await root.requestFullscreen()
      else throw new Error('Fullscreen unsupported')
    } catch { byId('status').textContent = 'Fullscreen is unavailable here. Presentation mode and keyboard navigation still work.' }
  })
  document.addEventListener('fullscreenchange', () => {
    fullscreen.setAttribute('aria-pressed', String(Boolean(document.fullscreenElement)))
  })
  window.addEventListener('hashchange', () => {
    const selected = fromHash()
    if (selected >= 0) go(selected, { hash: false })
  })
  root.addEventListener('click', event => {
    const link = event.target.closest('a[href^="#"]')
    if (!link) return
    const target = slides.findIndex(slide => `#${slide.id}` === link.getAttribute('href'))
    if (target >= 0) { event.preventDefault(); go(target) }
  })
  document.addEventListener('keydown', event => {
    if (!presenting() || event.altKey || event.ctrlKey || event.metaKey ||
        event.target.closest('input,select,textarea,canvas,[contenteditable="true"],[data-enclosure-viewer]')) return
    const commands = { ArrowRight: () => go(current + 1), PageDown: () => go(current + 1),
      ArrowLeft: () => go(current - 1), PageUp: () => go(current - 1),
      Home: () => go(0), End: () => go(slides.length - 1),
      Escape: leave, n: toggleNotes, N: toggleNotes }
    if (commands[event.key]) { event.preventDefault(); commands[event.key]() }
  })

  root.querySelector('.talk-toolbar').hidden = false
  update()
  const observer = new IntersectionObserver(entries => {
    if (presenting()) return
    const visible = entries.filter(entry => entry.isIntersecting)
    if (!visible.length) return
    visible.sort((a, b) => b.intersectionRatio - a.intersectionRatio)
    const selected = slides.indexOf(visible[0].target)
    if (selected >= 0) { current = selected; update() }
  }, { threshold: [.25, .5, .75] })
  slides.forEach(slide => observer.observe(slide))
})()
