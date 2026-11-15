import json, os, re, sys

SITE = '/Users/ziruizhao/Downloads/zirui-zhao-site'
PORT = '/Users/ziruizhao/Documents/PersonalPortfolioWebsite'
SRC = f'{SITE}/.backup-original/index-DnZOTAZ6.js'   # always patch from the pristine copy
OUT = f'{SITE}/assets/index-DnZOTAZ6.js'
CSS_SRC = f'{SITE}/.backup-original/index-C-HYMxcf.css'
CSS_OUT = f'{SITE}/assets/index-C-HYMxcf.css'

s = open(SRC).read()

def tl(v):
    """JS template literal."""
    assert '`' not in v and '${' not in v, v
    return '`' + v + '`'

def obj(d):
    parts = []
    for k, v in d.items():
        if v is None:
            continue
        if isinstance(v, dict):
            parts.append(f'{k}:{obj(v)}')
        elif isinstance(v, int):
            parts.append(f'{k}:{v}')
        else:
            parts.append(f'{k}:{tl(v)}')
    return '{' + ','.join(parts) + '}'

# ---- 1. Playground metadata ------------------------------------------------
# Playground holds only Zirui's own pieces (the portfolio's playground images, and the ArtsFest poster). The nine
# pieces kept from the original template (w01 The winter, w02 Fear of Lice, w03 Extior, w05 Koi Plaza, w13 Oval Altar,
# w16 Almost Touching, w20 Manta Courtyard, w31 Square Tunnel, w33 Crosswalk Network) were AI-made and came out on
# 2026-11-13; list an id here to bring one back.
KEEP = []
ug_start = s.index('Ug={w01')
ug_end = s.index('},Wg={', ug_start) + 1
old_ug = s[ug_start + 3:ug_end]
# keep the original entries we hold on to, verbatim
kept = {}
for m in re.finditer(r'(w\d\d):(\{[^{}]*\})', old_ug):
    if m.group(1) in KEEP:
        kept[m.group(1)] = m.group(2)
assert len(kept) == len(KEEP), kept.keys()

meta = {}
for d in json.load(open(f'{PORT}/src/playground-images.json')):
    title = d['title']
    year = None
    m = re.match(r'^(.*), (20\d\d)$', title)
    if m:
        title, year = m.group(1), int(m.group(2))
    meta[f"pg-{d['id']}"] = {'title': title, 'year': year}

# The Marianopolis ArtsFest poster moved here from Works (2026-11-12): the whole poster, at its own shape.
EXTRA = {'artsfest': {'title': 'ArtsFest poster', 'year': 2024}}
meta.update(EXTRA)

entries = [f'{k}:{v}' for k, v in kept.items()]
entries += [f'"{k}":{obj(v)}' for k, v in meta.items()]
s = s[:ug_start] + 'Ug={' + ','.join(entries) + '}' + s[ug_end:]

# ---- 2. Trim descriptions to the works that are still shown -----------------
wg_start = s.index('Wg={w01')
wg_end = s.index('},Gg=', wg_start) + 1
bodies = dict(re.findall(r'(w\d\d):`([^`]*)`', s[wg_start:wg_end]))
s = s[:wg_start] + 'Wg={' + ','.join(f'{k}:{tl(bodies[k])}' for k in KEEP if k in bodies) + '}' + s[wg_end:]

# ---- 3. Playground order ---------------------------------------------------------
ORDER = ['pg-16', 'pg-07', 'pg-06', 'pg-25', 'pg-11', 'pg-24', 'pg-12',
         'pg-02', 'pg-23', 'pg-18', 'pg-34', 'pg-21', 'pg-01', 'pg-04',
         'pg-26', 'pg-09', 'pg-29', 'pg-15', 'pg-05', 'pg-35', 'pg-17', 'pg-08',
         'pg-32', 'pg-30', 'pg-13', 'pg-22',
         # Added last so every earlier piece keeps its place in the lattice.
         'artsfest']
assert len(ORDER) == len(set(ORDER)) == len(KEEP) + len(meta)
assert set(ORDER) == set(KEEP) | set(meta)
for k in ORDER:
    assert os.path.exists(f'{SITE}/works/{k}.webp'), k

old_gg = ('Gg=Array.from({length:35},(e,t)=>{let n=`w${String(t+1).padStart(2,`0`)}`;'
          'return{id:n,img:`works/${n}.webp`,body:Wg[n],...Ug[n]??{title:`Untitled`}}})')
assert s.count(old_gg) == 1
new_gg = ('Gg=[' + ','.join(tl(k) for k in ORDER) + '].map(n=>({id:n,img:`works/${n}.webp`,thumb:`works/thumbs/${n}.webp`,'
          'body:Wg[n],...Ug[n]??{title:`Untitled`}}))')
s = s.replace(old_gg, new_gg)

# ---- 4. Work entries -----------------------------------------------------------
class Raw(str):
    pass

def js(v):
    if isinstance(v, Raw): return str(v)
    if isinstance(v, bool): return '!0' if v else '!1'
    if isinstance(v, int): return str(v)
    if isinstance(v, (list, tuple)): return '[' + ','.join(js(x) for x in v) + ']'
    if isinstance(v, dict): return '{' + ','.join(f'{k}:{js(x)}' for k, x in v.items() if x is not None) + '}'
    return tl(v)

PORT_PROJECTS = open(f'{PORT}/src/projects.js').read()
a = PORT_PROJECTS.index('{', PORT_PROJECTS.index('export const projects ='))
P = json.loads(PORT_PROJECTS[a:PORT_PROJECTS.index('\n};', a) + 2])

def study(key, cover):
    """A full case study shown in the site's case window, drawn by work/case-embed.js."""
    p = P[key]
    return {
        'id': key, 'title': p.get('cardName', p['title']), 'year': int(p['year']),
        # The window's big title and facts column, exactly as the portfolio page has them.
        'heading': p.get('pageTitle', p['title']),
        'facts': [['Role' if k == 'My Role' else k, v if isinstance(v, list) else [v]] for k, v in p['metadata'].items()],
        'img': f'cases/{key}/{cover}', 'video': f"cases/{key}/{p['card']['video']}" if p['card'].get('video') else None,
        'ratio': Raw(p['card']['ratio'].replace(' ', '')), 'case': key,
        # The cursor and hover label take the project's own accent from the portfolio.
        'color': p['accent'],
    }

CASES = [
    # Zeen's card shows this still whenever its video isn't playing (lite mode, a slow connection, or before the video
    # arrives): a frame of the cover you supplied, cropped clear of its dark border and the black corner element.
    study('zeen', 'zeen-card-still.webp'),
    study('allot', P['allot']['card']['images'][0]),
    # Prism has no case study: the card opens its site in a new tab. Its video is drawn 2% larger from the left edge.
    {'id': 'prism', 'title': P['prism']['title'], 'year': int(P['prism']['year']),
     'img': f"cases/prism/{P['prism']['card']['poster']}", 'video': f"cases/prism/{P['prism']['card']['video']}",
     'ratio': Raw(P['prism']['card']['ratio'].replace(' ', '')), 'zoom': Raw('1.02'),
     'href': P['prism']['link'], 'external': True,
     # The portfolio gives Prism no accent; purple, after its cover.
     'color': '#8f5bff'},
]
for c in CASES:
    for k in ('img', 'hero', 'video'):
        if c.get(k):
            assert os.path.exists(f'{SITE}/{c[k]}'), c[k]

old_kg = 'Kg=[`w01`,`w02`,`w03`].map(e=>Gg.find(t=>t.id===e)).filter(Boolean)'
assert s.count(old_kg) == 1
# zzGo opens a work that lives on another site.
zz = 'zzGo=e=>{window.open(e.href,`_blank`,`noopener`)}'
s = s.replace(old_kg, 'Kg=[' + ','.join(js(c) for c in CASES) + '],' + zz)

def sub(old, new):
    global s
    assert s.count(old) == 1, old
    s = s.replace(old, new)

# ---- 5. Opening an outside link --------------------------------------------------
# The scene opens it at once, inside the click, so it is never blocked as a popup.
sub('open(e){let t=this.activeNodes().find(t=>t.work===e);',
    'open(e){if(e?.external){zzGo(e);return}let t=this.activeNodes().find(t=>t.work===e);')
# The list buttons and the window's previous/next do the same.
sub('P=(0,l.useCallback)(e=>{s(null),t.current?.open(e),a(e)},[])',
    'P=(0,l.useCallback)(e=>{if(e?.external){zzGo(e);return}s(null),t.current?.open(e),a(e)},[])')
# #works and #playground in the address open those views; Works is where a first click off Info goes.
sub('[h,g]=(0,l.useState)(`playground`)', '[h,g]=(0,l.useState)(()=>location.hash===`#playground`?`playground`:`works`)')
# The app starts in Info itself (unless the address asks for Works or Playground). Starting in the projects view for
# a moment set the scene off on the Works overview flight, which landed after Info had opened and left Info looking
# through the Works camera, close in.
sub('[c,u]=(0,l.useState)(`projects`)', '[c,u]=(0,l.useState)(()=>/^#(works|playground)$/.test(location.hash)?`projects`:`info`)')
sub('let F=(e,n)=>{n&&g(n),a(null),s(null),u(e),t.current?.close(),t.current?.goArea(e)};',
    'let F=(e,n)=>{n&&g(n),a(null),s(null),u(e),t.current?.close(),t.current?.goArea(e)};'
    # The Info page is where visitors land, unless the address asks for #playground or #works.
    '(0,l.useEffect)(()=>{/^#(works|playground)$/.test(location.hash)||F(`info`)},[]);')

# ---- 6. Work cards: drawn at their own ratio, and a cover video keeps playing on the card ----
ci = s.index('Kg.forEach((e,t)=>{')
c0 = s.index('a=new Image;a.onload=()=>{let e=1280,', ci)
c1 = s.index('a.src=`./${e.img}`', c0) + len('a.src=`./${e.img}`')
old_card = s[c0:c1]
assert 'r.drawImage(a,(a.width-c)/2,(a.height-l)/2,c,l,14,14,e,720)' in old_card
rr = 'o=(e,t,n,i,a)=>{r.beginPath(),r.moveTo(e+a,t),r.arcTo(e+n,t,e+n,t+i,a),r.arcTo(e+n,t+i,e,t+i,a),r.arcTo(e,t+i,e,t,a),r.arcTo(e,t,e+n,t,a),r.closePath()}'
assert rr in old_card
new_card = ('a=new Image,W=e;a.onload=()=>{let e=this.el.clientWidth<700?720:1280,H=Math.round(e/(W.ratio||16/9)),t=document.createElement(`canvas`);'
    't.width=e+28,t.height=H+28;let r=t.getContext(`2d`),' + rr + ','
    'p=a=>{let w=a.videoWidth||a.naturalWidth,h=a.videoHeight||a.naturalHeight;if(!w||!h)return;'
    'r.clearRect(0,0,t.width,t.height),r.fillStyle=`#ffffff`,o(0,0,t.width,t.height,26),r.fill(),r.save(),o(14,14,e,H,19),r.clip();'
    'let k=Math.max(e/w,H/h)*(W.zoom||1),c=w*k,l=h*k;r.imageSmoothingQuality=`high`,'
    'r.drawImage(a,0,0,w,h,W.zoom?14:14+(e-c)/2,14+(H-l)/2,c,l),r.restore()};p(a);'
    'let u=new fu(t);u.colorSpace=to,u.anisotropy=8,n.map=u,n.needsUpdate=!0,i.aspect=t.width/t.height;'
    'if(W.video){let v=document.createElement(`video`);v.muted=!0,v.loop=!0,v.playsInline=!0,v.preload=`none`,'
    'v.setAttribute(`muted`,``),v.setAttribute(`playsinline`,``);'
    # Redraws at most ~30 times a second, and only while Works is showing.
    'let L=0,f=()=>{let T=performance.now();v.readyState>=2&&this.mix.v>.02&&T-L>(this.el.clientWidth<700?66:32)&&(L=T,p(v),u.needsUpdate=!0),v.requestVideoFrameCallback?v.requestVideoFrameCallback(f):setTimeout(f,40)};f();'
    # Only plays while Works is showing and the tab is visible (never in lite mode); it loads the first time it is needed.
    'setInterval(()=>{this.mode===`works`&&!document.hidden&&!window.zzLite?(v.getAttribute(`src`)||(v.src=`./${W.video}`),v.paused&&v.play().catch(()=>{})):v.paused||v.pause()},400)}'
    '},a.src=`./${W.img}`')
s = s[:c0] + new_card + s[c1:]

# ---- 7. The case window --------------------------------------------------------------
# An optional larger hero image (ArtsFest's full poster).
sub('b=`./${e.img}`,x=e.body?', 'b=`./${e.hero??e.img}`,x=e.body?')
# Playground pieces (Gg) show only their image: no title, facts, text, caption or next card.
SOLO = 'Gg.includes(e)'
sub('className:`cs-sheet tx`,children:[', f'className:`cs-sheet tx${{{SOLO}?` cs-solo`:e.case?` cs-case`:``}}`,children:[')
sub('(0,$.jsxs)(`div`,{...m(`59d31868d8f3`),className:`tx-head`,children:[(0,$.jsxs)(`dl`,{...m(`24ddc6d3c7a5`),className:`tx-meta`,"data-in":!0,children:[',
    # A case study lists its own facts in the meta column.
    f'!{SOLO}&&(0,$.jsxs)(`div`,{{...m(`59d31868d8f3`),className:`tx-head`,children:[(0,$.jsxs)(`dl`,{{...m(`24ddc6d3c7a5`),className:`tx-meta`,"data-in":!0,children:'
    'e.facts?e.facts.map(([k,v])=>(0,$.jsxs)(`div`,{children:[(0,$.jsx)(`dt`,{children:k}),...v.map((d,j)=>(0,$.jsx)(`dd`,{children:d},j))]},k)):[')
sub('className:`tx-title`,children:e.title', 'className:`tx-title`,children:e.heading??e.title')
sub('e.desc&&(0,$.jsx)(`p`,{...m(`2122187d8fc4`,`elsewhere`),className:`tx-lead`',
    f'!{SOLO}&&e.desc&&(0,$.jsx)(`p`,{{...m(`2122187d8fc4`,`elsewhere`),className:`tx-lead`')
# A case study's hero and sections are drawn into this slot by the portfolio's renderer (work/case-embed.js).
sub('(0,$.jsxs)(`figure`,{...m(`4aa651bc0f6e`),className:`tx-figure`',
    'e.case?(0,$.jsx)(`div`,{className:`zz-mount`,"data-in":!0,ref:n=>window.zzCase?.(n,e.case)}):(0,$.jsxs)(`figure`,{...m(`4aa651bc0f6e`),className:`tx-figure`')
sub('(0,$.jsxs)(`figcaption`,{...m(`28c1a9ab45e8`,`elsewhere`),children:[e.title,e.year?`, ${e.year}`:``]})',
    f'!{SOLO}&&(0,$.jsxs)(`figcaption`,{{...m(`28c1a9ab45e8`,`elsewhere`),children:[e.title,e.year?`, ${{e.year}}`:``]}})')
sub('x.length>0&&(0,$.jsx)(`div`,{...m(`87d8cbd56d2c`,`elsewhere`),className:`tx-body`',
    f'!{SOLO}&&x.length>0&&(0,$.jsx)(`div`,{{...m(`87d8cbd56d2c`,`elsewhere`),className:`tx-body`')
sub('(0,$.jsxs)(`button`,{...m(`13eb15450893`),className:`cs-next`',
    f'!{SOLO}&&(0,$.jsxs)(`button`,{{...m(`13eb15450893`),className:`cs-next`')

# ---- 9. Shorter job descriptions in the Info card ------------------------------------
JOBS = {
    'redesigning prism collective’s website, building high-fidelity figma prototypes. created a reusable design system and 5+ visual assets to unify the club’s identity across web, social, and print.':
        'redesigning prism collective’s website and a reusable design system that unifies the club’s identity across web, social, and print.',
    'led end-to-end design of story-driven digital outreach reaching 20k+ montreal residents, using community feedback to create brand consistent visuals that drove a 700% engagement increase and connected 200+ families to social services.':
        'led design of digital outreach reaching 20k+ montreal residents, driving a 700% engagement increase and connecting 200+ families to social services.',
    'designed and tested python pipelines to parse 50,000+ keystroke events from raw xml logs into behavioral metrics on how bilingual users type and process language; co-authored research accepted to the 2026 cpa conference.':
        'built python pipelines turning 50,000+ keystroke events into metrics on how bilingual users type; co-authored research accepted to the 2026 cpa conference.',
}
for old, new in JOBS.items():
    sub(f'did:`{old}`', f'did:`{new}`')

# ---- 10. Things I like: guitars in place of soup ----------------------------------------
sub('{src:`likes/soup.webp`,caption:`soup`,alt:`tomato soup with croutons and grilled bread`}',
    '{src:`likes/guitars.webp`,caption:`guitars`,alt:`a yellow electric guitar on a stand beside a red curtain`}')

# ---- 11. The two Z circles on the Info name card are buttons (work/case-embed.js counts the presses) ----
sub('className:`sg-zz`,"aria-hidden":`true`,children:[(0,$.jsx)(`span`,{...m(`9205312d17e4`),className:`bul bul-z1`,children:',
    'className:`sg-zz`,children:[(0,$.jsx)(`span`,{...m(`9205312d17e4`),className:`bul bul-z1`,role:`button`,tabIndex:0,"data-zz":`z1`,"aria-label":`Pink Z`,children:')
sub('className:`bul bul-z2`,children:', 'className:`bul bul-z2`,role:`button`,tabIndex:0,"data-zz":`z2`,"aria-label":`Green Z`,children:')

# ---- 12. Works view: project colours on the cursor, and Zeen front and centre --------------
sub('colorOf(e){return this.colors.get(e)??`#ffffff`}', 'colorOf(e){return e?.color??this.colors.get(e)??`#ffffff`}')
# The first work (Zeen) takes the large spot in the middle of the view; the rest sit smaller around it, drawn
# 20% closer in toward it (so they overlap a little at the corners, Zeen in front).
sub('bigSpot(e,t){let n=[[-18,1.5,-7],[8,-11.5,6],[23,6,-19],[-8,12,-30],[30,-8,-36],[-30,-9,-24]],',
    'bigSpot(e,t){let n=[[0,-7,10],[-20.8,6.6,-6],[20.8,6.6,-6],[19.2,-16.6,-4.4],[24,-7.2,-26.8],[-24,-8.6,-17.2]],')
sub('bigSize(e){return[.82,1,.78,.7,.75,.72][e%6]}', 'bigSize(e){return[1.1,.78,.74,.68,.75,.72][e%6]}')

# ---- 13. The UW CS webring after the x.com handle, bottom right -----------------------------
RING = 'https://cs.uwatering.com/#https://www.zirui.ca/'
webring = ('(0,$.jsxs)(`span`,{className:`zz-webring`,children:['
    f'(0,$.jsx)(`a`,{{href:`{RING}?nav=prev`,"aria-label":`Previous site in the UW CS webring`,children:`←`}}),'
    f'(0,$.jsx)(`a`,{{href:`{RING}`,target:`_blank`,rel:`noreferrer`,className:`zz-crest-link`,"aria-label":`UW CS webring`,title:`UW CS webring`,children:(0,$.jsx)(`span`,{{className:`zz-crest`,"aria-hidden":`true`}})}}),'
    f'(0,$.jsx)(`a`,{{href:`{RING}?nav=next`,"aria-label":`Next site in the UW CS webring`,children:`→`}})]}})')
# The x.com handle loses its trailing arrow; the webring follows it.
sub('e.label,` `,f(`e2ffc48f1d6d`,`↗`)))]})', 'e.label)),' + webring + ']})')

# ---- 14. Light / dark toggle: a bold asterisk, and a bold crescent in dark mode -------------------------------------
# After a sheet of geometric logo marks (2026-11-14): light mode is a chunky six-armed asterisk; dark mode a crescent
# of the same weight (it was the asterisk in a rounded frame, which didn't work). Switching, one spins away and
# shrinks as the other swings in on a springy ease. At rest the asterisk ticks round a sixth of a turn every four
# seconds (with six arms, seamless) and the crescent rocks a little on the same beat (case-window.css). (Before: a
# 5 x 5 pixel sun and moon; before that, a half-filled square and the words "Light Dark".)
TT_ARMS = ','.join(f'(0,$.jsx)(`rect`,{{x:`6.55`,y:`1.3`,width:`2.9`,height:`13.4`,transform:`rotate({a} 8 8)`}})' for a in (0, 60, 120))
# The crescent: a 6.6 circle at the middle with a 5.4 circle 4.2 up and right taken out of it (the path runs along the
# big circle's long arc between the two crossing points, then back along the small one's).
TT = ('(0,$.jsx)(`g`,{className:`zz-tt-mw`,children:(0,$.jsx)(`path`,{className:`zz-tt-m`,d:`M6.89 1.49A6.6 6.6 0 1 0 14.51 9.11A5.4 5.4 0 0 1 6.89 1.49Z`,fill:`currentColor`})}),'
      '(0,$.jsx)(`g`,{className:`zz-tt-spin`,children:(0,$.jsxs)(`g`,{className:`zz-tt-a`,fill:`currentColor`,children:[' + TT_ARMS + ']})})')

sub('children:(0,$.jsxs)(`svg`,{...m(`bbb0f5c93433`),viewBox:`0 0 14 14`,width:`14`,height:`14`,"aria-hidden":`true`,children:[(0,$.jsx)(`rect`,{...m(`480e8dfd63c2`),x:`0.5`,y:`0.5`,width:`13`,height:`13`,fill:`none`,stroke:`currentColor`}),(0,$.jsx)(`path`,{...m(`4a74c637271b`),className:`half`,d:`M0.5 0.5 L13.5 13.5 L0.5 13.5 Z`,fill:`currentColor`})]})})',
    'children:(0,$.jsxs)(`svg`,{className:`zz-tt`,viewBox:`0 0 16 16`,width:`16`,height:`16`,"aria-hidden":`true`,children:['
    + TT + ']})})')

# ---- 15. Flat mode (was "Recruiter mode"): a button beside Light / Dark that switches to the original portfolio (recruiter/) --
# Both sit in one top-right group. Recruiter mode shows everywhere (Info is the landing page); the toggle hides itself outside Playground and Works.
sub('(0,$.jsx)(`button`,{...m(`61c4be3b24e2`),className:`theme-ico',
    '(0,$.jsxs)(`div`,{className:`zz-topright`,children:['
    '(0,$.jsx)(`a`,{className:`zz-recruiter`,href:`recruiter/`,title:`Switch to the flat portfolio`,children:`Flat mode`}),'
    '(0,$.jsx)(`button`,{...m(`61c4be3b24e2`),className:`theme-ico')
sub(']})}),(0,$.jsxs)(`div`,{...m(`e8040b71c573`),className:`corner-bl`',
    ']})})]}),(0,$.jsxs)(`div`,{...m(`e8040b71c573`),className:`corner-bl`')

# ---- 16. Smoother: a lighter render ---------------------------------------------------------
# Draw the 3D scene at no more than 1.5x the screen's resolution (it was up to 1.75x).
sub('this.renderer.setPixelRatio(i?.5:Math.min(window.devicePixelRatio,r?1.5:1.75))',
    'this.renderer.setPixelRatio(i?.5:Math.min(window.devicePixelRatio,r?1.25:1.5))')
# While a case study or pop-up is open over a landed camera, the scene behind it stops drawing once its dimming
# has settled (0.7s): the last frame stays on screen, still. Its clock is held too, so nothing jumps on closing.
# A resize clears the canvas, so one frame is drawn then.
sub('loop=()=>{if(this.disposed)return;this.raf=requestAnimationFrame(this.loop);',
    'loop=()=>{if(this.disposed)return;this.raf=requestAnimationFrame(this.loop);'
    # Lite mode on Info: a saved loop of the scene plays instead (work/perf.js sets zzHold), so nothing is drawn.
    'if(this.zzHold&&!this.flying&&!this.zzDirty){this.clock.elapsedTime-=this.clock.getDelta();return}'
    'if(this.focus&&!this.flying&&document.querySelector(`.case.is-open`)){let T=performance.now();this.zzOpenAt||=T;'
    'if(T-this.zzOpenAt>700&&!this.zzDirty){this.clock.elapsedTime-=this.clock.getDelta();return}}else this.zzOpenAt=0;this.zzDirty=!1;'
    # On phones the scene idles at half rate (every other frame) until it is touched, dragged or flying.
    'if(this.el.clientWidth<700&&!this.flying&&!this.nav.drag&&!this.nav.pinch&&!this.grab.active&&(this.zzHalf=!this.zzHalf))return;')

# ---- 17. Things I like: the arrow beside the caption is a "next photo" button ------------------
sub('className:`sg-picarrow`,"aria-hidden":`true`,children:',
    'className:`sg-picarrow`,role:`button`,tabIndex:c===`projects`?-1:0,"aria-label":`Next photo`,'
    'onClick:e=>{e.stopPropagation(),O((w+1)%Bg.length)},'
    'onKeyDown:e=>{(e.key===`Enter`||e.key===` `)&&(e.preventDefault(),O((w+1)%Bg.length))},children:')

# ---- 18. Things I like opens on photo 8, "food" ---------------------------------------------
FIRST = 7  # zero-based
sub('[w,T]=(0,l.useState)(0),[E,D]=(0,l.useState)([0])', f'[w,T]=(0,l.useState)({FIRST}),[E,D]=(0,l.useState)([{FIRST}])')

# ---- 19. Opening a card: the camera centres it first, then the window slides up -----------------
sub('this.flight=Mi.to(d,{t:1,duration:this.reduced?.01:1.3,ease:`power3.inOut`',
    'this.flight=Mi.to(d,{t:1,duration:this.reduced?.01:1.05,ease:`power3.inOut`')
sub('!f&&d.t>.7&&(f=!0,this.ev.onOpen(e))', '!f&&d.t>.97&&(f=!0,this.ev.onOpen(e))')

# ---- 20. Lighter: thumbnails for lattice textures, fewer pixel loops --------------------------
sub('c.src=`./${r.img}`,o.userData.node=s', 'c.src=`./${r.thumb||r.img}`,o.userData.node=s')
# (2026-11-14: fewer again, 320 to 190 and 140 to 90 on phones; the field had become cluttered.)
sub('this.glyphs=new Pg(r?200:420,r_)', 'this.glyphs=new Pg(r?90:190,r_)')

# ---- 21. Touch drags turn the view further -------------------------------------------------------
# The drag is scaled by the screen's height, so on a tall, narrow phone a full-width swipe barely turned it.
# 7.5x a mouse drag (it was 2.5x; tripled on 2026-11-13).
TOUCH_GAIN = 7.5
sub('let t=e.clientX-this.drag.x,n=e.clientY-this.drag.y;',
    f'let k=e.pointerType===`touch`?{TOUCH_GAIN}:1,t=(e.clientX-this.drag.x)*k,n=(e.clientY-this.drag.y)*k;')

# ---- 22. Info panels on phones: a faint tilt, and flat again when the finger lifts ------------------
# The panels lean toward the pointer (up to 14 degrees, lifting 5%). On phones that was a touch point that
# stayed put after the finger left, so a panel sat tilted. There the lean is 15% as strong, and a lifted or
# scrolling finger lets the panels settle flat.
PHONE_TILT = .15
sub('T=e=>{b=e.clientX,x=e.clientY},E=()=>{b=-1e4,x=-1e4};window.addEventListener(`pointermove`,T),document.addEventListener(`pointerleave`,E);let D=()=>{',
    'T=e=>{b=e.clientX,x=e.clientY},E=()=>{b=-1e4,x=-1e4},zzU=e=>{e.pointerType!==`mouse`&&E()},zzP=matchMedia(`(max-width: 640px)`);'
    'window.addEventListener(`pointermove`,T),document.addEventListener(`pointerleave`,E),window.addEventListener(`pointerup`,zzU),window.addEventListener(`pointercancel`,zzU);'
    f'let D=()=>{{let zzK=zzP.matches?{PHONE_TILT}:1;')
sub('o.ry+=(i*14-o.ry)*.1,o.rx+=(-a*12-o.rx)*.1,', 'o.ry+=(i*14*zzK-o.ry)*.1,o.rx+=(-a*12*zzK-o.rx)*.1,')
sub('o.lift+=(+!!s-o.lift)*.14,', 'o.lift+=(+!!s*zzK-o.lift)*.14,')
sub('cancelAnimationFrame(S),window.removeEventListener(`pointermove`,T),document.removeEventListener(`pointerleave`,E),',
    'cancelAnimationFrame(S),window.removeEventListener(`pointermove`,T),document.removeEventListener(`pointerleave`,E),window.removeEventListener(`pointerup`,zzU),window.removeEventListener(`pointercancel`,zzU),')

# ---- 23. The scene is reachable as window.zzScene (performance checks, lite mode, the phone dial) ----
sub('constructor(e,t,n){this.el=e,this.ev=t,this.reduced=n;', 'constructor(e,t,n){this.el=e,this.ev=t,this.reduced=n,window.zzScene=this;')

# ---- 24. Equivalent savings (the audit's Category A): same pixels, less work --------------------------
sub('resize=()=>{let e=this.el.clientWidth,', 'resize=()=>{this.zzDirty=!0;let e=this.el.clientWidth,')
# The environment-map generator and its source room are freed once the map exists (the map itself stays).
sub('let a=new zf(this.renderer);this.scene.environment=a.fromScene(new hg,.04).texture,',
    'let a=new zf(this.renderer),zzRoom=new hg;this.scene.environment=a.fromScene(zzRoom,.04).texture,a.dispose(),zzRoom.dispose(),')
# Route and card-link lines rewrote their points by creating two new GPU buffers per line each update (about 900
# a second). zzLine writes the same numbers, computed the same way, into the buffers they already have.
sub('t_=5,n_=8,r_=70,',
    'zzLine=window.zzLine=(L,l)=>{let g=L.geometry,S=g.attributes.instanceStart,E=g.attributes.instanceDistanceStart,n=l.length-3;'
    'if(!S||!E||S.data.array.length!==2*n||E.data.array.length!==2*S.count){g.setPositions(l),L.computeLineDistances();return}'
    'let p=S.data.array;for(let i=0;i<n;i+=3)p[2*i]=l[i],p[2*i+1]=l[i+1],p[2*i+2]=l[i+2],p[2*i+3]=l[i+3],p[2*i+4]=l[i+4],p[2*i+5]=l[i+5];'
    'S.data.needsUpdate=!0,g.computeBoundingBox(),g.computeBoundingSphere();'
    'let D=new Float32Array(2*S.count),o=g.attributes.instanceEnd;'
    'for(let i=0,j=0,c=S.count;i<c;i++,j+=2){let x=S.getX(i)-o.getX(i),y=S.getY(i)-o.getY(i),z=S.getZ(i)-o.getZ(i);D[j]=j===0?0:D[j-1],D[j+1]=D[j]+Math.sqrt(x*x+y*y+z*z)}'
    'E.data.array.set(D),E.data.needsUpdate=!0},t_=5,n_=8,r_=70,')
sub('a.line.geometry.setPositions(l),a.line.computeLineDistances()}', 'zzLine(a.line,l)}')
sub('p.line.geometry.setPositions(_),p.thin.geometry.setPositions(v),p.line.computeLineDistances(),p.thin.computeLineDistances();',
    'zzLine(p.line,_),zzLine(p.thin,v);')
# The camera's look-ahead point was rebuilt for every work on every frame; it is the same for all of them.
sub('this.nodes.forEach((r,i)=>{let a=+(r===this.hovered||r===this.grab.node||r===this.focus);',
    'let zzAhead=this.camera.position.clone().add(new J(0,0,-18).applyQuaternion(this.camera.quaternion));this.nodes.forEach((r,i)=>{let a=+(r===this.hovered||r===this.grab.node||r===this.focus);')
sub('let p=this.camera.position.clone().add(new J(0,0,-18).applyQuaternion(this.camera.quaternion)),m=', 'let p=zzAhead,m=')
# updateTiles built a text key of every position each frame that nothing reads.
sub("t=``,n=this.w4,r=Math.cos(n)", "n=this.w4,r=Math.cos(n)")
sub("if(s===this.grab.node||s===this.focus){t+=`g`;continue}", "if(s===this.grab.node||s===this.focus)continue;")
sub("u+a_*Math.round((e.z-u)/a_)),t+=s.rest.x+`,`+s.rest.y+`,`+s.rest.z+`;`}return t}", "u+a_*Math.round((e.z-u)/a_))}}")
sub('new J,this.big.forEach(', 'this.big.forEach(')

# ---- 25. Lite mode for slow devices (work/perf.js decides; window.zzLite) ----------------------------
# zzLighten: 1x resolution, no glitch pass, 2 in 5 of the floating pixel loops, a sparser lattice; then (below)
# half-rate idling and slower route redraws. Built light from the start when perf.js already knows.
sub('dispose(){this.disposed=!0,cancelAnimationFrame(this.raf)',
    'zzLighten(){if(this.zzLit)return;this.zzLit=!0;'
    'let p=Math.min(this.renderer.getPixelRatio(),1);this.renderer.setPixelRatio(p),this.composer.setPixelRatio(p),this.resize(),this.zzDirty=!0;'
    'this.glitch.enabled=!1;'
    'let g=this.glyphs;g.items=g.items.filter((e,i)=>i%5<2||(g.group.remove(e.s),e.s.material.dispose(),!1));'
    'let o=this.scene.children.find(e=>e.material===this.latMat),u=this.latMat.uniforms.uInk.value.clone();'
    'this.latMat=this.buildLattice(),this.latMat.uniforms.uInk.value.copy(u),o&&(this.scene.remove(o),o.geometry.dispose(),o.material.dispose())}'
    'dispose(){this.disposed=!0,cancelAnimationFrame(this.raf)')
sub('o.addEventListener(`pointerleave`,()=>{this.pointer.x=-1e4}),this.loop()}buildLattice(){',
    'o.addEventListener(`pointerleave`,()=>{this.pointer.x=-1e4}),window.zzLite&&this.zzLighten(),this.loop()}buildLattice(){')
sub('let l=i();if(i()<.55)continue;', 'let l=i();if(i()<(this.zzLit?.8:.55))continue;')
sub('if(this.el.clientWidth<700&&!this.flying&&!this.nav.drag', 'if((this.el.clientWidth<700||this.zzLit)&&!this.flying&&!this.nav.drag')
sub('(this.frameN=(this.frameN+1)%2)==0&&this.updateRoutes(t,n)', '(this.frameN=(this.frameN+1)%(this.zzLit?4:2))==0&&this.updateRoutes(t,n)')

# ---- 26. Phones: the dial steps from work to work ---------------------------------------------------
# On a phone the right-edge dial no longer turns the lattice: every 6 ticks moves to the next (finger up) or
# previous work in the current view (Works' cards, or Playground's pieces). The camera keeps its angle and glides
# (a critically damped spring on where it looks and how far back it sits) until that work fills about half the
# screen. A new step only redirects the glide, so a quick run of steps is one smooth motion, never a cut.
STEP_TICKS = 6
sub('dispose(){this.disposed=!0,cancelAnimationFrame(this.raf)',
    f'zzStep(e){{let k=Math.round(e/(v_*Math.PI/180)/{STEP_TICKS});if(this.zzK===void 0){{this.zzK=k;return}}if(this.zzMode!==this.mode)this.zzMode=this.mode,this.zzI=-1;'
    'let d=k-this.zzK;if(!d)return;this.zzK=k;let L=this.activeNodes(),n=L.length;if(!n)return;'
    'this.zzI=((this.zzI+d)%n+n)%n,this.zzCenter(L[this.zzI])}'
    'zzCenter(t){if(this.focus||!t)return;this.flight&&(this.flight.kill(),this.flight=null,this.flying=!1);'
    'let F=Math.tan(this.camera.fov*Math.PI/360)*2,c=Math.max(t.sprite.scale.x/(.5*F*this.camera.aspect),t.sprite.scale.y/(.48*F)),G=this.zzGlide;'
    'this.zzGlide={node:t,dist:c,v:G?.v??new J,dv:G?.dv??0,p:G?.p??this.nav.target.clone(),q:G?.q??this.nav.dist},this.nav.stop()}'
    # One step of the glide, run each frame before the controls place the camera.
    'zzGlideStep(e){let G=this.zzGlide;if(!G)return;if(this.nav.drag||this.nav.pinch||this.focus||this.flying){this.zzGlide=null;return}'
    # The aim point and distance ease toward the work first (0.15s), so every move starts on a soft S-curve.
    'let t=G.node,T=t.rest.clone().addScaledVector(new J(0,1,0).applyQuaternion(this.nav.q),t.sprite.scale.y*.56),s=1-Math.exp(-e/.15);'
    'G.p.lerp(T,s),G.q+=(G.dist-G.q)*s;let A=G.p.clone().sub(this.nav.target),k=24,c=2*Math.sqrt(k),D=G.q-this.nav.dist;'
    'G.v.addScaledVector(A,k*e).multiplyScalar(Math.max(0,1-c*e)),this.nav.target.addScaledVector(G.v,e),'
    'G.dv=(G.dv+k*D*e)*Math.max(0,1-c*e),this.nav.dist+=G.dv*e;'
        # Done once it is within the card's own gentle float (about 0.3) and nearly still; the free camera takes over.
    'T.distanceToSquared(this.nav.target)<.09&&G.v.lengthSq()<.25&&Math.abs(G.dist-this.nav.dist)<.1&&Math.abs(G.dv)<.1&&(this.zzGlide=null)}'
    'dispose(){this.disposed=!0,cancelAnimationFrame(this.raf)')
sub('this.flying||this.nav.update(e);', 'this.flying||(this.zzGlideStep(e),this.nav.update(e));')
# A glide counts as motion: full frame rate on phones until it settles.
sub('if((this.el.clientWidth<700||this.zzLit)&&!this.flying&&!this.nav.drag', 'if((this.el.clientWidth<700||this.zzLit)&&!this.flying&&!this.zzGlide&&!this.nav.drag')
sub('onAngle:e=>{t.current&&(t.current.w4=e)}', 'onAngle:e=>{t.current&&(window.innerWidth<700?t.current.zzStep(e):t.current.w4=e)}')

# ---- 27. The dial, like Apple's pickers ---------------------------------------------------------------
# The bars stay level while scrolling (each bar's left end used to dip or rise with the speed, up to 10px). The bars
# away from the centre sit further back (about half their old opacity), and a bar passing through the centre grows
# into the centre bar itself: its length, thickness and opacity, easing over one bar's spacing either side. Every
# bar has round ends. The
# centre bar's size comes from --zz-bar-w / --zz-bar-h on .dial (case-window.css), read whenever the dial is sized.
sub('x=()=>{let n=e.getBoundingClientRect(),r=Math.min(2,window.devicePixelRatio||1);',
    'x=()=>{let zs=getComputedStyle(e);t.zzW=parseFloat(zs.getPropertyValue(`--zz-bar-w`))||32,t.zzH=parseFloat(zs.getPropertyValue(`--zz-bar-h`))||2;'
    'let n=e.getBoundingClientRect(),r=Math.min(2,window.devicePixelRatio||1);')
# Inside the drawing loop `t` is each bar's height, so the canvas is kept as Z first.
sub('S=()=>{let e=t.width/Math.min(2,window.devicePixelRatio||1)', 'S=()=>{let Z=t,e=t.width/Math.min(2,window.devicePixelRatio||1)')
sub('p=(s?14:8)*(1+(.55+g*.9)*l)+g*2,m=f*(s?.85:.3+.35*l*g+.15*l),h=Math.max(-10,Math.min(10,y*.9))*(.4+.6*l);'
    'a.strokeStyle=`rgba(${r},${m.toFixed(3)})`,a.lineWidth=s?1.25:1,a.beginPath(),a.moveTo(o-p,t+h),a.lineTo(o,t),a.stroke()',
    'k=Math.max(0,1-Math.abs(t-i)/__),q=k*k*(3-2*k),P=(s?14:8)*(1+(.3+g*.45)*l)+g*2,M=f*(s?.42:.13+.15*l*g+.07*l),L=s?1.25:1,'
    # Round ends, drawn half a thickness in from each end so every bar keeps its exact length.
    # The centre bar is always the long one, but only thick and strong while the dial is pointed at, near the pointer
    # or dragged (g, which eases between 0 and 1); otherwise it has the other bars' thickness and opacity.
    # ...and, as it thickens, it takes the cursor's own colour (its tint, window.zzCur, shared by info-swipe.js; with no
    # tint the cursor is the ink colour, which the bar already is).
    'W=L+(Z.zzH-L)*q*g,N=P+(Z.zzW-P)*q,m=M+(.95-M)*q*g,Y=q*g,C3=window.zzCur,R=Y>0&&C3?r.split(`,`).map((v,i)=>Math.round(+v+(C3[i]-v)*Y)).join(`,`):r;'
    'a.strokeStyle=`rgba(${R},${m.toFixed(3)})`,a.lineWidth=W,a.lineCap=`round`,'
    'a.beginPath(),a.moveTo(o-N+W/2,t),a.lineTo(o-W/2,t),a.stroke()')

# ---- 28. Info opens further back ----------------------------------------------------------------------
# The works' cloud reaches about 24 units out; from 34 away it spilled off the screen. Info now sits 48 away
# (58 on phones, whose narrow screens show less across). bg/info-*.mp4 (lite mode) are rendered from the same spots.
INFO_DIST, INFO_DIST_PHONE = 48, 58
# The cloud sits a little right of centre on wide screens, between the panels: 3.5 units (it was 4.5).
sub('t=this.el.clientWidth>820?4.5:0', 't=this.el.clientWidth>820?3.5:0')
sub('Mi.to(this.nav,{dist:34,duration:this.reduced?.01:1.4,ease:`power3.inOut`,overwrite:!0})',
    f'Mi.to(this.nav,{{dist:this.el.clientWidth<700?{INFO_DIST_PHONE}:{INFO_DIST},duration:this.reduced?.01:1.4,ease:`power3.inOut`,overwrite:!0}})')

# ---- 29. From the loading screen into the 3D view -----------------------------------------------------------
# While the loading screen is up (<html class="zz-booting">, set by src/loader.html) the scene holds its entrance at
# zzIn = 0. When the loader finishes it fires "zz:booted" and zzIn eases to 1 over 1.9s: the works come in from three
# times further out, contracting into their cloud as they fade in, and the floating pixel loops grow from nothing
# with a slight overshoot, each a little after the last.
sub('constructor(e,t,n){this.el=e,this.ev=t,this.reduced=n,window.zzScene=this;',
    'constructor(e,t,n){this.el=e,this.ev=t,this.reduced=n,window.zzScene=this;'
    'this.zzIn=document.documentElement.classList.contains(`zz-booting`)?0:1;'
    'addEventListener(`zz:booted`,()=>{Mi.to(this,{zzIn:1,duration:this.reduced?.01:1.9,ease:`power3.out`})},{once:!0});')
sub('s.set(p*_*v,m*_*v,h*_*v).add(this.cloudCenter)', 's.set(p*_*v,m*_*v,h*_*v).multiplyScalar(1+2*(1-this.zzIn)**2).add(this.cloudCenter)')
sub('r.sprite.material.opacity=(this.focus&&this.focus!==r?.3:1)*(r===this.focus||r===this.grab.node?1:h)*g',
    'r.sprite.material.opacity=(this.focus&&this.focus!==r?.3:1)*(r===this.focus||r===this.grab.node?1:h)*g*Math.min(1,this.zzIn*1.5)')
# Each pixel loop keeps its size (b) and a start offset (dl) taken from its place in the list, so no random draw moves.
sub('this.items.push({s:i,p:s,ph:n()*6.28,sp:.2+n()*.6})', 'this.items.push({s:i,p:s,ph:n()*6.28,sp:.2+n()*.6,b:o,dl:this.items.length*.618%1*.55,i:this.items.length})')
sub('for(let r of this.items)r.s.position.set(o(r.p.x+Math.sin(e*.2*r.sp+r.ph)*1.5*n,t.x),o(r.p.y+e*.25*r.sp*n,t.y),o(r.p.z+Math.cos(e*.17*r.sp+r.ph)*1.5*n,t.z))}}',
    # (Section 37: a loop whose texture isn't drawn yet stays hidden, and grows in over 0.45s once it is, from ra.)
    'let k=this.zzGrow??1,T=this.zzThin;for(let r of this.items){if(!r.s.material.map.zzReady){r.s.visible=!1;continue}r.ra??=e;'
    'r.s.position.set(o(r.p.x+Math.sin(e*.2*r.sp+r.ph)*1.5*n,t.x),o(r.p.y+e*.25*r.sp*n,t.y),o(r.p.z+Math.cos(e*.17*r.sp+r.ph)*1.5*n,t.z));'
    # In Works (zzThin) two in three of them shrink away and come back when Works is left (th, about 0.2s each way).
    'let h=r.th??1,g=T&&r.i%3?0:1;h+=(g-h)*.08;Math.abs(g-h)<.003&&(h=g);'
    'if(r.zg!==1||h!==r.th){let q=Math.min(1,Math.max(0,(k-r.dl)/.45),Math.max(0,(e-r.ra)/.45)),w=q<1?1+2.70158*(q-1)**3+1.70158*(q-1)**2:1;r.s.scale.set(r.b*w*h,r.b*w*h,1),r.s.visible=h>.003&&q>0,r.zg=q<1?q:1}r.th=h}}}')
sub('this.glyphs.update(t,r,n)', '(this.glyphs.zzGrow=this.zzIn,this.glyphs.zzThin=this.mode===`works`,this.glyphs.update(t,r,n))')
# The Info cards' own entrance (sections rising, the name card unfolding) waits for the loader instead of playing
# underneath it.
sub('.to(s,{"--unf":`0deg`,duration:.3,ease:`sine.out`}));let l=new Map',
    '.to(s,{"--unf":`0deg`,duration:.3,ease:`sine.out`}));'
    'document.documentElement.classList.contains(`zz-booting`)&&(o.forEach(e=>e.pause(0)),addEventListener(`zz:booted`,()=>o.forEach(e=>e.restart(!0)),{once:!0}));'
    'let l=new Map')

# ---- 30. Zooming out of Works opens Playground; zooming well into Playground opens Works --------------------------
# Works rests 37 units back (c_ to l_). A pinch or ctrl-scroll out that will carry the camera past twice that,
# counting the zoom's own momentum (each frame adds zoomVel, which keeps 90% of itself, so it travels about
# e^(10 zoomVel) further), switches to Playground just as its nav button does. So a quick flick goes over at once
# and a slow zoom when it gets there. The camera stays where it is, so the zoom carries on into Playground's field.
# On phones the dial may have glided in to a card further back than 37; the threshold counts from there instead.
sub('this.zzGlide={node:t,dist:c,', 'this.zzSeen=c,this.zzGlide={node:t,dist:c,')
sub('this.flying||(this.zzGlideStep(e),this.nav.update(e));', 'this.flying||(this.zzGlideStep(e),this.nav.update(e),this.zzOut(e));')
# The nav button re-centres the camera's orbit on a point 6 units ahead and stops any zoom (the camera itself doesn't
# move). Done mid-pinch that would stall the zoom and make the rest of it 8 times slower, so the orbit point and
# zoom speed are put back as they were; once the zoom has come to rest, the orbit moves to 6 ahead as the button
# would have, and Playground handles as it always does.
#
# The other way: in Playground, one continuous zoom in (pinch or ctrl-scroll; a pause over 0.25s or any zoom out
# starts the count again) that adds up to 5 times closer opens Works. 5x in one go is a deliberate push (about a
# 170px spread of two fingers on a phone); zooming in to look at a piece stays well short of it.
#
# Works then appears where the camera already is, with no flight: the whole Works layout is anchored (zzW, applied in
# bigSpot) so that from the camera's current place and angle it is framed exactly as Works' own starting view frames
# it, and the camera's orbit point is set to match. The cards fade in, grow from 70% and rise into place with the
# usual mode crossfade, without the glitch burst (zzQuiet). For a second after, zooming in further is ignored and the
# camera can't come closer than Works' own distance, so the works always arrive at their usual size.
# Works' nav button (and recentring) still lead to the usual Works view: the button resets the anchor and flies home.
ZOOM_IN_TO_WORKS = 5
# How far out (times Works' resting distance) leaves Works. 1.5 was easy to cross by accident (2026-11-14); the camera can't
# go past 90 units, so the line never sits further out than 86.
ZOOM_OUT_OF_WORKS = 2
sub('return t.set(o*Math.cos(a)-s*Math.sin(a),r[1]+Math.sin(i*.26+e*1.3)*.5,o*Math.sin(a)+s*Math.cos(a)),t}bigSize',
    'return t.set(o*Math.cos(a)-s*Math.sin(a),r[1]+Math.sin(i*.26+e*1.3)*.5,o*Math.sin(a)+s*Math.cos(a)),this.zzW&&t.applyMatrix4(this.zzW),t}bigSize')
# The cards' float and their rise as they fade in follow the anchored layout's up, not the world's.
sub('r.sprite.position.set(s.x,s.y+c-(1-i)*6,s.z)',
    'let K=c-(1-i)*6,U=this.zzU;U?r.sprite.position.set(s.x+U.x*K,s.y+U.y*K,s.z+U.z*K):r.sprite.position.set(s.x,s.y+K,s.z)')
sub('burst(e){this.reduced||(this.glitchAmt=Math.max(this.glitchAmt,e))}',
    'burst(e){this.reduced||performance.now()-(this.zzQuiet||0)<600||(this.glitchAmt=Math.max(this.glitchAmt,e))}')
sub('recenter(){this.mode===`works`?this.flyTo(c_,l_):this.flyTo(o_,s_)}',
    'recenter(){this.mode===`works`?this.flyTo(this.zzW?c_.clone().applyMatrix4(this.zzW):c_,this.zzW?l_.clone().applyMatrix4(this.zzW):l_):this.flyTo(o_,s_)}')
sub('e===`works`&&this.flyTo(c_,l_))}', 'e===`works`&&(performance.now()-(this.zzNoFly||0)<500||(this.zzW=this.zzU=null,this.flyTo(c_,l_))))}')
# The controls stamp each zoom input (zzZt), so the count runs only while the fingers are zooming (and a quarter
# second after): two separate pinches with a pause between never add up, even while the first one's momentum runs on.
sub('if(e.ctrlKey){this.zoomVel+=', 'if(e.ctrlKey){this.zzZt=performance.now(),this.zoomVel+=')
sub('this.zoomVel+=(this.pinch.d-n)*.0012,', 'this.zzZt=performance.now(),this.zoomVel+=(this.pinch.d-n)*.0012,')
sub('dispose(){this.disposed=!0,cancelAnimationFrame(this.raf)',
    'zzOut(e){let N=this.nav,T=performance.now(),A=this.zzPush||(this.zzPush={L:0});'
    # The second after Works appears: no zooming in past its own distance.
    'if(T-(this.zzCalm||0)<1000&&this.mode===`works`){N.zoomVel<0&&(N.zoomVel=0);let h=c_.distanceTo(l_);N.dist<h&&(N.dist=h)}'
    # Into Works.
    'if(this.mode===`playground`&&!N.locked&&!this.focus&&!this.zzGlide&&!document.querySelector(`.case.is-open`)){'
    'let z=N.zoomVel;T-(N.zzZt||0)>250||z>1e-4?A.L=0:z<-1e-4&&(A.L+=-z*Math.min(1,(e||1/60)*60));'
    f'if(A.L>Math.log({ZOOM_IN_TO_WORKS})&&T-(this.zzOutT||0)>600){{A.L=0,this.zzOutT=T,this.zzRepivot=0,this.zzNoFly=this.zzQuiet=this.zzCalm=T;'
    'let P=this.camera.position.clone(),Q=N.q.clone(),R=Q.clone().multiply(new Go().setFromRotationMatrix(new ms().lookAt(c_,l_,new J(0,1,0))).invert()),h=c_.distanceTo(l_);'
    'this.zzW=new ms().makeTranslation(P.x,P.y,P.z).multiply(new ms().makeRotationFromQuaternion(R)).multiply(new ms().makeTranslation(-c_.x,-c_.y,-c_.z)),this.zzU=new J(0,1,0).applyQuaternion(R);'
    'document.querySelector(`.c-nav [data-showcase="nav-works"]`)?.click();'
    'N.stop(),N.q.copy(Q),N.target.copy(P).addScaledVector(new J(0,0,-1).applyQuaternion(Q),h),N.dist=h;return}'
    '}else A.L=0;'
    # Playground's usual orbit once the zoom has settled.
    'if(this.zzRepivot&&this.mode===`playground`&&!this.focus&&!N.pinch&&!N.drag&&Math.abs(N.zoomVel)<2e-4&&N.rotVel.lengthSq()<1e-6&&N.panVel.lengthSq()<1e-6){'
    'this.zzRepivot=0;let f=new J(0,0,-1).applyQuaternion(N.q),p=this.camera.position.clone();N.setFrom(p,p.clone().addScaledVector(f,6),new J(0,1,0).applyQuaternion(N.q))}'
    # Out of Works.
    'if(this.zzOutMode!==this.mode)this.zzOutMode=this.mode,this.zzSeen=0;'
    'if(this.mode!==`works`||this.focus||this.zzGlide||N.locked||document.querySelector(`.case.is-open`))return;'
    'let h=Math.max(c_.distanceTo(l_),this.zzSeen||0);'
    f'if(N.dist*Math.exp(10*Math.max(0,N.zoomVel))>Math.min(h*{ZOOM_OUT_OF_WORKS},N.maxDist-4)&&T-(this.zzOutT||0)>1500){{this.zzOutT=T,A.L=0;'
    'let p=N.target.clone(),d=N.dist,z=N.zoomVel,q=N.q.clone();document.querySelector(`.c-nav [data-showcase="nav-playground"]`)?.click();'
    'N.target.copy(p),N.dist=d,N.zoomVel=z,N.q.copy(q),this.zzRepivot=1}}'
    'dispose(){this.disposed=!0,cancelAnimationFrame(this.raf)')

# ---- 31. The name on the Info card has no entrance of its own ------------------------------------------------------
# Its letters used to rise one by one with a fade; now the name is simply there with its card (which still unfolds).
sub(',Mi.fromTo(a,{yPercent:105,autoAlpha:0},{yPercent:0,autoAlpha:1,duration:n?0:.7,stagger:.04,ease:`expo.out`,delay:n?0:.75})]', ']')

# ---- 32. More floating pixel loops: flat colour tiles after the reference sheet ------------------------------------
# src/tiles.js adds 12 tiles (spinning square spiral, play, sliding checkerboard, brick rows, tunnel, beating heart,
# bobbing question mark, exclamation, marching chevrons, breathing diamond, nudging arrow, scrolling bands) to the
# loops' list, then 15 smooth shapes after a second set of references (signage arrow, scalloped badge, VHS stripes,
# halftone wave, four-leaf blob, plus in a disc, sunset disc, burst, slot switch, U-turn route, knobbly cross, four
# arrows closing in, wire globe, six dots, breathing rounded squares; the daisy was taken out, 2026-11-14). Each makes
# as many textures as it has colourways (zzN, 1 or 2) instead of the usual 4 random ones: 34 in all.
SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
shapes = open(os.path.join(SRC_DIR, 'shapes.js')).read()  # the smooth shapes, shared with the loading screen
tiles = shapes + '\n' + open(os.path.join(SRC_DIR, 'tiles.js')).read()
assert '`' not in tiles
sub('Eg=[`#0101fd`,`#fefe02`,`#fe01fd`,`#01fe02`,`#00ffff`];function Dg(e)',
    'Eg=[`#0101fd`,`#fefe02`,`#fe01fd`,`#01fe02`,`#00ffff`];\n' + tiles + '\nfunction Dg(e)')
sub('Tg.forEach(e=>{for(let t=0;t<4;t++){', 'Tg.forEach(e=>{for(let t=0;t<(e.zzN||4);t++){')
# Some of the original loops change (2026-11-14). Taken out: the smooth fading circles, the block of random characters,
# the wave of ~ - = + * # characters (both too recognisably "ASCII art") and the pixel concentric rings (cut flat where
# they meet the square's edges); those last three sit together in the list, so they go as one run. Redrawn: the arrow
# in a dotted corner: its shaft was a one-pixel diagonal whose pixels only touched at their corners, so it broke up.
# Now the head and the shaft are both two pixels thick, the dotted corner is 2 x 2 dots at the same spacing, and the
# arrow eases out of the corner and back instead of moving at a steady pace.
sub('(e,t,n,r,i)=>{for(let e=0;e<4;e++){let a=(e*16+t*4)%64+2;r.strokeStyle=n[e%n.length],r.lineWidth=5,r.globalAlpha=1-a/70,r.beginPath(),r.arc(i+xg/2,xg/2,a,0,Math.PI*2),r.stroke()}r.globalAlpha=1},', '')
RUN_START, RUN_END = '(e,t,n,r,i)=>{let a=Cg(300+t*7);', '(e,t,n)=>{let r=t%4;for(let t=0;t<yg;t++)'
assert s.count(RUN_START) == 1 and s.count(RUN_END) == 1
run = s[s.index(RUN_START):s.index(RUN_END)]
assert run.count('fillText') == 2 and run.count('=>') == 3 and 'o=Math.round(a/2)' in run, run
sub(run, '')
sub('(e,t,n)=>{let r=[0,1,2,3,3,2,1,0][t],i=4-r,a=4-r;for(let t=0;t<6;t++)e(i+t,a,n[0]),e(i,a+t,n[0]);for(let t=1;t<9;t++)e(i+t,a+t,n[0]);for(let t=0;t<yg;t++)t%2==0&&(e(t,15,n[1]),e(15,t,n[1]))}',
    '(e,t,n)=>{let o=3-[0,0,1,2,2,2,1,0][t];'
    'for(let k=0;k<6;k++)e(o+k,o,n[0]),e(o+k,o+1,n[0]),e(o,o+k,n[0]),e(o+1,o+k,n[0]);'
    'for(let k=0;k<8;k++)e(o+k,o+k,n[0]),e(o+k+1,o+k,n[0]),e(o+k,o+k+1,n[0]),e(o+k+1,o+k+1,n[0]);'
    'for(let k=2;k<=14;k+=4)for(let j=0;j<2;j++)for(let m=0;m<2;m++)e(k+j,14+m,n[1]),e(14+m,k+j,n[1])}')

# ---- 33. Each Playground piece's little marker sits off one of the piece's edges, and its lines meet it ----------
# It used to sit just under the middle of every picture. Now each piece has its own spot, taken from its id so it is
# the same every visit: off the bottom, top, left or right edge, 12-88% of the way along, a tenth of the picture's
# height out from the border. It follows the picture's size and its slight tilt when pointed at. (The picture is
# anchored 6% of its height below its bottom edge, centred: center (.5, -.06).) The coloured lines between pieces
# run to the markers (they ran to the pictures' anchors, which is where the markers used to be).
sub('r.marker?.position.copy(r.sprite.position),r.sprite.scale.set(',
    'if(r.marker){let k=r.zzMk;if(!k){let h=0;for(let ch of String(r.work.id))h=h*31+ch.charCodeAt(0)|0;'
    'h=Math.imul(h^h>>>16,73244475),h=Math.imul(h^h>>>16,73244475),h=(h^h>>>16)>>>0;k=r.zzMk={side:h&3,t:.12+(h>>>2)%1000/1000*.76}}'
    'let w=u*r.aspect,g=.1*u,X=k.side<2?(k.t-.5)*w:k.side===2?-.5*w-g:.5*w+g,Y=k.side<2?(k.side?1.06*u+g:.06*u-g):(.06+k.t)*u,c0=Math.cos(d.rotation),s0=Math.sin(d.rotation);'
    'r.marker.position.copy(r.sprite.position).add(new J(X*c0-Y*s0,X*s0+Y*c0,0).applyQuaternion(this.camera.quaternion))}'
    'r.sprite.scale.set(')
sub('n.copy(this.currentPos(a.a)).add(a.off),r.copy(this.currentPos(a.b)).add(a.off);',
    'n.copy(a.a.marker?a.a.marker.position:this.currentPos(a.a)).add(a.off),r.copy(a.b.marker?a.b.marker.position:this.currentPos(a.b)).add(a.off);')
# Every marker stands upright (2026-11-14); three in ten used to be turned 45 degrees, so square ones read as diamonds.
# The random draw that chose the turn is still made, so each marker keeps the shape and size it had.
sub('t.material.rotation=o()<.3?Math.PI/4:0,', 't.material.rotation=(o(),0),')

# ---- 34. A mouse wheel zooms; a trackpad's two-finger scroll still turns the view ---------------------------------
# Browsers don't say which device a scroll comes from, so each burst of scrolling (no gap over 0.25s) is judged on its
# first event and keeps that judgement: scrolling by lines or pages (Firefox's wheel), or in whole wheel notches of
# 120 (wheelDeltaY) that aren't simply 3x the pixel delta (which is how Chrome and Safari report trackpad scrolling),
# or a large whole-number step with no sideways part, is a mouse wheel; any sideways movement means a trackpad.
# A wheel notch zooms by about 15% (down out, up in), and counts as zooming for the Works / Playground switches.
# Pinching (ctrl + scroll) zooms as before.
sub('locked=!1;wheel=e=>{if(!this.enabled||(e.preventDefault(),this.locked))return;if(e.ctrlKey){this.zzZt=performance.now(),this.zoomVel+=Math.sign(e.deltaY)*Math.min(Math.abs(e.deltaY),60)*.0012;return}',
    'zzMouse(e){let T=performance.now(),G=this.zzWg;(!G||T-G.t>250)&&(G=this.zzWg={m:null,t:T}),G.t=T;'
    'if(G.m===null){let w=e.wheelDeltaY;G.m=e.deltaMode?!0:e.deltaX?!1:w&&w===-3*e.deltaY?!1:w&&w%120===0?!0:Math.abs(e.deltaY)>=50&&Number.isInteger(e.deltaY)}'
    'else e.deltaX&&(G.m=!1);return G.m}'
    'locked=!1;wheel=e=>{if(!this.enabled||(e.preventDefault(),this.locked))return;if(e.ctrlKey){this.zzZt=performance.now(),this.zoomVel+=Math.sign(e.deltaY)*Math.min(Math.abs(e.deltaY),60)*.0012;return}'
    'if(this.zzMouse(e)){let w=e.wheelDeltaY,n=w&&w%120===0?Math.abs(w)/120:e.deltaMode?Math.abs(e.deltaY)/3:Math.abs(e.deltaY)/100;'
    'this.zzZt=performance.now(),this.zoomVel+=Math.sign(e.deltaY)*Math.min(n,3)*.015;return}')

# ---- 35. On iPhones the 3D view carries on under Safari's bottom bar -------------------------------------------------
# Safari's fixed layout stops above its bottom bar, so the page's grey background showed in a band under it.
# case-window.css stretches the stage down to the screen's bottom edge there (100lvh); the canvas grows with it.
# Framing stays exactly as it was: the camera's lens still describes the area above the bar (aspect and fov as before,
# so the phone dial's glide, tap picking and every size work out the same) and the view offset just draws the extra
# rows below it. Elsewhere the canvas is no taller than that area and nothing changes.
sub('resize=()=>{this.zzDirty=!0;let e=this.el.clientWidth,t=this.el.clientHeight;this.renderer.setSize(e,t),this.composer?.setSize(e,t),this.camera.aspect=e/t,this.camera.fov=e<700?72:60,this.camera.updateProjectionMatrix();',
    'resize=()=>{this.zzDirty=!0;let e=this.el.clientWidth,t=this.el.clientHeight,V=this.zzSvh||(this.zzSvh=document.body.appendChild(document.createElement(`i`)));'
    'V.style.cssText=`position:fixed;top:0;left:0;width:0;height:100svh;visibility:hidden;pointer-events:none`,V=Math.min(t,V.offsetHeight||t);'
    'this.renderer.setSize(e,t),this.composer?.setSize(e,t),this.camera.fov=e<700?72:60,'
    't-V>1?this.camera.setViewOffset(e,V,0,0,e,t):(this.camera.aspect=e/t,this.camera.clearViewOffset()),this.camera.updateProjectionMatrix();')

# ---- 37. The floating loops' textures are drawn a slice at a time --------------------------------------------------
# Drawing all of them (83 strips of 8 frames, each roughed and grained) took about 0.9s of unbroken work on a laptop,
# more on a phone, right while the loading intro plays, so the intro froze. Now each strip's canvas and texture are
# made at once but drawn later, one frame (or the strip's grain) per job, from a queue worked through at the start of
# each animation frame for at most 5ms while the page is loading and 8ms after. When a strip is finished its texture
# and the eight per-frame copies the loops use are marked ready and uploaded; until then the loops using it stay
# hidden (section 21). Jobs keep their order, so the loops come out exactly as before.
sub('function Ng(e,t){let n=document.createElement(`canvas`);n.width=1024,n.height=xg;let r=n.getContext(`2d`);for(let n=0;n<vg;n++){let i=n*xg;e((e,t,n)=>{e<0||t<0||e>=yg||t>=yg||(r.fillStyle=n,r.fillRect(i+e*bg,t*bg,bg,bg))},n,t,r,i)}Mg(r,n.width,n.height);let i=new fu(n);return i.colorSpace=to,i.magFilter=Ii,i.minFilter=zi,i.generateMipmaps=!1,i.repeat.set(1/vg,1),i}',
    'var zzQ=[],zzQb=0;function zzRun(){if(zzQb||!zzQ.length)return;zzQb=1;let f=()=>{let T=performance.now(),B=document.documentElement.classList.contains(`zz-booting`)?5:8;'
    'while(zzQ.length&&performance.now()-T<B)zzQ.shift()();zzQ.length?document.hidden?setTimeout(f,50):requestAnimationFrame(f):zzQb=0};document.hidden?setTimeout(f,50):requestAnimationFrame(f)}'
    'function Ng(e,t){let n=document.createElement(`canvas`);n.width=1024,n.height=xg;let r=n.getContext(`2d`),i=new fu(n);i.colorSpace=to,i.magFilter=Ii,i.minFilter=zi,i.generateMipmaps=!1,i.repeat.set(1/vg,1);'
    'for(let a=0;a<vg;a++)zzQ.push(()=>{let o=a*xg;e((X,Y,C)=>{X<0||Y<0||X>=yg||Y>=yg||(r.fillStyle=C,r.fillRect(o+X*bg,Y*bg,bg,bg))},a,t,r,o)});'
    'zzQ.push(()=>{Mg(r,n.width,n.height),i.zzReady=!0,i.needsUpdate=!0;for(let c of i.zzC||[])c.zzReady=!0,c.needsUpdate=!0});zzRun();return i}')
# Each strip's eight copies (one per frame, offset along the strip) are listed on it, so they can be marked ready.
sub('this.phases=r.map(e=>Array.from({length:vg},(t,n)=>{let r=e.clone();return r.userData.k=n,r}))',
    'this.phases=r.map(e=>Array.from({length:vg},(t,n)=>{let r=e.clone();return r.userData.k=n,(e.zzC||=[]).push(r),r}))')

# ---- 38. Opening a case study or a Playground picture: no flash ------------------------------------------------------
# The window's entrance (sheet rising from 70px below at 94% and fading in) was started from a useEffect, which runs
# after the browser has painted: for one frame the window showed fully, at full size, then snapped to hidden and rose
# in. It now starts from a useLayoutEffect, before the first paint. The dimmed backdrop behind it used to appear at
# once, too; on a fresh open it now fades in over 0.45s with the sheet (not again when stepping to the next work while
# the window is open, zzWas).
sub('(0,l.useEffect)(()=>{let t=o.current;if(!t||!e)return;if(window.matchMedia(`(prefers-reduced-motion: reduce)`).matches){let e=Mi.fromTo(t.querySelector(`.cs-sheet`),{autoAlpha:0},{autoAlpha:1,duration:.25});return()=>{e.kill()}}let n=Mi.timeline({defaults:{ease:`expo.out`}});return n.fromTo(',
    '(0,l.useLayoutEffect)(()=>{let t=o.current;if(!t||!e){t&&(t.zzWas=null);return}let W=t.zzWas;t.zzWas=e;'
    'if(window.matchMedia(`(prefers-reduced-motion: reduce)`).matches){let e=Mi.fromTo(t.querySelector(`.cs-sheet`),{autoAlpha:0},{autoAlpha:1,duration:.25});return()=>{e.kill()}}'
    # (The backdrop's fade is a tween of its own, alongside: added to the timeline first, it pushed the sheet's entrance
    # back by its length.) Both are made paused, at their starting look, and set going two frames later: a case study's
    # first frame is slow to draw, and with the clock running through it the window first showed already 40% in. Now
    # that slow first frame is drawn invisible and the rise starts from nothing after it. Closing or stepping to another
    # work before then cancels the start (a backdrop fade not yet begun is run so it isn't left clear).
    'let n=Mi.timeline({defaults:{ease:`expo.out`},paused:!0}),B=t.querySelector(`.cs-scroll`),'
    'Bt=B&&!W&&Mi.fromTo(B,{backgroundColor:`rgba(0,0,0,0)`},{backgroundColor:getComputedStyle(B).backgroundColor,duration:.45,ease:`power2.out`,clearProps:`backgroundColor`,paused:!0}),'
    'R=requestAnimationFrame(()=>{R=requestAnimationFrame(()=>{R=0,n.play(0),Bt&&Bt.play(0)})});'
    'return n.fromTo(')

sub('.fromTo(t.querySelectorAll(`[data-in]`),{y:24,autoAlpha:0},{y:0,autoAlpha:1,duration:.8,stagger:.035},.15),()=>{n.kill()}},[e])',
    '.fromTo(t.querySelectorAll(`[data-in]`),{y:24,autoAlpha:0},{y:0,autoAlpha:1,duration:.8,stagger:.035},.15),()=>{R&&cancelAnimationFrame(R),n.kill(),Bt&&Bt.paused()&&Bt.play(0)}},[e])')

# ---- 39. The links between the works vary ---------------------------------------------------------------------------------
# They were all the same coloured dashed line (each with a thin dotted line beside it). Now each of the three has its own
# stroke: one solid, one dashed as before, one dotted with a heavier dot.
sub('let r=(e,t,n,r)=>{let i=new pg;i.setPositions(Array(123).fill(0));let a=new qh({color:new X(e),linewidth:t,dashed:!0,dashSize:n,gapSize:r,transparent:!0,opacity:0});',
    'let r=(e,t,n,r,D=!0)=>{let i=new pg;i.setPositions(Array(123).fill(0));let a=new qh({color:new X(e),linewidth:t,dashed:D,dashSize:n,gapSize:r,transparent:!0,opacity:0});')
sub('seed:i*3.7+1,line:r(a,2.4,.5,.32),thin:r(`#111111`,1,.12,.3)})',
    'seed:i*3.7+1,line:r(a,...[[2.6,0,0,!1],[2.4,.5,.32,!0],[3.6,.04,.26,!0]][i%3]),thin:r(`#111111`,1,.12,.3)})')

# ---- 40. The home view's cloud has the three case studies in it too ----------------------------------------------------
# Zeen, Allot and Prism join the cloud of Playground pieces as cards of their own (their Works pictures, drawn at most
# 400px wide in the cloud's white frame). They are added after the routes and markers are made, so they have neither,
# they fade in and out with the cloud (cloud.v) so they never show in Playground, and Playground's navigation (the
# phone dial, activeNodes) leaves them out. In the cloud they take turns along its spiral like the rest.
sub('this.buildWorks(),this.buildRoutes(),this.buildFrames(),', 'this.buildWorks(),this.buildRoutes(),this.zzCloudCases(),this.buildFrames(),')
sub('buildWorks(){let e=f_(11)',
    'zzCloudCases(){let R=f_(29);for(let w of Kg){let M=new tl({color:16777215,fog:!1,transparent:!0,opacity:0}),P=new hl(M);P.renderOrder=4,P.center.set(.5,-.06),P.visible=!1;'
    'let N={work:w,rest:this.cloudCenter.clone(),base:this.cloudCenter.clone(),sprite:P,aspect:16/10,hover:0,hv:0,lean:0,size:.85+R()*.45,w4:0,w4p:0,zzCloudOnly:1},I=new Image;'
    'I.onload=()=>{let W=Math.min(400,I.naturalWidth),H=Math.round(W*I.naturalHeight/I.naturalWidth),C=document.createElement(`canvas`);C.width=W+20,C.height=H+20;'
    'let x=C.getContext(`2d`),q=(a,b,c,d,r)=>{x.beginPath(),x.moveTo(a+r,b),x.arcTo(a+c,b,a+c,b+d,r),x.arcTo(a+c,b+d,a,b+d,r),x.arcTo(a,b+d,a,b,r),x.arcTo(a,b,a+c,b,r),x.closePath()};'
    'x.fillStyle=`#ffffff`,q(0,0,C.width,C.height,22),x.fill(),x.save(),q(10,10,W,H,17),x.clip(),x.imageSmoothingQuality=`high`,x.drawImage(I,10,10,W,H),x.restore();'
    'let T=new fu(C);T.colorSpace=to,T.anisotropy=4,M.map=T,M.needsUpdate=!0,N.aspect=C.width/C.height};'
    'I.src=`./${w.img}`,P.userData.node=N,this.scene.add(P),this.nodes.push(N)}}'
    'buildWorks(){let e=f_(11)')
sub('activeNodes(){return this.mode===`works`?this.big:this.nodes}', 'activeNodes(){return this.mode===`works`?this.big:this.nodes.filter(e=>!e.zzCloudOnly)}')
sub('g*Math.min(1,this.zzIn*1.5),r.marker&&(r.marker.material.opacity=r.sprite.material.opacity,r.marker.visible=g>.02),r.sprite.visible=!!r.sprite.material.map&&g>.02',
    'g*Math.min(1,this.zzIn*1.5)*(r.zzCloudOnly?this.cloud.v:1),r.marker&&(r.marker.material.opacity=r.sprite.material.opacity,r.marker.visible=g>.02),'
    'r.sprite.visible=!!r.sprite.material.map&&g>.02&&(!r.zzCloudOnly||this.cloud.v>.02)')

# ---- 41. Left open for a long time, the view no longer turns inverted ----------------------------------------------------
# The glitch pass over the 3D view (the occasional torn bands, inverted and cyan blocks) picks its blocks with a sine
# hash of the scene clock, which keeps counting while the tab sits in the background. Past about an hour the GPU's sine
# of such large numbers collapses, the hash comes out 0 for every block, and since the glitch strength only ever fades
# towards zero (never reaching it), every block passed the "invert this one" test: the whole view turned negative and
# stayed that way. The pass now hashes the clock wrapped to a small range (it only needs a fresh pattern 14 times a
# second), and the strength settles to exactly 0 between bursts, so no block inverts then. The contour sky's grain,
# dust and cursor-lens wobble get the same wrapping, so they too look the same after hours as in the first minute.
sub('float tb = floor(uTime * 14.0);', 'float tb = mod(floor(uTime * 14.0), 2048.0);')
sub('hash(vUv * 1000.0 + uTime)', 'hash(vUv * 1000.0 + mod(uTime, 64.0))')
sub('this.glitchAmt+=(0-this.glitchAmt)*Math.min(1,e*7),', 'this.glitchAmt+=(0-this.glitchAmt)*Math.min(1,e*7),this.glitchAmt<.002&&(this.glitchAmt=0),')
sub('gl_FragCoord.xy + t*37.0', 'gl_FragCoord.xy + mod(t, 32.0)*37.0')
sub('sin(t * 2.0 - md * 40.0)', 'sin(mod(t, 6.2831853) * 2.0 - md * 40.0)')
sub('sin(t * 3.0)', 'sin(mod(t, 6.2831853) * 3.0)')
sub('floor(t*12.0)', 'mod(floor(t*12.0), 1024.0)')
sub('floor(t*6.0)', 'mod(floor(t*6.0), 1024.0)')

open(OUT, 'w').write(s)
css = open(CSS_SRC).read()
open(CSS_OUT, 'w').write(css)

# ---- 8. index.html loads the case renderer before the site's own script ---------------
import time
html = open(f'{SITE}/.backup-original/index.html').read()
main_tag = '<script type="module" crossorigin src="./assets/index-DnZOTAZ6.js"></script>'
assert html.count(main_tag) == 1
stamp = int(time.time())
html = html.replace(main_tag, f'<script type="module" src="./work/case-embed.js?v={stamp}"></script>\n    '
                    + main_tag.replace('index-DnZOTAZ6.js', f'index-DnZOTAZ6.js?v={stamp}'))
# Link previews: a looping video (og:video) for apps that play one, its poster as the image everywhere else.
SITE_URL = 'https://www.zirui.ca'  # the address the site is served from; previews need absolute links
TITLE = 'Zirui Zhao'  # the title link previews show
DESCRIPTION = "Zirui Zhao's works floating in an endless, glitching lattice."
IMAGE_ALT = "Zirui Zhao's works floating over a topographic lattice"
og = f"""
    <link rel="canonical" href="{SITE_URL}/" />
    <meta property="og:type" content="website" />
    <meta property="og:site_name" content="Zirui Zhao" />
    <meta property="og:title" content="{TITLE}" />
    <meta property="og:description" content="{DESCRIPTION}" />
    <meta property="og:url" content="{SITE_URL}/" />
    <meta property="og:image" content="{SITE_URL}/og/preview.jpg" />
    <meta property="og:image:type" content="image/jpeg" />
    <meta property="og:image:width" content="1200" />
    <meta property="og:image:height" content="630" />
    <meta property="og:image:alt" content="{IMAGE_ALT}" />
    <meta property="og:video" content="{SITE_URL}/og/preview.mp4" />
    <meta property="og:video:secure_url" content="{SITE_URL}/og/preview.mp4" />
    <meta property="og:video:type" content="video/mp4" />
    <meta property="og:video:width" content="960" />
    <meta property="og:video:height" content="586" />
    <meta name="twitter:card" content="summary_large_image" />
    <meta name="twitter:title" content="{TITLE}" />
    <meta name="twitter:description" content="{DESCRIPTION}" />
    <meta name="twitter:image" content="{SITE_URL}/og/preview.jpg" />
    <meta name="twitter:image:alt" content="{IMAGE_ALT}" />"""
desc_tag = f'<meta name="description" content="{DESCRIPTION}" />'
assert html.count(desc_tag) == 1
html = html.replace(desc_tag, desc_tag + og)
for f in ('og/preview.jpg', 'og/preview.mp4'):
    assert os.path.exists(f'{SITE}/{f}'), f
FONTS = '<link href="https://fonts.googleapis.com/css2?family=Chivo:wght@300;400;500;600;700&family=Chivo+Mono:wght@400&display=swap" rel="stylesheet" />'
assert html.count(FONTS) == 1
html = html.replace(FONTS, FONTS.replace('rel="stylesheet" />', 'rel="stylesheet" media="print" onload="this.media=\'all\'" />'))
# The browser tab reads just the name, like the link previews.
TAB = '<title>Zirui Zhao · Lattice of Works</title>'
assert html.count(TAB) == 1
html = html.replace(TAB, '<title>Zirui Zhao</title>')
# An easter egg for whoever opens the page source: plus icons around "you found me!" (easter-egg.py).
import subprocess
art = subprocess.check_output(['python3', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'easter-egg.py')], text=True).rstrip('\n')
assert '--' not in art
DOCTYPE = '<!doctype html>\n'
assert html.startswith(DOCTYPE)
html = DOCTYPE + '<!--\n\n' + art + '\n\n-->\n' + html[len(DOCTYPE):]
# The loading screen paints before any script loads (src/loader.html); work/perf.js lifts it.
loader = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src', 'loader.html')).read().strip()
# Its slithering stack shows the 3D view's own loops (section 32's shapes.js and tiles.js, the same code) and five
# Playground pieces the user picked: Weightless, BCRC Montreal's two posters (Trains of Thought, Map of Care), RUN.
# and AI Dehumanization.
INTRO_WORKS = ['pg-16', 'pg-34', 'pg-35', 'pg-04', 'pg-23']
assert loader.count('/*ZZ_TILES*/') == 1 and loader.count('/*ZZ_WORKS*/') == 1
for w in INTRO_WORKS:
    assert w in ORDER and os.path.exists(f'{SITE}/works/thumbs/{w}.webp'), w
loader = loader.replace('/*ZZ_TILES*/', tiles).replace('/*ZZ_WORKS*/', json.dumps([f'works/thumbs/{w}.webp' for w in INTRO_WORKS]))
BODY = '<body>'
assert html.count(BODY) == 1
html = html.replace(BODY, BODY + '\n' + loader, 1)
open(f'{SITE}/index.html', 'w').write(html)

# ---- The unlisted icons page (showcase/), for a social post: five of the site's icons on its background ------------------
# Built from src/showcase.html with the same loop code (shapes.js, tiles.js) and the loader's contour-sky shader, so it
# draws exactly what the site draws. ?export=<url> renders it frame by frame for a video.
SKY_START, SKY_END = "      var NOISE = ", "'gl_FragColor=vec4(clamp(col,0.0,1.0),1.0);}';"
raw_loader = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src', 'loader.html')).read()
assert raw_loader.count(SKY_START) == 1 and raw_loader.count(SKY_END) == 1
sky_shader = raw_loader[raw_loader.index(SKY_START):raw_loader.index(SKY_END) + len(SKY_END)].strip()
show = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src', 'showcase.html')).read()
assert show.count('/*ZZ_TILES*/') == 1 and show.count('/*ZZ_SKY_SHADER*/') == 1
show = show.replace('/*ZZ_TILES*/', tiles).replace('/*ZZ_SKY_SHADER*/', sky_shader)
os.makedirs(f'{SITE}/showcase', exist_ok=True)
open(f'{SITE}/showcase/index.html', 'w').write(show)
print('ok', len(s))
