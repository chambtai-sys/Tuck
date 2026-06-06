#!/usr/bin/env python3
"""
Tuck - A professional Linux CLI tool for byte-level image editing.
"""

import argparse
import os
import sys
import struct


# ANSI color codes for terminal output
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    BG_DARK = "\033[40m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"


# Magic byte signatures for image type identification
MAGIC_SIGNATURES = [
    (b"\x89PNG\r\n\x1a\n", "PNG", "Portable Network Graphics"),
    (b"\xff\xd8\xff", "JPEG", "Joint Photographic Experts Group"),
    (b"GIF87a", "GIF87a", "Graphics Interchange Format (87a)"),
    (b"GIF89a", "GIF89a", "Graphics Interchange Format (89a)"),
    (b"BM", "BMP", "Windows Bitmap"),
    (b"II\x2a\x00", "TIFF", "Tagged Image File Format (Little Endian)"),
    (b"MM\x00\x2a", "TIFF", "Tagged Image File Format (Big Endian)"),
    (b"RIFF", "WEBP", "WebP Image (RIFF container)"),
    (b"\x00\x00\x01\x00", "ICO", "Windows Icon"),
    (b"\x00\x00\x02\x00", "CUR", "Windows Cursor"),
    (b"\x89HDF", "HDF", "Hierarchical Data Format"),
    (b"8BPS", "PSD", "Adobe Photoshop Document"),
    (b"\x00\x00\x00\x0cjP", "JPEG2000", "JPEG 2000"),
]


def validate_file(filepath):
    """Validate that the file exists and is readable."""
    if not os.path.isfile(filepath):
        sys.stderr.write(f"{Colors.RED}Error:{Colors.RESET} File not found: {filepath}\n")
        sys.exit(1)
    if not os.access(filepath, os.R_OK):
        sys.stderr.write(f"{Colors.RED}Error:{Colors.RESET} File not readable: {filepath}\n")
        sys.exit(1)


def colorize_byte(byte_val):
    """Return a colorized hex string based on byte value."""
    if byte_val == 0x00:
        return f"{Colors.DIM}00{Colors.RESET}"
    elif byte_val == 0xFF:
        return f"{Colors.BRIGHT_RED}ff{Colors.RESET}"
    elif 0x20 <= byte_val <= 0x7E:
        # Printable ASCII range
        return f"{Colors.BRIGHT_GREEN}{byte_val:02x}{Colors.RESET}"
    elif byte_val < 0x20:
        # Control characters
        return f"{Colors.BRIGHT_BLUE}{byte_val:02x}{Colors.RESET}"
    else:
        # High bytes
        return f"{Colors.YELLOW}{byte_val:02x}{Colors.RESET}"


def colorize_ascii(byte_val):
    """Return a colorized ASCII character representation."""
    if 0x20 <= byte_val <= 0x7E:
        return f"{Colors.BRIGHT_GREEN}{chr(byte_val)}{Colors.RESET}"
    else:
        return f"{Colors.DIM}.{Colors.RESET}"


def cmd_view(args):
    """Display a formatted hex + ASCII dump of the image file."""
    filepath = args.file
    validate_file(filepath)

    file_size = os.path.getsize(filepath)
    offset = args.offset if args.offset else 0
    length = args.length if args.length else min(file_size - offset, 512)

    if offset >= file_size:
        sys.stderr.write(f"{Colors.RED}Error:{Colors.RESET} Offset {offset} exceeds file size {file_size}\n")
        sys.exit(1)

    # Clamp length
    length = min(length, file_size - offset)

    with open(filepath, "rb") as f:
        f.seek(offset)
        data = f.read(length)

    # Header
    print(f"{Colors.BOLD}{Colors.CYAN}┌─ Tuck Hex View ──────────────────────────────────────────────────────┐{Colors.RESET}")
    print(f"{Colors.CYAN}│{Colors.RESET} File: {Colors.BRIGHT_YELLOW}{filepath}{Colors.RESET}")
    print(f"{Colors.CYAN}│{Colors.RESET} Size: {Colors.WHITE}{file_size}{Colors.RESET} bytes | "
          f"Showing: {Colors.WHITE}{offset}{Colors.RESET} - {Colors.WHITE}{offset + length - 1}{Colors.RESET} "
          f"({Colors.WHITE}{length}{Colors.RESET} bytes)")
    print(f"{Colors.BOLD}{Colors.CYAN}├──────────┬─────────────────────────────────────────────────┬──────────────────┤{Colors.RESET}")
    print(f"{Colors.CYAN}│{Colors.RESET} {Colors.BOLD}Offset{Colors.RESET}   {Colors.CYAN}│{Colors.RESET}"
          f" {Colors.BOLD}00 01 02 03 04 05 06 07  08 09 0A 0B 0C 0D 0E 0F{Colors.RESET} "
          f"{Colors.CYAN}│{Colors.RESET} {Colors.BOLD}ASCII{Colors.RESET}            {Colors.CYAN}│{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}├──────────┼─────────────────────────────────────────────────┼──────────────────┤{Colors.RESET}")

    # Hex dump rows (16 bytes per line)
    for i in range(0, len(data), 16):
        row = data[i:i + 16]
        addr = offset + i

        # Offset column
        offset_str = f"{Colors.MAGENTA}{addr:08x}{Colors.RESET}"

        # Hex columns
        hex_parts = []
        for j, byte in enumerate(row):
            hex_parts.append(colorize_byte(byte))
        # Pad if row is less than 16 bytes
        while len(hex_parts) < 16:
            hex_parts.append("  ")

        # Add spacing between 8-byte groups
        hex_left = " ".join(hex_parts[:8])
        hex_right = " ".join(hex_parts[8:])
        hex_str = f"{hex_left}  {hex_right}"

        # ASCII column
        ascii_parts = []
        for byte in row:
            ascii_parts.append(colorize_ascii(byte))
        ascii_str = "".join(ascii_parts)
        # Pad ASCII
        padding = " " * (16 - len(row))

        print(f"{Colors.CYAN}│{Colors.RESET} {offset_str} {Colors.CYAN}│{Colors.RESET} {hex_str} {Colors.CYAN}│{Colors.RESET} {ascii_str}{padding} {Colors.CYAN}│{Colors.RESET}")

    print(f"{Colors.BOLD}{Colors.CYAN}└──────────┴─────────────────────────────────────────────────┴──────────────────┘{Colors.RESET}")


def cmd_edit(args):
    """Change the byte at a specific offset."""
    filepath = args.file
    validate_file(filepath)

    offset = args.offset
    hex_value = args.hex_value

    # Parse hex value(s)
    hex_value = hex_value.replace("0x", "").replace("0X", "").replace(" ", "")
    if len(hex_value) % 2 != 0:
        sys.stderr.write(f"{Colors.RED}Error:{Colors.RESET} Hex value must have even number of digits\n")
        sys.exit(1)

    try:
        new_bytes = bytes.fromhex(hex_value)
    except ValueError:
        sys.stderr.write(f"{Colors.RED}Error:{Colors.RESET} Invalid hex value: {hex_value}\n")
        sys.exit(1)

    file_size = os.path.getsize(filepath)
    if offset >= file_size:
        sys.stderr.write(f"{Colors.RED}Error:{Colors.RESET} Offset {offset} exceeds file size {file_size}\n")
        sys.exit(1)

    if offset + len(new_bytes) > file_size:
        sys.stderr.write(f"{Colors.RED}Error:{Colors.RESET} Edit would extend past end of file\n")
        sys.exit(1)

    # Read original bytes for display
    with open(filepath, "rb") as f:
        f.seek(offset)
        old_bytes = f.read(len(new_bytes))

    # Write new bytes
    with open(filepath, "r+b") as f:
        f.seek(offset)
        f.write(new_bytes)

    print(f"{Colors.BOLD}{Colors.GREEN}✓ Edit successful{Colors.RESET}")
    print(f"  File:   {Colors.BRIGHT_YELLOW}{filepath}{Colors.RESET}")
    print(f"  Offset: {Colors.MAGENTA}0x{offset:08x}{Colors.RESET} ({offset})")
    print(f"  Before: {Colors.RED}{old_bytes.hex()}{Colors.RESET}")
    print(f"  After:  {Colors.GREEN}{new_bytes.hex()}{Colors.RESET}")


def cmd_find(args):
    """Search for hex or ASCII patterns in the image."""
    filepath = args.file
    validate_file(filepath)

    pattern_str = args.pattern
    max_results = args.max_results

    # Determine if pattern is hex or ASCII
    is_hex = False
    if pattern_str.startswith("0x") or pattern_str.startswith("0X"):
        is_hex = True
        pattern_str = pattern_str[2:]

    if is_hex or all(c in "0123456789abcdefABCDEF" for c in pattern_str.replace(" ", "")):
        # Try to parse as hex
        clean_hex = pattern_str.replace(" ", "")
        if len(clean_hex) % 2 == 0:
            try:
                pattern = bytes.fromhex(clean_hex)
                is_hex = True
            except ValueError:
                pattern = pattern_str.encode("utf-8")
        else:
            pattern = pattern_str.encode("utf-8")
    else:
        pattern = pattern_str.encode("utf-8")

    with open(filepath, "rb") as f:
        data = f.read()

    print(f"{Colors.BOLD}{Colors.CYAN}┌─ Tuck Pattern Search ───────────────────────────────────┐{Colors.RESET}")
    if is_hex:
        print(f"{Colors.CYAN}│{Colors.RESET} Pattern (hex): {Colors.BRIGHT_YELLOW}{pattern.hex()}{Colors.RESET}")
    else:
        print(f"{Colors.CYAN}│{Colors.RESET} Pattern (ASCII): {Colors.BRIGHT_YELLOW}{pattern_str}{Colors.RESET} "
              f"(hex: {pattern.hex()})")
    print(f"{Colors.CYAN}│{Colors.RESET} File: {Colors.WHITE}{filepath}{Colors.RESET} ({len(data)} bytes)")
    print(f"{Colors.BOLD}{Colors.CYAN}├──────────────────────────────────────────────────────────────────────────┤{Colors.RESET}")

    # Search
    results = []
    start = 0
    while True:
        idx = data.find(pattern, start)
        if idx == -1:
            break
        results.append(idx)
        if len(results) >= max_results:
            break
        start = idx + 1

    if not results:
        print(f"{Colors.CYAN}│{Colors.RESET} {Colors.YELLOW}No matches found.{Colors.RESET}")
    else:
        print(f"{Colors.CYAN}│{Colors.RESET} Found {Colors.GREEN}{len(results)}{Colors.RESET} match(es):")
        print(f"{Colors.CYAN}│{Colors.RESET}")
        for i, offset in enumerate(results, 1):
            # Show context (8 bytes before and after)
            ctx_start = max(0, offset - 8)
            ctx_end = min(len(data), offset + len(pattern) + 8)
            context = data[ctx_start:ctx_end]

            ctx_hex = ""
            for j, byte in enumerate(context):
                actual_offset = ctx_start + j
                if offset <= actual_offset < offset + len(pattern):
                    ctx_hex += f"{Colors.BRIGHT_RED}{byte:02x}{Colors.RESET} "
                else:
                    ctx_hex += f"{Colors.DIM}{byte:02x}{Colors.RESET} "

            print(f"{Colors.CYAN}│{Colors.RESET}  [{i}] Offset: {Colors.MAGENTA}0x{offset:08x}{Colors.RESET} ({offset})")
            print(f"{Colors.CYAN}│{Colors.RESET}      Context: {ctx_hex}")

    print(f"{Colors.BOLD}{Colors.CYAN}└──────────────────────────────────────────────────────────────────────────┘{Colors.RESET}")

    if not results:
        sys.exit(1)


def cmd_save(args):
    """Save the file bytes to a new output file."""
    filepath = args.file
    output = args.output
    validate_file(filepath)

    if os.path.abspath(filepath) == os.path.abspath(output):
        sys.stderr.write(f"{Colors.RED}Error:{Colors.RESET} Source and destination are the same file\n")
        sys.exit(1)

    # Check if output directory exists
    output_dir = os.path.dirname(output)
    if output_dir and not os.path.isdir(output_dir):
        sys.stderr.write(f"{Colors.RED}Error:{Colors.RESET} Output directory does not exist: {output_dir}\n")
        sys.exit(1)

    with open(filepath, "rb") as f:
        data = f.read()

    with open(output, "wb") as f:
        f.write(data)

    file_size = len(data)
    print(f"{Colors.BOLD}{Colors.GREEN}✓ File saved successfully{Colors.RESET}")
    print(f"  Source:      {Colors.WHITE}{filepath}{Colors.RESET}")
    print(f"  Destination: {Colors.BRIGHT_YELLOW}{output}{Colors.RESET}")
    print(f"  Size:        {Colors.WHITE}{file_size}{Colors.RESET} bytes")


def cmd_info(args):
    """Identify the image type by reading magic bytes."""
    filepath = args.file
    validate_file(filepath)

    file_size = os.path.getsize(filepath)

    with open(filepath, "rb") as f:
        header = f.read(32)

    # Identify type
    detected_type = None
    detected_desc = None
    for signature, type_name, description in MAGIC_SIGNATURES:
        if header[:len(signature)] == signature:
            detected_type = type_name
            detected_desc = description
            break

    # Special check for WEBP (needs RIFF + WEBP check)
    if detected_type == "WEBP":
        if len(header) >= 12 and header[8:12] == b"WEBP":
            detected_desc = "WebP Image"
        else:
            detected_type = "RIFF"
            detected_desc = "RIFF Container (non-WebP)"

    print(f"{Colors.BOLD}{Colors.CYAN}┌─ Tuck File Info ───────────────────────────────────────────────────────┐{Colors.RESET}")
    print(f"{Colors.CYAN}│{Colors.RESET} File: {Colors.BRIGHT_YELLOW}{filepath}{Colors.RESET}")
    print(f"{Colors.CYAN}│{Colors.RESET} Size: {Colors.WHITE}{file_size}{Colors.RESET} bytes ({file_size / 1024:.2f} KB)")
    print(f"{Colors.CYAN}├──────────────────────────────────────────────────────────────────────────┤{Colors.RESET}")

    if detected_type:
        print(f"{Colors.CYAN}│{Colors.RESET} Type:        {Colors.BRIGHT_GREEN}{detected_type}{Colors.RESET}")
        print(f"{Colors.CYAN}│{Colors.RESET} Description: {Colors.WHITE}{detected_desc}{Colors.RESET}")
    else:
        print(f"{Colors.CYAN}│{Colors.RESET} Type:        {Colors.YELLOW}Unknown{Colors.RESET}")
        print(f"{Colors.CYAN}│{Colors.RESET} Description: {Colors.DIM}Could not identify image format{Colors.RESET}")

    # Show magic bytes
    magic_display = " ".join(f"{b:02x}" for b in header[:16])
    print(f"{Colors.CYAN}│{Colors.RESET} Magic bytes: {Colors.MAGENTA}{magic_display}{Colors.RESET}")

    # Additional info for known types
    if detected_type == "PNG" and len(header) >= 24:
        width = struct.unpack(">I", header[16:20])[0]
        height = struct.unpack(">I", header[20:24])[0]
        print(f"{Colors.CYAN}│{Colors.RESET} Dimensions:  {Colors.WHITE}{width} x {height}{Colors.RESET}")
    elif detected_type == "GIF87a" or detected_type == "GIF89a":
        if len(header) >= 10:
            width = struct.unpack("<H", header[6:8])[0]
            height = struct.unpack("<H", header[8:10])[0]
            print(f"{Colors.CYAN}│{Colors.RESET} Dimensions:  {Colors.WHITE}{width} x {height}{Colors.RESET}")
    elif detected_type == "BMP" and len(header) >= 26:
        width = struct.unpack("<I", header[18:22])[0]
        height = struct.unpack("<I", header[22:26])[0]
        print(f"{Colors.CYAN}│{Colors.RESET} Dimensions:  {Colors.WHITE}{width} x {height}{Colors.RESET}")

    print(f"{Colors.BOLD}{Colors.CYAN}└──────────────────────────────────────────────────────────────────────────┘{Colors.RESET}")


def main():
    parser = argparse.ArgumentParser(
        prog="tuck",
        description=f"{Colors.BOLD}{Colors.CYAN}Tuck{Colors.RESET} — A professional byte-level image editing tool for Linux.",
        epilog=f"Examples:\n"
               f"  tuck view image.png\n"
               f"  tuck view image.png --offset 0x10 --length 128\n"
               f"  tuck edit image.png 0 89504E47\n"
               f"  tuck find image.png IHDR\n"
               f"  tuck find image.png 0xFFD8FF\n"
               f"  tuck save image.png modified.png\n"
               f"  tuck info image.png\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--version", action="version", version="%(prog)s 1.0.0"
    )

    subparsers = parser.add_subparsers(
        title="commands",
        dest="command",
        metavar="<command>",
    )

    # view command
    view_parser = subparsers.add_parser(
        "view",
        help="Display a formatted hex + ASCII dump of the file",
        description="Display a formatted, colorized hex dump with ASCII representation.",
    )
    view_parser.add_argument("file", help="Path to the image file")
    view_parser.add_argument(
        "-o", "--offset", type=lambda x: int(x, 0), default=0,
        help="Starting byte offset (supports hex with 0x prefix)",
    )
    view_parser.add_argument(
        "-l", "--length", type=lambda x: int(x, 0), default=None,
        help="Number of bytes to display (default: 512)",
    )

    # edit command
    edit_parser = subparsers.add_parser(
        "edit",
        help="Change byte(s) at a specific offset",
        description="Modify one or more bytes at a given offset in the file.",
    )
    edit_parser.add_argument("file", help="Path to the image file")
    edit_parser.add_argument(
        "offset", type=lambda x: int(x, 0),
        help="Byte offset to edit (supports hex with 0x prefix)",
    )
    edit_parser.add_argument(
        "hex_value",
        help="New hex value(s) to write (e.g., 'FF' or '89504E47')",
    )

    # find command
    find_parser = subparsers.add_parser(
        "find",
        help="Search for hex or ASCII patterns in the file",
        description="Search for a byte pattern (hex or ASCII) within the file.",
    )
    find_parser.add_argument("file", help="Path to the image file")
    find_parser.add_argument(
        "pattern",
        help="Pattern to search for (hex with 0x prefix, or ASCII string)",
    )
    find_parser.add_argument(
        "-m", "--max-results", type=int, default=50,
        help="Maximum number of results to display (default: 50)",
    )

    # save command
    save_parser = subparsers.add_parser(
        "save",
        help="Save the file bytes to a new output file",
        description="Copy the file to a new location (useful after editing).",
    )
    save_parser.add_argument("file", help="Path to the source file")
    save_parser.add_argument("output", help="Path to the output file")

    # info command
    info_parser = subparsers.add_parser(
        "info",
        help="Identify image type by reading magic bytes",
        description="Identify the image format by inspecting the file's magic bytes.",
    )
    info_parser.add_argument("file", help="Path to the image file")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    commands = {
        "view": cmd_view,
        "edit": cmd_edit,
        "find": cmd_find,
        "save": cmd_save,
        "info": cmd_info,
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()
