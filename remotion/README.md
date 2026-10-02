# remotion/ — 予備のレンダラー（原則は使わない）

このスタジオの標準は **HyperFrames**（`video/`）です。Remotion は次のような
「HyperFrames より Remotion の方が明確に向いている」動画のときだけ Claude が使います。

- React コンポーネントで大量のデータ駆動パターンを量産したい（例：同じ型で 50 商品分を一括生成）
- 既存の Remotion 資産・テンプレートを流用したい
- Remotion 固有のライブラリ（@remotion/lottie, @remotion/three 等）が必要

使う場合も仕様・制作フロー（STEP 1〜7）・Beat Grid・事実確認ルールは同じです。

```bash
cd remotion
npm install            # 初回のみ
bash render.sh still   # 確認用の静止画 → remotion/out/still.png
bash render.sh render  # MP4 → output/draft/remotion_<日時>.mp4
```

- 仕様: 1080×1920 / 30fps / H.264 / yuv420p（`src/Root.tsx`, `remotion.config.ts`）
- 拍 → フレーム: `frame = round((beat - 1) * 60 / bpm * fps)`（`src/ProductAd.tsx` の `beatToFrame`）
- ブラウザは HyperFrames が用意した Chrome Headless Shell を再利用します（追加ダウンロード不要）
- 既存の Remotion 作品を HyperFrames に移植したい場合は公式 Skill `/remotion-to-hyperframes` を使います
- Remotion は会社規模によって有料ライセンスが必要です（https://www.remotion.dev/license）
