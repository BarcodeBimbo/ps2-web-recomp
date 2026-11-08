$ErrorActionPreference = "Continue"
$log = "C:\PS2Recomp\logs\autonomous-pipeline\owner-build-watch-2026-11-07.log"
function Say($m) { $t = Get-Date -Format "yyyy-MM-dd HH:mm:ss"; Add-Content $log "[$t] $m"; Write-Output "[$t] $m" }
Say "watch start"
$targets = @(
  @{ name="hitman-web-next"; wasm="C:\PS2Recomp\build\web-a2116d2ac08a7be4db4e8455ad58d2e5-next\ps2web.wasm"; cmakeMatch="web-a2116d2ac08a7be4db4e8455ad58d2e5-next" },
  @{ name="nfs-web-next"; wasm="C:\PS2Recomp\build\web-60c82f4a111da300ac23bbec85272788-next\ps2web.wasm"; cmakeMatch="web-60c82f4a111da300ac23bbec85272788-next" },
  @{ name="hitman-native"; exe="C:\PS2Recomp\build\native-a2116d2ac08a7be4db4e8455ad58d2e5\ps2run.exe"; cmakeMatch="native-a2116d2ac08a7be4db4e8455ad58d2e5" }
)
$done = @{}
while ($done.Count -lt $targets.Count) {
  foreach ($t in $targets) {
    if ($done.ContainsKey($t.name)) { continue }
    $cmakeLive = $false
    Get-CimInstance Win32_Process -Filter "Name='cmake.exe'" -ErrorAction SilentlyContinue | ForEach-Object {
      if ($_.CommandLine -and $_.CommandLine -like "*$($t.cmakeMatch)*") { $script:cmakeLive = $true }
    }
    $artifact = if ($t.ContainsKey("wasm")) { $t.wasm } else { $t.exe }
    $artOk = Test-Path $artifact
    $mtime = if ($artOk) { (Get-Item $artifact).LastWriteTime.ToString("HH:mm:ss") } else { "missing" }
    if (-not $cmakeLive -and $artOk) {
      # For web-next, also require wasm newer than watch start roughly - check size > 1MB
      $len = (Get-Item $artifact).Length
      if ($len -gt 1MB) {
        Say "COMPLETE $($t.name) artifact=$artifact mtime=$mtime bytes=$len"
        $done[$t.name] = $true
        Add-Content "C:\PS2Recomp\logs\workers\W-HITMAN-platform-heartbeat.log" "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] BUILD_WATCH $($t.name) COMPLETE"
      }
    }
  }
  # owner heartbeat refresh every loop
  $myPid = $PID
  $utc = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
  $local = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
  Set-Content "C:\PS2Recomp\logs\campaign-owner-alive.txt" "campaign-owner ALIVE`nstatus=permanent-overnight-running`npid=$myPid`nlocal=$local`nutc=$utc`nwatcher=build-complete`n" -Encoding utf8
  @{status="permanent-overnight-running";pid=$myPid;utc=$utc;local=$local;role="campaign-owner";watcher="build-complete";done=@($done.Keys)} | ConvertTo-Json | Set-Content "C:\PS2Recomp\logs\campaign-owner-heartbeat.json" -Encoding utf8
  Start-Sleep -Seconds 45
}
Say "all watched builds complete"
