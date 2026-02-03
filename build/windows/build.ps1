python -m pip install --upgrade pip
pip install pyinstaller

pyinstaller --noconfirm --clean --windowed `
  --name QuickXRename `
  --icon docs\quickXrename.ico `
  --add-data "docs;docs" `
  src\main.py

# Optional: Inno Setup installer
if (Test-Path "$PSScriptRoot\installer.iss") {
  & "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe" "$PSScriptRoot\installer.iss"
}
