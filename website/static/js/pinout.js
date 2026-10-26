for (const root of document.querySelectorAll('[data-pinout-tool]')) {
  const data = JSON.parse(root.querySelector('[data-pinout-json]').textContent)
  const revision = root.querySelector('[data-pinout-revision]')
  const picker = root.querySelector('[data-pinout-pick]')
  const selected = root.querySelector('[data-pinout-selection]')
  root.querySelectorAll('select,button').forEach(el => el.disabled = false)
  function pick(value) {
    const pin = data.pins.find(pin => pin.pin === Number(value))
    picker.value = String(pin.pin)
    root.querySelectorAll('.row').forEach(row => row.classList.toggle('selected', Number(row.dataset.pin) === pin.pin))
    root.querySelector('[data-selected-title]').textContent = `Pin ${pin.pin} · ${pin.name} · ${pin.volts} V`
    root.querySelector('[data-selected-use]').textContent = `${pin.use[revision.value]}. ${pin.note[revision.value]}`
    root.querySelector('[data-selected-functions]').textContent = pin.functions.includes('GPIO') ? ['GPIO',...pin.alternatives.map(a=>a.label)].join(' · ') : pin.name
    root.querySelector('[data-selected-gpio]').textContent = pin.bank === null ? 'Power / ground pin; no GPIO address.' : `Bank ${pin.bank}, line ${pin.offset}; legacy global GPIO ${pin.legacyGpio}. Verify /dev/gpiochip identity on the running image.`
    root.querySelector('[data-selected-net]').textContent = pin.net[revision.value]
    selected.hidden = false
    root.dataset.selectedPin = String(pin.pin)
  }
  revision.addEventListener('change', () => {
    for (const pin of data.pins) {
      root.querySelector(`[data-pin-use="${pin.pin}"]`).textContent = pin.use[revision.value]
      root.querySelector(`[data-table-use="${pin.pin}"]`).textContent = pin.use[revision.value]
      root.querySelector(`[data-table-note="${pin.pin}"]`).textContent = pin.note[revision.value]
      root.querySelector(`[data-table-net="${pin.pin}"]`).textContent = pin.net[revision.value]
      root.querySelector(`[data-pin="${pin.pin}"]`).setAttribute('aria-label',`Pin ${pin.pin}: ${pin.name}; ${pin.volts} V; ${pin.use[revision.value]}`)
    }
    root.querySelector('[data-diagram-revision]').textContent = revision.value === 'released' ? 'ShieldSigner 0.0.7 · released' : 'ShieldSigner 0.0.8 · PWM candidate'
    root.querySelector('svg title').textContent = `Luckfox Mini A/B pinout · ${root.querySelector('[data-diagram-revision]').textContent}`
    pick(picker.value)
  })
  picker.addEventListener('change',()=>pick(picker.value))
  root.querySelectorAll('[data-pin]').forEach(link=>link.addEventListener('click',event=>{event.preventDefault();pick(link.dataset.pin)}))
  root.querySelectorAll('[data-pinout-filter]').forEach(button=>button.addEventListener('click',()=>{
    const kind=button.dataset.pinoutFilter
    root.querySelectorAll('[data-pin]').forEach(row=>row.classList.toggle('dimmed',kind!=='ALL' && !row.dataset.functions.split(' ').includes(kind)))
    root.querySelectorAll('[data-pinout-filter]').forEach(b=>b.setAttribute('aria-pressed',String(b===button)))
  }))
  pick(14)
}
