# Application Icons

Budget Analyser uses a modern wallet icon with a blue gradient background, white wallet body, green card with chip, and gold dollar coin.

## Icon Files

| File | Size | Purpose |
|------|------|---------|
| `icon-source.svg` | 1024x1024 | Source vector (edit this to change the icon) |
| `icon-1024.png` | 1024x1024 | High-res source PNG |
| `icon.png` | 512x512 | Base PNG icon |
| `icon.icns` | Multi-size | macOS app bundle icon (.dmg) |
| `icon.ico` | Multi-size | Windows app icon (.exe/.msi) |
| `32x32.png` | 32x32 | Small icon |
| `64x64.png` | 64x64 | Medium-small icon |
| `128x128.png` | 128x128 | Medium icon |
| `128x128@2x.png` | 256x256 | Retina medium icon |
| `Square*.png` | Various | Windows Store logos |
| `StoreLogo.png` | 50x50 | Windows Store logo |

## Regenerating Icons

To regenerate all sizes from the source SVG:

```bash
# 1. Convert SVG to 1024x1024 PNG
rsvg-convert -w 1024 -h 1024 src-tauri/icons/icon-source.svg -o src-tauri/icons/icon-1024.png

# 2. Generate all icon formats
cd src/frontend
npx tauri icon src-tauri/icons/icon-1024.png
```
