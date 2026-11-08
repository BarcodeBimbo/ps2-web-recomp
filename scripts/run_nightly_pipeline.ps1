# Schedulable wrapper for nightly download → build → heal → verify.
# Example Task Scheduler action:
#   powershell -NoProfile -ExecutionPolicy Bypass -File C:\PS2Recomp\scripts\run_nightly_pipeline.ps1
param(
    [string[]]$Game,
    [switch]$Library,
    [int]$Frames = 200,
    [switch]$SkipBuild,
    [switch]$DryHeal
)
$ErrorActionPreference = "Stop"
Set-Location C:\PS2Recomp
$py = "py"
$args = @("-3", "scripts\nightly_pipeline.py", "--frames", "$Frames")
if ($Library) { $args += "--library" }
if ($SkipBuild) { $args += "--skip-build" }
if ($DryHeal) { $args += "--dry-heal" }
foreach ($g in $Game) { $args += @("--game", $g) }
if (-not $Library -and (-not $Game -or $Game.Count -eq 0)) {
    $args += "--library"
    $args += "--skip-build"
}
& $py @args
exit $LASTEXITCODE
