# Schedulable wrapper for nightly download → build → heal → verify (+ optional Chrome gates).
# Example Task Scheduler action:
#   powershell -NoProfile -ExecutionPolicy Bypass -File C:\PS2Recomp\scripts\run_nightly_pipeline.ps1
param(
    [string[]]$Game,
    [switch]$Library,
    [int]$Frames = 200,
    [switch]$SkipBuild,
    [switch]$DryHeal,
    [switch]$ChromeServe,
    [switch]$StoreContract
)
$ErrorActionPreference = "Stop"
Set-Location C:\PS2Recomp
$argsList = @("-3", "scripts\nightly_pipeline.py", "--frames", "$Frames")
if ($Library) { $argsList += "--library" }
if ($SkipBuild) { $argsList += "--skip-build" }
if ($DryHeal) { $argsList += "--dry-heal" }
if ($ChromeServe) { $argsList += "--chrome-serve" }
if ($StoreContract) { $argsList += "--store-contract" }
foreach ($g in $Game) { $argsList += @("--game", $g) }
if (-not $Library -and (-not $Game -or $Game.Count -eq 0)) {
    $argsList += "--library"
    $argsList += "--skip-build"
    $argsList += "--store-contract"
}
& py @argsList
exit $LASTEXITCODE
