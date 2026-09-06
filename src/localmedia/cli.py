from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .core import (
    LocalMediaError,
    compress,
    convert,
    extract_audio,
    find_toolchain,
    probe,
    resize,
    strip_metadata,
    target_size,
    trim,
)
from .utils import ensure_input, human_bytes, output_path

MEDIA_EXTS = {
    ".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v", ".mpeg", ".mpg", ".ts",
    ".mp3", ".wav", ".flac", ".aac", ".m4a", ".ogg", ".opus",
}


def add_common_output(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("-o", "--output", help="Output file path")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite output if it exists")


def make_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="localmedia",
        description="Local-only FFmpeg media conversion and compression toolkit.",
    )
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sp = p.add_subparsers(dest="command", required=True)

    sp.add_parser("doctor", help="Check FFmpeg and FFprobe availability")

    info = sp.add_parser("info", help="Inspect a media file")
    info.add_argument("input")
    info.add_argument("--json", action="store_true", dest="as_json")

    conv = sp.add_parser("convert", help="Convert to another container/format")
    conv.add_argument("input")
    conv.add_argument("--to", required=True, dest="fmt", help="Output extension, e.g. mp4")
    add_common_output(conv)

    comp = sp.add_parser("compress", help="CRF-based video compression")
    comp.add_argument("input")
    comp.add_argument("--codec", choices=["h264", "h265", "av1"], default="h264")
    comp.add_argument("--crf", type=int, default=28)
    comp.add_argument("--preset", default="medium")
    comp.add_argument("--audio-bitrate", default="128k")
    add_common_output(comp)

    targ = sp.add_parser("target-size", help="Two-pass compression toward a target size")
    targ.add_argument("input")
    targ.add_argument("--mb", required=True, type=float, help="Target size in decimal MB")
    targ.add_argument("--codec", choices=["h264", "h265"], default="h264")
    targ.add_argument("--preset", default="medium")
    targ.add_argument("--audio-bitrate", default="128k")
    add_common_output(targ)

    res = sp.add_parser("resize", help="Resize video preserving aspect ratio")
    res.add_argument("input")
    group = res.add_mutually_exclusive_group(required=True)
    group.add_argument("--width", type=int)
    group.add_argument("--height", type=int)
    res.add_argument("--crf", type=int, default=23)
    add_common_output(res)

    tr = sp.add_parser("trim", help="Trim a media file")
    tr.add_argument("input")
    tr.add_argument("--start", required=True)
    end_group = tr.add_mutually_exclusive_group()
    end_group.add_argument("--end")
    end_group.add_argument("--duration")
    tr.add_argument("--copy", action="store_true", dest="stream_copy")
    add_common_output(tr)

    aud = sp.add_parser("audio", help="Extract audio")
    aud.add_argument("input")
    aud.add_argument("--to", required=True, choices=["mp3", "aac", "opus", "wav", "flac"], dest="fmt")
    aud.add_argument("--bitrate", default="192k")
    add_common_output(aud)

    meta = sp.add_parser("strip-metadata", help="Remove global metadata and chapters")
    meta.add_argument("input")
    add_common_output(meta)

    batch = sp.add_parser("batch", help="Batch-convert a directory")
    batch.add_argument("directory")
    batch.add_argument("--to", required=True, dest="fmt")
    batch.add_argument("--recursive", action="store_true")
    batch.add_argument("--overwrite", action="store_true")
    return p


def resolve_out(src: Path, explicit: str | None, suffix: str, ext: str | None = None) -> Path:
    return Path(explicit).expanduser().resolve() if explicit else output_path(src, suffix, ext)


def main(argv: list[str] | None = None) -> int:
    args = make_parser().parse_args(argv)
    try:
        if args.command == "doctor":
            tools = find_toolchain()
            print("Local Media Toolkit: OK")
            print(f"ffmpeg : {tools.ffmpeg}")
            print(f"ffprobe: {tools.ffprobe}")
            return 0

        if args.command == "info":
            src = ensure_input(args.input)
            data = probe(src)
            if args.as_json:
                print(json.dumps(data, indent=2))
            else:
                fmt = data.get("format", {})
                print(f"File      : {src}")
                print(f"Size      : {human_bytes(int(fmt.get('size', 0) or 0))}")
                print(f"Duration  : {float(fmt.get('duration', 0) or 0):.3f} s")
                print(f"Format    : {fmt.get('format_long_name', fmt.get('format_name', 'unknown'))}")
                for i, stream in enumerate(data.get("streams", [])):
                    codec_type = stream.get("codec_type", "unknown")
                    codec = stream.get("codec_name", "unknown")
                    extra = ""
                    if codec_type == "video":
                        extra = f" {stream.get('width', '?')}x{stream.get('height', '?')}"
                    print(f"Stream {i}  : {codec_type} / {codec}{extra}")
            return 0

        if args.command == "batch":
            directory = Path(args.directory).expanduser().resolve()
            if not directory.is_dir():
                raise ValueError(f"Directory does not exist: {directory}")
            iterator = directory.rglob("*") if args.recursive else directory.glob("*")
            inputs = [p for p in iterator if p.is_file() and p.suffix.lower() in MEDIA_EXTS]
            if not inputs:
                print("No supported media files found.")
                return 0
            failures = 0
            for src in inputs:
                out = src.with_suffix("." + args.fmt.lstrip("."))
                if out == src:
                    out = output_path(src, "_converted", args.fmt)
                print(f"[convert] {src.name} -> {out.name}")
                try:
                    convert(src, out, overwrite=args.overwrite)
                except Exception as exc:  # continue batch by design
                    failures += 1
                    print(f"[failed] {src}: {exc}", file=sys.stderr)
            print(f"Completed: {len(inputs) - failures}/{len(inputs)}")
            return 1 if failures else 0

        src = ensure_input(args.input)

        if args.command == "convert":
            out = resolve_out(src, args.output, "_converted", args.fmt)
            convert(src, out, overwrite=args.overwrite)
        elif args.command == "compress":
            out = resolve_out(src, args.output, "_compressed", "mp4")
            compress(
                src, out, codec=args.codec, crf=args.crf, preset=args.preset,
                audio_bitrate=args.audio_bitrate, overwrite=args.overwrite,
            )
        elif args.command == "target-size":
            out = resolve_out(src, args.output, "_target", "mp4")
            vbps, abps = target_size(
                src, out, megabytes=args.mb, codec=args.codec, preset=args.preset,
                audio_bitrate=args.audio_bitrate, overwrite=args.overwrite,
            )
            print(f"Planned video bitrate: {vbps/1000:.0f} kb/s; audio: {abps/1000:.0f} kb/s")
        elif args.command == "resize":
            out = resolve_out(src, args.output, "_resized", "mp4")
            resize(src, out, width=args.width, height=args.height, crf=args.crf, overwrite=args.overwrite)
        elif args.command == "trim":
            out = resolve_out(src, args.output, "_trimmed", src.suffix.lstrip("."))
            trim(
                src, out, start=args.start, end=args.end, duration=args.duration,
                stream_copy=args.stream_copy, overwrite=args.overwrite,
            )
        elif args.command == "audio":
            out = resolve_out(src, args.output, "_audio", args.fmt)
            extract_audio(src, out, fmt=args.fmt, bitrate=args.bitrate, overwrite=args.overwrite)
        elif args.command == "strip-metadata":
            out = resolve_out(src, args.output, "_clean", src.suffix.lstrip("."))
            strip_metadata(src, out, overwrite=args.overwrite)
        else:
            raise AssertionError(args.command)

        print(f"Output: {out}")
        if out.exists():
            print(f"Size  : {human_bytes(out.stat().st_size)}")
        return 0
    except (LocalMediaError, FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
