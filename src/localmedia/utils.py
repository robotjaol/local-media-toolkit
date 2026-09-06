from __future__ import annotations

import re
from pathlib import Path

_TIME_RE = re.compile(r"^(?:(?P<h>\d+):)?(?:(?P<m>\d{1,2}):)?(?P<s>\d+(?:\.\d+)?)$")


def parse_time(value: str) -> float:
    """Parse SS, MM:SS, or HH:MM:SS into seconds."""
    raw = value.strip()
    if not raw:
        raise ValueError("Time value cannot be empty")
    parts = raw.split(":")
    if len(parts) > 3:
        raise ValueError(f"Invalid time value: {value}")
    try:
        nums = [float(x) for x in parts]
    except ValueError as exc:
        raise ValueError(f"Invalid time value: {value}") from exc
    if any(x < 0 for x in nums):
        raise ValueError("Time cannot be negative")
    if len(nums) == 1:
        return nums[0]
    if len(nums) == 2:
        minutes, seconds = nums
        if seconds >= 60:
            raise ValueError("Seconds must be < 60 in MM:SS format")
        return minutes * 60 + seconds
    hours, minutes, seconds = nums
    if minutes >= 60 or seconds >= 60:
        raise ValueError("Minutes and seconds must be < 60 in HH:MM:SS format")
    return hours * 3600 + minutes * 60 + seconds


def human_bytes(size: int) -> str:
    value = float(size)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if value < 1024 or unit == "TiB":
            return f"{value:.2f} {unit}"
        value /= 1024
    return f"{value:.2f} TiB"


def ensure_input(path: str | Path) -> Path:
    p = Path(path).expanduser().resolve()
    if not p.exists():
        raise FileNotFoundError(f"Input does not exist: {p}")
    if not p.is_file():
        raise ValueError(f"Expected a file: {p}")
    return p


def output_path(input_path: Path, suffix: str, extension: str | None = None) -> Path:
    ext = extension or input_path.suffix.lstrip(".")
    ext = ext.lstrip(".")
    return input_path.with_name(f"{input_path.stem}{suffix}.{ext}")


def parse_bitrate(value: str) -> int:
    """Parse e.g. 128k, 2M, or integer bits/s."""
    v = value.strip().lower()
    multiplier = 1
    if v.endswith("k"):
        multiplier = 1_000
        v = v[:-1]
    elif v.endswith("m"):
        multiplier = 1_000_000
        v = v[:-1]
    try:
        n = float(v)
    except ValueError as exc:
        raise ValueError(f"Invalid bitrate: {value}") from exc
    if n <= 0:
        raise ValueError("Bitrate must be positive")
    return int(n * multiplier)
