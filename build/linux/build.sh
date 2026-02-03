#!/usr/bin/env bash
set -euo pipefail

python3 -m pip install --upgrade pip
pip3 install pyinstaller appimage-builder

pyinstaller --noconfirm --clean --windowed \
  --name QuickXRename \
  --add-data "docs:docs" \
  src/main.py

appimage-builder --recipe build/linux/appimage.yml
