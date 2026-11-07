$ErrorActionPreference = "Stop"
$env:PATH = "C:\PS2Recomp\third_party\wgpu-native\lib;C:\PS2Recomp\tools\msys64\clang64\bin;C:\PS2Recomp\tools\msys64\usr\bin;" + $env:PATH
$env:EMSDK = "C:\PS2Recomp\tools\emsdk"
$env:PS2_WEB_ASYNC_MODE = "asyncify"
$env:PS2_BUILD_JOBS = "1"
Set-Location C:\PS2Recomp
$queue = Get-Content logs\asyncify_queue.txt | Where-Object { $_ -and $_ -notmatch 'c0c45270' }
$log = "logs\asyncify-queue-run.log"
"" | Set-Content $log
foreach ($gid in $queue) {
  Add-Content $log "$(Get-Date -Format o) START $gid"
  try {
    python -u logs\rebuild_asyncify_one.py $gid 2>&1 | Tee-Object -FilePath "logs\asyncify-$gid.log"
    Add-Content $log "$(Get-Date -Format o) DONE $gid exit $LASTEXITCODE"
  } catch {
    Add-Content $log "$(Get-Date -Format o) FAIL $gid $_"
  }
}
Add-Content $log "$(Get-Date -Format o) QUEUE COMPLETE"
