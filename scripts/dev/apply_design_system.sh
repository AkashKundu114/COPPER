#!/usr/bin/env bash
# ==============================================================================
# COPPER design-system codemod
# Run once from the repo root: `bash scripts/dev/apply_design_system.sh`
#
# What it does:
#   - Renames generic Tailwind color families to the new copper/graphite
#     token families, shade-for-shade, across every .ts/.tsx file under
#     frontend/src. Because the new families (accent/molten/verdigris/danger)
#     were given full 50-950 ramps in tailwind.config.js, every renamed class
#     (e.g. `bg-sky-500` -> `bg-accent-500`) still resolves to a real color —
#     nothing goes blank.
#   - Swaps the small set of hardcoded hex accents scattered through
#     DashboardView / CommandPalette / BenchmarkMetricsView for their new
#     token equivalents.
#
# What it deliberately leaves alone:
#   - `slate-*` neutrals (already a cool dark gray, compatible with the new
#     graphite palette; not worth the risk of a blind rename).
#   - Multi-series data-visualization color arrays (e.g. the bar/radar chart
#     palettes in BenchmarkMetricsView) — collapsing those to one accent
#     color would remove the visual distinction between series. Recolor
#     those by hand if you want them on-theme.
#   - `text-white` / `bg-white` — visually near-identical to the new
#     `text-DEFAULT` (#EDEDEA), not worth touching.
#
# Safe to re-run; every substitution is idempotent.
# ==============================================================================
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SRC_DIR="$ROOT_DIR/frontend/src"

if [ ! -d "$SRC_DIR" ]; then
  echo "Could not find $SRC_DIR — run this from inside the repo." >&2
  exit 1
fi

# Cross-platform in-place sed (GNU vs BSD/macOS)
sedi() {
  if sed --version >/dev/null 2>&1; then
    sed -i "$@"
  else
    sed -i '' "$@"
  fi
}

echo "==> Renaming color families (sky/cyan -> accent, emerald -> verdigris, amber -> molten, rose -> danger)"
find "$SRC_DIR" -type f \( -name "*.ts" -o -name "*.tsx" \) -print0 | while IFS= read -r -d '' file; do
  sedi \
    -e 's/\bsky-/accent-/g' \
    -e 's/\bcyan-/accent-/g' \
    -e 's/\bemerald-/verdigris-/g' \
    -e 's/\bamber-/molten-/g' \
    -e 's/\brose-/danger-/g' \
    "$file"
done

echo "==> Swapping hardcoded hex accents for their token equivalents"
find "$SRC_DIR" -type f \( -name "*.ts" -o -name "*.tsx" \) -print0 | while IFS= read -r -d '' file; do
  sedi \
    -e 's/#f97316/#C97C4C/g' \
    -e 's/#F97316/#C97C4C/g' \
    -e 's/#ea580c/#AD6339/g' \
    -e 's/#EA580C/#AD6339/g' \
    -e 's/#fb923c/#DB9563/g' \
    -e 's/#FB923C/#DB9563/g' \
    -e 's/#b87333/#C97C4C/g' \
    -e 's/#B87333/#C97C4C/g' \
    -e 's/#ff5722/#FF7A45/g' \
    -e 's/#FF5722/#FF7A45/g' \
    "$file"
done

echo "==> Done. Run 'npm run build' (or 'npm run lint') inside frontend/ to confirm nothing broke, then review the diff — it's mechanical but worth a skim, especially anywhere colors were used to distinguish data series rather than as UI chrome."
