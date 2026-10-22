// Browser-local checklist only: no telemetry, accounts, seeds or card data.
document.addEventListener('alpine:init', () => {
  Alpine.data('taskProgress', (slug, total) => ({
    done: [],
    key: `shieldsigner-checklist-v1-${slug}`,
    init() {
      try {
        const saved = JSON.parse(localStorage.getItem(this.key) || '[]');
        this.done = Array.isArray(saved) ? saved.filter(n => Number.isInteger(n) && n >= 0 && n < total) : [];
      } catch { this.done = []; }
    },
    get count() { return new Set(this.done).size; },
    toggle(index) {
      this.done = this.done.includes(index) ? this.done.filter(n => n !== index) : [...this.done, index];
      this.save();
    },
    reset() { this.done = []; this.save(); },
    save() { try { localStorage.setItem(this.key, JSON.stringify(this.done)); } catch {} }
  }));
});
function showCopyButtons() {
  if (navigator.clipboard) document.querySelectorAll('.copy-command').forEach(button => button.hidden = false);
}
document.addEventListener('DOMContentLoaded', showCopyButtons);
document.addEventListener('click', async event => {
  const button = event.target.closest('.copy-command');
  if (!button) return;
  const block = button.closest('.command-block');
  const status = block.querySelector('.copy-feedback');
  try {
    await navigator.clipboard.writeText(block.querySelector('code').textContent);
    status.textContent = 'Copied';
    button.textContent = 'Copied';
  } catch { status.textContent = 'Copy unavailable. Select the command text below.'; }
});

// All requests are static files; filtering and quantity calculations stay local.
document.addEventListener('DOMContentLoaded', () => {
  const normalize = value => String(value).toLowerCase().replace(/[µμ]/g, 'u').replace(/ω/g, 'ohm').replace(/\s+/g, '');
  const partsForm = document.querySelector('.parts-form');
  if (partsForm) {
    const output = document.querySelector('#parts-results');
    function showParts(params, updateURL = false) {
      const variant = ['modular', 'standard'].includes(params.get('variant')) ? params.get('variant') : 'modular';
      const requestedScope = params.get('scope') || 'system';
      const scope = ['all', 'system', 'carrier'].includes(requestedScope) ? requestedScope : 'all';
      const query = (params.get('q') || '').trim().slice(0, 200);
      const rawQuantity = params.get('quantity') || '1';
      let quantity = /^\d+$/.test(rawQuantity) ? Number(rawQuantity) : 0;
      const invalid = !Number.isInteger(quantity) || quantity < 1 || quantity > 100;
      if (invalid) quantity = 1;
      partsForm.elements.variant.value = variant;
      partsForm.elements.scope.value = scope;
      partsForm.elements.q.value = query;
      partsForm.elements.quantity.value = quantity;
      output.replaceChildren(document.querySelector(`template[data-parts-variant="${variant}"]`).content.cloneNode(true));
      output.querySelector('.parts-result-summary strong').textContent = `${quantity} board${quantity === 1 ? '' : 's'}`;
      if (query) output.querySelector('.parts-result-summary > span').append(document.createTextNode(` · “${query}”`));
      if (invalid) {
        const error = document.createElement('p');
        error.className = 'task-notice'; error.setAttribute('role', 'alert');
        error.textContent = 'Choose 1–100 boards. Showing quantities for one board.';
        output.prepend(error);
      }
      const matches = {};
      for (const group of output.querySelectorAll('[data-part-group]')) {
        for (const item of group.querySelectorAll('[data-part]')) {
          if (!normalize(Object.values(JSON.parse(item.dataset.search)).join(' ')).includes(normalize(query))) item.remove();
          else item.querySelector('[data-total]').textContent = Number(item.dataset.qty) * quantity;
        }
        matches[group.dataset.partGroup] = group.querySelectorAll('[data-part]').length;
        group.querySelector('[data-group-count]').textContent = matches[group.dataset.partGroup];
      }
      for (const group of output.querySelectorAll('[data-part-group]')) {
        if (!matches[group.dataset.partGroup] || (scope !== 'all' && scope !== group.dataset.partGroup)) group.remove();
      }
      if (!output.querySelector('[data-part-group]')) {
        const message = document.createElement('p'); message.className = 'empty-state';
        message.textContent = 'No matching parts in this category.'; output.append(message);
        const other = scope === 'system' ? 'carrier' : 'system';
        if (scope !== 'all' && matches[other]) {
          const link = document.createElement('a');
          link.href = '/build/parts/?' + new URLSearchParams({variant, scope: other, q: query, quantity});
          link.textContent = `Show ${matches[other]} matching ${other} result${matches[other] === 1 ? '' : 's'} →`;
          output.append(link);
        }
      }
      if (updateURL) history.replaceState(null, '', '?' + new URLSearchParams({variant, scope, q: query, quantity}));
    }
    const update = () => showParts(new URLSearchParams(new FormData(partsForm)), true);
    partsForm.addEventListener('submit', event => { event.preventDefault(); update(); });
    partsForm.addEventListener('input', update);
    partsForm.addEventListener('change', update);
    window.addEventListener('popstate', () => showParts(new URLSearchParams(location.search)));
    showParts(new URLSearchParams(location.search));
  }
  const guideForm = document.querySelector('form.search');
  if (guideForm) {
    const input = guideForm.elements.q;
    input.value = new URLSearchParams(location.search).get('q') || '';
    const index = fetch('/static/guide-search.json').then(response => {
      if (!response.ok) throw new Error('Search index unavailable');
      return response.json();
    });
    async function search(updateURL = false) {
      try {
        const entries = await index;
        const query = input.value.trim().slice(0, 200).toLowerCase();
        let count = 0;
        for (const card of document.querySelectorAll('[data-guide]')) {
          card.hidden = !(entries[card.dataset.guide] || '').includes(query);
          if (!card.hidden) count++;
        }
        document.querySelector('[data-search-summary]').textContent = `${count} guide${count === 1 ? '' : 's'}${query ? ` matching “${input.value.trim()}”` : ''}`;
        document.querySelector('[data-search-empty]').hidden = count > 0;
        if (updateURL) history.replaceState(null, '', '?' + new URLSearchParams({q: input.value}));
      } catch {
        document.querySelector('[data-search-summary]').textContent = 'Search unavailable. Browse all guides below.';
      }
    }
    guideForm.addEventListener('submit', event => { event.preventDefault(); search(true); });
    input.addEventListener('input', () => search(true));
    window.addEventListener('popstate', () => { input.value = new URLSearchParams(location.search).get('q') || ''; search(); });
    search();
  }
  // Preserve existing query-string card bookmarks on the static card routes.
  if (location.pathname === '/build/cards/') {
    const card = new URLSearchParams(location.search).get('card');
    if (['seedkeeper', 'satochip', 'diy'].includes(card)) location.replace(`/build/cards/${card}/${location.hash}`);
  }
});
