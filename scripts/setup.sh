#!/usr/bin/env bash
# 制作環境のセットアップ（何度実行しても安全）。
#   bash scripts/setup.sh            … 必要なものを揃える
#   bash scripts/setup.sh --check    … 状態確認だけ（何もインストールしない）
#   bash scripts/setup.sh --update   … HyperFrames CLI / Skills も最新化する
set -u
cd "$(dirname "$0")/.."
ROOT="$(pwd)"

MODE="install"
case "${1:-}" in
  --check) MODE="check" ;;
  --update) MODE="update" ;;
esac

ok()   { printf "  \033[32m✓\033[0m %s\n" "$*"; }
warn() { printf "  \033[33m!\033[0m %s\n" "$*"; }
fail() { printf "  \033[31m✗\033[0m %s\n" "$*"; }
STATUS=0

echo "== 0. フォルダ構成・Git の安全設定 =="
# 商品素材・企画・プレビュー・出力・一時ファイルはローカル専用（.gitignore 済み）。無ければ作る。
for d in input/current/product/images input/current/product/videos input/current/product/logo \
  input/current/reference/videos input/current/reference/images input/current/audio \
  planning/reference-analysis preview/storyboard output/draft output/final temp archive; do
  mkdir -p "$d"
done
if [ ! -f input/current/brief.md ]; then cp templates/brief.md input/current/brief.md && ok "input/current/brief.md をテンプレートから作成"; fi
for f in templates/planning/*; do
  [ -f "planning/$(basename "$f")" ] || cp "$f" "planning/$(basename "$f")"
done
ok "作業フォルダ（input / planning / preview / output / temp / archive）"
if git rev-parse --git-dir >/dev/null 2>&1; then
  if [ "$(git config --get core.hooksPath || true)" != ".githooks" ]; then
    git config core.hooksPath .githooks && ok "コミット前チェック（.githooks/pre-commit）を有効化"
  else
    ok "コミット前チェック有効（素材・動画・秘密情報のコミットを防止）"
  fi
  LEAK="$(git ls-files -- input/current planning preview output temp archive video | grep -v '\.gitkeep$' || true)"
  SECRET="$(git ls-files | grep -E '(^|/)\.env($|\.)|\.pem$|\.key$|credentials|settings\.local\.json' | grep -v '\.env\.example$' || true)"
  if [ -n "$LEAK" ]; then warn "ローカル専用のはずのファイルが Git 管理されています:"; printf '      %s\n' $LEAK; fi
  if [ -n "$SECRET" ]; then fail "秘密情報の可能性があるファイルが Git 管理されています:"; printf '      %s\n' $SECRET; STATUS=1; fi
fi

echo "== 1. 基本ツール =="
if command -v node >/dev/null 2>&1; then
  NODE_MAJOR="$(node -p 'process.versions.node.split(".")[0]')"
  if [ "$NODE_MAJOR" -ge 22 ]; then ok "Node.js $(node -v)"; else fail "Node.js 22 以上が必要です（現在 $(node -v)）"; STATUS=1; fi
else
  fail "Node.js が見つかりません（https://nodejs.org から 22 以上を入れてください）"; STATUS=1
fi
if command -v ffmpeg >/dev/null 2>&1 && command -v ffprobe >/dev/null 2>&1; then
  ok "FFmpeg $(ffmpeg -version | head -1 | awk '{print $3}')"
else
  fail "FFmpeg / ffprobe が見つかりません（Mac: brew install ffmpeg）"; STATUS=1
fi
if command -v python3 >/dev/null 2>&1; then ok "Python $(python3 -V | awk '{print $2}')"; else fail "python3 が見つかりません"; STATUS=1; fi

echo "== 2. HyperFrames CLI =="
if [ "$MODE" != "check" ]; then
  if [ ! -d node_modules/hyperframes ]; then
    npm install --no-audit --no-fund >/dev/null 2>&1 && ok "npm install 完了" || { fail "npm install に失敗"; STATUS=1; }
  fi
  if [ "$MODE" = "update" ]; then
    LATEST="$(npm view hyperframes version 2>/dev/null || true)"
    if [ -n "$LATEST" ]; then
      npm install --no-audit --no-fund --save-dev "hyperframes@$LATEST" >/dev/null 2>&1 && ok "hyperframes を $LATEST に更新"
    fi
  fi
fi
if [ -x node_modules/.bin/hyperframes ]; then
  ok "hyperframes $(npx --no-install hyperframes --version 2>/dev/null | tail -1)"
else
  fail "hyperframes 未インストール（bash scripts/setup.sh を実行）"; STATUS=1
fi

echo "== 3. レンダリング用ブラウザ (Chrome Headless Shell) =="
CHROME="$(npx --no-install hyperframes browser path 2>/dev/null | tail -1 || true)"
if [ -n "$CHROME" ] && [ -x "$CHROME" ]; then
  ok "Chrome: 準備済み"
elif [ "$MODE" != "check" ]; then
  npx --no-install hyperframes browser ensure >/dev/null 2>&1 && ok "Chrome をダウンロードしました" || { fail "Chrome の準備に失敗（npx hyperframes browser ensure）"; STATUS=1; }
else
  warn "Chrome 未準備（bash scripts/setup.sh で自動取得）"
fi

echo "== 4. GSAP（ローカル同梱） =="
if [ -s assets/vendor/gsap.min.js ]; then ok "assets/vendor/gsap.min.js"; else fail "assets/vendor/gsap.min.js がありません"; STATUS=1; fi

echo "== 5. 日本語フォント (OFL / Google Fonts) =="
FONT_BASE="https://raw.githubusercontent.com/google/fonts/main/ofl"
# ファイル名|リポジトリ内パス
FONTS="NotoSansJP-Variable.ttf|notosansjp/NotoSansJP%5Bwght%5D.ttf
NotoSerifJP-Variable.ttf|notoserifjp/NotoSerifJP%5Bwght%5D.ttf
DelaGothicOne-Regular.ttf|delagothicone/DelaGothicOne-Regular.ttf
MPLUSRounded1c-ExtraBold.ttf|mplusrounded1c/MPLUSRounded1c-ExtraBold.ttf
ZenKakuGothicNew-Black.ttf|zenkakugothicnew/ZenKakuGothicNew-Black.ttf
ZenMaruGothic-Black.ttf|zenmarugothic/ZenMaruGothic-Black.ttf
ShipporiMinchoB1-ExtraBold.ttf|shipporiminchob1/ShipporiMinchoB1-ExtraBold.ttf
RocknRollOne-Regular.ttf|rocknrollone/RocknRollOne-Regular.ttf
MochiyPopOne-Regular.ttf|mochiypopone/MochiyPopOne-Regular.ttf"
mkdir -p assets/fonts
MISSING=0
while IFS='|' read -r NAME PATHPART; do
  [ -z "$NAME" ] && continue
  if [ -s "assets/fonts/$NAME" ]; then continue; fi
  if [ "$MODE" = "check" ]; then MISSING=$((MISSING+1)); continue; fi
  if curl -fsSL --max-time 180 -o "assets/fonts/$NAME.part" "$FONT_BASE/$PATHPART"; then
    mv "assets/fonts/$NAME.part" "assets/fonts/$NAME"
  else
    rm -f "assets/fonts/$NAME.part"; MISSING=$((MISSING+1))
  fi
done <<EOF
$FONTS
EOF
if [ "$MISSING" -eq 0 ]; then ok "フォント 9 種類 準備済み (assets/fonts/)"; else warn "フォント $MISSING 個が未取得（Noto Sans JP は HyperFrames 内蔵なので制作は可能）"; fi

echo "== 6. HyperFrames Skills =="
if [ -f .claude/skills/hyperframes/SKILL.md ]; then ok "公式 Skills 導入済み (.claude/skills/)"; else fail "公式 Skills がありません"; STATUS=1; fi
if [ "$MODE" = "update" ]; then
  npx -y skills add heygen-com/hyperframes --agent claude-code -y >/dev/null 2>&1 || warn "npx skills add に失敗"
  npx --no-install hyperframes skills update >/dev/null 2>&1 || warn "hyperframes skills update に失敗"
  # このスタジオ独自の手順 Skill が消えていたら git から戻す
  if [ ! -f .claude/skills/tiktok-shop-video/SKILL.md ]; then git checkout -- .claude/skills/tiktok-shop-video 2>/dev/null || true; fi
  ok "Skills を最新化しました"
fi
if [ -f .claude/skills/tiktok-shop-video/SKILL.md ]; then ok "制作手順 Skill (tiktok-shop-video)"; else fail "tiktok-shop-video Skill がありません"; STATUS=1; fi
if [ "$MODE" = "check" ] && [ -x node_modules/.bin/hyperframes ]; then
  npx --no-install hyperframes skills check >/dev/null 2>&1 && ok "HyperFrames Skills は最新" || warn "HyperFrames Skills に更新あり（bash scripts/setup.sh --update）"
fi

echo
if [ "$STATUS" -eq 0 ]; then echo "セットアップOK：制作を始められます。"; else echo "未解決の項目があります（上の ✗ を確認）。"; fi
exit "$STATUS"
