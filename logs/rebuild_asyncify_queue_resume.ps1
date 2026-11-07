$ErrorActionPreference = "Continue"
$env:PATH = "C:\PS2Recomp\third_party\wgpu-native\lib;C:\PS2Recomp\tools\msys64\clang64\bin;C:\PS2Recomp\tools\msys64\usr\bin;" + $env:PATH
$env:EMSDK = "C:\PS2Recomp\tools\emsdk"
$env:PS2_WEB_ASYNC_MODE = "asyncify"
$env:PS2_BUILD_JOBS = "1"
Set-Location C:\PS2Recomp
# Resume after crash: skip already-asyncify games; leave Def Jam for end retry.
$queue = @(
  '9ce58de36f3fbe96fb260a3221d91f20',
  'a2116d2ac08a7be4db4e8455ad58d2e5',
  'f141051d9b9fae0fb48deced01311f44',
  'ffb47d7e14cf9f5c02425d9158c29b76',
  '76615f9956b13094771e370c883c7170'
)
$log = "logs\asyncify-queue-run.log"
Add-Content $log "$(Get-Date -Format o) RESUME after crash; remaining=$($queue -join ',')"
foreach ($gid in $queue) {
  $bj = "build\web-$gid\build.json"
  if (Test-Path $bj) {
    try {
      $mode = (Get-Content $bj -Raw | ConvertFrom-Json).async_mode
      if ($mode -eq 'asyncify') {
        Add-Content $log "$(Get-Date -Format o) SKIP $gid already asyncify"
        continue
      }
    } catch {}
  }
  Add-Content $log "$(Get-Date -Format o) START $gid"
  try {
    python -u logs\rebuild_asyncify_one.py $gid 2>&1 | Tee-Object -FilePath "logs\asyncify-$gid.log"
    Add-Content $log "$(Get-Date -Format o) DONE $gid exit $LASTEXITCODE"
  } catch {
    Add-Content $log "$(Get-Date -Format o) FAIL $gid $_"
  }
}
Add-Content $log "$(Get-Date -Format o) QUEUE COMPLETE"
