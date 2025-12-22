#!/usr/bin/env python3
"""Convert PNG icon to Windows ICO format."""

from PIL import Image
import os
from pathlib import Path

def main():
    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    assets_dir = project_root / "assets"
    
    # Open the source image
    img = Image.open(assets_dir / "icon.png")
    
    # Convert to RGBA if necessary
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    
    # Define sizes for Windows ICO (standard sizes)
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    
    # Create resized images
    icons = []
    for size in sizes:
        resized = img.resize(size, Image.Resampling.LANCZOS)
        icons.append(resized)
    
    # Save as ICO with multiple sizes
    ico_path = assets_dir / "icon.ico"
    icons[0].save(
        ico_path,
        format="ICO",
        sizes=[(s[0], s[1]) for s in sizes],
        append_images=icons[1:]
    )
    
    print(f"Successfully created {ico_path}")
    print(f"File size: {os.path.getsize(ico_path)} bytes")


if __name__ == "__main__":
    main()
