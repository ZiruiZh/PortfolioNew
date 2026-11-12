// Decides whether this device gets the full 3D scene or a lighter one ("lite"), and drives the loading screen.
//
// Lite is chosen up front when the address asks for it (?lite=1; ?lite=0 forces the full scene), when an earlier
// visit measured this device as slow (remembered for a week), when the browser asks to save data, or when the
// device reports 2 GB of memory or 2 cores or fewer. Otherwise the scene is timed behind the loading screen, and
// again for its first 20 seconds on screen; a device that can't hold about 40 frames a second switches to lite.
//
// Lite (zzScene.zzLighten, in the bundle) draws at 1x with no glitch pass, keeps 2 in 5 of the floating pixel
// loops and a sparser lattice, idles at half rate, and leaves the Works card video still. Here, on Info, the live
// scene is swapped for a saved loop of it (bg/info-*.mp4): nothing behind the panels is drawn or interactive.
// This module runs before the site's own script, so the scene is built light from the start when it can be.

const params = new URLSearchParams(location.search);
const KEY = 'zz-perf';
const WEEK = 7 * 864e5;
const store = {
  get() { try { return JSON.parse(localStorage.getItem(KEY)); } catch { return null; } },
  set(v) { try { localStorage.setItem(KEY, JSON.stringify(v)); } catch {} },
  clear() { try { localStorage.removeItem(KEY); } catch {} },
};

function upfront() {
  if (params.get('lite') === '1') return 'asked';
  if (params.get('lite') === '0') { store.clear(); return 'full'; }
  const saved = store.get();
  if (saved?.lite && Date.now() - saved.at < WEEK) return 'remembered';
  if (navigator.connection?.saveData) return 'save-data';
  if (navigator.deviceMemory && navigator.deviceMemory <= 2) return 'low-memory';
  if (navigator.hardwareConcurrency && navigator.hardwareConcurrency <= 2) return 'few-cores';
  return null;
}

const reason = upfront();
const forcedFull = reason === 'full';
window.zzLite = !!reason && !forcedFull;
window.zzLiteReason = window.zzLite ? reason : null;
document.documentElement.dataset.perf = window.zzLite ? 'lite' : 'full';

function goLite(why) {
  if (window.zzLite && window.zzScene?.zzLit) return;
  window.zzLite = true;
  window.zzLiteReason = why;
  document.documentElement.dataset.perf = 'lite';
  if (why === 'slow' || why === 'slow-later' || why === 'software') store.set({ lite: true, at: Date.now(), why });
  window.zzScene?.zzLighten?.();
  infoVideo.sync();
}
window.zzGoLite = goLite;

// ---- timing --------------------------------------------------------------------------------------
const frame = () => new Promise(resolve => requestAnimationFrame(resolve));
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
// The average gap between frames over `ms`, or null if the page was hidden (no frames to judge by).
async function frameGap(ms) {
  const gaps = [];
  let last = performance.now();
  const end = last + ms;
  const done = sleep(ms + 400).then(() => 'late');
  while (performance.now() < end) {
    if (await Promise.race([frame().then(() => 'frame'), done]) === 'late' || document.hidden) return null;
    const now = performance.now();
    gaps.push(Math.min(100, now - last));
    last = now;
  }
  gaps.splice(0, 3); // the first few carry whatever happened before
  return gaps.length > 10 ? gaps.reduce((a, b) => a + b, 0) / gaps.length : null;
}
const SLOW_GAP = 24;       // ms: below about 42 frames a second
const SLOW_LATER_GAP = 28; // a little more lenient once the page is in use

const caseOpen = () => !!document.querySelector('.case.is-open');
async function boot() {
  const loader = window.zzLoader;
  const t0 = performance.now();
  loader?.set(6);
  while (!window.zzScene && !document.querySelector('.fail') && performance.now() - t0 < 10000) await sleep(50);
  const S = window.zzScene;
  if (!S) { loader?.done(); return; }
  if (S.soft && !forcedFull) goLite('software');
  // Progress: how many works have their picture on the lattice.
  while (performance.now() - t0 < 8000) {
    const all = S.nodes.length || 1;
    const got = S.nodes.filter(n => n.sprite.material.map).length;
    loader?.set(12 + (got / all) * 70);
    if (got / all >= 0.9) break;
    await sleep(80);
  }
  if (!window.zzLite && !forcedFull) {
    loader?.set(88);
    const gap = await frameGap(900);
    if (gap && gap > SLOW_GAP) goLite('slow');
  }
  loader?.done();
  infoVideo.sync();
  // Keep an eye on it while it settles in: two slow stretches in a row and it lightens.
  if (forcedFull) return;
  let strikes = 0;
  for (const until = performance.now() + 20000; performance.now() < until && !window.zzLite;) {
    await sleep(1500);
    if (document.hidden || caseOpen()) { strikes = 0; continue; }
    const gap = await frameGap(1500);
    strikes = gap && gap > SLOW_LATER_GAP ? strikes + 1 : 0;
    if (strikes >= 2) goLite('slow-later');
  }
}

// ---- Info's background in lite: a saved loop instead of the live scene ------------------------
const infoVideo = (() => {
  let video = null, timer = 0, on = false, failed = false;
  const tall = () => innerWidth / innerHeight < 0.8;
  function make(S) {
    const name = tall() ? 'info-tall' : 'info-wide';
    video = document.createElement('video');
    video.className = 'zz-bgvid';
    video.muted = video.loop = video.playsInline = true;
    video.setAttribute('muted', ''); video.setAttribute('playsinline', ''); video.setAttribute('aria-hidden', 'true');
    video.preload = 'auto';
    video.poster = `./bg/${name}.jpg`;
    video.src = `./bg/${name}.mp4`;
    video.addEventListener('error', () => { failed = true; hide(); });
    S.el.append(video);
  }
  function show(S) {
    if (on || failed) return;
    if (!video) make(S);
    on = true;
    video.play().catch(() => {});
    video.classList.add('is-on');
    // Once the loop has faded in over the live frame, the scene stops drawing (its clock held).
    setTimeout(() => { if (on) S.zzHold = true; }, 650);
  }
  function hide() {
    const S = window.zzScene;
    if (S) S.zzHold = false;
    if (!on) return;
    on = false;
    video?.classList.remove('is-on');
    setTimeout(() => { if (!on) video?.pause(); }, 700);
  }
  function check() {
    const S = window.zzScene;
    const info = !!document.querySelector('.cards.is-open');
    if (!S || !window.zzLite || !info || document.hidden) { hide(); return; }
    // Wait for the works to arrive and settle into their cloud before swapping the live view for the loop.
    if (S.cloud.v > 0.98 && !S.flying && (S.zzIn ?? 1) > 0.999) show(S);
  }
  return {
    sync() {
      if (!window.zzLite) return;
      clearInterval(timer);
      timer = setInterval(check, 200);
      check();
    },
  };
})();

boot();
