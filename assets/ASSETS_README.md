# Downloadyha GUI Assets

This directory contains visual assets and resources for a potential Downloadyha Desktop GUI application.

## Directory Structure

```
assets/
├── icons/              # Application icons and UI elements
│   ├── app_icon.svg           # Full featured app icon with play + download
│   └── app_icon_simple.svg    # Minimalist circular download arrow
├── logos/              # Branding and logo files
│   └── logo_text.svg          # Text logo with gradient
├── placeholders/       # Placeholder images
│   └── thumbnail_placeholder.svg  # Video thumbnail placeholder
└── ASSETS_README.md    # This file
```

## Color Scheme

The Downloadyha brand uses a modern cyberpunk-inspired color palette:

| Color Name      | Hex Code  | RGB              | Usage                           |
|-----------------|-----------|------------------|---------------------------------|
| Electric Cyan   | `#00D2FF` | `rgb(0,210,255)` | Primary brand color, highlights |
| Cyber Purple    | `#9B51E0` | `rgb(155,81,224)`| Secondary accent, mid-tones     |
| Neon Magenta    | `#DC50FF` | `rgb(220,80,255)`| Gradient end, call-to-actions   |
| Emerald Green   | `#2ECC71` | `rgb(46,204,113)`| Success states                  |
| Amber Yellow    | `#F1C40F` | `rgb(241,196,15)`| Warnings, metadata              |
| Crimson Red     | `#E74C3C` | `rgb(231,76,60)` | Errors, destructive actions     |

## Icons Provided

### 1. **app_icon.svg** (512x512)
Full-featured application icon with:
- Rounded square background with gradient (Cyan → Purple → Magenta)
- Video play symbol (representing YouTube)
- Download arrow pointing down
- Modern, recognizable design suitable for desktop shortcuts

**Use cases:** Desktop shortcuts, taskbar, app switcher, installer

### 2. **app_icon_simple.svg** (512x512)
Minimalist circular icon with:
- Circular gradient background
- Bold download arrow in white
- Cleaner design for smaller sizes

**Use cases:** System tray, small UI elements, notifications

## Logo Files

### **logo_text.svg** (800x200)
Horizontal brand logo with:
- "Downloadyha" text with gradient fill
- Tagline: "Fast & Beautiful YouTube Downloader"
- Suitable for splash screens and about dialogs

## Placeholder Graphics

### **thumbnail_placeholder.svg** (320x180)
Video thumbnail placeholder (16:9 aspect ratio) with:
- Dark gradient background
- Play icon overlay
- Video camera icon
- Used in download queue when thumbnail unavailable

## Converting SVG to Other Formats

### Python (using cairosvg)
```python
import cairosvg

# Convert SVG to PNG at different sizes
sizes = [16, 32, 48, 64, 128, 256, 512]

for size in sizes:
    cairosvg.svg2png(
        url='assets/icons/app_icon.svg',
        write_to=f'assets/icons/app_icon_{size}.png',
        output_width=size,
        output_height=size
    )
```

### Command Line (using Inkscape)
```bash
# Single conversion
inkscape app_icon.svg --export-type=png --export-width=512 -o app_icon_512.png

# Batch conversion for multiple sizes
for size in 16 32 48 64 128 256 512; do
    inkscape app_icon.svg --export-type=png --export-width=$size -o app_icon_${size}.png
done
```

### Command Line (using ImageMagick)
```bash
# Convert SVG to PNG
convert -background none app_icon.svg -resize 512x512 app_icon_512.png

# Create ICO file with multiple resolutions (Windows)
convert app_icon.svg -background none \
    \( -clone 0 -resize 16x16 \) \
    \( -clone 0 -resize 32x32 \) \
    \( -clone 0 -resize 48x48 \) \
    \( -clone 0 -resize 64x64 \) \
    \( -clone 0 -resize 128x128 \) \
    \( -clone 0 -resize 256x256 \) \
    -delete 0 downloadyha.ico
```

## Creating Windows ICO Files

For Windows desktop applications, you need a multi-resolution ICO file:

### Using Python (Pillow)
```python
from PIL import Image
import cairosvg
from io import BytesIO

def svg_to_ico(svg_path, ico_path):
    sizes = [(16,16), (32,32), (48,48), (64,64), (128,128), (256,256)]
    images = []
    
    for size in sizes:
        png_data = cairosvg.svg2png(
            url=svg_path,
            output_width=size[0],
            output_height=size[1]
        )
        img = Image.open(BytesIO(png_data))
        images.append(img)
    
    images[0].save(
        ico_path,
        format='ICO',
        sizes=sizes,
        append_images=images[1:]
    )

svg_to_ico('assets/icons/app_icon.svg', 'assets/icons/downloadyha.ico')
```

## GUI Framework Recommendations

### For Python Desktop GUI:

1. **PyQt6 / PySide6** (Recommended)
   - Professional, native-looking UI
   - Cross-platform (Windows, macOS, Linux)
   - Excellent documentation
   - Good integration with existing Python codebase

2. **Tkinter + ttkbootstrap**
   - Built into Python
   - Lightweight
   - Modern themes via ttkbootstrap
   - Easier learning curve

3. **Electron + Python Backend**
   - Web technologies (HTML/CSS/JavaScript)
   - Modern UI possibilities
   - Larger bundle size
   - Python runs as backend service

### Icon Integration Example (PyQt6)

```python
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtGui import QIcon
import sys

class DownloadyhaWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Downloadyha")
        self.setWindowIcon(QIcon('assets/icons/app_icon_512.png'))
        self.setGeometry(100, 100, 800, 600)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DownloadyhaWindow()
    window.show()
    sys.exit(app.exec())
```

## Icon Resources & Tools

### Free Icon Libraries (for additional UI icons)
- **Lucide Icons**: https://lucide.dev/ (Modern, consistent, MIT licensed)
- **Heroicons**: https://heroicons.com/ (Tailwind CSS icons, MIT licensed)
- **Feather Icons**: https://feathericons.com/ (Minimalist, MIT licensed)
- **Phosphor Icons**: https://phosphoricons.com/ (Flexible, MIT licensed)

### Design Tools
- **Figma**: https://figma.com (Web-based design tool)
- **Inkscape**: https://inkscape.org/ (Free SVG editor)
- **GIMP**: https://gimp.org/ (Free image editor)
- **Photopea**: https://photopea.com/ (Web-based Photoshop alternative)

## Unicode/Emoji Fallbacks

If generating images is not feasible, use these Unicode symbols as placeholders:

```python
ICONS = {
    'download': '⬇️',      # or '💾' or '📥'
    'video': '🎬',         # or '🎥' or '📹'
    'audio': '🎵',         # or '🎧' or '🔊'
    'folder': '📁',        # or '🗂️'
    'playlist': '📑',      # or '🎶'
    'success': '✅',       # or '✔️'
    'error': '❌',         # or '⚠️'
    'processing': '⚙️',   # or '🔄' or '⏳'
    'play': '▶️',          # or '▷'
    'settings': '⚙️',     # or '🔧'
}
```

## ASCII Art Logo (Terminal Fallback)

The project already includes ASCII art in `src/downloadyha/ui.py`:

```
    ____                      __                 ____  __          
   / __ \____ _      ______  / /___  ____ _____ / / / / /_  ____ _ 
  / / / / __ \ \ /\ / / __ \/ / __ \/ __ `/ __  / /_/ / __ \/ __ `/
 / /_/ / /_/ /\ V  V / / / / / /_/ / /_/ / /_/ / __  / / / / /_/ / 
/_____/\____/  \_/\_/_/ /_/_/\____/\__,_/\__,_/_/ /_/_/ /_/\__,_/  
```

## Next Steps for GUI Development

1. **Choose Framework**: Select PyQt6/PySide6 for professional desktop app
2. **Generate PNG Icons**: Convert SVGs to multiple PNG sizes
3. **Create ICO File**: Generate `downloadyha.ico` for Windows
4. **Design UI Mockups**: Create wireframes for main window, settings, queue
5. **Implement Core UI**: Main window with download queue and progress
6. **Integrate Backend**: Connect UI to existing `downloadyha` CLI logic
7. **Package Application**: Use PyInstaller with icon bundling

## License

These assets follow the same MIT License as the Downloadyha project.

---

**Author**: Ahmed Tarek Zaher  
**Project**: Downloadyha  
**Created**: 2026-10-01
