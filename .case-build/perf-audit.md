# Performance audit — Lattice of Works (zirui.ca)

**Stack:** three.js r186 · WebGLRenderer + EffectComposer (RenderPass → glitch ShaderPass → OutputPass) · no physics engine (hand-written springs) · React 19 (vanilla three inside a component, not R3F) · GSAP · Vite build, patched by `.case-build/patch-bundle.py`.

**Rig:** Claude's browser pane, Chromium on an Apple M3 Pro, 120 Hz. Desktop at 1440×900 (dpr 1.5, canvas 2160×1350) unless noted. Phone at 375×812 (dpr 1.25, canvas 468×1015).

Numbers come from an in-page harness:
- rAF intervals
- the scene loop's CPU time per rendered frame (JS plus command submission)
- `renderer.info` totals per frame (counters reset manually, because the composer resets them per pass)
- `performance.memory`
- Resource Timing

The GPU time per frame could not be read; the timer query extension is off in this browser.

The changes the audit applies (Category A) are kept separate below from the changes you asked for directly (lite mode, the frozen case background and so on), which deliberately change what's shown.

---

## 1. Baseline (pushed build `2d2cf10`, before any change below)

| Metric | Info | Works | Playground | Case open (Zeen) |
|---|---|---|---|---|
| Frame interval p50 / p95 (ms, 120 Hz) | 8.4 / 9.5 | 8.3 / 9.3 | 8.3 / 9.4 | 8.4 / 9.5 |
| Scene loop CPU p50 / p95 (ms) | 1.2 / 2.1 | 0.8 / 1.2 | 1.0 / 2.2 | 0.8 / 1.2 |
| Frames drawn per second | 120 | 120 | 120 | 40 (every 3rd) |
| Draw calls / triangles / line vertices | 143 / 12.3k / 19.4k | 54 / 6.0k / 19.4k | 120 / 12.1k / 19.4k | 56 / 6.0k |
| `programs` / geometries / textures | 17 / 54 / 103 | 17 / 62 / 107 | 17 / 62 / 107 | 18 / 63 / 109 |
| Long tasks | 0 | 0 | 0 | 0 |

**Loading**
- First contentful paint: 444 ms. LCP: no entry (the page is a canvas).
- Long tasks in the first 10 s: 0, so total blocking time is 0.
- Network: 2.64 MB across 58 requests.

**Memory**
- JS heap: 41.6 MB after load.
- Over 24 view switches and 4 case opens: 24.6 → 33.8 MB. A second identical round: 39.1 → 31.7 MB. No growth.
- GPU objects (geometries / textures): 63/109 → 65/117 on the first round as images loaded lazily, then flat at 65/117 on the second. No leak.

**Estimated VRAM**
- Framebuffers: 66.7 MB (canvas plus two RGBA16F composer targets).
- Textures: 84.5 MB (112 images, with mipmaps).

**Phone size**
- 60 frames drawn per second (the existing half-rate idling), CPU 1.0 / 2.1 ms.
- FCP 492 ms, heap 52.5 MB.
- VRAM 10.9 MB framebuffers + 66.9 MB textures.

**Route lines**
- 34 route lines were rebuilt every 2nd frame, each through `LineGeometry.setPositions` plus `computeLineDistances`. Each rebuild creates two new GPU buffers. Measured: about 900 rebuilds per second.
- The 5 big-card links (two lines each) did the same every frame in Works.

---

## 2. Checklist

### 1 · Leaks and RAM/VRAM
| Item | Result | Evidence |
|---|---|---|
| Objects removed without dispose | Not found | The scene is built once and never torn down while the page is open. GPU counts were flat across two full rounds (65/117). `zzLighten` disposes what it replaces. |
| Material maps disposed | N/A | No runtime teardown. The scene's `dispose()` (page unload only) doesn't free geometries or materials; that has no effect while the page is open. |
| PMREMGenerator not disposed | **Found → fixed (A1)** | The generator and its `RoomEnvironment` were kept alive after building the environment map. |
| Composer / render targets | Not found | `resize` uses `setSize`. The composer isn't disposed on unmount (page unload only). |
| Multiple WebGLRenderers | Not found | One renderer. The software-renderer probe context is released with `WEBGL_lose_context`. |
| rAF loops not cancelled | Not found | The scene loop and the Info tilt loop both cancel in cleanup. Neither duplicates on view changes (the tilt loop is gated to Info). |
| Listeners not removed | Not found | Scene `dispose` and React effect cleanups remove them. |
| AnimationMixer | N/A | — |
| GSAP not killed | Not found | Intro timelines are killed in cleanup, and flights kill the previous one. |
| Physics | N/A | No engine. |
| Workers / ObjectURLs / ImageBitmaps / Audio | N/A | None used. |
| `THREE.Cache` | Not found | Not enabled. |
| Duplicate loads | Not found | Each image loads once. The 64 glyph phase textures share one `Source`. |
| Detached DOM | Not found | The case window's content is removed on close (`.zz-case` count back to 0). |
| `console.log` of large objects | Not found | 1 call in the bundle (React's), and no scene logging. |
| Oversized textures | Found (reported) | Work-card canvases are drawn 1280 px wide (≈5.3 MB each with mipmaps) but shown at most about 900 px wide. Shrinking them would change pixels, so it's listed as B1. |
| Unused vertex attributes | Not found | The lattice's `aT` and `aSeed` are read by its shader. The environment room already drops `uv`. |
| `will-change` | Found (minor) | Permanent on 8 small elements (cursor parts, titles). Not measured, so not changed. |

### 2 · Per-frame CPU
| Item | Result | Evidence |
|---|---|---|
| Allocations in the loop | **Found → partly fixed (A3, A4, A5)** | Per-node `camera.position.clone().add(new Vector3…)` was hoisted out of the node loop. An unused per-frame text key and a stray `new Vector3` were removed. Others remain (`currentPos` clone per node, route point arrays) and are small. |
| Several rAF tickers | Found (not changed) | Scene loop + GSAP ticker + Info tilt loop (Info only) + dial loop (stops when idle) + favicon interval (8/s). Merging them would change their order. Not measured. |
| Raycast per pointermove | Not found | `pickWork` runs once per frame against about 35 sprites. |
| `matrixAutoUpdate` on static objects | N/A | Nearly everything moves every frame. |
| Per-frame `traverse` | Not found | — |
| Dynamic geometry recreated | **Found → fixed (A2)** | Route and card-link lines rebuilt their buffers (about 900/s). |
| Physics sync / broadphase / worker | N/A | — |
| Timers running in hidden tabs | Found (minor) | The favicon (125 ms) and Z-counter sender (400 ms) intervals keep running; browsers throttle them to 1/s. The card-video check skips hidden tabs. |
| GPU readbacks in the loop | Not found | — |

### 3 · GPU / rendering
| Item | Result | Evidence |
|---|---|---|
| Rendering when nothing changes | Not applicable as A | The scene animates continuously (time-driven motion), so render-on-demand would change output. While a case study is open it now stops drawing; that was a request (R2). |
| Rendering hidden or off-screen | Not found | rAF stops in hidden tabs, and the canvas is always on screen. |
| Draw calls / instancing | Found (B2) | 120–143 calls in Info and Playground, mostly individual sprites (glyphs and works). Instancing would change the sort order of transparent sprites. |
| Material duplication | Found (B2) | One SpriteMaterial per glyph sprite (320). Programs are shared (11). |
| Shader recompiles / pre-warm | Not found | `programs` stayed at 11 across view switches. `compileAsync` isn't used; first-use hitches weren't measured. |
| `antialias` with a composer | **Unresolved (U1)** | — |
| Post-processing | Found (U2) | The glitch pass runs every frame, though it only shows during bursts and dimming. |
| `preserveDrawingBuffer` / log depth | Not found | Both off. |
| Shadows | N/A | No shadow maps. |
| `frustumCulled = false` | Found (justified) | On the lattice and routes, whose shaders move vertices (`uOffset`). Culling would be wrong. |
| Overdraw | Found (not changed) | A full-screen sky shader plus transparent sprites. |
| Mipmaps on UI textures | Not found | Card textures are minified, so the mipmaps are used. |
| `setSize` per frame | Not found | Only in `resize`. |
| Multiple WebGL canvases | Not found | One WebGL canvas. The others are 2D (dial, Info pixel trails, loader). |
| `powerPreference` | Not found | Already `high-performance`. |
| GPGPU | N/A | — |

### 4 · DOM / CSS / animation
| Item | Result | Evidence |
|---|---|---|
| Animating layout properties | Not found | Transforms and opacity only. |
| Layout thrashing | Found, negligible | The Info tilt loop interleaves 18 `getBoundingClientRect` reads with style writes each frame. Measured 0.035 ms/frame, so not changed. |
| Non-passive touch/wheel listeners | Found (needed) | Scene wheel (zoom), phone panel touchmove, desktop panel wheel and case-margin wheel. All call `preventDefault`, scoped to their elements. |
| Large blur / backdrop-filter | Not found | Only a brief 10 px blur on the case close animation. |
| Huge DOM | Found (B3) | Zeen's case study is 28k px tall with 26 videos. |
| Off-screen video decoding | Not found | Case videos pause off-screen, and the card video plays only in Works on a visible tab. |
| Hidden animations | Not found | The Info effects stop outside Info. |

### 5 · Loading
| Item | Result | Evidence |
|---|---|---|
| Bundle | Not found / noted | A 986 KB minified production bundle (277 KB gzip), with no source maps shipped and no code splitting. The recruiter page is separate and prefetched on hover. |
| Compression / cache headers | **Unresolved (U3)** | Set by the host, not visible in the code. |
| Geometry compression | N/A | All geometry is procedural. |
| KTX2 textures | B4 | — |
| Lazy loading | Not found | Case media uses `preload="none"` and loads near view. |
| Duplicate requests | Not found | 58 requests, no repeats. |
| Main-thread texture decode | Found (not changed) | Work images are decoded and drawn into 2D canvases on the main thread. No long tasks were recorded, so there's nothing to measure against. |

### 6 · R3F
N/A. This is vanilla three inside a React component. The scene's per-frame `onHover` only touches React or the DOM when the hovered work changes (checked).

---

## 3. Applied changes (Category A: same pixels)

All are in `.case-build/patch-bundle.py`, sections 24–24b.

| # | Change | Problem | Before → after | Equivalence check |
|---|---|---|---|---|
| A1 | `pmrem.dispose(); room.dispose()` after `fromScene` | The generator's targets, materials and room meshes stayed alive | programs 17 → 11; geometries 62 → 49 (Works) | Pixel diff: 0 px |
| A2 | `zzLine()` writes route and card-link points and line distances into the buffers each line already has. It runs the same arithmetic as `setPositions` / `computeLineDistances`, and falls back to them if the sizes ever differ. | Two new GPU buffers per line per update | Rebuilds about 900/s → 0/s | Pixel diff 0 px in Playground (routes) and Works (card links) |
| A3 | The camera look-ahead point is computed once per frame instead of once per work | About 35 Vector3 allocations a frame | Same value, 1 allocation | Pixel diff: 0 px |
| A4 | Removed `updateTiles`' text key, which nothing read | About 105 number-to-string conversions a frame | — | Pixel diff: 0 px |
| A5 | Removed a stray `new Vector3` per frame | Garbage | — | Pixel diff: 0 px |

**How equivalence was checked**
- The pushed version (`2d2cf10`) was checked out separately and served alongside the new build, with only a `window.zzScene` hook added.
- Each build rendered one frame with a frozen setup: the loop stopped, the clock fixed at t = 42, a fixed camera, the pointer away, the glitch held at 0, and the view state set directly.
- Frames were captured at 2160×1350 and compared with ImageMagick (`compare -metric AE`). The result was **0 differing pixels** in both Playground and Works.
- The floating pixel-glyph sprites were hidden in both builds. Their sheets add `Math.random()` grain when drawn, so even the old build differed from itself by 47.7k px between loads with them shown. The glyph code isn't touched by A1–A5.
- Zeen's video card was left out because a video frame can't be frozen.

**Measured CPU:** about 1 ms either side on this M3 Pro, too small and noisy to show a change. The gain is in GPU-buffer churn and garbage, measured above.

---

## 4. Changes that alter output

### Applied at your request (not audit changes)
| | Change | Effect | Visible difference |
|---|---|---|---|
| R1 | Lite mode for slow devices | See below for the triggers and settings | Only on lite devices: softer 1× image, no glitch bursts, fewer floating glyphs, sparser lattice, 30 fps idle, Zeen's card still, and Info's background is a 10 s loop instead of live |
| R2 | The background stops drawing 0.7 s after a case study or pop-up opens, with its clock held | 40 → 0 frames per second while reading | The dimmed background is a still frame |
| R3 | Case studies go still when slow: in lite mode, or when the opening media isn't ready after 2.5 s (then for the rest of the visit) | Videos load only when you press play; illustrations aren't animated | Posters with play buttons instead of autoplaying loops |
| R4 | Works cards 20% closer, phone tilt at 15%, swipe and dial navigation, loading screen, case scrolling inside its frame | — | As asked |

**When lite mode starts.** Any of these:
- the address has `?lite=1` (`?lite=0` forces the full scene)
- a slow measurement on an earlier visit, remembered for 7 days
- the browser's Save-Data setting
- the device reports 2 GB of memory or less, or 2 cores or fewer
- a software GPU
- an average frame gap over 24 ms while the loader is up
- two slow 1.5 s stretches (over 28 ms) in the first 20 s

**What lite mode changes.**
- 1× pixel ratio and no glitch pass.
- 2 in 5 glyph sprites kept, and the lattice keeps 20% of its lines instead of 45%.
- 30 fps idle and route updates every 4th frame.
- Zeen's card video stays still.
- On Info, the live scene is replaced by `bg/info-{wide,tall}.mp4`: 10 s seamless loops, about 2 MB each, rendered frame by frame from the scene at the landing camera.

**Lite measurements (1280×800, same machine)**
- Frames drawn per second: Info 120 → 0, Works 120 → 60, Playground 120 → 60.
- CPU p50: Works 0.7 → 0.5 ms, Playground 1.1 → 0.7 ms.
- Draw calls: Works 54 → 33, Playground 119 → 100.
- Line vertices: 19.4k → 8.3k.
- Canvas: 1920×1200 → 1280×800.
- Framebuffer VRAM: 52.7 → 23.4 MB. JS heap: 53.8 → 41.8 MB.

### Proposed, not applied
| | Change | Expected saving | Exact difference | Would anyone notice? |
|---|---|---|---|---|
| B1 | Draw work-card canvases at 900 px wide instead of 1280 | About 2.6 MB VRAM per card (≈13 MB for 5) and faster uploads | Card textures softer when a card is opened up close | Likely, at the moment of opening |
| B2 | Instance glyph sprites (InstancedMesh with a sprite-sheet atlas) | About 60–90 fewer draw calls in Info and Playground | Transparent sort order between glyphs and works can change where they overlap | Unlikely |
| B3 | `content-visibility:auto` on case study sections | Faster first paint of long studies; less layout work while scrolling | Possible scrollbar-length jumps before sections are first seen | Possible (scrollbar only) |
| B4 | KTX2 (UASTC) for work images | Roughly 4–6× less texture VRAM | Lossy compression artefacts | Unlikely at viewing distance |
| B5 | Cap desktop pixel ratio at 1.25 for everyone | 31% fewer pixels shaded | Slightly softer lines on Retina screens | Possible on close inspection |

---

## 5. After (Category A only, 1440×900, same rig)

| Metric | Info | Works | Playground |
|---|---|---|---|
| Frame interval p50 / p95 (ms) | 8.4 / 9.9 | 8.3 / 9.3 | 8.3 / 9.8 |
| Scene loop CPU p50 / p95 (ms) | 1.3 / 2.5 | 0.8 / 1.6 | 1.2 / 2.4 |
| `programs` / geometries | 11 / 49 | 11 / 49 | 11 / 49 |
| Line buffer rebuilds per second | — | 0 | 0 (was about 900) |
| Long tasks | 0 | 0 | 0 |

- **Loading:** FCP 84 ms (repeat visit, warm), TBT 0, 2.65 MB across 58 requests. The loader and its percentage paint before any script runs.
- **Case open:** 0 frames drawn per second (was 40), from R2.
- **Frame intervals and CPU:** unchanged within noise on this machine.

---

## 6. Unresolved

- **U1 · `antialias: true` on the canvas.** Every pass renders into the composer's non-multisampled targets, so canvas MSAA should do nothing. But in this browser the scene's context reports `antialias:false, depth:false` even in the old build, while a test canvas honours `antialias:true`. So the change couldn't be measured, and I reverted it.
  - To settle it: in desktop Chrome, compare `renderer.getContext().getContextAttributes()` and GPU memory (`chrome://gpu`, or a Spector.js capture) with `antialias` true and false, plus a pixel diff.
- **U2 · The glitch pass between bursts.** If its shader returns the input unchanged when `uAmt = 0` and `uDim = 0`, skipping it then would be Category A and save one full-screen pass a frame.
  - To settle it: read the fragment shader and pixel-diff with the pass disabled at `uAmt = uDim = 0`.
- **U3 · Brotli/gzip and cache headers.** These depend on the host serving zirui.ca.
  - To settle it: `curl -I https://www.zirui.ca/assets/index-DnZOTAZ6.js` and check `content-encoding` and `cache-control`.
- **GPU frame time.** Not readable here, because `EXT_disjoint_timer_query_webgl2` is disabled.
  - To settle it: a Chrome performance trace with GPU rows, or a Spector.js capture on a real low-end phone, which would also confirm that the lite thresholds trip where intended.
- **10-minute heap.** Only measured over about 2 minutes of heavy switching, with no growth.
