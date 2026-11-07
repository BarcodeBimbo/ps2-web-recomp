$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
Add-Type -AssemblyName System.Windows.Forms

$owner = [System.Windows.Forms.Form]::new()
$owner.TopMost = $true
$dialog = [System.Windows.Forms.OpenFileDialog]::new()
try {
    $dialog.Title = 'Select a PS2 disc image'
    $dialog.Filter = 'PS2 discs and archives|*.iso;*.bin;*.cue;*.img;*.chd;*.rom;*.zip;*.zipx;*.7z;*.rar;*.tar;*.gz;*.tgz;*.bz2;*.tbz2;*.xz;*.txz;*.zst;*.lzma;*.cab;*.arj;*.lzh;*.lha;*.cpio;*.xar;*.z|All files|*.*'
    $dialog.CheckFileExists = $true
    if ($dialog.ShowDialog($owner) -eq [System.Windows.Forms.DialogResult]::OK) {
        [Console]::WriteLine($dialog.FileName)
    }
} finally {
    $dialog.Dispose()
    $owner.Dispose()
}
