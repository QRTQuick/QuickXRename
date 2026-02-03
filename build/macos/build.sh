#!/usr/bin/env bash
set -euo pipefail

python3 -m pip install --upgrade pip
pip3 install pyinstaller

ICON_ARG=()
if [ -f "docs/quickXrename.icns" ]; then
  ICON_ARG=(--icon "docs/quickXrename.icns")
fi

pyinstaller --noconfirm --clean --windowed \
  --name QuickXRename \
  "${ICON_ARG[@]}" \
  --add-data "docs:docs" \
  src/main.py

hdiutil create -volname "QuickXRename" \
  -srcfolder dist/QuickXRename.app \
  -ov -format UDZO dist/QuickXRename.dmg
