#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APPDIR="$ROOT_DIR/build/AppDir"
PYTHON_VERSION="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
SITE_PACKAGES="$APPDIR/usr/lib/python${PYTHON_VERSION}/site-packages"

echo "[build_appimage] Cleaning AppDir at $APPDIR"
rm -rf "$APPDIR"
mkdir -p \
    "$APPDIR/usr/bin" \
    "$APPDIR/usr/share/applications" \
    "$APPDIR/usr/share/icons/hicolor/256x256/apps" \
    "$APPDIR/usr/share/metainfo" \
    "$SITE_PACKAGES"

echo "[build_appimage] Creating AppRun"
cat <<'ARUN' > "$APPDIR/AppRun"
#!/bin/sh
HERE="$(dirname "$(readlink -f "$0")")"
export APPDIR="$HERE"
exec "$HERE/usr/bin/crypto-float-monitor" "$@"
ARUN
chmod +x "$APPDIR/AppRun"

echo "[build_appimage] Creating launcher script"
cat <<'LAUNCH' > "$APPDIR/usr/bin/crypto-float-monitor"
#!/bin/sh
SCRIPT_PATH="$(readlink -f "$0")"
BIN_DIR="$(dirname "$SCRIPT_PATH")"
APPDIR="$(dirname "$BIN_DIR")"
PYTHON_VERSION="$(/usr/bin/env python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
PYTHON_SITE="$APPDIR/usr/lib/python$PYTHON_VERSION/site-packages"
QT_PLUGIN_PATH_DIR="$PYTHON_SITE/PyQt6/Qt6/plugins"
QT_QML_DIR="$PYTHON_SITE/PyQt6/Qt6/qml"
QT_LIB_DIR="$PYTHON_SITE/PyQt6/Qt6/lib"
export PYTHONPATH="$PYTHON_SITE${PYTHONPATH+:$PYTHONPATH}"
export QT_PLUGIN_PATH="$QT_PLUGIN_PATH_DIR${QT_PLUGIN_PATH+:$QT_PLUGIN_PATH}"
export QML2_IMPORT_PATH="$QT_QML_DIR${QML2_IMPORT_PATH+:$QML2_IMPORT_PATH}"
export LD_LIBRARY_PATH="$QT_LIB_DIR${LD_LIBRARY_PATH+:$LD_LIBRARY_PATH}"
exec /usr/bin/env python3 -m crypto_float_monitor.main "$@"
LAUNCH
chmod +x "$APPDIR/usr/bin/crypto-float-monitor"

DESKTOP_FILE="$APPDIR/crypto-float-monitor.desktop"
cat <<'DESK' > "$DESKTOP_FILE"
[Desktop Entry]
Type=Application
Name=Crypto Float Monitor
Comment=Floating crypto price ticker
Exec=crypto-float-monitor
Icon=crypto-float-monitor
Terminal=false
Categories=Finance;Utility;
DESK
install -m 644 "$DESKTOP_FILE" "$APPDIR/usr/share/applications/crypto-float-monitor.desktop"

echo "[build_appimage] Copying icons"
install -m 644 "$ROOT_DIR/assets/btc_logo.png" "$APPDIR/crypto-float-monitor.png"
install -m 644 "$ROOT_DIR/assets/btc_logo.png" \
    "$APPDIR/usr/share/icons/hicolor/256x256/apps/crypto-float-monitor.png"

echo "[build_appimage] Installing Python dependencies into $SITE_PACKAGES"
python3 -m pip install --upgrade --no-warn-script-location \
    --target "$SITE_PACKAGES" \
    PyQt6 PyQt6-Qt6 PyQt6-sip websocket-client

python3 -m pip install --upgrade --no-warn-script-location \
    --target "$SITE_PACKAGES" \
    "$ROOT_DIR"

echo "[build_appimage] AppDir ready at $APPDIR"
