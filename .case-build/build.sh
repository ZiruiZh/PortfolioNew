# Rebuilds the case study renderer from the portfolio (read-only) and re-patches the site's bundle and index.html.
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"; SITE="$(dirname "$HERE")"
cd "$HERE"
ln -sfn /Users/ziruizhao/Documents/PersonalPortfolioWebsite/node_modules node_modules
node prepare.mjs
node node_modules/vite/bin/vite.js build --config vite.config.mjs
rm -rf "$SITE/work" && mkdir -p "$SITE/work" && cp -R dist/. "$SITE/work/"
python3 patch-bundle.py
# Refuse to leave a broken page behind: the patched bundle must parse.
cp "$SITE/assets/index-DnZOTAZ6.js" "$HERE/.check.mjs" && node --check "$HERE/.check.mjs" && rm "$HERE/.check.mjs"
