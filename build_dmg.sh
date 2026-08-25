#!/usr/bin/env bash
set -e

APP_NAME="AgentFeed"
DMG_NAME="AgentFeed-macOS.dmg"
SOURCE_APP="dist/${APP_NAME}.app"
TEMP_DMG_DIR="/tmp/${APP_NAME}_dmg_staging_$$"

echo "🔨 Building macOS standard DMG installer..."

# Ensure clean staging directory
rm -rf "$TEMP_DMG_DIR"
mkdir -p "$TEMP_DMG_DIR"

# Copy .app bundle
cp -R "$SOURCE_APP" "$TEMP_DMG_DIR/${APP_NAME}.app"

# Create symlink to /Applications for standard drag-and-drop installation
ln -s /Applications "$TEMP_DMG_DIR/Applications"

# Clean previous dmg if exists
rm -f "dist/${DMG_NAME}" "${DMG_NAME}"

# Create compressed DMG disk image
hdiutil create -volname "${APP_NAME}" \
  -srcfolder "$TEMP_DMG_DIR" \
  -ov \
  -format UDZO \
  "dist/${DMG_NAME}"

# Clean up staging
rm -rf "$TEMP_DMG_DIR"

echo "✅ Successfully generated: dist/${DMG_NAME}"
ls -lh "dist/${DMG_NAME}"
