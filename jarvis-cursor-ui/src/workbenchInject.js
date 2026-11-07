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
const vscode = require("vscode");

const MARKER_START = "CORTANA-INJECT-START";
const MARKER_END = "CORTANA-INJECT-END";
const MARKER_HUD_START = "CORTANA-HUD-START";
const MARKER_HUD_END = "CORTANA-HUD-END";
const STYLE_ID = "cortana-workbench-css";
const BOOT_STAGED_NAME = "cortana-boot-splash.png";
/** Authoritative boot still: calibrating splash (CSS-drawn cover; PNG staged for binding). */
const BOOT_SOURCE_REL = path.join("media", "reference-calibrating-splash.png");
const HUD_MARKUP_REL = path.join("media", "inject", "hud-markup.html");
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
    .replace(/<script[^>]*id=["']cortana-hud-voice-script["'][\s\S]*?<\/script>\s*/gi, "")
    .replace(/<script[^>]*id=["']cortana-hud-wake-script["'][\s\S]*?<\/script>\s*/gi, "")
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

async function readHudMarkup(context) {
  const full = path.join(context.extensionUri.fsPath, HUD_MARKUP_REL);
  let markup = await fsp.readFile(full, "utf8");
  const { date, clock } = formatHudClock();
  markup = markup
    .replace(/>Monday, 15 June 2026</, `>${date}<`)
    .replace(/>11:18:21 am</i, `>${clock}<`);
  const clockScript = [
    `<script id="cortana-hud-clock-script">`,
    `(function(){function t(){var d=new Date(),c=document.getElementById("cortana-hud-clock"),a=document.getElementById("cortana-hud-date");`,
    `if(c)c.textContent=d.toLocaleTimeString(undefined,{hour:"numeric",minute:"2-digit",second:"2-digit",hour12:true});`,
    `if(a)a.textContent=d.toLocaleDateString(undefined,{weekday:"long",year:"numeric",month:"long",day:"numeric"});}`,
    `t();setInterval(t,1000);}());`,
    `</script>`,
  ].join("");
  const voiceScript = buildHudVoiceScript();
  const wakeScript = buildHudWakeScript();
  return { markup, clockScript, voiceScript, wakeScript };
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
    "function tryVoiceDom(){return !!clickFirst(VOICE_SELS);}",
    "function tryOpenChatDom(){return !!clickFirst(CHAT_SELS);}",
    "function revealIde(){",
    "var cb=document.getElementById('cortana-focus-toggle');",
    "if(cb&&!cb.checked){cb.checked=true;try{cb.dispatchEvent(new Event('change',{bubbles:true}));}catch(e){}return true;}",
    "return false;",
    "}",
    "function startVoice(){",
    "signal();",
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
    "return el.closest('[data-cortana-action=\"voice\"],[data-cortana-voice],#cortana-mic-btn,.jcc-mic,.jcc-voice,#cortana-talk-cta,.jcc-talk');",
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
    "var s=statusEl(),box=voiceBox(),ov=ovVoice();",
    "if(s)s.textContent=text;",
    "if(box){box.classList.remove('is-listening','is-offline','is-responding');",
    "if(mode)box.classList.add(mode);}",
    "if(ov){if(mode==='is-offline'){ov.textContent='Offline';ov.setAttribute('data-tone','');}",
    "else if(mode==='is-listening'||mode==='is-responding'){ov.textContent='Online';ov.setAttribute('data-tone','ok');}",
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
    "try{stream.getTracks().forEach(function(t){t.stop();});}catch(e){}",
    "startRec();",
    "}).catch(function(){setStatus('Offline','is-offline');});",
    "}else{startRec();}",
    "}",
    "function onFocusChange(){",
    "if(wakeAllowed()){want=true;arm();}",
    "else{want=false;stopRec();setStatus('Standby','');}",
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


function buildHudBlock({ uuid, markup, clockScript, voiceScript, wakeScript }) {
  return [
    `<!-- ${MARKER_HUD_START} uuid=${uuid} -->`,
    markup.trim(),
    clockScript,
    voiceScript || "",
    wakeScript || "",
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

  // CSP img-src allows 'self' and data:. Stage PNG as sibling of workbench.html.
  // Bind URL + bootMs via CSS vars only — boot.css composes PNG + progress + particle layers.
  // Do NOT override background-image here (would wipe multi-layer boot.css stacks).
  parts.push(
    [
      "/* === cortana staged splash binding === */",
      `:root {`,
      `  --cortana-boot-splash: url(./${BOOT_STAGED_NAME});`,
      `  --cortana-boot-ms: ${bootMs}ms;`,
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
    clockScript: hudBundle.clockScript,
    voiceScript: hudBundle.voiceScript,
    wakeScript: hudBundle.wakeScript,
  });

  let patched;
  try {
    patched = insertBeforeHeadClose(html, block);
    patched = insertBeforeBodyClose(patched, hudBlock);
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
