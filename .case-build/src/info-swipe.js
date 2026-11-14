// On phones, the Info panels can be pulled away to show the Works view, with the feel of iOS scrolling:
//
// - Past the top of the panels, a pull down meets a rubber band that gives less the further it goes. At the
//   threshold the panels pop free and drop away. Past the bottom, a pull up does the same, and they rise away.
//   Short of the threshold they spring back.
// - A swipe left, anywhere on the panels, moves them one to one with the finger. Let go far enough, or with a
//   quick flick, and they slide off; otherwise they spring back.
//
// Then Works opens, exactly as its nav button does. Every motion carries the finger's speed, and a moving
// panel can be caught again mid-spring.
//
// On wider screens a sideways trackpad scroll over the panels does the same: the left column follows a scroll to
// the left and the right column a scroll to the right, the two moving apart one to one. Past 160px they slide
// off and Works opens; let go short of that and they spring back.

import { rubber, give, unrubber, spring, glide, tick } from './motion.js';

const phone = matchMedia('(max-width: 640px)');
const reduced = matchMedia('(prefers-reduced-motion: reduce)');

const SLOP = 8;          // px a finger moves before the drag picks a direction
const PULL = 64;         // px the panels travel, on screen, before a pull pops (about 140px of finger)
const span = () => Math.min(innerHeight * 0.4, 340);

const showWorks = () => document.querySelector('.c-nav [data-showcase="nav-works"]')?.click();

// ---- the panels' position ----------------------------------------------------------------------
let stack = null;
const pos = { x: 0, y: 0, scale: 1, alpha: 1 };
function draw() {
  const { x, y, scale, alpha } = pos;
  if (!x && !y && scale === 1 && alpha === 1) {
    stack.style.transform = stack.style.opacity = stack.style.transition = stack.style.willChange = '';
    return;
  }
  // The stack's own fade and slide transitions would trail the finger, so they wait until it is done.
  stack.style.transition = 'none';
  stack.style.willChange = 'transform, opacity';
  stack.style.transform = `translate3d(${x.toFixed(2)}px, ${y.toFixed(2)}px, 0) scale(${scale.toFixed(4)})`;
  stack.style.opacity = alpha.toFixed(3);
}
// While pulling up or down the panels sink back a touch, a hint that something gives at the end.
const setPull = y => { pos.y = y; pos.scale = 1 - 0.03 * Math.min(1, Math.abs(y) / PULL); };
const setSlide = x => { pos.x = x; pos.alpha = 1 - 0.25 * Math.min(1, Math.max(0, -x) / stack.clientWidth); };
const reset = () => { Object.assign(pos, { x: 0, y: 0, scale: 1, alpha: 1 }); draw(); };

let stop = null;   // cancels the running spring or glide
let busy = false;  // the panels are on their way out
const halt = () => { stop?.(); stop = null; };

// Back to rest, carrying the finger's speed.
function settle(axis, velocity) {
  halt();
  if (reduced.matches) { reset(); return; }
  if (axis === 'y') stop = spring(pos.y, 0, velocity, { k: 300, z: 1 }, y => { setPull(y); draw(); }, () => { stop = null; reset(); });
  else stop = spring(pos.x, 0, velocity, { k: 300, z: 0.9 }, x => { setSlide(x); draw(); }, () => { stop = null; reset(); });
}

// Off they go, and Works opens behind them.
function leave(axis, direction, velocity) {
  halt();
  busy = true;
  tick();
  showWorks();
  const done = () => { stop = null; busy = false; reset(); };
  if (reduced.matches) { done(); return; }
  if (axis === 'y') {
    const from = pos.y, far = innerHeight * 0.45;
    const v = direction * Math.max(Math.abs(velocity), 1100); // a pop: never slower than this
    stop = spring(from, direction * innerHeight, v, { k: 170, z: 1 }, y => {
      const gone = Math.min(1, Math.abs(y - from) / far);
      pos.y = y; pos.scale = 0.97 - 0.03 * gone; pos.alpha = 1 - gone;
      draw();
      return gone >= 1; // out of sight: done
    }, done);
  } else {
    const from = pos.x, width = stack.clientWidth, far = width * 0.6;
    const v = Math.min(velocity, -900);
    stop = spring(from, -width * 1.1, v, { k: 200, z: 1 }, x => {
      pos.x = x; pos.alpha = (1 - 0.25 * Math.min(1, -from / width)) * (1 - Math.min(1, (from - x) / far));
      draw();
      return pos.alpha <= 0;
    }, done);
  }
}

// ---- the gesture --------------------------------------------------------------------------------
let g = null;
let quietUntil = 0; // the click that may follow a drag is swallowed

const isOpen = () => !!stack?.closest('.cards.is-open:not(.case-open)');
// Leave alone anything inside that handles its own touches: a sideways scroller or a drawing pad.
function ownsTouch(target) {
  for (let el = target; el && el !== stack; el = el.parentElement) {
    const style = getComputedStyle(el);
    if (style.touchAction === 'none') return true;
    if (el.scrollWidth > el.clientWidth + 1 && /auto|scroll/.test(style.overflowX)) return true;
  }
  return false;
}
function velocity() {
  const s = g.samples, last = s[s.length - 1];
  if (performance.now() - last.t > 80) return { x: 0, y: 0 }; // the finger stopped before it lifted
  const first = s.find(p => last.t - p.t <= 100) ?? last;
  const dt = (last.t - first.t) / 1000;
  return dt > 0 ? { x: (last.x - first.x) / dt, y: (last.y - first.y) / dt } : { x: 0, y: 0 };
}
function sample(touch) {
  const now = performance.now();
  g.samples.push({ t: now, x: touch.clientX, y: touch.clientY });
  while (g.samples.length > 2 && now - g.samples[0].t > 120) g.samples.shift();
}

function onStart(event) {
  if (busy || !phone.matches || event.touches.length !== 1 || !isOpen() || ownsTouch(event.target)) {
    if (g && event.touches.length > 1) cancel();
    return;
  }
  const t = event.touches[0];
  const max = Math.max(0, stack.scrollHeight - stack.clientHeight);
  g = { x0: t.clientX, y0: t.clientY, max, mode: 'pending', locked: false, samples: [] };
  sample(t);
  // A panel still springing back is caught where it is and carries on with this finger.
  if (pos.x || pos.y) {
    halt();
    g.locked = true;
    if (pos.x) { g.mode = 'left'; g.x0 = t.clientX - pos.x; }
    else { g.mode = 'v'; g.s0 = pos.y > 0 ? -unrubber(pos.y, span()) : max + unrubber(-pos.y, span()); }
  } else {
    halt();
    g.top = stack.scrollTop <= 0;
    g.bottom = stack.scrollTop >= max - 1;
  }
}

function onMove(event) {
  if (!g || g.mode === 'native' || g.mode === 'gone') return;
  if (event.touches.length !== 1) { cancel(); return; }
  const t = event.touches[0];
  sample(t);
  let dx = t.clientX - g.x0, dy = t.clientY - g.y0;

  if (g.mode === 'pending') {
    // At an edge, a pull away from the content is taken from the very first move, before the browser bounces.
    if (g.top && dy > 0 && dy >= Math.abs(dx)) g.mode = 'v';
    else if (g.bottom && dy < 0 && -dy >= Math.abs(dx)) g.mode = 'v';
    else if (Math.hypot(dx, dy) < SLOP) return;
    else if (dx < 0 && -dx > Math.abs(dy)) g.mode = 'left';
    else { g.mode = 'native'; return; }
    if (!event.cancelable) { g.mode = 'native'; return; } // the browser is already scrolling
    g.s0 = stack.scrollTop;
    g.locked = g.mode === 'left';
  }
  if (event.cancelable) event.preventDefault();

  // A pull at the top that turns out to be a sideways swipe becomes one, as long as it is still short.
  if (g.mode === 'v' && !g.locked && Math.hypot(dx, dy) >= SLOP) {
    g.locked = true;
    if (dx < 0 && -dx > Math.abs(dy) * 1.2) { g.mode = 'left'; setPull(0); }
  }

  if (g.mode === 'left') {
    // One to one, leftward. Rightward there is nowhere to go, so it barely gives.
    setSlide(dx <= 0 ? dx : rubber(dx, stack.clientWidth * 0.25));
    draw();
    return;
  }

  // Vertical: the panels scroll as usual, and past either end they stretch on a rubber band.
  const at = g.s0 - dy;
  g.over = at < 0 ? at : at > g.max ? at - g.max : 0;
  if (at < 0) {
    setPull(rubber(-at, span()));
    if (pos.y >= PULL) { g.mode = 'gone'; leave('y', 1, velocity().y); return; }
  } else if (at > g.max) {
    setPull(-rubber(at - g.max, span()));
    if (-pos.y >= PULL) { g.mode = 'gone'; leave('y', -1, velocity().y); return; }
  } else {
    setPull(0);
    stack.scrollTop = at;
  }
  draw();
}

function onEnd(event) {
  if (!g || event.touches.length) return;
  const mode = g.mode;
  if (mode !== 'pending' && mode !== 'native') quietUntil = performance.now() + 400;
  if (mode === 'left') {
    const v = velocity().x;
    // Where the panels would coast to, the way iOS judges a flick.
    const projected = pos.x + v * 0.2;
    if (projected < -stack.clientWidth * 0.4) leave('x', -1, v);
    else settle('x', v);
  } else if (mode === 'v') {
    const v = velocity().y;
    // A stretched band lets go at its own, slower speed, not the finger's.
    if (pos.y) settle('y', v * give(g.over, span()));
    else if (Math.abs(v) > 60) stop = glide(stack, -v, () => { stop = null; });
  }
  g = null;
}

function cancel() {
  if (!g) return;
  if (g.mode === 'left') settle('x', 0);
  else if (g.mode === 'v' && pos.y) settle('y', 0);
  g = null;
}

function bind(el) {
  stack = el;
  el.addEventListener('touchstart', onStart, { passive: true });
  el.addEventListener('touchmove', onMove, { passive: false });
  el.addEventListener('touchend', onEnd);
  el.addEventListener('touchcancel', event => { onEnd(event); });
  el.addEventListener('click', event => {
    if (performance.now() < quietUntil) { event.preventDefault(); event.stopPropagation(); }
  }, true);
  // The blur along the column's top edge (case-window.css) shows once the panels have scrolled under it.
  const scrolled = () => el.classList.toggle('zz-scrolled', el.scrollTop > 2);
  el.addEventListener('scroll', scrolled, { passive: true });
  scrolled();
}

// ---- wider screens: a sideways scroll over the two columns ------------------------------------------
const APART = 160; // px the columns travel apart before they go
let columns = [], spread = 0, wheel = null, wheelStop = null;
function drawColumns(d, alpha = 1) {
  const [left, right] = columns;
  if (!left || !right) return;
  if (!d && alpha === 1) {
    for (const el of columns) el.style.transform = el.style.opacity = el.style.willChange = '';
    return;
  }
  left.style.transform = `translate3d(${(-d).toFixed(2)}px, 0, 0)`;
  right.style.transform = `translate3d(${d.toFixed(2)}px, 0, 0)`;
  for (const el of columns) { el.style.opacity = alpha.toFixed(3); el.style.willChange = 'transform, opacity'; }
}
const fadeFor = d => 1 - 0.25 * Math.min(1, Math.max(0, d) / 340);
function columnsSettle(velocity = 0) {
  wheelStop?.();
  if (reduced.matches) { spread = 0; drawColumns(0); return; }
  wheelStop = spring(spread, 0, velocity, { k: 300, z: 0.9 }, d => { spread = d; drawColumns(d, fadeFor(d)); }, () => { wheelStop = null; spread = 0; drawColumns(0); });
}
function columnsLeave() {
  wheelStop?.();
  busy = true;
  tick();
  showWorks();
  const done = () => { wheelStop = null; busy = false; spread = 0; drawColumns(0); };
  if (reduced.matches) { done(); return; }
  const from = spread, far = 360;
  wheelStop = spring(from, from + 520, 1400, { k: 200, z: 1 }, d => {
    spread = d;
    const alpha = fadeFor(from) * (1 - Math.min(1, (d - from) / far));
    drawColumns(d, alpha);
    return alpha <= 0;
  }, done);
}
function onWheel(event) {
  if (phone.matches || busy || !document.querySelector('.cards.is-open:not(.case-open)')) return;
  const unit = event.deltaMode === 1 ? 16 : event.deltaMode === 2 ? innerHeight : 1;
  const dx = event.deltaX * unit, dy = event.deltaY * unit;
  const side = event.currentTarget === columns[0] ? 1 : -1; // outward is left for the left column, right for the right
  const now = performance.now();
  // A gesture is a run of wheel events with no gap over 150ms; its first few pixels pick the axis.
  if (!wheel || now - wheel.last > 150) { wheelStop?.(); wheel = { axis: null, sum: 0, sx: 0, sy: 0, last: now, raw: spread }; }
  wheel.last = now;
  if (!wheel.axis) {
    wheel.sx += Math.abs(dx); wheel.sy += Math.abs(dy);
    if (wheel.sx + wheel.sy < 6) return;
    wheel.axis = wheel.sx > wheel.sy * 1.2 ? 'x' : 'y';
  }
  if (wheel.axis !== 'x') return;
  event.preventDefault(); // no browser back/forward swipe
  // Fingers moving left scroll content right (deltaX > 0): the columns move with the fingers.
  wheel.raw += side * dx;
  spread = wheel.raw >= 0 ? wheel.raw : -rubber(-wheel.raw, 120);
  drawColumns(spread, fadeFor(spread));
  if (spread >= APART) { wheel = null; columnsLeave(); return; }
  clearTimeout(wheel.timer);
  wheel.timer = setTimeout(() => { if (wheel && !busy) { wheel = null; columnsSettle(0); } }, 160);
}
function bindColumns() {
  const found = [document.querySelector('.cards .sg-col-l'), document.querySelector('.cards .sg-col-r')];
  if (!found[0] || !found[1] || (found[0] === columns[0] && found[1] === columns[1])) return;
  columns = found;
  for (const el of columns) el.addEventListener('wheel', onWheel, { passive: false });
}

// The panels' scroller is drawn by the site's own script; pick it up once it is there.
const find = () => {
  if (!columns[0]?.isConnected) bindColumns();
  if (stack?.isConnected) return;
  const el = document.querySelector('.cards .sg-stack');
  if (el) { halt(); busy = false; g = null; bind(el); }
};
find();
new MutationObserver(find).observe(document.documentElement, { childList: true, subtree: true });
