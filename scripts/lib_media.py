"""Shared helpers for the analysis / review scripts (Python stdlib + ffmpeg only)."""
from __future__ import annotations

import array
import json
import math
import os
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMP = ROOT / "temp"  # 一時ファイル置き場（Git 管理外）
VIDEO_EXT = {".mp4", ".mov", ".m4v", ".webm", ".mkv", ".avi"}
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".avif", ".gif", ".bmp", ".tif", ".tiff"}
AUDIO_EXT = {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac"}


def run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, check=check)


def list_files(folder: Path, exts: set[str]) -> list[Path]:
    if not folder.exists():
        return []
    return sorted(p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in exts)


def label_font() -> str | None:
    """A TTF usable by ffmpeg drawtext (Japanese-capable when possible)."""
    for cand in [ROOT / "assets/fonts/NotoSansJP-Variable.ttf"]:
        if cand.exists():
            return str(cand)
    if shutil.which("fc-match"):
        r = run(["fc-match", "-f", "%{file}", "sans:lang=ja"], check=False)
        if r.returncode == 0 and r.stdout and os.path.exists(r.stdout):
            return r.stdout
    for cand in ["/System/Library/Fonts/Hiragino Sans GB.ttc", "/Library/Fonts/Arial Unicode.ttf",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]:
        if os.path.exists(cand):
            return cand
    return None


def esc_drawtext(text: str) -> str:
    return text.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\u2019").replace("%", "\\%")


def probe(path: Path) -> dict:
    r = run(["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)])
    data = json.loads(r.stdout)
    v = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), None)
    a = next((s for s in data.get("streams", []) if s.get("codec_type") == "audio"), None)
    info: dict = {"duration": float(data.get("format", {}).get("duration", 0) or 0)}
    if v:
        num, den = (v.get("avg_frame_rate") or v.get("r_frame_rate") or "0/1").split("/")
        fps = float(num) / float(den) if float(den) else 0.0
        w, h = int(v.get("width", 0)), int(v.get("height", 0))
        rot = 0
        for sd in v.get("side_data_list", []) or []:
            if "rotation" in sd:
                rot = int(sd["rotation"])
        if abs(rot) in (90, 270):
            w, h = h, w
        info.update({"width": w, "height": h, "fps": round(fps, 3), "vcodec": v.get("codec_name"),
                     "pix_fmt": v.get("pix_fmt"), "nb_frames": v.get("nb_frames")})
    if a:
        info.update({"has_audio": True, "acodec": a.get("codec_name"),
                     "sample_rate": int(a.get("sample_rate", 0) or 0), "channels": a.get("channels")})
    else:
        info["has_audio"] = False
    return info


# ---------------------------------------------------------------- video

def scene_scores(path: Path) -> list[tuple[float, float]]:
    """(time, scene-change score 0..1) for every frame, computed on a downscaled copy."""
    r = run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-an", "-vf",
             "scale=160:-2,select='gte(scene,0)',metadata=print:file=-", "-f", "null", "-"], check=False)
    out: list[tuple[float, float]] = []
    t = None
    for line in r.stdout.splitlines():
        m = re.search(r"pts_time:([\d.]+)", line)
        if m:
            t = float(m.group(1))
            continue
        m = re.search(r"lavfi\.scene_score=([\d.]+)", line)
        if m and t is not None:
            out.append((t, float(m.group(1))))
    return out


def detect_cuts(scores: list[tuple[float, float]], duration: float, threshold: float | None,
                min_shot: float = 0.25) -> tuple[list[float], float]:
    """Cut times (seconds). Adaptive threshold unless one is given."""
    vals = [s for _, s in scores]
    if not vals:
        return [], threshold or 0.3
    if threshold is None:
        mean = sum(vals) / len(vals)
        sd = math.sqrt(sum((x - mean) ** 2 for x in vals) / len(vals))
        threshold = min(0.45, max(0.18, mean + 4 * sd))
    cuts: list[float] = []
    for i, (t, s) in enumerate(scores):
        if s < threshold:
            continue
        # local peak only
        prev_s = scores[i - 1][1] if i > 0 else 0
        next_s = scores[i + 1][1] if i + 1 < len(scores) else 0
        if s < prev_s or s < next_s:
            continue
        if t < min_shot or duration - t < min_shot * 0.5:
            continue
        if cuts and t - cuts[-1] < min_shot:
            continue
        cuts.append(round(t, 3))
    return cuts, threshold


def grab_frame(path: Path, t: float, out: Path, width: int = 360) -> bool:
    out.parent.mkdir(parents=True, exist_ok=True)
    r = run(["ffmpeg", "-v", "error", "-y", "-ss", f"{max(t, 0):.3f}", "-i", str(path), "-frames:v", "1",
             "-vf", f"scale={width}:-2", str(out)], check=False)
    return r.returncode == 0 and out.exists()


def tile_sheet(frames: list[Path], labels: list[str], out: Path, cols: int, cell_w: int = 270) -> bool:
    """Contact sheet of equally-sized frames with labels burned in (ffmpeg only)."""
    if not frames:
        return False
    font = label_font()
    inputs: list[str] = []
    filters: list[str] = []
    for i, (f, lab) in enumerate(zip(frames, labels)):
        inputs += ["-i", str(f)]
        chain = f"[{i}:v]scale={cell_w}:-2,pad={cell_w}:ih+44:0:44:color=0x111111"
        if font:
            chain += (f",drawtext=fontfile='{font}':text='{esc_drawtext(lab)}':x=8:y=12:fontsize=20:"
                      f"fontcolor=white")
        filters.append(chain + f",setsar=1[c{i}]")
    n = len(frames)
    rows = math.ceil(n / cols)
    # pad with blank cells so xstack has a full grid
    first_h = None
    r = run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
             "-of", "csv=p=0", str(frames[0])], check=False)
    try:
        w0, h0 = [int(x) for x in r.stdout.strip().split(",")[:2]]
        first_h = int(round(h0 * cell_w / w0 / 2) * 2) + 44
    except Exception:
        first_h = int(cell_w * 16 / 9) + 44
    for j in range(n, rows * cols):
        filters.append(f"color=c=0x111111:s={cell_w}x{first_h}:d=1,setsar=1[c{j}]")
    # make all cells the same height (crop/pad)
    norm = []
    for j in range(rows * cols):
        filters.append(f"[c{j}]scale={cell_w}:{first_h}:force_original_aspect_ratio=decrease,"
                       f"pad={cell_w}:{first_h}:(ow-iw)/2:(oh-ih)/2:color=0x111111[n{j}]")
        norm.append(f"[n{j}]")
    layout = "|".join(f"{(j % cols) * (cell_w + 6)}_{(j // cols) * (first_h + 6)}" for j in range(rows * cols))
    if rows * cols == 1:
        filters.append(f"{norm[0]}copy[out]")
    else:
        filters.append(f"{''.join(norm)}xstack=inputs={rows * cols}:layout={layout}:fill=0x000000[out]")
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(filters), "-map", "[out]",
           "-frames:v", "1", str(out)]
    r = run(cmd, check=False)
    if r.returncode != 0:
        print("  tile_sheet failed:", r.stderr[-400:])
    return r.returncode == 0


def palette(image_or_video: Path, t: float | None = None, k: int = 5) -> list[dict]:
    """Dominant colours via tiny k-means on a 48x48 thumbnail."""
    cmd = ["ffmpeg", "-v", "error"]
    if t is not None:
        cmd += ["-ss", f"{t:.3f}"]
    cmd += ["-i", str(image_or_video), "-frames:v", "1", "-vf", "scale=48:48:flags=area", "-f", "rawvideo",
            "-pix_fmt", "rgb24", "-"]
    r = subprocess.run(cmd, capture_output=True)
    raw = r.stdout
    if len(raw) < 3:
        return []
    px = [(raw[i], raw[i + 1], raw[i + 2]) for i in range(0, len(raw) - 2, 3)]
    step = max(1, len(px) // k)
    cents = [px[i * step] for i in range(k)]
    for _ in range(12):
        groups: list[list[tuple[int, int, int]]] = [[] for _ in cents]
        for p in px:
            j = min(range(len(cents)), key=lambda c: (p[0] - cents[c][0]) ** 2 + (p[1] - cents[c][1]) ** 2
                    + (p[2] - cents[c][2]) ** 2)
            groups[j].append(p)
        cents = [tuple(sum(c[i] for c in g) // len(g) for i in range(3)) if g else cents[n]
                 for n, g in enumerate(groups)]
    total = len(px)
    res = []
    for c, g in sorted(zip(cents, groups), key=lambda x: -len(x[1])):
        if not g:
            continue
        res.append({"hex": "#%02x%02x%02x" % c, "share": round(len(g) / total, 3)})
    return res


# ---------------------------------------------------------------- audio

def decode_mono(path: Path, sr: int = 11025) -> array.array:
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vn", "-ac", "1", "-ar", str(sr), "-f",
                        "s16le", "-"], capture_output=True)
    a = array.array("h")
    a.frombytes(r.stdout[: len(r.stdout) // 2 * 2])
    return a


def onset_envelope(samples: array.array, sr: int = 11025, hop: int = 256) -> tuple[list[float], float]:
    """Log-energy flux onset strength. Returns (envelope, frames-per-second)."""
    n = len(samples) // hop
    energies = []
    for i in range(n):
        seg = samples[i * hop:(i + 1) * hop]
        e = sum(x * x for x in seg) / hop
        energies.append(math.log1p(e))
    env = [0.0] + [max(0.0, energies[i] - energies[i - 1]) for i in range(1, len(energies))]
    # light smoothing
    sm = [(env[max(0, i - 1)] + 2 * env[i] + env[min(len(env) - 1, i + 1)]) / 4 for i in range(len(env))]
    return sm, sr / hop


def estimate_tempo(env: list[float], fps: float, lo: float = 70, hi: float = 180) -> tuple[float, float]:
    """Autocorrelation tempo with a mild prior around 120 BPM. Returns (bpm, confidence 0..1)."""
    if len(env) < fps * 4:
        return 0.0, 0.0
    mean = sum(env) / len(env)
    x = [v - mean for v in env]
    denom = sum(v * v for v in x) or 1.0
    best, best_score, scores = 0.0, -1.0, []
    for bpm10 in range(int(lo * 2), int(hi * 2) + 1):
        bpm = bpm10 / 2
        lag = fps * 60 / bpm
        l0 = int(lag)
        frac = lag - l0
        ac = 0.0
        for i in range(len(x) - l0 - 1):
            ac += x[i] * ((1 - frac) * x[i + l0] + frac * x[i + l0 + 1])
        ac /= denom
        prior = math.exp(-0.5 * (math.log2(bpm / 120) / 0.9) ** 2)
        s = ac * prior
        scores.append(s)
        if s > best_score:
            best, best_score = bpm, s
    srt = sorted(scores, reverse=True)
    conf = 0.0 if srt[0] <= 0 else max(0.0, min(1.0, (srt[0] - (sum(srt[:40]) / 40)) / srt[0] * 3))
    return refine_tempo(env, fps, best), round(conf, 2)


def _comb(env: list[float], fps: float, bpm: float) -> float:
    period = fps * 60 / bpm
    best = 0.0
    for p10 in range(0, int(period * 4)):
        t, s, n = p10 / 4, 0.0, 0
        while t < len(env) - 1:
            i = int(t)
            f = t - i
            s += (1 - f) * env[i] + f * env[i + 1]
            n += 1
            t += period
        if n:
            best = max(best, s / n)
    return best


def refine_tempo(env: list[float], fps: float, bpm: float) -> float:
    """Fine-tune a coarse BPM (±4 BPM, 0.1 steps) by comb-filter alignment with the onset envelope."""
    if bpm <= 0:
        return bpm
    cands = [round(bpm + d / 10, 1) for d in range(-40, 41)]
    return max(cands, key=lambda b: _comb(env, fps, b))


def track_beats(env: list[float], fps: float, bpm: float) -> list[float]:
    """Best phase of a fixed grid. Returns beat times in seconds."""
    if bpm <= 0:
        return []
    period = fps * 60 / bpm
    best_phase, best_sum = 0.0, -1.0
    for p4 in range(max(1, int(period * 4))):
        s, t = 0.0, p4 / 4
        while t < len(env) - 1:
            i = int(t)
            f = t - i
            s += (1 - f) * env[i] + f * env[i + 1]
            t += period
        if s > best_sum:
            best_phase, best_sum = p4 / 4, s
    beats, t = [], best_phase
    while t < len(env):
        beats.append(round(t / fps, 3))
        t += period
    return beats


def onset_peaks(env: list[float], fps: float, top: int = 24) -> list[float]:
    if not env:
        return []
    mean = sum(env) / len(env)
    peaks = []
    w = max(1, int(fps * 0.1))
    for i in range(1, len(env) - 1):
        if env[i] > mean * 2 and env[i] == max(env[max(0, i - w):i + w + 1]):
            peaks.append((env[i], i / fps))
    peaks.sort(reverse=True)
    return sorted(round(t, 3) for _, t in peaks[:top])


def loudness(path: Path) -> dict:
    r = run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-vn", "-af", "ebur128=peak=true", "-f",
             "null", "-"], check=False)
    txt = r.stderr
    res = {}
    m = re.findall(r"I:\s+(-?[\d.]+) LUFS", txt)
    if m:
        res["integrated_lufs"] = float(m[-1])
    m = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", txt)
    if m:
        res["true_peak_dbfs"] = float(m[-1])
    return res


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def rel(p: Path) -> str:
    try:
        return str(p.resolve().relative_to(ROOT))
    except ValueError:
        return str(p)
