---
name: tiktok-shop-video
description: >
  このリポジトリ専用の TikTok Shop アフィリエイト商品紹介動画（1080x1920 / 30fps / MP4 / 15〜25秒）の制作手順。
  「この商品で動画案を作って」「動画案」「Aで作って / Bで / Cで」「この案で制作」「修正して」「納品して」
  「次の商品」「保管して」などの依頼、または input/current/ の商品素材・参考動画から動画を作る依頼で必ず使う。
  STEP 1 商品分析 → STEP 2 参考動画の文法抽出 → STEP 3 Storyboard 3案 → STEP 4 代表静止画 →（ユーザーが選択）→
  STEP 5 HyperFrames で制作 → STEP 6 Beat Grid で音・映像を同期 → STEP 7 自己レビュー → 承認後に最終書き出し。
---

# TikTok Shop 商品動画スタジオ — 制作手順

このスキルは **手順と品質ゲート** を定める。映像の作り方そのものは HyperFrames 公式 Skill
（`/hyperframes` → `/general-video`, `/hyperframes-core`, `/hyperframes-animation`, `/hyperframes-creative`,
`/media-use`, `/hyperframes-audio`, `/hyperframes-cli`, `/hyperframes-registry`）に従い、
**公式 Skill とこのスキルが矛盾したら公式 Skill を優先**する（ただし下の「絶対ルール」と「ユーザーの確認ポイント」は常に守る）。

ユーザーはプログラミング初心者。コマンド・ファイル編集はすべて Claude が行い、ユーザーには
「何ができたか」「どれを選ぶか」「何を直したいか」だけを、日本語で短く聞く。

## 絶対ルール（事実と表現）

1. **存在しない商品機能を追加しない。** 画面テキスト・ナレーションの事実は `planning/facts.md` の ID（F1, F2…）に紐づくものだけ。
2. **商品形状を改変しない。** 商品画像/動画は `object-fit: contain`・等倍率スケールのみ。変形・歪み・部分的な描き足し・色の差し替え・AI での作り直しをしない（背景の切り抜きは形を変えない範囲でのみ可）。
3. **架空レビューを作らない。** 星評価・口コミ・「みんな使ってる」・販売数・ランキングは、ユーザーが資料を出した場合のみ。
4. **架空価格を作らない。** 価格・割引・クーポン・期間は brief に書かれた通りのみ。書かれていなければ表示しない。
5. **存在しない Before/After を作らない。** 実際の素材がない比較画像・効果の再現映像を作らない。
6. **医療・美容効果を断定しない。** 「治る」「消える」「必ず痩せる」「〜に効く」等は使わない。根拠資料がない機能的効果も言い切らない（薬機法・景品表示法を意識）。「No.1」「最安」「業界初」も根拠がなければ使わない。
7. **参考動画はコピーしない。** 借りるのは「映像表現の文法」（構成・テンポ・動き・文字の出し方・色の使い方・同期の仕方）だけ。参考動画の商品・ブランド・ロゴ・コピー文・人物・固有の画は使わない。
8. 不明な情報は推測で埋めず、ユーザーに確認するか、使わない。

## ユーザーの確認ポイント（必ず止まる）

- **STEP 4 の後**：A/B/C の代表静止画を見せて、選択（または混合・修正指示）を待つ。**選択前に完成 MP4 を作らない。**
- **STEP 7 の後**：ドラフト MP4 と自己レビュー結果を見せて、承認または修正指示を待つ。**承認前に `output/final/final.mp4` を書き出さない。**

## フォルダ

| 場所 | 中身 |
|---|---|
| `input/current/brief.md` | ユーザーが書く商品ブリーフ |
| `input/current/product/{images,videos,logo}/` | 商品素材 |
| `input/current/reference/{videos,images}/` | 参考動画・参考画像 |
| `input/current/audio/` | （任意）ユーザーが用意した商用利用可の音源 |
| `planning/` | product-analysis.md, facts.md, style-guide.md, storyboard.md, shot-plan.json, beat-grid.md, reference-analysis/ |
| `preview/storyboard/` | 代表静止画（`<案>/<シーン>.png`, `<案>_overview.png`, `index.html`）。`_src/<案>/` は静止画用 HyperFrames プロジェクト |
| `video/` | 選ばれた案の HyperFrames プロジェクト（制作のたびに新規作成） |
| `output/draft/` | ドラフト MP4 と `review/<名前>/`（機械チェック + 自己レビュー） |
| `output/final/final.mp4` | 承認済みの納品 MP4（前の版は `final_<日時>.mp4` に自動退避） |
| `archive/` | 過去の制作一式 |
| `temp/` | 一時ファイル（スクリプトが自動で使う・消してよい） |
| `remotion/` | 予備（HyperFrames より明確に適している場合のみ。`remotion/README.md`） |
| `scripts/` | 補助スクリプト（下表） |

| スクリプト | 用途 |
|---|---|
| `bash scripts/setup.sh` (`--check`, `--update`) | 環境準備 / 確認 / HyperFrames CLI・Skills の最新化 |
| `python3 scripts/inspect_product.py` | 商品素材の一覧・解像度・透過・パレット・一覧画像 |
| `python3 scripts/analyze_reference.py` | 参考動画の計測（カット・ショット長・BPM・カットの拍一致・色・音量）と確認用シート |
| `python3 scripts/beatgrid.py` (`--option X`, `--music <file>`, `--suggest <秒>`) | Beat Grid の計算・検証・`planning/beat-grid.md` 生成 |
| `node scripts/storyboard_stills.mjs --init` / `node scripts/storyboard_stills.mjs [X]` | 代表静止画プロジェクトの雛形作成 / HyperFrames snapshot で静止画化 |
| `node scripts/new_video.mjs --option X` / `--sync` | 選ばれた案の HyperFrames プロジェクト `video/` を作成 / 素材の再コピー |
| `python3 scripts/review_video.py <mp4>` | 書き出し後の機械チェックと確認用シート |
| `bash scripts/finalize.sh <mp4>` | 承認済み MP4 をラウドネス調整して `output/final/final.mp4` へ |
| `bash scripts/archive.sh <名前>` | 1 本分を `archive/` に保管して作業フォルダを初期化 |

---

## STEP 0 — 準備（毎回・黙って実行）

1. `bash scripts/setup.sh` を実行（フォルダ構成・brief/planning の雛形・Chrome・フォント・npm・コミット前チェックを用意。何度実行しても安全）。✗ があれば解決してから進む。
2. HyperFrames Skills の鮮度確認：`npx hyperframes skills check`。古ければ `bash scripts/setup.sh --update` を実行し、
   `.claude/skills/tiktok-shop-video/` が消えていないか確認（消えたら `git checkout -- .claude/skills/tiktok-shop-video`）。
   HyperFrames CLI の更新内容（旧→新バージョン）は報告に一言含める。
3. 入力チェック：`input/current/brief.md` が埋まっているか、`product/` に素材があるか、`reference/` に参考があるか。
   - 商品素材や商品名が無い → 何を入れればよいか具体的に伝えて止まる。
   - brief が一部空欄 → 進めてよいが、空欄は「使わない情報」として扱い、最後に確認事項として挙げる。
   - 参考動画が無い → HyperFrames の house style（`/hyperframes-creative` → `house-style.md`）で進めてよいが、そう伝える。
   - HEIC など読めない形式 → ffmpeg で JPG/PNG に変換して同じフォルダに置く（元ファイルは残す）。
4. 前の制作物（`video/` や埋まった `planning/`）が残っていて別商品なら、ユーザーに確認して `bash scripts/archive.sh <前の名前>`。

## STEP 1 — 商品情報を分析

1. `python3 scripts/inspect_product.py` → `planning/product-assets.png` を見て、必要な素材は個別にも見る（実物の形・色・ロゴ・パッケージの文字）。
2. `brief.md` を読む。商品ページ URL があれば WebFetch で確認してよい（出典として URL を記録）。
3. `planning/facts.md` に事実台帳を作る：ID / 事実 / 出典（brief・パッケージ写真の文字・URL）/ 動画での言い換え可否。
   パッケージに写っている文字は「写真で読める範囲」だけ。推測した効能・スペックは書かない。
4. `planning/product-analysis.md` を書く：何の商品か、誰のどんな場面か、一番の訴求点（1つ）、素材ごとの使い道と注意（解像度・背景・切り抜き可否）、背景色との相性、足りない情報。

## STEP 2 — 参考動画・画像の「文法」を抽出

1. `python3 scripts/analyze_reference.py` → `planning/reference-analysis/summary.md` と各 `analysis.json`。
2. 画像を見る（まとめて見る：シートを優先）：`contact_sheet.png`（1ショット1枚）→ `hook_sheet.png`（冒頭3秒・6fps）→ 必要なら `timeline_sheet.png` と `shots/NN.png`（各ショットの 最初|中間|最後 → カメラワーク・文字の動き・イージング）。
3. `planning/style-guide.md` を埋める。**必須の抽出項目**：カット構成 / テンポ / カメラワーク / 文字の動き / タイポグラフィ / 色 / 余白 / イージング / トランジション / 音との同期 / 1シーンの長さ。
   数値（ショット長・最初のカット・BPM・カットの拍一致率・パレット）は計測値を根拠として書く。
   見た目の判断（書体の印象、ポップかスライドか、オーバーシュートの有無）は「どのシートの何秒で見たか」を添える。
4. 最後に「採用する文法」と「採用しない要素（参考動画固有の商品・ブランド・コピー・人物・画）」を明記。
   タイポグラフィは `assets/fonts/fonts.css` の書体（Noto Sans JP 100–900 / Dela Gothic One / M PLUS Rounded 1c / Zen Kaku Gothic New / Zen Maru Gothic / Shippori Mincho B1 / Noto Serif JP / RocknRoll One / Mochiy Pop One）から近いものを選ぶ。

## STEP 3 — 商品に最適化した Storyboard を 3 案（A / B / C）

先に読む：`/hyperframes-creative` → `references/story-spine.md`, `beat-direction.md`, `house-style.md`, `video-composition.md`, `typography.md`、
`/hyperframes` → `references/pitch-round.md`（サンプリングの考え方。ただし案の数はユーザー指定の **3 案**）。

- 3 案は「同じ動画の色違い」にしない。冒頭フックの種類・構成・シルエット（画面の主要要素の配置）が異なること。目安：
  - **A**：参考動画の文法に最も忠実に、この商品へ最適化した案
  - **B**：商品の一番の強み（facts の核）を最大化する、別の切り口の案
  - **C**：あえて定番から外した意外性のある案（ただし事実ルールの範囲内）
- TikTok 広告として：0 フレーム目から意味のある画（黒・フェードイン始まり禁止）、**1〜2 秒以内に強いフック**、**3 秒以内に商品を明確に見せる**、1 シーン 1 メッセージ、テロップは 1 行 ~13 文字・64px 以上・セーフゾーン内（上 160 / 下 480 / 左 60 / 右 140 px）、最後 2〜3 秒に CTA。
- CTA は事実の範囲で（例：「左下のカートからチェック」「詳しくは商品リンクへ」）。「今だけ」「残りわずか」は brief に根拠がある場合のみ。
- BPM を決める：参考動画の BPM、ユーザー音源の BPM（`python3 scripts/beatgrid.py --music input/current/audio/<file> --option X`）、
  または拍がフレームに揃う値（`python3 scripts/beatgrid.py --suggest 20` → 90/100/120/150 BPM）。
- `planning/shot-plan.json` に 3 案を書く（各シーン：id `A-01` 形式, role, beat, beats, visual, assets, text[{copy, style, beat}], camera, motion, easing, transition_out, sfx[{beat, name}], facts[ID]）。
  SFX 名は `.claude/skills/media-use/audio/assets/sfx/manifest.json` の名前（whoosh-short, pop, impact-bass-1, riser, sparkle, click など。Pixabay ライセンス・商用可）。
- `python3 scripts/beatgrid.py` を実行し、警告（尺 15〜25 秒外、隙間、文字の表示時間不足、存在しない事実 ID）をすべて解消。
- `planning/storyboard.md` に 3 案の説明（コンセプト / 借りた文法 / なぜこの商品に合うか / 尺・BPM / シーン一覧）と、おすすめとその理由を書く。

## STEP 4 — 各シーンの代表静止画（動画はまだ作らない）

HyperFrames の review loop（`/hyperframes` → `references/review-loop.md` § 2、`/hyperframes-creative` → `references/storyboard-recipe.md`）に沿った「スケッチ」を、9:16 の実寸で作る。

1. `node scripts/storyboard_stills.mjs --init` → `preview/storyboard/_src/{A,B,C}/index.html`（各シーン = 1 秒の静止クリップ、`assets/` に商品素材・フォント・GSAP がコピー済み）。
2. 各シーンの `<section id="A-01" class="clip scene" data-start=… data-duration="1">` の中を、そのシーンの **キーモーメント（一番見せたい瞬間の完成レイアウト）** に描き直す：
   実際の商品画像、確定コピー（一字一句）、選んだ書体・色・余白。動き（GSAP）は付けない。
   後の制作でこのレイアウトを「着飾る」ので、ここで配置・階層・コピーを決め切る。
3. `node scripts/storyboard_stills.mjs` → `preview/storyboard/<案>/<シーン>.png`（1080×1920）、`<案>_overview.png`、`_checks/<案>_safezone.png`、`index.html`。
4. 自分で `A_overview.png` などと `_checks/*_safezone.png` を見て確認：商品が歪んでいない／文字がセーフゾーン内／読める大きさ／1 行の不自然な改行（1 文字だけの行）なし／コントラスト。直して再実行。
5. **ユーザーに提示して止まる**：
   - 各案の 1 行コンセプト、尺・BPM、シーン数、フックの内容、おすすめ案と理由
   - 画像：`preview/storyboard/A_overview.png`, `B_overview.png`, `C_overview.png`（ローカルのファイルとして案内。SendUserFile が使えるなら 3 枚を送る）、一覧ページ `preview/storyboard/index.html`
   - 事実確認で使えなかった情報・確認したいこと
   - 質問：「A / B / C のどれで作りますか？（混ぜる・直すも可）」

## STEP 5 — 選ばれた案で制作（HyperFrames）

ユーザーの選択・修正指示を `planning/storyboard.md` の「選択結果」と `shot-plan.json` に反映。レイアウトが変わる修正なら、
**先に静止画を直して再提示**（STEP 4 に戻る）。レイアウトが確定したら：

1. `node scripts/new_video.mjs --option X` → `video/`（`hyperframes init --resolution portrait` 済み・GSAP ローカル化・フォント @font-face・素材/SFX コピー済み・尺設定済み）。
2. HyperFrames の作法で進める（`/hyperframes` の表に従い、`/general-video` の手順。読み込み必須：`/hyperframes-core`、`/hyperframes-animation`、`/hyperframes-creative` の house-style / video-composition、音は `/media-use` と `/hyperframes-audio`）。
   最初に `npx hyperframes skills update general-video`。
3. `video/BRIEF.md`（`/hyperframes` → `references/brief-format.md` 形式。`workflow: general-video`, `flow: companion`, `storyboard: yes`, `destination: tiktok`, `aspect: 1080x1920`, `language: ja`, `length`, `message`）、
   `video/frame.md`（style-guide からデザイン仕様：パレット・書体の役割・サイズ・イージング・禁止事項）、
   `video/STORYBOARD.md`（`references/storyboard-format.md` 形式。各 Frame に `src: compositions/frames/NN-<role>.html`、確定スケッチは `preview/storyboard/_src/X/index.html#X-NN`）を書く。
4. 見た目の効果（グリッチ・フィルムグレイン・シャイン等）やトランジションは、手作りする前に `npx hyperframes catalog --query "<英語で効果>" --json` で探し、あれば `npx hyperframes add <name>`。
5. シーンを作る：確定スケッチのレイアウトを **描き直さず** 着飾る（動き・トランジション・質感）。各シーンの動きは `/hyperframes-animation` の blueprint / rules を名前で引用して作る。
   - すべての時刻は Beat Grid から：`shot-plan.json` の `start_s` / `at_s`（`python3 scripts/beatgrid.py` で計算済み）をそのまま使う。手で秒数を作らない。
   - テキストは最初の動きがシーン開始から 0.2 秒以内。読み終わる前に消さない。
   - 商品画像は `object-fit: contain`。スケール・移動・回転・マスクは可、変形（非等倍・歪み・ワープ）は不可。
   - GSAP は `assets/vendor/gsap.min.js`（CDN はブロックされることがある）。決定的であること（`Math.random`・時計・ネットワーク禁止）。
6. 途中確認：`cd video && npx hyperframes lint`、仕上げに `npx hyperframes check`（エラー 0 にする）、
   `npx hyperframes snapshot video --at <各シーン中点>` で見た目確認。
7. ドラフト書き出し：`cd video && npx hyperframes render --quality looks --output ../output/draft/<商品名>_v1.mp4`（修正ごとに v2, v3…）。
   ローカル環境でユーザーが見られる場合は `npx hyperframes preview --background` の Studio URL も案内してよい。ドラフト MP4 もプレビューとして案内する。

## STEP 6 — 音楽・効果音・映像を共通の Beat Grid で設計

- 単位は **拍（Beat 1 始まり）**。`planning/beat-grid.md`（自動生成）が「Beat 1 HOOK / Beat 5 商品登場 / Beat 9 特徴1 …」の一覧。
  カット・テキスト出現・SFX・主要な動きのピークはすべて拍（または半拍）に置く。
- 音楽の方針（brief の指定 → なければ確認）：
  1. **ユーザー音源**（`input/current/audio/`）：`python3 scripts/beatgrid.py --music video/assets/audio/<file> --option X` で BPM・最初の拍を計測。
     `<audio id="bgm" data-timeline-role="music" data-media-start="<最初の拍の秒>" …>` で Beat 1 = 0 秒に合わせる。必要なら `npx hyperframes beats video` で Studio 用ビートも生成。
  2. **TikTok の商用音楽ライブラリで後付け**（アフィリエイトで一般的）：動画には SFX のみ入れ、BGM は入れない。設計した BPM をユーザーに伝え、近い BPM の曲を選ぶよう案内する。
  3. **生成/検索**（`/media-use` の BGM：HeyGen 検索は要サインイン、MusicGen は低速）：ユーザーが希望した場合のみ。
  ※ 権利の分からない曲（参考動画の音源を含む）は使わない。
- SFX：`video/assets/sfx/` から。`<audio id="sfx-NN" src="assets/sfx/<name>.mp3" data-start="<at_s>" …>`。入れすぎない（1 シーン 1〜2 個）。
- ナレーションを入れる場合は `/media-use` の TTS と `/hyperframes-audio` の carve（BGM の下げ）に従う。

## STEP 7 — 自己レビュー（完成後に必ず）

1. `python3 scripts/review_video.py output/draft/<file>.mp4` → `output/draft/review/<file>/report.md` と
   `hook_sheet.png`（0〜3 秒）, `scenes_sheet.png`, `scenes_safezone.png` を見る。
2. `output/draft/review/<file>/self-review.md` を書く。各項目に ◎/○/△/× と根拠（何秒・どの画像）と修正内容：
   | 項目 | 見るポイント |
   |---|---|
   | 冒頭 1〜3 秒 | 0 フレーム目から意味のある画か／1〜2 秒でスクロールを止める理由があるか／3 秒以内に商品が出るか |
   | 商品視認性 | 大きさ・明るさ・背景との分離・歪みなし・ロゴ/パッケージが読める |
   | 字幕・テロップ | 読める大きさと時間（約 8 文字/秒）・セーフゾーン内・誤字なし・不自然な改行なし |
   | テンポ | ショット長が style-guide の文法と合っているか・間延び/詰め込みなし |
   | 音との同期 | カット・文字・SFX が Beat Grid に乗っているか（report の一致数）・ラウドネス |
   | 広告としての魅力 | 1 つのメッセージが伝わるか・欲しくなる理由があるか |
   | CTA | 最後に何をすればいいか明確か・セーフゾーン内・誇張なし |
   | 事実確認 | 画面上の全テキストを facts.md の ID と照合（表にする）・絶対ルール 1〜8 の違反なし |
3. △/× があれば直して再レンダー（v2…）→ 再レビュー。機械チェックの FAIL は必ず解消。
4. **ユーザーに提示して止まる**：ドラフト MP4 のパス（SendUserFile が使えるなら送る）、自己レビューの要約、残る確認事項。
5. 承認されたら：`cd video && npx hyperframes render --quality delivery --output ../output/draft/<商品名>_delivery.mp4` →
   `bash scripts/finalize.sh output/draft/<商品名>_delivery.mp4` → **`output/final/final.mp4`** → `python3 scripts/review_video.py output/final/final.mp4` で最終確認。
   完成の案内は「`output/final/final.mp4` ができました」と場所をはっきり伝える。
6. 納品時の一言：投稿時はキャプションに「#PR」等の広告表記を入れること（ステルスマーケティング規制）を案内する。
   HyperFrames の recipe 保存（`/hyperframes` → `review-loop.md` § 4）は、ユーザーが同じ型を量産したいと言ったときに提案。

## 次の商品へ

ユーザーが「次の商品」「保管して」と言ったら `bash scripts/archive.sh <商品名の英数字>`（`output/final/final.mp4` も一緒に保管され、次の商品で上書きされない）。
`input/current/` と `planning/` がテンプレートに戻るので、ユーザーは新しい素材を入れて brief.md を書けばよい。

## Remotion を使う条件

原則 HyperFrames。次の場合のみ `remotion/` を使い、使う理由をユーザーに説明してから進める：
同じ型の大量バリエーションを React のデータ駆動で量産する、既存の Remotion 資産を使う、Remotion 固有ライブラリが必要。
仕様・STEP・Beat Grid・絶対ルールは同じ。既存 Remotion 作品の HyperFrames 化は `/remotion-to-hyperframes`。

## Git のルール（ローカル運用）

**Git に入れるのは「仕組み」だけ**：`scripts/`・`templates/`（brief.md の雛形含む）・`.claude/`（Skills・設定・フック）・
`CLAUDE.md`・`README.md`・`package.json`・`assets/fonts/fonts.css`・`assets/vendor/`・`remotion/` の設定とソース・`.gitignore`・`.githooks/`・`.env.example`。

**Git に入れないもの（ローカルのみ・`.gitignore` 済み）**：`input/current/` の全部（brief.md・商品画像/動画・参考動画・音源）、`planning/` の中身、
`preview/`、`output/`（ドラフト・final.mp4）、`temp/`、`renders/`、`snapshots/`、`video/`（商品ごとの HyperFrames プロジェクト）、`archive/`、フォント実体、すべての動画ファイル。

**秘密情報（APIキー・トークン・認証情報）は絶対にコミットしない**：使う場合は `.env`（Git 管理外）にだけ書き、コード・ドキュメント・ログ・コミットメッセージに値を書かない。
`git add -f` / `--no-verify` は使わない。`.githooks/pre-commit` が素材・動画・5MB 超・秘密情報らしき文字列のコミットを止める。

- 制作作業（STEP 1〜7）ではコミットしない。成果物はローカルのファイルとして案内する。
- 仕組み（スクリプト・テンプレート・Skill）を直したときだけ、ユーザーに確認してからコミットする。
