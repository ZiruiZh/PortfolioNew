// The tab icon plays the "crosses growing out" pixel animation from the 3D view: four little crosses spread
// from a centre dot and fold back in, their colours rotating, eight frames a second like the scene.
// Browsers that don't redraw tab icons live (and people who ask for reduced motion) keep favicon.svg,
// the widest frame.
const COLOURS = ['#ff1a3c', '#12a9e8', '#fccc0a'];
const REACH = [0, 1, 2, 3, 3, 2, 1, 0];
const GRID = 15, CELL = 4, SIZE = 64, PAD = (SIZE - GRID * CELL) / 2;

function cells(t) {
  const out = [];
  const plot = (x, y, colour) => { if (x >= 0 && y >= 0 && x < GRID && y < GRID) out.push([x, y, colour]); };
  const cross = (x, y, colour) => { for (let a = -1; a <= 1; a++) { plot(x + a, y, colour); plot(x, y + a, colour); } };
  const r = 2 + REACH[t];
  [[7, 7 - r], [7 + r, 7], [7, 7 + r], [7 - r, 7]].forEach(([x, y], i) => cross(x, y, COLOURS[(i + t) % 3]));
  plot(7, 7, COLOURS[(t + 2) % 3]);
  return out;
}

function frames() {
  const canvas = document.createElement('canvas');
  canvas.width = canvas.height = SIZE;
  const ctx = canvas.getContext('2d');
  return REACH.map((_, t) => {
    ctx.clearRect(0, 0, SIZE, SIZE);
    for (const [x, y, colour] of cells(t)) {
      ctx.fillStyle = colour;
      ctx.fillRect(PAD + x * CELL, PAD + y * CELL, CELL, CELL);
    }
    return canvas.toDataURL('image/png');
  });
}

const reduced = matchMedia('(prefers-reduced-motion: reduce)');
let link = document.querySelector('link[rel~="icon"]');
if (!link) {
  link = document.createElement('link');
  link.rel = 'icon';
  document.head.append(link);
}
const still = link.getAttribute('href');
const pictures = frames();
let t = 0, timer = 0;

function start() {
  if (timer || reduced.matches) return;
  link.type = 'image/png';
  timer = setInterval(() => { t = (t + 1) % pictures.length; link.href = pictures[t]; }, 125);
}
function stop() {
  clearInterval(timer);
  timer = 0;
  link.type = 'image/svg+xml';
  if (still) link.href = still;
}
reduced.addEventListener('change', () => (reduced.matches ? stop() : start()));
start();
