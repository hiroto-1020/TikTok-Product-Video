#!/bin/bash
# クラウドセッション開始時に制作環境（npm / Chrome Headless Shell / 日本語フォント）を用意する。
set -uo pipefail
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi
cd "${CLAUDE_PROJECT_DIR:-$(dirname "$0")/../..}"
bash scripts/setup.sh >/tmp/tiktok-studio-setup.log 2>&1 || {
  echo "setup.sh reported problems — see /tmp/tiktok-studio-setup.log" >&2
}
# video/ が残っていれば素材を再コピー（フォント・素材は git 管理外のため）
if [ -f video/hyperframes.json ]; then
  node scripts/new_video.mjs --sync >>/tmp/tiktok-studio-setup.log 2>&1 || true
fi
exit 0
