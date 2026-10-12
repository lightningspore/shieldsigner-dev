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
document.addEventListener('htmx:afterSwap', showCopyButtons);
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
