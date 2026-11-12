# Builds the original portfolio (read-only source) into this site's recruiter/ folder, which the
# "Recruiter mode" button opens. The portfolio is copied to a temporary folder first, so nothing in it
# changes, not even Vite's cache.
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"; SITE="$(dirname "$HERE")"
PORT=/Users/ziruizhao/Documents/PersonalPortfolioWebsite
TMP="$(cd "$(mktemp -d)" && pwd -P)"
trap 'rm -rf "$TMP"' EXIT

rsync -a --exclude node_modules --exclude dist --exclude .git --exclude .reference --exclude .claude \
  --exclude tests --exclude scripts "$PORT/" "$TMP/src-copy/"
ln -s "$PORT/node_modules" "$TMP/src-copy/node_modules"

# Only the real home page (index.html), with relative paths so it works from a subfolder.
cat > "$TMP/src-copy/vite.recruiter.mjs" <<CFG
import { defineConfig } from 'vite';
export default defineConfig({
  root: '$TMP/src-copy',
  base: './',
  cacheDir: '$TMP/vite-cache',
  logLevel: 'warn',
  build: { outDir: '$TMP/out', emptyOutDir: true },
});
CFG
(cd "$TMP/src-copy" && node node_modules/vite/bin/vite.js build --config vite.recruiter.mjs)

python3 "$HERE/recruiter-post.py" "$TMP/out"
rm -rf "$SITE/recruiter" && mv "$TMP/out" "$SITE/recruiter"
echo "recruiter/ built: $(du -sh "$SITE/recruiter" | cut -f1)"
