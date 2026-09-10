from pathlib import Path
from unittest.mock import patch

import pytest

from localmedia.core import LocalMediaError
from localmedia.images import ImageTools, convert_image, discover_imagemagick, parse_formats

FORMAT_LIST = """
  Format  Module    Mode  Description
     PNG* PNG       rw-   Portable Network Graphics
    JPEG* JPEG      rw-   Joint Photographic Experts Group
     RAW  DNG       r--   Camera raw
     OUT  OUT       -w+   Write only
"""


@pytest.fixture
def image_tools():
    return ImageTools(("magick",), ("magick", "identify"), parse_formats(FORMAT_LIST))


def test_formats_use_actual_read_write_flags():
    formats = parse_formats(FORMAT_LIST)
    assert set(formats) == {"PNG", "JPEG", "RAW", "OUT"}
    assert formats["RAW"].readable and not formats["RAW"].writable
    assert formats["OUT"].writable and not formats["OUT"].readable


def test_new_format_table_without_module_column():
    formats = parse_formats("  PNG* rw- Portable Network Graphics\n  RAW r-- Camera raw")
    assert formats["PNG"].writable
    assert formats["RAW"].readable and not formats["RAW"].writable


def test_missing_imagemagick():
    with patch("localmedia.images.shutil.which", return_value=None):
        with pytest.raises(LocalMediaError, match="ImageMagick not found"):
            discover_imagemagick()


def test_discovery_queries_installed_binary():
    with patch("localmedia.images.shutil.which", return_value="/tools/magick"):
        with patch("localmedia.images.execute", side_effect=["ImageMagick 7", FORMAT_LIST]):
            assert discover_imagemagick().formats["PNG"].writable


def test_safe_paths_resize_and_quality(tmp_path, image_tools):
    source = tmp_path / "photo [1] %02d & name.png"
    source.write_bytes(b"original")
    output = tmp_path / "result with spaces.jpg"
    calls = []

    def execute(args):
        calls.append(args)
        if "identify" in args:
            return "PNG\n"
        Path(args[-1].split(":", 1)[1]).write_bytes(b"converted")
        return ""

    with patch("localmedia.images.execute", side_effect=execute):
        convert_image(image_tools, source, output, "JPEG", quality=80, width=320)
    assert output.read_bytes() == b"converted"
    assert source.read_bytes() == b"original"
    assert "320x>" in calls[-1]
    assert calls[-1][-3:-1] == ["-quality", "80"]
    assert all(str(source) not in args for args in calls)


@pytest.mark.parametrize("same_source", [True, False])
def test_never_overwrites(tmp_path, image_tools, same_source):
    source = tmp_path / "source.png"
    source.write_bytes(b"original")
    output = source if same_source else tmp_path / "exists.png"
    output.write_bytes(b"original")
    with pytest.raises(LocalMediaError, match="already exists"):
        convert_image(image_tools, source, output, "PNG")
    assert output.read_bytes() == b"original"


@pytest.mark.parametrize("detected", ["PNG\nPNG\n", "UNKNOWN\n", ""])
def test_rejects_unsupported_or_multiple_frames(tmp_path, image_tools, detected):
    source = tmp_path / "input"
    source.write_bytes(b"input")
    output = tmp_path / "output.png"
    with patch("localmedia.images.execute", return_value=detected):
        with pytest.raises(LocalMediaError):
            convert_image(image_tools, source, output, "PNG")
    assert not output.exists()


def test_invalid_input_and_backend_failure_leave_no_output(tmp_path, image_tools):
    source = tmp_path / "broken.png"
    source.write_bytes(b"invalid")
    output = tmp_path / "out.png"
    with patch("localmedia.images.execute", side_effect=LocalMediaError("invalid file")):
        with pytest.raises(LocalMediaError, match="invalid file"):
            convert_image(image_tools, source, output, "PNG")
    assert not output.exists()


def test_unsupported_output(tmp_path, image_tools):
    source = tmp_path / "input.png"
    source.touch()
    with pytest.raises(LocalMediaError, match="not writable"):
        convert_image(image_tools, source, tmp_path / "out.raw", "RAW")


def test_output_created_during_conversion_is_preserved(tmp_path, image_tools):
    source, output = tmp_path / "in.png", tmp_path / "out.png"
    source.touch()

    def execute(args):
        if "identify" in args:
            return "PNG\n"
        Path(args[-1].split(":", 1)[1]).write_bytes(b"converted")
        output.write_bytes(b"another process")
        return ""

    with patch("localmedia.images.execute", side_effect=execute):
        with pytest.raises(FileExistsError):
            convert_image(image_tools, source, output, "PNG")
    assert output.read_bytes() == b"another process"
