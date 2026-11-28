for (const root of document.querySelectorAll('[data-full-pinout]')) {
  const data=JSON.parse(root.querySelector('[data-full-pinout-json]').textContent)
  const picker=root.querySelector('[data-full-pick]')
  const selected=root.querySelector('[data-full-selection]')
  function pick(value) {
    const pin=data.pins.find(p=>p.pin===Number(value))
    picker.value=String(pin.pin)
    root.querySelectorAll('[data-full-pin]').forEach(row=>row.classList.toggle('selected',Number(row.dataset.fullPin)===pin.pin))
    selected.textContent=`Contact ${pin.pin} · ${pin.name} — ${pin.use}. Carrier net: ${pin.net.startsWith('unconnected-')?'unconnected':pin.net}.`
    selected.hidden=false
    root.dataset.selectedPin=String(pin.pin)
  }
  picker.disabled=false
  picker.addEventListener('change',()=>pick(picker.value))
  root.querySelectorAll('[data-full-pin]').forEach(link=>link.addEventListener('click',event=>{event.preventDefault();pick(link.dataset.fullPin)}))
  pick(1)
}
