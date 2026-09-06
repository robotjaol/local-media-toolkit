from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from .utils import parse_bitrate


class LocalMediaError(RuntimeError):
    pass


@dataclass(frozen=True)
class Toolchain:
    ffmpeg: str
    ffprobe: str


def find_toolchain() -> Toolchain:
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        raise LocalMediaError(
            "FFmpeg/FFprobe were not found in PATH. Install FFmpeg, reopen the terminal, "
            "then run `localmedia doctor`."
        )
    return Toolchain(ffmpeg=ffmpeg, ffprobe=ffprobe)


def run(cmd: Sequence[str], *, capture: bool = False) -> subprocess.CompletedProcess[str]:
    kwargs = {
        "text": True,
        "check": False,
    }
    if capture:
        kwargs.update({"stdout": subprocess.PIPE, "stderr": subprocess.PIPE})
    proc = subprocess.run(list(cmd), **kwargs)  # noqa: S603
    if proc.returncode != 0:
        detail = (proc.stderr or "").strip() if capture else ""
        raise LocalMediaError(detail or f"Command failed with exit code {proc.returncode}")
    return proc


def probe(path: Path) -> dict:
    tools = find_toolchain()
    proc = run(
        [
            tools.ffprobe,
            "-v",
            "error",
            "-show_format",
            "-show_streams",
            "-of",
            "json",
            str(path),
        ],
        capture=True,
    )
    return json.loads(proc.stdout)


def duration_seconds(path: Path) -> float:
    data = probe(path)
    raw = data.get("format", {}).get("duration")
    if raw is None:
        raise LocalMediaError("Could not determine input duration")
    duration = float(raw)
    if duration <= 0:
        raise LocalMediaError("Input duration must be positive")
    return duration


def codec_args(codec: str, crf: int, preset: str) -> list[str]:
    mapping = {
        "h264": ["-c:v", "libx264", "-preset", preset, "-crf", str(crf)],
        "h265": ["-c:v", "libx265", "-preset", preset, "-crf", str(crf)],
        "av1": ["-c:v", "libsvtav1", "-preset", "8", "-crf", str(crf)],
    }
    try:
        return mapping[codec]
    except KeyError as exc:
        raise ValueError(f"Unsupported codec: {codec}") from exc


def overwrite_args(overwrite: bool) -> list[str]:
    return ["-y"] if overwrite else ["-n"]


def convert(input_path: Path, output: Path, *, overwrite: bool = False) -> None:
    tools = find_toolchain()
    run([tools.ffmpeg, *overwrite_args(overwrite), "-i", str(input_path), str(output)])


def compress(
    input_path: Path,
    output: Path,
    *,
    codec: str = "h264",
    crf: int = 28,
    preset: str = "medium",
    audio_bitrate: str = "128k",
    overwrite: bool = False,
) -> None:
    tools = find_toolchain()
    run(
        [
            tools.ffmpeg,
            *overwrite_args(overwrite),
            "-i",
            str(input_path),
            *codec_args(codec, crf, preset),
            "-c:a",
            "aac",
            "-b:a",
            audio_bitrate,
            "-movflags",
            "+faststart",
            str(output),
        ]
    )


def target_size(
    input_path: Path,
    output: Path,
    *,
    megabytes: float,
    codec: str = "h264",
    audio_bitrate: str = "128k",
    preset: str = "medium",
    overwrite: bool = False,
) -> tuple[int, int]:
    if megabytes <= 0:
        raise ValueError("Target size must be positive")
    if codec not in {"h264", "h265"}:
        raise ValueError("Target-size mode supports h264 or h265")

    duration = duration_seconds(input_path)
    audio_bps = parse_bitrate(audio_bitrate)
    target_bits = megabytes * 1_000_000 * 8
    total_bps = int((target_bits / duration) * 0.965)
    video_bps = total_bps - audio_bps
    if video_bps < 100_000:
        raise LocalMediaError(
            "Target is too small for this duration/audio bitrate. Increase --mb or lower --audio-bitrate."
        )

    tools = find_toolchain()
    encoder = "libx264" if codec == "h264" else "libx265"
    null_sink = "NUL" if os.name == "nt" else "/dev/null"

    with tempfile.TemporaryDirectory(prefix="localmedia-pass-") as td:
        passlog = str(Path(td) / "ffmpeg2pass")
        common = [
            "-c:v",
            encoder,
            "-preset",
            preset,
            "-b:v",
            str(video_bps),
            "-passlogfile",
            passlog,
        ]
        run(
            [
                tools.ffmpeg,
                "-y",
                "-i",
                str(input_path),
                *common,
                "-pass",
                "1",
                "-an",
                "-f",
                "null",
                null_sink,
            ]
        )
        run(
            [
                tools.ffmpeg,
                *overwrite_args(overwrite),
                "-i",
                str(input_path),
                *common,
                "-pass",
                "2",
                "-c:a",
                "aac",
                "-b:a",
                audio_bitrate,
                "-movflags",
                "+faststart",
                str(output),
            ]
        )
    return video_bps, audio_bps


def resize(
    input_path: Path,
    output: Path,
    *,
    width: int | None,
    height: int | None,
    crf: int = 23,
    overwrite: bool = False,
) -> None:
    if (width is None) == (height is None):
        raise ValueError("Provide exactly one of width or height")
    if width is not None and width <= 0 or height is not None and height <= 0:
        raise ValueError("Dimensions must be positive")
    scale = f"scale={width}:-2" if width else f"scale=-2:{height}"
    tools = find_toolchain()
    run(
        [
            tools.ffmpeg,
            *overwrite_args(overwrite),
            "-i",
            str(input_path),
            "-vf",
            scale,
            "-c:v",
            "libx264",
            "-crf",
            str(crf),
            "-preset",
            "medium",
            "-c:a",
            "copy",
            str(output),
        ]
    )


def trim(
    input_path: Path,
    output: Path,
    *,
    start: str,
    end: str | None = None,
    duration: str | None = None,
    stream_copy: bool = False,
    overwrite: bool = False,
) -> None:
    if end and duration:
        raise ValueError("Use either end or duration, not both")
    tools = find_toolchain()
    cmd = [tools.ffmpeg, *overwrite_args(overwrite), "-ss", start, "-i", str(input_path)]
    if end:
        cmd += ["-to", end]
    if duration:
        cmd += ["-t", duration]
    if stream_copy:
        cmd += ["-c", "copy"]
    else:
        cmd += ["-c:v", "libx264", "-crf", "23", "-preset", "medium", "-c:a", "aac"]
    cmd.append(str(output))
    run(cmd)


def extract_audio(
    input_path: Path,
    output: Path,
    *,
    fmt: str,
    bitrate: str = "192k",
    overwrite: bool = False,
) -> None:
    tools = find_toolchain()
    codec_map = {
        "mp3": ["-c:a", "libmp3lame", "-b:a", bitrate],
        "aac": ["-c:a", "aac", "-b:a", bitrate],
        "opus": ["-c:a", "libopus", "-b:a", bitrate],
        "wav": ["-c:a", "pcm_s16le"],
        "flac": ["-c:a", "flac"],
    }
    if fmt not in codec_map:
        raise ValueError(f"Unsupported audio format: {fmt}")
    run(
        [
            tools.ffmpeg,
            *overwrite_args(overwrite),
            "-i",
            str(input_path),
            "-vn",
            *codec_map[fmt],
            str(output),
        ]
    )


def strip_metadata(input_path: Path, output: Path, *, overwrite: bool = False) -> None:
    tools = find_toolchain()
    run(
        [
            tools.ffmpeg,
            *overwrite_args(overwrite),
            "-i",
            str(input_path),
            "-map_metadata",
            "-1",
            "-map_chapters",
            "-1",
            "-c",
            "copy",
            str(output),
        ]
    )
