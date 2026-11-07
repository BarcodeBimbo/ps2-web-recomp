"use strict";

const vscode = require("vscode");

/** @typedef {"mark1"|"mark50"|"endgame"|"stealth"} SuitId */

const SUITS = [
  {
    id: "mark1",
    label: "Mark I",
    theme: "JARVIS Mark I",
    accent: "#00d9ff",
    accent2: "#4d9fff",
    bg: "#050d1a",
  },
  {
    id: "mark50",
    label: "Mark 50",
    theme: "JARVIS Mark 50",
    accent: "#7af0ff",
    accent2: "#e8f7ff",
    bg: "#040c18",
  },
  {
    id: "endgame",
    label: "Endgame",
    theme: "JARVIS Endgame",
    accent: "#ffb020",
    accent2: "#ff4d4d",
    bg: "#120808",
  },
  {
    id: "stealth",
    label: "Stealth",
    theme: "JARVIS Stealth",
    accent: "#6a9a8a",
    accent2: "#9ab8a8",
    bg: "#060a0a",
  },
];

const KEY = "jarvis.suitMode";

function list() {
  return SUITS;
}

/** @param {vscode.ExtensionContext} context */
function getSuit(context) {
  const id = context.globalState.get(KEY, "mark1");
  return SUITS.find((s) => s.id === id) || SUITS[0];
}

/** @param {vscode.ExtensionContext} context @param {SuitId|string} id */
async function setSuit(context, id) {
  const suit = SUITS.find((s) => s.id === id) || SUITS[0];
  await context.globalState.update(KEY, suit.id);
  const cfg = vscode.workspace.getConfiguration();
  await cfg.update("workbench.colorTheme", suit.theme, vscode.ConfigurationTarget.Global);
  return suit;
}

/** @param {vscode.ExtensionContext} context */
async function pickSuit(context) {
  const pick = await vscode.window.showQuickPick(
    SUITS.map((s) => ({ label: s.label, description: s.theme, id: s.id })),
    { title: "JARVIS Suit Mode" }
  );
  if (!pick) return getSuit(context);
  return setSuit(context, pick.id);
}

module.exports = { SUITS, list, getSuit, setSuit, pickSuit };
