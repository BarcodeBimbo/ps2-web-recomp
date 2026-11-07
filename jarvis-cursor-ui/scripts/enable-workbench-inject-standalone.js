"use strict";

/**
 * Standalone mirror of workbenchInject.enable() for Admin/UAC enable outside VS Code.
 * Does NOT depend on the vscode module. Writes Program Files workbench + optional state sidecar.
 *
 * Usage:
 *   node enable-workbench-inject-standalone.js
 *   node enable-workbench-inject-standalone.js --ext "C:\\Users\\...\\jarvis-cursor-ui-0.5.0"
 */

const fs = require("fs");
const fsp = fs.promises;
const path = require("path");
const crypto = require("crypto");

const MARKER_START = "CORTANA-INJECT-START";
const MARKER_END = "CORTANA-INJECT-END";
const STYLE_ID = "CORTANA-workbench-css";
const BOOT_STAGED_NAME = "CORTANA-boot-splash.png";
/** Authoritative boot still: Command Center frame (same as reference-command-center.png). */
const BOOT_SOURCE_REL = path.join("media", "reference-command-center-2.png");
const GLOBAL_BACKUP_NAME = "workbench.CORTANA.pristine.html";

const CSS_REL_PATHS = [
  path.join("media", "inject", "tokens.css"),
  path.join("media", "inject", "boot.css"),
  path.join("media", "inject", "hud.css"),
];

const WORKBENCH_DEFAULT = path.join(
  "C:",
  "Program Files",
  "cursor",
  "resources",
  "app",
  "out",
  "vs",
  "code",
  "electron-sandbox",
  "workbench",
  "workbench.html"
);

function argValue(flag) {
  const i = process.argv.indexOf(flag);
  if (i >= 0 && process.argv[i + 1]) return process.argv[i + 1];
  return null;
}

function newUuid() {
  if (typeof crypto.randomUUID === "function") return crypto.randomUUID();
  const hex = crypto.randomBytes(16).toString("hex");
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
}

async function pathExists(p) {
  try {
    await fsp.access(p, fs.constants.F_OK);
    return true;
  } catch {
    return false;
  }
}

function formatWriteError(err) {
  if (!err) return "Unknown write error";
  const code = err.code || "";
  if (code === "EACCES" || code === "EPERM") {
    return (
      "EACCES: Cannot write Cursor workbench files under Program Files. " +
      "Run this script (or Cursor) as Administrator once to Enable CORTANA injection."
    );
  }
  return err.message || String(err);
}

function inferAppRoot(workbenchPath) {
  return path.resolve(workbenchPath, "..", "..", "..", "..", "..", "..");
}

function backupBesideWorkbench(workbenchPath, uuid) {
  return path.join(path.dirname(workbenchPath), `workbench.CORTANA.${uuid}.bak.html`);
}

function stagedSplashPath(workbenchPath) {
  return path.join(path.dirname(workbenchPath), BOOT_STAGED_NAME);
}

async function safeUnlink(filePath) {
  try {
    await fsp.unlink(filePath);
  } catch (err) {
    if (err && err.code !== "ENOENT") throw err;
  }
}

async function writeTextFile(target, content) {
  const dir = path.dirname(target);
  const tmp = path.join(dir, `.CORTANA-write-${process.pid}-${Date.now()}.tmp`);
  try {
    await fsp.writeFile(tmp, content, "utf8");
    try {
      await fsp.rename(tmp, target);
      return;
    } catch {
      try {
        await safeUnlink(target);
      } catch {
        /* continue */
      }
      try {
        await fsp.rename(tmp, target);
        return;
      } catch {
        /* fall through */
      }
    }
  } catch {
    /* fall through */
  } finally {
    try {
      await safeUnlink(tmp);
    } catch {
      /* ignore */
    }
  }
  await fsp.writeFile(target, content, "utf8");
}

function isAlreadyPatched(html) {
  return (
    html.includes(MARKER_START) ||
    html.includes(`id="${STYLE_ID}"`) ||
    html.includes(`id='${STYLE_ID}'`)
  );
}

function parseMarkers(html) {
  const startRe =
    /<!--\s*CORTANA-INJECT-START\s+uuid=([^\s]+)\s+cursorVersion=([^\s]+)\s+cursorCommit=([^\s>]*)\s*-->/;
  const endRe = /<!--\s*CORTANA-INJECT-END\s*-->/;
  const styleRe = /<style\s+id=["']CORTANA-workbench-css["'][\s\S]*?<\/style>/i;
  const startMatch = html.match(startRe);
  const endMatch = html.match(endRe);
  const styleMatch = html.match(styleRe);
  return {
    hasStart: Boolean(startMatch),
    hasEnd: Boolean(endMatch),
    hasStyle: Boolean(styleMatch),
    uuid: startMatch ? startMatch[1] : null,
    startIndex: startMatch ? startMatch.index : -1,
    endIndex: endMatch ? endMatch.index : -1,
    endLen: endMatch ? endMatch[0].length : 0,
  };
}

function stripPatch(html) {
  const m = parseMarkers(html);
  if (m.hasStart && m.hasEnd && m.startIndex <= m.endIndex) {
    const from = m.startIndex;
    const to = m.endIndex + m.endLen;
    return `${html.slice(0, from)}${html.slice(to)}`.replace(/\n{3,}/g, "\n\n");
  }
  return html
    .replace(/<!--\s*CORTANA-INJECT-START[\s\S]*?-->\s*/g, "")
    .replace(/<style\s+id=["']CORTANA-workbench-css["'][\s\S]*?<\/style>\s*/gi, "")
    .replace(/<!--\s*CORTANA-INJECT-END\s*-->\s*/g, "")
    .replace(/\n{3,}/g, "\n\n");
}

function insertBeforeHeadClose(html, block) {
  const lower = html.toLowerCase();
  const idx = lower.lastIndexOf("</head>");
  if (idx === -1) throw new Error("workbench.html missing </head> — refusing to patch");
  const before = html.slice(0, idx).replace(/\s*$/, "\n");
  const after = html.slice(idx);
  return `${before}${block}\n${after}`;
}

function buildPatchBlock({ uuid, version, commit, css }) {
  return [
    `<!-- ${MARKER_START} uuid=${uuid} cursorVersion=${version} cursorCommit=${commit || ""} -->`,
    `<style id="${STYLE_ID}">`,
    css,
    `</style>`,
    `<!-- ${MARKER_END} -->`,
  ].join("\n");
}

async function readProductFingerprint(appRoot) {
  let version = "";
  let commit = "";
  let vscodeVersion = "";
  const productPath = appRoot ? path.join(appRoot, "product.json") : "";
  if (productPath && (await pathExists(productPath))) {
    try {
      const product = JSON.parse(await fsp.readFile(productPath, "utf8"));
      if (product.version != null) version = String(product.version);
      if (product.commit != null) commit = String(product.commit);
      if (product.vscodeVersion != null) vscodeVersion = String(product.vscodeVersion);
    } catch {
      /* ignore */
    }
  }
  return { version, commit, vscodeVersion, productPath };
}

async function readCssBundle(extRoot, bootMs) {
  const warnings = [];
  const parts = [];
  for (const rel of CSS_REL_PATHS) {
    const full = path.join(extRoot, rel);
    try {
      const text = await fsp.readFile(full, "utf8");
      parts.push(`/* === ${rel.replace(/\\/g, "/")} === */\n${text}`);
    } catch (err) {
      warnings.push(`missing CSS: ${rel.replace(/\\/g, "/")} (${err.code || err.message})`);
    }
  }
  // Vars only — boot.css owns multi-layer PNG + progress + particle stacks.
  parts.push(
    [
      "/* === CORTANA staged splash binding === */",
      `:root {`,
      `  --CORTANA-boot-splash: url(./${BOOT_STAGED_NAME});`,
      `  --CORTANA-boot-ms: ${bootMs}ms;`,
      `}`,
    ].join("\n")
  );
  return { css: parts.join("\n\n"), warnings };
}

function resolveExtRoot() {
  const fromArg = argValue("--ext");
  if (fromArg) return path.resolve(fromArg);
  const installed = path.join(
    process.env.USERPROFILE || "",
    ".cursor",
    "extensions",
    "ps2recomp-local.jarvis-cursor-ui-0.5.0"
  );
  const source = path.join("C:", "PS2Recomp", "jarvis-cursor-ui");
  if (fs.existsSync(path.join(installed, "src", "workbenchInject.js"))) return installed;
  return source;
}

function resolveGlobalStorage(extRoot) {
  const fromArg = argValue("--global-storage");
  if (fromArg) return path.resolve(fromArg);
  const pkg = JSON.parse(fs.readFileSync(path.join(extRoot, "package.json"), "utf8"));
  const id = `${pkg.publisher}.${pkg.name}`;
  return path.join(
    process.env.APPDATA || "",
    "Cursor",
    "User",
    "globalStorage",
    id
  );
}

function resolveBootMs() {
  const fromArg = argValue("--boot-ms");
  if (fromArg != null) {
    const n = Number(fromArg);
    if (Number.isFinite(n) && n >= 0) return Math.min(10000, Math.round(n));
  }
  // Prefer User settings if present
  try {
    const settingsPath = path.join(
      process.env.APPDATA || "",
      "Cursor",
      "User",
      "settings.json"
    );
    if (fs.existsSync(settingsPath)) {
      const raw = fs.readFileSync(settingsPath, "utf8");
      // strip // and /* */ comments loosely for VS Code JSONC
      const stripped = raw
        .replace(/\/\*[\s\S]*?\*\//g, "")
        .replace(/^\s*\/\/.*$/gm, "");
      const j = JSON.parse(stripped);
      const n = Number(j["CORTANA.injection.bootMs"]);
      if (Number.isFinite(n) && n >= 0) return Math.min(10000, Math.round(n));
    }
  } catch {
    /* default */
  }
  return 1200;
}

async function main() {
  const report = {
    ok: false,
    elevationHint: "Run elevated if EACCES",
    written: [],
    failed: [],
    meta: {},
  };

  const extRoot = resolveExtRoot();
  const workbenchPath = argValue("--workbench") || WORKBENCH_DEFAULT;
  const bootMs = resolveBootMs();
  const globalStorage = resolveGlobalStorage(extRoot);
  const appRoot = inferAppRoot(workbenchPath);

  report.meta = {
    extRoot,
    workbenchPath,
    appRoot,
    globalStorage,
    bootMs,
    isAdminProbe: process.env.CORTANA_ENABLE_ELEVATED === "1",
  };

  console.log(JSON.stringify({ phase: "start", ...report.meta }, null, 2));

  if (!(await pathExists(workbenchPath))) {
    report.failed.push({ path: workbenchPath, error: "workbench.html not found" });
    console.log(JSON.stringify(report, null, 2));
    process.exit(2);
  }

  let html = await fsp.readFile(workbenchPath, "utf8");
  const fp = await readProductFingerprint(appRoot);

  if (isAlreadyPatched(html)) {
    html = stripPatch(html);
    if (isAlreadyPatched(html)) {
      report.failed.push({
        path: workbenchPath,
        error: "Refusing to backup an already-patched workbench.html",
      });
      console.log(JSON.stringify(report, null, 2));
      process.exit(3);
    }
  }

  const markerUuid = newUuid();
  const backupUuid = newUuid();
  const backupPath = backupBesideWorkbench(workbenchPath, backupUuid);

  try {
    await writeTextFile(backupPath, html);
    report.written.push({ role: "backup-beside", path: backupPath, bytes: Buffer.byteLength(html, "utf8") });
  } catch (err) {
    report.failed.push({ path: backupPath, error: formatWriteError(err), code: err.code || "" });
    console.log(JSON.stringify(report, null, 2));
    process.exit(4);
  }

  try {
    await fsp.mkdir(globalStorage, { recursive: true });
    const secondary = path.join(globalStorage, GLOBAL_BACKUP_NAME);
    await writeTextFile(secondary, html);
    report.written.push({
      role: "backup-globalStorage",
      path: secondary,
      bytes: Buffer.byteLength(html, "utf8"),
    });
  } catch (err) {
    report.meta.secondaryBackupError = formatWriteError(err);
  }

  const splashSrc = path.join(extRoot, BOOT_SOURCE_REL);
  const splashDest = stagedSplashPath(workbenchPath);
  try {
    if (!(await pathExists(splashSrc))) {
      report.failed.push({ path: splashSrc, error: "boot splash source missing" });
    } else {
      await fsp.copyFile(splashSrc, splashDest);
      const st = await fsp.stat(splashDest);
      report.written.push({ role: "boot-splash", path: splashDest, bytes: st.size });
    }
  } catch (err) {
    report.failed.push({ path: splashDest, error: formatWriteError(err), code: err.code || "" });
  }

  const { css, warnings } = await readCssBundle(extRoot, bootMs);
  report.meta.cssWarnings = warnings;
  report.meta.cssBytes = Buffer.byteLength(css, "utf8");

  if (!css.trim()) {
    report.failed.push({ path: "media/inject/*.css", error: "No CSS available" });
    console.log(JSON.stringify(report, null, 2));
    process.exit(5);
  }

  const block = buildPatchBlock({
    uuid: markerUuid,
    version: fp.version,
    commit: fp.commit,
    css,
  });

  let patched;
  try {
    patched = insertBeforeHeadClose(html, block);
  } catch (err) {
    report.failed.push({ path: workbenchPath, error: err.message || String(err) });
    console.log(JSON.stringify(report, null, 2));
    process.exit(6);
  }

  try {
    await writeTextFile(workbenchPath, patched);
    report.written.push({
      role: "workbench-patched",
      path: workbenchPath,
      bytes: Buffer.byteLength(patched, "utf8"),
      markerUuid,
      backupUuid,
      cursorVersion: fp.version,
      cursorCommit: fp.commit,
    });
  } catch (err) {
    report.failed.push({ path: workbenchPath, error: formatWriteError(err), code: err.code || "" });
    // best-effort cleanup of staged splash if patch failed
    try {
      await safeUnlink(splashDest);
    } catch {
      /* ignore */
    }
    console.log(JSON.stringify(report, null, 2));
    process.exit(7);
  }

  // Sidecar state for extension / ops (vscode globalState still needs Enable in-app to fully mirror)
  const statePath = path.join(globalStorage, "CORTANA-injection-standalone-state.json");
  const state = {
    enabled: true,
    active: true,
    cursorVersion: fp.version,
    cursorCommit: fp.commit,
    backupUuid,
    markerUuid,
    lastError: warnings.length ? warnings.join("; ") : "",
    lastOkFingerprint: `${fp.version || ""}|${fp.commit || ""}|${fp.vscodeVersion || ""}`,
    patchedAt: new Date().toISOString(),
    workbenchPath,
    method: "standalone-enable-script",
    note: "Checksum / corrupt-install warning intentionally NOT fixed.",
  };
  try {
    await fsp.mkdir(globalStorage, { recursive: true });
    await writeTextFile(statePath, JSON.stringify(state, null, 2));
    report.written.push({ role: "state-sidecar", path: statePath });
  } catch (err) {
    report.meta.stateWriteError = formatWriteError(err);
  }

  report.ok = report.failed.length === 0;
  report.message = report.ok
    ? "Injection enabled — reload Cursor. Integrity/corrupt warning is expected and not auto-fixed."
    : "Injection partially applied — see failed[]";
  console.log(JSON.stringify(report, null, 2));
  process.exit(report.ok ? 0 : 8);
}

main().catch((err) => {
  console.error(JSON.stringify({ ok: false, fatal: formatWriteError(err) }, null, 2));
  process.exit(1);
});
