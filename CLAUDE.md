# TikTok Shop 商品動画スタジオ

TikTok Shop アフィリエイト用の縦型商品紹介動画（**1080×1920 / 9:16 / 30fps / MP4 / 15〜25 秒**）を継続的に作るための作業場。
ユーザーはプログラミング初心者。**コマンド実行・ファイル編集・インストールはすべて Claude が行う**。ユーザーへの返答は日本語で、専門用語を避けて短く。

## 依頼と手順の対応

| ユーザーの言葉（例） | やること |
|---|---|
| 「この商品で動画案を作って」「動画案」 | `/tiktok-shop-video` の STEP 0〜4 → A/B/C の代表静止画を見せて **止まる** |
| 「Bで作って」「Aの〜を直してCで」 | STEP 5〜7 → ドラフト MP4 と自己レビューを見せて **止まる** |
| 「OK」「これで納品」 | 最終書き出し → `output/final/` |
| 「ここを直して」 | 該当 STEP に戻って修正（レイアウト変更なら静止画から） |
| 「次の商品」「保管して」 | `bash scripts/archive.sh <名前>` |

詳細手順は必ず **`.claude/skills/tiktok-shop-video/SKILL.md`** を読んでから実行する。

## 基本方針

- 動画制作は **HyperFrames** が原則。公式 Skill（`.claude/skills/hyperframes*`, `general-video`, `media-use` など。入口は `/hyperframes`）とそのベストプラクティスを優先する。
- HyperFrames より明確に適している場合のみ `remotion/`（Remotion）を使う。理由をユーザーに説明してから。
- 制作順序は固定：STEP 1 商品分析 → 2 参考動画の文法抽出 → 3 Storyboard 3 案 → 4 代表静止画 →（ユーザーが選ぶ）→ 5 制作 → 6 Beat Grid 同期 → 7 自己レビュー。
  **いきなり完成 MP4 を作らない。**
- 音楽・効果音・映像は共通の Beat Grid（`planning/shot-plan.json` → `python3 scripts/beatgrid.py` → `planning/beat-grid.md`）で管理する。

## 絶対ルール

- 存在しない商品機能を追加しない（画面の事実は `planning/facts.md` の ID に紐づくものだけ）。
- 商品形状を改変しない（等倍率スケールのみ・歪み/描き足し/色替え/AI 再生成なし）。
- 架空レビュー・架空価格・存在しない Before/After を作らない。
- 医療・美容効果を断定しない。根拠のない「No.1」「最安」等も使わない。
- 参考動画は「映像表現の文法」だけを参考にし、商品・ブランド・コピー・人物・固有の画はコピーしない。

## 技術メモ

- 初回/新しいクラウドセッションでは最初に `bash scripts/setup.sh`（Chrome Headless Shell・日本語フォント・npm を用意）。
- CDN（cdn.jsdelivr.net）はネットワークで遮断されることがある → GSAP は `assets/vendor/gsap.min.js` を使う（`scripts/new_video.mjs` が自動で置き換える）。
- フォント実体は git 管理外。`assets/fonts/fonts.css` の @font-face をコンポジション内に書く（`new_video.mjs` が自動挿入）。
- 新しいセッションで `video/` を再開するときは `node scripts/new_video.mjs --sync` で素材を再コピーしてから preview/render。
- `video/CLAUDE.md` は HyperFrames が生成したプロジェクト規約。`video/` 内の作業ではそれにも従う。
- HyperFrames CLI はリポジトリ直下の `package.json` で固定（`npx hyperframes`）。更新は `bash scripts/setup.sh --update`。
- ユーザーに見せる成果物（静止画・MP4）は、作業ブランチにコミット・push してから案内する。
