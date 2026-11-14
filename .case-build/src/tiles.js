// Pixel tiles for the 3D view's floating loops, after the reference sheet of flat colour tiles (2026-11-13).
// patch-bundle.py (section 32) inserts this file into the bundle right after the loops' own list (Tg) and before any
// of them are drawn. Like the others, each is a 16 x 16 grid drawn for 8 frames (a one-second loop at 8 frames a
// second) and given the same printed grain; unlike them each fills its whole square with a flat colour, keeps
// its own colours (one or two colourways, not four random ones), and has its edges diffused and worn (rough, below).
// The drawing function gets set(x, y, colour), the frame t (0-7) and the colourway [background, shape].
{
  const G = '#18c64a', R = '#ff5714', B = '#2b40d0', Y = '#ffe100', P = '#f8a0e6', C = '#66e6e0', W = '#ffffff', D = '#ff1a3c';
  // Roughs up one drawn frame (128 x 128px at x0 on the strip) so no edge is ruler-straight. Near every edge between
  // two colours each pixel may take the colour of a pixel up to 3px away (a sprayed, diffused edge); the tile's own
  // outline wears away unevenly, more at the very edge. The noise is new each frame, so edges shimmer slightly as the
  // loop plays, like hand-drawn line boil. The site's usual grain goes on afterwards.
  const SIZE = 128, REACH = 3.5, WEAR = 4;
  const rough = (ctx, x0, seed) => {
    let s = (seed * 9301 + 49297) % 2147483647 || 1;
    const rnd = () => (s = (s * 16807) % 2147483647) / 2147483647;
    const img = ctx.getImageData(x0, 0, SIZE, SIZE), d = img.data, src = new Uint8ClampedArray(d);
    const same = (a, b) => src[a] === src[b] && src[a + 1] === src[b + 1] && src[a + 2] === src[b + 2];
    const at = (x, y) => (Math.min(SIZE - 1, Math.max(0, y)) * SIZE + Math.min(SIZE - 1, Math.max(0, x))) * 4;
    // Which of the 16 x 16 grid cells touch a cell of another colour; only their pixels can change.
    const near = new Uint8Array(256);
    for (let cy = 0; cy < 16; cy++) for (let cx = 0; cx < 16; cx++) {
      const o = at(cx * 8 + 4, cy * 8 + 4);
      for (let j = -1; j <= 1 && !near[cy * 16 + cx]; j++) for (let i = -1; i <= 1; i++) {
        if (!same(o, at((cx + i) * 8 + 4, (cy + j) * 8 + 4))) { near[cy * 16 + cx] = 1; break; }
      }
    }
    for (let y = 0; y < SIZE; y++) for (let x = 0; x < SIZE; x++) {
      const o = (y * SIZE + x) * 4, edge = Math.min(x, y, SIZE - 1 - x, SIZE - 1 - y);
      if (edge < WEAR && rnd() < (WEAR - edge) * 0.2) { d[o + 3] = 0; continue; }
      if (!near[(y >> 3) * 16 + (x >> 3)]) continue;
      const so = at(x + Math.round((rnd() + rnd() - 1) * REACH), y + Math.round((rnd() + rnd() - 1) * REACH));
      if (!same(o, so) && rnd() < 0.7) d[o] = src[so], d[o + 1] = src[so + 1], d[o + 2] = src[so + 2];
    }
    ctx.putImageData(img, x0, 0);
  };
  let made = 0;
  const tile = (draw, ways) => {
    let k = -1;
    const f = (set, t, colours, ctx, x0) => {
      if (t === 0) k++, made++;
      const way = ways[k % ways.length];
      for (let y = 0; y < 16; y++) for (let x = 0; x < 16; x++) set(x, y, way[0]);
      draw(set, t, way);
      rough(ctx, x0, made * 8 + t);
    };
    f.zzN = ways.length; // how many colourways (textures) to make
    return f;
  };
  const rows = (set, bitmap, x0, y0, colour) => bitmap.forEach((row, y) => {
    for (let x = 0; x < row.length; x++) if (row[x] === 'X') set(x0 + x, y0 + y, colour);
  });
  const turn = (x, y, k) => { for (; k > 0; k--) [x, y] = [15 - y, x]; return [x, y]; };

  // A square spiral, 1px line and 1px gap, from the edge in.
  const spiral = [];
  {
    let x = 1, y = 1, dx = 1, dy = 0;
    spiral.push([x, y]);
    for (const n of [13, 13, 13, 11, 11, 9, 9, 7, 7, 5, 5, 3, 3, 1]) {
      for (let i = 0; i < n; i++) { x += dx; y += dy; spiral.push([x, y]); }
      [dx, dy] = [-dy, dx];
    }
  }
  const HEART = ['.XXX...XXX.', 'XXXXX.XXXXX', 'XXXXXXXXXXX', 'XXXXXXXXXXX', 'XXXXXXXXXXX',
    '.XXXXXXXXX.', '..XXXXXXX..', '...XXXXX...', '....XXX....', '.....X.....'];
  const HEART_SMALL = ['.XX...XX.', 'XXXX.XXXX', 'XXXXXXXXX', 'XXXXXXXXX', '.XXXXXXX.', '..XXXXX..', '...XXX...', '....X....'];
  const QUESTION = ['.XXXXX.', 'XX...XX', 'XX...XX', '.....XX', '....XX.', '...XX..', '...XX..', '.......', '...XX..', '...XX..'];

  Tg.push(
    // Square spiral, turning a quarter every two frames.
    tile((set, t, [, c]) => spiral.forEach(([x, y]) => set(...turn(x, y, (t >> 1) & 3), c)), [[G, B], [Y, D]]),
    // Play: the triangle nudges forward and settles back.
    tile((set, t, [, c]) => {
      const o = [0, 0, 1, 2, 2, 2, 1, 0][t];
      [1, 3, 5, 7, 9, 9, 7, 5, 3, 1].forEach((w, i) => { for (let x = 0; x < w; x++) set(4 + o + x, 3 + i, c); });
    }, [[R, B]]),
    // Checkerboard of 2px squares sliding diagonally, a pixel a frame.
    tile((set, t, [, c]) => {
      for (let y = 0; y < 16; y++) for (let x = 0; x < 16; x++) if ((((x + t) >> 1) + ((y + t) >> 1)) & 1) set(x, y, c);
    }, [[Y, D], [P, B]]),
    // Brick rows (each row offset by half a brick) sliding along together.
    tile((set, t, [, c]) => {
      for (let y = 0; y < 16; y++) {
        const r = y >> 1;
        for (let x = 0; x < 16; x++) if ((((x + t + (r & 1) * 2) >> 2) & 1)) set(x, y, c);
      }
    }, [[B, D]]),
    // Nested squares moving outward, like a tunnel.
    tile((set, t, [, c]) => {
      for (let y = 0; y < 16; y++) for (let x = 0; x < 16; x++) {
        const u = Math.floor(Math.max(Math.abs(x - 7.5), Math.abs(y - 7.5)) + 0.5);
        if (((u + 8 - (t >> 1)) >> 1) & 1) set(x, y, c);
      }
    }, [[Y, D], [W, P]]),
    // Heart: lub-dub, then a rest.
    tile((set, t, [, c]) => {
      if ([1, 0, 1, 0, 0, 0, 0, 0][t]) rows(set, HEART, 2, 3, c);
      else rows(set, HEART_SMALL, 3, 4, c);
    }, [[P, D], [R, Y]]),
    // Question mark, bobbing.
    tile((set, t, [, c]) => rows(set, QUESTION, 4, 3 + [0, 0, -1, -1, 0, 0, 1, 1][t], c), [[P, R]]),
    // Exclamation mark: the bar draws down, then the dot lands.
    tile((set, t, [, c]) => {
      const n = Math.min(7, (t + 1) * 2);
      for (let y = 3; y < 3 + n; y++) set(7, y, c), set(8, y, c);
      if (t >= 3) for (const [x, y] of [[7, 11], [8, 11], [7, 12], [8, 12]]) set(x, y, c);
    }, [[B, Y]]),
    // Chat bubble with typing dots.
    tile((set, t, [, c]) => {
      for (let x = 3; x <= 12; x++) set(x, 3, c), set(x, 11, c);
      for (let y = 4; y <= 10; y++) set(2, y, c), set(13, y, c);
      for (const [x, y] of [[4, 12], [5, 12], [4, 13]]) set(x, y, c);
      [4, 7, 10].slice(0, t % 4).forEach(x => { set(x, 6, c), set(x + 1, 6, c), set(x, 7, c), set(x + 1, 7, c); });
    }, [[G, Y]]),
    // Two chevrons marching left.
    tile((set, t, [, c]) => {
      for (let y = 3; y <= 12; y++) {
        const a = Math.abs(y - 7.5) - 0.5;
        for (let x = 0; x < 16; x++) if ((((x - a + t) % 8) + 8) % 8 < 2) set(x, y, c);
      }
    }, [[W, G]]),
    // Diamond ring, breathing.
    tile((set, t, [, c]) => {
      const r = [4, 5, 6, 7, 7, 6, 5, 4][t];
      for (let y = 0; y < 16; y++) for (let x = 0; x < 16; x++) {
        const s = Math.abs(x - 7.5) + Math.abs(y - 7.5);
        if ((s >= r - 1 && s <= r) || s <= 1) set(x, y, c);
      }
    }, [[C, B]]),
    // Arrow pointing down-right, nudging along its own direction and settling back.
    tile((set, t, [, c]) => {
      const o = [0, 0, 1, 2, 2, 2, 1, 0][t] - 1, at = (x, y) => set(x + o, y + o, c);
      for (let i = 0; i <= 8; i++) at(3 + i, 3 + i), at(4 + i, 3 + i);
      for (let i = 0; i <= 5; i++) at(6 + i, 11), at(11, 6 + i);
    }, [[G, Y]]),
    // Four colour bands scrolling up.
    tile((set, t) => {
      const band = [Y, G, B, D];
      for (let y = 0; y < 16; y++) for (let x = 0; x < 16; x++) set(x, y, band[((y + t * 2) >> 2) & 3]);
    }, [[Y]]),
  );
}
