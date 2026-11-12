// Pointing at "Recruiter mode" starts fetching the portfolio (its page, scripts and styles),
// so the switch is quick when the click lands.
let started = false;
function warm() {
  if (started) return;
  started = true;
  const base = new URL('recruiter/', document.baseURI);
  const hint = href => {
    const link = document.createElement('link');
    link.rel = 'prefetch';
    link.href = href;
    document.head.append(link);
  };
  fetch(base).then(response => response.text()).then(html => {
    const doc = new DOMParser().parseFromString(html, 'text/html');
    doc.querySelectorAll('script[src], link[rel=stylesheet][href], link[rel=modulepreload][href]')
      .forEach(node => hint(new URL(node.getAttribute('src') ?? node.getAttribute('href'), base).href));
  }).catch(() => {});
}
['pointerover', 'focusin'].forEach(type => document.addEventListener(type, event => {
  if (event.target.closest?.('.zz-recruiter')) warm();
}, { passive: true }));
