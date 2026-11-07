# Run AFTER rebuild workers finish — renames jarvis→cortana in hot inject/theme/extension files.
# Preserves jarvis.institute and Jarvis 3D marketplace credits.
# IMPORTANT: replacements are case-sensitive (JARVIS→CORTANA, Jarvis→Cortana, jarvis→cortana).
$ErrorActionPreference = "Stop"
if (-not (Test-Path "$PSScriptRoot\..\src\workbenchInject.js")) { $extRoot = Resolve-Path "$PSScriptRoot\.." } else { $extRoot = Resolve-Path "$PSScriptRoot\.." }

function Rename-Content([string]$content) {
  $ph = @{}
  $n = 0
  foreach ($re in @('https://jarvis\.institute/?', 'jarvis\.institute', 'nextgencode\.jarvis-3d-theme', 'Jarvis 3D Theme', 'Jarvis 3D', 'jarvis-3d-theme')) {
    $content = [regex]::Replace($content, $re, {
      param($m)
      $k = "__P${script:n}__"
      $script:ph[$k] = $m.Value
      $script:n++
      $k
    })
  }
  # Case-sensitive (PowerShell -replace is NOT)
  $content = [regex]::Replace($content, 'JARVIS', 'CORTANA')
  $content = [regex]::Replace($content, 'Jarvis', 'Cortana')
  $content = [regex]::Replace($content, 'jarvis', 'cortana')
  foreach ($k in $ph.Keys) { $content = $content.Replace($k, $ph[$k]) }
  return $content
}

$targets = @(
  'media\inject\hud.css', 'media\inject\tokens.css', 'media\inject\boot.css', 'media\inject\hud-markup.html',
  'src\workbenchInject.js', 'src\extension.js', 'src\commandCenterView.js', 'package.json'
) + (Get-ChildItem "$extRoot\themes\*.json" | ForEach-Object { "themes\$($_.Name)" })

foreach ($rel in $targets) {
  $path = Join-Path $extRoot $rel
  if (-not (Test-Path $path)) { Write-Host "skip missing $rel"; continue }
  $script:ph = @{}
  $script:n = 0
  $raw = [IO.File]::ReadAllText($path)
  $new = Rename-Content $raw
  if ($new -ne $raw) { [IO.File]::WriteAllText($path, $new); Write-Host "updated $rel" } else { Write-Host "nochange $rel" }
}

Get-ChildItem "$extRoot\themes\jarvis-*.json" -ErrorAction SilentlyContinue | ForEach-Object {
  $newName = $_.Name -creplace '^jarvis-', 'cortana-'
  $dest = Join-Path $_.DirectoryName $newName
  if ($_.FullName -ne $dest) {
    Move-Item $_.FullName $dest -Force
    Write-Host "renamed theme file -> $newName"
  }
}

$activitySrc = Join-Path $extRoot "media\jarvis-activity.svg"
$activityDst = Join-Path $extRoot "media\cortana-activity.svg"
if ((Test-Path $activitySrc) -and -not (Test-Path $activityDst)) {
  Copy-Item $activitySrc $activityDst -Force
  Write-Host "copied media/cortana-activity.svg"
}

Write-Host "Done. Update package.json theme paths if needed, then rebuild VSIX and re-Enable injection."
