#!/usr/bin/env bash
set -euo pipefail

python3 -m pip install --upgrade pip
pip3 install pyinstaller

pyinstaller --noconfirm --clean --windowed \
  --name QuickXRename \
  --icon docs/quickXrename.icns \
  --add-data "docs:docs" \
  src/main.py

hdiutil create -volname "QuickXRename" \
  -srcfolder dist/QuickXRename.app \
  -ov -format UDZO dist/QuickXRename.dmg
