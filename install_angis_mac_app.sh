#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"
APP_NAME="Angis"
APP_DIR="/Applications/${APP_NAME}.app"
CONTENTS_DIR="${APP_DIR}/Contents"
MACOS_DIR="${CONTENTS_DIR}/MacOS"
RESOURCES_DIR="${CONTENTS_DIR}/Resources"

echo "Installing ${APP_NAME}.app to /Applications..."

if [ ! -d "$PROJECT_DIR" ]; then
  echo "Error: Project folder not found: $PROJECT_DIR"
  exit 1
fi

mkdir -p "$MACOS_DIR"
mkdir -p "$RESOURCES_DIR"

LOGO_PNG="${PROJECT_DIR}/logo/logo.png"
ICONSET_DIR="${RESOURCES_DIR}/Angis.iconset"
ICON_FILE="${RESOURCES_DIR}/Angis.icns"
if [ -f "$LOGO_PNG" ]; then
  rm -rf "$ICONSET_DIR"
  mkdir -p "$ICONSET_DIR"
  sips -z 16 16 "$LOGO_PNG" --out "${ICONSET_DIR}/icon_16x16.png" >/dev/null
  sips -z 32 32 "$LOGO_PNG" --out "${ICONSET_DIR}/icon_16x16@2x.png" >/dev/null
  sips -z 32 32 "$LOGO_PNG" --out "${ICONSET_DIR}/icon_32x32.png" >/dev/null
  sips -z 64 64 "$LOGO_PNG" --out "${ICONSET_DIR}/icon_32x32@2x.png" >/dev/null
  sips -z 128 128 "$LOGO_PNG" --out "${ICONSET_DIR}/icon_128x128.png" >/dev/null
  sips -z 256 256 "$LOGO_PNG" --out "${ICONSET_DIR}/icon_128x128@2x.png" >/dev/null
  sips -z 256 256 "$LOGO_PNG" --out "${ICONSET_DIR}/icon_256x256.png" >/dev/null
  sips -z 512 512 "$LOGO_PNG" --out "${ICONSET_DIR}/icon_256x256@2x.png" >/dev/null
  sips -z 512 512 "$LOGO_PNG" --out "${ICONSET_DIR}/icon_512x512.png" >/dev/null
  sips -z 1024 1024 "$LOGO_PNG" --out "${ICONSET_DIR}/icon_512x512@2x.png" >/dev/null
  iconutil -c icns "$ICONSET_DIR" -o "$ICON_FILE"
  rm -rf "$ICONSET_DIR"
else
  echo "Warning: logo image not found: $LOGO_PNG"
fi

cat > "${CONTENTS_DIR}/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
 "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleName</key>
  <string>Angis</string>
  <key>CFBundleDisplayName</key>
  <string>Angis</string>
  <key>CFBundleIdentifier</key>
  <string>com.fellflow.angis</string>
  <key>CFBundleVersion</key>
  <string>1.0.0</string>
  <key>CFBundleShortVersionString</key>
  <string>1.0.0</string>
  <key>CFBundleExecutable</key>
  <string>AngisLauncher</string>
  <key>CFBundleIconFile</key>
  <string>Angis</string>
  <key>CFBundlePackageType</key>
  <string>APPL</string>
  <key>LSMinimumSystemVersion</key>
  <string>11.0</string>
  <key>NSHighResolutionCapable</key>
  <true/>
</dict>
</plist>
PLIST

PYTHON_BIN="$(python3 -c 'import sys; print(sys.executable)')"

cat > "${MACOS_DIR}/AngisLauncher" <<LAUNCHER
#!/bin/bash

PROJECT_DIR="$PROJECT_DIR"
PYTHON="$PYTHON_BIN"

cd "\$PROJECT_DIR" || exit 1

if [ -x "\$PYTHON" ]; then
  "\$PYTHON" -m angis ide "\$@"
else
  osascript -e 'display dialog "Python 3.10+ is required to run Angis." buttons {"OK"} default button "OK"'
  exit 1
fi
LAUNCHER

chmod +x "${MACOS_DIR}/AngisLauncher"

touch "$APP_DIR"

echo "Done."
echo "Installed: ${APP_DIR}"
echo "You can now open Angis from Applications."
