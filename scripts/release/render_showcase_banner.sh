#!/usr/bin/env bash
set -euo pipefail

fail() {
  printf 'render_showcase_banner.sh: %s\n' "$*" >&2
  exit 1
}

require_tool() {
  command -v "$1" >/dev/null 2>&1 || fail "required tool not found: $1"
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
SHOWCASE_SOURCE="${PROJECT_ROOT}/examples/showcase/hypolatex-showcase.md"
PDF_PATH="${PROJECT_ROOT}/build/showcase/hypolatex-showcase.pdf"
BANNER_PATH="${PROJECT_ROOT}/assets/readme/showcase-banner.png"
WORK_DIR="${PROJECT_ROOT}/build/showcase/banner-pages"
PAGE_SELECTION=(1 5 9 13)

require_tool uv
require_tool pdftoppm

if command -v montage >/dev/null 2>&1; then
  COMPOSER="montage"
elif command -v convert >/dev/null 2>&1; then
  COMPOSER="convert"
else
  fail "required ImageMagick tool not found: montage or convert"
fi

[[ -f "${SHOWCASE_SOURCE}" ]] || fail "missing showcase source: ${SHOWCASE_SOURCE}"

mkdir -p "$(dirname "${PDF_PATH}")" "$(dirname "${BANNER_PATH}")" "${WORK_DIR}"
rm -f "${WORK_DIR}"/page-*.png "${BANNER_PATH}"

(
  cd "${PROJECT_ROOT}"
  PYTHONDONTWRITEBYTECODE=1 uv run hypolatex build "${SHOWCASE_SOURCE}" --output "${PDF_PATH}"
) || fail "hypolatex build failed for ${SHOWCASE_SOURCE}"

[[ -s "${PDF_PATH}" ]] || fail "showcase PDF was not created: ${PDF_PATH}"

for page_number in "${PAGE_SELECTION[@]}"; do
  pdftoppm -png -singlefile -f "${page_number}" -l "${page_number}" -r 120 \
    "${PDF_PATH}" "${WORK_DIR}/page-${page_number}" \
    || fail "pdftoppm failed while rasterizing page ${page_number} from ${PDF_PATH}"
done

shopt -s nullglob
PAGES=("${WORK_DIR}"/page-1.png "${WORK_DIR}"/page-5.png "${WORK_DIR}"/page-9.png "${WORK_DIR}"/page-13.png)
shopt -u nullglob
(( ${#PAGES[@]} > 0 )) || fail "pdftoppm produced no PNG pages in ${WORK_DIR}"

if [[ "${COMPOSER}" == "montage" ]]; then
  montage "${PAGES[@]}" \
    -thumbnail 720x920 \
    -background '#f8fafc' \
    -bordercolor '#d0d7de' \
    -border 2 \
    -geometry '+18+18' \
    -tile 4x1 \
    "${BANNER_PATH}" \
    || fail "montage failed while composing assets/readme/showcase-banner.png"
else
  convert "${PAGES[@]}" \
    -resize 720x920 \
    +append \
    -background '#f8fafc' \
    -gravity center \
    -extent 2880x920 \
    "${BANNER_PATH}" \
    || fail "convert failed while composing assets/readme/showcase-banner.png"
fi

[[ -s "${BANNER_PATH}" ]] || fail "banner PNG was not created: assets/readme/showcase-banner.png"
printf 'Generated assets/readme/showcase-banner.png from build/showcase/hypolatex-showcase.pdf\n'
