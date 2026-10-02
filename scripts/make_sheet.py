#!/usr/bin/env python3
"""Labelled contact sheet from PNGs (used by storyboard_stills.mjs and review_video.py).

  python3 scripts/make_sheet.py --out sheet.png --cols 4 [--cell 300] [--safe] img1.png::"label 1" img2.png::"label 2"

--safe draws the TikTok UI keep-out zones (planning/shot-plan.json → safe_area) in translucent red.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib_media import ROOT, TEMP, run, tile_sheet  # noqa: E402

DEFAULT_SAFE = {"top": 160, "bottom": 480, "left": 60, "right": 140}


def safe_area() -> dict:
    p = ROOT / "planning/shot-plan.json"
    try:
        return {**DEFAULT_SAFE, **json.loads(p.read_text(encoding="utf-8")).get("safe_area", {})}
    except Exception:
        return DEFAULT_SAFE


def overlay_safe(src: Path, dst: Path) -> Path:
    s = safe_area()
    vf = (f"scale=1080:1920,"
          f"drawbox=x=0:y=0:w=iw:h={s['top']}:color=red@0.28:t=fill,"
          f"drawbox=x=0:y=ih-{s['bottom']}:w=iw:h={s['bottom']}:color=red@0.28:t=fill,"
          f"drawbox=x=0:y={s['top']}:w={s['left']}:h=ih-{s['top']}-{s['bottom']}:color=red@0.28:t=fill,"
          f"drawbox=x=iw-{s['right']}:y={s['top']}:w={s['right']}:h=ih-{s['top']}-{s['bottom']}:color=red@0.28:t=fill")
    run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-vf", vf, "-frames:v", "1", str(dst)], check=False)
    return dst if dst.exists() else src


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--cols", type=int, default=4)
    ap.add_argument("--cell", type=int, default=300)
    ap.add_argument("--safe", action="store_true")
    ap.add_argument("items", nargs="+", help="path::label")
    a = ap.parse_args()
    frames, labels = [], []
    TEMP.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(dir=TEMP, prefix="sheet_"))
    try:
        for i, it in enumerate(a.items):
            path, _, label = it.partition("::")
            p = Path(path)
            if not p.exists():
                print("missing:", p)
                continue
            if a.safe:
                p = overlay_safe(p, tmp / f"{i:03d}.png")
            frames.append(p)
            labels.append(label or p.stem)
        ok = tile_sheet(frames, labels, Path(a.out), cols=a.cols, cell_w=a.cell)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
