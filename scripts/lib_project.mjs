// Shared helpers for HyperFrames projects inside this studio (storyboard sketches + the video build).
import { cpSync, existsSync, mkdirSync, readdirSync, readFileSync, statSync, writeFileSync } from "node:fs";
import { dirname, join, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";

export const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
export const SFX_DIR = join(ROOT, ".claude/skills/media-use/audio/assets/sfx");

export function readJSON(path, fallback = null) {
  try {
    return JSON.parse(readFileSync(path, "utf8"));
  } catch {
    return fallback;
  }
}

export function rel(p) {
  return relative(ROOT, p) || ".";
}

function copyDirFiles(src, dst, filter = () => true) {
  if (!existsSync(src)) return 0;
  mkdirSync(dst, { recursive: true });
  let n = 0;
  for (const name of readdirSync(src)) {
    if (name.startsWith(".")) continue;
    const s = join(src, name);
    const d = join(dst, name);
    if (statSync(s).isDirectory()) {
      n += copyDirFiles(s, d, filter);
    } else if (filter(name)) {
      if (!existsSync(d) || statSync(d).size !== statSync(s).size) {
        cpSync(s, d);
        n++;
      }
    }
  }
  return n;
}

/**
 * Copy everything a composition may reference into <project>/assets so it is self-contained:
 *   assets/product/{images,videos,logo}  ← input/current/product
 *   assets/audio                         ← input/current/audio
 *   assets/fonts                         ← assets/fonts (setup.sh downloads them)
 *   assets/vendor                        ← assets/vendor (local GSAP — CDNs may be blocked)
 *   assets/sfx                           ← HyperFrames media-use SFX library (Pixabay licence, commercial OK)
 */
export function syncAssets(projectDir, { sfx = true } = {}) {
  const a = join(projectDir, "assets");
  const counts = {
    product: copyDirFiles(join(ROOT, "input/current/product"), join(a, "product")),
    audio: copyDirFiles(join(ROOT, "input/current/audio"), join(a, "audio")),
    fonts: copyDirFiles(join(ROOT, "assets/fonts"), join(a, "fonts")),
    vendor: copyDirFiles(join(ROOT, "assets/vendor"), join(a, "vendor")),
    sfx: sfx ? copyDirFiles(SFX_DIR, join(a, "sfx"), (n) => n.endsWith(".mp3") || n.endsWith(".json") || n.endsWith(".md")) : 0,
  };
  return counts;
}

/** The @font-face block, with URLs relative to the composition file. */
export function fontFaceBlock(prefix = "assets/fonts/") {
  const css = readFileSync(join(ROOT, "assets/fonts/fonts.css"), "utf8");
  return css
    .replace(/\/\*[\s\S]*?\*\//g, "")
    .replace(/url\("([^"]+)"\)/g, (_, f) => `url("${prefix}${f}")`)
    .trim();
}

export function npx(args, opts = {}) {
  return spawnSync("npx", ["--no-install", "hyperframes", ...args], {
    cwd: ROOT,
    encoding: "utf8",
    env: { ...process.env, HYPERFRAMES_SKIP_SKILLS: "1" },
    ...opts,
  });
}

/** Clips with an id + data-start + data-duration (any attribute order). */
export function parseClips(html, idPattern = /^[A-Z]-\d+/) {
  const out = [];
  const tagRe = /<(section|div)\b([^>]*)>/g;
  let m;
  while ((m = tagRe.exec(html))) {
    const attrs = m[2];
    const get = (k) => (attrs.match(new RegExp(`\\b${k}="([^"]*)"`)) || [])[1];
    const id = get("id");
    const start = get("data-start");
    const dur = get("data-duration");
    if (id && idPattern.test(id) && start !== undefined && dur !== undefined) {
      out.push({ id, start: Number(start), duration: Number(dur) });
    }
  }
  return out.sort((x, y) => x.start - y.start);
}

export function writeIfMissing(path, content) {
  if (!existsSync(path)) {
    mkdirSync(dirname(path), { recursive: true });
    writeFileSync(path, content);
    return true;
  }
  return false;
}
