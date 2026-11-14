// Smooth animated shapes (2026-11-14), after a second set of references: transit signage, Swiss posters, VHS sleeves
// and flat colour pictograms. Bold, simple and brightly coloured. Shared by the 3D view's floating loops (tiles.js,
// which roughs them up and grains them like the pixel tiles) and the loading screen (loader.html, which runs before
// the site's own script), so both are inlined from here by patch-bundle.py.
//
// Each entry is [draw, colourways]. draw(c, t, way) paints frame t (0-7) of an eight-frame, one-second loop onto a
// 128 x 128 square whose background (way[0]) is already filled. With only 8 frames a loop, the motions are ones that
// read well in steps and join up seamlessly: turns by exactly one step of a shape's own symmetry, stripes and dashes
// moving on by one period, waves, and eased nudges that come back to where they began.
var zzShapes = (function () {
  const K = '#141414', O = '#ff4f12', L = '#d8ff3c', U = '#8a4fff', N = '#0d5a36', T = '#33dcdc', S = '#f6d69c',
    M = '#701c1c', E = '#1f2cff', Rd = '#ff2b1b', Gy = '#d9d9d3', Cy = '#c7f5f3',
    G = '#18c64a', Y = '#ffe100', P = '#f8a0e6', W = '#ffffff', SIZE = 128, TAU = Math.PI * 2;
  const disc = (c, x, y, r) => { c.beginPath(); c.arc(x, y, r, 0, TAU); c.fill(); };
  const rrect = (c, x, y, w, h, r) => {
    c.beginPath(); c.moveTo(x + r, y);
    c.arcTo(x + w, y, x + w, y + h, r); c.arcTo(x + w, y + h, x, y + h, r);
    c.arcTo(x, y + h, x, y, r); c.arcTo(x, y, x + w, y, r); c.closePath();
  };
  return [
    // A signage arrow nudging out along its own direction and settling back.
    [(c, t, [, a]) => {
      const o = [0, 0, 3, 7, 9, 9, 6, 2][t];
      c.translate(-o, -o);
      c.fillStyle = c.strokeStyle = a;
      c.fillRect(24, 24, 62, 24); c.fillRect(24, 24, 24, 62);
      c.lineWidth = 24; c.beginPath(); c.moveTo(38, 38); c.lineTo(102, 102); c.stroke();
    }, [[O, W], [K, W]]],
    // A scalloped badge turning by one scallop a loop, a dot at its heart.
    [(c, t, [, a, d]) => {
      const n = 12, rot = t / 8 * TAU / n;
      c.fillStyle = a;
      disc(c, 64, 64, 40);
      for (let i = 0; i < n; i++) { const th = rot + i / n * TAU; disc(c, 64 + Math.cos(th) * 42, 64 + Math.sin(th) * 42, 10); }
      c.fillStyle = d; disc(c, 64, 64, 15);
    }, [[K, O, W], [Gy, E, W]]],
    // VHS sleeve stripes: diagonal bands thickening towards one side, sliding on by one band a loop.
    [(c, t, [, a]) => {
      const P = 18;
      c.fillStyle = a;
      c.translate(64, 64); c.rotate(-Math.PI / 3);
      for (let x = -130 + t / 8 * P; x < 130; x += P) c.fillRect(x, -110, 1.5 + Math.max(0, Math.min(1, (x + 70) / 150)) * 12, 220);
    }, [[K, O]]],
    // A halftone grid whose dots swell and shrink in a wave running corner to corner.
    [(c, t, [, a]) => {
      c.fillStyle = a;
      for (let j = 0; j < 6; j++) for (let i = 0; i < 6; i++) {
        const s = 0.5 + 0.5 * Math.cos(((i + j) / 6 - t / 8) * TAU);
        disc(c, 14 + i * 20, 14 + j * 20, 1.5 + s * 8.5);
      }
    }, [[K, Rd]]],
    // A four-leaf blob turning a quarter turn a loop (being four-fold, it joins up seamlessly).
    [(c, t, [, a]) => {
      c.fillStyle = a;
      c.translate(64, 64); c.rotate(t / 8 * TAU / 4);
      for (let i = 0; i < 4; i++) { const th = i / 4 * TAU; disc(c, Math.cos(th) * 25, Math.sin(th) * 25, 25); }
    }, [[E, K]]],
    // A bold plus in a disc: still, then a quarter turn (which looks the same) in one eased move.
    [(c, t, [, a, d]) => {
      c.fillStyle = a; disc(c, 64, 64, 50);
      c.fillStyle = d;
      c.translate(64, 64); c.rotate([0, 0, .06, .3, .7, .94, 1, 1][t] * TAU / 4);
      rrect(c, -35, -11, 70, 22, 11); c.fill(); rrect(c, -11, -35, 22, 70, 11); c.fill();
    }, [[G, Rd, G], [Y, E, Y]]],
    // A sunset disc: bars across its lower part, thickening as they go down, scrolling down by one bar a loop.
    [(c, t, [, a, d]) => {
      c.fillStyle = a; disc(c, 64, 64, 48);
      c.beginPath(); c.arc(64, 64, 48, 0, TAU); c.clip();
      c.fillStyle = d;
      const P = 13;
      for (let y = 30 - P + t / 8 * P; y < 120; y += P) {
        const w = Math.max(0, Math.min(1, (y - 40) / 70)) * 9;
        if (w > 0.4) c.fillRect(0, y, SIZE, w);
      }
    }, [[Gy, G, K]]],
    // A many-pointed burst turning by one point a loop.
    [(c, t, [, a]) => {
      const n = 16, rot = t / 8 * TAU / n;
      c.fillStyle = a; c.beginPath();
      for (let i = 0; i < n * 2; i++) {
        const th = rot + i / (n * 2) * TAU, r = i % 2 ? 22 : 56;
        c.lineTo(64 + Math.cos(th) * r, 64 + Math.sin(th) * r);
      }
      c.closePath(); c.fill();
    }, [[Cy, O]]],
    // A slot: a bar sliding across inside a rounded stadium and back, like a switch being thrown.
    [(c, t, [, a, d, e]) => {
      c.fillStyle = a; rrect(c, 8, 26, 112, 76, 38); c.fill();
      c.fillStyle = d; rrect(c, 22, 40, 84, 48, 24); c.fill();
      c.clip();
      c.fillStyle = e; c.fillRect(30 + [0, .1, .45, .85, 1, .9, .55, .15][t] * 28, 50, 40, 28);
    }, [[Cy, U, N, P]]],
    // A route turning back on itself, ending in an arrowhead; its dashes run along it.
    [(c, t, [, a]) => {
      c.strokeStyle = a; c.lineWidth = 8; c.lineCap = 'butt';
      c.setLineDash([14, 8]); c.lineDashOffset = -t / 8 * 22;
      c.beginPath(); c.moveTo(118, 94); c.lineTo(54, 94); c.arc(54, 70, 24, Math.PI / 2, -Math.PI / 2); c.lineTo(90, 46); c.stroke();
      c.setLineDash([]); c.lineCap = 'round'; c.lineJoin = 'round';
      c.beginPath(); c.moveTo(78, 31); c.lineTo(93, 46); c.lineTo(78, 61); c.stroke();
    }, [[T, L]]],
    // A knobbly cross-shaped blob whose eight knobs swell in turn, round and round.
    [(c, t, [bg, a]) => {
      c.fillStyle = a; c.fillRect(34, 34, 60, 60);
      [[-1, -1], [0, -1], [1, -1], [1, 0], [1, 1], [0, 1], [-1, 1], [-1, 0]].forEach(([i, j], k) => {
        const b = k === t ? 1 : k === (t + 7) % 8 ? 0.45 : 0;
        disc(c, 64 + i * 30, 64 + j * 30, 13 + b * 4);
      });
      c.fillStyle = bg;
      for (const s of [-1, 1]) for (const q of [-15, 15]) { disc(c, 64 + s * 30, 64 + q, 4.5); disc(c, 64 + q, 64 + s * 30, 4.5); }
    }, [[S, M]]],
    // Four arrows from the corners closing in on the middle and easing back out, one of them yellow.
    [(c, t, [, a, d]) => {
      const o = [0, 2, 6, 9, 9, 7, 3, 0][t];
      c.translate(64, 64);
      for (let i = 0; i < 4; i++) {
        c.save(); c.rotate(i * TAU / 4); c.translate(-12 + o, -12 + o); // the tip, pointing at the middle
        c.fillStyle = c.strokeStyle = i === 2 ? d : a;
        c.fillRect(-26, -11, 26, 11); c.fillRect(-11, -26, 11, 26);
        c.lineWidth = 11; c.beginPath(); c.moveTo(-5, -5); c.lineTo(-38, -38); c.stroke();
        c.restore();
      }
    }, [[K, W, Y]]],
    // A wire globe turning: its meridians slide round by one spacing a loop.
    [(c, t, [, a]) => {
      c.strokeStyle = a; c.lineWidth = 4.5;
      c.beginPath(); c.arc(64, 64, 46, 0, TAU); c.stroke(); c.clip();
      for (const y of [-30, -14, 0, 14, 30]) {
        const h = Math.sqrt(46 * 46 - y * y);
        c.beginPath(); c.moveTo(64 - h, 64 + y); c.lineTo(64 + h, 64 + y); c.stroke();
      }
      for (let k = 0; k < 6; k++) {
        const rx = Math.abs(Math.cos((k + t / 8) / 6 * Math.PI)) * 46;
        c.beginPath(); c.ellipse(64, 64, Math.max(0.5, rx), 46, 0, 0, TAU); c.stroke();
      }
    }, [[L, K]]],
    // Six dots coming up one by one, a beat with all six, then gone.
    [(c, t, [, a]) => {
      c.fillStyle = a;
      [[44, 34], [84, 34], [44, 64], [84, 64], [44, 94], [84, 94]].slice(0, [1, 2, 3, 4, 5, 6, 6, 0][t]).forEach(([x, y]) => disc(c, x, y, 12));
    }, [[Rd, K]]],
    // A grid of rounded squares in two sets, one growing as the other shrinks.
    [(c, t, [, a]) => {
      c.fillStyle = a;
      const s = Math.cos(t / 8 * TAU);
      for (let j = 0; j < 4; j++) for (let i = 0; i < 4; i++) {
        const w = 17 + ((i + j) % 2 ? s : -s) * 6;
        rrect(c, 16 + i * 32 - w / 2, 16 + j * 32 - w / 2, w, w, 3); c.fill();
      }
    }, [[O, P]]],
  ];
})();
