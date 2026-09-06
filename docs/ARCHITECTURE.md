# Architecture

## Design objective

Keep the application small enough to audit and keep media processing local.

## Components

```text
CLI / Tk GUI
    |
    v
Python command orchestration
    |
    +--> ffprobe JSON inspection
    |
    +--> ffmpeg subprocess execution
    |
    v
Local filesystem output
```

The project does not proxy media through an HTTP service and does not require a browser.

## Command execution

Arguments are passed to Python's subprocess API as an argument vector rather than through a shell command string. This reduces shell-injection exposure from filenames and user-provided paths.

## Why not bundle FFmpeg

FFmpeg builds vary by platform, codec availability, optional libraries, and license configuration. Separating this wrapper from the FFmpeg binary keeps updates and licensing clearer and allows users to choose the build appropriate to their system.

## Target-size mode

Target-size mode:

1. Reads media duration with FFprobe.
2. Calculates an approximate total bitrate from requested bytes and duration.
3. Reserves the selected audio bitrate.
4. Applies a small container-overhead margin.
5. Runs two-pass H.264 or H.265 video encoding.
6. Writes AAC audio and fast-start MP4 metadata.

Final bytes may differ because containers and codec behavior have overhead and rate-control variance.
