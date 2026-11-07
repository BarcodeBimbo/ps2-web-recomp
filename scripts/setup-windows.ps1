$ErrorActionPreference = 'Stop'
try {
    if ($env:PROCESSOR_ARCHITECTURE -ne 'AMD64') {
        throw 'Use an x64 edition of Windows and the x64 Command Prompt.'
    }
    Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
    if ($PWD.Path -notmatch '^[A-Za-z]:\\[A-Za-z0-9_.\\-]+$') {
        throw 'Extract the ZIP to a short local folder with no spaces, such as C:\PS2Recomp, then run Setup.cmd.'
    }
    foreach ($legacy in @('Mobile.cmd', 'SetupDownloader.cmd', 'SetupRuntime.cmd')) {
        if (Test-Path -LiteralPath $legacy) { Remove-Item -LiteralPath $legacy -Force; Write-Host ('Removed obsolete launcher: ' + $legacy) }
    }
    foreach ($internal in @('downloader', 'runtime')) {
        if (Test-Path -LiteralPath $internal) { $item = Get-Item -LiteralPath $internal -Force; $item.Attributes = $item.Attributes -bor [System.IO.FileAttributes]::Hidden }
    }
    Write-Host '[Bootstrap] Checking Python runtime...'
    $pythonVersion = '3.14.10'
    $pythonSha256 = '90905e64a840557d8c1bc4f5b74db3d7ee85e3ffb217611cac1c7813acea4159'
    $pythonFolder = 'tools\python-' + $pythonVersion
    $python = Join-Path $PWD ($pythonFolder + '\python.exe')
    $runtimeReady = $false
    if (Test-Path -LiteralPath $python) {
        try {
            & $python -c "import ssl, zipfile, hashlib, subprocess, http.server" 2>$null
            $runtimeReady = ($LASTEXITCODE -eq 0)
        } catch { $runtimeReady = $false }
    }
    if (!$runtimeReady) {
        $stage = Join-Path ([System.IO.Path]::GetTempPath()) ('ps2recomp-' + [guid]::NewGuid())
        New-Item -ItemType Directory -Path $stage | Out-Null
        try {
            $archive = Join-Path $stage 'python.zip'
            Write-Host 'Downloading Python for Windows...'
            Invoke-WebRequest -UseBasicParsing ('https://www.python.org/ftp/python/' + $pythonVersion + '/python-' + $pythonVersion + '-embed-amd64.zip') -OutFile $archive
            if ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant() -ne $pythonSha256) {
                throw 'Python download checksum mismatch. Run Setup.cmd again.'
            }
            Write-Host '[Bootstrap] Python downloaded and verified; extracting...'
            Expand-Archive -LiteralPath $archive -DestinationPath (Join-Path $stage 'python')
            New-Item -ItemType Directory -Force -Path 'tools' | Out-Null
            if (Test-Path -LiteralPath $pythonFolder) { Remove-Item -LiteralPath $pythonFolder -Recurse -Force }
            Move-Item -LiteralPath (Join-Path $stage 'python') -Destination $pythonFolder
        } finally {
            Remove-Item -LiteralPath $stage -Recurse -Force
        }
    }
    Write-Host '[Bootstrap] Python ready. Starting numbered setup stages...'
    & $python -X utf8 -u scripts/windows_setup.py
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} catch {
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}
