"use strict";
const fs = require("fs");
const path = require("path");
const dir =
  "C:/Program Files/cursor/resources/app/out/vs/code/electron-sandbox/workbench";
const files = [
  "workbench.html",
  "cortana-hud-clock.js",
  "cortana-hud-live.js",
  "cortana-hud-wave.js",
  "cortana-hud-voice.js",
  "cortana-hud-wake.js",
  "cortana-hud-interact.js",
];
for (const f of files) {
  const p = path.join(dir, f);
  const ok = fs.existsSync(p);
  const n = ok ? fs.statSync(p).size : 0;
  console.log(f, ok ? "OK" : "MISSING", n);
}
const html = fs.readFileSync(path.join(dir, "workbench.html"), "utf8");
const wake = fs.readFileSync(path.join(dir, "cortana-hud-wake.js"), "utf8");
console.log("hud root", html.includes("cortana-cc-hud"));
console.log("wake script tag", html.includes("cortana-hud-wake.js"));
console.log("SpeechRecognition in wake.js", /SpeechRecognition/.test(wake));
console.log("Hey Cortana in wake.js", /hey\s*cortana/i.test(wake));
console.log("Manhattan", html.includes("Manhattan"));
console.log("badge tasks=3", /data-nav="tasks"[\s\S]*?data-count="3"/.test(html));
console.log("badge conversations=12", /data-nav="conversations"[\s\S]*?data-count="12"/.test(html));
console.log("badge tools=18", /data-nav="tools"[\s\S]*?data-count="18"/.test(html));
console.log(
  "script tags",
  html.match(/cortana-hud-[\w-]+\.js/g) || []
);
const settingsPath = path.join(
  process.env.APPDATA || "",
  "Cursor",
  "User",
  "settings.json"
);
if (fs.existsSync(settingsPath)) {
  const s = fs.readFileSync(settingsPath, "utf8");
  const m = s.match(/"cortana\.injection\.enabled"\s*:\s*(true|false)/);
  console.log("settings injection.enabled", m ? m[1] : "unset");
}
