"use strict";

const vscode = require("vscode");
const { getSuit, setSuit } = require("./suitModes");
const { getState, patchState } = require("./sessionCinema");

const KEY = "CORTANA.presets";

/** @param {import("vscode").ExtensionContext} context */
function listPresets(context) {
  return context.globalState.get(KEY, []);
}

/** @param {import("vscode").ExtensionContext} context */
async function savePreset(context, name) {
  if (!name) {
    name = await vscode.window.showInputBox({
      title: "Save Workspace Preset",
      prompt: "Preset name",
      value: "Mission Profile",
    });
  }
  if (!name) return null;
  const suit = getSuit(context);
  const session = getState(context);
  const presets = listPresets(context).filter((p) => p.name !== name);
  const entry = {
    name,
    suitId: suit.id,
    focusFortress: !!session.focusFortress,
    streamPack: !!session.streamPack,
    watermark: !!session.watermark,
    friday: !!session.friday,
    cinema: !!session.cinema,
    glow: session.glow ?? 1,
    savedAt: Date.now(),
  };
  presets.unshift(entry);
  await context.globalState.update(KEY, presets.slice(0, 20));
  return entry;
}

/** @param {import("vscode").ExtensionContext} context */
async function applyPreset(context, name) {
  let presets = listPresets(context);
  let target = name ? presets.find((p) => p.name === name) : null;
  if (!target) {
    const pick = await vscode.window.showQuickPick(
      presets.map((p) => ({ label: p.name, description: p.suitId, p })),
      { title: "Apply Workspace Preset" }
    );
    if (!pick) return null;
    target = pick.p;
  }
  await setSuit(context, target.suitId);
  await patchState(context, {
    focusFortress: !!target.focusFortress,
    streamPack: !!target.streamPack,
    watermark: !!target.watermark,
    friday: !!target.friday,
    cinema: !!target.cinema,
    glow: target.glow ?? 1,
  });
  return target;
}

module.exports = { listPresets, savePreset, applyPreset };
