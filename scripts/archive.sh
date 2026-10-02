#!/usr/bin/env bash
# 制作1本分をまとめて archive/<日付>_<名前>/ に保管し、次の商品用に作業フォルダを空に戻す。
# archive/ は Git 管理外（ローカルのみ）。素材・動画を含むためコミットされない。
#   bash scripts/archive.sh <名前>          例: bash scripts/archive.sh hand-cream
#   bash scripts/archive.sh <名前> --dry-run
set -euo pipefail
cd "$(dirname "$0")/.."

NAME="${1:-}"
if [ -z "$NAME" ]; then
  echo "usage: bash scripts/archive.sh <名前（英数字とハイフン）> [--dry-run]"; exit 1
fi
SLUG="$(printf '%s' "$NAME" | tr ' /' '--' | tr -cd '[:alnum:]_.-')"
[ -z "$SLUG" ] && SLUG="project"
DEST="archive/$(date +%Y-%m-%d)_${SLUG}"
if [ -e "$DEST" ]; then DEST="${DEST}_$(date +%H%M%S)"; fi
DRY="${2:-}"

move() { # move <src> <dst-dir>  (skips empty / .gitkeep-only)
  local src="$1" dst="$2"
  [ -e "$src" ] || return 0
  if [ -d "$src" ] && [ -z "$(find "$src" -mindepth 1 ! -name .gitkeep -print -quit)" ]; then return 0; fi
  echo "  $src → $dst/"
  if [ "$DRY" != "--dry-run" ]; then mkdir -p "$dst"; mv "$src" "$dst/"; fi
}

echo "保管先: $DEST"
move input/current "$DEST/input"
for f in planning/*; do [ "$(basename "$f")" = "reference-analysis" ] && continue; move "$f" "$DEST/planning"; done
move planning/reference-analysis "$DEST/planning"
[ "$DRY" != "--dry-run" ] && rm -rf preview/storyboard/_src/*/assets preview/storyboard/_src/*/snapshots temp/*
for f in preview/storyboard/*; do move "$f" "$DEST/preview/storyboard"; done
for f in output/draft/* output/final/*; do
  [ "$(basename "$f")" = ".gitkeep" ] && continue
  move "$f" "$DEST/output/$(basename "$(dirname "$f")")"
done
if [ -d video ]; then
  if [ "$DRY" != "--dry-run" ]; then
    rm -rf video/node_modules video/renders video/snapshots video/.hyperframes \
      video/assets/fonts video/assets/vendor video/assets/sfx video/assets/product video/assets/audio
  fi
  move video "$DEST"
fi
[ "$DRY" = "--dry-run" ] && { echo "(dry-run: 何も移動していません)"; exit 0; }

# 作業フォルダを初期状態に戻す
mkdir -p input/current/product/{images,videos,logo} input/current/reference/{videos,images} input/current/audio \
  planning/reference-analysis preview/storyboard output/draft output/final temp
for d in input/current/product/images input/current/product/videos input/current/product/logo \
  input/current/reference/videos input/current/reference/images input/current/audio \
  planning/reference-analysis preview/storyboard output/draft output/final; do touch "$d/.gitkeep"; done
cp templates/brief.md input/current/brief.md
for f in templates/planning/*; do cp "$f" planning/; done
echo "✓ 保管しました: $DEST"
echo "✓ input/current/ と planning/ をテンプレートに戻しました。次の商品の素材を入れてください。"
