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
    +--> ImageMagick format discovery, identification and image conversion
    |
    v
Local filesystem output
```

The project does not proxy media through an HTTP service and does not require a browser.

## Desktop workflow

`gui.py` builds two instances of `ConverterTab` in one Tk notebook. They share layout,
file queues, result actions and status handling. Each tab snapshots its settings before
starting a worker thread; workers emit events through `queue.Queue`. The Tk event loop
polls those events and is the only thread that accesses widgets. A failed file does not
stop the rest of the queue. Completed rows are skipped on retry. Closing waits for active
work to finish. Video runs the existing CLI without `--overwrite`.

`images.py` discovers ImageMagick and parses the installed format table's read/write
flags. It identifies actual input contents, rejects multi-frame/page inputs, and performs
optional quality and aspect-preserving resize operations. ImageMagick receives literal
staged paths, avoiding its filename expression syntax. Encoded results are copied to an
exclusively created destination only after conversion succeeds. Temporary files are
cleaned up automatically. Listed coders can still fail due to delegates or policy; their
error text is preserved for the user. See [the image tutorial](IMAGE_CONVERTER.md).

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
