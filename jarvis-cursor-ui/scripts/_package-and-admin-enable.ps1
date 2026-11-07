# Package Cortana Workstation 0.5.5 + install + elevated Admin Enable
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path (Join-Path $Root "package.json"))) {
  $Root = "C:\PS2Recomp\cortana-cursor-ui"
}
Set-Location $Root

$pkg = Get-Content .\package.json -Raw | ConvertFrom-Json
$ver = $pkg.version
$vsixName = "$($pkg.name)-$ver.vsix"
Write-Host "=== Package $($pkg.displayName) $ver ==="

# Ensure vsce
$vsce = Get-Command vsce -ErrorAction SilentlyContinue
if (-not $vsce) {
  Write-Host "Installing @vscode/vsce locally..."
  npm install --no-save --no-package-lock @vscode/vsce 2>&1 | Select-Object -Last 5
}

Write-Host "Packaging VSIX..."
npx --yes @vscode/vsce package --allow-missing-repository --skip-license -o $vsixName
if (-not (Test-Path $vsixName)) { throw "VSIX missing: $vsixName" }
Write-Host "VSIX OK: $((Get-Item $vsixName).FullName) ($((Get-Item $vsixName).Length) bytes)"

$cursor = "C:\Program Files\cursor\resources\app\bin\cursor.cmd"
if (-not (Test-Path $cursor)) { $cursor = "cursor" }

Write-Host "=== Install extension ==="
& $cursor --install-extension (Resolve-Path $vsixName).Path --force
if ($LASTEXITCODE -ne 0) { throw "cursor --install-extension failed: $LASTEXITCODE" }

$extDir = Join-Path $env:USERPROFILE ".cursor\extensions\ps2recomp-local.cortana-cursor-ui-$ver"
if (-not (Test-Path (Join-Path $extDir "package.json"))) {
  Write-Host "Install path missing — copying source tree to $extDir"
  New-Item -ItemType Directory -Force -Path $extDir | Out-Null
  robocopy $Root $extDir /E /XD .git node_modules .vscode _probe icons _font_probe /NFL /NDL /NJH /NJS /nc /ns /np | Out-Null
  if (-not (Test-Path (Join-Path $extDir "package.json"))) { throw "Failed to stage extension at $extDir" }
}

Write-Host "Installed/synced: $extDir"
$pkgInstalled = Get-Content (Join-Path $extDir "package.json") -Raw | ConvertFrom-Json
Write-Host "displayName=$($pkgInstalled.displayName) version=$($pkgInstalled.version)"

# Elevated Admin Enable
$node = (Get-Command node).Source
$enableJs = Join-Path $Root "scripts\admin-enable-elevated.js"
$outLog = Join-Path $Root "scripts\admin-enable-last-run.json"
$arg = "-NoProfile -ExecutionPolicy Bypass -Command `"& '$node' '$enableJs' --ext '$extDir' | Tee-Object -FilePath '$outLog'; exit `$LASTEXITCODE`""

Write-Host "=== Elevated Admin Enable (UAC) ==="
$p = Start-Process -FilePath "powershell.exe" -Verb RunAs -ArgumentList $arg -Wait -PassThru
Write-Host "Elevated exit: $($p.ExitCode)"
if (Test-Path $outLog) {
  Write-Host "--- enable report ---"
  Get-Content $outLog -Raw
}

if ($p.ExitCode -ne 0) {
  Write-Host "TRYING non-elevated enable (may EACCES)..."
  & $node $enableJs --ext $extDir | Tee-Object -FilePath $outLog
  exit $LASTEXITCODE
}
exit 0
