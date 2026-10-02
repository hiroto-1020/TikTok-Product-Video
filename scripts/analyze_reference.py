#!/usr/bin/env python3
"""STEP 2 helper — measure the reference videos / images so the "visual grammar" can be extracted.

Measures what a machine can measure reliably (cuts, shot lengths, tempo, beat/cut sync, colour,
loudness) and exports frames so Claude can *look* at what a machine can't (typography, text motion,
camera moves, easing, transitions, whitespace).

Usage:
  python3 scripts/analyze_reference.py                 # everything in input/current/reference/
  python3 scripts/analyze_reference.py path/to/a.mp4   # one file
  python3 scripts/analyze_reference.py --threshold 0.3 # force a cut threshold

Outputs → planning/reference-analysis/<name>/
  analysis.json     every number below
  contact_sheet.png one frame per shot (midpoint), labelled with shot no. / start / length
  hook_sheet.png    first 3 seconds at 6 fps (opening grammar: hook, first cut, first text)
  timeline_sheet.png the whole video at 2 fps (rhythm overview)
  shots/NN.png      first | middle | last frame of every shot (camera move / text motion / easing)
and planning/reference-analysis/summary.md (one table for all references)
"""
from __future__ import annotations

import argparse
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib_media import (IMAGE_EXT, ROOT, TEMP, VIDEO_EXT, decode_mono, detect_cuts, estimate_tempo,  # noqa: E402
                       grab_frame, list_files, loudness, onset_envelope, onset_peaks, palette, probe, rel,
                       run, scene_scores, tile_sheet, track_beats, write_json)

REF = ROOT / "input/current/reference"
OUT = ROOT / "planning/reference-analysis"


def hstack3(frames: list[Path], out: Path) -> None:
    ins = []
    for f in frames:
        ins += ["-i", str(f)]
    run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex",
         "[0:v]scale=240:-2,pad=iw+6:ih:0:0:black[a];[1:v]scale=240:-2,pad=iw+6:ih:0:0:black[b];"
         "[2:v]scale=240:-2[c];[a][b][c]hstack=inputs=3", str(out)], check=False)


def analyze_video(path: Path, threshold: float | None) -> dict:
    name = path.stem
    od = OUT / name
    (od / "shots").mkdir(parents=True, exist_ok=True)
    tmp = TEMP / "reference" / name
    tmp.mkdir(parents=True, exist_ok=True)
    info = probe(path)
    dur = info["duration"]
    print(f"▶ {path.name}: {info.get('width')}x{info.get('height')} {info.get('fps')}fps {dur:.2f}s")

    scores = scene_scores(path)
    cuts, used_thr = detect_cuts(scores, dur, threshold)
    bounds = [0.0] + cuts + [dur]
    fps = info.get("fps") or 30
    shots = []
    for i in range(len(bounds) - 1):
        s, e = bounds[i], bounds[i + 1]
        inner = [sc for t, sc in scores if s < t < e]
        motion = round(statistics.mean(inner), 4) if inner else 0.0
        shots.append({"no": i + 1, "start": round(s, 3), "end": round(e, 3), "length": round(e - s, 3),
                      "frames": round((e - s) * fps), "motion_index": motion,
                      "palette": palette(path, (s + e) / 2, k=4)})

    # frames for visual reading
    sheet_frames, sheet_labels = [], []
    for sh in shots:
        n = sh["no"]
        s, e = sh["start"], sh["end"]
        trio = [tmp / f"{n:02d}_a.png", tmp / f"{n:02d}_b.png", tmp / f"{n:02d}_c.png"]
        grab_frame(path, s + min(0.05, (e - s) / 4), trio[0])
        grab_frame(path, (s + e) / 2, trio[1])
        grab_frame(path, max(s, e - 0.08), trio[2])
        hstack3(trio, od / "shots" / f"{n:02d}.png")
        sheet_frames.append(trio[1])
        sheet_labels.append(f"#{n} {s:.2f}s  {sh['length']:.2f}s")
    tile_sheet(sheet_frames, sheet_labels, od / "contact_sheet.png", cols=6)

    hook = []
    t = 0.0
    while t < min(3.0, dur):
        f = tmp / f"hook_{int(t * 100):04d}.png"
        if grab_frame(path, t, f):
            hook.append(f)
        t += 1 / 6
    tile_sheet(hook, [f"{i / 6:.2f}s" for i in range(len(hook))], od / "hook_sheet.png", cols=6, cell_w=200)

    tl = []
    t = 0.0
    while t < dur:
        f = tmp / f"tl_{int(t * 100):05d}.png"
        if grab_frame(path, t, f, width=240):
            tl.append(f)
        t += 0.5
    tile_sheet(tl, [f"{i * 0.5:.1f}s" for i in range(len(tl))], od / "timeline_sheet.png", cols=8, cell_w=160)

    # audio
    audio = {"has_audio": info.get("has_audio", False)}
    if info.get("has_audio"):
        sr = 11025
        samples = decode_mono(path, sr)
        env, efps = onset_envelope(samples, sr)
        bpm, conf = estimate_tempo(env, efps)
        beats = track_beats(env, efps, bpm)
        peaks = onset_peaks(env, efps)
        audio.update({"bpm_estimate": bpm, "bpm_confidence": conf, "beat_times": beats[:200],
                      "accent_times": peaks, **loudness(path)})
        if beats and cuts:
            near = []
            for c in cuts:
                d = min(abs(c - b) for b in beats)
                near.append(d)
            beat_len = 60 / bpm
            audio["cut_to_beat"] = {
                "cuts_within_80ms_of_beat": sum(1 for d in near if d <= 0.08),
                "cuts_total": len(cuts),
                "ratio": round(sum(1 for d in near if d <= 0.08) / len(cuts), 2),
                "median_offset_s": round(statistics.median(near), 3),
                "median_shot_in_beats": round(statistics.median([s["length"] for s in shots]) / beat_len, 2),
            }
        if peaks and cuts:
            audio["cuts_on_accents"] = sum(1 for c in cuts if min(abs(c - p) for p in peaks) <= 0.08)

    lengths = [s["length"] for s in shots]
    result = {
        "file": rel(path),
        "probe": info,
        "cut_threshold": round(used_thr, 3),
        "cuts": cuts,
        "shot_count": len(shots),
        "shot_length": {
            "mean": round(statistics.mean(lengths), 3),
            "median": round(statistics.median(lengths), 3),
            "min": round(min(lengths), 3),
            "max": round(max(lengths), 3),
            "first_cut_at": cuts[0] if cuts else None,
            "cuts_per_10s": round(len(cuts) / dur * 10, 2) if dur else 0,
        },
        "shots": shots,
        "overall_palette": palette(path, dur / 2, k=6),
        "audio": audio,
        "sheets": {
            "contact_sheet": rel(od / "contact_sheet.png"),
            "hook_sheet": rel(od / "hook_sheet.png"),
            "timeline_sheet": rel(od / "timeline_sheet.png"),
            "shot_strips": rel(od / "shots"),
        },
        "to_read_visually": [
            "typography (family feel, weight, size vs frame, stroke/box, position)",
            "text motion (in/out style, per-character or per-line, duration) — compare first|mid|last in shots/",
            "camera work (push-in, pan, handheld, macro, static) — compare first|last frame of each strip",
            "transitions (hard cut / whip / zoom / match cut / flash) — look across contact_sheet boundaries",
            "easing feel (snappy overshoot vs smooth) — hook_sheet spacing between frames",
            "whitespace / layout grid / safe-area use",
        ],
    }
    write_json(od / "analysis.json", result)
    for f in tmp.iterdir():
        f.unlink()
    tmp.rmdir()
    print(f"  shots={len(shots)} median={result['shot_length']['median']}s "
          f"bpm={audio.get('bpm_estimate', '-')} → {rel(od)}")
    return result


def analyze_image(path: Path) -> dict:
    od = OUT / "_images"
    od.mkdir(parents=True, exist_ok=True)
    r = run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of",
             "csv=p=0", str(path)], check=False)
    wh = r.stdout.strip().split(",")
    res = {"file": rel(path), "size": wh[:2] if len(wh) >= 2 else None, "palette": palette(path, None, k=6)}
    print(f"▶ {path.name}: palette {[p['hex'] for p in res['palette']]}")
    return res


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="*")
    ap.add_argument("--threshold", type=float, default=None, help="scene-cut threshold 0..1 (default adaptive)")
    args = ap.parse_args()

    if args.files:
        vids = [Path(f) for f in args.files if Path(f).suffix.lower() in VIDEO_EXT]
        imgs = [Path(f) for f in args.files if Path(f).suffix.lower() in IMAGE_EXT]
    else:
        vids = list_files(REF / "videos", VIDEO_EXT)
        imgs = list_files(REF / "images", IMAGE_EXT)
    if not vids and not imgs:
        print("参考素材がありません: input/current/reference/videos/ か images/ に入れてください。")
        sys.exit(1)

    results = [analyze_video(v, args.threshold) for v in vids]
    images = [analyze_image(i) for i in imgs]
    if images:
        write_json(OUT / "_images" / "analysis.json", images)

    lines = ["# Reference analysis — measured values", "",
             "自動計測の結果です。タイポグラフィ・文字の動き・カメラワーク等は各フォルダの画像を見て判断します。", "",
             "| file | size | fps | dur | shots | median shot | first cut | cuts/10s | BPM (conf) | cuts on beat | LUFS |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in results:
        p, sl, au = r["probe"], r["shot_length"], r["audio"]
        cb = au.get("cut_to_beat", {})
        lines.append(f"| {Path(r['file']).name} | {p.get('width')}x{p.get('height')} | {p.get('fps')} | "
                     f"{p['duration']:.2f}s | {r['shot_count']} | {sl['median']}s | {sl['first_cut_at']} | "
                     f"{sl['cuts_per_10s']} | {au.get('bpm_estimate', '-')} ({au.get('bpm_confidence', '-')}) | "
                     f"{cb.get('cuts_within_80ms_of_beat', '-')}/{cb.get('cuts_total', '-')} | "
                     f"{au.get('integrated_lufs', '-')} |")
    for im in images:
        lines.append(f"\n- image `{Path(im['file']).name}` palette: " + ", ".join(
            f"{c['hex']} ({int(c['share'] * 100)}%)" for c in im["palette"]))
    (OUT / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\n✓ summary → {rel(OUT / 'summary.md')}")


if __name__ == "__main__":
    main()
