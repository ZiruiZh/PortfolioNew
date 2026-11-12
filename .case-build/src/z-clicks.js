// The two Z circles on the Info name card are buttons. Every press counts toward one total per circle,
// shared by every visitor on every device, kept by a free public counter service (abacus.jasoncameron.dev).
// Hovering a Z shows its total on the site's cursor label; on touch screens it floats above the circle.
//
// The service adds one per request and allows 30 requests per 10 seconds per visitor, so presses show
// at once and are sent in the background at a safe pace. Presses not yet sent when someone leaves are
// kept in their browser and sent on their next visit.

const API = 'https://abacus.jasoncameron.dev';
// ?zz-ns=<name> points the counters elsewhere, for trying things out without touching the real totals.
const NS = new URLSearchParams(location.search).get('zz-ns') || 'zz-lattice-q7k2m9';
const Z = {
  z1: { key: 'z-pink', name: 'Pink Z', color: '#f74fa8' },
  z2: { key: 'z-green', name: 'Green Z', color: '#4cd964' },
};
const IDS = Object.keys(Z);
const reduced = matchMedia('(prefers-reduced-motion: reduce)');
const finePointer = matchMedia('(pointer: fine)');

// ---- counts ------------------------------------------------------------------------------
const STASH = `zz-pending:${NS}`;
const store = {
  get() { try { return JSON.parse(localStorage.getItem(STASH)) || {}; } catch { return {}; } },
  set(value) { try { localStorage.setItem(STASH, JSON.stringify(value)); } catch {} },
};
const clean = n => Math.min(2000, Math.max(0, Math.floor(Number(n) || 0)));
const server = { z1: null, z2: null };   // the last total the service reported
const pending = { z1: 0, z2: 0 };        // presses in this tab not yet sent
// Claim presses an earlier visit left behind, so two open tabs never send the same ones.
function reclaim() {
  const left = store.get();
  IDS.forEach(id => { pending[id] += clean(left[id]); });
  store.set({});
}
function stash() {
  const left = store.get();
  store.set(Object.fromEntries(IDS.map(id => [id, clean(left[id]) + pending[id]])));
  IDS.forEach(id => { pending[id] = 0; });
}
reclaim();
addEventListener('pagehide', stash);
addEventListener('pageshow', event => { if (event.persisted) reclaim(); });

const total = id => (server[id] == null ? null : server[id] + pending[id]);
const words = n => (n == null ? 'counting…' : `${n.toLocaleString('en-US')} ${n === 1 ? 'click' : 'clicks'}`);

let pausedUntil = 0, lastFetch = 0;
async function call(path) {
  const response = await fetch(`${API}/${path}`, { cache: 'no-store' });
  if (response.status === 404) return { value: 0 }; // nobody has pressed it yet
  if (response.status === 429) { pausedUntil = Date.now() + 10000; throw new Error('slow down'); }
  if (!response.ok) throw new Error(String(response.status));
  return response.json();
}
async function refresh(force = false) {
  if (!force && Date.now() - lastFetch < 15000) return;
  lastFetch = Date.now();
  await Promise.all(IDS.map(async id => {
    try {
      const { value } = await call(`get/${encodeURIComponent(NS)}/${Z[id].key}`);
      server[id] = Math.max(server[id] ?? 0, Number(value) || 0);
    } catch {}
  }));
  render();
}
// One press goes out at a time, alternating between the circles, well inside the service's limit.
let turn = 0, sending = false;
setInterval(async () => {
  if (sending || Date.now() < pausedUntil || navigator.onLine === false) return;
  const waiting = IDS.filter(id => pending[id] > 0);
  if (!waiting.length) return;
  const id = waiting[turn++ % waiting.length];
  sending = true;
  try {
    const { value } = await call(`hit/${encodeURIComponent(NS)}/${Z[id].key}`);
    pending[id] = Math.max(0, pending[id] - 1);
    server[id] = Math.max(server[id] ?? 0, Number(value) || 0);
    render();
  } catch {
    pausedUntil = Math.max(pausedUntil, Date.now() + 4000);
  } finally {
    sending = false;
  }
}, 400);

// ---- labels ----------------------------------------------------------------------------------
let hovered = null;
const cursorLabel = detail => dispatchEvent(new CustomEvent('zc:work', { detail }));
function render() {
  document.querySelectorAll('[data-zz]').forEach(el => {
    const id = el.dataset.zz;
    el.setAttribute('aria-label', `${Z[id].name}, ${words(total(id))}`);
  });
  if (hovered) cursorLabel({ title: words(total(hovered.dataset.zz)), color: Z[hovered.dataset.zz].color });
}
document.addEventListener('pointerover', event => {
  if (event.pointerType && event.pointerType !== 'mouse' && event.pointerType !== 'pen') return;
  const el = event.target.closest?.('[data-zz]') ?? null;
  if (el === hovered) return;
  hovered = el;
  if (el) { render(); refresh(); } else cursorLabel(null);
});

// ---- the press: a gentle press-in and spring back, nothing more -----------------------------
const squished = new WeakMap();
function squish(el) {
  if (reduced.matches) return;
  squished.get(el)?.cancel();
  squished.set(el, el.animate([{ scale: 1 }, { scale: 0.92 }], { duration: 80, easing: 'ease-out', fill: 'forwards' }));
}
function release(el) { squished.get(el)?.cancel(); squished.delete(el); }
function pop(el) {
  if (reduced.matches) return;
  el.animate([{ scale: 0.92 }, { scale: 1.04, offset: 0.45 }, { scale: 1 }], { duration: 260, easing: 'cubic-bezier(.2,.8,.3,1)' });
}
const centre = el => { const r = el.getBoundingClientRect(); return { x: r.left + r.width / 2, y: r.top + r.height / 2, size: r.width }; };
const fx = (className, styles) => {
  const node = document.createElement('span');
  node.className = `zz-fx ${className}`;
  Object.assign(node.style, styles);
  document.body.append(node);
  return node;
};

// A note floats above a circle for a moment: its total after a tap on touch screens (there is no
// cursor there), or the news when it takes the lead.
let bubble = null, bubbleTimer = 0;
function showBubble(el, text, ms = 1300) {
  const { x, y, size } = centre(el);
  bubble ??= fx('zz-bubble', {});
  bubble.textContent = text;
  Object.assign(bubble.style, { left: `${x}px`, top: `${y - size / 2 - 14}px`, background: Z[el.dataset.zz].color });
  bubble.getAnimations().forEach(a => a.cancel());
  bubble.animate([{ opacity: 0, translate: '-50% -80%' }, { opacity: 1, translate: '-50% -100%' }], { duration: 160, fill: 'forwards', easing: 'ease-out' });
  clearTimeout(bubbleTimer);
  bubbleTimer = setTimeout(() => {
    bubble.animate([{ opacity: 1 }, { opacity: 0 }], { duration: 250, fill: 'forwards' }).onfinish = () => { bubble?.remove(); bubble = null; };
  }, ms);
}

// Who is ahead: 'z1', 'z2', 'tie', or null until both totals are known.
const leader = () => {
  if (server.z1 == null || server.z2 == null) return null;
  const gap = total('z1') - total('z2');
  return gap > 0 ? 'z1' : gap < 0 ? 'z2' : 'tie';
};
const COLOUR = { z1: 'pink', z2: 'green' };
const news = document.createElement('p');
news.setAttribute('aria-live', 'polite');
news.style.cssText = 'position:absolute;width:1px;height:1px;margin:-1px;padding:0;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap;border:0';
document.body.append(news);
let leadUntil = 0;

function press(el, touch) {
  const id = el.dataset.zz;
  const before = leader();
  pending[id] += 1;
  release(el);
  pop(el);
  if (touch) navigator.vibrate?.(8);
  // A press that puts this circle ahead says so; otherwise touch screens show the new total.
  if (before && before !== id && leader() === id) {
    const line = `and ${COLOUR[id]} takes the lead!`;
    leadUntil = performance.now() + 1800;
    showBubble(el, line, 1800);
    news.textContent = line;
  } else if (touch && performance.now() > leadUntil) {
    showBubble(el, words(total(id)));
  }
  render();
  if (server[id] == null) refresh(true);
}

document.addEventListener('pointerdown', event => {
  const el = event.target.closest?.('[data-zz]');
  if (el) squish(el);
});
// A press that turns into a swipe gets no click, so the circle lets go on its own shortly after the finger.
['pointerup', 'pointercancel'].forEach(type => document.addEventListener(type, () => {
  setTimeout(() => document.querySelectorAll('[data-zz]').forEach(release), type === 'pointerup' ? 100 : 0);
}));
document.addEventListener('click', event => {
  const el = event.target.closest?.('[data-zz]');
  if (!el) return;
  press(el, !finePointer.matches || event.pointerType === 'touch');
});
document.addEventListener('keydown', event => {
  const el = event.target.closest?.('[data-zz]');
  if (!el || (event.key !== 'Enter' && event.key !== ' ')) return;
  event.preventDefault();
  if (!event.repeat || event.key === 'Enter') press(el, false);
});

// The totals load shortly after the page settles, and again whenever someone hovers a Z.
setTimeout(() => refresh(true), 1500);
