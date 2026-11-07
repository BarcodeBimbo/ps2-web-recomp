"use strict";

const vscode = require("vscode");

/**
 * @returns {{total:number,errors:number,warnings:number,hints:number,items:Array<{severity:string,message:string,file:string,line:number,uri:string}>}}
 */
function getThreats(limit = 12) {
  const diags = vscode.languages.getDiagnostics();
  /** @type {Array<{severity:string,message:string,file:string,line:number,uri:string,sev:number}>} */
  const items = [];
  let errors = 0;
  let warnings = 0;
  let hints = 0;

  for (const [uri, list] of diags) {
    for (const d of list) {
      const sev = d.severity;
      if (sev === vscode.DiagnosticSeverity.Error) errors += 1;
      else if (sev === vscode.DiagnosticSeverity.Warning) warnings += 1;
      else hints += 1;
      items.push({
        severity: severityLabel(sev),
        message: String(d.message || "").slice(0, 140),
        file: uri.fsPath.split(/[/\\]/).pop() || uri.fsPath,
        line: (d.range?.start?.line || 0) + 1,
        uri: uri.toString(),
        sev,
      });
    }
  }

  items.sort((a, b) => a.sev - b.sev);
  return {
    total: errors + warnings + hints,
    errors,
    warnings,
    hints,
    items: items.slice(0, limit).map(({ sev, ...rest }) => rest),
  };
}

function severityLabel(sev) {
  if (sev === vscode.DiagnosticSeverity.Error) return "error";
  if (sev === vscode.DiagnosticSeverity.Warning) return "warning";
  if (sev === vscode.DiagnosticSeverity.Information) return "info";
  return "hint";
}

/** @param {string} uriStr */
async function openThreat(uriStr, line) {
  try {
    const uri = vscode.Uri.parse(uriStr);
    const doc = await vscode.workspace.openTextDocument(uri);
    const editor = await vscode.window.showTextDocument(doc);
    const pos = new vscode.Position(Math.max(0, (line || 1) - 1), 0);
    editor.selection = new vscode.Selection(pos, pos);
    editor.revealRange(new vscode.Range(pos, pos));
  } catch {
    vscode.window.showWarningMessage("Could not open that threat location.");
  }
}

module.exports = { getThreats, openThreat };
