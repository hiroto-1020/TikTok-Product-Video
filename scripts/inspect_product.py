#!/usr/bin/env python3
"""STEP 1 helper — inventory the product material in input/current/product/.

For every image / video / logo: size, aspect, alpha (cut-out ready?), duration, palette, and whether
it is large enough for a 1080x1920 frame. Writes planning/product-assets.json and a labelled
contact sheet planning/product-assets.png so Claude can look at the real product shape before
planning (the product shape must never be altered).

Usage: python3 scripts/inspect_product.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib_media import (IMAGE_EXT, ROOT, TEMP, VIDEO_EXT, grab_frame, list_files, palette, probe, rel, run,  # noqa: E402
                       tile_sheet, write_json)

PROD = ROOT / "input/current/product"
OUT = ROOT / "planning"


def image_info(p: Path) -> dict:
    r = run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height,pix_fmt",
             "-of", "csv=p=0", str(p)], check=False)
    parts = r.stdout.strip().split(",")
    if len(parts) < 3:
        return {"file": rel(p), "error": "読み込めません（HEIC等は JPG/PNG に変換してください）"}
    w, h, pix = int(parts[0]), int(parts[1]), parts[2]
    alpha = any(k in pix for k in ("rgba", "argb", "bgra", "abgr", "ya", "yuva", "pal8"))
    short = min(w, h)
    return {
        "file": rel(p), "width": w, "height": h, "aspect": round(w / h, 3), "has_alpha": alpha,
        "fullscreen_ok": w >= 1080 and h >= 1350,
        "quality_note": "高解像度" if short >= 1080 else ("中解像度（全画面拡大は粗くなる可能性）" if short >= 720
                                                    else "低解像度（小さく配置する）"),
        "palette": palette(p, None, k=5),
    }


def main() -> None:
    groups = {"images": IMAGE_EXT, "videos": VIDEO_EXT, "logo": IMAGE_EXT | {".svg"}}
    data: dict = {}
    frames, labels = [], []
    tmp = TEMP / "product"
    tmp.mkdir(parents=True, exist_ok=True)
    for g, exts in groups.items():
        items = []
        for p in list_files(PROD / g, exts):
            if p.suffix.lower() == ".svg":
                items.append({"file": rel(p), "note": "SVG（ベクター・そのまま使用可）"})
                continue
            if g == "videos":
                info = probe(p)
                info["file"] = rel(p)
                info["palette"] = palette(p, info["duration"] / 2, k=5)
                items.append(info)
                for k, t in enumerate([0.1, info["duration"] / 2, max(0, info["duration"] - 0.2)]):
                    f = tmp / f"{p.stem}_{k}.png"
                    if grab_frame(p, t, f, width=360):
                        frames.append(f)
                        labels.append(f"videos/{p.name} {t:.1f}s")
            else:
                info = image_info(p)
                items.append(info)
                f = tmp / f"{g}_{p.stem}.png"
                if "error" not in info and run(["ffmpeg", "-v", "error", "-y", "-i", str(p), "-vf",
                                                "scale=360:-2", "-frames:v", "1", str(f)], check=False).returncode == 0:
                    frames.append(f)
                    labels.append(f"{g}/{p.name}")
        data[g] = items
        print(f"{g}: {len(items)} file(s)")
        for it in items:
            print("   ", it.get("file"), {k: it.get(k) for k in ("width", "height", "duration", "has_alpha",
                                                                  "quality_note", "error") if k in it})
    brief = ROOT / "input/current/brief.md"
    data["brief_present"] = brief.exists() and brief.stat().st_size > 0
    write_json(OUT / "product-assets.json", data)
    if frames:
        tile_sheet(frames, labels, OUT / "product-assets.png", cols=4, cell_w=300)
        print(f"✓ contact sheet → {rel(OUT / 'product-assets.png')}")
    for f in tmp.iterdir():
        f.unlink()
    tmp.rmdir()
    print(f"✓ inventory → {rel(OUT / 'product-assets.json')}")
    if not any(data[g] for g in groups):
        print("商品素材がありません: input/current/product/images などに入れてください。")
        sys.exit(1)


if __name__ == "__main__":
    main()
