"use strict";
const fs = require("fs");
const fsp = fs.promises;
const path = require("path");
const crypto = require("crypto");

const EXT = process.argv[2] || path.join(process.env.USERPROFILE, ".cursor", "extensions", "ps2recomp-local.jarvis-cursor-ui-0.5.2");
const WB = process.argv[3] || "C:\\Program Files\\cursor\\resources\\app\\out\\vs\\code\\electron-sandbox\\workbench\\workbench.html";
const MARKER_START = "JARVIS-INJECT-START";
const MARKER_END = "JARVIS-INJECT-END";
const MARKER_HUD_START = "JARVIS-HUD-START";
const MARKER_HUD_END = "JARVIS-HUD-END";
const STYLE_ID = "jarvis-workbench-css";
const BOOT_STAGED = "jarvis-boot-splash.png";
const BOOT_SRC = path.join(EXT, "media", "reference-command-center-2.png");

function uuid() {
  return crypto.randomUUID ? crypto.randomUUID() : crypto.randomBytes(16).toString("hex").replace(/(.{8})(.{4})(.{4})(.{4})(.{12})/, "$1-$2-$3-$4-$5");
}

async function writeAtomic(file, text) {
  const dir = path.dirname(file);
  const tmp = path.join(dir, `.jarvis-tmp-${process.pid}-${Date.now()}`);
  await fsp.writeFile(tmp, text, "utf8");
  await fsp.rename(tmp, file);
}

function stripAll(html) {
  return html
    .replace(/<!--\s*JARVIS-INJECT-START[\s\S]*?<!--\s*JARVIS-INJECT-END\s*-->\s*/g, "")
    .replace(/<!--\s*JARVIS-HUD-START[\s\S]*?<!--\s*JARVIS-HUD-END\s*-->\s*/g, "")
    .replace(/<!--\s*CORTANA-INJECT-START[\s\S]*?<!--\s*CORTANA-INJECT-END\s*-->\s*/g, "")
    .replace(/<style\s+id=["']jarvis-workbench-css["'][\s\S]*?<\/style>\s*/gi, "")
    .replace(/<style\s+id=["']CORTANA-workbench-css["'][\s\S]*?<\/style>\s*/gi, "");
}

async function syncChecksum(appRoot, workbenchPath) {
  const productPath = path.join(appRoot, "product.json");
  if (!fs.existsSync(productPath)) return { ok: false, message: "no product.json" };
  const buf = await fsp.readFile(workbenchPath);
  // VS Code uses md5 base64 of file contents for checksums
  const md5 = crypto.createHash("md5").update(buf).digest("base64");
  let raw = await fsp.readFile(productPath, "utf8");
  const key = "vs/code/electron-sandbox/workbench/workbench.html";
  const re = new RegExp(`("${key.replace(/\//g, "\\/")}"\\s*:\\s*")([^"]*)(")`);
  if (!re.test(raw)) return { ok: false, message: "checksum key missing" };
  raw = raw.replace(re, `$1${md5}$3`);
  await writeAtomic(productPath, raw);
  return { ok: true, md5 };
}

(async () => {
  const report = { ok: false, ext: EXT, wb: WB };
  try {
    if (!fs.existsSync(EXT)) throw new Error("ext missing: " + EXT);
    if (!fs.existsSync(WB)) throw new Error("workbench missing");
    if (!fs.existsSync(BOOT_SRC)) throw new Error("boot png missing: " + BOOT_SRC);

    let html = await fsp.readFile(WB, "utf8");
    // backup pristine-ish (strip first so bak is cleaner? keep current as bak)
    const bak = path.join(path.dirname(WB), `workbench.jarvis.${uuid()}.bak.html`);
    // If current is patched, strip for a usable restore base only if we have previous pristine
    const pristineCandidate = (await fsp.readdir(path.dirname(WB))).find(n => n.startsWith("workbench.jarvis.") && n.endsWith(".bak.html"));
    await fsp.writeFile(bak, html, "utf8");
    report.bak = bak;

    html = stripAll(html);
    if (html.includes(MARKER_START) || html.includes("jarvis-cc-hud")) {
      throw new Error("strip failed — markers remain");
    }

    const bootMs = 1200;
    const cssParts = [];
    for (const rel of ["media/inject/tokens.css", "media/inject/boot.css", "media/inject/hud.css"]) {
      const p = path.join(EXT, rel);
      cssParts.push(`/* === ${rel} === */\n` + (await fsp.readFile(p, "utf8")));
    }
    cssParts.push(`/* === jarvis staged splash binding === */\n:root {\n  --jarvis-boot-splash: url(./${BOOT_STAGED});\n  --jarvis-boot-ms: ${bootMs}ms;\n}`);
    const css = cssParts.join("\n\n");
    if (!css.includes("JARVIS-HEALTH")) throw new Error("CSS missing JARVIS-HEALTH");

    let markup = await fsp.readFile(path.join(EXT, "media", "inject", "hud-markup.html"), "utf8");
    // strip outer wrappers if file is full fragment
    if (!markup.includes("jarvis-cc-hud")) throw new Error("hud markup missing jarvis-cc-hud");

    const id = uuid();
    // product fingerprint
    let version = "unknown", commit = "";
    try {
      const product = JSON.parse(await fsp.readFile(path.join(path.resolve(WB, "..", "..", "..", "..", "..", ".."), "product.json"), "utf8"));
      version = String(product.version || version);
      commit = String(product.commit || "");
    } catch {}

    const styleBlock = [
      `<!-- ${MARKER_START} uuid=${id} cursorVersion=${version} cursorCommit=${commit} -->`,
      `<style id="${STYLE_ID}">`,
      css,
      `</style>`,
      `<!-- ${MARKER_END} -->`,
    ].join("\n");

    const hudBlock = [
      `<!-- ${MARKER_HUD_START} uuid=${id} -->`,
      markup,
      `<!-- ${MARKER_HUD_END} -->`,
    ].join("\n");

    if (!/<\/head>/i.test(html)) throw new Error("no </head>");
    if (!/<\/body>/i.test(html)) throw new Error("no </body>");
    html = html.replace(/<\/head>/i, styleBlock + "\n</head>");
    html = html.replace(/<\/body>/i, hudBlock + "\n</body>");

    // stage splash
    const splashDest = path.join(path.dirname(WB), BOOT_STAGED);
    await fsp.copyFile(BOOT_SRC, splashDest);
    const st = await fsp.stat(splashDest);
    report.splashBytes = st.size;

    await writeAtomic(WB, html);

    const appRoot = path.resolve(WB, "..", "..", "..", "..", "..", "..");
    report.checksum = await syncChecksum(appRoot, WB);

    report.ok = true;
    report.hasHud = html.includes("jarvis-cc-hud");
    report.hasBootGrow = css.includes("jarvis-boot-bar-grow");
    report.wbBytes = Buffer.byteLength(html, "utf8");
    console.log(JSON.stringify(report, null, 2));
  } catch (err) {
    report.error = err && err.message ? err.message : String(err);
    console.log(JSON.stringify(report, null, 2));
    process.exit(1);
  }
})();
