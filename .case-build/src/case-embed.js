// Draws a portfolio case study inside this site's case window. The site's bundle calls
// window.zzCase(node, key) from a ref on the window's content slot, and zzCase(null) when it goes.
import css from './embed-css.js';
import { installCaseStudy } from './case-study.js';
import { setProjectMedia } from './projects.js';
import './z-clicks.js';
import './recruiter-prefetch.js';

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

const reducedQuery = matchMedia('(prefers-reduced-motion: reduce)');
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
}

window.zzCase = (node, key) => {
  // React swaps ref callbacks on every render (null, then the same node); only a real change rebuilds.
  clearTimeout(pending);
  if (!node) { pending = setTimeout(teardown, 0); return; }
  if (current && current.node === node && current.key === key) return;
  teardown();
  build(node, key);
};
