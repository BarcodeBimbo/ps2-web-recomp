$wbDir = "C:\Program Files\cursor\resources\app\out\vs\code\electron-sandbox\workbench"
$report = @{ ok = $false; actions = @() }
try {
  $html = Get-Content "$wbDir\workbench.html" -Raw
  if ($html -match "JARVIS-INJECT|CORTANA-INJECT|jarvis-cc-hud|cortana-cc-hud") {
    # restore from smallest bak
    $baks = Get-ChildItem "$wbDir\workbench.jarvis.*.bak.html" | Sort-Object Length
    $pristine = $baks | Where-Object { $_.Length -lt 5000 } | Select-Object -First 1
    if (-not $pristine) { throw "no pristine bak" }
    Copy-Item $pristine.FullName "$wbDir\workbench.html" -Force
    $report.actions += "restored from $($pristine.Name)"
  } else {
    $report.actions += "workbench already pristine"
  }
  Get-ChildItem $wbDir -Filter "jarvis-boot-splash.png" -ErrorAction SilentlyContinue | ForEach-Object {
    Remove-Item $_.FullName -Force
    $report.actions += "removed splash $($_.Name)"
  }
  Get-ChildItem $wbDir -Filter "cortana-boot-splash.png" -ErrorAction SilentlyContinue | ForEach-Object {
    Remove-Item $_.FullName -Force
    $report.actions += "removed splash $($_.Name)"
  }
  # keep pristine bak; remove large inject baks
  Get-ChildItem "$wbDir\workbench.jarvis.*.bak.html" | Where-Object { $_.Length -gt 10000 } | ForEach-Object {
    Remove-Item $_.FullName -Force
    $report.actions += "removed inject bak $($_.Name)"
  }
  $report.ok = $true
  $report.finalSize = (Get-Item "$wbDir\workbench.html").Length
} catch {
  $report.error = $_.Exception.Message
}
$report | ConvertTo-Json -Compress | Set-Content "C:\PS2Recomp\jarvis-cursor-ui\scripts\uninstall-last-run.json" -Encoding UTF8
