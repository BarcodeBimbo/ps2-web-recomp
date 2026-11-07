"use strict";

/**
 * Elevated Admin Enable for Cortana Workstation — full Rank-1 inject via workbenchInject.enable()
 * with a minimal vscode stub (no Cursor session required).
 *
 * Usage (elevated):
 *   node scripts/admin-enable-elevated.js [--ext <path>]
 */

const fs = require("fs");
const path = require("path");
const Module = require("module");
const os = require("os");

const EXT_DIR = path.join(process.env.USERPROFILE || "", ".cursor", "extensions");
const SOURCE_FALLBACK = path.join("C:", "PS2Recomp", "cortana-cursor-ui");
const APP_ROOT = path.join("C:", "Program Files", "cursor", "resources", "app");

function argValue(flag) {
  const i = process.argv.indexOf(flag);
  if (i >= 0 && process.argv[i + 1]) return path.resolve(process.argv[i + 1]);
  return null;
}

/** Prefer newest installed ps2recomp-local.cortana-cursor-ui-* (semver folder suffix). */
function findLatestInstall() {
  if (!fs.existsSync(EXT_DIR)) return null;
  const prefix = "ps2recomp-local.cortana-cursor-ui-";
  const hits = fs
    .readdirSync(EXT_DIR, { withFileTypes: true })
    .filter((d) => d.isDirectory() && d.name.startsWith(prefix))
    .map((d) => {
      const ver = d.name.slice(prefix.length);
      const parts = ver.split(".").map((n) => parseInt(n, 10) || 0);
      return { name: d.name, ver, parts, full: path.join(EXT_DIR, d.name) };
    })
    .filter((h) => fs.existsSync(path.join(h.full, "package.json")));
  hits.sort((a, b) => {
    for (let i = 0; i < 3; i++) {
      const d = (b.parts[i] || 0) - (a.parts[i] || 0);
      if (d) return d;
    }
    return 0;
  });
  return hits[0] ? hits[0].full : null;
}

function resolveExt() {
  const fromArg = argValue("--ext");
  if (fromArg && fs.existsSync(path.join(fromArg, "package.json"))) return fromArg;
  const latest = findLatestInstall();
  if (latest) return latest;
  if (fs.existsSync(path.join(SOURCE_FALLBACK, "package.json"))) return SOURCE_FALLBACK;
  throw new Error("Extension root not found (tried newest cortana-cursor-ui install + source junction)");
}

const extRoot = resolveExt();
const pkg = JSON.parse(fs.readFileSync(path.join(extRoot, "package.json"), "utf8"));
const extId = `${pkg.publisher}.${pkg.name}`;
const globalStorage = path.join(
  process.env.APPDATA || "",
  "Cursor",
  "User",
  "globalStorage",
  extId
);
fs.mkdirSync(globalStorage, { recursive: true });

const memory = new Map();
const vscodeStub = {
  version: "1.99.0",
  env: {
    appRoot: APP_ROOT,
    machineId: "cortana-admin-enable",
    sessionId: "cortana-admin-enable",
  },
  Uri: {
    file(p) {
      return { fsPath: p, scheme: "file", toString: () => `file://${p}` };
    },
  },
  ConfigurationTarget: { Global: 1 },
  DiagnosticSeverity: { Error: 0, Warning: 1, Information: 2, Hint: 3 },
  workspace: {
    workspaceFolders: [
      {
        uri: { fsPath: "C:\\PS2Recomp", scheme: "file" },
        name: "PS2Recomp",
        index: 0,
      },
    ],
    getConfiguration() {
      return {
        get(key, def) {
          if (key === "enabled") return false;
          if (key === "bootMs") return 1200;
          return def;
        },
        async update() {
          return undefined;
        },
      };
    },
  },
  languages: {
    getDiagnostics() {
      return [];
    },
  },
  extensions: {
    getExtension(id) {
      if (id === extId) {
        return { id: extId, packageJSON: pkg };
      }
      return undefined;
    },
  },
};

const origLoad = Module._load;
Module._load = function (request, parent, isMain) {
  if (request === "vscode") return vscodeStub;
  return origLoad.apply(this, arguments);
};

const inject = require(path.join(extRoot, "src", "workbenchInject.js"));

const context = {
  extension: { id: extId, packageJSON: pkg },
  extensionUri: { fsPath: extRoot },
  globalStorageUri: { fsPath: globalStorage },
  globalState: {
    get(key, def) {
      return memory.has(key) ? memory.get(key) : def;
    },
    async update(key, val) {
      memory.set(key, val);
    },
  },
};

(async () => {
  const report = {
    ok: false,
    displayName: pkg.displayName,
    version: pkg.version,
    extRoot,
    host: os.hostname(),
    user: os.userInfo().username,
  };
  try {
    const result = await inject.enable(context);
    report.enable = result;
    report.ok = Boolean(result && result.ok);
    const wb = path.join(
      APP_ROOT,
      "out",
      "vs",
      "code",
      "electron-sandbox",
      "workbench",
      "workbench.html"
    );
    if (fs.existsSync(wb)) {
      const html = fs.readFileSync(wb, "utf8");
      report.hasCssMarker = html.includes("CORTANA-INJECT-START");
      report.hasHud = html.includes("cortana-cc-hud") && html.includes("CORTANA-HUD-START");
      const wakeJs = path.join(path.dirname(wb), "cortana-hud-wake.js");
      const wakeSrc = fs.existsSync(wakeJs) ? fs.readFileSync(wakeJs, "utf8") : "";
      report.hasWake =
        html.includes("cortana-hud-wake.js") &&
        /hey\s*cortana|webkitSpeechRecognition|SpeechRecognition/i.test(wakeSrc || html);
      report.hasManhattan = html.includes("Manhattan");
      report.wbBytes = Buffer.byteLength(html, "utf8");
      report.stagedWakeJs = fs.existsSync(wakeJs);
    }
    console.log(JSON.stringify(report, null, 2));
    process.exit(report.ok ? 0 : 1);
  } catch (err) {
    report.error = err && err.stack ? err.stack : String(err);
    console.log(JSON.stringify(report, null, 2));
    process.exit(1);
  }
})();
