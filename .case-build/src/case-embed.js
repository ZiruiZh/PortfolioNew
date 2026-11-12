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

function teardown() {
  if (!current) return;
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
  const study = installCaseStudy({ reducedQuery });
  study.render(key);
  study.setMode('project');
  current = { node, key, study, scope };
  // A case study scrolls inside its own frame (case-window.css): it opens at the top, and a wheel over the dark
  // margin around the frame still scrolls it.
  const sheet = node.closest('.cs-sheet');
  sheet?.scrollTo(0, 0);
  const margin = node.closest('.cs-scroll');
  if (margin && sheet && !margin.dataset.zzWheel) {
    margin.dataset.zzWheel = '1';
    margin.addEventListener('wheel', event => {
      if (event.target !== margin) return;
      event.preventDefault();
      sheet.scrollBy({ top: event.deltaY * (event.deltaMode === 1 ? 16 : 1), behavior: 'instant' });
    }, { passive: false });
  }
  // Still loading its opening picture or video after 2.5s: this one holds its videos on their posters (they can
  // still be played), and the rest of this visit's case studies open still.
  if (!reducedQuery.matches) setTimeout(() => {
    if (current?.scope !== scope) return;
    const hero = scope.querySelector('#case-hero video, #case-hero img');
    const ready = !hero || (hero.tagName === 'VIDEO' ? hero.readyState >= 3 : hero.complete && hero.naturalWidth > 0);
    if (ready) return;
    slowCases = true;
    scope.querySelectorAll('video').forEach(video => { video.dataset.held = '1'; video.pause(); });
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
