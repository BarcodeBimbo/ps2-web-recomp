"use strict";

const KEY = "CORTANA.sessionState";

/**
 * @param {import("vscode").ExtensionContext} context
 */
function getState(context) {
  return (
    context.workspaceState.get(KEY) || {
      cinema: false,
      focusFortress: false,
      streamPack: false,
      watermark: false,
      friday: false,
      sound: true,
      tts: true,
      glow: 1,
      keystrokes: 0,
      sessionStarted: Date.now(),
    }
  );
}

/**
 * @param {import("vscode").ExtensionContext} context
 * @param {Record<string, unknown>} patch
 */
async function patchState(context, patch) {
  const next = { ...getState(context), ...patch };
  await context.workspaceState.update(KEY, next);
  return next;
}

/**
 * @param {import("vscode").ExtensionContext} context
 */
async function toggle(context, key) {
  const cur = getState(context);
  return patchState(context, { [key]: !cur[key] });
}

/**
 * @param {import("vscode").ExtensionContext} context
 */
function bumpKeystroke(context) {
  const cur = getState(context);
  const keystrokes = (cur.keystrokes || 0) + 1;
  // fire-and-forget
  context.workspaceState.update(KEY, { ...cur, keystrokes });
  return keystrokes;
}

function sessionMinutes(state) {
  const started = state.sessionStarted || Date.now();
  return Math.max(0, Math.floor((Date.now() - started) / 60000));
}

module.exports = { getState, patchState, toggle, bumpKeystroke, sessionMinutes };
