"use strict";

/**
 * Static wiring check for injection fail-safes (Worker D).
 * Run: node scripts/verify-fail-safes.js
 */

const path = require("path");
const fs = require("fs");

const root = path.join(__dirname, "..");
const wi = fs.readFileSync(path.join(root, "src/workbenchInject.js"), "utf8");
const ext = fs.readFileSync(path.join(root, "src/extension.js"), "utf8");
const pkg = JSON.parse(fs.readFileSync(path.join(root, "package.json"), "utf8"));

const checks = [];
function assert(name, cond) {
  checks.push({ name, ok: Boolean(cond) });
}

assert("enable export", /async function enable\(/.test(wi));
assert("disable export", /async function disable\(/.test(wi));
assert("healthCheck export", /async function healthCheck\(/.test(wi));
assert("status export", /async function status\(/.test(wi));
assert("reconcile export", /async function reconcileOnActivate\(/.test(wi));
assert("fingerprint lastOk", /lastOkFingerprint/.test(wi));
assert("probeInjectedCssHealth", /function probeInjectedCssHealth\(/.test(wi));
assert("disabled-due-to-update", /disabled-due-to-update/.test(wi));
assert("health-fail status", /status: "health-fail"/.test(wi));
assert("never auto-reapply", /never auto-reapply/.test(wi));
assert("splash PNG required on enable", /Boot splash PNG staging failed/.test(wi));
assert(
  "cmd enable",
  pkg.contributes.commands.some((c) => c.command === "CORTANA.injection.enable")
);
assert(
  "cmd disable",
  pkg.contributes.commands.some((c) => c.command === "CORTANA.injection.disable")
);
assert(
  "cmd reenable",
  pkg.contributes.commands.some((c) => c.command === "CORTANA.injection.reenableAfterUpdate")
);
assert(
  "cmd health",
  pkg.contributes.commands.some((c) => c.command === "CORTANA.injection.healthCheck")
);
assert(
  "cmd status",
  pkg.contributes.commands.some((c) => c.command === "CORTANA.injection.status")
);
assert(
  "ext reconcile notify",
  /disabled-due-to-update/.test(ext) &&
    /health-fail/.test(ext) &&
    /reenableAfterUpdate/.test(ext)
);
assert("ext soft reprobe", /60000/.test(ext) && /Periodic health-fail/.test(ext));
assert(
  "css tokens health",
  fs.readFileSync(path.join(root, "media/inject/tokens.css"), "utf8").includes("CORTANA-HEALTH")
);
assert(
  "css boot health",
  fs.readFileSync(path.join(root, "media/inject/boot.css"), "utf8").includes("CORTANA-HEALTH")
);
assert(
  "css hud health",
  fs.readFileSync(path.join(root, "media/inject/hud.css"), "utf8").includes("CORTANA-HEALTH")
);
assert(
  "splash png exists",
  fs.existsSync(path.join(root, "media/reference-command-center-2.png"))
);
assert(
  "calibrating png retained",
  fs.existsSync(path.join(root, "media/reference-calibrating-splash.png"))
);
assert(
  "boot source is CC-2",
  /reference-command-center-2\.png/.test(wi)
);
assert(
  "cc2 png exists",
  fs.existsSync(path.join(root, "media/reference-command-center-2.png"))
);
assert(
  "cc png exists",
  fs.existsSync(path.join(root, "media/reference-command-center.png"))
);

const fail = checks.filter((c) => !c.ok);
console.log(
  JSON.stringify(
    {
      pass: checks.length - fail.length,
      fail: fail.length,
      failed: fail.map((f) => f.name),
      checks,
    },
    null,
    2
  )
);
process.exit(fail.length ? 1 : 0);
