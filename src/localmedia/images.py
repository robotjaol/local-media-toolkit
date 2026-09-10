from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .core import LocalMediaError


@dataclass(frozen=True)
class ImageFormat:
    name: str
    readable: bool
    writable: bool
    description: str


@dataclass(frozen=True)
class ImageTools:
    convert: tuple[str, ...]
    identify: tuple[str, ...]
    formats: dict[str, ImageFormat]


def execute(args: list[str]) -> str:
    try:
        result = subprocess.run(
            args, capture_output=True, text=True, errors="replace", check=False,
            stdin=subprocess.DEVNULL,
        )
    except OSError as exc:
        raise LocalMediaError(
            f"Cannot start ImageMagick: {exc}. Check installation and PATH."
        ) from exc
    if result.returncode:
        raise LocalMediaError(
            "ImageMagick failed. Check the file, available delegates, output permissions, "
            "and security policy.\n" + (result.stderr.strip() or "No error details returned.")
        )
    return result.stdout


def parse_formats(text: str) -> dict[str, ImageFormat]:
    formats = {}
    for line in text.splitlines():
        match = re.match(
            r"^\s*([A-Z0-9]+)\*?\s+(?:\S+\s+)?([r-][w-][+-])\s+(.+)$", line
        )
        if match:
            name, mode, description = match.groups()
            formats[name] = ImageFormat(name, mode[0] == "r", mode[1] == "w", description)
    return formats


def discover_imagemagick() -> ImageTools:
    magick = shutil.which("magick")
    if magick:
        convert, identify = (magick,), (magick, "identify")
    elif os.name != "nt" and shutil.which("convert") and shutil.which("identify"):
        # Windows convert.exe is a filesystem utility, not ImageMagick.
        convert, identify = (shutil.which("convert"),), (shutil.which("identify"),)
    else:
        raise LocalMediaError(
            "ImageMagick not found. Install ImageMagick, reopen the app, or click "
            "Refresh formats after updating PATH. See docs/IMAGE_CONVERTER.md."
        )
    if "ImageMagick" not in execute([*convert, "-version"]):
        raise LocalMediaError("The detected executable is not ImageMagick.")
    formats = parse_formats(execute([*identify, "-list", "format"]))
    if not any(fmt.writable for fmt in formats.values()):
        raise LocalMediaError("ImageMagick returned no writable formats. Check its installation.")
    return ImageTools(convert, identify, formats)


def supports_quality(fmt: str) -> bool:
    # This is an option mapping, not a claim that these coders are installed.
    return fmt in {"JPEG", "JPG", "JPE", "WEBP", "AVIF", "HEIC", "HEIF", "JP2", "J2K"}


def convert_image(
    tools: ImageTools, source: Path, output: Path, fmt: str, *,
    quality: int | None = None, width: int | None = None, height: int | None = None,
) -> None:
    source, output = source.resolve(), output.resolve()
    if not source.is_file():
        raise LocalMediaError(f"Input file does not exist: {source}")
    capability = tools.formats.get(fmt)
    if not capability or not capability.writable:
        raise LocalMediaError(f"{fmt} is not writable by this ImageMagick installation.")
    if quality is not None and (not supports_quality(fmt) or not 1 <= quality <= 100):
        raise ValueError("Quality must be 1–100 and supported by the selected format.")
    if any(value is not None and value <= 0 for value in (width, height)):
        raise ValueError("Image dimensions must be positive.")
    if source == output or output.exists():
        raise LocalMediaError("Output already exists. Choose a new name; originals are preserved.")
    # A private, literal filename prevents ImageMagick interpreting brackets, %, or @ in paths.
    with tempfile.TemporaryDirectory(prefix="localmedia-image-") as directory:
        staged = Path(directory) / "input"
        shutil.copyfile(source, staged)
        detected = execute([*tools.identify, "-ping", "-format", "%m\n", str(staged)])
        names = detected.splitlines()
        if not names or any(
            name not in tools.formats or not tools.formats[name].readable for name in names
        ):
            raise LocalMediaError("Input format is not readable by this ImageMagick installation.")
        if len(names) != 1:
            raise LocalMediaError(
                "Animated or multi-page input is not supported by this still-image converter. "
                "Export one frame/page first."
            )
        converted = Path(directory) / "output"
        args = [*tools.convert, str(staged), "-auto-orient"]
        if width or height:
            args += ["-resize", f"{width or ''}x{height or ''}>"]
        if quality is not None:
            args += ["-quality", str(quality)]
        execute([*args, f"{fmt}:{converted}"])
        if not converted.is_file() or not converted.stat().st_size:
            raise LocalMediaError("The selected coder did not produce a single image file.")
        # Exclusive creation also protects files created by another process during conversion.
        with output.open("xb") as destination:
            try:
                with converted.open("rb") as result:
                    shutil.copyfileobj(result, destination)
            except OSError:
                destination.close()
                output.unlink(missing_ok=True)
                raise
