#!/bin/bash
set -e

APP_DIR="/Applications/Angis.app"
CONTENTS_DIR="$APP_DIR/Contents"
RESOURCES_DIR="$CONTENTS_DIR/Resources"
ICONSET_DIR="/tmp/Angis.iconset"
ICON_PNG="/tmp/angis_icon_1024.png"
ICON_ICNS="$RESOURCES_DIR/Angis.icns"

echo "Fixing Angis app icon..."

if [ ! -d "$APP_DIR" ]; then
  echo "Error: /Applications/Angis.app not found."
  echo "Run your installer script first."
  exit 1
fi

mkdir -p "$RESOURCES_DIR"
rm -rf "$ICONSET_DIR"
mkdir -p "$ICONSET_DIR"

python3 - <<'PY'
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

out = Path("/tmp/angis_icon_1024.png")

size = 1024
img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Rounded black background
margin = 80
radius = 180
draw.rounded_rectangle(
    [margin, margin, size - margin, size - margin],
    radius=radius,
    fill=(10, 10, 14, 255),
    outline=(80, 80, 90, 255),
    width=8,
)

# Glow circle
draw.ellipse(
    [250, 180, 774, 704],
    fill=(30, 30, 45, 255),
    outline=(150, 150, 180, 255),
    width=8,
)

# Big A
try:
    font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 470)
except:
    font = ImageFont.load_default()

text = "A"
bbox = draw.textbbox((0, 0), text, font=font)
tw = bbox[2] - bbox[0]
th = bbox[3] - bbox[1]
x = (size - tw) / 2
y = 220

draw.text((x + 8, y + 8), text, font=font, fill=(0, 0, 0, 180))
draw.text((x, y), text, font=font, fill=(245, 245, 255, 255))

# Small name
try:
    small = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 90)
except:
    small = ImageFont.load_default()

label = "ANGIS"
bbox = draw.textbbox((0, 0), label, font=small)
lw = bbox[2] - bbox[0]
draw.text(((size - lw) / 2, 760), label, font=small, fill=(220, 220, 235, 255))

img.save(out)
print(out)
PY

# Create all macOS icon sizes
sips -z 16 16 "$ICON_PNG" --out "$ICONSET_DIR/icon_16x16.png" >/dev/null
sips -z 32 32 "$ICON_PNG" --out "$ICONSET_DIR/icon_16x16@2x.png" >/dev/null
sips -z 32 32 "$ICON_PNG" --out "$ICONSET_DIR/icon_32x32.png" >/dev/null
sips -z 64 64 "$ICON_PNG" --out "$ICONSET_DIR/icon_32x32@2x.png" >/dev/null
sips -z 128 128 "$ICON_PNG" --out "$ICONSET_DIR/icon_128x128.png" >/dev/null
sips -z 256 256 "$ICON_PNG" --out "$ICONSET_DIR/icon_128x128@2x.png" >/dev/null
sips -z 256 256 "$ICON_PNG" --out "$ICONSET_DIR/icon_256x256.png" >/dev/null
sips -z 512 512 "$ICON_PNG" --out "$ICONSET_DIR/icon_256x256@2x.png" >/dev/null
sips -z 512 512 "$ICON_PNG" --out "$ICONSET_DIR/icon_512x512.png" >/dev/null
sips -z 1024 1024 "$ICON_PNG" --out "$ICONSET_DIR/icon_512x512@2x.png" >/dev/null

iconutil -c icns "$ICONSET_DIR" -o "$ICON_ICNS"

# Add icon reference to Info.plist
/usr/libexec/PlistBuddy -c "Delete :CFBundleIconFile" "$CONTENTS_DIR/Info.plist" 2>/dev/null || true
/usr/libexec/PlistBuddy -c "Add :CFBundleIconFile string Angis" "$CONTENTS_DIR/Info.plist"

# Refresh macOS icon cache for this app
touch "$APP_DIR"
touch "$CONTENTS_DIR/Info.plist"

echo "Done. Icon installed at:"
echo "$ICON_ICNS"
echo ""
echo "Now run:"
echo "open /Applications"
