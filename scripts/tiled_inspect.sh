#!/usr/bin/env bash
# Render the chapter-four maps with Tiled's own renderer so the map data can be
# inspected inside the application instead of only through the runtime loader.
#
# Tiled's --export-map CLI cannot load these maps (it reports "载入源地图失败"
# for every file, including maps that the runtime loads fine), and --evaluate
# has no mapEditor without a GUI session, so the inspection uses tmxrasterizer,
# the official headless renderer that ships with Tiled.
#
# Usage: bash scripts/tiled_inspect.sh [output_dir]
set -euo pipefail

TILED_APP="${TILED_APP:-/Applications/Tiled.app}"
OUT_DIR="${1:-artifacts/tiled-inspect}"
RASTERIZER="$TILED_APP/Contents/MacOS/tmxrasterizer"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [ ! -x "$RASTERIZER" ]; then
  echo "Tiled not found at $TILED_APP (override with TILED_APP=/path/to/Tiled.app)" >&2
  exit 1
fi

mkdir -p "$OUT_DIR"
for map in c4_yamen c4_lixiang; do
  src="$ROOT/maps/$map.tmj"
  [ -f "$src" ] || { echo "missing map: $src" >&2; exit 1; }
  # Art layer only: this is what the map actually places in the world.
  "$RASTERIZER" --size 1400 "$src" "$ROOT/$OUT_DIR/$map-tiled.png"
  # All layers: adds the PlanZones walkable areas and the ArtFootprints
  # collision boxes, which are hidden in the editor by default.
  "$RASTERIZER" --size 1400 --ignore-visibility "$src" "$ROOT/$OUT_DIR/$map-all-layers.png"
  echo "rendered $map"
done

ls -la "$ROOT/$OUT_DIR"
