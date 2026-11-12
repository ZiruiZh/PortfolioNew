# Small copies of the playground pieces for the 3D lattice (the pop-up still opens the full image).
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"; SITE="$(dirname "$HERE")"
mkdir -p "$SITE/works/thumbs"
for src in "$SITE"/works/*.webp; do
  out="$SITE/works/thumbs/$(basename "$src")"
  [ "$out" -nt "$src" ] && continue
  magick "$src" -resize '400x520>' -strip -quality 72 "$out"
done
