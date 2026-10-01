#!/usr/bin/env python3
"""
Icon Generation Script for Downloadyha GUI

Generates highly polished native PNG and multi-resolution ICO files
for the Downloadyha Desktop application using only built-in Python and Pillow.
Requires: pip install pillow
"""

import math
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFilter
except ImportError:
    print("ERROR: Required package not installed.")
    print("Please run: pip install pillow")
    exit(1)


# Project paths
SCRIPT_DIR = Path(__file__).parent
ASSETS_DIR = SCRIPT_DIR.parent
ICONS_DIR = ASSETS_DIR / "icons"
GUI_RESOURCES_DIR = ASSETS_DIR.parent / "src" / "downloadyha_gui" / "resources"

# Icon sizes to generate
PNG_SIZES = [16, 32, 48, 64, 128, 256, 512]
ICO_SIZES = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]


def create_linear_gradient(size, start_color, mid_color, end_color):
    """Create a high-res diagonal linear gradient surface."""
    w, h = size
    gradient = Image.new("RGBA", size)
    draw = ImageDraw.Draw(gradient)

    # Diagonal max distance
    max_dist = math.sqrt(w * w + h * h)

    # Precompute for speed
    r1, g1, b1 = start_color
    r2, g2, b2 = mid_color
    r3, g3, b3 = end_color

    # We will draw diagonal lines to create the gradient
    for y in range(h):
        for x in range(w):
            # Diagonal progress 0.0 to 1.0
            t = (x + y) / (w + h)

            if t < 0.5:
                # Interpolate start to mid
                p = t * 2.0
                r = int(r1 + (r2 - r1) * p)
                g = int(g1 + (g2 - g1) * p)
                b = int(b1 + (b2 - b1) * p)
            else:
                # Interpolate mid to end
                p = (t - 0.5) * 2.0
                r = int(r2 + (r3 - r2) * p)
                g = int(g2 + (g3 - g2) * p)
                b = int(b2 + (b3 - b2) * p)

            gradient.putpixel((x, y), (r, g, b, 255))

    return gradient


def draw_rounded_rectangle(size, bounds, radius, color):
    """Draw a rounded rectangle with antialiased edges on a transparent canvas."""
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle(bounds, radius=radius, fill=color)
    return img


def draw_polygon(size, points, color):
    """Draw a polygon on a transparent canvas."""
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.polygon(points, fill=color)
    return img


def generate_master_icon():
    """
    Generate a high-resolution 2048x2048 master icon.
    This master image will be supersampled and scaled down for perfect edges.
    """
    SIZE = 2048
    master = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))

    # Theme colors
    CYAN = (0, 210, 255)
    PURPLE = (155, 81, 224)
    MAGENTA = (220, 80, 255)

    # 1. Background Cyber Gradient Squircle
    print("  ... Drawing Gradient Background")
    gradient_bg = create_linear_gradient((SIZE, SIZE), CYAN, PURPLE, MAGENTA)
    bg_bounds = (128, 128, SIZE - 128, SIZE - 128)
    bg_radius = 440

    bg_mask = Image.new("L", (SIZE, SIZE), 0)
    draw_bg_mask = ImageDraw.Draw(bg_mask)
    draw_bg_mask.rounded_rectangle(bg_bounds, radius=bg_radius, fill=255)

    # Apply mask to gradient
    app_bg = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    app_bg.paste(gradient_bg, (0, 0), mask=bg_mask)

    master.alpha_composite(app_bg)

    # 2. Central Play Media Card (White/Frosted)
    print("  ... Drawing Media Card")
    card_bounds = (460, 460, SIZE - 460, SIZE - 460)
    card_radius = 240

    # Card drop shadow
    shadow = draw_rounded_rectangle((SIZE, SIZE), card_bounds, card_radius, (0, 0, 0, 90))
    shadow = shadow.filter(ImageFilter.GaussianBlur(40))
    master.alpha_composite(shadow)

    # Card surface
    card = draw_rounded_rectangle((SIZE, SIZE), card_bounds, card_radius, (255, 255, 255, 245))
    master.alpha_composite(card)

    # 3. Dynamic Download Arrow + Tray inside Card
    print("  ... Drawing Download Arrow")
    arrow_color = PURPLE

    arrow_img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    arrow_draw = ImageDraw.Draw(arrow_img)

    # Arrow Shaft
    shaft_bounds = (SIZE//2 - 90, SIZE//2 - 280, SIZE//2 + 90, SIZE//2 + 100)
    arrow_draw.rounded_rectangle(shaft_bounds, radius=30, fill=(255, 255, 255, 255))

    # Arrow Head
    center_x = SIZE // 2
    head_points = [
        (center_x - 300, SIZE // 2 + 50),
        (center_x + 300, SIZE // 2 + 50),
        (center_x, SIZE // 2 + 350)
    ]
    # Draw arrow head carefully
    arrow_draw.polygon(head_points, fill=(255, 255, 255, 255))

    # Download Tray
    tray_bounds = (center_x - 320, SIZE // 2 + 420, center_x + 320, SIZE // 2 + 520)
    arrow_draw.rounded_rectangle(tray_bounds, radius=50, fill=(255, 255, 255, 255))

    # Cutout or gradient fill arrow? Let's use the main gradient!
    gradient_arrow = create_linear_gradient((SIZE, SIZE), CYAN, PURPLE, MAGENTA)

    # Alpha mask the gradient onto the arrow shape
    arrow_mask = arrow_img.split()[3]
    arrow_colored = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    arrow_colored.paste(gradient_arrow, (0, 0), mask=arrow_mask)

    master.alpha_composite(arrow_colored)

    return master


def generate_all_icons():
    """Generate all icon variants using Pillow."""
    print("Downloadyha High-Res Icon Generator")
    print("=" * 60)

    ICONS_DIR.mkdir(parents=True, exist_ok=True)
    GUI_RESOURCES_DIR.mkdir(parents=True, exist_ok=True)

    print("[+] Generating 2048x2048 Master Icon (Supersampling)")
    master_icon = generate_master_icon()

    print("\n[+] Exporting PNG sizes...")
    for size in PNG_SIZES:
        output_name = f"app_icon_{size}.png"
        output_path = ICONS_DIR / output_name

        # High quality downsampling
        resized = master_icon.resize((size, size), Image.Resampling.LANCZOS)
        resized.save(output_path, "PNG")
        print(f"  -> Saved {output_name} ({size}x{size})")

    print("\n[+] Exporting multi-resolution ICO files...")
    ico_images = []
    for w, h in ICO_SIZES:
        resized = master_icon.resize((w, h), Image.Resampling.LANCZOS)
        ico_images.append(resized)

    # Save main ICO
    ico_path = ICONS_DIR / "downloadyha.ico"
    ico_images[0].save(
        ico_path,
        format='ICO',
        sizes=ICO_SIZES,
        append_images=ico_images[1:]
    )
    print(f"  -> Saved {ico_path.name}")

    # Save a copy to GUI resources for the application window
    app_ico = GUI_RESOURCES_DIR / "icon.ico"
    ico_images[0].save(
        app_ico,
        format='ICO',
        sizes=ICO_SIZES,
        append_images=ico_images[1:]
    )
    print(f"  -> Saved {app_ico.name} (GUI Resources)")

    print("\n" + "=" * 60)
    print("[SUCCESS] Icon generation complete!")
    print(f"Icons directory: {ICONS_DIR}")


if __name__ == "__main__":
    generate_all_icons()
