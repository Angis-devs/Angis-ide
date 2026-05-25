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
