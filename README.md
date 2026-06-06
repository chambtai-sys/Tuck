# Tuck

**A professional Linux CLI tool for byte-level image editing.**

Tuck allows you to inspect, search, and modify raw bytes in image files directly from the terminal. It provides a colorful hex dump viewer, pattern search, and byte-level editing — all using only the Python standard library.

## Features

- 🔍 **Hex Viewer** — Colorized hex + ASCII dump with offset navigation
- ✏️ **Byte Editor** — Modify bytes at any offset
- 🔎 **Pattern Search** — Find hex or ASCII patterns with context display
- 💾 **Save** — Copy modified files to new locations
- 📋 **File Info** — Identify image types via magic bytes (PNG, JPEG, GIF, BMP, TIFF, WebP, ICO, PSD, etc.)
- 🎨 **Terminal Colors** — Professional, readable output with ANSI colors
- 📦 **Zero Dependencies** — Uses only the Python standard library

## Installation

```bash
# Clone or copy to your system
git clone https://github.com/chambtai-sys/Tuck.git && cd Tuck

# Make executable
chmod +x tuck.py

# Optional: symlink to PATH
sudo ln -s $(pwd)/tuck.py /usr/local/bin/tuck
```

## Usage

### View hex dump

```bash
# View first 512 bytes (default)
./tuck.py view image.png

# View 128 bytes starting at offset 0x10
./tuck.py view image.png --offset 0x10 --length 128

# View with decimal offset
./tuck.py view image.png -o 256 -l 64
```

### Edit bytes

```bash
# Change byte at offset 0 to 0x89
./tuck.py edit image.png 0 89

# Write multiple bytes at offset 0
./tuck.py edit image.png 0 89504E47

# Use hex offset
./tuck.py edit image.png 0x1A FF
```

### Find patterns

```bash
# Search for ASCII string
./tuck.py find image.png IHDR

# Search for hex pattern (0x prefix)
./tuck.py find image.png 0xFFD8FF

# Limit results
./tuck.py find image.png 0xFF --max-results 10
```

### Save file

```bash
# Save a copy (useful after editing)
./tuck.py save image.png modified.png
```

### File info

```bash
# Identify image type and display metadata
./tuck.py info image.png
./tuck.py info photo.jpg
```

## Supported Image Formats (Detection)

| Format   | Magic Bytes               |
|----------|---------------------------|
| PNG      | `89 50 4E 47 0D 0A 1A 0A` |
| JPEG     | `FF D8 FF`                |
| GIF87a   | `47 49 46 38 37 61`       |
| GIF89a   | `47 49 46 38 39 61`       |
| BMP      | `42 4D`                   |
| TIFF (LE)| `49 49 2A 00`             |
| TIFF (BE)| `4D 4D 00 2A`             |
| WebP     | `52 49 46 46 ... 57 45 42 50` |
| ICO      | `00 00 01 00`             |
| PSD      | `38 42 50 53`             |
| JPEG2000 | `00 00 00 0C 6A 50`       |

## Color Coding (Hex View)

- **Green** — Printable ASCII characters (0x20–0x7E)
- **Blue** — Control characters (0x00–0x1F)
- **Yellow** — High bytes (0x80–0xFE)
- **Red** — 0xFF bytes
- **Dim** — Null bytes (0x00)

## Requirements

- Python 3.6+
- Linux terminal with ANSI color support
- No external dependencies

## License

MIT License — see [LICENSE](LICENSE) file for details.
