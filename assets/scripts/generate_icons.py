#!/usr/bin/env python3
"""
Icon Generation Script for Downloadyha GUI

Converts SVG icons to multiple PNG sizes and Windows ICO format.
Requires: pip install cairosvg pillow
"""

import os
from pathlib import Path
from io import BytesIO

try:
    import cairosvg
    from PIL import Image
except ImportError:
    print("ERROR: Required packages not installed.")
    print("Please run: pip install cairosvg pillow")
    exit(1)


# Project paths
SCRIPT_DIR = Path(__file__).parent
ASSETS_DIR = SCRIPT_DIR.parent
ICONS_DIR = ASSETS_DIR / "icons"

# Icon sizes to generate
PNG_SIZES = [16, 32, 48, 64, 128, 256, 512]
ICO_SIZES = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]


def svg_to_png(svg_path: Path, output_path: Path, size: int) -> None:
    """Convert SVG to PNG at specified size."""
    print(f"  → Generating {output_path.name} ({size}x{size})")

    cairosvg.svg2png(
        url=str(svg_path),
        write_to=str(output_path),
        output_width=size,
        output_height=size
    )


def svg_to_ico(svg_path: Path, output_path: Path) -> None:
    """Convert SVG to multi-resolution ICO file."""
    print(f"  → Generating {output_path.name} (multi-resolution)")

    images = []

    for width, height in ICO_SIZES:
        png_data = cairosvg.svg2png(
            url=str(svg_path),
            output_width=width,
            output_height=height
        )
        img = Image.open(BytesIO(png_data))
        images.append(img)

    # Save as ICO with all sizes
    images[0].save(
        str(output_path),
        format='ICO',
        sizes=ICO_SIZES,
        append_images=images[1:]
    )


def generate_all_icons():
    """Generate all icon variants from SVG sources."""
    print("Downloadyha Icon Generator")
    print("=" * 60)

    # Check if SVG files exist
    svg_files = {
        'main': ICONS_DIR / "app_icon.svg",
        'simple': ICONS_DIR / "app_icon_simple.svg"
    }

    for name, svg_path in svg_files.items():
        if not svg_path.exists():
            print(f"\n❌ ERROR: {svg_path} not found!")
            continue

        print(f"\n📦 Processing {svg_path.name}")

        # Generate PNG files at different sizes
        for size in PNG_SIZES:
            output_name = f"app_icon_{name}_{size}.png" if name != 'main' else f"app_icon_{size}.png"
            output_path = ICONS_DIR / output_name

            try:
                svg_to_png(svg_path, output_path, size)
            except Exception as e:
                print(f"  ❌ Failed to generate {output_name}: {e}")

        # Generate ICO file (Windows)
        if name == 'main':
            ico_path = ICONS_DIR / "downloadyha.ico"
            try:
                svg_to_ico(svg_path, ico_path)
            except Exception as e:
                print(f"  ❌ Failed to generate ICO: {e}")

    print("\n" + "=" * 60)
    print("✅ Icon generation complete!")
    print(f"📁 Output directory: {ICONS_DIR}")


if __name__ == "__main__":
    generate_all_icons()
