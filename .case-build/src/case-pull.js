// A Works case study or a Playground pop-up can be pulled back down past its top, the way an iOS sheet is
// dismissed.
//
// - Touch: at the top of the study, a drag down takes hold of the whole window, which follows the finger one to
//   one while the dimmed backdrop clears. Let go far enough down, or with a flick, and it carries on down and
//   closes; otherwise it springs back up. Dragging back above where it started scrolls the study again, and a
//   window still springing back can be caught mid-way.
// - Wheel or trackpad: at the top, a scroll up stretches the window down on a rubber band that gives less and
//   less. At 80px it pops and closes; stop short and it springs back. Only a scroll that starts at the top pulls:
//   a fling that reaches the top on its own momentum just stops there, as before. A mouse wheel takes two quick
//   notches to close it.
//
// Closing is the window's own Close button, so the 3D view flies back exactly as it does from there; the window
// keeps its downward speed on the way out.

import { rubber, unrubber, spring, glide, tick } from './motion.js';

const reduced = matchMedia('(prefers-reduced-motion: reduce)');
const SLOP = 8;   // px a finger moves before the drag picks a direction
const POP = 80;   // px the window travels on the wheel's rubber band before it pops (about 195px of scrolling)
const span = () => Math.min(innerHeight * 0.4, 340);

// Leave alone anything inside that handles its own touches: a sideways scroller or a drawing pad.
function ownsTouch(target, sheet) {
  for (let el = target; el && el !== sheet; el = el.parentElement) {
    const style = getComputedStyle(el);
    if (style.touchAction === 'none') return true;
    if (el.scrollWidth > el.clientWidth + 1 && /auto|scroll/.test(style.overflowX)) return true;
  }
  return false;
}

export function bindPull(sheet, margin) {
  if (!sheet || !margin || sheet.dataset.zzPull) return;
  sheet.dataset.zzPull = '1';
  // A case study scrolls inside its window (case-window.css); a Playground pop-up scrolls on its backdrop.
  const scroller = sheet.classList.contains('cs-case') ? sheet : margin;

  let y = 0;            // how far down the window sits
  let stop = null;      // cancels the running spring or glide
  let closing = false;
  let backdrop = null;  // the margin's own dim colour, [r, g, b, a]
  const halt = () => { stop?.(); stop = null; };

  function draw() {
    if (y <= 0) {
      sheet.style.translate = sheet.style.willChange = margin.style.backgroundColor = '';
      return;
    }
    if (!backdrop) backdrop = (getComputedStyle(margin).backgroundColor.match(/[\d.]+/g) || [0, 0, 0, 0.5]).map(Number);
    const [r, g, b, a = 1] = backdrop;
    sheet.style.translate = `0 ${y.toFixed(2)}px`;
    sheet.style.willChange = 'translate';
    // The backdrop clears as the window goes down, to 40% of its dim halfway down the screen.
    margin.style.backgroundColor = `rgba(${r},${g},${b},${(a * (1 - 0.6 * Math.min(1, y / (innerHeight * 0.5)))).toFixed(3)})`;
  }

  function settle(velocity) {
    halt();
    if (reduced.matches) { y = 0; draw(); return; }
    stop = spring(y, 0, velocity, { k: 300, z: 1 }, v => { y = v; draw(); }, () => { stop = null; y = 0; draw(); });
  }

  function close(velocity) {
    halt();
    closing = true;
    sheet.querySelector('.cs-x')?.click();
    // Should the window somehow still be here once a close would be over, it comes back to rest.
    setTimeout(() => { halt(); closing = false; y = 0; draw(); }, 1500);
    if (reduced.matches) return;
    const to = innerHeight;
    stop = spring(y, to, Math.max(velocity, 1400), { k: 170, z: 1 }, v => {
      y = v;
      draw();
      return !sheet.isConnected || y >= to - 1;
    }, () => { stop = null; });
  }

  // ---- wheel and trackpad ----------------------------------------------------------------------
  // A gesture is a run of wheel events with no gap over 150ms.
  let wheel = null, idle = 0;
  function onWheel(event) {
    if (!sheet.isConnected) return;
    if (closing) { if (event.cancelable) event.preventDefault(); return; }
    if (event.ctrlKey) return; // a pinch
    const unit = event.deltaMode === 1 ? 16 : event.deltaMode === 2 ? innerHeight : 1;
    const dx = event.deltaX * unit, dy = event.deltaY * unit;
    const now = performance.now();
    if (!wheel || now - wheel.last > 150) {
      // A window still springing back is caught where it is.
      if (y) halt();
      wheel = { top: scroller.scrollTop <= 0, last: now, raw: y ? unrubber(y, span()) : 0 };
    }
    wheel.last = now;
    if (!y) {
      if (scroller.scrollTop > 0) { wheel.top = false; return; }
      if (!wheel.top || dy >= 0 || Math.abs(dx) > Math.abs(dy) || !event.cancelable) return;
    }
    event.preventDefault();
    // A mouse wheel's notch can be 300px in one go; no single notch pulls more than 120, so it takes two to close.
    wheel.raw = Math.max(0, wheel.raw - Math.max(dy, -120));
    y = rubber(wheel.raw, span());
    draw();
    clearTimeout(idle);
    if (y >= POP) { wheel = null; tick(); close(900); return; }
    idle = setTimeout(() => { if (!closing && y) { wheel = null; settle(0); } }, 160);
  }
  // On the margin, so a scroll over the dark edge around the window pulls too; it runs before the margin's own
  // wheel handler (case-embed.js), which leaves alone what this one takes.
  margin.addEventListener('wheel', onWheel, { passive: false, capture: true });

  // ---- touch -----------------------------------------------------------------------------------
  let g = null, quietUntil = 0;
  function sample(touch) {
    const now = performance.now();
    g.samples.push({ t: now, y: touch.clientY });
    while (g.samples.length > 2 && now - g.samples[0].t > 120) g.samples.shift();
  }
  function velocity() {
    const s = g.samples, last = s[s.length - 1];
    if (performance.now() - last.t > 80) return 0; // the finger stopped before it lifted
    const first = s.find(p => last.t - p.t <= 100) ?? last;
    const dt = (last.t - first.t) / 1000;
    return dt > 0 ? (last.y - first.y) / dt : 0;
  }
  function onStart(event) {
    if (closing || event.touches.length !== 1 || ownsTouch(event.target, sheet)) {
      if (g && event.touches.length > 1) cancel();
      return;
    }
    const t = event.touches[0];
    halt();
    g = { x0: t.clientX, y0: t.clientY, mode: 'pending', samples: [], far: 0 };
    sample(t);
    if (y) { g.mode = 'pull'; g.y0 = t.clientY - y; } // caught mid-spring
    else g.top = scroller.scrollTop <= 0;
  }
  function onMove(event) {
    if (!g || g.mode === 'native') return;
    if (event.touches.length !== 1) { cancel(); return; }
    const t = event.touches[0];
    sample(t);
    const dx = t.clientX - g.x0, dy = t.clientY - g.y0;
    if (g.mode === 'pending') {
      // At the top, a drag down is taken from the very first move, before the browser bounces.
      if (g.top && dy > 0 && dy >= Math.abs(dx)) g.mode = 'pull';
      else if (Math.hypot(dx, dy) < SLOP) return;
      else { g.mode = 'native'; return; }
      if (!event.cancelable) { g.mode = 'native'; return; } // the browser is already scrolling
    }
    if (event.cancelable) event.preventDefault();
    g.far = Math.max(g.far, Math.abs(dy));
    if (dy >= 0) { y = dy; scroller.scrollTop = 0; }       // the window follows the finger one to one
    else { y = 0; scroller.scrollTop = -dy; g.scrolled = true; } // above where it started, the study scrolls
    draw();
  }
  function onEnd(event) {
    if (!g || event.touches.length) return;
    if (g.mode === 'pull') {
      if (g.far > SLOP) quietUntil = performance.now() + 400;
      const v = velocity();
      if (y > 0) {
        // Where the window would coast to, the way iOS judges a flick.
        if (y + v * 0.2 > Math.min(sheet.clientHeight * 0.3, 220) && v > -300) close(v);
        else settle(v);
      } else if (g.scrolled && Math.abs(v) > 60) {
        stop = glide(scroller, -v, () => { stop = null; });
      }
    }
    g = null;
  }
  function cancel() {
    if (g?.mode === 'pull' && y) settle(0);
    g = null;
  }
  sheet.addEventListener('touchstart', onStart, { passive: true });
  sheet.addEventListener('touchmove', onMove, { passive: false });
  sheet.addEventListener('touchend', onEnd);
  sheet.addEventListener('touchcancel', onEnd);
  // The tap a drag may leave behind is swallowed; the Close this code presses itself (untrusted) goes through.
  sheet.addEventListener('click', event => {
    if (event.isTrusted && performance.now() < quietUntil) { event.preventDefault(); event.stopPropagation(); }
  }, true);
}

// Every window gets it as it opens: Works case studies and Playground pop-ups alike.
const find = () => {
  for (const sheet of document.querySelectorAll('.cs-scroll > .cs-sheet:not([data-zz-pull])')) bindPull(sheet, sheet.parentElement);
};
find();
new MutationObserver(find).observe(document.documentElement, { childList: true, subtree: true });
