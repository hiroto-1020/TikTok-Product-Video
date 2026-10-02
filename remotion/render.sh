#!/usr/bin/env bash
# Remotion のレンダー（ブラウザは HyperFrames が用意した Chrome Headless Shell を再利用）
#   bash render.sh still   → out/still.png（10フレーム目）
#   bash render.sh render  → ../output/draft/remotion_<日時>.mp4
set -euo pipefail
cd "$(dirname "$0")"
[ -d node_modules ] || npm install --no-audit --no-fund
CHROME="$(cd .. && npx --no-install hyperframes browser path 2>/dev/null | tail -1 || true)"
EXTRA=()
if [ -n "$CHROME" ] && [ -x "$CHROME" ]; then EXTRA=(--browser-executable="$CHROME"); fi
case "${1:-render}" in
  still) npx remotion still src/index.ts ProductAd out/still.png --frame=10 "${EXTRA[@]}" ;;
  *) npx remotion render src/index.ts ProductAd "../output/draft/remotion_$(date +%Y%m%d_%H%M%S).mp4" "${EXTRA[@]}" ;;
esac
