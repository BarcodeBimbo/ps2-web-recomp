"use strict";

/**
 * CORTANA workbench injection engine (phase 6).
 *
 * First-party Custom CSS Loader / CSS Injector pattern (Rank 1):
 * locate Cursor workbench.html → backup pristine → insert marked inline <style>
 * before </head>. Disable restores backup (or strips markers).
 *
 * God-as-builder / local-owner rebuild: no third-party loader dependency.
 * CSP: CSS-first only; never strip Cursor Content-Security-Policy.
 *
 * Integrity / "corrupt installation" toast: suppressed by syncing
 * product.json checksums[workbench.html] to SHA-256 (base64, no padding) of the
 * on-disk workbench after Enable/Disable/restore. Inject behavior unchanged.
 */

const fs = require("fs");
const fsp = fs.promises;
const path = require("path");
const crypto = require("crypto");
const os = require("os");
const { spawnSync } = require("child_process");
const vscode = require("vscode");

const MARKER_START = "CORTANA-INJECT-START";
const MARKER_END = "CORTANA-INJECT-END";
const MARKER_HUD_START = "CORTANA-HUD-START";
const MARKER_HUD_END = "CORTANA-HUD-END";
const STYLE_ID = "cortana-workbench-css";
const BOOT_STAGED_NAME = "cortana-boot-splash.png";
/** Authoritative boot still: calibrating splash (CSS-drawn cover; PNG staged for binding). */
const BOOT_SOURCE_REL = path.join("media", "reference-calibrating-splash.png");
/** Hero globe cutout (CC-2) — NOT boot splash. Staged beside workbench for HUD CSS. */
const HERO_GLOBE_STAGED_NAME = "jcc-hero-globe.png";
const HERO_GLOBE_SOURCE_REL = path.join("media", "inject", "jcc-hero-globe.png");
const HUD_MARKUP_REL = path.join("media", "inject", "hud-markup.html");
const CURSOR_MODELS_REL = path.join("media", "inject", "cursor-models.json");
/** Cursor reactive storage key → availableDefaultModels2 (real picker catalog). */
const CURSOR_APPUSER_DB_KEY =
  "src.vs.platform.reactivestorage.browser.reactiveStorageServiceImpl.persistentStorage.applicationUser";
const GLOBAL_BACKUP_NAME = "workbench.cortana.pristine.html";
/** Cursor product.json checksums key for the patched workbench HTML. */
const WORKBENCH_CHECKSUM_KEY = "vs/code/electron-sandbox/workbench/workbench.html";

/** CSS inlined in this order (Worker A owns boot.css; Worker B owns hud.css). */
const CSS_REL_PATHS = [
  path.join("media", "inject", "tokens.css"),
  path.join("media", "inject", "boot.css"),
  path.join("media", "inject", "hud-photo-assets.css"),
  path.join("media", "inject", "hud.css"),
];

const GS = {
  enabled: "cortana.injection.enabled",
  active: "cortana.injection.active",
  cursorVersion: "cortana.injection.cursorVersion",
  cursorCommit: "cortana.injection.cursorCommit",
  backupUuid: "cortana.injection.backupUuid",
  markerUuid: "cortana.injection.markerUuid",
  lastError: "cortana.injection.lastError",
  lastOkFingerprint: "cortana.injection.lastOkFingerprint",
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function newUuid() {
  if (typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
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
  if (!err) {
    return "Unknown write error";
  }
  const code = err.code || "";
  if (code === "EACCES" || code === "EPERM") {
    return (
      "EACCES: Cannot write Cursor workbench files under Program Files. " +
      "Run Cursor as Administrator once to Enable/Disable CORTANA injection."
    );
  }
  return err.message || String(err);
}

function fingerprintString(version, commit, vscodeVersion) {
  return `${version || ""}|${commit || ""}|${vscodeVersion || ""}`;
}

/** Cursor/VS Code integrity digest: SHA-256 → base64, strip trailing '='. */
function computeWorkbenchChecksum(buf) {
  return crypto.createHash("sha256").update(buf).digest("base64").replace(/=+$/, "");
}

function productJsonPath(appRoot) {
  return path.join(appRoot, "product.json");
}

/**
 * Quiet the "corrupted installation" toast by rewriting product.json checksums
 * for workbench.html to match the file currently on disk.
 * Soft-fail on EACCES — inject itself still succeeded.
 */
async function syncWorkbenchChecksum(appRoot, workbenchPath) {
  if (!appRoot || !workbenchPath) {
    return { ok: false, message: "appRoot/workbenchPath required for checksum sync" };
  }
  const productPath = productJsonPath(appRoot);
  if (!(await pathExists(productPath))) {
    return { ok: false, message: "product.json not found — cannot quiet integrity toast" };
  }
  if (!(await pathExists(workbenchPath))) {
    return { ok: false, message: "workbench.html missing for checksum sync" };
  }

  let productRaw;
  let product;
  try {
    productRaw = await fsp.readFile(productPath, "utf8");
    product = JSON.parse(productRaw);
  } catch (err) {
    return { ok: false, message: `Cannot read product.json: ${err.message || err}` };
  }

  if (!product.checksums || typeof product.checksums !== "object") {
    return { ok: true, skipped: true, message: "product.json has no checksums map" };
  }

  let key = WORKBENCH_CHECKSUM_KEY;
  if (!(key in product.checksums)) {
    const alt = Object.keys(product.checksums).find(
      (k) => /workbench\.html$/i.test(k) && /electron-sandbox/i.test(k)
    );
    if (!alt) {
      return { ok: true, skipped: true, message: "workbench.html not listed in checksums" };
    }
    key = alt;
  }

  const buf = await fsp.readFile(workbenchPath);
  const digest = computeWorkbenchChecksum(buf);
  if (product.checksums[key] === digest) {
    return { ok: true, synced: false, key, digest, message: "checksum already matches" };
  }

  const previous = product.checksums[key];
  product.checksums[key] = digest;
  // Preserve Cursor tab indentation.
  const next = `${JSON.stringify(product, null, "\t")}\n`;
  try {
    await writeTextFile(productPath, next);
  } catch (err) {
    return { ok: false, message: formatWriteError(err), previous, digest, key };
  }
  return {
    ok: true,
    synced: true,
    key,
    digest,
    previous,
    message: "product.json workbench checksum updated (integrity toast suppressed)",
  };
}

function inferAppRoot(workbenchPath) {
  // …/resources/app/out/vs/code/electron-sandbox/workbench/workbench.html → app root
  return path.resolve(workbenchPath, "..", "..", "..", "..", "..", "..");
}

function backupBesideWorkbench(workbenchPath, uuid) {
  return path.join(path.dirname(workbenchPath), `workbench.cortana.${uuid}.bak.html`);
}

function stagedSplashPath(workbenchPath) {
  return path.join(path.dirname(workbenchPath), BOOT_STAGED_NAME);
}

function stagedHeroGlobePath(workbenchPath) {
  return path.join(path.dirname(workbenchPath), HERO_GLOBE_STAGED_NAME);
}

function globalBackupFile(context) {
  return path.join(context.globalStorageUri.fsPath, GLOBAL_BACKUP_NAME);
}

async function ensureGlobalStorage(context) {
  await fsp.mkdir(context.globalStorageUri.fsPath, { recursive: true });
}

async function safeUnlink(filePath) {
  try {
    await fsp.unlink(filePath);
  } catch (err) {
    if (err && err.code !== "ENOENT") {
      throw err;
    }
  }
}

/**
 * Soft write: prefer temp+rename; fall back to direct write.
 * Never leave a .tmp beside the target on success.
 */
async function writeTextFile(target, content) {
  const dir = path.dirname(target);
  const tmp = path.join(dir, `.cortana-write-${process.pid}-${Date.now()}.tmp`);
  try {
    await fsp.writeFile(tmp, content, "utf8");
    try {
      await fsp.rename(tmp, target);
      return;
    } catch {
      // Windows often cannot rename-over; replace explicitly.
      try {
        await safeUnlink(target);
      } catch {
        /* continue to direct write */
      }
      try {
        await fsp.rename(tmp, target);
        return;
      } catch {
        /* fall through */
      }
    }
  } catch {
    /* fall through to direct write */
  } finally {
    try {
      await safeUnlink(tmp);
    } catch {
      /* ignore */
    }
  }
  await fsp.writeFile(target, content, "utf8");
}

async function copyFileBinary(src, dest) {
  await fsp.copyFile(src, dest);
}

// ---------------------------------------------------------------------------
// Locate / fingerprint
// ---------------------------------------------------------------------------

/**
 * Probe order mirrors be5invis / CSS Injector Cursor paths:
 * appRoot electron-sandbox workbench.html → apc variant → electron-browser →
 * execPath resources/app → Program Files hard probe.
 */
async function locateWorkbench() {
  const candidates = [];

  const appRoot = vscode.env.appRoot;
  if (appRoot) {
    candidates.push(
      path.join(appRoot, "out", "vs", "code", "electron-sandbox", "workbench", "workbench.html"),
      path.join(
        appRoot,
        "out",
        "vs",
        "code",
        "electron-sandbox",
        "workbench",
        "workbench-apc-extension.html"
      ),
      path.join(appRoot, "out", "vs", "code", "electron-browser", "workbench", "workbench.html")
    );
  }

  try {
    const execDir = path.dirname(process.execPath);
    const resourcesApp = path.join(execDir, "resources", "app");
    candidates.push(
      path.join(resourcesApp, "out", "vs", "code", "electron-sandbox", "workbench", "workbench.html"),
      path.join(
        resourcesApp,
        "out",
        "vs",
        "code",
        "electron-sandbox",
        "workbench",
        "workbench-apc-extension.html"
      )
    );
  } catch {
    /* ignore */
  }

  candidates.push(
    path.join(
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
    )
  );

  let apcFallback = null;
  const seen = new Set();
  for (const candidate of candidates) {
    const normalized = path.normalize(candidate);
    if (seen.has(normalized)) {
      continue;
    }
    seen.add(normalized);
    if (!(await pathExists(normalized))) {
      continue;
    }
    if (path.basename(normalized).toLowerCase() === "workbench-apc-extension.html") {
      if (!apcFallback) {
        apcFallback = normalized;
      }
      continue;
    }
    return { workbenchPath: normalized, appRoot: inferAppRoot(normalized) };
  }

  if (apcFallback) {
    return { workbenchPath: apcFallback, appRoot: inferAppRoot(apcFallback) };
  }
  return null;
}

async function readProductFingerprint(appRoot) {
  let version = "";
  let commit = "";
  let productVscodeVersion = "";
  const productPath = appRoot ? path.join(appRoot, "product.json") : "";
  if (productPath && (await pathExists(productPath))) {
    try {
      const product = JSON.parse(await fsp.readFile(productPath, "utf8"));
      if (product.version != null) {
        version = String(product.version);
      }
      if (product.commit != null) {
        commit = String(product.commit);
      }
      if (product.vscodeVersion != null) {
        productVscodeVersion = String(product.vscodeVersion);
      }
    } catch {
      /* fall through */
    }
  }
  if (!version && vscode.version) {
    version = String(vscode.version);
  }
  // Prefer live vscode.version; fall back to product.json vscodeVersion (standalone / early activate).
  const vscodeVersion = vscode.version
    ? String(vscode.version)
    : productVscodeVersion || "";
  return {
    version,
    commit,
    vscodeVersion,
    productPath,
  };
}

async function getFingerprint() {
  const loc = await locateWorkbench();
  if (!loc) {
    return {
      version: vscode.version ? String(vscode.version) : "",
      commit: "",
      appRoot: vscode.env.appRoot || "",
      workbenchPath: "",
    };
  }
  const fp = await readProductFingerprint(loc.appRoot);
  return {
    version: fp.version,
    commit: fp.commit,
    appRoot: loc.appRoot,
    workbenchPath: loc.workbenchPath,
  };
}

// ---------------------------------------------------------------------------
// Markers / HTML patch
// ---------------------------------------------------------------------------

function parseMarkers(html) {
  const startRe =
    /<!--\s*CORTANA-INJECT-START\s+uuid=([^\s]+)\s+cursorVersion=([^\s]+)\s+cursorCommit=([^\s>]*)\s*-->/;
  const endRe = /<!--\s*CORTANA-INJECT-END\s*-->/;
  const styleRe = /<style\s+id=["']cortana-workbench-css["'][\s\S]*?<\/style>/i;
  const hudStartRe = /<!--\s*CORTANA-HUD-START\s+uuid=([^\s]+)\s*-->/;
  const hudEndRe = /<!--\s*CORTANA-HUD-END\s*-->/;

  const startMatch = html.match(startRe);
  const endMatch = html.match(endRe);
  const styleMatch = html.match(styleRe);
  const hudStartMatch = html.match(hudStartRe);
  const hudEndMatch = html.match(hudEndRe);

  return {
    hasStart: Boolean(startMatch),
    hasEnd: Boolean(endMatch),
    hasStyle: Boolean(styleMatch),
    hasHudStart: Boolean(hudStartMatch),
    hasHudEnd: Boolean(hudEndMatch),
    hasHudRoot: html.includes('id="cortana-cc-hud"') || html.includes("id='cortana-cc-hud'"),
    uuid: startMatch ? startMatch[1] : null,
    hudUuid: hudStartMatch ? hudStartMatch[1] : null,
    cursorVersion: startMatch ? startMatch[2] : null,
    cursorCommit: startMatch ? (startMatch[3] || "") : null,
    startIndex: startMatch ? startMatch.index : -1,
    endIndex: endMatch ? endMatch.index : -1,
    startLen: startMatch ? startMatch[0].length : 0,
    endLen: endMatch ? endMatch[0].length : 0,
    hudStartIndex: hudStartMatch ? hudStartMatch.index : -1,
    hudEndIndex: hudEndMatch ? hudEndMatch.index : -1,
    hudEndLen: hudEndMatch ? hudEndMatch[0].length : 0,
  };
}

function isAlreadyPatched(html) {
  return (
    html.includes(MARKER_START) ||
    html.includes(MARKER_HUD_START) ||
    html.includes(`id="${STYLE_ID}"`) ||
    html.includes(`id='${STYLE_ID}'`) ||
    html.includes('id="cortana-cc-hud"')
  );
}

/**
 * Fail-safe (2): missing/corrupt markers, start without end, wrong uuid, missing style id / HUD.
 */
function markersValid(html, expectedUuid) {
  const m = parseMarkers(html);
  if (!m.hasStart && !m.hasEnd && !m.hasStyle && !m.hasHudStart && !m.hasHudEnd) {
    return { ok: false, reason: "markers missing", markers: m };
  }
  if (m.hasStart && !m.hasEnd) {
    return { ok: false, reason: "start marker without end", markers: m };
  }
  if (!m.hasStart && m.hasEnd) {
    return { ok: false, reason: "end marker without start", markers: m };
  }
  if (m.hasStart && m.hasEnd && m.startIndex > m.endIndex) {
    return { ok: false, reason: "marker order corrupt", markers: m };
  }
  if (!m.hasStyle) {
    return { ok: false, reason: "missing style id cortana-workbench-css", markers: m };
  }
  if (expectedUuid && m.uuid !== expectedUuid) {
    return { ok: false, reason: "wrong marker uuid", markers: m };
  }
  if (m.hasHudStart || m.hasHudEnd || m.hasHudRoot) {
    if (m.hasHudStart && !m.hasHudEnd) {
      return { ok: false, reason: "HUD start marker without end", markers: m };
    }
    if (!m.hasHudStart && m.hasHudEnd) {
      return { ok: false, reason: "HUD end marker without start", markers: m };
    }
    if (m.hasHudStart && m.hasHudEnd && m.hudStartIndex > m.hudEndIndex) {
      return { ok: false, reason: "HUD marker order corrupt", markers: m };
    }
    if (!m.hasHudRoot) {
      return { ok: false, reason: "missing cortana-cc-hud root", markers: m };
    }
    if (expectedUuid && m.hudUuid && m.hudUuid !== expectedUuid) {
      return { ok: false, reason: "wrong HUD marker uuid", markers: m };
    }
  } else {
    return { ok: false, reason: "missing Command Center HUD markup", markers: m };
  }
  return { ok: true, reason: "ok", markers: m };
}

/**
 * Fail-safe (2) content probe: injected <style> must still carry sheet markers
 * after sibling A–C CSS polish. Soft: only when a style block is present.
 */
const CSS_HEALTH_NEEDLES = [
  "CORTANA-HEALTH",
  "--cortana-cyan",
  "cortana-boot",
  "media/inject/hud.css",
];

function extractInjectedStyleCss(html) {
  const styleRe = /<style\s+id=["']cortana-workbench-css["']>([\s\S]*?)<\/style>/i;
  const match = html.match(styleRe);
  return match ? match[1] : "";
}

function probeInjectedCssHealth(html) {
  const css = extractInjectedStyleCss(html);
  if (!css) {
    return { ok: false, reason: "empty injected style block", found: [] };
  }
  const found = [];
  const missing = [];
  for (const needle of CSS_HEALTH_NEEDLES) {
    if (css.includes(needle)) {
      found.push(needle);
    } else {
      missing.push(needle);
    }
  }
  // Require health tag + at least boot + cyan token; HUD path comment is soft-preferred
  const required = ["CORTANA-HEALTH", "--cortana-cyan", "cortana-boot"];
  const missingRequired = required.filter((n) => !css.includes(n));
  if (missingRequired.length) {
    return {
      ok: false,
      reason: `missing CSS health needles: ${missingRequired.join(", ")}`,
      found,
      missing,
    };
  }
  return { ok: true, reason: "ok", found, missing };
}

function stripHudMarkup(html) {
  const m = parseMarkers(html);
  if (m.hasHudStart && m.hasHudEnd && m.hudStartIndex <= m.hudEndIndex) {
    const from = m.hudStartIndex;
    const to = m.hudEndIndex + m.hudEndLen;
    return `${html.slice(0, from)}${html.slice(to)}`.replace(/\n{3,}/g, "\n\n");
  }
  return html
    .replace(/<!--\s*CORTANA-HUD-START[\s\S]*?-->[\s\S]*?<!--\s*CORTANA-HUD-END\s*-->\s*/g, "")
    .replace(/<script[^>]*id=["']cortana-hud-clock-script["'][\s\S]*?<\/script>\s*/gi, "")
    .replace(/<script[^>]*id=["']cortana-hud-live-script["'][\s\S]*?<\/script>\s*/gi, "")
    .replace(/<script[^>]*id=["']cortana-hud-wave-script["'][\s\S]*?<\/script>\s*/gi, "")
    .replace(/<script[^>]*id=["']cortana-hud-voice-script["'][\s\S]*?<\/script>\s*/gi, "")
    .replace(/<script[^>]*id=["']cortana-hud-wake-script["'][\s\S]*?<\/script>\s*/gi, "")
    .replace(/<script[^>]*id=["']cortana-hud-interact-script["'][\s\S]*?<\/script>\s*/gi, "")
    .replace(/<style[^>]*id=["']cortana-hud-interact-css["'][\s\S]*?<\/style>\s*/gi, "")
    .replace(/\n{3,}/g, "\n\n");
}

function stripPatch(html) {
  let out = html;
  const m = parseMarkers(out);
  if (m.hasStart && m.hasEnd && m.startIndex <= m.endIndex) {
    const from = m.startIndex;
    const to = m.endIndex + m.endLen;
    out = `${out.slice(0, from)}${out.slice(to)}`;
  } else {
    out = out
      .replace(/<!--\s*CORTANA-INJECT-START[\s\S]*?-->\s*/g, "")
      .replace(/<style\s+id=["']cortana-workbench-css["'][\s\S]*?<\/style>\s*/gi, "")
      .replace(/<!--\s*CORTANA-INJECT-END\s*-->\s*/g, "");
  }
  out = stripHudMarkup(out);
  return out.replace(/\n{3,}/g, "\n\n");
}

function insertBeforeHeadClose(html, block) {
  const lower = html.toLowerCase();
  const idx = lower.lastIndexOf("</head>");
  if (idx === -1) {
    throw new Error("workbench.html missing </head> — refusing to patch");
  }
  const before = html.slice(0, idx).replace(/\s*$/, "\n");
  const after = html.slice(idx);
  return `${before}${block}\n${after}`;
}

function insertBeforeBodyClose(html, block) {
  const lower = html.toLowerCase();
  const idx = lower.lastIndexOf("</body>");
  if (idx === -1) {
    throw new Error("workbench.html missing </body> — refusing to patch HUD");
  }
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

function formatHudClock(now = new Date()) {
  const date = now.toLocaleDateString(undefined, {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  });
  const clock = now.toLocaleTimeString(undefined, {
    hour: "numeric",
    minute: "2-digit",
    second: "2-digit",
    hour12: true,
  });
  return { date, clock };
}

function escapeHudText(s) {
  return String(s ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

/** @typedef {{ id: string, label: string, defaultOn?: boolean, degradationStatus?: number, supportsAgent?: boolean }} CursorCatalogModel */

/**
 * Normalize catalog entries — never invent providers; only Cursor model ids from catalog source.
 * @param {unknown[]} raw
 * @returns {CursorCatalogModel[]}
 */
function normalizeCursorCatalogModels(raw) {
  if (!Array.isArray(raw)) {
    return [];
  }
  const seen = new Set();
  const out = [];
  for (const item of raw) {
    if (!item || typeof item !== "object") {
      continue;
    }
    const id = String(item.id || item.name || item.serverModelName || "").trim();
    if (!id || seen.has(id)) {
      continue;
    }
    seen.add(id);
    const label = String(item.label || item.clientDisplayName || item.inputboxShortModelName || id).trim();
    out.push({
      id,
      label: label || id,
      defaultOn: Boolean(item.defaultOn),
      degradationStatus: Number(item.degradationStatus) || 0,
      supportsAgent: Boolean(item.supportsAgent),
    });
  }
  return out;
}

function cursorStateDbPath() {
  const appData = process.env.APPDATA || process.env.HOME || "";
  if (!appData) {
    return "";
  }
  return path.join(appData, "Cursor", "User", "globalStorage", "state.vscdb");
}

/**
 * Pull availableDefaultModels2 from live Cursor state.vscdb when sqlite3 CLI is available.
 * Soft-fail → bundled media/inject/cursor-models.json.
 */
async function tryReadModelsFromStateVscdb() {
  const dbPath = cursorStateDbPath();
  if (!dbPath || !(await pathExists(dbPath))) {
    return null;
  }
  const sqlite3 = spawnSync("sqlite3", ["-version"], { encoding: "utf8", timeout: 4000 });
  if (sqlite3.error || sqlite3.status !== 0) {
    return null;
  }
  const py = spawnSync(
    process.platform === "win32" ? "python" : "python3",
    ["-c", `import json,sqlite3,os;db=os.path.join(os.environ.get('APPDATA',''),'Cursor','User','globalStorage','state.vscdb');con=sqlite3.connect('file:'+db+'?mode=ro',uri=True);raw=con.execute('SELECT value FROM ItemTable WHERE key=?',(${JSON.stringify(CURSOR_APPUSER_DB_KEY)},)).fetchone()[0];data=json.loads(raw);models=data.get('availableDefaultModels2') or [];out=[]
for m in models:
 out.append({'id':m.get('name') or m.get('serverModelName') or '','label':m.get('clientDisplayName') or m.get('inputboxShortModelName') or (m.get('name') or ''),'defaultOn':bool(m.get('defaultOn')),'degradationStatus':int(m.get('degradationStatus') or 0),'supportsAgent':bool(m.get('supportsAgent'))})
print(json.dumps({'source':'state.vscdb availableDefaultModels2','models':out}))`],
    { encoding: "utf8", timeout: 20000, windowsHide: true }
  );
  if (py.error || py.status !== 0 || !py.stdout) {
    return null;
  }
  try {
    const parsed = JSON.parse(py.stdout.trim());
    const models = normalizeCursorCatalogModels(parsed.models);
    if (!models.length) {
      return null;
    }
    return {
      source: parsed.source || "state.vscdb availableDefaultModels2",
      syncedAt: new Date().toISOString(),
      models,
    };
  } catch {
    return null;
  }
}

/**
 * Load real Cursor model catalog for LLM Status stamping (never hardcoded provider tiles).
 * @param {import("vscode").ExtensionContext} context
 */
async function loadCursorModelCatalog(context) {
  const live = await tryReadModelsFromStateVscdb();
  if (live && live.models.length) {
    return live;
  }
  const jsonPath = path.join(context.extensionUri.fsPath, CURSOR_MODELS_REL);
  try {
    const raw = JSON.parse(await fsp.readFile(jsonPath, "utf8"));
    const models = normalizeCursorCatalogModels(raw.models);
    return {
      source: raw.source || "media/inject/cursor-models.json",
      syncedAt: raw.syncedAt || raw.syncedFrom || null,
      models,
    };
  } catch {
    return { source: "unavailable", syncedAt: null, models: [] };
  }
}

async function countWorkspaceAgentTranscripts() {
  const folders = vscode.workspace.workspaceFolders || [];
  let count = 0;
  const seen = new Set();
  for (const folder of folders) {
    const roots = [folder.uri.fsPath];
    const projectsDir = path.join(folder.uri.fsPath, ".cursor", "projects");
    try {
      if (await pathExists(projectsDir)) {
        const subs = await fsp.readdir(projectsDir);
        for (const sub of subs) {
          roots.push(path.join(projectsDir, sub));
        }
      }
    } catch {
      /* ignore */
    }
    for (const root of roots) {
      const dirs = [
        path.join(root, "agent-transcripts"),
        path.join(root, ".cursor", "agent-transcripts"),
      ];
      for (const dir of dirs) {
        const norm = path.normalize(dir).toLowerCase();
        if (seen.has(norm)) {
          continue;
        }
        seen.add(norm);
        if (!(await pathExists(dir))) {
          continue;
        }
        try {
          const names = await fsp.readdir(dir);
          count += names.filter((n) => /\.jsonl$/i.test(n)).length;
        } catch {
          /* ignore */
        }
      }
    }
  }
  return count;
}

/**
 * AI Core Overview facts at inject — os/workspace/Cursor catalog only (no invented counts).
 * @param {import("vscode").ExtensionContext} context
 * @param {{ models: CursorCatalogModel[] }} catalog
 * @param {{ version?: string, commit?: string }} fp
 */
async function collectHudOverviewFacts(context, catalog, fp) {
  const transcripts = await countWorkspaceAgentTranscripts();
  const models = catalog.models || [];
  const agentCapable = models.filter((m) => m.supportsAgent).length;
  const extVersion = (() => {
    try {
      return vscode.extensions.getExtension(context.extension.id)?.packageJSON?.version || "";
    } catch {
      return "";
    }
  })();
  return {
    core: fp.version ? `Cursor ${fp.version}` : "Cursor",
    memory: {
      num: transcripts > 0 ? String(transcripts) : "—",
      unit: transcripts > 0 ? (transcripts === 1 ? "transcript" : "transcripts") : "",
    },
    voice: "Standby",
    agents: {
      num: agentCapable > 0 ? String(agentCapable) : "—",
      unit: agentCapable > 0 ? (agentCapable === 1 ? "agent model" : "agent models") : "",
    },
    llms: {
      num: models.length > 0 ? String(models.length) : "—",
      unit: models.length > 0 ? (models.length === 1 ? "model" : "models") : "",
    },
    system: extVersion ? `CORTANA ${extVersion}` : "CORTANA",
    extensionVersion: extVersion,
  };
}

function stampHudOverviewPanel(markup, overview, catalog) {
  const models = catalog.models || [];
  let out = markup;
  const memN = overview.memory?.num ?? "—";
  const memU = overview.memory?.unit ?? "";
  const agN = overview.agents?.num ?? "—";
  const agU = overview.agents?.unit ?? "";
  const llN = overview.llms?.num ?? "—";
  const llU = overview.llms?.unit ?? "";

  out = out
    .replace(/data-memory-count="[^"]*"/, `data-memory-count="${escapeHudText(memN)}"`)
    .replace(/data-agent-count="[^"]*"/, `data-agent-count="${escapeHudText(agN)}"`)
    .replace(/data-llm-count="[^"]*"/, `data-llm-count="${escapeHudText(llN)}"`);
  out = out.replace(
    /id="cortana-ov-workstation"([^>]*)>\s*<\/span>/,
    `id="cortana-ov-workstation"$1>${escapeHudText(overview.core || "—")}</span>`
  );
  out = out.replace(
    /id="cortana-ov-system"([^>]*)>\s*<\/span>/,
    `id="cortana-ov-system"$1>${escapeHudText(overview.system || "—")}</span>`
  );
  out = out.replace(
    /<span class="jcc-ov-num" data-ov-num="memory"><\/span>\s*<span class="jcc-ov-unit" data-ov-unit="memory"><\/span>/,
    `<span class="jcc-ov-num" data-ov-num="memory">${escapeHudText(memN)}</span><span class="jcc-ov-unit" data-ov-unit="memory">${escapeHudText(memU)}</span>`
  );
  out = out.replace(
    /<span class="jcc-ov-num" data-ov-num="agents"><\/span>\s*<span class="jcc-ov-unit" data-ov-unit="agents"><\/span>/,
    `<span class="jcc-ov-num" data-ov-num="agents">${escapeHudText(agN)}</span><span class="jcc-ov-unit" data-ov-unit="agents">${escapeHudText(agU)}</span>`
  );
  out = out.replace(
    /<span class="jcc-ov-num" data-ov-num="llms"><\/span>\s*<span class="jcc-ov-unit" data-ov-unit="llms"><\/span>/,
    `<span class="jcc-ov-num" data-ov-num="llms">${escapeHudText(llN)}</span><span class="jcc-ov-unit" data-ov-unit="llms">${escapeHudText(llU)}</span>`
  );
  out = out.replace(
    /id="cortana-ov-voice"([^>]*)>\s*<\/span>/,
    `id="cortana-ov-voice"$1>${escapeHudText(overview.voice || "Standby")}</span>`
  );
  if (!models.length) {
    return out;
  }
  return out;
}

/** Replace placeholder provider tiles with one chip per Cursor catalog model. */
function stampHudLlmGrid(markup, catalog) {
  const models = catalog.models || [];
  const source = escapeHudText(catalog.source || "cursor-models.json");
  const chips = models.length
    ? models
        .map((m) => {
          const id = escapeHudText(m.id);
          const label = escapeHudText(m.label || m.id);
          const degraded = Number(m.degradationStatus) > 0;
          const on = Boolean(m.defaultOn) && !degraded;
          const status = degraded ? "Degraded" : on ? "Default" : "Available";
          const cls = degraded ? "unknown" : on ? "on" : "";
          return `<div class="jcc-llm-chip ${cls}" data-model-id="${id}" data-cursor-model="1" data-status="${degraded ? "degraded" : on ? "default" : "available"}"><span>${label}</span><em>${escapeHudText(status)}</em></div>`;
        })
        .join("\n          ")
    : `<p class="jcc-feed-empty" style="grid-column:1/-1">Awaiting data — open Cursor once, run scripts/_list_picker_models.py, or re-Enable injection.</p>`;
  const state = models.length ? "live" : "empty";
  const re =
    /<div\s+class="jcc-llm-grid"\s+id="cortana-llm-grid"[\s\S]*?<\/div>(?=\s*<\/section>)/i;
  if (!re.test(markup)) {
    return markup;
  }
  return markup.replace(
    re,
    `<div class="jcc-llm-grid" id="cortana-llm-grid" data-jcc-llm-source="${source}" data-state="${state}" data-model-count="${models.length}">\n          ${chips}\n        </div>`
  );
}

/** @param {unknown} n @returns {number | null} */
function clampHudPct(n) {
  if (typeof n !== "number" || !Number.isFinite(n)) return null;
  return Math.max(0, Math.min(100, Math.round(n)));
}

function sampleCpuTimes() {
  const cpus = os.cpus();
  if (!cpus || !cpus.length) return null;
  let idle = 0;
  let total = 0;
  for (const c of cpus) {
    const t = c.times;
    idle += t.idle;
    total += t.user + t.nice + t.sys + t.idle + t.irq;
  }
  return { idle, total };
}

/** Instantaneous CPU % via two os.cpus() samples; null if unavailable. */
async function sampleCpuPct() {
  const a = sampleCpuTimes();
  if (!a) return null;
  await new Promise((r) => setTimeout(r, 120));
  const b = sampleCpuTimes();
  if (!b) return null;
  const dTotal = b.total - a.total;
  const dIdle = b.idle - a.idle;
  if (dTotal <= 0) return null;
  return clampHudPct(100 * (1 - dIdle / dTotal));
}

/** Workspace volume used % via fs.statfsSync; null if unavailable. */
function sampleDiskPct() {
  try {
    if (typeof fs.statfsSync !== "function") return null;
    const root =
      vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || process.cwd();
    if (!root) return null;
    const s = fs.statfsSync(root);
    const bsize = Number(s.bsize) || Number(s.frsize) || 0;
    const blocks = Number(s.blocks) || 0;
    const avail = Number(s.bavail != null ? s.bavail : s.bfree) || 0;
    const total = blocks * bsize;
    if (!total) return null;
    return clampHudPct(((total - avail * bsize) / total) * 100);
  } catch {
    return null;
  }
}

/** Honest inject-time facts only — never invent weather, missions, or dummy gauges. */
async function collectHudLiveFacts() {
  let user = "—";
  let initials = "—";
  try {
    const u = os.userInfo();
    user = (u && u.username) || "—";
    const parts = String(user).trim().split(/[.\s_-]+/).filter(Boolean);
    initials = parts.length
      ? parts
          .slice(0, 2)
          .map((p) => p[0].toUpperCase())
          .join("")
      : String(user).slice(0, 2).toUpperCase() || "—";
  } catch {
    /* keep — */
  }
  const host = (() => {
    try {
      return os.hostname() || "—";
    } catch {
      return "—";
    }
  })();
  const folders = vscode.workspace.workspaceFolders || [];
  const workspace = folders.length ? folders.map((f) => f.name).join(", ") : "No folder open";
  let ramPct = null;
  try {
    const total = os.totalmem();
    const free = os.freemem();
    if (total > 0) ramPct = clampHudPct(((total - free) / total) * 100);
  } catch {
    ramPct = null;
  }
  let cpuPct = null;
  try {
    cpuPct = await sampleCpuPct();
  } catch {
    cpuPct = null;
  }
  const diskPct = sampleDiskPct();
  return { user, initials, host, workspace, ramPct, cpuPct, diskPct };
}

/**
 * Stamp a System Monitor gauge with a real percent, or leave blank (—).
 * @param {string} markup
 * @param {string} id e.g. cortana-gauge-ram
 * @param {string} lab
 * @param {number | null} pct
 * @param {string} title
 */
function stampHudGauge(markup, id, lab, metric, pct, title) {
  const p = clampHudPct(pct);
  const open =
    p == null
      ? `<div class="jcc-gauge jcc-gauge-await" style="--p:0" id="${id}" data-lab="${lab}" data-metric="${metric}" title="${title}">`
      : `<div class="jcc-gauge" style="--p:${p}" data-pct="${p}" id="${id}" data-lab="${lab}" data-metric="${metric}" title="${title}">`;
  const re = new RegExp(`<div\\b[^>]*\\bid="${id}"[^>]*>`, "i");
  if (!re.test(markup)) return markup;
  return markup.replace(re, open);
}

async function readHudMarkup(context) {
  const full = path.join(context.extensionUri.fsPath, HUD_MARKUP_REL);
  let markup = await fsp.readFile(full, "utf8");
  const { date, clock } = formatHudClock();
  const live = await collectHudLiveFacts();
  const loc = await locateWorkbench();
  const fp = loc ? await readProductFingerprint(loc.appRoot) : { version: "", commit: "" };
  const catalog = await loadCursorModelCatalog(context);
  const overview = await collectHudOverviewFacts(context, catalog, fp);
  markup = markup
    .replace(/id="cortana-hud-date">[^<]*</, `id="cortana-hud-date">${escapeHudText(date)}<`)
    .replace(/id="cortana-hud-clock">[^<]*</, `id="cortana-hud-clock">${escapeHudText(clock)}<`)
    .replace(/id="cortana-op-av">[^<]*</, `id="cortana-op-av">${escapeHudText(live.initials)}<`)
    .replace(/id="cortana-op-name">[^<]*</, `id="cortana-op-name">${escapeHudText(live.user)}<`)
    .replace(/id="cortana-meta-host">[^<]*</, `id="cortana-meta-host">${escapeHudText(live.host)}<`)
    .replace(/id="cortana-meta-ws">[^<]*</, `id="cortana-meta-ws">${escapeHudText(live.workspace)}<`)
    .replace(
      /id="cortana-system-status-text">[^<]*</,
      `id="cortana-system-status-text">SYSTEM STATUS · INJECT ON<`
    );
  markup = stampHudOverviewPanel(markup, overview, catalog);
  markup = stampHudLlmGrid(markup, catalog);
  markup = stampHudGauge(
    markup,
    "cortana-gauge-cpu",
    "CPU",
    "cpu",
    live.cpuPct,
    "CPU from os.cpus sample at inject"
  );
  markup = stampHudGauge(
    markup,
    "cortana-gauge-ram",
    "RAM",
    "ram",
    live.ramPct,
    "RAM from os.freemem at inject"
  );
  markup = stampHudGauge(
    markup,
    "cortana-gauge-disk",
    "Disk",
    "disk",
    live.diskPct,
    "Disk from fs.statfs at inject"
  );
  const clockScript = [
    `<script id="cortana-hud-clock-script">`,
    `(function(){function t(){var d=new Date(),c=document.getElementById("cortana-hud-clock"),a=document.getElementById("cortana-hud-date");`,
    `if(c)c.textContent=d.toLocaleTimeString(undefined,{hour:"numeric",minute:"2-digit",second:"2-digit",hour12:true});`,
    `if(a)a.textContent=d.toLocaleDateString(undefined,{weekday:"long",year:"numeric",month:"long",day:"numeric"});}`,
    `t();setInterval(t,1000);}());`,
    `</script>`,
  ].join("");
  const liveScript = buildHudLiveScript(overview);
  const waveScript = buildHudWaveScript();
  const voiceScript = buildHudVoiceScript();
  const wakeScript = buildHudWakeScript();
  const interactStyle = buildHudInteractStyle();
  const interactScript = buildHudInteractScript();
  return {
    markup,
    clockScript,
    liveScript,
    waveScript,
    voiceScript,
    wakeScript,
    interactStyle,
    interactScript,
  };
}

/**
 * Browser-honest live fields: network, overview data-ov-live rows, talk hint, voice row sync.
 * @param {Record<string, unknown>} overviewSeed inject-time facts from collectHudOverviewFacts
 */
function buildHudLiveScript(overviewSeed) {
  const seedJson = JSON.stringify(overviewSeed || {}).replace(/</g, "\\u003c");
  const body = [
    "(function(){",
    "if(window.__cortanaLiveWired)return;window.__cortanaLiveWired=true;",
    `var OV_SEED=${seedJson};`,
    "function setOvNum(key,num,unit){",
    "var n=document.querySelector('[data-ov-num=\"'+key+'\"]');",
    "var u=document.querySelector('[data-ov-unit=\"'+key+'\"]');",
    "if(n&&num!=null&&num!=='')n.textContent=String(num);",
    "if(u)u.textContent=unit!=null?String(unit):'';",
    "}",
    "function applyOverviewSeed(){",
    "if(!OV_SEED)return;",
    "var core=document.querySelector('[data-ov-live=\"core\"]')||document.getElementById('cortana-ov-workstation');",
    "if(core&&OV_SEED.core)core.textContent=OV_SEED.core;",
    "var sys=document.querySelector('[data-ov-live=\"system\"]')||document.getElementById('cortana-ov-system');",
    "if(sys&&OV_SEED.system)sys.textContent=OV_SEED.system;",
    "if(OV_SEED.memory)setOvNum('memory',OV_SEED.memory.num,OV_SEED.memory.unit);",
    "if(OV_SEED.agents)setOvNum('agents',OV_SEED.agents.num,OV_SEED.agents.unit);",
    "if(OV_SEED.llms)setOvNum('llms',OV_SEED.llms.num,OV_SEED.llms.unit);",
    "}",
    "function net(){",
    "var el=document.getElementById('cortana-meta-net');if(!el)return;",
    "var on=typeof navigator!=='undefined'&&navigator.onLine;",
    "el.textContent=on?'Online':'Offline';",
    "if(on)el.classList.add('ok');else el.classList.remove('ok');",
    "}",
    "function syncTalkHint(){",
    "var voice=document.getElementById('cortana-voice-status');",
    "var hint=document.getElementById('cortana-talk-hint');",
    "if(!voice||!hint)return;",
    "var t=String(voice.textContent||'').trim();",
    "if(/^Listening/i.test(t))hint.textContent='Listening…';",
    "else if(/responding/i.test(t))hint.textContent='Responding…';",
    "else if(/^Offline/i.test(t))hint.textContent='Voice offline';",
    "else hint.textContent='Tap to speak';",
    "}",
    "function syncVoiceOv(){",
    "var v=document.getElementById('cortana-voice-status');",
    "var ov=document.getElementById('cortana-ov-voice')||document.querySelector('[data-ov-live=\"voice\"]');",
    "if(v&&ov){var t=String(v.textContent||'').trim();ov.textContent=t||'Standby';}",
    "}",
    "applyOverviewSeed();",
    "net();",
    "syncVoiceOv();",
    "window.addEventListener('online',net);",
    "window.addEventListener('offline',net);",
    "var voiceEl=document.getElementById('cortana-voice-status');",
    "if(voiceEl&&window.MutationObserver){",
    "new MutationObserver(function(){syncTalkHint();syncVoiceOv();}).observe(voiceEl,{childList:true,characterData:true,subtree:true});",
    "}",
    "syncTalkHint();",
    "setInterval(function(){syncTalkHint();syncVoiceOv();},1500);",
    "})();",
  ].join("");
  return `<script id="cortana-hud-live-script">${body}</script>`;
}

/**
 * Injected HUD voice click bridge.
 * Workbench page has no vscode API — try Cursor DOM mic / chat openers,
 * CustomEvent + postMessage hooks, then a HUD toast naming cortana.voice.talk.
 */
function buildHudVoiceScript() {
  // Keep as one IIFE string; no template ${} interpolation inside body.
  const body = [
    "(function(){",
    "if(window.__cortanaVoiceWired)return;window.__cortanaVoiceWired=true;",
    "var VOICE_SELS=[",
    "'button[aria-label=\"Start voice chat\"]',",
    "'button[aria-label*=\"Start voice chat\" i]',",
    "'button[aria-label*=\"Voice Chat\" i]',",
    "'button[aria-label*=\"voice chat\" i]',",
    "'button[title*=\"Start voice chat\" i]',",
    "'button[aria-label*=\"Start Voice\" i]',",
    "'.codicon-mic',",
    "'button[aria-label*=\"Dictate\" i]',",
    "'button[aria-label*=\"microphone\" i]',",
    "'button[aria-label*=\"Microphone\" i]'",
    "];",
    "var CHAT_SELS=[",
    "'button[aria-label=\"Chat\"]',",
    "'a[aria-label=\"Chat\"]',",
    "'button[aria-label*=\"Open Chat\" i]',",
    "'button[aria-label*=\"Agent\" i]',",
    "'div[aria-label*=\"Chat\" i]',",
    "'.codicon-comment-discussion',",
    "'[data-command=\"workbench.action.chat.open\"]',",
    "'[data-command=\"aichat.newchataction\"]'",
    "];",
    "function qsa(sel){try{return Array.prototype.slice.call(document.querySelectorAll(sel));}catch(e){return[];}}",
    "function clickFirst(sels){",
    "for(var i=0;i<sels.length;i++){",
    "var nodes=qsa(sels[i]);",
    "for(var j=0;j<nodes.length;j++){",
    "var el=nodes[j];",
    "if(!el||el.closest&&el.closest('#cortana-cc-hud'))continue;",
    "try{el.click();return el;}catch(e){}",
    "}",
    "}",
    "return null;",
    "}",
    "function toast(msg){",
    "var host=document.getElementById('cortana-cc-hud')||document.body;",
    "var t=document.getElementById('cortana-voice-toast');",
    "if(!t){t=document.createElement('div');t.id='cortana-voice-toast';",
    "t.setAttribute('role','status');",
    "t.style.cssText='position:fixed;left:50%;bottom:88px;transform:translateX(-50%);z-index:100000;",
    "padding:10px 16px;border-radius:8px;background:rgba(0,20,40,.92);border:1px solid rgba(0,212,255,.45);",
    "color:#cfefff;font:12px/1.35 Segoe UI,system-ui,sans-serif;pointer-events:none;max-width:420px;text-align:center;",
    "box-shadow:0 0 24px rgba(0,212,255,.2)';host.appendChild(t);}",
    "t.textContent=msg;t.style.opacity='1';",
    "clearTimeout(t.__hide);t.__hide=setTimeout(function(){t.style.opacity='0';},4200);",
    "}",
    "function signal(){",
    "try{window.dispatchEvent(new CustomEvent('cortana-voice',{detail:{source:'hud',action:'talk'}}));}catch(e){}",
    "try{window.postMessage({type:'cortana-voice',action:'talk',source:'hud'},'*');}catch(e){}",
    "if(typeof window.__cortanaVoiceClick==='function'){",
    "try{window.__cortanaVoiceClick({source:'hud'});}catch(e){}",
    "}",
    "}",
    "function markVoiceLive(on){",
    "var live=!!on;",
    "window.__cortanaVoiceLiveState=live;",
    "var hud=document.getElementById('cortana-cc-hud');",
    "var talk=document.getElementById('cortana-talk-cta');",
    "var wrap=talk&&talk.closest?talk.closest('.jcc-talk-wrap'):(hud?hud.querySelector('.jcc-talk-wrap'):null);",
    "var rail=hud?hud.querySelector('.jcc-voice'):null;",
    "var hint=document.getElementById('cortana-talk-hint');",
    "var nodes=[hud,talk,wrap,rail].filter(Boolean);",
    "for(var i=0;i<nodes.length;i++){",
    "var el=nodes[i];",
    "if(live){el.classList.add('is-live');el.setAttribute('data-voice-live','1');}",
    "else{el.classList.remove('is-live');el.removeAttribute('data-voice-live');}",
    "}",
    "if(hint)hint.textContent=live?'Voice active':'Tap to speak';",
    "try{window.dispatchEvent(new CustomEvent('cortana-voice-live',{detail:{live:live,source:'hud'}}));}catch(e){}",
    "try{window.postMessage({type:'cortana-voice-live',live:live,source:'hud'},'*');}catch(e){}",
    "return live;",
    "}",
    "function publishMicStream(stream,meta){",
    "if(!stream)return null;",
    "window.__cortanaMicStream=stream;",
    "if(typeof window.__cortanaOnMicStream==='function'){",
    "try{window.__cortanaOnMicStream(stream,meta||{source:'voice'});}catch(e){}",
    "}",
    "try{window.dispatchEvent(new CustomEvent('cortana-mic-stream',{detail:{stream:stream,meta:meta||{source:'voice'}}}));}catch(e){}",
    "return stream;",
    "}",
    "function ensureTalkMic(meta,cb){",
    "var existing=window.__cortanaMicStream;",
    "if(existing&&existing.active){publishMicStream(existing,meta);if(cb)cb(existing);return;}",
    "var md=navigator.mediaDevices;",
    "if(!md||!md.getUserMedia){if(cb)cb(null);return;}",
    "md.getUserMedia({audio:true}).then(function(stream){",
    "publishMicStream(stream,meta);if(cb)cb(stream);",
    "}).catch(function(){if(cb)cb(null);});",
    "}",
    "window.__cortanaPublishMicStream=publishMicStream;",
    "window.__cortanaEnsureTalkMic=ensureTalkMic;",
    "var _prevVoiceLive=typeof window.__cortanaVoiceLive==='function'?window.__cortanaVoiceLive:null;",
    "window.__cortanaVoiceLive=function(on){",
    "var live=markVoiceLive(on);",
    "if(live)ensureTalkMic({source:'voice-live',live:true});",
    "if(_prevVoiceLive){try{_prevVoiceLive(on);}catch(e){}}",
    "return live;",
    "};",
    "function tryVoiceDom(){return !!clickFirst(VOICE_SELS);}",
    "function tryOpenChatDom(){return !!clickFirst(CHAT_SELS);}",
    "function revealIde(){",
    "var cb=document.getElementById('cortana-focus-toggle');",
    "if(cb&&!cb.checked){cb.checked=true;try{cb.dispatchEvent(new Event('change',{bubbles:true}));}catch(e){}return true;}",
    "return false;",
    "}",
    "function runExtCommand(id){",
    "if(typeof window.__cortanaRunCommand==='function')return window.__cortanaRunCommand(id);",
    "try{",
    "var a=document.createElement('a');a.href='command:'+id;",
    "a.style.cssText='position:fixed;left:-9999px;opacity:0';",
    "document.body.appendChild(a);a.click();setTimeout(function(){try{a.remove();}catch(e){}},80);",
    "return true;}catch(e){return false;}",
    "}",
    "function startVoice(){",
    "runExtCommand('cortana.voice.talk');",
    "signal();",
    "window.__cortanaVoiceLive(true);",
    "ensureTalkMic({source:'mic',live:true});",
    "revealIde();",
    "if(tryVoiceDom()){toast('Voice channel — Cursor mic engaged');return;}",
    "tryOpenChatDom();",
    "setTimeout(function(){",
    "if(tryVoiceDom()){toast('Voice channel — Cursor mic engaged');return;}",
    "toast('Press Command Palette → CORTANA: Talk / Start Voice (cortana.voice.talk)');",
    "},400);",
    "}",
    "window.__cortanaStartVoice=startVoice;",
    "function isVoiceTarget(el){",
    "if(!el||!el.closest)return null;",
    "return el.closest('[data-cortana-action=\"voice\"],[data-cortana-voice],#cortana-mic-btn,.jcc-mic,.jcc-mic-hint,.jcc-voice,#cortana-talk-cta,.jcc-talk,.jcc-talk-wrap');",
    "}",
    "function onActivate(e){",
    "var t=isVoiceTarget(e.target);",
    "if(!t||!t.closest('#cortana-cc-hud'))return;",
    "if(e.type==='keydown'&&e.key!=='Enter'&&e.key!==' ')return;",
    "e.preventDefault();e.stopPropagation();",
    "startVoice();",
    "}",
    "document.addEventListener('click',onActivate,true);",
    "document.addEventListener('keydown',onActivate,true);",
    "})();",
  ].join("");
  return `<script id="cortana-hud-voice-script">${body}</script>`;
}


/**
 * Hands-free wake word ("Hey Cortana") via SpeechRecognition.
 * Privacy: mic/recognition only while inject HUD is present and data-cortana-wake is on
 * (paused in Focus Mode / data-cortana-mute). No listening when injection is disabled.
 * Calls the same window.__cortanaStartVoice helper as the rail mic click.
 */
function buildHudWakeScript() {
  const body = [
    "(function(){",
    "if(window.__cortanaWakeWired)return;window.__cortanaWakeWired=true;",
    "var PHRASE=/\\bhey\\s+cortana\\b/i;",
    "var lastFire=0,rec=null,armed=false,want=true;",
    "function hud(){return document.getElementById('cortana-cc-hud');}",
    "function voiceBox(){var h=hud();return h?h.querySelector('.jcc-voice'):null;}",
    "function statusEl(){var h=hud();return h?(h.querySelector('#cortana-voice-status')||h.querySelector('.jcc-listen')):null;}",
    "function ovVoice(){var h=hud();return h?h.querySelector('[data-row=\"voice\"] .jcc-ov-v'):null;}",
    "function setStatus(text,mode){",
    "var s=statusEl(),box=voiceBox(),ov=ovVoice(),hint=document.getElementById('cortana-talk-hint');",
    "if(s)s.textContent=text;",
    "if(box){box.classList.remove('is-listening','is-offline','is-responding');",
    "if(mode)box.classList.add(mode);}",
    "if(ov){",
    "if(mode==='is-offline'){ov.textContent='Offline';ov.removeAttribute('data-tone');}",
    "else if(mode==='is-listening'){ov.textContent='Listening';ov.setAttribute('data-tone','ok');}",
    "else if(mode==='is-responding'){ov.textContent='Responding';ov.setAttribute('data-tone','ok');}",
    "else{ov.textContent='Standby';ov.removeAttribute('data-tone');}",
    "}",
    "if(hint){",
    "if(mode==='is-listening')hint.textContent='Listening…';",
    "else if(mode==='is-responding')hint.textContent='Responding…';",
    "else if(mode==='is-offline')hint.textContent='Voice offline';",
    "else hint.textContent='Tap to speak';",
    "}",
    "}",
    "function wakeAllowed(){",
    "var h=hud();if(!h)return false;",
    "var mute=(h.getAttribute('data-cortana-mute')||'').toLowerCase();",
    "if(mute==='1'||mute==='true'||mute==='on')return false;",
    "var wake=(h.getAttribute('data-cortana-wake')||'on').toLowerCase();",
    "if(wake==='off'||wake==='0'||wake==='false')return false;",
    "var focus=document.getElementById('cortana-focus-toggle');",
    "if(focus&&focus.checked)return false;",
    "return true;",
    "}",
    "function invokeVoice(){",
    "if(typeof window.__cortanaStartVoice==='function'){try{window.__cortanaStartVoice();return true;}catch(e){}}",
    "try{window.dispatchEvent(new CustomEvent('cortana-voice',{detail:{source:'wake',action:'talk'}}));}catch(e){}",
    "return false;",
    "}",
    "function onWake(){",
    "var now=Date.now();if(now-lastFire<4500)return;lastFire=now;",
    "setStatus('Cortana responding\\u2026','is-responding');",
    "if(typeof window.__cortanaVoiceLive==='function'){",
    "try{window.__cortanaVoiceLive(true);}catch(e){}",
    "}else{",
    "var talk=document.getElementById('cortana-talk-cta'),h=hud();",
    "if(talk){talk.classList.add('is-live');talk.setAttribute('data-voice-live','1');}",
    "if(h){h.classList.add('is-live');h.setAttribute('data-voice-live','1');}",
    "}",
    "if(typeof window.__cortanaEnsureTalkMic==='function'){",
    "try{window.__cortanaEnsureTalkMic({source:'wake',live:true});}catch(e){}",
    "}",
    "invokeVoice();",
    "setTimeout(function(){if(armed&&wakeAllowed())setStatus('Listening\\u2026','is-listening');},2200);",
    "}",
    "function matches(text){",
    "var t=String(text||'').toLowerCase().replace(/[^a-z0-9\\s]/g,' ').replace(/\\s+/g,' ').trim();",
    "return PHRASE.test(t);",
    "}",
    "function stopRec(){",
    "armed=false;",
    "if(rec){try{rec.onend=null;rec.onerror=null;rec.onresult=null;rec.stop();}catch(e){}rec=null;}",
    "}",
    "function bindRec(r){",
    "r.continuous=true;r.interimResults=true;r.lang='en-US';",
    "r.onstart=function(){armed=true;if(wakeAllowed())setStatus('Listening\\u2026','is-listening');};",
    "r.onresult=function(ev){",
    "if(!wakeAllowed())return;",
    "for(var i=ev.resultIndex;i<ev.results.length;i++){",
    "var tr=ev.results[i][0]&&ev.results[i][0].transcript;",
    "if(matches(tr)){onWake();break;}",
    "}",
    "};",
    "r.onerror=function(ev){",
    "var err=ev&&ev.error?String(ev.error):'error';",
    "if(err==='aborted'||err==='no-speech')return;",
    "setStatus('Offline','is-offline');armed=false;",
    "};",
    "r.onend=function(){",
    "if(!want||!wakeAllowed()){armed=false;return;}",
    "try{r.start();}catch(e){setTimeout(function(){try{r.start();}catch(e2){setStatus('Offline','is-offline');}},400);}",
    "};",
    "}",
    "function startRec(){",
    "if(!wakeAllowed()){setStatus('Standby','');return;}",
    "var SR=window.SpeechRecognition||window.webkitSpeechRecognition;",
    "if(!SR){setStatus('Offline','is-offline');return;}",
    "stopRec();",
    "rec=new SR();bindRec(rec);want=true;",
    "try{rec.start();}catch(e){setStatus('Offline','is-offline');}",
    "}",
    "function arm(){",
    "if(!hud())return;",
    "if(!wakeAllowed()){stopRec();setStatus('Standby','');return;}",
    "if(armed)return;",
    "setStatus('Standby','');",
    "var md=navigator.mediaDevices;",
    "if(md&&md.getUserMedia){",
    "md.getUserMedia({audio:true}).then(function(stream){",
    "if(typeof window.__cortanaPublishMicStream==='function'){",
    "try{window.__cortanaPublishMicStream(stream,{source:'wake-arm',live:false});}catch(e){}",
    "}else{",
    "window.__cortanaMicStream=stream;",
    "if(typeof window.__cortanaOnMicStream==='function'){",
    "try{window.__cortanaOnMicStream(stream,{source:'wake-arm',live:false});}catch(e){}",
    "}",
    "try{window.dispatchEvent(new CustomEvent('cortana-mic-stream',{detail:{stream:stream,meta:{source:'wake-arm',live:false}}}));}catch(e){}",
    "}",
    "startRec();",
    "}).catch(function(){setStatus('Offline','is-offline');});",
    "}else{startRec();}",
    "}",
    "function onFocusChange(){",
    "if(wakeAllowed()){want=true;arm();}",
    "else{want=false;stopRec();setStatus('Standby','');",
    "if(typeof window.__cortanaVoiceLive==='function'){try{window.__cortanaVoiceLive(false);}catch(e){}}",
    "}",
    "}",
    "function boot(){",
    "if(!hud()){setTimeout(boot,800);return;}",
    "var focus=document.getElementById('cortana-focus-toggle');",
    "if(focus&&!focus.__cortanaWakeBound){focus.__cortanaWakeBound=1;focus.addEventListener('change',onFocusChange);}",
    "arm();",
    "}",
    "if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);",
    "else boot();",
    "})();",
  ].join("");
  return `<script id="cortana-hud-wake-script">${body}</script>`;
}

/** Mic-driven talk meter + rail/capsule waveform level (pairs with voice/wake publishMic). */
function buildHudWaveScript() {
  const body = [
    "(function(){",
    "if(window.__cortanaWaveWired)return;window.__cortanaWaveWired=true;",
    "function meterBar(){return document.getElementById('cortana-talk-meter-bar');}",
    "function waveNodes(){",
    "try{return document.querySelectorAll('#cortana-cc-hud .jcc-wave.voice,#cortana-cc-hud .jcc-talk-wave');}",
    "catch(e){return[];}",
    "}",
    "var ctx=null,raf=0;",
    "function stopLoop(){if(raf){cancelAnimationFrame(raf);raf=0;}}",
    "function startLoop(stream){",
    "if(!stream||!stream.active)return;",
    "stopLoop();",
    "try{",
    "var AC=window.AudioContext||window.webkitAudioContext;if(!AC)return;",
    "if(!ctx)ctx=new AC();",
    "if(ctx.state==='suspended'){try{ctx.resume();}catch(e){}}",
    "var src=ctx.createMediaStreamSource(stream);",
    "var an=ctx.createAnalyser();an.fftSize=256;src.connect(an);",
    "var data=new Uint8Array(an.frequencyBinCount);",
    "function tick(){",
    "an.getByteFrequencyData(data);var s=0,i;for(i=0;i<data.length;i++)s+=data[i];",
    "var n=Math.min(100,Math.round((s/data.length)/1.65));",
    "var bar=meterBar();if(bar)bar.style.width=n+'%';",
    "var nodes=waveNodes();for(i=0;i<nodes.length;i++){nodes[i].setAttribute('data-level',String(n));}",
    "raf=requestAnimationFrame(tick);",
    "}",
    "tick();",
    "}catch(e){}",
    "}",
    "window.__cortanaOnMicStream=function(stream,meta){",
    "if(stream&&stream.active)startLoop(stream);else stopLoop();",
    "};",
    "window.addEventListener('cortana-mic-stream',function(ev){",
    "var d=ev&&ev.detail;if(d&&d.stream)startLoop(d.stream);",
    "});",
    "if(window.__cortanaMicStream&&window.__cortanaMicStream.active)startLoop(window.__cortanaMicStream);",
    "})();",
  ].join("");
  return `<script id="cortana-hud-wave-script">${body}</script>`;
}

/**
 * Pointer-events patch: HUD shell is click-through; main column + footer chrome
 * must explicitly capture input (Worker WIRE — inject engine, not full hud.css rewrite).
 */
function buildHudInteractStyle() {
  return [
    `<style id="cortana-hud-interact-css">`,
    "/* CORTANA-HEALTH: interact-pointer */",
    "#cortana-cc-hud .jcc-main,",
    "#cortana-cc-hud .jcc-grid,",
    "#cortana-cc-hud .jcc-footer,",
    "#cortana-cc-hud .jcc-talk-wrap,",
    "#cortana-cc-hud .jcc-cmd,",
    "#cortana-cc-hud .jcc-briefing,",
    "#cortana-cc-hud .jcc-memory-map,",
    "#cortana-cc-hud .jcc-operator,",
    "#cortana-cc-hud .jcc-status-pill,",
    "#cortana-cc-hud .jcc-clock-wrap,",
    "#cortana-cc-hud .jcc-brand { pointer-events: auto !important; }",
    "#cortana-cc-hud button, #cortana-cc-hud .jcc-nav-item, #cortana-cc-hud .jcc-focus { cursor: pointer; }",
    "</style>",
  ].join("\n");
}

/**
 * HUD bootstrap: focus toggle, nav, quick commands, command: URI bridge to extension host.
 */
function buildHudInteractScript() {
  const body = [
    "(function(){",
    "if(window.__cortanaInteractWired)return;window.__cortanaInteractWired=true;",
    "function hud(){return document.getElementById('cortana-cc-hud');}",
    "function runExtCommand(id){",
    "if(!id)return false;",
    "try{",
    "var a=document.createElement('a');",
    "a.href='command:'+id;",
    "a.setAttribute('draggable','false');",
    "a.style.cssText='position:fixed;left:-9999px;top:0;opacity:0;pointer-events:none';",
    "(document.body||document.documentElement).appendChild(a);",
    "a.click();",
    "setTimeout(function(){try{a.remove();}catch(e){}},80);",
    "return true;",
    "}catch(e){return false;}",
    "}",
    "window.__cortanaRunCommand=runExtCommand;",
    "function wireVoiceBridge(){",
    "var prev=typeof window.__cortanaVoiceClick==='function'?window.__cortanaVoiceClick:null;",
    "window.__cortanaVoiceClick=function(meta){",
    "runExtCommand('cortana.voice.talk');",
    "if(prev){try{prev(meta);}catch(e){}}",
    "};",
    "window.addEventListener('cortana-voice',function(){runExtCommand('cortana.voice.talk');});",
    "window.addEventListener('message',function(ev){",
    "var d=ev&&ev.data;if(!d||d.type!=='cortana-voice')return;",
    "runExtCommand('cortana.voice.talk');",
    "},false);",
    "}",
    "function onDocClick(e){",
    "var t=e.target;if(!t||!t.closest)return;",
    "var root=t.closest('#cortana-cc-hud');if(!root)return;",
    "var cmdEl=t.closest('[data-cortana-cmd]');",
    "if(cmdEl){",
    "var cmd=(cmdEl.getAttribute('data-cortana-cmd')||'').toLowerCase();",
    "if(cmd==='task'){e.preventDefault();runExtCommand('workbench.action.tasks.runTask');return;}",
    "if(cmd==='calendar'){e.preventDefault();return;}",
    "if(cmd==='workflow'){e.preventDefault();runExtCommand('workbench.action.showCommands');return;}",
    "}",
    "var nav=t.closest('.jcc-nav-item');",
    "if(nav){e.preventDefault();",
    "var items=root.querySelectorAll('.jcc-nav-item');",
    "for(var i=0;i<items.length;i++)items[i].classList.remove('active');",
    "nav.classList.add('active');",
    "}",
    "}",
    "function boot(){",
    "if(!hud()){setTimeout(boot,400);return;}",
    "document.body&&document.body.classList.add('cortana-inject','cortana-boot');",
    "setTimeout(function(){document.body&&document.body.classList.remove('cortana-boot');},",
    "parseInt(getComputedStyle(document.documentElement).getPropertyValue('--cortana-boot-ms'),10)||1800);",
    "wireVoiceBridge();",
    "document.addEventListener('click',onDocClick,true);",
    "}",
    "if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);",
    "else boot();",
    "})();",
  ].join("");
  return `<script id="cortana-hud-interact-script">${body}</script>`;
}

/** Crash guard: refuse patches that place HUD markup or scripts after </body>. */
function validateHudPatchPlacement(html) {
  const lower = html.toLowerCase();
  const bodyIdx = lower.lastIndexOf("</body>");
  if (bodyIdx === -1) {
    throw new Error("workbench.html missing </body> — refusing to write patch");
  }
  const htmlIdx = lower.lastIndexOf("</html>");
  const tailStart = bodyIdx + "</body>".length;
  const tail = html.slice(tailStart, htmlIdx === -1 ? undefined : htmlIdx).trim();
  if (/<script\b/i.test(tail) || /CORTANA-HUD/i.test(tail) || /cortana-cc-hud/i.test(tail)) {
    throw new Error(
      "Inject block would sit outside </body> (scripts/HUD after body) — refusing write (Cursor crash guard)"
    );
  }
  const m = parseMarkers(html);
  if (m.hasHudStart && m.hudStartIndex > bodyIdx) {
    throw new Error("HUD markers start after </body> — refusing write");
  }
  if (m.hasHudEnd && m.hudEndIndex > bodyIdx) {
    throw new Error("HUD markers end after </body> — refusing write");
  }
  return true;
}

function buildHudBlock({
  uuid,
  markup,
  interactStyle,
  clockScript,
  liveScript,
  waveScript,
  voiceScript,
  wakeScript,
  interactScript,
}) {
  return [
    `<!-- ${MARKER_HUD_START} uuid=${uuid} -->`,
    interactStyle || "",
    markup.trim(),
    clockScript,
    liveScript || "",
    waveScript || "",
    voiceScript || "",
    wakeScript || "",
    interactScript || "",
    `<!-- ${MARKER_HUD_END} -->`,
  ].join("\n");
}

// ---------------------------------------------------------------------------
// globalState + settings mirror
// ---------------------------------------------------------------------------

async function readState(context) {
  const gs = context.globalState;
  return {
    enabled: Boolean(gs.get(GS.enabled, false)),
    active: Boolean(gs.get(GS.active, false)),
    cursorVersion: gs.get(GS.cursorVersion, "") || "",
    cursorCommit: gs.get(GS.cursorCommit, "") || "",
    backupUuid: gs.get(GS.backupUuid, "") || "",
    markerUuid: gs.get(GS.markerUuid, "") || "",
    lastError: gs.get(GS.lastError, "") || "",
    lastOkFingerprint: gs.get(GS.lastOkFingerprint, "") || "",
  };
}

async function writeState(context, patch) {
  const updates = [];
  if ("enabled" in patch) {
    updates.push(context.globalState.update(GS.enabled, Boolean(patch.enabled)));
  }
  if ("active" in patch) {
    updates.push(context.globalState.update(GS.active, Boolean(patch.active)));
  }
  if ("cursorVersion" in patch) {
    updates.push(context.globalState.update(GS.cursorVersion, patch.cursorVersion || ""));
  }
  if ("cursorCommit" in patch) {
    updates.push(context.globalState.update(GS.cursorCommit, patch.cursorCommit || ""));
  }
  if ("backupUuid" in patch) {
    updates.push(context.globalState.update(GS.backupUuid, patch.backupUuid || ""));
  }
  if ("markerUuid" in patch) {
    updates.push(context.globalState.update(GS.markerUuid, patch.markerUuid || ""));
  }
  if ("lastError" in patch) {
    updates.push(context.globalState.update(GS.lastError, patch.lastError || ""));
  }
  if ("lastOkFingerprint" in patch) {
    updates.push(context.globalState.update(GS.lastOkFingerprint, patch.lastOkFingerprint || ""));
  }
  await Promise.all(updates);
}

async function mirrorEnabledSetting(enabled) {
  try {
    const cfg = vscode.workspace.getConfiguration("cortana.injection");
    await cfg.update("enabled", Boolean(enabled), vscode.ConfigurationTarget.Global);
  } catch {
    // package.json contribution may land from a sibling agent; ignore mirror failures.
  }
}

function readEnabledSetting() {
  try {
    return Boolean(vscode.workspace.getConfiguration("cortana.injection").get("enabled", false));
  } catch {
    return false;
  }
}

// ---------------------------------------------------------------------------
// CSS + splash
// ---------------------------------------------------------------------------

function resolveBootMs() {
  let bootMs = 1200;
  try {
    bootMs = Number(vscode.workspace.getConfiguration("cortana.injection").get("bootMs", 1200));
  } catch {
    bootMs = 1200;
  }
  if (!Number.isFinite(bootMs) || bootMs < 0) {
    bootMs = 1200;
  }
  if (bootMs > 10000) {
    bootMs = 10000;
  }
  return Math.round(bootMs);
}

async function readCssBundle(context) {
  const warnings = [];
  const parts = [];

  for (const rel of CSS_REL_PATHS) {
    const full = path.join(context.extensionUri.fsPath, rel);
    try {
      const text = await fsp.readFile(full, "utf8");
      parts.push(`/* === ${rel.replace(/\\/g, "/")} === */\n${text}`);
    } catch (err) {
      warnings.push(`missing CSS: ${rel.replace(/\\/g, "/")} (${err.code || err.message})`);
    }
  }

  const bootMs = resolveBootMs();

  // CSP img-src allows 'self' and data:. Stage PNGs as siblings of workbench.html.
  // Bind URL + bootMs via CSS vars only — boot.css composes PNG + progress + particle layers.
  // Hero globe is a separate CC-2 cutout — never alias boot/calibrating splash.
  // Do NOT override background-image here (would wipe multi-layer boot.css stacks).
  parts.push(
    [
      "/* === cortana staged splash + hero globe binding === */",
      `:root {`,
      `  --cortana-boot-splash: url(./${BOOT_STAGED_NAME});`,
      `  --cortana-boot-ms: ${bootMs}ms;`,
      `  --cortana-hero-globe: url(./${HERO_GLOBE_STAGED_NAME});`,
      `}`,
    ].join("\n")
  );

  return { css: parts.join("\n\n"), warnings };
}

async function stageBootSplash(context, workbenchPath) {
  const src = path.join(context.extensionUri.fsPath, BOOT_SOURCE_REL);
  const dest = stagedSplashPath(workbenchPath);
  if (!(await pathExists(src))) {
    return { ok: false, message: `boot splash source missing: ${BOOT_SOURCE_REL}` };
  }
  await copyFileBinary(src, dest);
  return { ok: true, path: dest };
}

async function stageHeroGlobe(context, workbenchPath) {
  const src = path.join(context.extensionUri.fsPath, HERO_GLOBE_SOURCE_REL);
  const dest = stagedHeroGlobePath(workbenchPath);
  if (!(await pathExists(src))) {
    return { ok: false, message: `hero globe source missing: ${HERO_GLOBE_SOURCE_REL}` };
  }
  await copyFileBinary(src, dest);
  return { ok: true, path: dest };
}

async function removeStagedSplash(workbenchPath) {
  if (!workbenchPath) {
    return;
  }
  try {
    await safeUnlink(stagedSplashPath(workbenchPath));
  } catch (err) {
    // Soft: splash delete must not block restore of HTML.
    if (err && (err.code === "EACCES" || err.code === "EPERM")) {
      return formatWriteError(err);
    }
    throw err;
  }
  try {
    await safeUnlink(stagedHeroGlobePath(workbenchPath));
  } catch (err) {
    if (err && (err.code === "EACCES" || err.code === "EPERM")) {
      return formatWriteError(err);
    }
    throw err;
  }
  return null;
}

// ---------------------------------------------------------------------------
// Backup / restore
// ---------------------------------------------------------------------------

/**
 * Never backup an already-patched file (classic Custom CSS poison).
 * Primary: workbench.cortana.<uuid>.bak.html beside workbench.
 * Secondary: globalStorage pristine copy for update-wipe recovery.
 */
async function createPristineBackup(context, workbenchPath, pristineHtml, uuid) {
  const primary = backupBesideWorkbench(workbenchPath, uuid);
  await writeTextFile(primary, pristineHtml);
  try {
    await ensureGlobalStorage(context);
    await writeTextFile(globalBackupFile(context), pristineHtml);
  } catch (err) {
    // Secondary backup is best-effort; primary is required.
    return {
      primary,
      secondaryError: err && err.message ? err.message : String(err),
    };
  }
  return { primary };
}

async function loadBackupHtml(context, workbenchPath, backupUuid) {
  if (backupUuid && workbenchPath) {
    const primary = backupBesideWorkbench(workbenchPath, backupUuid);
    if (await pathExists(primary)) {
      return { html: await fsp.readFile(primary, "utf8"), source: "beside-workbench" };
    }
  }

  // Scan directory for any cortana bak if uuid lost
  if (workbenchPath) {
    try {
      const dir = path.dirname(workbenchPath);
      const names = await fsp.readdir(dir);
      const bak = names.filter((n) => /^workbench\.cortana\..+\.bak\.html$/i.test(n)).sort();
      if (bak.length) {
        const full = path.join(dir, bak[bak.length - 1]);
        return { html: await fsp.readFile(full, "utf8"), source: "beside-workbench-scan" };
      }
    } catch {
      /* ignore */
    }
  }

  const secondary = globalBackupFile(context);
  if (await pathExists(secondary)) {
    return { html: await fsp.readFile(secondary, "utf8"), source: "globalStorage" };
  }

  return null;
}

async function restoreWorkbenchHtml(context, workbenchPath, backupUuid) {
  const current = await fsp.readFile(workbenchPath, "utf8");
  const backup = await loadBackupHtml(context, workbenchPath, backupUuid);

  let restored;
  let method;
  if (backup && backup.html && !isAlreadyPatched(backup.html)) {
    restored = backup.html;
    method = backup.source;
  } else if (isAlreadyPatched(current)) {
    restored = stripPatch(current);
    method = "strip-markers";
  } else {
    restored = current;
    method = "already-pristine";
  }

  if (restored !== current) {
    await writeTextFile(workbenchPath, restored);
  }

  const splashErr = await removeStagedSplash(workbenchPath);
  // Keep product.json checksum aligned so Cursor does not toast "corrupt installation".
  let checksum = null;
  try {
    checksum = await syncWorkbenchChecksum(inferAppRoot(workbenchPath), workbenchPath);
  } catch (err) {
    checksum = { ok: false, message: formatWriteError(err) };
  }
  return { method, splashError: splashErr || null, checksum };
}

async function clearInjectionState(context, reason) {
  await writeState(context, {
    enabled: false,
    active: false,
    lastError: reason || "",
  });
  await mirrorEnabledSetting(false);
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/**
 * reconcileOnActivate — never auto-enable.
 * Auto-disable + restore on Cursor version/commit/vscode.version mismatch
 * or corrupt/missing markers while enabled|active.
 */
async function reconcileOnActivate(context) {
  const loc = await locateWorkbench();
  if (!loc) {
    return {
      status: "unavailable",
      message: "Cursor workbench.html not found under vscode.env.appRoot / execPath probes",
    };
  }

  let html;
  try {
    html = await fsp.readFile(loc.workbenchPath, "utf8");
  } catch (err) {
    return { status: "error", message: `Cannot read workbench.html: ${err.message || err}` };
  }

  const fp = await readProductFingerprint(loc.appRoot);
  const state = await readState(context);
  const currentFp = fingerprintString(fp.version, fp.commit, fp.vscodeVersion);

  if (state.active || state.enabled) {
    // Fail-safe (1): product.json version+commit and vscode.version vs stored fingerprint
    let mismatch = false;
    let mismatchReason = "";
    if (state.lastOkFingerprint) {
      if (state.lastOkFingerprint !== currentFp) {
        mismatch = true;
        mismatchReason = `Cursor updated (${state.lastOkFingerprint} → ${currentFp}) — CORTANA injection disabled. Re-enable after verify.`;
      }
    } else if (state.cursorVersion || state.cursorCommit) {
      if (state.cursorVersion !== fp.version || state.cursorCommit !== fp.commit) {
        mismatch = true;
        mismatchReason = `Cursor updated (${state.cursorVersion}/${state.cursorCommit} → ${fp.version}/${fp.commit}) — CORTANA injection disabled. Re-enable after verify.`;
      }
    }

    if (mismatch) {
      try {
        await restoreWorkbenchHtml(context, loc.workbenchPath, state.backupUuid);
      } catch (err) {
        const msg = formatWriteError(err);
        await writeState(context, { enabled: false, active: false, lastError: msg });
        await mirrorEnabledSetting(false);
        return {
          status: "disabled-due-to-update",
          message: mismatchReason,
          restoreError: msg,
        };
      }
      await clearInjectionState(context, mismatchReason);
      // Fail-safe (1): never auto-re-enable — notify via extension Re-enable button
      return { status: "disabled-due-to-update", message: mismatchReason };
    }

    // Fail-safe (2): corrupt / wrong-uuid / missing style while patch expected on disk
    const expectedUuid = state.markerUuid || undefined;
    if (state.active || isAlreadyPatched(html)) {
      const validity = markersValid(html, expectedUuid);
      if (!validity.ok) {
        const reason = `Patch detection failed: ${validity.reason} — CORTANA injection disabled.`;
        try {
          await restoreWorkbenchHtml(context, loc.workbenchPath, state.backupUuid);
        } catch (err) {
          const msg = formatWriteError(err);
          await writeState(context, { enabled: false, active: false, lastError: msg });
          await mirrorEnabledSetting(false);
          return { status: "health-fail", message: reason, restoreError: msg };
        }
        await clearInjectionState(context, reason);
        return { status: "health-fail", message: reason };
      }

      // CSS sheet probe: HUD/tokens health markers must survive A–C rebuilds
      const styleProbe = probeInjectedCssHealth(html);
      if (!styleProbe.ok) {
        const reason = `Health probe failed: ${styleProbe.reason} — CORTANA injection disabled.`;
        try {
          await restoreWorkbenchHtml(context, loc.workbenchPath, state.backupUuid);
        } catch (err) {
          const msg = formatWriteError(err);
          await writeState(context, { enabled: false, active: false, lastError: msg });
          await mirrorEnabledSetting(false);
          return { status: "health-fail", message: reason, restoreError: msg };
        }
        await clearInjectionState(context, reason);
        return { status: "health-fail", message: reason };
      }
    }

    // enabled but patch missing — never auto-reapply
    if (state.enabled && !parseMarkers(html).hasStart) {
      const reason = "patch missing — re-enable manually";
      try {
        await restoreWorkbenchHtml(context, loc.workbenchPath, state.backupUuid);
      } catch {
        /* already missing */
      }
      await clearInjectionState(context, reason);
      return { status: "health-fail", message: reason };
    }
  }

  if (state.enabled && state.active) {
    // Quiet integrity toast for already-enabled installs (Admin write may soft-fail).
    let checksum = null;
    try {
      checksum = await syncWorkbenchChecksum(loc.appRoot, loc.workbenchPath);
    } catch (err) {
      checksum = { ok: false, message: formatWriteError(err) };
    }
    return {
      status: "ok",
      message: "injection active and healthy",
      checksum,
    };
  }
  if (state.enabled && !state.active) {
    return {
      status: "enabled-inactive",
      message: "enabled in state but not marked active — re-run Enable",
    };
  }
  return { status: "idle", message: "injection not enabled" };
}

async function enable(context) {
  const loc = await locateWorkbench();
  if (!loc) {
    const message = "workbench.html not found — cannot enable injection";
    await writeState(context, { lastError: message });
    return { ok: false, message };
  }

  let html;
  try {
    html = await fsp.readFile(loc.workbenchPath, "utf8");
  } catch (err) {
    const message = `Cannot read workbench.html: ${err.message || err}`;
    await writeState(context, { lastError: message });
    return { ok: false, message };
  }

  const state = await readState(context);
  const fp = await readProductFingerprint(loc.appRoot);

  // Clear any existing patch before backing up (never backup patched HTML).
  if (isAlreadyPatched(html)) {
    try {
      await restoreWorkbenchHtml(context, loc.workbenchPath, state.backupUuid);
      html = await fsp.readFile(loc.workbenchPath, "utf8");
    } catch (err) {
      // Fall back to in-memory strip so we still can proceed if restore write works later
      html = stripPatch(html);
      if (isAlreadyPatched(html)) {
        const message = formatWriteError(err);
        await writeState(context, { lastError: message });
        return { ok: false, message };
      }
    }
  }

  if (isAlreadyPatched(html)) {
    const message = "Refusing to backup an already-patched workbench.html";
    await writeState(context, { lastError: message });
    return { ok: false, message };
  }

  const markerUuid = newUuid();
  const backupUuid = newUuid();

  try {
    await createPristineBackup(context, loc.workbenchPath, html, backupUuid);
  } catch (err) {
    const message = formatWriteError(err);
    await writeState(context, { lastError: message, enabled: false, active: false });
    await mirrorEnabledSetting(false);
    return { ok: false, message };
  }

  // God lock: boot must be real PNG staged beside workbench — not CSS-only fallback.
  const splash = await stageBootSplash(context, loc.workbenchPath).catch((err) => ({
    ok: false,
    message: formatWriteError(err),
  }));
  if (!splash || !splash.ok) {
    const message =
      (splash && splash.message) ||
      "Boot splash PNG staging failed — Enable requires reference-calibrating-splash.png";
    await writeState(context, { lastError: message, enabled: false, active: false });
    await mirrorEnabledSetting(false);
    return { ok: false, message };
  }

  // Decorative hero cutout (CC-2) — soft: never blocks Enable / IDE if missing.
  await stageHeroGlobe(context, loc.workbenchPath).catch(() => null);

  const { css, warnings } = await readCssBundle(context);
  if (!css.trim()) {
    const message = "No CSS available to inject (media/inject/*.css missing)";
    await writeState(context, { lastError: message });
    return { ok: false, message };
  }
  if (!css.includes("CORTANA-HEALTH")) {
    const message =
      "Inject CSS missing CORTANA-HEALTH marker (tokens.css / hud.css) — refusing Enable";
    await writeState(context, { lastError: message });
    return { ok: false, message };
  }

  let hudBundle;
  try {
    hudBundle = await readHudMarkup(context);
  } catch (err) {
    const message = `HUD markup missing (${HUD_MARKUP_REL.replace(/\\/g, "/")}): ${err.code || err.message}`;
    await writeState(context, { lastError: message });
    return { ok: false, message };
  }
  if (!hudBundle.markup || !hudBundle.markup.includes("cortana-cc-hud")) {
    const message = "HUD markup invalid — missing cortana-cc-hud root";
    await writeState(context, { lastError: message });
    return { ok: false, message };
  }

  const block = buildPatchBlock({
    uuid: markerUuid,
    version: fp.version,
    commit: fp.commit,
    css,
  });
  const hudBlock = buildHudBlock({
    uuid: markerUuid,
    markup: hudBundle.markup,
    interactStyle: hudBundle.interactStyle,
    clockScript: hudBundle.clockScript,
    liveScript: hudBundle.liveScript,
    waveScript: hudBundle.waveScript,
    voiceScript: hudBundle.voiceScript,
    wakeScript: hudBundle.wakeScript,
    interactScript: hudBundle.interactScript,
  });

  let patched;
  try {
    patched = insertBeforeHeadClose(html, block);
    patched = insertBeforeBodyClose(patched, hudBlock);
    validateHudPatchPlacement(patched);
  } catch (err) {
    const message = err.message || String(err);
    await writeState(context, { lastError: message });
    return { ok: false, message };
  }

  try {
    await writeTextFile(loc.workbenchPath, patched);
  } catch (err) {
    // Soft-fail: leave disk alone (backup is pristine; do not mark active).
    const message = formatWriteError(err);
    try {
      await removeStagedSplash(loc.workbenchPath);
    } catch {
      /* ignore */
    }
    await writeState(context, {
      enabled: false,
      active: false,
      lastError: message,
      backupUuid,
    });
    await mirrorEnabledSetting(false);
    return { ok: false, message };
  }

  // Suppress Cursor "corrupted installation" toast (product.json workbench checksum).
  const checksum = await syncWorkbenchChecksum(loc.appRoot, loc.workbenchPath).catch((err) => ({
    ok: false,
    message: formatWriteError(err),
  }));

  const warnText = warnings.length ? warnings.join("; ") : "";
  const checksumNote =
    checksum && checksum.ok
      ? checksum.synced
        ? ""
        : ""
      : checksum && checksum.message
        ? ` checksum: ${checksum.message}`
        : " checksum: sync failed";
  const lastError = [warnText, checksumNote].filter(Boolean).join(" | ");

  await writeState(context, {
    enabled: true,
    active: true,
    cursorVersion: fp.version,
    cursorCommit: fp.commit,
    backupUuid,
    markerUuid,
    lastError,
    lastOkFingerprint: fingerprintString(fp.version, fp.commit, fp.vscodeVersion),
  });
  await mirrorEnabledSetting(true);

  return {
    ok: true,
    checksum,
    message: lastError
      ? `Injection enabled with warnings: ${lastError}`
      : "Injection enabled — reload Cursor window to apply. Integrity toast suppressed via product.json checksum sync.",
  };
}

async function disable(context, reason) {
  const loc = await locateWorkbench();
  const state = await readState(context);
  const why = reason || "disabled by user";

  if (!loc) {
    await clearInjectionState(context, why);
    return {
      ok: true,
      message: `State cleared (${why}); workbench.html not found to restore`,
    };
  }

  try {
    const result = await restoreWorkbenchHtml(context, loc.workbenchPath, state.backupUuid);
    await writeState(context, {
      enabled: false,
      active: false,
      lastError: why,
    });
    await mirrorEnabledSetting(false);
    return {
      ok: true,
      message: `Injection disabled (${result.method}): ${why}`,
    };
  } catch (err) {
    const message = formatWriteError(err);
    // Soft-fail: still clear intent so we do not keep claiming active wrongly if disk unknown
    await writeState(context, {
      enabled: false,
      active: false,
      lastError: message,
    });
    await mirrorEnabledSetting(false);
    return { ok: false, message };
  }
}

async function status(context) {
  const state = await readState(context);
  const fp = await getFingerprint();
  const settingEnabled = readEnabledSetting();

  const disk = {
    located: Boolean(fp.workbenchPath),
    patched: false,
    markersValid: false,
    uuid: null,
    stylePresent: false,
    splashStaged: false,
    backupPresent: false,
  };

  if (fp.workbenchPath && (await pathExists(fp.workbenchPath))) {
    try {
      const html = await fsp.readFile(fp.workbenchPath, "utf8");
      const m = parseMarkers(html);
      const v = markersValid(html, state.markerUuid || undefined);
      disk.patched = m.hasStart || m.hasStyle;
      disk.markersValid = v.ok;
      disk.uuid = m.uuid;
      disk.stylePresent = m.hasStyle;
      disk.markerReason = v.reason;
    } catch (err) {
      disk.readError = err.message || String(err);
    }
    disk.splashStaged = await pathExists(stagedSplashPath(fp.workbenchPath));
    if (state.backupUuid) {
      disk.backupPresent = await pathExists(backupBesideWorkbench(fp.workbenchPath, state.backupUuid));
    }
  }

  let globalBackupPresent = false;
  try {
    globalBackupPresent = await pathExists(globalBackupFile(context));
  } catch {
    globalBackupPresent = false;
  }

  return {
    enabled: state.enabled,
    active: state.active,
    settingEnabled,
    cursorVersion: state.cursorVersion,
    cursorCommit: state.cursorCommit,
    backupUuid: state.backupUuid,
    markerUuid: state.markerUuid,
    lastError: state.lastError,
    lastOkFingerprint: state.lastOkFingerprint,
    vscodeVersion: vscode.version || "",
    fingerprint: fp,
    disk,
    globalBackupPresent,
  };
}

async function healthCheck(context) {
  const details = {
    workbench: null,
    fingerprint: null,
    markers: null,
    backup: null,
    splash: null,
    css: [],
    state: null,
    issues: [],
  };

  const loc = await locateWorkbench();
  details.workbench = loc
    ? { path: loc.workbenchPath, appRoot: loc.appRoot }
    : { path: null, appRoot: vscode.env.appRoot || null };

  if (!loc) {
    details.issues.push("workbench.html not located");
    return { ok: false, details };
  }

  const fp = await readProductFingerprint(loc.appRoot);
  details.fingerprint = {
    version: fp.version,
    commit: fp.commit,
    vscodeVersion: fp.vscodeVersion,
    string: fingerprintString(fp.version, fp.commit, fp.vscodeVersion),
  };

  const state = await readState(context);
  details.state = state;

  let html = "";
  try {
    html = await fsp.readFile(loc.workbenchPath, "utf8");
  } catch (err) {
    details.issues.push(`read workbench failed: ${err.message || err}`);
    return { ok: false, details };
  }

  const validity = markersValid(html, state.markerUuid || undefined);
  details.markers = {
    patched: isAlreadyPatched(html),
    ...validity,
  };

  if (state.active && !validity.ok) {
    details.issues.push(`active but markers invalid: ${validity.reason}`);
  }
  if (state.enabled && state.active && !validity.ok) {
    details.issues.push("enabled+active requires healthy markers");
  }

  if (
    (state.active || state.enabled) &&
    state.lastOkFingerprint &&
    state.lastOkFingerprint !== details.fingerprint.string
  ) {
    details.issues.push("fingerprint mismatch vs lastOkFingerprint");
  }

  const primaryBak =
    state.backupUuid && backupBesideWorkbench(loc.workbenchPath, state.backupUuid);
  details.backup = {
    primary: primaryBak || null,
    primaryPresent: primaryBak ? await pathExists(primaryBak) : false,
    globalPresent: await pathExists(globalBackupFile(context)),
  };
  if (state.active && !details.backup.primaryPresent && !details.backup.globalPresent) {
    details.issues.push("no backup available for restore");
  }

  const splashPath = stagedSplashPath(loc.workbenchPath);
  details.splash = {
    path: splashPath,
    present: await pathExists(splashPath),
    sourcePresent: await pathExists(path.join(context.extensionUri.fsPath, BOOT_SOURCE_REL)),
  };
  if (state.active && !details.splash.present) {
    details.issues.push("active but cortana-boot-splash.png not staged beside workbench");
  }
  if (state.active && !details.splash.sourcePresent) {
    details.issues.push("boot source PNG missing (reference-calibrating-splash.png)");
  }

  details.warnings = details.warnings || [];

  for (const rel of CSS_REL_PATHS) {
    const full = path.join(context.extensionUri.fsPath, rel);
    const present = await pathExists(full);
    details.css.push({ path: rel.replace(/\\/g, "/"), present });
    if (!present) {
      details.issues.push(`CSS missing: ${rel.replace(/\\/g, "/")}`);
    }
  }

  const hudMarkupFull = path.join(context.extensionUri.fsPath, HUD_MARKUP_REL);
  details.hudMarkup = {
    path: HUD_MARKUP_REL.replace(/\\/g, "/"),
    present: await pathExists(hudMarkupFull),
    injected: Boolean(parseMarkers(html).hasHudRoot),
  };
  if (!details.hudMarkup.present) {
    details.issues.push(`HUD markup missing: ${details.hudMarkup.path}`);
  }
  if (state.active && !details.hudMarkup.injected) {
    details.issues.push("active but cortana-cc-hud not present in workbench.html");
  }

  // Content probe against live workbench style + on-disk sheets
  const styleProbe = probeInjectedCssHealth(html);
  details.cssHealth = styleProbe;
  if (state.active && isAlreadyPatched(html) && !styleProbe.ok) {
    details.issues.push(`injected CSS health: ${styleProbe.reason}`);
  }
  for (const rel of CSS_REL_PATHS) {
    const full = path.join(context.extensionUri.fsPath, rel);
    if (!(await pathExists(full))) {
      continue;
    }
    try {
      const text = await fsp.readFile(full, "utf8");
      const hasHealth = text.includes("CORTANA-HEALTH");
      details.css.push({
        path: `${rel.replace(/\\/g, "/")}:health`,
        present: hasHealth,
      });
      if (!hasHealth) {
        // boot.css is owned by Worker A and may briefly lack the comment while polishing;
        // tokens/hud + injected-bundle probe remain the hard fail-safe (2) needles.
        const msg = `CSS health marker missing in ${rel.replace(/\\/g, "/")}`;
        if (rel.includes("boot.css")) {
          details.warnings.push(msg);
        } else {
          details.issues.push(msg);
        }
      }
    } catch {
      /* ignore read */
    }
  }

  // Integrity checksum vs product.json (corrupt-installation toast source)
  try {
    const productPath = productJsonPath(loc.appRoot);
    const buf = await fsp.readFile(loc.workbenchPath);
    const digest = computeWorkbenchChecksum(buf);
    let stored = null;
    let key = WORKBENCH_CHECKSUM_KEY;
    if (await pathExists(productPath)) {
      const product = JSON.parse(await fsp.readFile(productPath, "utf8"));
      if (product.checksums && typeof product.checksums === "object") {
        if (!(key in product.checksums)) {
          const alt = Object.keys(product.checksums).find(
            (k) => /workbench\.html$/i.test(k) && /electron-sandbox/i.test(k)
          );
          if (alt) {
            key = alt;
          }
        }
        stored = product.checksums[key] || null;
      }
    }
    details.checksum = {
      key,
      digest,
      stored,
      matches: Boolean(stored && stored === digest),
    };
    if (state.active && stored && stored !== digest) {
      details.warnings.push(
        "product.json workbench checksum mismatch — Enable/Reload as Admin syncs it (suppresses corrupt toast)"
      );
    }
  } catch (err) {
    details.checksum = { error: err && err.message ? err.message : String(err) };
  }

  // Writable probe (non-destructive): access W_OK
  // Non-Admin after a successful Enable is expected — warn only; do not fail health
  // (periodic probe must not tear down a healthy patch just because ACL is read-only).
  try {
    await fsp.access(loc.workbenchPath, fs.constants.W_OK);
    details.writable = true;
  } catch {
    details.writable = false;
    if (state.enabled || state.active) {
      details.warnings.push(
        "workbench.html not writable (Admin ACL required for Enable/Disable writes)"
      );
    }
  }

  const ok = details.issues.length === 0;
  return { ok, details };
}

module.exports = {
  reconcileOnActivate,
  enable,
  disable,
  status,
  healthCheck,
  getFingerprint,
  syncWorkbenchChecksum,
};
