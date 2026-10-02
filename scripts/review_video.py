#!/usr/bin/env python3
"""STEP 7 helper — machine checks for a rendered MP4 + the sheets Claude needs for the self-review.

Usage:
  python3 scripts/review_video.py                      # newest MP4 in output/draft/
  python3 scripts/review_video.py output/final/x.mp4

Checks (PASS / WARN / FAIL):
  spec      1080x1920, 30 fps, H.264 + yuv420p, AAC audio, 15–25 s
  black     black frames (blackdetect) — the first frame must not be black (hook)
  freeze    frozen stretches > 1.2 s (freezedetect) — usually a dead scene
  cuts      detected cuts vs the planned scene boundaries of the selected option (beat grid)
  audio     integrated loudness (TikTok ≈ -14 LUFS ±2), true peak ≤ -1 dBTP, planned SFX hits audible
Sheets → output/<draft|final>/review/<name>/
  hook_sheet.png      0.0–3.0 s every 0.25 s (first impression)
  scenes_sheet.png    midpoint of every planned scene
  scenes_safezone.png same, TikTok UI keep-out zones in red (captions / CTA must stay out)
  report.json / report.md
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib_media import (ROOT, TEMP, decode_mono, detect_cuts, grab_frame, loudness, onset_envelope, onset_peaks,  # noqa: E402
                       probe, rel, run, scene_scores, write_json)


def newest_draft() -> Path | None:
    c = sorted((ROOT / "output/draft").glob("*.mp4"), key=lambda p: p.stat().st_mtime)
    return c[-1] if c else None


def sheet(out: Path, items: list[tuple[Path, str]], safe: bool = False, cols: int = 5) -> None:
    args = ["python3", str(ROOT / "scripts/make_sheet.py"), "--out", str(out), "--cols", str(cols), "--cell", "240"]
    if safe:
        args.append("--safe")
    args += [f"{p}::{lab}" for p, lab in items]
    subprocess.run(args, capture_output=True, text=True)


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else newest_draft()
    if not path or not path.exists():
        sys.exit("MP4 が見つかりません（output/draft/ にレンダリングしてください）")
    path = path.resolve()
    od = path.parent / "review" / path.stem
    fr = TEMP / "review" / path.stem
    fr.mkdir(parents=True, exist_ok=True)
    checks: list[dict] = []

    def add(name: str, status: str, detail: str) -> None:
        checks.append({"check": name, "status": status, "detail": detail})

    info = probe(path)
    dur = info["duration"]
    plan = {}
    try:
        plan = json.loads((ROOT / "planning/shot-plan.json").read_text(encoding="utf-8"))
    except Exception:
        pass
    spec = plan.get("spec", {"min_s": 15, "max_s": 25})

    add("解像度", "PASS" if (info.get("width"), info.get("height")) == (1080, 1920) else "FAIL",
        f"{info.get('width')}x{info.get('height')}")
    add("fps", "PASS" if abs((info.get("fps") or 0) - 30) < 0.01 else "FAIL", str(info.get("fps")))
    add("コーデック", "PASS" if info.get("vcodec") == "h264" and info.get("pix_fmt") == "yuv420p" else "WARN",
        f"{info.get('vcodec')} / {info.get('pix_fmt')}")
    add("尺", "PASS" if spec.get("min_s", 15) <= dur <= spec.get("max_s", 25) else "FAIL", f"{dur:.2f}s")
    add("音声トラック", "PASS" if info.get("has_audio") else "WARN",
        f"{info.get('acodec')} {info.get('sample_rate')}Hz" if info.get("has_audio") else "無音（TikTokで後付けする方針ならOK）")

    # black / freeze
    r = run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-vf",
             "blackdetect=d=0.05:pix_th=0.06,freezedetect=n=0.003:d=1.2", "-an", "-f", "null", "-"], check=False)
    blacks = [(float(a), float(b)) for a, b in re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", r.stderr)]
    freezes = re.findall(r"freeze_start: ([\d.]+)[\s\S]*?freeze_duration: ([\d.]+)", r.stderr)
    first_black = any(s <= 0.04 for s, _ in blacks)
    add("冒頭フレーム", "FAIL" if first_black else "PASS", "0秒目が黒" if first_black else "0秒目から映像あり")
    add("黒フレーム", "PASS" if not blacks else "WARN", ", ".join(f"{s:.2f}-{e:.2f}s" for s, e in blacks) or "なし")
    add("静止区間(>1.2s)", "PASS" if not freezes else "WARN",
        ", ".join(f"{float(s):.2f}s〜{float(d):.2f}s間" for s, d in freezes) or "なし")

    # planned scenes
    opt = next((o for o in plan.get("options", []) if o.get("id") == plan.get("selected")), None)
    scenes = (opt or {}).get("scenes", [])
    planned_cuts = [sc["start_s"] for sc in scenes[1:] if "start_s" in sc]
    scores = scene_scores(path)
    cuts, thr = detect_cuts(scores, dur, None, min_shot=0.2)
    if planned_cuts:
        vals = sorted(s for _, s in scores) or [0.0]
        median = vals[len(vals) // 2]

        def changed_at(pc: float) -> bool:
            # a planned boundary counts when the picture visibly changes within ±2 frames
            if any(abs(pc - c) <= 0.07 for c in cuts):
                return True
            win = [s for t, s in scores if abs(t - pc) <= 0.07]
            return bool(win) and max(win) >= max(0.03, 4 * median)

        hit = [pc for pc in planned_cuts if changed_at(pc)]
        add("カット位置 vs Beat Grid", "PASS" if len(hit) >= len(planned_cuts) * 0.8 else "WARN",
            f"計画 {len(planned_cuts)} / 一致 {len(hit)}（±2f）。検出カット: {', '.join(f'{c:.2f}' for c in cuts)}"
            "（トランジションで繋ぐ箇所はカットとして検出されないことがあります）")
    if opt and abs((opt.get("duration_s") or dur) - dur) > 0.1:
        add("尺 vs 計画", "WARN", f"計画 {opt.get('duration_s')}s / 実際 {dur:.2f}s")

    # audio
    audio = {}
    if info.get("has_audio"):
        audio = loudness(path)
        lufs = audio.get("integrated_lufs")
        tp = audio.get("true_peak_dbfs")
        if lufs is not None:
            add("ラウドネス", "PASS" if -16.5 <= lufs <= -11.5 else "WARN", f"{lufs} LUFS（目安 -14 ±2）")
        if tp is not None:
            add("トゥルーピーク", "PASS" if tp <= -1.0 else "WARN", f"{tp} dBTP（-1 以下推奨）")
        env, efps = onset_envelope(decode_mono(path), 11025)
        peaks = onset_peaks(env, efps, top=60)
        sfx = [(sc["id"], fx.get("name"), fx["at_s"]) for sc in scenes for fx in sc.get("sfx", []) or []
               if fx.get("name") and "at_s" in fx]
        if sfx:
            heard = [s for s in sfx if any(abs(s[2] - p) <= 0.06 for p in peaks)]
            add("SFX vs Beat Grid", "PASS" if len(heard) >= len(sfx) * 0.7 else "WARN",
                f"計画 {len(sfx)} / 音の立ち上がりと一致 {len(heard)}（±60ms）")

    # sheets
    hook = []
    t = 0.0
    while t <= min(3.0, dur - 0.01):
        f = fr / f"hook_{int(t * 100):03d}.png"
        if grab_frame(path, t, f, width=540):
            hook.append((f, f"{t:.2f}s"))
        t += 0.25
    sheet(od / "hook_sheet.png", hook, cols=7)
    mids = []
    if scenes and all("start_s" in s for s in scenes):
        for sc in scenes:
            m = (sc["start_s"] + sc["end_s"]) / 2
            f = fr / f"{sc['id']}.png"
            if m < dur and grab_frame(path, m, f, width=1080):
                mids.append((f, f"{sc['id']} {sc.get('role', '')} {m:.2f}s"))
    else:
        n = 8
        for i in range(n):
            m = dur * (i + 0.5) / n
            f = fr / f"mid_{i}.png"
            if grab_frame(path, m, f, width=1080):
                mids.append((f, f"{m:.2f}s"))
    sheet(od / "scenes_sheet.png", mids)
    sheet(od / "scenes_safezone.png", mids, safe=True)
    shutil.rmtree(fr, ignore_errors=True)

    report = {"file": rel(path), "probe": info, "audio": audio, "detected_cuts": cuts, "checks": checks,
              "sheets": {k: rel(od / f"{k}.png") for k in ("hook_sheet", "scenes_sheet", "scenes_safezone")}}
    write_json(od / "report.json", report)
    icon = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌"}
    md = [f"# 機械チェック — {path.name}", "", "| 項目 | 結果 | 詳細 |", "|---|---|---|"]
    md += [f"| {c['check']} | {icon[c['status']]} {c['status']} | {c['detail']} |" for c in checks]
    md += ["", f"- 冒頭3秒: `{rel(od / 'hook_sheet.png')}`", f"- 各シーン: `{rel(od / 'scenes_sheet.png')}`",
           f"- セーフゾーン: `{rel(od / 'scenes_safezone.png')}`", ""]
    (od / "report.md").write_text("\n".join(md), encoding="utf-8")
    for c in checks:
        print(f"{icon[c['status']]} {c['check']}: {c['detail']}")
    print(f"✓ {rel(od / 'report.md')}")


if __name__ == "__main__":
    main()
