# FFmpeg-Only Recipes

You do not need Local Media Toolkit to benefit from the local-first workflow. If FFmpeg is installed, the following commands work directly in Windows PowerShell, macOS Terminal, and Linux shells with normal path-quoting differences.

## Convert to MP4

```bash
ffmpeg -i input.mov -c:v libx264 -crf 23 -preset medium -c:a aac -b:a 128k -movflags +faststart output.mp4
```

## Reduce file size

```bash
ffmpeg -i input.mp4 -c:v libx264 -crf 28 -preset medium -c:a aac -b:a 128k output-smaller.mp4
```

## Resize to 720p

```bash
ffmpeg -i input.mp4 -vf "scale=-2:720" -c:v libx264 -crf 23 -c:a copy output-720p.mp4
```

## Convert H.264 to H.265

```bash
ffmpeg -i input.mp4 -c:v libx265 -crf 28 -preset medium -c:a aac -b:a 128k output-hevc.mp4
```

## Extract MP3 audio

```bash
ffmpeg -i input.mp4 -vn -c:a libmp3lame -b:a 192k output.mp3
```

## Fast trim without re-encoding

```bash
ffmpeg -ss 00:00:10 -i input.mp4 -t 20 -c copy clip.mp4
```

## Remove global metadata

```bash
ffmpeg -i input.mp4 -map_metadata -1 -map_chapters -1 -c copy clean.mp4
```

## Inspect file metadata and streams

```bash
ffprobe -v error -show_format -show_streams input.mp4
```

## Why use the wrapper then?

The wrapper provides safer defaults, automatic output names, cross-platform target-size logic, batch operations, discoverable help, a local GUI, tests, and repeatable workflows. FFmpeg remains the underlying engine.
