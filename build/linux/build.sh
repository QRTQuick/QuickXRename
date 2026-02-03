#!/usr/bin/env bash
set -euo pipefail

# System libs for Qt on Linux (needed for AppImage packaging)
if command -v apt-get >/dev/null 2>&1; then
  sudo apt-get update
  sudo apt-get install -y \
    libtiff5 \
    libxkbcommon-x11-0 \
    libxcb-cursor0 \
    libxcb-keysyms1 \
    libxcb-icccm4 \
    libxcb-xkb1 \
    libxcb-render-util0 \
    libxcb-image0 \
    libxcb-util1 \
    libxcb-shape0
fi

python3 -m pip install --upgrade pip
pip3 install pyinstaller appimage-builder

pyinstaller --noconfirm --clean --windowed \
  --name QuickXRename \
  --add-data "docs:docs" \
  src/main.py

# Prepare AppDir and icon
rm -rf AppDir
mkdir -p AppDir
cp -R dist/QuickXRename/* AppDir/
mkdir -p AppDir/usr/share/icons/hicolor/256x256/apps
if [ -f "docs/quickXrename logo1.png" ]; then
  cp "docs/quickXrename logo1.png" AppDir/usr/share/icons/hicolor/256x256/apps/quickxrename.png
fi

appimage-builder --recipe build/linux/appimage.yml
