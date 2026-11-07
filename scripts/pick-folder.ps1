$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
Add-Type -AssemblyName System.Windows.Forms

$owner = [System.Windows.Forms.Form]::new()
$owner.TopMost = $true
$dialog = [System.Windows.Forms.FolderBrowserDialog]::new()
try {
    $dialog.Description = 'Select a PS2 covers folder'
    $dialog.ShowNewFolderButton = $false
    if ($dialog.ShowDialog($owner) -eq [System.Windows.Forms.DialogResult]::OK) {
        [Console]::WriteLine($dialog.SelectedPath)
    }
} finally {
    $dialog.Dispose()
    $owner.Dispose()
}
