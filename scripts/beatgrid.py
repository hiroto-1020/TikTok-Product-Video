#!/usr/bin/env python3
"""STEP 6 helper — the shared Beat Grid.

Reads planning/shot-plan.json, converts every scene / text / SFX "beat" into seconds and frame
numbers, validates the plan, writes the computed times back into the JSON and renders
planning/beat-grid.md (the human-readable grid: "Beat 1 HOOK / Beat 9 商品登場 / …").

Usage:
  python3 scripts/beatgrid.py                     # all options
  python3 scripts/beatgrid.py --option B          # one option
  python3 scripts/beatgrid.py --music input/current/audio/bgm.mp3 --option B
        → measure the track's BPM + first downbeat and write them into option B before computing
  python3 scripts/beatgrid.py --suggest 20        # frame-exact BPM choices for a 20 s cut

Beat n starts at  offset_s + (n-1) * 60 / bpm.  At 30 fps, BPM 90/100/120/150 put every beat on an
exact frame (20/18/15/12 frames per beat); other tempos are rounded to the nearest frame.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib_media import ROOT, decode_mono, estimate_tempo, onset_envelope, track_beats  # noqa: E402

PLAN = ROOT / "planning/shot-plan.json"
FACTS = ROOT / "planning/facts.md"
OUT_MD = ROOT / "planning/beat-grid.md"


def t_of(beat: float, bpm: float, offset: float) -> float:
    return offset + (beat - 1) * 60.0 / bpm


def frame_of(t: float, fps: int) -> int:
    return int(round(t * fps))


def known_facts() -> set[str]:
    if not FACTS.exists():
        return set()
    return set(re.findall(r"\b(F\d+)\b", FACTS.read_text(encoding="utf-8")))


def measure_music(path: Path) -> tuple[float, float, float]:
    sr = 11025
    env, efps = onset_envelope(decode_mono(path, sr), sr)
    bpm, conf = estimate_tempo(env, efps)
    beats = track_beats(env, efps, bpm)
    return bpm, (beats[0] if beats else 0.0), conf


def process(opt: dict, spec: dict, facts: set[str]) -> tuple[list[str], list[str]]:
    fps = int(spec.get("fps", 30))
    bpm = float(opt.get("bpm") or 0)
    off = float(opt.get("offset_s") or 0)
    warns: list[str] = []
    md: list[str] = []
    if bpm <= 0:
        return [f"{opt.get('id')}: bpm が未設定"], md
    fpb = fps * 60 / bpm
    if abs(fpb - round(fpb)) > 1e-6:
        warns.append(f"{opt['id']}: {bpm} BPM は 1拍={fpb:.2f}フレーム（端数は最も近いフレームに丸めます）")
    scenes = opt.get("scenes", [])
    expected = 1
    for sc in scenes:
        b, n = float(sc.get("beat", 0)), float(sc.get("beats", 0))
        if b != expected:
            warns.append(f"{sc.get('id')}: beat {b:g} から開始（前シーンの終わりは beat {expected:g}）→ 隙間/重なり")
        if n <= 0:
            warns.append(f"{sc.get('id')}: beats が 0")
        s, e = t_of(b, bpm, off), t_of(b + n, bpm, off)
        sc["start_s"], sc["end_s"], sc["length_s"] = round(s, 3), round(e, 3), round(e - s, 3)
        sc["start_frame"], sc["end_frame"] = frame_of(s, fps), frame_of(e, fps)
        if e - s < 0.5:
            warns.append(f"{sc['id']}: {e - s:.2f}s は短すぎる可能性（文字が読めない）")
        if e - s > 4.0:
            warns.append(f"{sc['id']}: {e - s:.2f}s は長め（TikTokでは間延びしやすい）")
        for tx in sc.get("text", []) or []:
            tb = float(tx.get("beat", b))
            if not (b <= tb < b + n):
                warns.append(f"{sc['id']}: テキスト「{tx.get('copy', '')}」の beat {tb:g} がシーン外")
            tx["at_s"] = round(t_of(tb, bpm, off), 3)
            tx["at_frame"] = frame_of(tx["at_s"], fps)
            chars = len(re.sub(r"\s", "", tx.get("copy", "")))
            if chars > 0:
                readable = 0.25 + chars * 0.12  # ~8 文字/秒 + 反応時間
                if e - tx["at_s"] < readable:
                    warns.append(f"{sc['id']}: 「{tx.get('copy')}」{chars}文字に対し表示 {e - tx['at_s']:.2f}s"
                                 f"（目安 {readable:.1f}s 以上）")
        for fx in sc.get("sfx", []) or []:
            if fx.get("name"):
                fx["at_s"] = round(t_of(float(fx.get("beat", b)), bpm, off), 3)
                fx["at_frame"] = frame_of(fx["at_s"], fps)
        for f in sc.get("facts", []) or []:
            if facts and f not in facts:
                warns.append(f"{sc['id']}: 事実ID {f} が planning/facts.md にありません")
        expected = b + n
    total_beats = expected - 1
    total = t_of(expected, bpm, off)
    opt["total_beats"] = total_beats
    opt["duration_s"] = round(total, 3)
    opt["duration_frames"] = frame_of(total, fps)
    lo, hi = spec.get("min_s", 15), spec.get("max_s", 25)
    if not (lo <= total <= hi):
        warns.append(f"{opt['id']}: 合計 {total:.2f}s が {lo}〜{hi}s の範囲外")

    md.append(f"## 案{opt['id']} — {opt.get('title', '')}")
    md.append("")
    md.append(f"- BPM {bpm:g} / 1拍 {60 / bpm:.3f}s = {fpb:.2f}f / 1小節(4拍) {240 / bpm:.2f}s / "
              f"オフセット {off:.3f}s")
    md.append(f"- 合計 {total_beats:g} 拍 = **{total:.2f}s ({frame_of(total, fps)}f)**")
    md.append(f"- 音楽: {opt.get('music', {}).get('source') or '未定'}")
    md.append("")
    md.append("| Beat | 時刻 | frame | シーン | 役割 | 長さ | 画面 | テキスト | SFX | 遷移 |")
    md.append("|---|---|---|---|---|---|---|---|---|---|")
    for sc in scenes:
        texts = " / ".join(f"「{t.get('copy')}」@b{t.get('beat', sc.get('beat'))}" for t in sc.get("text", []) or []
                           if t.get("copy"))
        sfx = ", ".join(f"{x.get('name')}@b{x.get('beat')}" for x in sc.get("sfx", []) or [] if x.get("name"))
        md.append(f"| {sc.get('beat'):g} | {sc['start_s']:.2f}s | {sc['start_frame']} | {sc.get('id')} | "
                  f"{sc.get('role', '')} | {sc['length_s']:.2f}s ({sc.get('beats'):g}拍) | "
                  f"{(sc.get('visual') or '')[:40]} | {texts} | {sfx} | {sc.get('transition_out', '')} |")
    md.append("")
    return warns, md


def suggest(seconds: float, fps: int = 30) -> None:
    print(f"{seconds:g}s 付近で拍がフレームぴったりになる BPM:")
    for bpm in (90, 100, 112.5, 120, 128.57, 150):
        fpb = fps * 60 / bpm
        beats = round(seconds * bpm / 60)
        print(f"  {bpm:>7g} BPM  1拍={fpb:.2f}f  {beats}拍 → {beats * 60 / bpm:.2f}s  ({beats / 4:g}小節)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--option")
    ap.add_argument("--music", help="measure BPM/offset from this track and store it in --option")
    ap.add_argument("--suggest", type=float)
    args = ap.parse_args()
    if args.suggest:
        suggest(args.suggest)
        return
    if not PLAN.exists():
        sys.exit("planning/shot-plan.json がありません")
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    opts = plan.get("options", [])
    if args.option:
        opts = [o for o in opts if o.get("id") == args.option]
        if not opts:
            sys.exit(f"案 {args.option} がありません")
    if args.music:
        if len(opts) != 1:
            sys.exit("--music は --option と一緒に指定してください")
        bpm, first, conf = measure_music(Path(args.music))
        opts[0]["bpm"] = bpm
        opts[0]["offset_s"] = 0.0
        opts[0].setdefault("music", {})
        opts[0]["music"].update({"source": args.music, "measured_bpm": bpm, "first_beat_s": first,
                                 "confidence": conf,
                                 "note": f"曲の最初の拍 {first:.3f}s を動画の Beat 1 に合わせるには曲を {first:.3f}s トリム"})
        print(f"♪ {args.music}: {bpm} BPM (conf {conf}), first beat {first:.3f}s")
    facts = known_facts()
    all_warn, md = [], ["# Beat Grid", "",
                        "音楽・効果音・映像（カット/文字/動き）を同じ拍番号で管理します。"
                        "`python3 scripts/beatgrid.py` が自動生成（手で編集しない）。", ""]
    for o in opts:
        w, m = process(o, plan.get("spec", {}), facts)
        all_warn += w
        md += m
    PLAN.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if all_warn:
        md += ["## 要確認", ""] + [f"- {w}" for w in all_warn] + [""]
    OUT_MD.write_text("\n".join(md), encoding="utf-8")
    for o in opts:
        print(f"案{o.get('id')}: {o.get('duration_s')}s / {o.get('total_beats')}拍 @ {o.get('bpm')}BPM")
    for w in all_warn:
        print("  ! " + w)
    print("✓ planning/beat-grid.md")


if __name__ == "__main__":
    main()
