#!/usr/bin/env python3
"""Tests for Tuck CLI tool."""

import os
import sys
import struct
import subprocess
import tempfile
import pytest

TUCK_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tuck.py")


def run_tuck(*args):
    """Run tuck.py with arguments and return result."""
    result = subprocess.run(
        [sys.executable, TUCK_PATH] + list(args),
        capture_output=True, text=True
    )
    return result


@pytest.fixture
def png_file(tmp_path):
    """Create a minimal fake PNG file for testing."""
    filepath = tmp_path / "test.png"
    # PNG magic + IHDR chunk (simplified)
    data = b"\x89PNG\r\n\x1a\n"  # PNG signature
    # IHDR chunk: length(4) + type(4) + width(4) + height(4) + ...
    width = struct.pack(">I", 100)
    height = struct.pack(">I", 200)
    ihdr_data = width + height + b"\x08\x02\x00\x00\x00"  # 8-bit RGB
    ihdr_length = struct.pack(">I", len(ihdr_data))
    data += ihdr_length + b"IHDR" + ihdr_data
    # Pad to have some more bytes
    data += b"\x00" * 64
    filepath.write_bytes(data)
    return str(filepath)


@pytest.fixture
def jpeg_file(tmp_path):
    """Create a minimal fake JPEG file for testing."""
    filepath = tmp_path / "test.jpg"
    data = b"\xff\xd8\xff\xe0" + b"\x00" * 100
    filepath.write_bytes(data)
    return str(filepath)


@pytest.fixture
def gif_file(tmp_path):
    """Create a minimal fake GIF file for testing."""
    filepath = tmp_path / "test.gif"
    # GIF89a + width(2) + height(2)
    data = b"GIF89a" + struct.pack("<H", 320) + struct.pack("<H", 240) + b"\x00" * 50
    filepath.write_bytes(data)
    return str(filepath)


@pytest.fixture
def bmp_file(tmp_path):
    """Create a minimal fake BMP file for testing."""
    filepath = tmp_path / "test.bmp"
    # BMP header
    data = b"BM" + b"\x00" * 16
    data += struct.pack("<I", 64)  # width at offset 18
    data += struct.pack("<I", 48)  # height at offset 22
    data += b"\x00" * 50
    filepath.write_bytes(data)
    return str(filepath)


@pytest.fixture
def binary_file(tmp_path):
    """Create a generic binary file with known content."""
    filepath = tmp_path / "data.bin"
    data = bytes(range(256)) + b"HELLO WORLD" + bytes(range(256))
    filepath.write_bytes(data)
    return str(filepath)


class TestVersion:
    def test_version(self):
        result = run_tuck("--version")
        assert result.returncode == 0
        assert "1.0.0" in result.stdout


class TestHelp:
    def test_help(self):
        result = run_tuck("--help")
        assert result.returncode == 0
        assert "Tuck" in result.stdout
        assert "view" in result.stdout
        assert "edit" in result.stdout
        assert "find" in result.stdout
        assert "save" in result.stdout
        assert "info" in result.stdout

    def test_no_command(self):
        result = run_tuck()
        assert result.returncode == 0
        assert "view" in result.stdout

    def test_view_help(self):
        result = run_tuck("view", "--help")
        assert result.returncode == 0
        assert "offset" in result.stdout
        assert "length" in result.stdout


class TestView:
    def test_view_png(self, png_file):
        result = run_tuck("view", png_file)
        assert result.returncode == 0
        assert "Hex View" in result.stdout
        assert "89" in result.stdout  # PNG first byte

    def test_view_with_offset(self, binary_file):
        result = run_tuck("view", binary_file, "--offset", "16", "--length", "16")
        assert result.returncode == 0
        assert "00000010" in result.stdout  # offset in hex

    def test_view_with_hex_offset(self, binary_file):
        result = run_tuck("view", binary_file, "--offset", "0x20", "--length", "16")
        assert result.returncode == 0
        assert "00000020" in result.stdout

    def test_view_nonexistent_file(self):
        result = run_tuck("view", "/nonexistent/file.png")
        assert result.returncode != 0
        assert "Error" in result.stderr

    def test_view_offset_past_eof(self, png_file):
        result = run_tuck("view", png_file, "--offset", "999999")
        assert result.returncode != 0
        assert "exceeds" in result.stderr


class TestEdit:
    def test_edit_single_byte(self, binary_file):
        result = run_tuck("edit", binary_file, "0", "FF")
        assert result.returncode == 0
        assert "Edit successful" in result.stdout
        with open(binary_file, "rb") as f:
            assert f.read(1) == b"\xff"

    def test_edit_multiple_bytes(self, binary_file):
        result = run_tuck("edit", binary_file, "0", "DEADBEEF")
        assert result.returncode == 0
        with open(binary_file, "rb") as f:
            assert f.read(4) == b"\xde\xad\xbe\xef"

    def test_edit_hex_offset(self, binary_file):
        result = run_tuck("edit", binary_file, "0x10", "AA")
        assert result.returncode == 0
        with open(binary_file, "rb") as f:
            f.seek(0x10)
            assert f.read(1) == b"\xaa"

    def test_edit_with_0x_prefix_value(self, binary_file):
        result = run_tuck("edit", binary_file, "0", "0xBB")
        assert result.returncode == 0
        with open(binary_file, "rb") as f:
            assert f.read(1) == b"\xbb"

    def test_edit_invalid_hex(self, binary_file):
        result = run_tuck("edit", binary_file, "0", "ZZ")
        assert result.returncode != 0
        assert "Invalid hex" in result.stderr

    def test_edit_odd_length_hex(self, binary_file):
        result = run_tuck("edit", binary_file, "0", "FFF")
        assert result.returncode != 0
        assert "even number" in result.stderr

    def test_edit_past_eof(self, binary_file):
        result = run_tuck("edit", binary_file, "999999", "FF")
        assert result.returncode != 0
        assert "exceeds" in result.stderr

    def test_edit_extends_past_eof(self, binary_file):
        file_size = os.path.getsize(binary_file)
        result = run_tuck("edit", binary_file, str(file_size - 1), "FFFF")
        assert result.returncode != 0
        assert "extend past" in result.stderr


class TestFind:
    def test_find_ascii(self, binary_file):
        result = run_tuck("find", binary_file, "HELLO")
        assert result.returncode == 0
        assert "match" in result.stdout

    def test_find_hex_pattern(self, binary_file):
        result = run_tuck("find", binary_file, "0x48454C4C4F")  # "HELLO" in hex
        assert result.returncode == 0
        assert "match" in result.stdout
        assert "00000100" in result.stdout  # offset 256 in hex

    def test_find_no_match(self, binary_file):
        result = run_tuck("find", binary_file, "ZZZYYYXXX")
        assert result.returncode != 0
        assert "No matches" in result.stdout

    def test_find_max_results(self, binary_file):
        # 0x00 appears multiple times
        result = run_tuck("find", binary_file, "0x0001", "--max-results", "2")
        assert result.returncode == 0

    def test_find_nonexistent_file(self):
        result = run_tuck("find", "/nonexistent", "FF")
        assert result.returncode != 0


class TestSave:
    def test_save_creates_copy(self, binary_file, tmp_path):
        output = str(tmp_path / "output.bin")
        result = run_tuck("save", binary_file, output)
        assert result.returncode == 0
        assert "saved successfully" in result.stdout
        assert os.path.exists(output)
        with open(binary_file, "rb") as f1, open(output, "rb") as f2:
            assert f1.read() == f2.read()

    def test_save_same_file(self, binary_file):
        result = run_tuck("save", binary_file, binary_file)
        assert result.returncode != 0
        assert "same file" in result.stderr

    def test_save_nonexistent_dir(self, binary_file):
        result = run_tuck("save", binary_file, "/nonexistent_dir/output.bin")
        assert result.returncode != 0
        assert "does not exist" in result.stderr

    def test_save_nonexistent_source(self, tmp_path):
        output = str(tmp_path / "output.bin")
        result = run_tuck("save", "/nonexistent", output)
        assert result.returncode != 0


class TestInfo:
    def test_info_png(self, png_file):
        result = run_tuck("info", png_file)
        assert result.returncode == 0
        assert "PNG" in result.stdout
        assert "100" in result.stdout  # width
        assert "200" in result.stdout  # height

    def test_info_jpeg(self, jpeg_file):
        result = run_tuck("info", jpeg_file)
        assert result.returncode == 0
        assert "JPEG" in result.stdout

    def test_info_gif(self, gif_file):
        result = run_tuck("info", gif_file)
        assert result.returncode == 0
        assert "GIF" in result.stdout
        assert "320" in result.stdout  # width
        assert "240" in result.stdout  # height

    def test_info_bmp(self, bmp_file):
        result = run_tuck("info", bmp_file)
        assert result.returncode == 0
        assert "BMP" in result.stdout
        assert "64" in result.stdout  # width
        assert "48" in result.stdout  # height

    def test_info_unknown(self, binary_file):
        result = run_tuck("info", binary_file)
        assert result.returncode == 0
        assert "Unknown" in result.stdout

    def test_info_nonexistent(self):
        result = run_tuck("info", "/nonexistent")
        assert result.returncode != 0


class TestIntegration:
    def test_edit_then_view(self, binary_file):
        """Edit a byte, then verify it shows in view."""
        run_tuck("edit", binary_file, "0", "CAFEBABE")
        result = run_tuck("view", binary_file, "--offset", "0", "--length", "16")
        assert result.returncode == 0
        # The hex dump should contain our written bytes (ca fe ba be)
        output_lower = result.stdout.lower()
        assert "ca" in output_lower
        assert "fe" in output_lower
        assert "ba" in output_lower
        assert "be" in output_lower

    def test_edit_then_save(self, binary_file, tmp_path):
        """Edit bytes, save to new file, verify."""
        run_tuck("edit", binary_file, "0", "DEADBEEF")
        output = str(tmp_path / "saved.bin")
        run_tuck("save", binary_file, output)
        with open(output, "rb") as f:
            assert f.read(4) == b"\xde\xad\xbe\xef"

    def test_find_after_edit(self, binary_file):
        """Edit to insert a pattern, then find it."""
        run_tuck("edit", binary_file, "0", "BAADF00D")
        result = run_tuck("find", binary_file, "0xBAADF00D")
        assert result.returncode == 0
        assert "00000000" in result.stdout
