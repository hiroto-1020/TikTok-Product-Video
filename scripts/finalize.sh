#!/usr/bin/env bash
# 承認済みの MP4 を納品形式に整えて output/final/final.mp4 に置く。
#   bash scripts/finalize.sh <入力.mp4>            → output/final/final.mp4
#   bash scripts/finalize.sh <入力.mp4> <名前>     → output/final/<名前>.mp4（別名が必要な場合のみ）
#     ・既存の final.mp4 は上書きせず final_<日時>.mp4 に退避
#     ・映像は再エンコードしない（-c:v copy）
#     ・音声があれば TikTok 向けラウドネス（-14 LUFS / ピーク -1.5 dB 以下）に調整して AAC 192k
#     ・moov を先頭へ（faststart）
# output/ は Git 管理外（ローカルのみ）。
set -euo pipefail
cd "$(dirname "$0")/.."
IN="${1:?usage: bash scripts/finalize.sh <input.mp4> [name]}"
NAME="${2:-final}"
OUT="output/final/${NAME%.mp4}.mp4"
mkdir -p output/final
if [ -e "$OUT" ]; then
  BAK="output/final/${NAME%.mp4}_$(date +%Y%m%d_%H%M%S).mp4"
  mv "$OUT" "$BAK"
  echo "既存の $OUT を $BAK に退避しました"
fi
DUR="$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$IN")"
VDUR="$(ffprobe -v error -select_streams v:0 -show_entries stream=duration -of csv=p=0 "$IN")"
[ -n "$VDUR" ] && [ "$VDUR" != "N/A" ] && DUR="$VDUR"
if ffprobe -v error -select_streams a -show_entries stream=index -of csv=p=0 "$IN" | grep -q .; then
  # 統合ラウドネスを測って一定ゲインで -14 LUFS に合わせ、リミッターでピークを -1.5 dBTP 以下に抑える
  I="$(ffmpeg -hide_banner -nostats -i "$IN" -vn -af ebur128=peak=true -f null - 2>&1 | grep -E '^\s+I:' | tail -1 | awk '{print $2}')"
  GAIN="$(python3 -c "print(round(-14 - float('${I:--14}'), 2))")"
  echo "loudness: ${I} LUFS → gain ${GAIN} dB"
  ffmpeg -v error -y -i "$IN" -map 0:v:0 -map 0:a:0 -c:v copy -t "$DUR" \
    -af "volume=${GAIN}dB,alimiter=limit=0.84:attack=2:release=50:level=false,aresample=48000" \
    -c:a aac -b:a 192k -movflags +faststart "$OUT"
else
  ffmpeg -v error -y -i "$IN" -c copy -movflags +faststart "$OUT"
fi
ffprobe -v error -show_entries stream=codec_name,width,height,r_frame_rate -show_entries format=duration -of compact "$OUT"
echo "✓ $OUT"
