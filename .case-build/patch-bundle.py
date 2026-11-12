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
KEEP = ['w01', 'w02', 'w03', 'w05', 'w13', 'w16', 'w20', 'w31', 'w33']
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

entries = [f'{k}:{v}' for k, v in kept.items()]
entries += [f'"{k}":{obj(v)}' for k, v in meta.items()]
s = s[:ug_start] + 'Ug={' + ','.join(entries) + '}' + s[ug_end:]

# ---- 2. Trim descriptions to the works that are still shown -----------------
wg_start = s.index('Wg={w01')
wg_end = s.index('},Gg=', wg_start) + 1
bodies = dict(re.findall(r'(w\d\d):`([^`]*)`', s[wg_start:wg_end]))
s = s[:wg_start] + 'Wg={' + ','.join(f'{k}:{tl(bodies[k])}' for k in KEEP if k in bodies) + '}' + s[wg_end:]

# ---- 3. Playground order: originals spread through the new pieces ----------
ORDER = ['pg-16', 'w01', 'pg-07', 'pg-06', 'pg-25', 'w02', 'pg-11', 'pg-24', 'w03', 'pg-12',
         'pg-02', 'w05', 'pg-23', 'pg-18', 'pg-34', 'w13', 'pg-21', 'pg-01', 'pg-04', 'w16',
         'pg-26', 'pg-09', 'pg-29', 'w20', 'pg-15', 'pg-05', 'pg-35', 'w31', 'pg-17', 'pg-08',
         'pg-32', 'w33', 'pg-30', 'pg-13', 'pg-22']
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
    study('zeen', P['zeen']['card']['poster']),
    study('allot', P['allot']['card']['images'][0]),
    # Prism has no case study: the card opens its site in a new tab. Its video is drawn 2% larger from the left edge.
    {'id': 'prism', 'title': P['prism']['title'], 'year': int(P['prism']['year']),
     'img': f"cases/prism/{P['prism']['card']['poster']}", 'video': f"cases/prism/{P['prism']['card']['video']}",
     'ratio': Raw(P['prism']['card']['ratio'].replace(' ', '')), 'zoom': Raw('1.02'),
     'href': P['prism']['link'], 'external': True,
     # The portfolio gives Prism no accent; purple, after its cover.
     'color': '#8f5bff'},
    # ArtsFest stays in this site's own case window with its short text.
    {'id': 'artsfest', 'img': 'cases/artsfest/artsfest-thumb.webp', 'hero': 'cases/artsfest/artsfest-1.webp', 'color': P['artsfest']['accent'],
     'title': 'ArtsFest', 'year': 2024, 'desc': 'One poster for a whole festival',
     'body': '\n\n'.join([
         'For Marianopolis’ ArtsFest convention, I designed the poster that welcomed the whole school into the event.',
         'Getting the energy of the day into a single graphic was the challenge, and the fun.',
         'Client: ArtsFest, an arts festival. Timeline: 3 weeks. Role: lead designer.',
     ])},
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
# #works and #info in the address open those views.
sub('[h,g]=(0,l.useState)(`playground`)', '[h,g]=(0,l.useState)(()=>location.hash===`#works`?`works`:`playground`)')
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
    # Only plays while Works is showing and the tab is visible; it loads the first time it is needed.
    'setInterval(()=>{this.mode===`works`&&!document.hidden?(v.getAttribute(`src`)||(v.src=`./${W.video}`),v.paused&&v.play().catch(()=>{})):v.paused||v.pause()},400)}'
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
# The first work (Zeen) takes the large spot in the middle of the view; the rest sit smaller around it.
sub('bigSpot(e,t){let n=[[-18,1.5,-7],[8,-11.5,6],[23,6,-19],[-8,12,-30],[30,-8,-36],[-30,-9,-24]],',
    'bigSpot(e,t){let n=[[0,-7,10],[-26,10,-10],[26,10,-10],[24,-19,-8],[30,-8,-36],[-30,-9,-24]],')
sub('bigSize(e){return[.82,1,.78,.7,.75,.72][e%6]}', 'bigSize(e){return[1.1,.78,.74,.68,.75,.72][e%6]}')

# ---- 13. The UW CS webring after the x.com handle, bottom right -----------------------------
RING = 'https://cs.uwatering.com/#https://www.zirui.ca/'
webring = ('(0,$.jsxs)(`span`,{className:`zz-webring`,children:['
    f'(0,$.jsx)(`a`,{{href:`{RING}?nav=prev`,"aria-label":`Previous site in the UW CS webring`,children:`←`}}),'
    f'(0,$.jsx)(`a`,{{href:`{RING}`,target:`_blank`,rel:`noreferrer`,className:`zz-crest-link`,"aria-label":`UW CS webring`,title:`UW CS webring`,children:(0,$.jsx)(`span`,{{className:`zz-crest`,"aria-hidden":`true`}})}}),'
    f'(0,$.jsx)(`a`,{{href:`{RING}?nav=next`,"aria-label":`Next site in the UW CS webring`,children:`→`}})]}})')
# The x.com handle loses its trailing arrow; the webring follows it.
sub('e.label,` `,f(`e2ffc48f1d6d`,`↗`)))]})', 'e.label)),' + webring + ']})')

# ---- 14. Light / dark toggle: plain words like the nav, no rotating square ---------------------
sub('children:(0,$.jsxs)(`svg`,{...m(`bbb0f5c93433`),viewBox:`0 0 14 14`,width:`14`,height:`14`,"aria-hidden":`true`,children:[(0,$.jsx)(`rect`,{...m(`480e8dfd63c2`),x:`0.5`,y:`0.5`,width:`13`,height:`13`,fill:`none`,stroke:`currentColor`}),(0,$.jsx)(`path`,{...m(`4a74c637271b`),className:`half`,d:`M0.5 0.5 L13.5 13.5 L0.5 13.5 Z`,fill:`currentColor`})]})})',
    'children:[(0,$.jsx)(`span`,{className:`tt-opt${j?` is-on`:``}`,children:`Light`},`l`),(0,$.jsx)(`span`,{className:`tt-opt${j?``:` is-on`}`,children:`Dark`},`d`)]})')

# ---- 15. Recruiter mode: a button beside Light / Dark that switches to the original portfolio (recruiter/) --
# Both sit in one top-right group. Recruiter mode shows everywhere (Info is the landing page); the toggle hides itself outside Playground and Works.
sub('(0,$.jsx)(`button`,{...m(`61c4be3b24e2`),className:`theme-ico',
    '(0,$.jsxs)(`div`,{className:`zz-topright`,children:['
    '(0,$.jsx)(`a`,{className:`zz-recruiter`,href:`recruiter/`,title:`Switch to the original portfolio`,children:`Recruiter mode`}),'
    '(0,$.jsx)(`button`,{...m(`61c4be3b24e2`),className:`theme-ico')
sub('children:`Dark`},`d`)]}),(0,$.jsxs)(`div`,{...m(`e8040b71c573`),className:`corner-bl`',
    'children:`Dark`},`d`)]})]}),(0,$.jsxs)(`div`,{...m(`e8040b71c573`),className:`corner-bl`')

# ---- 16. Smoother: a lighter render ---------------------------------------------------------
# Draw the 3D scene at no more than 1.5x the screen's resolution (it was up to 1.75x).
sub('this.renderer.setPixelRatio(i?.5:Math.min(window.devicePixelRatio,r?1.5:1.75))',
    'this.renderer.setPixelRatio(i?.5:Math.min(window.devicePixelRatio,r?1.25:1.5))')
# While a window is open over a landed camera, the dimmed scene behind it draws every third frame.
sub('loop=()=>{if(this.disposed)return;this.raf=requestAnimationFrame(this.loop);',
    'loop=()=>{if(this.disposed)return;this.raf=requestAnimationFrame(this.loop);'
    'if(this.focus&&!this.flying&&document.querySelector(`.case.is-open`)&&(this.zzSkip=((this.zzSkip||0)+1)%3))return;'
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
sub('this.glyphs=new Pg(r?200:420,r_)', 'this.glyphs=new Pg(r?140:320,r_)')

# ---- 21. Touch drags turn the view further -------------------------------------------------------
# The drag is scaled by the screen's height, so on a tall, narrow phone a full-width swipe barely turned it.
TOUCH_GAIN = 2.5
sub('let t=e.clientX-this.drag.x,n=e.clientY-this.drag.y;',
    f'let k=e.pointerType===`touch`?{TOUCH_GAIN}:1,t=(e.clientX-this.drag.x)*k,n=(e.clientY-this.drag.y)*k;')

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
open(f'{SITE}/index.html', 'w').write(html)
print('ok', len(s))
