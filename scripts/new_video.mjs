#!/usr/bin/env node
// STEP 5 — scaffold the HyperFrames project for the chosen storyboard option.
//
//   node scripts/new_video.mjs --option B      create video/ (HyperFrames, 1080x1920) for option B
//   node scripts/new_video.mjs --sync          re-copy product / audio / fonts / GSAP / SFX into video/assets
//                                              (run this at the start of a new session before preview/render)
//
// The project is created with the official CLI (`hyperframes init --resolution portrait`) and then
// made offline-safe: GSAP is loaded from assets/vendor (CDNs can be blocked) and the Japanese fonts
// are declared with in-file @font-face rules pointing at assets/fonts.
import { existsSync, readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { join } from "node:path";
import { ROOT, fontFaceBlock, npx, readJSON, rel, syncAssets } from "./lib_project.mjs";

const VIDEO = join(ROOT, "video");
const args = process.argv.slice(2);
const opt = (k) => {
  const i = args.indexOf(k);
  return i >= 0 ? args[i + 1] : undefined;
};

function localizeGsap(file) {
  if (!existsSync(file)) return;
  const html = readFileSync(file, "utf8");
  const next = html.replace(/https:\/\/cdn\.jsdelivr\.net\/npm\/gsap@[^"']+\/dist\/gsap\.min\.js/g, "assets/vendor/gsap.min.js");
  if (next !== html) writeFileSync(file, next);
}

function sync() {
  if (!existsSync(join(VIDEO, "hyperframes.json"))) {
    console.error("video/ がありません（先に --option で作成）");
    process.exit(1);
  }
  const c = syncAssets(VIDEO);
  localizeGsap(join(VIDEO, "index.html"));
  console.log(`✓ synced assets into ${rel(VIDEO)}/assets`, c);
}

function create(id) {
  const plan = readJSON(join(ROOT, "planning/shot-plan.json"), {});
  const option = (plan.options || []).find((o) => o.id === id);
  if (!option) {
    console.error(`planning/shot-plan.json に案 ${id} がありません`);
    process.exit(1);
  }
  if (existsSync(VIDEO)) {
    console.error("video/ が既にあります。前の制作は `bash scripts/archive.sh <名前>` で保管してから実行してください。");
    process.exit(1);
  }
  const r = npx(["init", "video", "--resolution", "portrait", "--non-interactive", "--example", "blank", "--skill", "general-video"]);
  if (r.status !== 0) {
    console.error(r.stdout?.slice(-2000), r.stderr?.slice(-2000));
    process.exit(1);
  }
  const counts = syncAssets(VIDEO);
  const index = join(VIDEO, "index.html");
  localizeGsap(index);
  let html = readFileSync(index, "utf8");
  const dur = option.duration_s || 20;
  html = html.replace(/(<div\s+id="root"[\s\S]*?data-duration=")[\d.]+"/, `$1${dur}"`);
  html = html.replace(/(<h1 id="title"[^>]*data-duration=")[\d.]+"/, `$1${dur}"`);
  html = html.replace("<style>", `<style>\n      ${fontFaceBlock("assets/fonts/").split("\n").join("\n      ")}`);
  html = html.replace('<html lang="en"', '<html lang="ja"');
  writeFileSync(index, html);
  mkdirSync(join(VIDEO, "compositions", "frames"), { recursive: true });
  plan.selected = id;
  plan.status = "selected";
  writeFileSync(join(ROOT, "planning/shot-plan.json"), JSON.stringify(plan, null, 2) + "\n");
  console.log(`✓ ${rel(VIDEO)}/ created for option ${id} (${dur}s, 1080x1920, 30fps)`);
  console.log("  assets:", counts);
  console.log("  next: write video/BRIEF.md + video/STORYBOARD.md, then build scenes in video/compositions/frames/");
}

if (args.includes("--sync")) sync();
else if (opt("--option")) create(opt("--option"));
else {
  console.log("usage: node scripts/new_video.mjs --option <A|B|C>  |  --sync");
  process.exit(1);
}
