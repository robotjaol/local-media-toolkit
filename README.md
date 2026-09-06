# Local Media Toolkit

> Privacy-first, cross-platform FFmpeg tooling for converting, compressing, resizing, trimming, inspecting, and batch-processing media entirely on your own machine.

**No uploads. No cloud converter. No tracking. Your media stays local.**

[![CI](https://github.com/YOUR_GITHUB_USERNAME/local-media-toolkit/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_GITHUB_USERNAME/local-media-toolkit/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![FFmpeg](https://img.shields.io/badge/powered%20by-FFmpeg-green.svg)](https://ffmpeg.org/)

## Why this exists

Online media converters are convenient, but they require uploading files to a third-party server. For private footage, work documents, customer recordings, unreleased content, research data, or simply large files, that creates avoidable privacy, bandwidth, and retention risks.

Local Media Toolkit is a thin, auditable command-line and desktop wrapper around FFmpeg. It keeps the heavy lifting on your computer while making common workflows easier to discover and repeat.

## Features

| Capability | Command | Typical use |
|---|---|---|
| Environment check | `localmedia doctor` | Verify FFmpeg / FFprobe installation |
| Media inspection | `localmedia info video.mp4` | Codec, duration, streams, dimensions |
| Format conversion | `localmedia convert input.mov --to mp4` | MOV to MP4, MKV to MP4, etc. |
| Quality compression | `localmedia compress input.mp4 --crf 28` | Reduce file size while controlling quality |
| Target-size compression | `localmedia target-size input.mp4 --mb 25` | Aim for a maximum upload size |
| Resize | `localmedia resize input.mp4 --height 1080` | Downscale while preserving aspect ratio |
| Trim | `localmedia trim input.mp4 --start 00:00:10 --end 00:00:30` | Cut a clip locally |
| Extract audio | `localmedia audio input.mp4 --to mp3` | Video to audio |
| Remove metadata | `localmedia strip-metadata input.mp4` | Produce a privacy-clean copy |
| Batch convert | `localmedia batch ./videos --to mp4` | Convert an entire directory |
| Desktop GUI | `localmedia-gui` | Point-and-click local conversion/compression |

## Architecture

```text
User
  |
  +--> CLI: localmedia ------------------+
  |                                      |
  +--> Desktop GUI: localmedia-gui ------+--> LocalMedia Python core
                                             |
                                             +--> ffprobe: inspect input
                                             +--> ffmpeg: transform media
                                             |
                                             +--> output file on local disk

No application server. No browser upload. No remote processing.
```

## Install FFmpeg first

This repository intentionally does **not** bundle FFmpeg. Install FFmpeg using your operating system's package manager or a trusted build provider.

### Windows 10 / 11

Recommended using Windows Package Manager:

```powershell
winget install --id Gyan.FFmpeg -e
```

Close and reopen your terminal, then verify:

```powershell
ffmpeg -version
ffprobe -version
```

The official FFmpeg download page links to Gyan.dev as a Windows build provider.

### macOS

Using Homebrew:

```bash
brew install ffmpeg
ffmpeg -version
ffprobe -version
```

### Ubuntu / Debian

```bash
sudo apt update
sudo apt install -y ffmpeg
ffmpeg -version
ffprobe -version
```

If your distribution package is older than the codec/features you need, use the FFmpeg project's official download guidance.

## Install Local Media Toolkit

### Option A: install from source

```bash
git clone https://github.com/YOUR_GITHUB_USERNAME/local-media-toolkit.git
cd local-media-toolkit
python -m pip install .
```

### Option B: editable install for development

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

macOS / Ubuntu:

```bash
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

Then:

```bash
localmedia doctor
```

## Quick start

### 1. Convert MOV to MP4

```bash
localmedia convert input.mov --to mp4
```

Explicit output:

```bash
localmedia convert input.mov --to mp4 -o output.mp4
```

### 2. Reduce video size with CRF

```bash
localmedia compress input.mp4 --crf 28 --preset medium
```

Lower CRF normally means higher quality and larger files. A practical H.264 starting range is around 18 to 30. The exact visual result depends on the source.

Codec presets:

```bash
localmedia compress input.mp4 --codec h264 --crf 28
localmedia compress input.mp4 --codec h265 --crf 28
localmedia compress input.mp4 --codec av1  --crf 32
```

### 3. Compress toward a target size

```bash
localmedia target-size input.mp4 --mb 25
```

This uses duration from `ffprobe`, reserves an audio bitrate budget, and performs two-pass video encoding for a closer size target. Container overhead means the final size is an approximation, not a cryptographic guarantee.

### 4. Resize to 1080p height

```bash
localmedia resize input.mp4 --height 1080
```

Or width:

```bash
localmedia resize input.mp4 --width 1280
```

### 5. Trim a clip

Accurate re-encode:

```bash
localmedia trim input.mp4 --start 00:00:10 --end 00:00:30
```

Fast stream-copy trim:

```bash
localmedia trim input.mp4 --start 00:00:10 --end 00:00:30 --copy
```

Stream copy is much faster but cuts may align to keyframes rather than exact frame boundaries.

### 6. Extract audio

```bash
localmedia audio input.mp4 --to mp3 --bitrate 192k
```

Also supports `wav`, `flac`, `aac`, and `opus` when your FFmpeg build contains the required codec.

### 7. Remove metadata

```bash
localmedia strip-metadata input.mp4
```

This creates a new file with global metadata stripped. It does not claim to remove every possible identifying signal from the audiovisual content itself.

### 8. Batch convert

```bash
localmedia batch ./incoming --to mp4
```

Recursive:

```bash
localmedia batch ./incoming --to mp4 --recursive
```

### 9. Desktop GUI

```bash
localmedia-gui
```

The GUI uses Python's standard Tk interface and executes the same local FFmpeg workflow. No web server is started.

## Command reference

```text
localmedia doctor
localmedia info INPUT [--json]
localmedia convert INPUT --to FORMAT [-o OUTPUT] [--overwrite]
localmedia compress INPUT [-o OUTPUT] [--codec h264|h265|av1] [--crf N] [--preset NAME]
localmedia target-size INPUT --mb SIZE [-o OUTPUT] [--codec h264|h265] [--audio-bitrate 128k]
localmedia resize INPUT [--width N | --height N] [-o OUTPUT] [--crf N]
localmedia trim INPUT --start TIME [--end TIME | --duration TIME] [-o OUTPUT] [--copy]
localmedia audio INPUT --to FORMAT [-o OUTPUT] [--bitrate 192k]
localmedia strip-metadata INPUT [-o OUTPUT]
localmedia batch DIRECTORY --to FORMAT [--recursive] [--overwrite]
```

Run `localmedia <command> --help` for command-specific arguments.

## Common recipes

### Social media friendly H.264 MP4

```bash
ffmpeg -i input.mov -c:v libx264 -preset medium -crf 23 -c:a aac -b:a 128k -movflags +faststart output.mp4
```

Equivalent wrapper flow:

```bash
localmedia compress input.mov --codec h264 --crf 23 -o output.mp4
```

### Smaller H.265 archive copy

```bash
localmedia compress input.mp4 --codec h265 --crf 28
```

H.265 can reduce bitrate for similar visual quality, but compatibility and encoding speed differ from H.264.

### Strip metadata before sharing

```bash
localmedia strip-metadata private-video.mp4 -o share-copy.mp4
```

For users who want zero Python wrapper, see [docs/FFMPEG_ONLY.md](docs/FFMPEG_ONLY.md) for direct FFmpeg commands.

## Privacy model

Local Media Toolkit is designed around a simple threat-reduction principle: **do not transmit the media in the first place**.

The application itself:

1. Does not upload media.
2. Does not run a cloud backend.
3. Does not require an account or API key.
4. Does not include analytics or telemetry.
5. Invokes the local `ffmpeg` and `ffprobe` executables available in `PATH`.

This does not make the operating system, third-party FFmpeg build, storage device, or other software on your machine inherently private. Review your own environment for sensitive workflows.

## Performance notes

Encoding speed depends on codec, preset, resolution, CPU/GPU, and FFmpeg build options. The default commands favor broad CPU compatibility. Advanced users can call FFmpeg directly for hardware acceleration such as NVENC, Quick Sync Video, VideoToolbox, VAAPI, or other supported encoders.

A future hardware-acceleration abstraction is listed in the roadmap rather than silently selecting a GPU codec that may not exist on every machine.

## Project structure

```text
local-media-toolkit/
├── .github/
│   ├── ISSUE_TEMPLATE/
│   ├── pull_request_template.md
│   └── workflows/
├── docs/
│   ├── ARCHITECTURE.md
│   ├── CODEC_GUIDE.md
│   ├── FFMPEG_ONLY.md
│   ├── PRIVACY.md
│   └── TROUBLESHOOTING.md
├── scripts/
│   ├── bootstrap.ps1
│   └── bootstrap.sh
├── src/localmedia/
│   ├── __init__.py
│   ├── cli.py
│   ├── core.py
│   ├── gui.py
│   └── utils.py
├── tests/
│   ├── test_core.py
│   └── test_utils.py
├── CHANGELOG.md
├── CODE_OF_CONDUCT.md
├── CONTRIBUTING.md
├── LICENSE
├── SECURITY.md
└── pyproject.toml
```

## Development

```bash
python -m pip install -e ".[dev]"
pytest -q
ruff check .
```

Integration smoke test, requires FFmpeg:

```bash
python scripts/smoke_test.py
```

## Roadmap

- Hardware encoder detection and explicit NVENC / QSV / VideoToolbox / VAAPI presets
- Subtitle burn-in and subtitle extraction
- Image sequence and GIF workflows
- Drag-and-drop desktop UI
- Reproducible benchmark suite for quality, speed, and size
- Optional standalone desktop packaging without requiring Python from end users
- Automated release binaries for Windows, macOS, and Linux

## Security

Do not open untrusted media with outdated codec stacks. Keep FFmpeg and your OS patched. See [SECURITY.md](SECURITY.md).

## Licensing

The Local Media Toolkit source code is released under the MIT License. FFmpeg is a separate project with its own licensing terms, which can vary depending on how it is built and which optional libraries are enabled. This repository does not redistribute FFmpeg binaries. See [docs/LICENSING.md](docs/LICENSING.md).

## Contributing

Issues, documentation improvements, platform fixes, codec presets, and tests are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request.

## Acknowledgements

Built on top of [FFmpeg](https://ffmpeg.org/), the cross-platform multimedia framework.

---

**Principle:** if a file can be converted locally, you should not have to upload it to a random converter just to change its format or reduce its size.
