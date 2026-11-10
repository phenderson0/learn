#!/usr/bin/env bash
# render.sh — render a Mermaid or SVG source file to PNG, optionally publish it.
#
#   render.sh mermaid <source.mmd> <out.png>
#   render.sh svg     <source.svg> <out.png>
#   render.sh publish <rendered.png> <slug> [viz-dir]   -> prints the published path
#   render.sh check                                     -> report available renderers
#
# Mermaid: mmdc (global) or `npx -y @mermaid-js/mermaid-cli`. Uses an installed
#          Chrome/Chromium if one is found (set PUPPETEER_EXECUTABLE_PATH to override).
# SVG:     rsvg-convert, then ImageMagick, then python cairosvg.
set -euo pipefail

die() { echo "render.sh: $*" >&2; exit 1; }

find_chrome() {
  if [[ -n "${PUPPETEER_EXECUTABLE_PATH:-}" && -x "$PUPPETEER_EXECUTABLE_PATH" ]]; then
    echo "$PUPPETEER_EXECUTABLE_PATH"; return
  fi
  for c in google-chrome google-chrome-stable chromium chromium-browser; do
    command -v "$c" >/dev/null 2>&1 && { command -v "$c"; return; }
  done
  for c in "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
           "/Applications/Chromium.app/Contents/MacOS/Chromium"; do
    [[ -x "$c" ]] && { echo "$c"; return; }
  done
}

mmdc_cmd() {
  if command -v mmdc >/dev/null 2>&1; then echo "mmdc"
  elif command -v npx >/dev/null 2>&1 && command -v node >/dev/null 2>&1; then echo "npx -y @mermaid-js/mermaid-cli"
  fi
}

render_mermaid() {
  local src=$1 out=$2 cmd chrome cfg
  cmd=$(mmdc_cmd); [[ -n "$cmd" ]] || die "no Mermaid renderer: install Node.js (then npx fetches mermaid-cli) or 'npm i -g @mermaid-js/mermaid-cli'"
  cfg=$(mktemp --suffix=.json 2>/dev/null || mktemp)
  chrome=$(find_chrome || true)
  if [[ -n "$chrome" ]]; then
    printf '{"executablePath":"%s","args":["--no-sandbox"]}\n' "$chrome" >"$cfg"
  else
    printf '{"args":["--no-sandbox"]}\n' >"$cfg"
  fi
  # -s 2 = 2x scale for crisp text; white background so it reads in any theme.
  $cmd -i "$src" -o "$out" -b white -s 2 -p "$cfg" -q
  rm -f "$cfg"
}

render_svg() {
  local src=$1 out=$2
  if command -v rsvg-convert >/dev/null 2>&1; then
    rsvg-convert -z 2 -b white -o "$out" "$src"
  elif command -v magick >/dev/null 2>&1; then
    magick -density 192 -background white "$src" -flatten "$out"
  elif python3 -c "import cairosvg" >/dev/null 2>&1; then
    python3 -c "import sys,cairosvg; cairosvg.svg2png(url=sys.argv[1], write_to=sys.argv[2], scale=2, background_color='white')" "$src" "$out"
  else
    die "no SVG renderer: install librsvg2-bin (rsvg-convert), ImageMagick, or 'pip install cairosvg'"
  fi
}

publish() {
  local png=$1 slug=$2 dir=${3:-${LEARN_VIZ_DIR:-$PWD/viz}} clean dest
  [[ -f "$png" ]] || die "no such file: $png"
  clean=$(echo "$slug" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g; s/^-+|-+$//g')
  [[ -n "$clean" ]] || clean=viz
  mkdir -p "$dir"
  dest="$dir/viz-$clean-$(date +%s%3N).png"
  cp "$png" "$dest"
  echo "$dest"
}

check() {
  echo "mermaid: $(mmdc_cmd || true)"; [[ -n "$(mmdc_cmd || true)" ]] || echo "         none — install Node.js (or npm i -g @mermaid-js/mermaid-cli)"
  echo "chrome:  $(find_chrome || echo 'none (mermaid-cli will try its own Chromium)')"
  for t in rsvg-convert magick; do command -v $t >/dev/null 2>&1 && echo "svg:     $t"; done
  python3 -c "import cairosvg" >/dev/null 2>&1 && echo "svg:     cairosvg" || true
  command -v rsvg-convert >/dev/null 2>&1 || command -v magick >/dev/null 2>&1 || python3 -c "import cairosvg" >/dev/null 2>&1 \
    || echo "svg:     none — install librsvg2-bin (rsvg-convert), ImageMagick, or cairosvg"
}

case "${1:-}" in
  mermaid) [[ $# -eq 3 ]] || die "usage: render.sh mermaid <src> <out.png>"; render_mermaid "$2" "$3"; echo "$3" ;;
  svg)     [[ $# -eq 3 ]] || die "usage: render.sh svg <src> <out.png>"; render_svg "$2" "$3"; echo "$3" ;;
  publish) [[ $# -ge 3 ]] || die "usage: render.sh publish <png> <slug> [dir]"; publish "$2" "$3" "${4:-}" ;;
  check)   check ;;
  *) die "usage: render.sh {mermaid|svg|publish|check} ..." ;;
esac
