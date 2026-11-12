"""Post-build fixes for recruiter/ (the original portfolio, built into a subfolder of this site).

- Links written from the site root ("/zeen/", "/assets/resume.pdf") point into this folder instead.
- "back to cool mode" joins the portfolio's own navigation, top bar and phone menu, and leads back
  to this site's main view.
"""
import glob
import os
import sys

out = sys.argv[1]


def replace_once(text, old, new, where):
    assert text.count(old) == 1, f'{where}: expected one {old!r}, found {text.count(old)}'
    return text.replace(old, new)


# The Zeen prototype ships inside this folder (zeen/), so its link stays inside it too.
hits = 0
for path in glob.glob(os.path.join(out, 'assets', '*.js')):
    code = open(path, encoding='utf-8').read()
    if 'href:"/zeen/"' in code:
        code = replace_once(code, 'href:"/zeen/"', 'href:"./zeen/"', path)
        open(path, 'w', encoding='utf-8').write(code)
        hits += 1
assert hits == 1, f'Zeen prototype link found in {hits} files'

html_path = os.path.join(out, 'index.html')
html = open(html_path, encoding='utf-8').read()
resume = [os.path.basename(p) for p in glob.glob(os.path.join(out, 'assets', 'resume-*.pdf'))]
assert len(resume) == 1, resume
html = html.replace('href="/assets/resume.pdf"', f'href="./assets/{resume[0]}"')

html = replace_once(
    html,
    '<a class="cell nav-link" href="#about"><span class="link-label">about</span></a>',
    '<a class="cell nav-link" href="#about"><span class="link-label">about</span></a>\n'
    '        <a class="cell nav-link zz-exit" href="../"><span class="link-label">back to cool mode</span></a>',
    'top bar')
html = replace_once(
    html,
    '<li><a href="#about">about</a></li>',
    '<li><a href="#about">about</a></li>\n          <li><a href="../">back to cool mode</a></li>',
    'phone menu')
assert '="/' not in html.replace('="//', ''), 'a root-relative link is left in recruiter/index.html'
open(html_path, 'w', encoding='utf-8').write(html)
print('recruiter/ links fixed; exit link added')
