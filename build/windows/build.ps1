python -m pip install --upgrade pip
pip install pyinstaller

$iconPath = "docs\quickXrename.ico"
$iconArg = @()
if (Test-Path $iconPath) {
  $iconArg = @("--icon", $iconPath)
}

pyinstaller --noconfirm --clean --windowed `
  --name QuickXRename `
  @iconArg `
  --add-data "docs;docs" `
  src\main.py

# Optional: Inno Setup installer (runs only if dist output exists)
$distPath = "dist\QuickXRename\*"
if ((Test-Path "$PSScriptRoot\installer.iss") -and (Test-Path "dist\QuickXRename")) {
  & "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe" "$PSScriptRoot\installer.iss"
}
