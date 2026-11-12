// Shared motion for the site's drag gestures (info-swipe.js, case-pull.js): iOS's rubber band, a damped spring
// stepped every frame, iOS-style momentum, and a light haptic tick.

const RUBBER = 0.55; // UIScrollView's rubber-band constant

// UIScrollView's rubber band: a stretch follows at 0.55x at first, then less and less, never past s.
export const rubber = (d, s) => Math.sign(d) * (1 - 1 / ((Math.abs(d) * RUBBER) / s + 1)) * s;
// How fast the stretch moves for each px/s of finger at a pull of d: the band hands on less and less of it.
export const give = (d, s) => RUBBER / (((Math.abs(d) * RUBBER) / s + 1) ** 2);
// The input distance that gives a stretch of d (to pick something back up mid-spring).
export const unrubber = (d, s) => Math.sign(d) * Math.abs(d) / (RUBBER * (1 - Math.min(0.95, Math.abs(d) / s)));

// A damped spring (stiffness k, damping ratio z, unit mass), stepped every frame from the finger's velocity.
// onFrame can return true to end it early. Returns a function that stops it.
export function spring(from, to, velocity, { k = 320, z = 1 }, onFrame, onRest) {
  let x = from, v = velocity, last = performance.now(), id = 0;
  const c = 2 * z * Math.sqrt(k);
  const step = now => {
    const dt = Math.min(0.05, (now - last) / 1000);
    last = now;
    for (let n = Math.max(1, Math.ceil(dt / 0.004)), h = dt / n, i = 0; i < n; i++) {
      v += (-k * (x - to) - c * v) * h;
      x += v * h;
    }
    const done = Math.abs(x - to) < 0.5 && Math.abs(v) < 20;
    if (onFrame(done ? to : x) === true || done) onRest?.();
    else id = requestAnimationFrame(step);
  };
  id = requestAnimationFrame(step);
  return () => cancelAnimationFrame(id);
}

// iOS-style momentum (deceleration rate 0.998 per ms), for the rare drag this code scrolls itself.
export function glide(el, velocity, onRest) {
  let v = velocity, last = performance.now(), id = 0;
  const step = now => {
    const ms = Math.min(50, now - last);
    last = now;
    v *= Math.pow(0.998, ms);
    const before = el.scrollTop;
    el.scrollTop = before + (v * ms) / 1000;
    if (Math.abs(v) < 12 || el.scrollTop === before) onRest?.();
    else id = requestAnimationFrame(step);
  };
  id = requestAnimationFrame(step);
  return () => cancelAnimationFrame(id);
}

// A light tick as a pull pops: navigator.vibrate where there is one (Android). On iPhones, toggling a hidden
// switch control plays the system's selection tick (Safari 18 and later; earlier ones stay silent).
const apple = /iP(hone|ad|od)/.test(navigator.userAgent) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
export function tick() {
  try {
    // Chrome allows vibration only once the page has had a tap.
    if (navigator.vibrate) { if (navigator.userActivation?.hasBeenActive !== false) navigator.vibrate(8); return; }
    if (!apple) return;
    const label = document.createElement('label');
    label.setAttribute('aria-hidden', 'true');
    label.style.display = 'none';
    label.addEventListener('click', event => event.stopPropagation());
    const input = document.createElement('input');
    input.type = 'checkbox';
    input.setAttribute('switch', '');
    label.append(input);
    document.head.append(label);
    label.click();
    label.remove();
  } catch {}
}
