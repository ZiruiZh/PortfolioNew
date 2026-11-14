// Draws a portfolio case study inside this site's case window. The site's bundle calls
// window.zzCase(node, key) from a ref on the window's content slot, and zzCase(null) when it goes.
// First: decides lite mode before the site's own script builds the scene.
import './perf.js';
import css from './embed-css.js';
import { installCaseStudy } from './case-study.js';
import { setProjectMedia } from './projects.js';
import './z-clicks.js';
import './recruiter-prefetch.js';
import './favicon.js';
import './info-swipe.js';
import './case-pull.js';

const style = document.createElement('style');
style.dataset.zzCase = '';
style.textContent = css;
document.head.append(style);

// The renderer clones the site footer onto each study; this site keeps its own, so the clone is an empty, hidden stub.
const footer = document.createElement('footer');
footer.id = 'work-info';
footer.hidden = true;
footer.innerHTML = '<h2>Info</h2>';
document.body.append(footer);

const motionQuery = matchMedia('(prefers-reduced-motion: reduce)');
// The renderer draws a still case study (posters with play buttons, illustrations as plain pictures) when this
// matches: reduced motion, lite mode (work/perf.js), or a case study that has already loaded slowly this visit.
let slowCases = false;
const reducedQuery = {
  get matches() { return motionQuery.matches || !!window.zzLite || slowCases; },
  addEventListener: (...args) => motionQuery.addEventListener(...args),
  removeEventListener: (...args) => motionQuery.removeEventListener(...args),
};
const SLOW_CASE_MS = 2500;
let current = null, pending = 0;

// ---- what comes into view, loads and fades in -------------------------------------------------------------------------
// Everything below the first screenful of a case study starts faded, blurred and a little low, and clears into place as
// it scrolls into view (several arriving together come in a beat apart). Screen recordings' posters are loaded once
// they are within about 600px (pictures are lazy too, prepare.mjs). Reduced motion: everything simply shows.
const REVEAL = '.case-sections .case-section > *';
function reveal(scope, sheet) {
  const loadPosters = el => el.querySelectorAll('video[data-poster]').forEach(video => {
    video.poster = video.dataset.poster;
    delete video.dataset.poster;
  });
  const near = new IntersectionObserver(entries => entries.forEach(entry => {
    if (!entry.isIntersecting) return;
    loadPosters(entry.target);
    near.unobserve(entry.target);
  }), { root: sheet, rootMargin: '600px 0px' });
  const blocks = [...scope.querySelectorAll(REVEAL)];
  blocks.forEach(block => block.querySelector('video[data-poster]') && near.observe(block));
  if (motionQuery.matches) return () => near.disconnect();
  const fold = sheet.getBoundingClientRect().top + sheet.clientHeight * 0.92;
  const later = blocks.filter(block => block.getBoundingClientRect().top > fold);
  later.forEach(block => block.classList.add('zz-reveal'));
  const seen = new IntersectionObserver(entries => {
    let n = 0;
    for (const entry of entries) {
      if (!entry.isIntersecting) continue;
      const block = entry.target;
      block.style.setProperty('--zz-d', `${(n++ * 0.09).toFixed(2)}s`);
      block.classList.add('is-in');
      loadPosters(block);
      seen.unobserve(block);
      // Once in, it drops the effect (and the blur filter with it) so it draws as usual.
      setTimeout(() => block.classList.remove('zz-reveal', 'is-in'), 2200);
    }
  }, { root: sheet, rootMargin: '0px 0px -4% 0px', threshold: 0.05 });
  later.forEach(block => seen.observe(block));
  return () => { near.disconnect(); seen.disconnect(); };
}

function teardown() {
  if (!current) return;
  current.stopReveal?.();
  current.study.setMode('closed'); // pauses every video
  current.study.dispose();
  current.scope.remove();
  current = null;
}

function build(node, key) {
  setProjectMedia(key);
  const scope = document.createElement('div');
  scope.className = 'zz-case';
  // The renderer's own skeleton. Title and facts are drawn by the window itself, so theirs stay hidden.
  scope.innerHTML = `<div class="project-page" id="project">
      <nav class="case-rail" hidden><ol class="case-index" id="case-index"></ol></nav>
      <h1 id="project-title" hidden></h1><dl id="case-meta" hidden></dl>
      <p class="case-notice" id="case-notice" hidden></p>
      <figure class="case-hero" id="case-hero"></figure>
      <div class="case-sections" id="case-sections"></div>
    </div>`;
  node.replaceChildren(scope);
  // The opening video follows only the reader's reduced-motion setting: it autoplays even in lite mode.
  const study = installCaseStudy({ reducedQuery, heroQuery: motionQuery });
  study.render(key);
  study.setMode('project');
  current = { node, key, study, scope };
  const revealIn = node.closest('.cs-sheet');
  if (revealIn) current.stopReveal = reveal(scope, revealIn);
  // A case study scrolls inside its own frame (case-window.css): it opens at the top, and a wheel over the dark
  // margin around the frame still scrolls it.
  const sheet = node.closest('.cs-sheet');
  sheet?.scrollTo(0, 0);
  const margin = node.closest('.cs-scroll');
  if (margin && sheet && !margin.dataset.zzWheel) {
    margin.dataset.zzWheel = '1';
    margin.addEventListener('wheel', event => {
      if (event.target !== margin || event.defaultPrevented) return;
      event.preventDefault();
      sheet.scrollBy({ top: event.deltaY * (event.deltaMode === 1 ? 16 : 1), behavior: 'instant' });
    }, { passive: false });
  }
  // Still loading its opening picture or video after 2.5s: the videos further down hold on their posters (they can
  // still be played), and the rest of this visit's case studies open still. The opening video keeps playing.
  if (!reducedQuery.matches) setTimeout(() => {
    if (current?.scope !== scope) return;
    const hero = scope.querySelector('#case-hero video, #case-hero img');
    const ready = !hero || (hero.tagName === 'VIDEO' ? hero.readyState >= 3 : hero.complete && hero.naturalWidth > 0);
    if (ready) return;
    slowCases = true;
    scope.querySelectorAll('#case-sections video').forEach(video => { video.dataset.held = '1'; video.pause(); });
  }, SLOW_CASE_MS);
}

window.zzCase = (node, key) => {
  // React swaps ref callbacks on every render (null, then the same node); only a real change rebuilds.
  clearTimeout(pending);
  if (!node) { pending = setTimeout(teardown, 0); return; }
  if (current && current.node === node && current.key === key) return;
  teardown();
  build(node, key);
};
