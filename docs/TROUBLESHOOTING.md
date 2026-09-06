# Troubleshooting

## `ffmpeg` is not recognized / command not found

Install FFmpeg and reopen the terminal so the updated `PATH` is loaded.

Windows:

```powershell
winget install --id Gyan.FFmpeg -e
```

macOS:

```bash
brew install ffmpeg
```

Ubuntu / Debian:

```bash
sudo apt update && sudo apt install -y ffmpeg
```

Then run:

```bash
localmedia doctor
```

## Unknown encoder

Your FFmpeg build may not include the encoder requested. Inspect available encoders:

```bash
ffmpeg -encoders
```

Try H.264 with `libx264` first if supported by your build.

## Output already exists

By default the toolkit does not overwrite files. Add `--overwrite` only when you are sure the output path may be replaced.

## Target file is larger than requested

Target-size mode is approximate. MP4/container overhead, audio padding, muxing overhead, and rate-control variance can affect final bytes. Request a slightly smaller target when an external platform enforces a hard upload limit.

## GUI does not open on Linux

The Python installation may not include Tk. On Debian/Ubuntu, install the distribution's Tk package for your Python version, often:

```bash
sudo apt install python3-tk
```

The CLI does not require Tk.
