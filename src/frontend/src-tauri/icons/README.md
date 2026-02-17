# Application Icons

This directory should contain application icons in various sizes.

## Required Icons

For a complete icon set, you'll need:
- `32x32.png` - Small icon
- `128x128.png` - Medium icon
- `128x128@2x.png` - Retina medium icon
- `icon.icns` - macOS icon bundle
- `icon.ico` - Windows icon bundle
- `icon.png` - Base icon (1024x1024 recommended)

## Temporary Setup

Currently using placeholder icons. To add proper icons:

1. Create a 1024x1024 PNG icon for the Budget Analyser application
2. Use the Tauri icon generator to create all required sizes:
   ```bash
   npm run tauri icon /path/to/your/icon.png
   ```

This will automatically generate all required icon formats and sizes.
