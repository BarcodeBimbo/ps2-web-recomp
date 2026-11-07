"use strict";

const vscode = require("vscode");
const { FileMapProvider } = require("./fileMapProvider");
const { CommandCenterViewProvider } = require("./commandCenterView");
const { getSuit, setSuit, pickSuit } = require("./suitModes");
const { toggle, bumpKeystroke, getState } = require("./sessionCinema");
const { savePreset, applyPreset } = require("./workspacePresets");
const voice = require("./voiceBridge");

/** Soft-load inject engine (siblings may still be writing workbenchInject.js). */
let inject;
try {
  inject = require("./workbenchInject");
} catch (err) {
  console.warn("[jarvis] workbenchInject not loaded yet:", err && err.message ? err.message : err);
  inject = {
    async reconcileOnActivate() {
      return { status: "unavailable", message: "workbenchInject.js missing — injection engine not built yet." };
    },
    async enable() {
      return { ok: false, message: "workbenchInject.js missing — cannot enable injection." };
    },
    async disable() {
      return { ok: false, message: "workbenchInject.js missing — cannot disable injection." };
    },
    async status() {
      return { available: false, reason: "workbenchInject.js missing" };
    },
    async healthCheck() {
      return { ok: false, details: "workbenchInject.js missing" };
    },
    async getFingerprint() {
      return { version: null, commit: null, appRoot: null, workbenchPath: null };
    },
  };
}

function injectionCfg() {
  return vscode.workspace.getConfiguration("jarvis.injection");
}

/** Injection is primary HUD when enabled and fallback webview is off. */
function injectionIsPrimary() {
  const cfg = injectionCfg();
  return cfg.get("enabled") === true && cfg.get("fallbackWebview") !== true;
}

function isAccessError(err, message) {
  const code = err && (err.code || err.errno);
  const text = String(message || (err && err.message) || err || "");
  return code === "EACCES" || /EACCES|access denied|permission denied/i.test(text);
}

async function suggestReload(prefix) {
  const pick = await vscode.window.showInformationMessage(
    `${prefix} Reload Window to apply workbench changes.`,
    "Reload Window"
  );
  if (pick === "Reload Window") {
    await vscode.commands.executeCommand("workbench.action.reloadWindow");
  }
}

/** @param {vscode.ExtensionContext} context */
async function activate(context) {
  const fileMap = new FileMapProvider(context);
  const commandCenter = new CommandCenterViewProvider(context, fileMap);

  context.subscriptions.push(
    vscode.window.registerWebviewViewProvider("jarvis.commandCenter", commandCenter, {
      webviewOptions: { retainContextWhenHidden: true },
    }),
    vscode.window.registerWebviewViewProvider("jarvis.fileMap", fileMap, {
      webviewOptions: { retainContextWhenHidden: true },
    }),
    vscode.commands.registerCommand("jarvis.fileMap.refresh", () => {
      fileMap.refresh();
      commandCenter.refresh();
    }),
    vscode.commands.registerCommand("jarvis.fileMap.focus", async () => {
      await vscode.commands.executeCommand("workbench.view.extension.jarvisCommand");
      if (typeof fileMap.reveal === "function") fileMap.reveal();
    }),
    vscode.commands.registerCommand("jarvis.commandCenter.focus", async () => {
      // When injection is primary, do not force-focus webview as the HUD surface
      if (injectionIsPrimary()) {
        vscode.window.showInformationMessage(
          "Workbench injection is primary HUD. Command Center webview is optional fallback (set jarvis.injection.fallbackWebview)."
        );
        return;
      }
      await vscode.commands.executeCommand("workbench.view.extension.jarvisCommand");
      if (typeof commandCenter.reveal === "function") commandCenter.reveal();
    }),
    vscode.commands.registerCommand("jarvis.theme.applyHints", async () => {
      const suit = getSuit(context);
      const cfg = vscode.workspace.getConfiguration();
      await cfg.update("workbench.colorTheme", suit.theme, vscode.ConfigurationTarget.Global);
      await cfg.update("workbench.sideBar.location", "left", vscode.ConfigurationTarget.Global);
      if (injectionIsPrimary()) {
        vscode.window.showInformationMessage(
          `${suit.theme} applied. Injection is primary HUD — File Map webview remains available.`
        );
      } else {
        vscode.window.showInformationMessage(
          `${suit.theme} applied. Open Command Center for JARVIS HUD + File Map.`
        );
      }
      commandCenter.refresh();
    }),
    vscode.commands.registerCommand("jarvis.suit.pick", async () => {
      await pickSuit(context);
      commandCenter.refresh();
    }),
    vscode.commands.registerCommand("jarvis.suit.set", async (id) => {
      await setSuit(context, id || "mark1");
      commandCenter.refresh();
    }),
    vscode.commands.registerCommand("jarvis.voice.talk", () => voice.startVoice()),
    vscode.commands.registerCommand("jarvis.voice.chat", () => voice.openChat()),
    vscode.commands.registerCommand("jarvis.toggle.focusFortress", async () => {
      await toggle(context, "focusFortress");
      commandCenter.refresh();
    }),
    vscode.commands.registerCommand("jarvis.toggle.cinema", async () => {
      await toggle(context, "cinema");
      commandCenter.refresh();
    }),
    vscode.commands.registerCommand("jarvis.toggle.streamPack", async () => {
      await toggle(context, "streamPack");
      commandCenter.refresh();
    }),
    vscode.commands.registerCommand("jarvis.toggle.friday", async () => {
      await toggle(context, "friday");
      commandCenter.refresh();
    }),
    vscode.commands.registerCommand("jarvis.preset.save", async () => {
      await savePreset(context);
      commandCenter.refresh();
    }),
    vscode.commands.registerCommand("jarvis.preset.apply", async () => {
      await applyPreset(context);
      commandCenter.refresh();
    }),
    vscode.commands.registerCommand("jarvis.hud.refresh", () => commandCenter.refresh()),

    // Phase 6 injection commands (registered before reconcile so Re-enable button works)
    vscode.commands.registerCommand("jarvis.injection.enable", async () => {
      try {
        const result = await inject.enable(context);
        if (result && result.ok) {
          await suggestReload(
            result.message || "Workbench injection enabled."
          );
        } else {
          const msg = (result && result.message) || "Failed to enable workbench injection.";
          const adminNote = isAccessError(null, msg)
            ? " Run Cursor / terminal as Admin once to write under Program Files."
            : "";
          vscode.window.showErrorMessage(msg + adminNote);
        }
      } catch (err) {
        const msg = err && err.message ? err.message : String(err);
        const adminNote = isAccessError(err, msg)
          ? " Run Cursor / terminal as Admin once to write under Program Files."
          : "";
        vscode.window.showErrorMessage(`Enable injection failed: ${msg}${adminNote}`);
      }
    }),
    vscode.commands.registerCommand("jarvis.injection.disable", async () => {
      try {
        const result = await inject.disable(context);
        if (result && result.ok) {
          await suggestReload(
            result.message || "Workbench injection disabled."
          );
        } else {
          vscode.window.showErrorMessage(
            (result && result.message) || "Failed to disable workbench injection."
          );
        }
      } catch (err) {
        vscode.window.showErrorMessage(
          `Disable injection failed: ${err && err.message ? err.message : err}`
        );
      }
    }),
    vscode.commands.registerCommand("jarvis.injection.reenableAfterUpdate", async () => {
      // Explicit God intent: re-patch after Cursor update / health fail
      try {
        const result = await inject.enable(context);
        if (result && result.ok) {
          await suggestReload(
            result.message || "Injection re-enabled after verify."
          );
        } else {
          const msg =
            (result && result.message) || "Failed to re-enable workbench injection.";
          const adminNote = isAccessError(null, msg)
            ? " Run as Admin once if Program Files write was denied."
            : "";
          vscode.window.showErrorMessage(msg + adminNote);
        }
      } catch (err) {
        const msg = err && err.message ? err.message : String(err);
        const adminNote = isAccessError(err, msg)
          ? " Run as Admin once if Program Files write was denied."
          : "";
        vscode.window.showErrorMessage(`Re-enable injection failed: ${msg}${adminNote}`);
      }
    }),
    vscode.commands.registerCommand("jarvis.injection.healthCheck", async () => {
      try {
        const result = await inject.healthCheck(context);
        const details =
          result && result.details != null
            ? typeof result.details === "string"
              ? result.details
              : JSON.stringify(result.details, null, 2)
            : "";
        if (result && result.ok) {
          vscode.window.showInformationMessage(
            details ? `Injection health OK. ${details}` : "Injection health OK."
          );
        } else {
          vscode.window.showWarningMessage(
            details ? `Injection health FAIL. ${details}` : "Injection health FAIL."
          );
        }
      } catch (err) {
        vscode.window.showErrorMessage(
          `Health check failed: ${err && err.message ? err.message : err}`
        );
      }
    }),
    vscode.commands.registerCommand("jarvis.injection.status", async () => {
      try {
        const status = await inject.status(context);
        const summary =
          status == null
            ? "(no status)"
            : typeof status === "string"
              ? status
              : JSON.stringify(status, null, 2);
        const items = [
          { label: "$(info) Injection status", detail: summary.slice(0, 200) },
          { label: "Copy full JSON", description: "clipboard" },
        ];
        const pick = await vscode.window.showQuickPick(items, {
          placeHolder: "JARVIS injection status",
          matchOnDetail: true,
        });
        if (pick && pick.description === "clipboard") {
          await vscode.env.clipboard.writeText(summary);
          vscode.window.showInformationMessage("Injection status copied to clipboard.");
        } else if (status != null) {
          vscode.window.showInformationMessage(
            summary.length > 280 ? summary.slice(0, 277) + "…" : summary
          );
        }
      } catch (err) {
        vscode.window.showErrorMessage(
          `Status failed: ${err && err.message ? err.message : err}`
        );
      }
    })
  );

  // Phase 6: reconcile after providers + commands (Re-enable button → executeCommand)
  try {
    const reconciled = await inject.reconcileOnActivate(context);
    if (
      reconciled &&
      (reconciled.status === "disabled-due-to-update" ||
        reconciled.status === "health-fail")
    ) {
      const msg =
        reconciled.message ||
        `Workbench injection ${reconciled.status}. Verify Cursor install, then re-enable.`;
      const pick = await vscode.window.showWarningMessage(msg, "Re-enable after verify");
      if (pick === "Re-enable after verify") {
        await vscode.commands.executeCommand("jarvis.injection.reenableAfterUpdate");
      }
    }
  } catch (err) {
    console.warn("[jarvis] reconcileOnActivate failed:", err);
  }

  if (injectionIsPrimary()) {
    console.info(
      "[jarvis] Injection is primary HUD; Command Center webview registered as optional fallback only."
    );
  }

  const watcher = vscode.workspace.createFileSystemWatcher("**/*");
  const bounce = debounce(() => {
    fileMap.refresh();
    commandCenter.refresh();
  }, 800);
  watcher.onDidCreate(bounce);
  watcher.onDidDelete(bounce);
  watcher.onDidChange(bounce);
  context.subscriptions.push(watcher);

  context.subscriptions.push(
    vscode.languages.onDidChangeDiagnostics(() => commandCenter.refresh())
  );

  context.subscriptions.push(
    vscode.workspace.onDidChangeTextDocument(() => {
      bumpKeystroke(context);
      const st = getState(context);
      commandCenter.post({
        type: "energy",
        keystrokes: st.keystrokes,
      });
    })
  );

  // Periodic GitHUD / threat soft refresh (no splash remount)
  const gitTimer = setInterval(() => commandCenter.refresh({ full: false }), 15000);
  context.subscriptions.push({ dispose: () => clearInterval(gitTimer) });
}

function debounce(fn, ms) {
  let t;
  return () => {
    clearTimeout(t);
    t = setTimeout(fn, ms);
  };
}

function deactivate() {}

module.exports = { activate, deactivate };
