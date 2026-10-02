#!/usr/bin/env node
// STEP 4 — representative still for every scene of every storyboard option, rendered by HyperFrames.
//
//   node scripts/storyboard_stills.mjs --init        scaffold preview/storyboard/_src/<A|B|C>/index.html
//                                                    from planning/shot-plan.json (only if missing)
//   node scripts/storyboard_stills.mjs               render stills for every option in _src/
//   node scripts/storyboard_stills.mjs B             render one option
//
// Each option is a tiny HyperFrames project: every scene is a static 1-second clip
// (<section class="clip scene" id="A-01" data-start="0" data-duration="1">) drawn at its key moment
// with the real product images, real fonts and the real on-screen copy. `hyperframes snapshot`
// captures the middle of each clip, so the stills come from the same engine as the final render.
//
// Output:
//   preview/storyboard/<ID>/<scene-id>.png       1080x1920 still per scene
//   preview/storyboard/<ID>_overview.png         labelled sheet per option (what the user looks at)
//   preview/storyboard/_checks/<ID>_safezone.png same sheet with TikTok UI keep-out zones in red
//   preview/storyboard/index.html                gallery of all options with beats / copy / motion notes
import { existsSync, mkdirSync, readdirSync, readFileSync, renameSync, rmSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { spawnSync } from "node:child_process";
import { ROOT, fontFaceBlock, npx, parseClips, readJSON, rel, syncAssets, writeIfMissing } from "./lib_project.mjs";

const SB = join(ROOT, "preview/storyboard");
const SRC = join(SB, "_src");
const TMP = join(ROOT, "temp", "storyboard"); // 一時ファイル（Git 管理外）
const plan = readJSON(join(ROOT, "planning/shot-plan.json"), { options: [] });
const args = process.argv.slice(2);

const esc = (s = "") => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);

function firstProductImage() {
  const dir = join(ROOT, "input/current/product/images");
  if (!existsSync(dir)) return null;
  const f = readdirSync(dir).filter((n) => /\.(png|jpe?g|webp|avif)$/i.test(n)).sort()[0];
  return f ? `assets/product/images/${f}` : null;
}

function skeleton(opt) {
  const img = firstProductImage();
  const scenes = opt.scenes || [];
  const sections = scenes
    .map((sc, i) => {
      const copy = (sc.text || []).map((t) => t.copy).filter(Boolean);
      return `      <!-- ${sc.id} ${sc.role || ""}: ${esc(sc.visual || "")} -->
      <section id="${sc.id}" class="clip scene" data-start="${i}" data-duration="1" data-track-index="0">
        <div class="bg"></div>
        ${img ? `<img class="product" src="${img}" alt="" />` : `<div class="product placeholder">PRODUCT</div>`}
        <div class="copy">${copy.map((c) => `<p class="line">${esc(c)}</p>`).join("")}</div>
        <div class="tag">${esc(sc.role || "")}</div>
      </section>`;
    })
    .join("\n");
  return `<!doctype html>
<html lang="ja" data-resolution="portrait">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <title>Storyboard ${opt.id} — ${esc(opt.title || "")}</title>
    <script src="assets/vendor/gsap.min.js"></script>
    <style>
      ${fontFaceBlock("assets/fonts/").split("\n").join("\n      ")}
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { width: 1080px; height: 1920px; overflow: hidden; background: #111; }
      #root { position: relative; width: 100%; height: 100%; overflow: hidden; font-family: "Noto Sans JP", sans-serif; }
      .scene { position: absolute; inset: 0; overflow: hidden; }
      .scene .bg { position: absolute; inset: 0; background: #f4f1ec; }
      .scene .product { position: absolute; left: 140px; top: 520px; width: 800px; height: 800px; object-fit: contain; }
      .scene .placeholder { display: grid; place-items: center; background: #ddd; color: #888; font-size: 64px; }
      .scene .copy { position: absolute; left: 60px; right: 140px; top: 220px; }
      .scene .line { font-weight: 900; font-size: 88px; line-height: 1.15; color: #111; }
      .scene .tag { position: absolute; left: 60px; bottom: 500px; font-size: 32px; color: #999; }
    </style>
  </head>
  <body>
    <!-- 静止画用スケッチ：各シーン = 1秒の静止クリップ。キーモーメント（完成形のレイアウト）を描く。動きは付けない。 -->
    <div id="root" data-composition-id="main" data-start="0" data-duration="${Math.max(1, scenes.length)}" data-width="1080" data-height="1920">
${sections}
    </div>
    <script>
      const tl = gsap.timeline({ paused: true });
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
`;
}

function init() {
  const opts = plan.options || [];
  if (!opts.length) {
    console.error("planning/shot-plan.json に options がありません");
    process.exit(1);
  }
  for (const opt of opts) {
    const dir = join(SRC, opt.id);
    mkdirSync(dir, { recursive: true });
    syncAssets(dir, { sfx: false });
    writeIfMissing(join(dir, "hyperframes.json"), JSON.stringify({ paths: { assets: "assets" }, media: { autoProxy: true } }, null, 2) + "\n");
    const made = writeIfMissing(join(dir, "index.html"), skeleton(opt));
    console.log(`${made ? "created" : "kept   "} ${rel(join(dir, "index.html"))} (${(opt.scenes || []).length} scenes)`);
  }
}

function sheet(out, items, safe = false) {
  const a = ["scripts/make_sheet.py", "--out", out, "--cols", String(Math.min(items.length, 4)), "--cell", "300"];
  if (safe) a.push("--safe");
  for (const it of items) a.push(`${it.png}::${it.label}`);
  const r = spawnSync("python3", a, { cwd: ROOT, encoding: "utf8" });
  if (r.status !== 0) console.error(r.stdout, r.stderr);
}

function render(ids) {
  const results = {};
  for (const id of ids) {
    const dir = join(SRC, id);
    const html = join(dir, "index.html");
    if (!existsSync(html)) {
      console.error(`skip ${id}: ${rel(html)} がありません（--init で作成）`);
      continue;
    }
    syncAssets(dir, { sfx: false });
    const clips = parseClips(readFileSync(html, "utf8"));
    if (!clips.length) {
      console.error(`skip ${id}: id="${id}-01" 形式の <section> が見つかりません`);
      continue;
    }
    const tmp = join(TMP, id);
    rmSync(tmp, { recursive: true, force: true });
    const at = clips.map((c) => (c.start + c.duration / 2).toFixed(3)).join(",");
    console.log(`▶ ${id}: ${clips.length} scenes → hyperframes snapshot`);
    const r = npx(["snapshot", rel(dir), "--at", at, "--no-end", "-o", rel(tmp), "--describe", "false"]);
    if (r.status !== 0) {
      console.error(r.stdout?.slice(-2000), r.stderr?.slice(-2000));
      process.exitCode = 1;
      continue;
    }
    const shots = readdirSync(tmp).filter((n) => /^frame-\d+-at-.*\.png$/.test(n)).sort();
    const outDir = join(SB, id);
    rmSync(outDir, { recursive: true, force: true });
    mkdirSync(outDir, { recursive: true });
    const opt = (plan.options || []).find((o) => o.id === id) || { scenes: [] };
    const items = [];
    clips.forEach((c, i) => {
      if (!shots[i]) return;
      const png = join(outDir, `${c.id}.png`);
      renameSync(join(tmp, shots[i]), png);
      const sc = (opt.scenes || []).find((s) => s.id === c.id) || {};
      const t = sc.start_s !== undefined ? `${sc.start_s.toFixed(2)}-${sc.end_s.toFixed(2)}s` : "";
      items.push({ png: rel(png), label: `${c.id} ${sc.role || ""} b${sc.beat ?? "?"} ${t}`.trim() });
    });
    sheet(rel(join(SB, `${id}_overview.png`)), items);
    mkdirSync(join(SB, "_checks"), { recursive: true });
    sheet(rel(join(SB, "_checks", `${id}_safezone.png`)), items, true);
    results[id] = items;
    console.log(`  ✓ ${items.length} stills → ${rel(outDir)}/, ${rel(join(SB, `${id}_overview.png`))}`);
  }
  rmSync(TMP, { recursive: true, force: true });
  gallery();
  return results;
}

function gallery() {
  const opts = (plan.options || []).filter((o) => existsSync(join(SB, o.id)));
  const card = (o, sc) => {
    const png = `${o.id}/${sc.id}.png`;
    const texts = (sc.text || []).filter((t) => t.copy).map((t) => `<li>「${esc(t.copy)}」<small>b${t.beat ?? sc.beat}</small></li>`).join("");
    const sfx = (sc.sfx || []).filter((x) => x.name).map((x) => `${esc(x.name)}@b${x.beat}`).join(", ");
    const time = sc.start_s !== undefined ? `${sc.start_s.toFixed(2)}–${sc.end_s.toFixed(2)}s` : "";
    return `<figure>
        ${existsSync(join(SB, png)) ? `<img src="${png}" alt="${esc(sc.id)}" loading="lazy" />` : `<div class="missing">no still</div>`}
        <figcaption>
          <div class="row"><b>${esc(sc.id)} · ${esc(sc.role || "")}</b><span>Beat ${sc.beat ?? "?"}–${(sc.beat ?? 0) + (sc.beats ?? 0) - 1} · ${time}</span></div>
          <p>${esc(sc.visual || "")}</p>
          ${texts ? `<ul>${texts}</ul>` : ""}
          <p class="meta">${sc.camera ? `カメラ: ${esc(sc.camera)}<br />` : ""}${sc.motion ? `動き: ${esc(sc.motion)}<br />` : ""}${sc.transition_out ? `遷移: ${esc(sc.transition_out)}<br />` : ""}${sfx ? `SFX: ${sfx}` : ""}</p>
        </figcaption>
      </figure>`;
  };
  const sections = opts
    .map(
      (o) => `<section id="option-${o.id}">
      <header><h2>案 ${o.id}　${esc(o.title || "")}</h2><p>${esc(o.concept || "")}</p>
      <p class="meta">${o.duration_s ? `${o.duration_s}s · ` : ""}${o.bpm ? `${o.bpm} BPM · ` : ""}${(o.scenes || []).length} scenes${o.music?.source ? ` · 音楽: ${esc(o.music.source)}` : ""}</p></header>
      <div class="grid">${(o.scenes || []).map((sc) => card(o, sc)).join("\n")}</div>
    </section>`,
    )
    .join("\n");
  const html = `<!doctype html>
<html lang="ja"><head><meta charset="utf-8" /><meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Storyboard — ${esc(plan.product || "")}</title>
<style>
  :root { --bg: #f6f5f2; --fg: #161616; --mute: #6b6b6b; --card: #fff; --line: #e4e1db; }
  @media (prefers-color-scheme: dark) { :root { --bg: #131313; --fg: #f1f1f1; --mute: #9a9a9a; --card: #1d1d1d; --line: #2c2c2c; } }
  body { margin: 0; padding: 24px 16px 64px; background: var(--bg); color: var(--fg); font: 14px/1.6 "Hiragino Sans", "Noto Sans JP", system-ui, sans-serif; }
  h1 { font-size: 22px; margin: 0 0 4px; } h2 { font-size: 18px; margin: 0; }
  section { margin: 32px 0; } header p { margin: 4px 0; color: var(--mute); }
  .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(190px, 1fr)); gap: 14px; margin-top: 12px; }
  figure { margin: 0; background: var(--card); border: 1px solid var(--line); border-radius: 10px; overflow: hidden; }
  figure img, .missing { display: block; width: 100%; aspect-ratio: 9 / 16; object-fit: cover; background: #000; }
  figcaption { padding: 8px 10px 10px; } .row { display: flex; justify-content: space-between; gap: 6px; font-size: 12px; }
  .row span, .meta { color: var(--mute); font-size: 12px; } ul { margin: 6px 0; padding-left: 0; list-style: none; } small { color: var(--mute); margin-left: 4px; }
</style></head>
<body>
  <h1>Storyboard — ${esc(plan.product || "")}</h1>
  <p class="meta">各シーンの代表静止画（HyperFrames snapshot・1080×1920）。Beat は planning/beat-grid.md と共通。</p>
  ${sections}
</body></html>
`;
  writeFileSync(join(SB, "index.html"), html);
  console.log(`✓ gallery → ${rel(join(SB, "index.html"))}`);
}

if (args.includes("--init")) {
  init();
} else {
  const ids = args.filter((a) => !a.startsWith("-"));
  const all = existsSync(SRC) ? readdirSync(SRC).filter((n) => existsSync(join(SRC, n, "index.html"))).sort() : [];
  render(ids.length ? ids : all);
}
