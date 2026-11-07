$ErrorActionPreference = 'Stop'
$env:PATH = "C:\PS2Recomp\third_party\wgpu-native\lib;C:\PS2Recomp\tools\msys64\clang64\bin;" + $env:PATH
$env:PS2_GPU_LOW_POWER = '1'
$gid = '60c82f4a111da300ac23bbec85272788'
$game = "games\$gid"
$runner = "build\native-$gid\ps2run.exe"
$elf = "$game\disc\boot.elf"
$iso = "$game\disc.iso"
$out = 'logs\nfs-mw-sif-trace.log'
$shots = "$game\shots_siftrace"
New-Item -ItemType Directory -Force -Path $shots | Out-Null
& $runner $elf --disc $iso --boot 'cdrom0:\SLUS_212.67;1' --frames 900 --trace-iop-modules `
  --press '200:start' --press '200:start:700' `
  --frames-dir $shots --frame-every 300 `
  --memcard "$game\siftrace.ps2" 2>&1 | Tee-Object -FilePath $out
