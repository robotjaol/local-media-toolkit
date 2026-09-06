# Codec Guide

## H.264 / AVC

Use when compatibility is the priority. H.264 is broadly supported by browsers, phones, editors, TVs, presentation software, and social platforms.

```bash
localmedia compress input.mp4 --codec h264 --crf 23
```

## H.265 / HEVC

Use when smaller files are worth slower encoding and potentially narrower playback compatibility.

```bash
localmedia compress input.mp4 --codec h265 --crf 28
```

## AV1

Use for modern, efficient software encoding when your FFmpeg build includes an AV1 encoder supported by this project (`libsvtav1`). AV1 encoding may be materially slower than H.264.

```bash
localmedia compress input.mp4 --codec av1 --crf 32
```

## CRF

CRF is a quality-targeted rate-control mode, not a file-size guarantee. Lower values generally produce better quality and larger files. Values are codec-specific and should not be compared as if numerically equivalent between codecs.

## Container vs codec

A `.mp4`, `.mkv`, or `.mov` extension names a container. H.264, H.265, AV1, AAC, Opus, and FLAC are codecs. "Convert to MP4" may involve only remuxing in some cases, but this toolkit's generic `convert` command lets FFmpeg choose defaults unless a specialized command explicitly selects codecs.
