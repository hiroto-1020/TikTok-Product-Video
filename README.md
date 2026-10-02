# TikTok Shop 商品動画スタジオ

商品素材・商品情報・参考動画を入れて Claude に一言送るだけで、
**15〜25 秒の TikTok 縦型商品広告（1080×1920 / 30fps / MP4）** を作るための作業場です。
コードを触る必要はありません。動画づくりには [HyperFrames](https://hyperframes.heygen.com)（公式 Skill 導入済み）を使います。

---

## はじめに（最初の 1 回だけ）

1. このリポジトリをパソコンに置く（例：`git clone https://github.com/hiroto-1020/TikTok-Product-Video.git`）
2. パソコンに **Node.js 22 以上**・**FFmpeg**・**Python 3** を入れる（Mac なら `brew install node ffmpeg python`）
3. このフォルダで Claude Code（デスクトップアプリ / ターミナル）を開き、「セットアップして」と送る
   → Claude が `bash scripts/setup.sh` を実行し、必要なフォルダ・ブラウザ・フォント・テンプレートを用意します

## 使い方（毎回これだけ）

```
商品素材をローカルフォルダへ入れる → brief.md を書く → Claude Code で動画を生成 → output/final/final.mp4
```

### 1. 素材を入れる（パソコン上のフォルダにコピーするだけ）

| フォルダ | 入れるもの |
|---|---|
| `input/current/product/images/` | 商品写真（正面・角度違い・パッケージ・使用シーンなど。JPG / PNG。大きいほど良い） |
| `input/current/product/videos/` | 商品動画（使用シーン・開封など。MP4 / MOV） |
| `input/current/product/logo/` | ブランドロゴ（あれば。PNG 透過 / SVG が理想） |
| `input/current/reference/videos/` | 「こんな雰囲気・テンポにしたい」TikTok 動画（MP4） |
| `input/current/reference/images/` | 色味・レイアウトの参考画像 |
| `input/current/audio/` | （任意）自分で用意した **商用利用OKの音源** |

参考動画からは **テンポ・カット割り・文字の出し方などの「見せ方」だけ** を真似します。商品やブランドはコピーしません。

### 2. `input/current/brief.md` を書く

商品名・特徴・ターゲット・入れたい言葉などを、わかる所だけ書きます。
**書いていない機能・価格・口コミは動画に入りません**（勝手に作らない仕組みです）。

### 3. Claude Code に送る

> この商品で動画案を作って

| | Claude がやること | あなたがやること |
|---|---|---|
| STEP 1 | 商品情報と素材を分析し、動画に使ってよい「事実」の一覧を作る | — |
| STEP 2 | 参考動画を分析（カット・テンポ・文字・色・音との合わせ方など） | — |
| STEP 3 | 3 つの動画案（A / B / C）を作る | — |
| STEP 4 | 各案の **シーンごとの静止画** を作って見せる（`preview/storyboard/`） | **A / B / C を選ぶ**（「Bで。2枚目の文字を大きく」など修正もOK） |
| STEP 5〜6 | 選んだ案で動画を制作（音楽・効果音・映像を同じリズムで設計） | — |
| STEP 7 | 完成動画を自己チェック（冒頭3秒・商品の見え方・字幕・テンポ・音・CTA・事実確認） | **ドラフト（`output/draft/`）を見て OK か修正を伝える** |
| 納品 | **`output/final/final.mp4`** を書き出す | TikTok に投稿 |

### 4. 次の商品へ

> 次の商品に進みたいので保管して

前回分（素材・企画・静止画・`final.mp4` など）は `archive/` にまとめて保管され、`input/current/` が空のテンプレートに戻ります。

---

## できあがる物の場所（すべてパソコンの中だけ）

| 場所 | 中身 |
|---|---|
| `preview/storyboard/A_overview.png` など | 3 案それぞれのシーン静止画の一覧 |
| `preview/storyboard/index.html` | 全案の静止画と説明（ブラウザで開く） |
| `planning/storyboard.md` | 3 案の説明 |
| `planning/beat-grid.md` | 何拍目に何が起きるかの設計表 |
| `output/draft/` | 確認用の動画と自己チェック結果（`review/…/self-review.md`） |
| `output/final/final.mp4` | **完成動画**（作り直した場合、前の版は `final_<日時>.mp4` として残ります） |

## GitHub に入るもの・入らないもの

| GitHub に入る（仕組み） | GitHub に入らない（パソコンの中だけ） |
|---|---|
| スクリプト（`scripts/`）、テンプレート（`templates/`・brief.md の雛形）、Skills と設定（`.claude/`）、HyperFrames / Remotion の設定、`CLAUDE.md`、`README.md` | 商品画像・商品動画・参考動画・音源・記入済み brief.md（`input/current/`）、企画ファイル（`planning/`）、静止画（`preview/`）、ドラフト・完成 MP4（`output/`）、一時ファイル（`temp/`・`renders/`）、制作中プロジェクト（`video/`）、保管庫（`archive/`） |

- **APIキー・パスワード・トークンは GitHub に入りません。** 必要になったときは `.env.example` をコピーした `.env` にだけ書きます（`.env` は自動で除外）。
- 万一これらをコミットしようとしても、コミット前チェック（`.githooks/pre-commit`）が止めます。

## 守っていること

- 存在しない機能・架空の価格・架空の口コミ・存在しない Before/After を作らない
- 商品の形を変えない
- 医療・美容の効果を言い切らない
- 参考動画の商品・ブランド・コピーは使わない
- 投稿時は「#PR」など広告であることの表記を入れてください（ステルスマーケティング規制）

## よくある質問

- **BGM は？** 3 通りから選べます：①自分で用意した音源 ②動画には効果音だけ入れ、TikTok アプリの商用音楽ライブラリで曲を付ける（動画は指定のテンポで作ってあるので、近いテンポの曲を選ぶ）③その他（相談）。
- **言葉を直したい / 色を変えたい** → 「2シーン目の文字を『〇〇』に」のように伝えるだけでOK。
- **環境が壊れたかも** → 「セットアップを確認して」と送ってください。
- **素材や動画のバックアップは？** GitHub には入らないので、必要なら `archive/` フォルダごと外付けドライブやクラウドストレージにコピーしてください。

---

<details>
<summary>技術メモ（Claude 用・読まなくてOK）</summary>

- 手順の正本: `CLAUDE.md` と `.claude/skills/tiktok-shop-video/SKILL.md`
- HyperFrames 公式 Skills: `.claude/skills/`（`npx skills add heygen-com/hyperframes` で導入、`bash scripts/setup.sh --update` で更新）
- 環境準備: `bash scripts/setup.sh`（フォルダ・雛形・Git の安全設定も行う。クラウドでは SessionStart フックが自動実行）
- Git 方針: `.gitignore`（ローカル専用パス・動画・秘密情報）+ `.githooks/pre-commit`（コミット前チェック）
- 補助スクリプト: `scripts/`（参考動画計測・Beat Grid・代表静止画・プロジェクト作成・自己レビュー・納品・保管）
- 予備レンダラー: `remotion/`（HyperFrames より適している場合のみ）
- フォント: `assets/fonts/fonts.css`（実体は setup が Google Fonts から取得・すべて OFL）
- GSAP: `assets/vendor/`（CDN 遮断対策でローカル同梱）
- 効果音: HyperFrames media-use 同梱（Pixabay ライセンス・商用可）

</details>
