import shutil

import pytest

from localmedia.core import LocalMediaError
from localmedia.images import convert_image, discover_imagemagick, execute


@pytest.fixture
def tools():
    if not shutil.which("magick") and not shutil.which("identify"):
        pytest.skip("ImageMagick is not installed")
    return discover_imagemagick()


def test_real_conversion_resize_and_invalid_file(tmp_path, tools):
    if not tools.formats.get("PNG") or not tools.formats["PNG"].writable:
        pytest.skip("PNG writer unavailable")
    source = tmp_path / "source with spaces.ppm"
    source.write_bytes(b"P6\n4 2\n255\n" + bytes([255, 0, 0]) * 8)
    original = source.read_bytes()
    output = tmp_path / "converted image.png"
    convert_image(tools, source, output, "PNG", width=2)
    assert execute([*tools.identify, "-format", "%m %wx%h", str(output)]) == "PNG 2x1"
    assert source.read_bytes() == original
    invalid = tmp_path / "invalid.png"
    invalid.write_text("This is not an image")
    with pytest.raises(LocalMediaError):
        convert_image(tools, invalid, tmp_path / "failed.png", "PNG")
    assert not (tmp_path / "failed.png").exists()


def test_real_special_filename_quality_and_animation(tmp_path, tools):
    if not all(name in tools.formats and tools.formats[name].writable for name in ("JPEG", "GIF")):
        pytest.skip("JPEG/GIF writer unavailable")
    source = tmp_path / "photo [1] %02d & spaces.ppm"
    source.write_bytes(b"P6\n4 2\n255\n" + bytes([0, 128, 255]) * 8)
    output = tmp_path / "result with spaces.jpeg"
    convert_image(tools, source, output, "JPEG", quality=75, width=100)
    assert execute([*tools.identify, "-format", "%m %wx%h", str(output)]) == "JPEG 4x2"
    animation = tmp_path / "animated.gif"
    execute([*tools.convert, "-size", "2x2", "xc:red", "xc:blue", str(animation)])
    with pytest.raises(LocalMediaError, match="multi-page"):
        convert_image(tools, animation, tmp_path / "still.jpeg", "JPEG")
